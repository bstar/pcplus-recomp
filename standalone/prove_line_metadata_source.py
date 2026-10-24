#!/usr/bin/env python3
"""Rebuild the changed live terminal and retain the diagnostic-glob counterexample."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--viewport',action='store_true',help='Run the live pane oracle in the fresh tree and reject a build without its DS correction')
    args=parser.parse_args();out=args.output.resolve()
    assert out.is_relative_to(ROOT/'build') and not out.exists()
    base=ROOT/'build/terminal';manifest=json.loads((base/'manifest.json').read_text())
    assert sha(base/'TERMINAL.EXE')==manifest['binary_sha256']
    # Include the separately owned diagnostic so a permissive glob cannot
    # accidentally pass merely because the fresh tree omitted its source.
    inputs={**manifest['sources'],'reconstruction/modes/width_request.asm':sha(ROOT/'reconstruction/modes/width_request.asm')}
    if args.viewport:
        for name in ['check_viewport_live.py','check_line_edit_live.py','check_transport.py','check_scroll.py','dos_image.py']:
            inputs['standalone/'+name]=sha(ROOT/'standalone'/name)
    fresh=out/'source'
    for name,digest in inputs.items():
        path=Path(name)
        assert not path.is_absolute() and '..' not in path.parts
        assert path.parts[0] not in ('build','analysis','original','originals','install')
        assert path.suffix.lower() not in ('.exe','.obj','.o','.img','.prm','.dir','.xlt')
        assert sha(ROOT/path)==digest
        target=fresh/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/path,target)
    negative=out/'negative-source';shutil.copytree(fresh,negative)
    builder=negative/'standalone/build_terminal.py';text=builder.read_text()
    excluded=" ROOT/'reconstruction/modes/width_request.asm')"
    assert text.count(excluded)==1
    builder.write_text(text.replace(excluded,')'))
    with(out/'negative-build.log').open('w')as log:
        failed=subprocess.run([sys.executable,'standalone/build_terminal.py'],cwd=negative,
            stdout=log,stderr=log,timeout=90)
    log=(out/'negative-build.log').read_text()
    assert failed.returncode and 'reconstruction/modes/width_request.asm:9: error:' in log
    assert 'ORG 0x2a6e' in log and not(negative/'build/terminal/TERMINAL.EXE').exists()
    cga_result=None
    if args.viewport:
        cga=out/'foreign-ds-source';shutil.copytree(fresh,cga)
        cga_builder=cga/'standalone/build_terminal.py';text=cga_builder.read_text()
        flag="'-DVIEWPORT_PRESERVE_DS',";assert text.count(flag)==1
        cga_builder.write_text(text.replace(flag,''))
        with(out/'foreign-ds-build.log').open('w')as log:
            subprocess.run([sys.executable,'standalone/build_terminal.py'],cwd=cga,
                stdout=log,stderr=log,check=True,timeout=90)
        with(out/'foreign-ds-check.log').open('w')as log:
            bad=subprocess.run([sys.executable,'standalone/check_viewport_live.py'],cwd=cga,
                stdout=log,stderr=log,timeout=90)
        assert bad.returncode and 'Viewport hardware callback inherited foreign DS' in (out/'foreign-ds-check.log').read_text()
        cga_result=dict(rejected=True,exit_code=bad.returncode,binary_sha256=sha(cga/'build/terminal/TERMINAL.EXE'),
            builder_sha256=sha(cga_builder),build_log_sha256=sha(out/'foreign-ds-build.log'),check_log_sha256=sha(out/'foreign-ds-check.log'))
    assert not(fresh/'build').exists() and not(fresh/'analysis').exists()
    with(out/'build.log').open('w')as log:
        subprocess.run([sys.executable,'standalone/build_terminal.py'],cwd=fresh,
            stdout=log,stderr=log,check=True,timeout=90)
    rebuilt=fresh/'build/terminal'
    assert sha(rebuilt/'TERMINAL.EXE')==manifest['binary_sha256']
    assert json.loads((rebuilt/'manifest.json').read_text())['sources']==manifest['sources']
    if args.viewport:
        with(out/'viewport-check.log').open('w')as log:
            subprocess.run([sys.executable,'standalone/check_viewport_live.py'],cwd=fresh,
                stdout=log,stderr=log,check=True,timeout=90)
        assert json.loads((rebuilt/'viewport-live-checks.json').read_text())['passed']
    for name,digest in inputs.items():assert sha(ROOT/name)==sha(fresh/name)==digest
    result=dict(passed=True,binary_sha256=manifest['binary_sha256'],source_files=len(inputs),
        sources=inputs,original_inputs=[],negative_exit_code=failed.returncode,
        negative_builder_sha256=sha(builder),negative_log_sha256=sha(out/'negative-build.log'),
        build_log_sha256=sha(out/'build.log'),checker_sha256=sha(Path(__file__)),
        scope='Empty-tree live terminal reproduction with native width diagnostic source present but excluded from the application link. Removing that exclusion fails NASM before linking. No originals, existing objects, analysis databases or Git discovery.')
    if args.viewport:
        result.update(viewport_passed=True,foreign_DS_negative=cga_result,
            viewport_log_sha256=sha(out/'viewport-check.log'),viewport_report_sha256=sha(rebuilt/'viewport-live-checks.json'))
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS terminal source reproduction:',len(inputs),'sources; diagnostic-glob counterexample rejects')


if __name__=='__main__':main()
