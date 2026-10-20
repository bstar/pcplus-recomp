#!/usr/bin/env python3
"""Reproduce twelve trap products and six unchanged controls from source."""
import argparse,json,re,shutil,subprocess,sys,uuid
from pathlib import Path
from build_aspect_process import ROOT,sha

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--label',default='source-'+uuid.uuid4().hex)
    args=p.parse_args();assert re.fullmatch(r'[A-Za-z0-9_-]+',args.label)
    folder=ROOT/'build/terminal-traps-source'/args.label
    folder.mkdir(parents=True,exist_ok=False);fresh=folder/'source'
    sources={};products=[]
    for mouse in [False,True]:
        base='terminal-traps-mouse' if mouse else 'terminal-traps'
        products.extend([base,*[base+'-probe-'+str(mode) for mode in range(5)]])
    for name in products:
        m=json.loads((ROOT/'build'/name/'manifest.json').read_text())
        assert m['binary_sha256']==sha(ROOT/'build'/name/'TERMINAL.EXE')
        for n,h in m['sources'].items():
            assert n not in sources or sources[n]==h
            sources[n]=h
    sources['standalone/build_terminal_traps.py']=sha(ROOT/'standalone/build_terminal_traps.py')
    products+=['terminal','terminal-process','terminal-mouse','terminal-mouse-process',
        'terminal-process-bank','terminal-process-bank-mouse']
    expected={n:sha(ROOT/'build'/n/'TERMINAL.EXE') for n in products}
    for n,h in sources.items():
        path=Path(n)
        assert not path.is_absolute() and '..' not in path.parts and path.parts[0] not in ['analysis','build']
        assert sha(ROOT/path)==h,n
        target=fresh/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/path,target)
    assert not (fresh/'build').exists() and not (fresh/'analysis').exists()
    assert not list(fresh.rglob('*.EXE')) and not list(fresh.rglob('*.exe'))
    code='''import sys,subprocess
subprocess.run([sys.executable,'standalone/build_terminal_traps.py'],check=True)
for flags in [[],['--external-render'],['--mouse'],['--mouse','--external-render'],
 ['--external-render','--exit-guard','--process-bank'],
 ['--external-render','--exit-guard','--process-bank','--mouse']]:
 subprocess.run([sys.executable,'standalone/build_terminal.py',*flags],check=True)
'''
    with (folder/'build.log').open('w') as log:
        run=subprocess.run([sys.executable,'-c',code],cwd=fresh,stdout=log,stderr=log,timeout=240)
    compared={n:dict(expected=expected[n],actual=sha(fresh/'build'/n/'TERMINAL.EXE')) for n in products} if not run.returncode else {}
    for n,h in sources.items():assert sha(ROOT/n)==h,n
    report=dict(passed=not run.returncode and len(compared)==18 and all(v['expected']==v['actual'] for v in compared.values()),
        products=compared,sources=sources,original_inputs=[],exit_code=run.returncode,
        checker_sha256=sha(Path(__file__)),build_log_sha256=sha(folder/'build.log'))
    (folder/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Fresh terminal traps:',len(compared),'products','PASS' if report['passed'] else 'FAIL',folder)
    return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
