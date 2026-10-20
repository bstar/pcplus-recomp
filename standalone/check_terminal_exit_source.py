#!/usr/bin/env python3
"""Reproduce guarded/probe/default terminals in a fresh source-only tree."""
import argparse,json,re,shutil,subprocess,sys,uuid
from pathlib import Path
from build_aspect_process import ROOT,sha
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--label',default='source-'+uuid.uuid4().hex)
    args=p.parse_args();assert re.fullmatch(r'[A-Za-z0-9_-]+',args.label)
    folder=ROOT/'build/terminal-exit-source'/args.label;folder.mkdir(parents=True,exist_ok=False)
    fresh=folder/'source';sources={};products=[]
    for mouse in [False,True]:
        base='terminal-exit-mouse' if mouse else 'terminal-exit'
        products.extend([base,*[base+'-probe-'+str(mode) for mode in range(4)]])
    products+=['terminal','terminal-process','terminal-mouse','terminal-mouse-process']
    for name in products:
        m=json.loads((ROOT/'build'/name/'manifest.json').read_text())
        assert m['binary_sha256']==sha(ROOT/'build'/name/'TERMINAL.EXE')
        for n,h in m['sources'].items():assert n not in sources or sources[n]==h;sources[n]=h
    sources['standalone/build_terminal_exit.py']=sha(ROOT/'standalone/build_terminal_exit.py')
    for n,h in sources.items():
        path=Path(n);assert not path.is_absolute() and '..' not in path.parts and path.parts[0] not in ['analysis','build']
        assert sha(ROOT/path)==h
        target=fresh/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/path,target)
    code='''import sys,subprocess
subprocess.run([sys.executable,'standalone/build_terminal_exit.py'],check=True)
for flags in [[],['--external-render'],['--mouse'],['--mouse','--external-render']]:
 subprocess.run([sys.executable,'standalone/build_terminal.py',*flags],check=True)
'''
    with (folder/'build.log').open('w') as log:
        run=subprocess.run([sys.executable,'-c',code],cwd=fresh,stdout=log,stderr=log,timeout=180)
    compared={n:dict(expected=sha(ROOT/'build'/n/'TERMINAL.EXE'),actual=sha(fresh/'build'/n/'TERMINAL.EXE')) for n in products} if not run.returncode else {}
    for n,h in sources.items():assert sha(ROOT/n)==h,n
    result=dict(passed=not run.returncode and len(compared)==14 and all(v['expected']==v['actual'] for v in compared.values()),
        products=compared,sources=sources,original_inputs=[],exit_code=run.returncode,checker_sha256=sha(Path(__file__)),build_log_sha256=sha(folder/'build.log'))
    (folder/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('Fresh terminal exit:',len(compared),'products','PASS' if result['passed'] else 'FAIL',folder)
    return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
