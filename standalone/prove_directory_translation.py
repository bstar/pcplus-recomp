#!/usr/bin/env python3
"""Reproduce translation resources from an isolated source closure and repeat DOS."""
import argparse,hashlib,json,shutil,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path);p.add_argument('--commit');a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 built=ROOT/'build/directory-translation';m=json.loads((built/'manifest.json').read_text());assert not m['original_inputs'] and sha(built/'TRANSLAT.EXE')==m['binary_sha256']
 sources=dict(m['sources'])
 for n in ['standalone/test_directory_translation_dos.py','standalone/test_directory_resources_dos.py','standalone/test_terminal.py','standalone/resource_noinherit.asm','standalone/prove_directory_translation.py']:sources[n]=sha(ROOT/n)
 for n,h in sources.items():assert sha(ROOT/n)==h,n
 commit=subprocess.check_output(['git','rev-parse','--verify','--end-of-options',a.commit+'^{commit}'],cwd=ROOT,text=True).strip() if a.commit else None
 out.mkdir(parents=True)
 with tempfile.TemporaryDirectory(prefix='pcplus-translation-') as temp:
  export=Path(temp)/'source';export.mkdir()
  for n,h in sources.items():
   relative=Path(n);assert not relative.is_absolute() and '..' not in relative.parts and relative.parts[0] in ('src','standalone','reconstruction')
   target=export/relative;target.parent.mkdir(parents=True,exist_ok=True)
   if commit:target.write_bytes(subprocess.check_output(['git','show',commit+':'+n],cwd=ROOT))
   else:shutil.copyfile(ROOT/n,target)
   assert sha(target)==h,n
  assert not any((p/'.git').exists() for p in [export,*export.parents])
  with (out/'build.log').open('w') as log:subprocess.run([sys.executable,'standalone/build_directory_translation.py'],cwd=export,stdout=log,stderr=log,check=True)
  rebuilt=json.loads((export/'build/directory-translation/manifest.json').read_text());assert rebuilt==m
  for n,h in m['objects'].items():assert sha(export/'build/directory-translation'/n)==h,n
  assert sha(export/'build/directory-translation/TRANSLAT.EXE')==m['binary_sha256']
  with (out/'test.log').open('w') as log:subprocess.run([sys.executable,'standalone/test_directory_translation_dos.py','--output',str(export/'build/native')],cwd=export,stdout=log,stderr=log,check=True)
  tested=json.loads((export/'build/native/result.json').read_text());assert tested['passed'] and tested['case_count']==16 and tested['noninheritable_child_witness'] and tested['sources']==m['sources']
  shutil.copytree(export,out/'export')
 for n,h in sources.items():assert sha(ROOT/n)==h,n
 result=dict(passed=True,exported_source_commit=commit,ancestor_git_unavailable=True,original_inputs=[],source_files=len(sources),sources=sources,binary_sha256=m['binary_sha256'],objects=m['objects'],DOS_workflows=tested['case_count'],native_assertions=tested['native_assertions'],noninheritable_child_witness=True,artifacts={str(q.relative_to(out)):sha(q) for q in out.rglob('*') if q.is_file()})
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS',len(sources),'sources; exact executable/objects;',tested['case_count'],'DOS workflows')
if __name__=='__main__':main()
