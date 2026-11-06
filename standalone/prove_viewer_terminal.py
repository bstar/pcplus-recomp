#!/usr/bin/env python3
"""Reproduce a viewer feature and its disabled parent from a public Git export."""
import argparse,json,os,re,subprocess,sys
from pathlib import Path
from build_path_session import ROOT,sha
from prove_phone_log_startup_terminal import flags

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ['terminal','output']:p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--disabled-sha256',required=True)
 p.add_argument('--feature',choices=['file-viewer','external-viewer','external-editor'],default='file-viewer');a=p.parse_args()
 assert re.fullmatch('[a-f0-9]{64}',a.disabled_sha256)
 binary=a.terminal.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 manifest=json.loads(binary.with_name('manifest.json').read_text());assert manifest['experimental_file_viewer'] and sha(binary)==manifest['binary_sha256']
 assert manifest['experimental_'+a.feature.replace('-','_')]
 revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
 tracked=subprocess.check_output(['git','ls-tree','-r','--name-only',revision],cwd=ROOT,text=True).splitlines()
 names=set(manifest['sources'])|{n for n in tracked if n.startswith('standalone/') and n.endswith('.py')}
 out.mkdir(parents=True);fresh=out/'source';sources={}
 for name in sorted(names):
  relative=Path(name)
  assert not relative.is_absolute() and '..' not in relative.parts and relative.parts[0] not in ['build','analysis','original','originals','install','.git']
  assert relative.suffix.lower() not in ['.exe','.com','.obj','.prm','.fon','.img','.db']
  data=subprocess.check_output(['git','show',revision+':'+name],cwd=ROOT)
  target=fresh/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
  stamp=(ROOT/name).stat();os.utime(target,ns=(stamp.st_atime_ns,stamp.st_mtime_ns))
  sources[name]=sha(target);assert sha(ROOT/name)==sources[name],name
 for name,digest in manifest['sources'].items():assert sources[name]==digest,name
 env=dict(os.environ,GIT_CEILING_DIRECTORIES=str(out))
 assert subprocess.run(['git','rev-parse','--show-toplevel'],cwd=fresh,env=env,capture_output=True).returncode
 selected=flags(manifest,True);feature='--'+a.feature;assert feature in selected
 with (out/'build.log').open('w') as log:
  for folder,options,want in [('enabled',selected,manifest['binary_sha256']),('disabled',[f for f in selected if f!=feature],a.disabled_sha256)]:
   subprocess.run([sys.executable,'standalone/build_terminal.py',*options,'--output-dir','build/'+folder],cwd=fresh,env=env,stdout=log,stderr=log,check=True)
   assert sha(fresh/'build'/folder/'TERMINAL.EXE')==want,folder
 for name,digest in sources.items():assert sha(ROOT/name)==sha(fresh/name)==digest,name
 result=dict(passed=True,source_commit=revision,source_count=len(sources),sources=sources,original_inputs=[],ancestor_git_unavailable=True,
  binary_sha256=manifest['binary_sha256'],disabled_sha256=a.disabled_sha256,build_log_sha256=sha(out/'build.log'),scope=__doc__+' Full-byte equality under the pinned Nix environment; no original files, prior objects, private settings or Git metadata in the export. Runtime/physical acceptance remains separate.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS public source export:',len(sources),'files; exact enabled and disabled terminal images')
if __name__=='__main__':main()
