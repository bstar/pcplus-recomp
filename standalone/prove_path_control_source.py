#!/usr/bin/env python3
"""Rebuild a path-control parent using only its declared public source inputs."""
import argparse,hashlib,json,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True)
 p.add_argument('--flags',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 binary=a.terminal.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 manifest=json.loads(binary.with_name('manifest.json').read_text());assert manifest['binary_sha256']==sha(binary)
 assert manifest['experimental_path_control'] and not manifest.get('original_inputs')
 fresh=out/'source';sources=manifest['sources'];out.mkdir(parents=True)
 for name,digest in sources.items():
  rel=Path(name);assert not rel.is_absolute() and '..' not in rel.parts and rel.parts[0] not in ('build','analysis','install')
  assert rel.suffix.lower() not in ('.exe','.com','.obj','.img','.prm','.dir','.xlt','.db')
  assert sha(ROOT/rel)==digest,name
  target=fresh/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/rel,target)
 assert not (fresh/'.git').exists() and not (fresh/'build').exists()
 flags=json.loads(a.flags.read_text());command=[sys.executable,'standalone/build_terminal.py',*flags,'--path-control','--notice-sound','--output-dir',str(fresh/'build/rebuilt')]
 with (out/'build.log').open('w') as log:subprocess.run(command,cwd=fresh,stdout=log,stderr=log,check=True)
 actual=sha(fresh/'build/rebuilt/TERMINAL.EXE');assert actual==sha(binary),(actual,sha(binary))
 for name,digest in sources.items():assert sha(ROOT/name)==digest,name
 result=dict(passed=True,binary_sha256=actual,source_count=len(sources),sources=sources,original_inputs=[],
  command=command,scope='Exact executable rebuild in a new Git-free tree from declared source files; no original executable inputs.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS',len(sources),'source-only inputs',actual)
if __name__=='__main__':main()
