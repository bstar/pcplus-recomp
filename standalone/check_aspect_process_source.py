#!/usr/bin/env python3
"""Rebuild the experimental ASPECT/process and compiler from a blank source tree."""
import argparse,json,re,shutil,subprocess,sys,uuid
from pathlib import Path
from build_aspect_process import ROOT,OUT,sha
import build_aspect_process as process
import build_aspect_runner as runner
import build_aspect_compiler_dos as dos_compiler


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--label',default='source-'+uuid.uuid4().hex)
    args=parser.parse_args();assert re.fullmatch(r'[A-Za-z0-9_-]+',args.label)
    folder=OUT/'source-proofs'/args.label;folder.mkdir(parents=True,exist_ok=False);source=folder/'source'
    if not (OUT/'manifest.json').exists():process.main(ROOT/'standalone/aspect_process_diagnostic.c')
    if not (ROOT/'build/aspect-compiler-dos/manifest.json').exists():dos_compiler.main()
    if not (ROOT/'build/aspect-runner/ASPECT.EXE').exists():runner.main()
    manifest=json.loads((OUT/'manifest.json').read_text());compiler=json.loads((ROOT/'build/aspect-compiler-dos/manifest.json').read_text())
    sources={**manifest['sources'],**compiler['sources']}
    for name,digest in sources.items():
        path=Path(name);assert not path.is_absolute() and '..' not in path.parts and path.parts[0] not in ('analysis','build')
        assert sha(ROOT/path)==digest,name
        target=source/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/path,target)
    assert not (source/'analysis').exists() and not (source/'build').exists()
    code='import build_aspect_compiler_dos as c;import build_aspect_process as p;import build_aspect_runner as r;from pathlib import Path;c.main();p.main(Path.cwd()/'+repr(manifest['main_source'])+');r.main()'
    with (folder/'build.log').open('w') as log:
        command=[sys.executable,'-c','import sys;sys.path.insert(0,"standalone");'+code]
        result=subprocess.run(command,cwd=source,stdout=log,stderr=log,timeout=120)
    products=['aspect-process/ASPECT.EXE','aspect-runner/ASPECT.EXE','aspect-compiler-dos/ASPCOMP.EXE','native-program/PROGRAM.EXE',
        'native-program/OWN1.COM','native-program/OWN2.COM','native-display/DISPLAY.EXE',
        'native-display/VIDEO.COM','process-serial/PSERIAL.EXE','process-serial/UART1.COM','process-serial/UART2.COM',
        'native-process/NATIVE.EXE','native-process/NAMES.EXE']
    products+=['native-process/'+name for name in json.loads((ROOT/'build/native-process/manifest.json').read_text())['children']]
    compared={}
    if not result.returncode:
        for name in products:compared[name]=dict(expected=sha(ROOT/'build'/name),actual=sha(source/'build'/name))
    report=dict(passed=not result.returncode and len(compared)==len(products) and all(r['expected']==r['actual'] for r in compared.values()),
        original_inputs=[],source_files=len(sources),sources=sources,products=compared,exit_code=result.returncode,
        manifest_sha256=sha(OUT/'manifest.json'),checker_sha256=sha(Path(__file__)),build_log_sha256=sha(folder/'build.log'),
        scope='Fresh experimental ASPECT/PROGRAM and DOS compiler rebuild from declared source inputs. Production dispatch and whole-application/hardware gates remain unchanged.')
    (folder/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('Fresh ASPECT process source:',len(compared),'products','PASS' if report['passed'] else 'FAIL');print(folder)
    return 0 if report['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
