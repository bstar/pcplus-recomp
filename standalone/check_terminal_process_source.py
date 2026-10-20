#!/usr/bin/env python3
"""Reproduce banked terminals/backend and their unbanked controls from source."""
import argparse,json,re,shutil,subprocess,sys,uuid
from pathlib import Path
from build_aspect_process import ROOT,sha
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--label',default='source-'+uuid.uuid4().hex)
    args=p.parse_args();assert re.fullmatch(r'[A-Za-z0-9_-]+',args.label)
    folder=ROOT/'build/terminal-process-source'/args.label;folder.mkdir(parents=True,exist_ok=False);fresh=folder/'source'
    sources={};products=[]
    terminals=['terminal-process-bank','terminal-process-bank-mouse','terminal','terminal-process','terminal-mouse','terminal-mouse-process','terminal-exit','terminal-exit-mouse']
    terminals += [base+'-probe-'+str(m) for base in ['terminal-process-bank','terminal-process-bank-mouse'] for m in range(4)]
    for name in terminals:
        manifest=json.loads((ROOT/'build'/name/'manifest.json').read_text());products.append(name+'/TERMINAL.EXE')
        for n,h in manifest['sources'].items():assert n not in sources or sources[n]==h;sources[n]=h
    for name in ['process','process-bank']:
        manifest=json.loads((ROOT/'build'/name/'manifest.json').read_text())
        products.extend(name+'/'+n for n in manifest['outputs'])
        for n,h in manifest['sources'].items():assert n not in sources or sources[n]==h;sources[n]=h
    for n,h in sources.items():
        path=Path(n);assert not path.is_absolute() and '..' not in path.parts and path.parts[0] not in ['build','analysis'];assert sha(ROOT/path)==h,n
        target=fresh/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/path,target)
    code='''import sys,subprocess
for flags in [[],['--external-render'],['--mouse'],['--mouse','--external-render'],
 ['--external-render','--exit-guard'],['--external-render','--exit-guard','--mouse'],
 ['--external-render','--exit-guard','--process-bank'],['--external-render','--exit-guard','--process-bank','--mouse']]:
 subprocess.run([sys.executable,'standalone/build_terminal.py',*flags],check=True)
for mouse in [False,True]:
 for mode in range(4):
  subprocess.run([sys.executable,'standalone/build_terminal.py','--external-render','--exit-guard','--process-bank',*(['--mouse'] if mouse else []),'--exit-probe',str(mode)],check=True)
for flags in [[],['--banked']]:
 subprocess.run([sys.executable,'standalone/build_process.py',*flags],check=True)
'''
    with (folder/'build.log').open('w') as log:run=subprocess.run([sys.executable,'-c',code],cwd=fresh,stdout=log,stderr=log,timeout=180)
    compared={n:dict(expected=sha(ROOT/'build'/n),actual=sha(fresh/'build'/n)) for n in products} if not run.returncode else {}
    for n,h in sources.items():assert sha(ROOT/n)==h,n
    report=dict(passed=not run.returncode and len(compared)==22 and all(v['expected']==v['actual'] for v in compared.values()),
        sources=sources,products=compared,exit_code=run.returncode,original_inputs=[],checker_sha256=sha(Path(__file__)),build_log_sha256=sha(folder/'build.log'))
    (folder/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('Fresh process banks:',len(compared),'products','PASS' if report['passed'] else 'FAIL',folder)
    return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
