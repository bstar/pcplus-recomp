#!/usr/bin/env python3
"""Reproduce both experimental products and normal products from source only."""
import argparse,json,re,shutil,subprocess,sys,uuid
from pathlib import Path
from build_aspect_process import ROOT,sha


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--label',default='source-'+uuid.uuid4().hex)
    args=parser.parse_args();assert re.fullmatch(r'[A-Za-z0-9_-]+',args.label)
    folder=ROOT/'build/aspect-parent-process/source-proofs'/args.label;folder.mkdir(parents=True,exist_ok=False)
    source=folder/'source';sources={}
    for name in ('terminal-process','terminal-mouse','aspect-process-parent','aspect-compiler-dos','aspect-runner'):
        manifest=json.loads((ROOT/'build'/name/'manifest.json').read_text())
        for path,digest in manifest['sources'].items():
            assert path not in sources or sources[path]==digest,path
            sources[path]=digest
    for name,digest in sources.items():
        path=Path(name);assert not path.is_absolute() and '..' not in path.parts and path.parts[0] not in ('analysis','build')
        assert sha(ROOT/path)==digest,name
        target=source/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/path,target)
    assert not (source/'build').exists() and not (source/'analysis').exists()
    code='''import sys,subprocess
sys.path.insert(0,'standalone')
import build_aspect_compiler_dos as compiler
import build_aspect_process as process
import build_aspect_runner as runner
compiler.main();process.main(parent_render=True);runner.main()
subprocess.run([sys.executable,'standalone/build_terminal.py','--external-render'],check=True)
subprocess.run([sys.executable,'standalone/build_terminal.py'],check=True)
subprocess.run([sys.executable,'standalone/build_terminal.py','--mouse'],check=True)
'''
    with (folder/'build.log').open('w') as log:result=subprocess.run([sys.executable,'-c',code],cwd=source,stdout=log,stderr=log,timeout=180)
    products=['aspect-process-parent/ASPECT.EXE','aspect-runner/ASPECT.EXE','aspect-compiler-dos/ASPCOMP.EXE',
        'terminal-process/TERMINAL.EXE','terminal/TERMINAL.EXE','terminal-mouse/TERMINAL.EXE','native-program/PROGRAM.EXE','native-program/OWN1.COM','native-program/OWN2.COM',
        'native-display/DISPLAY.EXE','native-display/VIDEO.COM','process-serial/PSERIAL.EXE','process-serial/UART1.COM','process-serial/UART2.COM',
        'native-process/NATIVE.EXE','native-process/NAMES.EXE']
    products+=['native-process/'+name for name in json.loads((ROOT/'build/native-process/manifest.json').read_text())['children']]
    compared={name:dict(expected=sha(ROOT/'build'/name),actual=sha(source/'build'/name)) for name in products} if not result.returncode else {}
    report=dict(passed=not result.returncode and len(compared)==26 and all(p['expected']==p['actual'] for p in compared.values()),
        original_inputs=[],source_files=len(sources),sources=sources,products=compared,exit_code=result.returncode,
        checker_sha256=sha(Path(__file__)),log_sha256=sha(folder/'build.log'),
        scope='Fresh declared-source tree; experimental capability11 parent/child, normal capability10 keyboard/mouse products, compiler and20 process components. No originals, existing objects or REA databases.')
    (folder/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('Fresh attached PROGRAM source:',len(compared),'products','PASS' if report['passed'] else 'FAIL');print(folder)
    return 0 if report['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
