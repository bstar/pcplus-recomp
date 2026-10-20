#!/usr/bin/env python3
"""Rebuild the composed component in a fresh tree containing only source inputs."""
import argparse,json,re,shutil,subprocess,sys,uuid
from pathlib import Path
from build_native_program import ROOT,OUT,sha


def main():
    global OUT
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label',default='source-'+uuid.uuid4().hex)
    parser.add_argument('--break-owner',action='store_true')
    args=parser.parse_args();assert re.fullmatch(r'[A-Za-z0-9_-]+',args.label)
    if args.break_owner:OUT=ROOT/'build/native-program-break'
    folder=OUT/'source-proofs'/args.label;folder.mkdir(parents=True,exist_ok=False)
    source=folder/'source';manifest=json.loads((OUT/'manifest.json').read_text())
    assert bool(manifest.get('break_owner'))==args.break_owner
    for name,digest in manifest['sources'].items():
        path=Path(name);assert not path.is_absolute() and '..' not in path.parts
        assert path.parts[0] not in ('analysis','build') and sha(ROOT/path)==digest
        dest=source/path;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/path,dest)
    assert not (source/'analysis').exists() and not (source/'build').exists()
    with (folder/'build.log').open('w') as log:
        result=subprocess.run([sys.executable,str(source/'standalone/build_native_program.py'),
            *(['--break-owner'] if args.break_owner else [])],
            cwd=source,stdout=log,stderr=log,timeout=120)
    products=['native-program/PROGRAM.EXE','native-program/OWN1.COM','native-program/OWN2.COM',
        'native-display/DISPLAY.EXE','native-display/VIDEO.COM','process-serial/PSERIAL.EXE',
        'process-serial/UART1.COM','process-serial/UART2.COM','native-process/NATIVE.EXE','native-process/NAMES.EXE']
    products += ['native-process/'+name for name in json.loads((ROOT/'build/native-process/manifest.json').read_text())['children']]
    if args.break_owner:
        products=[p.replace('native-program/','native-program-break/') for p in products]
        products += ['break-owner/BRKOWN.EXE','break-owner/BRKCHLD.COM']
    compared={}
    if not result.returncode:
        for name in products:
            compiled=source/'build'/name
            compared[name]=dict(expected=sha(ROOT/'build'/name),actual=sha(compiled))
    report=dict(passed=not result.returncode and len(compared)==len(products) and
        all(item['expected']==item['actual'] for item in compared.values()),
        component_only=True,original_inputs=[],source_files=len(manifest['sources']),
        sources=manifest['sources'],products=compared,exit_code=result.returncode,
        manifest_sha256=sha(OUT/'manifest.json'),checker_sha256=sha(Path(__file__)),
        build_log_sha256=sha(folder/'build.log'),
        scope='Fresh composed-component rebuild from declared source inputs, without analysis or prior build artifacts; not a whole-application reproducibility claim.')
    (folder/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Fresh source rebuild:',len(compared),'products', 'PASS' if report['passed'] else 'FAIL')
    print(folder)
    return 0 if report['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
