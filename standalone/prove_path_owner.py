#!/usr/bin/env python3
"""Reproduce the path diagnostic in an empty source tree without originals/Git."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--program',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 binary=a.program.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 m=json.loads(binary.with_name('manifest.json').read_text());assert sha(binary)==m['binary_sha256']
 fresh=out/'source';fresh.mkdir(parents=True)
 for n,h in m['sources'].items():
  relative=Path(n);assert not relative.is_absolute() and '..' not in relative.parts
  assert relative.parts[0] not in ('analysis','build','originals','install','.git')
  assert relative.suffix not in ('.exe','.obj','.com','.prm','.img') and sha(ROOT/n)==h
  target=fresh/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/n,target)
 env=dict(os.environ,GIT_CEILING_DIRECTORIES=str(out))
 assert subprocess.run(['git','rev-parse','--show-toplevel'],cwd=fresh,env=env,capture_output=True).returncode
 with (out/'build.log').open('w') as log:
  subprocess.run([sys.executable,'standalone/build_path_owner.py','--output','build/rebuilt'],cwd=fresh,env=env,stdout=log,stderr=log,check=True,timeout=120)
 rebuilt=fresh/'build/rebuilt/PATH.EXE';assert sha(rebuilt)==sha(binary)
 r={'passed':True,'program_sha256':sha(binary),'source_count':len(m['sources']),'original_inputs':[],
  'ancestor_git_unavailable':True,'sources':m['sources'],'proof_checker_sha256':sha(Path(__file__)),
  'toolchain':{n:sha(ROOT/n) for n in ('nix/flake.nix','nix/flake.lock','tools/dev')},'scope':__doc__}
 (out/'result.json').write_text(json.dumps(r,indent=2)+'\n');print('PASS exact source-only path diagnostic:',len(m['sources']),'inputs')

if __name__=='__main__':main()
