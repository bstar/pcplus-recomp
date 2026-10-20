#!/usr/bin/env python3
"""Rebuild the banked fault VM, attached terminal and process components from source."""
import argparse,json,re,shutil,subprocess,sys,uuid
from pathlib import Path
from build_aspect_process import ROOT,sha

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--label',default='source-'+uuid.uuid4().hex)
    args=parser.parse_args();assert re.fullmatch(r'[A-Za-z0-9_-]+',args.label)
    folder=ROOT/'build/aspect-unwind-break/source-proofs'/args.label
    folder.mkdir(parents=True,exist_ok=False);fresh=folder/'source';sources={}
    for component in ['aspect-fault-break','terminal-process']:
        manifest=json.loads((ROOT/'build'/component/'manifest.json').read_text())
        for name,digest in manifest['sources'].items():
            assert name not in sources or sources[name]==digest,name
            sources[name]=digest
    for name,digest in sources.items():
        path=Path(name)
        assert not path.is_absolute() and '..' not in path.parts and path.parts[0] not in ['analysis','build']
        assert sha(ROOT/path)==digest,name
        target=fresh/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/path,target)
    assert not (fresh/'analysis').exists() and not (fresh/'build').exists()
    code='''import sys,subprocess
from pathlib import Path
sys.path.insert(0,'standalone')
import build_aspect_process as process
root=Path.cwd()
process.main(root/'standalone/aspect_fault_driver.c',parent_render=True,output=root/'build/aspect-fault-break',break_owner=True)
subprocess.run([sys.executable,'standalone/build_terminal.py','--external-render'],check=True)
'''
    with (folder/'build.log').open('w') as log:
        result=subprocess.run([sys.executable,'-c',code],cwd=fresh,stdout=log,stderr=log,timeout=180)
    products=['aspect-fault-break/ASPECT.EXE','terminal-process/TERMINAL.EXE',
        'break-owner-far/BRKOWN.EXE','break-owner-far/BRKCHLD.COM',
        'native-program/PROGRAM.EXE','native-program/OWN1.COM','native-program/OWN2.COM',
        'native-display/DISPLAY.EXE','native-display/VIDEO.COM',
        'process-serial/PSERIAL.EXE','process-serial/UART1.COM','process-serial/UART2.COM',
        'native-process/NATIVE.EXE','native-process/NAMES.EXE']
    products+=['native-process/'+name for name in json.loads((ROOT/'build/native-process/manifest.json').read_text())['children']]
    compared={name:dict(expected=sha(ROOT/'build'/name),actual=sha(fresh/'build'/name))
              for name in products} if result.returncode==0 else {}
    report=dict(passed=result.returncode==0 and len(compared)==len(products) and
        all(p['expected']==p['actual'] for p in compared.values()),exit_code=result.returncode,
        source_files=len(sources),sources=sources,products=compared,original_inputs=[],
        checker_sha256=sha(Path(__file__)),build_log_sha256=sha(folder/'build.log'),
        scope='Fresh declared-source tree; banked full fault VM, attached terminal and process components. No original executable, prior object or REA database.')
    (folder/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Fresh banked source:',len(compared),'products','PASS' if report['passed'] else 'FAIL',folder)
    return 0 if report['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
