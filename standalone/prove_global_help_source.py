#!/usr/bin/env python3
"""Export public HEAD plus declared changes; rebuild and exercise global Help."""
import argparse,io,json,shutil,subprocess,sys,tarfile
from pathlib import Path
from build_context_help import ROOT,sha
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--package',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();package=a.package.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False);fresh=out/'source';fresh.mkdir()
 manifest=json.loads((package/'package.json').read_text())
 for name,digest in manifest['sources'].items():assert sha(ROOT/name)==digest,name
 archive=subprocess.check_output(['git','archive','HEAD'],cwd=ROOT)
 with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
  tar.extractall(fresh,members=[m for m in tar.getmembers() if m.name.split('/')[0] not in ('analysis','build','.git')],filter='data')
 overlay=set(manifest['sources'])|{'standalone/prove_global_help_source.py','standalone/test_global_help_main.py','standalone/global_help_watch.asm'}
 for name in overlay:
  target=fresh/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
 assert not (fresh/'.git').exists() and not (fresh/'build').exists() and not (fresh/'analysis').exists()
 exported={str(p.relative_to(fresh)):sha(p) for p in fresh.rglob('*') if p.is_file()}
 rebuilt=fresh/'build/rebuilt'
 with (out/'build.log').open('w') as log:
  subprocess.run([sys.executable,str(fresh/'standalone/build_global_help_profile.py'),'--output',str(rebuilt)],cwd=fresh,stdout=log,stderr=log,check=True)
 actual=json.loads((rebuilt/'package.json').read_text());assert actual['products']==manifest['products']
 runs=[]
 for case in ['normal','flow']:
  target=fresh/('build/help-'+case)
  with (out/(case+'.log')).open('w') as log:
   subprocess.run([sys.executable,str(fresh/'standalone/test_global_help_main.py'),'--package',str(rebuilt),'--output',str(target),'--case',case],cwd=fresh,stdout=log,stderr=log,check=True)
  result=json.loads((target/'result.json').read_text());assert result['passed'];runs.append(dict(case=case,result_sha256=sha(target/'result.json'),checks=result['checks']))
 for name,digest in manifest['sources'].items():assert sha(ROOT/name)==digest,name
 import hashlib
 report=dict(passed=True,products=actual['products'],source_files=len(exported),exported_inventory_sha256=hashlib.sha256(json.dumps(exported,sort_keys=True).encode()).hexdigest(),base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),overlay_sources={name:sha(ROOT/name) for name in sorted(overlay)},runs=runs,scope='Git-free export of public HEAD with declared application/test source overlay only. File inventory is captured before build/import code generation. No original executable, private configuration, analysis artifact or prior object. Exact parent/Chat/Help/HLP rebuild and normal-main plus flow-control Help sessions repeated. Unrelated worktree changes are not exported.')
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS cold global Help rebuild and DOS normal/flow tests',report['source_files'])
if __name__=='__main__':main()
