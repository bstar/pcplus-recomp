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
    args=parser.parse_args();out=args.output.resolve()
    assert out.is_relative_to(ROOT/'build') and not out.exists()
    base=ROOT/'build/terminal';manifest=json.loads((base/'manifest.json').read_text())
    assert sha(base/'TERMINAL.EXE')==manifest['binary_sha256']
    # Include the separately owned diagnostic so a permissive glob cannot
    # accidentally pass merely because the fresh tree omitted its source.
    inputs={**manifest['sources'],'reconstruction/modes/width_request.asm':sha(ROOT/'reconstruction/modes/width_request.asm')}
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
    assert not(fresh/'build').exists() and not(fresh/'analysis').exists()
    with(out/'build.log').open('w')as log:
        subprocess.run([sys.executable,'standalone/build_terminal.py'],cwd=fresh,
            stdout=log,stderr=log,check=True,timeout=90)
    rebuilt=fresh/'build/terminal'
    assert sha(rebuilt/'TERMINAL.EXE')==manifest['binary_sha256']
    assert json.loads((rebuilt/'manifest.json').read_text())['sources']==manifest['sources']
    for name,digest in inputs.items():assert sha(ROOT/name)==sha(fresh/name)==digest
    result=dict(passed=True,binary_sha256=manifest['binary_sha256'],source_files=len(inputs),
        sources=inputs,original_inputs=[],negative_exit_code=failed.returncode,
        negative_builder_sha256=sha(builder),negative_log_sha256=sha(out/'negative-build.log'),
        build_log_sha256=sha(out/'build.log'),checker_sha256=sha(Path(__file__)),
        scope='Empty-tree live terminal reproduction with native width diagnostic source present but excluded from the application link. Removing that exclusion fails NASM before linking. No originals, existing objects, analysis databases or Git discovery.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS terminal source reproduction:',len(inputs),'sources; diagnostic-glob counterexample rejects')


if __name__=='__main__':main()
