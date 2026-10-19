#!/usr/bin/env python3
"""Exercise production ASPECT.EXE as a DOS child with real redirected handles."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from build_aspect_runner import ROOT, OUT, main as build, sha

sys.path.insert(0, str(ROOT / 'src/aspect'))
from compiler import compile_source


HARNESS = r'''
#include <dos.h>
#include <stdio.h>
#include <process.h>
#include <io.h>
#include <fcntl.h>
#include <sys/stat.h>
static unsigned failed,checks,cases;
static void ck(unsigned condition){++checks;if(!condition)++failed;}
static void run(const char *name,const char *file,const char *limit,unsigned expected,unsigned escape){
 int out,err,saveout,saveerr,result;char path[16];void (__interrupt __far *vector)(void);
 vector=_dos_getvect(0);++cases;
 sprintf(path,"%s.OUT",name);out=open(path,O_CREAT|O_TRUNC|O_WRONLY|O_BINARY,S_IREAD|S_IWRITE);
 sprintf(path,"%s.ERR",name);err=open(path,O_CREAT|O_TRUNC|O_WRONLY|O_BINARY,S_IREAD|S_IWRITE);
 ck(out>=0&&err>=0);saveout=dup(1);saveerr=dup(2);ck(saveout>=0&&saveerr>=0);
 ck(dup2(out,1)==0&&dup2(err,2)==0);close(out);close(err);
 if(escape){_disable();*(unsigned __far *)MK_FP(0x40,0x1a)=0x1e;*(unsigned __far *)MK_FP(0x40,0x1c)=0x20;*(unsigned __far *)MK_FP(0x40,0x1e)=0x011b;_enable();}
 if(limit)result=spawnl(P_WAIT,"ASPECT.EXE","ASPECT",file,limit,(char *)0);
 else if(file)result=spawnl(P_WAIT,"ASPECT.EXE","ASPECT",file,(char *)0);
 else result=spawnl(P_WAIT,"ASPECT.EXE","ASPECT",(char *)0);
 dup2(saveout,1);dup2(saveerr,2);close(saveout);close(saveerr);
 ck(result==expected);ck(_dos_getvect(0)==vector);
 printf("CHILD %s exit=%d expected=%u vector=%u\n",name,result,expected,_dos_getvect(0)==vector);
}
int main(void){
'''


def main():
    build()
    tests = OUT / 'tests'
    tests.mkdir(exist_ok=True)
    (tests / 'ASPECT.EXE').write_bytes((OUT / 'ASPECT.EXE').read_bytes())
    definitions = [
        ('HELLO', 'message "Hello, DOS"\n', 0, b'Hello, DOS\r\n', None, False),
        ('CARET', 'message "A^MB^JC^@D^^E^^^F"\n', 0, b'A\rB\nC\xffD\x1eE^F\r\n', None, False),
        ('EARLY', 'message "before"\nexit\nmessage "after"\n', 0, b'before\r\n', None, False),
        ('UNKNOWN', 'transmit "wire"\n', 3, b'', None, False),
        ('ZERO', 'integer number\nnumber = 1 / 0\n', 11, b'', None, False),
        ('BUDGET', 'while 1\nendwhile\n', 6, b'', '12', False),
        ('CANCEL', 'while 1\nendwhile\n', 13, b'', None, True),
        ('PAUSE', 'pause 1\nmessage "awake"\n', 0, b'awake\r\n', None, False),
    ]
    program = HARNESS
    expectations = {}
    for name, body, error, output, limit, escape in definitions:
        source = 'proc main\n' + body + 'endproc\n'
        (tests / (name + '.ASX')).write_bytes(compile_source(source))
        program += f' run("{name}","{name}.ASX",{json.dumps(limit) if limit else "0"},{error},{int(escape)});\n'
        expectations[name] = dict(exit=error, stdout_hex=output.hex(), source=source,
                                  asx_sha256=sha(tests / (name + '.ASX')))
    extras = [('MISSING', 'ABSENT.ASX', None, 1), ('BADHEAD', 'BAD.ASX', None, 2),
              ('ARGS', None, None, 64), ('LIMIT0', 'HELLO.ASX', '0', 64),
              ('LIMITBIG', 'HELLO.ASX', '65536', 64), ('LIMITBAD', 'HELLO.ASX', '12x', 64),
              ('DEVICE', 'CON.ASX', None, 64), ('HELP', '/?', None, 0),
              ('SERPORT','HELLO.ASX','/S0:0003:03:N',14),
              ('SERDIV','HELLO.ASX','/S1:0000:03:N',14),
              ('SERLCR','HELLO.ASX','/S1:0003:83:N',14),
              ('SERFLOW','HELLO.ASX','/S1:0003:03:X',14),
              ('SERPTR','HELLO.ASX','/S1:0003:03:N:0000:0000',14)]
    (tests / 'BAD.ASX').write_bytes(b'\x81')
    (tests / 'ABSENT.ASX').unlink(missing_ok=True)
    for name, file, limit, error in extras:
        program += f' run("{name}",{json.dumps(file) if file else "0"},{json.dumps(limit) if limit else "0"},{error},0);\n'
        expectations[name] = dict(exit=error, stdout_hex=('ASPECT script.ASX [instruction-budget:1..65535] [/S1:0003:03:N]\r\n'.encode().hex() if name=='HELP' else ''))
    program += ' printf("RUNNER %u cases %u checks %u failures\\n",cases,checks,failed);return failed?1:0;}\n'
    (tests / 'harness.c').write_text(program)
    subprocess.run(['wcl', '-q', '-bt=dos', '-0', '-ms', '-s', '-w4', '-we', '-k4096',
                    '-fe=RUNTEST.EXE', str(tests / 'harness.c')], cwd=tests, check=True)
    config = f'[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=max\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "{tests}"\nc:\nRUNTEST >RESULT.TXT\nif errorlevel 1 goto failed\necho PASS>PASS.TXT\ngoto done\n:failed\necho FAIL>FAIL.TXT\n:done\nexit\n'
    (tests / 'dosbox.conf').write_text(config)
    for name in ['PASS.TXT', 'FAIL.TXT', 'RESULT.TXT']:
        (tests / name).unlink(missing_ok=True)
    with (tests / 'dosbox.log').open('w') as log:
        subprocess.run(['dosbox-x', '-fastlaunch', '-nogui', '-conf', str(tests / 'dosbox.conf')],
                       env=dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy'),
                       stdout=log, stderr=log, timeout=45, check=True)
    result = (tests / 'RESULT.TXT').read_text()
    assert (tests / 'PASS.TXT').exists() and not (tests / 'FAIL.TXT').exists(), result
    assert 'RUNNER 21 cases 105 checks 0 failures' in result, result
    for name, expected in expectations.items():
        output, error = (tests / (name + '.OUT')).read_bytes(), (tests / (name + '.ERR')).read_bytes()
        assert output.hex() == expected['stdout_hex'], (name, output)
        if expected['exit']:
            assert error and (b'Usage:' in error if expected['exit']==64 else b'ASPECT:' in error), (name, error)
        else:
            assert error == b'', (name, error)
        expected['stderr_hex'] = error.hex()
    report = dict(passed=True, original_inputs=[], binary_sha256=sha(OUT / 'ASPECT.EXE'),
                  manifest_sha256=sha(OUT / 'manifest.json'), checker_sha256=sha(Path(__file__)),
                  compiler_sha256=sha(ROOT / 'src/aspect/compiler.py'), result_sha256=sha(tests / 'RESULT.TXT'),
                  DOS_summary='RUNNER 21 cases 105 checks 0 failures', cases=expectations,
                  scope='Actual production DOS CLI spawned21 times with independent handles; exact stdout/stderr, statuses, BIOS Escape, native delay, malformed serial handoff admission and INT0 restoration. Fixed trusted source cases, not arbitrary-bytecode safety or complete serial scripting.')
    (OUT / 'checks.json').write_text(json.dumps(report, indent=2) + '\n')
    print(report['DOS_summary'])


if __name__ == '__main__':
    main()
