#!/usr/bin/env python3
"""Explicit original ASPCOMP oracle for authored interactive GET grammar probes."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[1]
COMPILER_SHA='5664fdfae375774da5303cc8b53c00ef773a6650132de73c7206e46ddc05039a'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def corpus(extended=False):
    bodies=['get','get value','get "x"','get number','get wide','get realnum','get value 10','get value,10',
        'get 10 value','get 10, value','get 1 2 value','get 1 2 3 value','get 1 2 3 4 value',
        'get 1 2 3 4 5 value','get 1 2 3 4 5 6 value','get value 1 2','get value 1 2 3',
        'get value 1 2 3 4','get value 1 2 3 4 5','get value "prompt"','get "prompt" value',
        'get 1 2 value 10','get 1 2 3 value 10','get 1 2 3 4 value 10','get 1 2 3 4 5 value 10',
        'get 1 2 3 4 5 6 7 value','get 1 2 3 4 5 6 7 8 value','get 1 2 3 4 5 6 7 8 9 value',
        'get 0 0 7 20 value','get 0 0 7 20 value "initial"','get value 0 0 7 20',
        'get number "prompt"','get value,10,0','get 1,2,3,4,value']
    if extended:
        bodies += ['get value '+arg for arg in ['0','1','80','81','255','256','-1','32767','32768','65535','10L','10.0','number','wide','realnum','failure','"10"','ON','(10)','number+1',',','10,',',10,','10 20']]
        bodies += ['get '+arg for arg in ['s0','i0','l0','f0','$FDATE','$NULL','failure','value+"X"','(value)','value,','10','number+1','number,10','wide,10','realnum,10']]
    rows=[dict(label=body,source='integer number\nlong wide\nfloat realnum\nstring value\nproc main\n'+body+'\nendproc\n') for body in bodies]
    if extended:
        for dtype,param in [('integer','intparm'),('long','longparm'),('float','floatparm'),('string','strparm')]:
            rows.append(dict(label='GET local '+dtype,source='proc main\n'+dtype+' target\nget target,10\nendproc\n'))
            rows.append(dict(label='GET parameter '+dtype,source='proc main\ncall worker with '+('"X"' if dtype=='string' else '0.0' if dtype=='float' else '0L' if dtype=='long' else '0')+'\nendproc\nproc worker\n'+param+' target\nget target,10\nendproc\n'))
    return rows

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--original',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--extended',action='store_true')
    args=parser.parse_args();original=args.original.resolve();out=args.output.resolve()
    assert sha(original)==COMPILER_SHA and not original.name.lower().endswith('.analysis.exe')
    assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    shutil.copyfile(original,out/'ASPCOMP.EXE');cases=corpus(args.extended);batch=['@echo off']
    for index,case in enumerate(cases):
        leaf='GT%03d'%index;case['name']=leaf;(out/(leaf+'.ASP')).write_bytes(case['source'].replace('\n','\r\n').encode('ascii'))
        batch.extend([f'ASPCOMP {leaf}.ASP >{leaf}.LOG',f'if errorlevel 1 goto E{leaf}',f'echo ZERO>{leaf}.RC',f'goto D{leaf}',f':E{leaf}',f'echo NONZERO>{leaf}.RC',f':D{leaf}'])
    batch+=['echo COMPLETE>DONE.TXT','exit'];(out/'RUN.BAT').write_bytes(('\r\n'.join(batch)+'\r\n').encode('ascii'))
    (out/'dosbox.conf').write_text('[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=386\ncycles=fixed 12000\n[mixer]\nnosound=true\n[autoexec]\nmount c "'+str(out)+'"\nc:\nset PCPLUS=\nRUN.BAT\n')
    with (out/'dosbox.log').open('w') as log:
        subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=60)
    assert (out/'DONE.TXT').read_text().strip()=='COMPLETE'
    rows=[]
    for case in cases:
        leaf=case['name'];log=(out/(leaf+'.LOG')).read_bytes();compiled=out/(leaf+'.ASX')
        accepted=b'Script file successfully compiled!' in log
        assert accepted==compiled.exists()==((out/(leaf+'.RC')).read_text().strip()=='ZERO')
        row=dict(**case,accepted=accepted,errors=[line for line in log.decode('cp437').splitlines() if line.startswith('Error')],log_sha256=hashlib.sha256(log).hexdigest())
        if accepted:row.update(hex=compiled.read_bytes().hex(' '),asx_sha256=sha(compiled))
        rows.append(row);print(case['label'],'ACCEPT' if accepted else row['errors'],flush=True)
    assert sha(original)==sha(out/'ASPCOMP.EXE')==COMPILER_SHA
    result=dict(passed=True,compiler_sha256=COMPILER_SHA,cases=rows,sources={'standalone/observe_aspect_get_compiler.py':sha(Path(__file__))},
        scope=__doc__+' Unmodified original compiler on owned DOS386 media; no private source, runtime execution or maintained grammar claim. Output lives only under ignored build.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':main()
