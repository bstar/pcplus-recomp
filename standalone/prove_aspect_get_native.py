#!/usr/bin/env python3
"""Rebuild GET component/filter diagnostic from only declared public inputs."""
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
    parser.add_argument('--build',required=True,type=Path);parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args();build=args.build.resolve();out=args.output.resolve()
    assert build.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build') and not out.exists()
    proof=json.loads((build/'result.json').read_text());assert proof['passed'] and proof['original_inputs']==[]
    out.mkdir(parents=True);fresh=out/'source';fresh.mkdir()
    for name,digest in proof['sources'].items():
        p=Path(name);assert not p.is_absolute() and '..' not in p.parts and p.parts[0] in ('src','standalone','reconstruction')
        assert p.suffix.lower() in ('.asm','.inc','.c','.json','.py') and sha(ROOT/p)==digest
        target=fresh/p;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/p,target)
    env=dict(os.environ,GIT_CEILING_DIRECTORIES=str(out))
    assert subprocess.run(['git','rev-parse','--show-toplevel'],cwd=fresh,env=env,capture_output=True).returncode
    with (out/'build.log').open('w') as log:
        subprocess.run([sys.executable,'standalone/build_aspect_get_native.py','--output','build/check'],cwd=fresh,env=env,stdout=log,stderr=log,check=True)
    actual=json.loads((fresh/'build/check/result.json').read_text())
    assert actual['passed'] and actual['sources']==proof['sources']
    for key in ('native_sha256','diagnostic_sha256','transcript'):assert actual[key]==proof[key],key
    for name,digest in proof['sources'].items():assert sha(ROOT/name)==sha(fresh/name)==digest
    result=dict(passed=True,source_count=len(proof['sources']),native_sha256=actual['native_sha256'],diagnostic_sha256=actual['diagnostic_sha256'],transcript=actual['transcript'],original_inputs=[],ancestor_git_unavailable=True,sources=proof['sources'],prover_sha256=sha(Path(__file__)),
        scope=__doc__+' Exact flat/linked DOS binaries and all65536 numeric-filter cases; other GET services are unexecuted stubs. Outer pinned Nix supplies tools; no original/runtime/UI integration claim.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS GET source export:',result['source_count'],'inputs; exact binaries/filter output')

if __name__=='__main__':main()
