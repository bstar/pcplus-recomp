#!/usr/bin/env python3
"""Rebuild only declared source inputs with originals/Git unavailable; repeat DOS."""
import argparse,hashlib,json,shutil,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--commit');args=p.parse_args()
 out=args.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 baseline=ROOT/'build/directory-resource-cli';manifest=json.loads((baseline/'manifest.json').read_text())
 assert not manifest['original_inputs'] and sha(baseline/'CLI.EXE')==manifest['binary_sha256']
 sources=dict(manifest['sources'])
 for name in ['standalone/test_directory_resource_cli_dos.py','standalone/test_terminal.py','standalone/test_directory_resources_dos.py','standalone/prove_directory_resource_cli.py']:sources[name]=sha(ROOT/name)
 for name,digest in sources.items():assert sha(ROOT/name)==digest,name
 commit=subprocess.check_output(['git','rev-parse','--verify','--end-of-options',args.commit+'^{commit}'],cwd=ROOT,text=True).strip() if args.commit else None
 out.mkdir(parents=True)
 with tempfile.TemporaryDirectory(prefix='pcplus-directory-resource-cli-') as tmp:
  export=Path(tmp)/'source';export.mkdir()
  for name,digest in sources.items():
   relative=Path(name);assert not relative.is_absolute() and '..' not in relative.parts and relative.parts[0] in ('src','standalone','reconstruction')
   target=export/relative;target.parent.mkdir(parents=True,exist_ok=True)
   if commit:target.write_bytes(subprocess.check_output(['git','show',commit+':'+name],cwd=ROOT))
   else:shutil.copyfile(ROOT/name,target)
   assert sha(target)==digest,name
  assert not any((p/'.git').exists() for p in [export,*export.parents]) and not (export/'analysis').exists()
  with (out/'build.log').open('w') as log:subprocess.run([sys.executable,'standalone/build_directory_resource_cli.py'],cwd=export,stdout=log,stderr=log,check=True)
  built=export/'build/directory-resource-cli';rebuilt=json.loads((built/'manifest.json').read_text());assert rebuilt==manifest
  for n,h in manifest['objects'].items():assert sha(built/n)==h,n
  assert sha(built/'CLI.EXE')==manifest['binary_sha256']
  with (out/'test.log').open('w') as log:subprocess.run([sys.executable,'standalone/test_directory_resource_cli_dos.py','--output',str(export/'build/dos-tests')],cwd=export,stdout=log,stderr=log,check=True)
  tested=json.loads((export/'build/dos-tests/result.json').read_text())
  assert tested['passed'] and tested['case_count']==17 and tested['hardware_restored']
  assert tested['binary_sha256']==manifest['binary_sha256'] and tested['sources']==manifest['sources']
  for n,h in tested['test_sources'].items():assert sources[n]==h,n
  shutil.copytree(export,out/'export')
 for n,h in sources.items():assert sha(ROOT/n)==h,n
 result=dict(passed=True,exported_source_commit=commit,ancestor_git_unavailable=True,original_inputs=[],source_files=len(sources),sources=sources,
  binary_sha256=manifest['binary_sha256'],objects=manifest['objects'],DOS_workflows=tested['case_count'],native_assertions=tested['native_assertions'],
  hardware_restored=True,immutable_CLI_provenance=True,limitations=manifest['limitations'],
  artifacts={str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()})
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS',len(sources),'sources; executable/'+str(len(manifest['objects']))+' objects exact;',tested['case_count'],'DOS workflows /',tested['native_assertions'],'assertions')
if __name__=='__main__':main()
