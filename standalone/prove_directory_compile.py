#!/usr/bin/env python3
"""Rebuild compiler owner, fault child and real compiler from isolated sources."""
import argparse,hashlib,json,shutil,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path);p.add_argument('--commit');a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 built=ROOT/'build/directory-compile';m=json.loads((built/'manifest.json').read_text());cm=json.loads((ROOT/'build/aspect-compiler-dos/manifest.json').read_text())
 assert not m['original_inputs'] and not cm['original_inputs'];assert sha(built/'DCOMPILE.EXE')==m['binary_sha256'] and sha(built/'FAULT.EXE')==m['fault_child_sha256']
 sources=dict(m['sources'])
 for n,h in cm['sources'].items():assert n not in sources or sources[n]==h;sources[n]=h
 for n in ['standalone/test_directory_compile_dos.py','src/aspect/compiler.py','standalone/prove_directory_compile.py']:sources[n]=sha(ROOT/n)
 for n,h in sources.items():assert sha(ROOT/n)==h,n
 commit=subprocess.check_output(['git','rev-parse','--verify','--end-of-options',a.commit+'^{commit}'],cwd=ROOT,text=True).strip() if a.commit else None
 out.mkdir(parents=True)
 with tempfile.TemporaryDirectory(prefix='pcplus-directory-compile-') as temp:
  export=Path(temp)/'source';export.mkdir()
  for n,h in sources.items():
   relative=Path(n);assert not relative.is_absolute() and '..' not in relative.parts and relative.parts[0] in ('src','standalone')
   target=export/relative;target.parent.mkdir(parents=True,exist_ok=True)
   if commit:target.write_bytes(subprocess.check_output(['git','show',commit+':'+n],cwd=ROOT))
   else:shutil.copyfile(ROOT/n,target)
   assert sha(target)==h,n
  assert not any((p/'.git').exists() for p in [export,*export.parents])
  with (out/'build.log').open('w') as log:
   for script in ['build_aspect_compiler_dos.py','build_directory_compile.py']:subprocess.run([sys.executable,'standalone/'+script],cwd=export,stdout=log,stderr=log,check=True)
  rebuilt=json.loads((export/'build/directory-compile/manifest.json').read_text());assert rebuilt==m
  for n,h in m['objects'].items():assert sha(export/'build/directory-compile'/n)==h,n
  assert sha(export/'build/directory-compile/DCOMPILE.EXE')==m['binary_sha256'] and sha(export/'build/directory-compile/FAULT.EXE')==m['fault_child_sha256']
  assert sha(export/'build/aspect-compiler-dos/ASPCOMP.EXE')==cm['binary_sha256']
  with (out/'test.log').open('w') as log:subprocess.run([sys.executable,'standalone/test_directory_compile_dos.py','--output',str(export/'build/native')],cwd=export,stdout=log,stderr=log,check=True)
  tested=json.loads((export/'build/native/result.json').read_text());assert tested['passed'] and tested['case_count']==19 and tested['sources']==m['sources']
  shutil.copytree(export,out/'export')
 for n,h in sources.items():assert sha(ROOT/n)==h,n
 result=dict(passed=True,exported_source_commit=commit,ancestor_git_unavailable=True,original_inputs=[],source_files=len(sources),sources=sources,binary_sha256=m['binary_sha256'],fault_child_sha256=m['fault_child_sha256'],compiler_binary_sha256=cm['binary_sha256'],objects=m['objects'],DOS_workflows=tested['case_count'],native_assertions=tested['native_assertions'],artifacts={str(q.relative_to(out)):sha(q) for q in out.rglob('*') if q.is_file()})
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS',len(sources),'sources; three executable files and',len(m['objects']),'objects exact;',tested['case_count'],'DOS workflows')
if __name__=='__main__':main()
