#!/usr/bin/env python3
"""Reproduce the guarded CLI, fault/exit probes and process products without originals."""
import argparse,json,re,shutil,subprocess,sys,uuid
from pathlib import Path
from build_exit_owner import ROOT,sha
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--label',default='source-'+uuid.uuid4().hex)
    parser.add_argument('--attached',action='store_true')
    parser.add_argument('--mouse',action='store_true')
    args=parser.parse_args();assert re.fullmatch(r'[A-Za-z0-9_-]+',args.label)
    if args.mouse:assert args.attached
    folder=ROOT/'build/exit-owner/source-proofs'/args.label;folder.mkdir(parents=True,exist_ok=False)
    fresh=folder/'source';sources={}
    components=['exit-owner','aspect-process-break','aspect-exit-break','aspect-fault-break','terminal-process','aspect-compiler-dos']
    if args.attached:components+=['aspect-exit-parent','terminal']
    if args.mouse:components+=['terminal-mouse','terminal-mouse-process']
    for name in components:
        manifest=json.loads((ROOT/'build'/name/'manifest.json').read_text())
        for path,digest in manifest['sources'].items():
            assert path not in sources or sources[path]==digest,path;sources[path]=digest
    for name,digest in sources.items():
        path=Path(name);assert not path.is_absolute() and '..' not in path.parts
        assert path.parts[0] not in ['analysis','build'] and sha(ROOT/path)==digest,name
        target=fresh/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/path,target)
    assert not (fresh/'analysis').exists() and not (fresh/'build').exists()
    code='''import sys,subprocess
from pathlib import Path
sys.path.insert(0,'standalone')
import build_exit_owner as exits
import build_aspect_process as process
import build_aspect_exit_probe as probe
import build_aspect_compiler_dos as compiler
root=Path.cwd()
exits.main()
process.main(parent_render=True,output=root/'build/aspect-process-break',break_owner=True)
probe.main()
process.main(root/'standalone/aspect_fault_driver.c',parent_render=True,output=root/'build/aspect-fault-break',break_owner=True)
compiler.main()
subprocess.run([sys.executable,'standalone/build_terminal.py','--external-render'],check=True)
'''
    if args.attached:code+="probe.main(attached=True)\nsubprocess.run([sys.executable,'standalone/build_terminal.py'],check=True)\n"
    if args.mouse:
        for flags in [['--mouse'],['--mouse','--external-render']]:
            code+=f"subprocess.run([sys.executable,'standalone/build_terminal.py',*{flags!r}],check=True)\n"
    with (folder/'build.log').open('w') as log:
        result=subprocess.run([sys.executable,'-c',code],cwd=fresh,stdout=log,stderr=log,timeout=180)
    products=['exit-owner/EXITPAR.EXE','exit-owner/EXITKID.EXE','aspect-process-break/ASPECT.EXE',
        'aspect-exit-break/ASPECT.EXE','aspect-fault-break/ASPECT.EXE','aspect-compiler-dos/ASPCOMP.EXE',
        'terminal-process/TERMINAL.EXE','break-owner-far/BRKOWN.EXE','break-owner-far/BRKCHLD.COM',
        'native-program/PROGRAM.EXE','native-program/OWN1.COM','native-program/OWN2.COM',
        'native-display/DISPLAY.EXE','native-display/VIDEO.COM','process-serial/PSERIAL.EXE',
        'process-serial/UART1.COM','process-serial/UART2.COM','native-process/NATIVE.EXE','native-process/NAMES.EXE']
    products+=['native-process/'+n for n in json.loads((ROOT/'build/native-process/manifest.json').read_text())['children']]
    if args.attached:products+=['aspect-exit-parent/ASPECT.EXE','terminal/TERMINAL.EXE']
    if args.mouse:products+=['terminal-mouse/TERMINAL.EXE','terminal-mouse-process/TERMINAL.EXE']
    compared={n:dict(expected=sha(ROOT/'build'/n),actual=sha(fresh/'build'/n)) for n in products} if not result.returncode else {}
    report=dict(passed=result.returncode==0 and len(compared)==len(products) and
        all(p['expected']==p['actual'] for p in compared.values()),exit_code=result.returncode,
        attached=args.attached,mouse=args.mouse,source_files=len(sources),sources=sources,products=compared,original_inputs=[],
        checker_sha256=sha(Path(__file__)),build_log_sha256=sha(folder/'build.log'),
        scope='Fresh declared-source tree: normal banked CLI, actual exit/fault probes, attached terminal, compiler and recovered process components. No original executable, object cache or REA database.')
    (folder/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Fresh exit source:',len(compared),'products','PASS' if report['passed'] else 'FAIL',folder)
    return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
