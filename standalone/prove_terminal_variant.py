#!/usr/bin/env python3
"""Rebuild a terminal variant from its declared public sources in an empty tree."""
import argparse,hashlib,json,os,re,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);p.add_argument('--flags-json',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 terminal=a.terminal.resolve();out=a.output.resolve();assert terminal.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 flags=json.loads(a.flags_json.read_text());assert isinstance(flags,list) and all(isinstance(f,str) and (re.fullmatch('--[a-z-]+',f) and f!='--output-dir' or f in ('25','28','43','50') and i>0 and flags[i-1]=='--session-rows-probe') for i,f in enumerate(flags))
 manifest=json.loads((terminal.parent/'manifest.json').read_text());assert sha(terminal)==manifest['binary_sha256']
 sources=manifest['sources'];fresh=out/'source'
 for name,digest in sources.items():
  rel=Path(name);assert not rel.is_absolute() and '..' not in rel.parts and rel.parts[0] not in ('build','analysis','original','originals','.git')
  assert rel.suffix.lower() not in ('.exe','.com','.obj','.o','.img','.prm','.dir','.xlt','.gpr','.gzf')
  source=ROOT/rel;assert not source.is_symlink() and sha(source)==digest,name
  dest=fresh/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest)
 assert not (fresh/'build').exists()
 env=dict(os.environ,GIT_CEILING_DIRECTORIES=str(out))
 git=subprocess.run(['git','rev-parse','--show-toplevel'],cwd=fresh,env=env,capture_output=True)
 assert git.returncode!=0,'Ancestor Git unexpectedly accessible'
 command=[sys.executable,'standalone/build_terminal.py',*flags,'--output-dir','build/reproduced']
 with (out/'build.log').open('w') as log:subprocess.run(command,cwd=fresh,env=env,stdout=log,stderr=log,check=True,timeout=240)
 actual=fresh/'build/reproduced/TERMINAL.EXE';assert sha(actual)==sha(terminal)
 for name,digest in sources.items():assert sha(ROOT/name)==sha(fresh/name)==digest,name
 record=dict(passed=True,terminal_sha256=sha(actual),source_files=len(sources),original_inputs=[],ancestor_git_unavailable=True,command=command[1:],flags=flags,manifest_sha256=sha(terminal.parent/'manifest.json'),flags_sha256=sha(a.flags_json),checker_sha256=sha(Path(__file__)),build_log_sha256=sha(out/'build.log'),scope=__doc__+' Requires caller pinned toolchain environment; byte identity, not runtime acceptance.')
 (out/'result.json').write_text(json.dumps(record,indent=2)+'\n');print('PASS source-only variant rebuild',len(sources),'files',sha(actual))
if __name__=='__main__':main()
