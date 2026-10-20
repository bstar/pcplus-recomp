#!/usr/bin/env python3
"""Validate ordinary exit, recovery and post-exit residency under memory pressure."""
import argparse,json,os,re,subprocess,sys,uuid
from pathlib import Path
from build_exit_owner import ROOT,OUT,sha
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--label',default='run-'+uuid.uuid4().hex)
    parser.add_argument('--case',action='append',choices=[m+str(f) for m in 'NRQDPL' for f in [0,1]])
    parser.add_argument('--aspect',action='store_true')
    args=parser.parse_args();assert re.fullmatch(r'[A-Za-z0-9_-]+',args.label)
    checker=sha(Path(__file__))
    run=(ROOT/'build/aspect-exit-break' if args.aspect else OUT)/'runs'/args.label;run.mkdir(parents=True,exist_ok=False)
    manifest=json.loads((OUT/'manifest.json').read_text())
    products={n:(OUT/n) for n in manifest['products']}
    if args.aspect:
        assert not args.case or args.case==['Q0']
        cli=ROOT/'build/aspect-exit-break';cm=json.loads((cli/'manifest.json').read_text())
        assert sha(cli/'ASPECT.EXE')==cm['binary_sha256']
        manifest['sources'].update(cm['sources'])
        manifest['scope']=cm['scope']
        manifest['sources']['src/aspect/compiler.py']=sha(ROOT/'src/aspect/compiler.py')
        manifest['sources']['standalone/exit_idle.asm']=sha(ROOT/'standalone/exit_idle.asm')
        manifest['products']={'EXITPAR.EXE':manifest['products']['EXITPAR.EXE'],'ASPECT.EXE':cm['binary_sha256']}
        products={'EXITPAR.EXE':OUT/'EXITPAR.EXE','ASPECT.EXE':cli/'ASPECT.EXE'}
    for name,digest in manifest['sources'].items():assert sha(ROOT/name)==digest,name
    results=[]
    for mode in (['Q0'] if args.aspect else args.case or [m+str(f) for m in 'NRQDPL' for f in [0,1]]):
        folder=run/mode;folder.mkdir()
        for name,digest in manifest['products'].items():
            assert sha(products[name])==digest;(folder/name).write_bytes(products[name].read_bytes())
        if args.aspect:
            sys.path.insert(0,str(ROOT/'src/aspect'));from compiler import compile_source
            source='proc main\nrun "IDLE.COM" WAIT\nendproc\n'
            (folder/'HOLD.ASP').write_text(source);(folder/'HOLD.ASX').write_bytes(compile_source(source))
            subprocess.run(['nasm','-fbin',str(ROOT/'standalone/exit_idle.asm'),'-o',str(folder/'IDLE.COM')],check=True)
        command=mode+(' ASPECT.EXE HOLD.ASX' if args.aspect else '')
        (folder/'CHECK.BAT').write_text('@echo off\nEXITPAR.EXE '+command+' >OUTPUT.TXT\nif errorlevel 1 goto bad\necho PASS>RESULT.TXT\ngoto done\n:bad\necho FAIL>RESULT.TXT\n:done\nexit\n')
        config=f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
cycles=max
[mixer]
nosound=true
[autoexec]
mount c "{folder}"
c:
CHECK.BAT
exit
'''
        (folder/'dosbox.conf').write_text(config)
        with (folder/'dosbox.log').open('w') as log:
            subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(folder/'dosbox.conf')],
                stdout=log,stderr=log,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),check=True,timeout=45)
        output=(folder/'OUTPUT.TXT').read_text()
        assert (folder/'RESULT.TXT').read_text().strip()=='PASS',output
        match=re.fullmatch(r'EXIT OWNER '+mode+r' checks=(\d+) failures=0 status=(\d+)\s*',output);assert match,output
        results.append(dict(case=mode,checks=int(match[1]),status=int(match[2]),
            artifacts={p.name:sha(p) for p in folder.iterdir() if p.is_file()}))
        print(mode,'PASS',match[1],'checks; raw DOS status',match[2],flush=True)
    for name,digest in manifest['sources'].items():assert sha(ROOT/name)==digest,name
    assert sha(Path(__file__))==checker
    receipt=dict(passed=True,actual_ASPECT_CLI=args.aspect,cases=results,sources=manifest['sources'],products=manifest['products'],
        checker_sha256=sha(Path(__file__)),scope=manifest['scope'])
    (run/'result.json').write_text(json.dumps(receipt,indent=2)+'\n')
if __name__=='__main__':main()
