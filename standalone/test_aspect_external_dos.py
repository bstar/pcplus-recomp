#!/usr/bin/env python3
"""DOS OMF frontend ABI and explicit product rejection until executor admission."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
from build_aspect_external import ROOT, OUT, sha


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--label', required=True)
    args = parser.parse_args()
    assert re.fullmatch(r'[A-Za-z0-9_-]+', args.label)
    out = ROOT / 'build/aspect-external-dos' / args.label
    out.mkdir(parents=True, exist_ok=False)
    stage = out / 'drive'
    stage.mkdir()
    compiler = ROOT / 'build/aspect-compiler-dos/ASPCOMP.EXE'
    runner = ROOT / 'build/aspect-runner/ASPECT.EXE'
    for path in (compiler, runner, OUT / 'EXTERNAL.EXE'):
        shutil.copyfile(path, stage / path.name)
    fixture = ROOT / 'standalone/fixtures/aspect_external_compiler_vectors.json'
    cases = json.loads(fixture.read_text())['cases']
    accepted, batch = [], ['@echo off', 'SET COMSPEC=C:\\CHILD.COM']
    for index, case in enumerate(cases):
        name = f'EX{index:03}'
        (stage / (name + '.ASP')).write_bytes(case['source'].encode('cp437'))
        batch.append(f'ASPCOMP {name}.ASP >{name}.CMP')
        if case['success']:
            batch.append('if errorlevel 1 goto failed')
            command = re.search(r'^\s*(dos|run|shell)(?:\s|$)', case['source'], re.M | re.I)[1].lower()
            accepted.append((name, {'dos': 0x28, 'run': 0x9b, 'shell': 0xa3}[command]))
        else:
            batch += [f'if errorlevel 1 goto C{index:03}', 'goto failed', f':C{index:03}']
    # A mistaken dispatch publication must not leave an interactive shell. This
    # authored sentinel exits immediately and leaves a detectable marker.
    sentinel = 'BITS 16\nORG 0x100\nmov ah,0x3c\nxor cx,cx\nmov dx,name\nint 0x21\njc done\nmov bx,ax\nmov ah,0x3e\nint 0x21\ndone:mov ax,0x4c00\nint 0x21\nname:db "UNSAFE.OUT",0\n'
    (out / 'sentinel.asm').write_text(sentinel)
    subprocess.run(['nasm', '-fbin', str(out / 'sentinel.asm'), '-o', str(stage / 'CHILD.COM')], check=True)
    program = r'''
#include <stdio.h>
#include <process.h>
#include <io.h>
#include <fcntl.h>
#include <sys/stat.h>
static unsigned cases,failures;
static void run(const char *path,const char *log){
 int fd,out,err,status;
 fd=open(log,O_CREAT|O_EXCL|O_RDWR|O_BINARY,S_IREAD|S_IWRITE);if(fd<0){++failures;return;}
 fflush(stdout);fflush(stderr);out=dup(1);err=dup(2);
 if(out<0||err<0||dup2(fd,1)||dup2(fd,2)){++failures;return;}
 status=spawnl(P_WAIT,"ASPECT.EXE","ASPECT",path,(char *)0);
 fflush(stdout);fflush(stderr);if(dup2(out,1)||dup2(err,2))++failures;
 if(close(out)||close(err)||close(fd))++failures;
 ++cases;if(status!=3){++failures;printf("FAIL %s returned%d\n",path,status);}
}
int main(void){
''' + ''.join(f' run("{name}.ASX","{name}.LOG");\n' for name, _ in accepted) + r'''
 if(access("UNSAFE.OUT",0)==0)++failures;
 printf("EXTERNAL_UNPUBLISHED %u cases %u failures\n",cases,failures);return failures?1:0;}
'''
    (out / 'harness.c').write_text(program)
    subprocess.run(['wcl', '-q', '-bt=dos', '-0', '-ms', '-ecc', '-s', '-w4', '-we', '-k4096', '-fe=' + str(stage / 'REJECT.EXE'), str(out / 'harness.c')], cwd=out, check=True)
    batch += ['EXTERNAL >BOUNDARY.TXT', 'if errorlevel 1 goto failed', 'REJECT >REJECT.TXT', 'if errorlevel 1 goto failed', 'echo PASS>PASS.TXT', 'goto done', ':failed', 'echo FAIL>FAIL.TXT', ':done', 'exit']
    (stage / 'RUN.BAT').write_text('\n'.join(batch) + '\n')
    (out / 'dosbox.conf').write_text(f'[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\nfpu=false\ncycles=max\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "{stage}"\nc:\ncall RUN.BAT\nexit\n')
    with (out / 'dosbox.log').open('w') as log:
        subprocess.run(['dosbox-x', '-fastlaunch', '-nogui', '-conf', str(out / 'dosbox.conf')], cwd=out, env=dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy'), stdout=log, stderr=log, check=True, timeout=120)
    boundary = (stage / 'BOUNDARY.TXT').read_text() if (stage / 'BOUNDARY.TXT').exists() else ''
    reject = (stage / 'REJECT.TXT').read_text() if (stage / 'REJECT.TXT').exists() else ''
    assert (stage / 'PASS.TXT').exists() and not (stage / 'FAIL.TXT').exists(), boundary + reject
    assert 'EXTERNAL_BOUNDARY 53 cases 436 checks 0 failures' in boundary, boundary
    assert 'EXTERNAL_UNPUBLISHED 29 cases 0 failures' in reject, reject
    records = []
    for index, case in enumerate(cases):
        name = f'EX{index:03}'
        target = stage / (name + '.ASX')
        assert target.exists() == case['success']
        if case['success']:
            assert sha(target) == case['asx_sha256']
            opcode = dict(accepted)[name]
            log = (stage / (name + '.LOG')).read_bytes()
            assert f'error 3, opcode {opcode:02X},'.encode() in log, (name, log)
            records.append(dict(case=name, opcode=opcode, log_sha256=sha(stage / (name + '.LOG'))))
    assert not (stage / 'UNSAFE.OUT').exists()
    assert sha(compiler) == sha(stage / 'ASPCOMP.EXE') and sha(runner) == sha(stage / 'ASPECT.EXE')
    result = dict(passed=True, frontend_DOS_cases=53, frontend_DOS_assertions=436,
                  compiler_cases=len(cases), accepted=29, rejected=41,
                  unsupported_product_cases=records, runtime_enabled=False,
                  runner_sha256=sha(runner), compiler_sha256=sha(compiler),
                  diagnostic_sha256=sha(OUT / 'EXTERNAL.EXE'), diagnostic_result_sha256=sha(stage / 'BOUNDARY.TXT'),
                  rejection_harness_sha256=sha(stage / 'REJECT.EXE'), rejection_result_sha256=sha(stage / 'REJECT.TXT'),
                  sentinel_sha256=sha(stage / 'CHILD.COM'), fixture_sha256=sha(fixture),
                  checker_sha256=sha(Path(__file__)), harness_sha256=sha(out / 'harness.c'), original_inputs=[],
                  scope='Actual8086 DOS OMF command frontends with explicit executor/COMSPEC/operand service models; all70 frozen compiler outcomes,29 exact accepted ASX products and all29 product CLI rejections at their actual opcode before any external side effect. No general child executor/display/UART integration claim.')
    (out / 'checks.json').write_text(json.dumps(result, indent=2) + '\n')
    print('External DOS:', 53, 'boundary cases/436 checks;', len(records), 'explicit product rejections PASS')


if __name__ == '__main__':
    main()
