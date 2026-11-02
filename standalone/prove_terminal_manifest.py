#!/usr/bin/env python3
"""Rebuild a selected terminal from declared sources in an empty, Git-free tree."""
import argparse,hashlib,json,os,shutil,subprocess,sys
from pathlib import Path
from prove_phone_log_startup_terminal import flags
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--terminal',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args();a.output=a.output.resolve();assert a.output.is_relative_to(ROOT/'build') and not a.output.exists()
m=json.loads((a.terminal.parent/'manifest.json').read_text());assert not m.get('original_inputs',[]) and sha(a.terminal)==m['binary_sha256']
fresh=a.output/'source';fresh.mkdir(parents=True)
for name,digest in m['sources'].items():
 path=Path(name);assert not path.is_absolute() and '..' not in path.parts and path.parts[0] not in ('build','analysis','originals','install')
 assert path.suffix.lower() not in ('.exe','.com','.obj','.o','.img','.prm','.dir') and sha(ROOT/path)==digest
 target=fresh/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/path,target)
assert not (fresh/'build').exists()
env=dict(os.environ,GIT_CEILING_DIRECTORIES=str(a.output))
assert subprocess.run(['git','rev-parse','--show-toplevel'],cwd=fresh,env=env,capture_output=True).returncode
command=[sys.executable,'standalone/build_terminal.py',*flags(m,True),'--output-dir',str(fresh/'build/rebuilt')]
with (a.output/'build.log').open('w') as log:subprocess.run(command,cwd=fresh,env=env,stdout=log,stderr=log,check=True,timeout=300)
rebuilt=fresh/'build/rebuilt/TERMINAL.EXE';assert sha(rebuilt)==m['binary_sha256']
r=dict(passed=True,terminal_sha256=sha(rebuilt),source_files=len(m['sources']),original_inputs=[],ancestor_git_unavailable=True,scope=__doc__)
(a.output/'result.json').write_text(json.dumps(r,indent=2)+'\n');print('PASS source-only exact terminal rebuild:',r['terminal_sha256'])
