#!/usr/bin/env python3
"""Reproduce a source-built PCKEYMAP from only its declared public inputs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args();build=args.build.resolve();out=args.output.resolve()
    assert build.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build') and not out.exists()
    manifest=json.loads((build/'result.json').read_text())
    assert manifest['passed'] and manifest['original_inputs']==[] and sha(build/'PCKEYMAP.EXE')==manifest['binary_sha256']
    fresh=out/'source';fresh.mkdir(parents=True)
    for name,digest in manifest['sources'].items():
        path=Path(name)
        assert not path.is_absolute() and '..' not in path.parts and path.parts[0] in ('src','standalone','reconstruction')
        assert path.suffix.lower() in ('.c','.h','.py','.asm','.inc','.json') and sha(ROOT/path)==digest,name
        target=fresh/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/path,target)
    env=dict(os.environ,GIT_CEILING_DIRECTORIES=str(out))
    assert subprocess.run(['git','rev-parse','--show-toplevel'],cwd=fresh,env=env,capture_output=True).returncode
    with (out/'build.log').open('w') as log:
        subprocess.run([sys.executable,'standalone/build_keymap_helper.py','--output','build/helper'],cwd=fresh,env=env,stdout=log,stderr=log,check=True)
    actual=json.loads((fresh/'build/helper/result.json').read_text())
    assert actual['binary_sha256']==manifest['binary_sha256']==sha(fresh/'build/helper/PCKEYMAP.EXE')
    assert actual['sources']==manifest['sources']
    for name,digest in manifest['sources'].items():assert sha(ROOT/name)==sha(fresh/name)==digest,name
    result=dict(passed=True,binary_sha256=actual['binary_sha256'],source_count=len(manifest['sources']),sources=manifest['sources'],
                prover_sha256=sha(Path(__file__)),original_inputs=[],ancestor_git_unavailable=True,
                scope='Exact helper from declared public inputs in an empty export; outer pinned Nix supplies tools. Runtime/parent/BBS/physical acceptance is separate.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS helper source export:',result['source_count'],'inputs; exact binary')


if __name__=='__main__':main()
