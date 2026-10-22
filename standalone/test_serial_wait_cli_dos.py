#!/usr/bin/env python3
"""Actual DOS environment admission before script/UART acquisition."""
import argparse,json,os,shutil,subprocess
from pathlib import Path
from check_aspect_runner import HARNESS,compile_source,ROOT,sha


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--label',required=True);a=p.parse_args()
    assert a.label.replace('-','').replace('_','').isalnum()
    out=ROOT/'build/aspect-txwait-cli'/a.label;out.mkdir(parents=True,exist_ok=False)
    binary=ROOT/'build/aspect-runner/ASPECT.EXE';shutil.copy2(binary,out/'ASPECT.EXE')
    (out/'HELLO.ASX').write_bytes(compile_source('proc main\nmessage "OK"\nendproc\n'))
    tests=[('DEFAULT',None,'HELLO.ASX',None,0)]
    for i,text in enumerate(['1','2','6','30','3600','0001','0030']):
        tests.append(('GOOD'+str(i),text,'HELLO.ASX',None,0))
    for i,text in enumerate(['0','0000','3601','9999','10000','00001','-1','+1',' 1','1 ','1s','1.0']):
        tests.append(('BAD'+str(i),text,'ABSENT.ASX','/S0:0003:03:N',64))
    tests += [('HELPBAD','0','/?',None,0),('VALIDSER','30','HELLO.ASX','/S0:0003:03:N',14),('CLEARED',None,'HELLO.ASX',None,0)]
    program=HARNESS.replace('#include <dos.h>','#include <dos.h>\n#include <stdlib.h>')
    for name,text,file,limit,status in tests:
        assignment='PCPLUS_TXWAIT='+str(text) if text is not None else 'PCPLUS_TXWAIT='
        program+=' ck(putenv('+json.dumps(assignment)+')==0);\n'
        program+=' run('+','.join([json.dumps(name),json.dumps(file),json.dumps(limit) if limit else '0',str(status),'0'])+');\n'
    program+=' printf("POLICY %u cases %u checks %u failures\\n",cases,checks,failed);return failed?1:0;}\n'
    (out/'driver.c').write_text(program)
    subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-s','-w4','-we','-k4096','-fe=RUNTEST.EXE',str(out/'driver.c')],cwd=out,check=True)
    config=f'[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=max\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "{out}"\nc:\nRUNTEST >RESULT.TXT\nif errorlevel 1 goto failed\necho PASS>PASS.TXT\ngoto done\n:failed\necho FAIL>FAIL.TXT\n:done\nexit\n'
    (out/'dosbox.conf').write_text(config)
    with (out/'dosbox.log').open('w') as log:
        subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=60,check=True)
    result=(out/'RESULT.TXT').read_text()
    assert (out/'PASS.TXT').exists() and not (out/'FAIL.TXT').exists(),result
    rows=[]
    for name,text,file,limit,status in tests:
        stdout=(out/(name+'.OUT')).read_bytes();stderr=(out/(name+'.ERR')).read_bytes()
        if name=='HELPBAD':
            assert stdout==b'ASPECT script.ASX [instruction-budget:1..65535] [/S1:0003:03:N]\r\nPCPLUS_TXWAIT=1..3600 sets transmit stall seconds (default30).\r\n' and not stderr
        elif not status:assert stdout==b'OK\r\n' and not stderr
        elif status==64:
            assert not stdout and stderr==b'ASPECT: PCPLUS_TXWAIT must be 1..3600 seconds (default30).\r\n'
        else:assert not stdout and b'ASPECT:' in stderr
        rows.append(dict(case=name,value=text,exit=status,passed=True,stdout_hex=stdout.hex(),stderr_hex=stderr.hex()))
    report=dict(passed=True,runner_sha256=sha(binary),cases=rows,DOS_summary=result,scope=__doc__+' Production child spawned with real DOS environment, redirected handles, vector restoration and statuses. Invalid policy precedes invalid serial admission and absent file. Help remains accessible; deleting assignment restores default. No physical modem claim.',captures={f.name:sha(f) for f in out.iterdir() if f.is_file()})
    (out/'checks.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,cases=len(rows),result=result)))


if __name__=='__main__':main()
