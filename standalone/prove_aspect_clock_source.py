#!/usr/bin/env python3
"""Cold public-source rebuild of both interpreters/compiler and DOS clock checks."""
import argparse,hashlib,io,json,shutil,subprocess,sys,tarfile
from pathlib import Path
from build_context_help import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('matched','output'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();out=a.output.resolve();matched=a.matched.resolve();assert out.is_relative_to(ROOT/'build') and matched.is_relative_to(ROOT/'build');out.mkdir(exist_ok=False);fresh=out/'source';fresh.mkdir()
 overlays=set();expected={}
 for folder in (matched,ROOT/'build/aspect-runner',ROOT/'build/aspect-compiler-dos',ROOT/'build/aspect-runtime'):
  m=json.loads((folder/'manifest.json').read_text())
  for n,h in m['sources'].items():assert sha(ROOT/n)==h,n;overlays.add(n)
  if folder!=ROOT/'build/aspect-runtime':expected[folder.name if folder==matched else folder.name]=m['binary_sha256']
 overlays|={'standalone/prove_aspect_clock_source.py','standalone/test_aspect_clock_dos.py','standalone/check_aspect_clock.py','standalone/fixtures/aspect_clock_native_units.json','standalone/fixtures/aspect_clock_compiler_vectors.json'}
 with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive','HEAD'],cwd=ROOT))) as tar:
  tar.extractall(fresh,members=[m for m in tar.getmembers() if m.name.split('/')[0] not in ('analysis','build','.git')],filter='data')
 for n in overlays:
  target=fresh/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/n,target)
 assert not any((fresh/n).exists() for n in ('analysis','build','.git'))
 inventory={str(f.relative_to(fresh)):sha(f) for f in fresh.rglob('*') if f.is_file()}
 with (out/'build.log').open('w') as log:
  for script in ('build_aspect_runtime.py','build_aspect_runner.py','build_aspect_compiler_dos.py'):
   subprocess.run([sys.executable,'standalone/'+script],cwd=fresh,stdout=log,stderr=log,check=True)
  code='from pathlib import Path;import sys;sys.path.insert(0,"standalone");from build_aspect_process import main;main(parent_render=True,output=(Path.cwd()/"build/matched"),notice_bank=True,notice_sound=True,notice_input=True,notice_help=True,help_resource=True,serial_bank=True,register_handoff=True,custom_irq=True,snapshot_lease=True,defer_script_buffers=True)'
  subprocess.run([sys.executable,'-c',code],cwd=fresh,stdout=log,stderr=log,check=True)
  subprocess.run([sys.executable,'standalone/test_aspect_clock_dos.py','--output',str(fresh/'build/clock-dos')],cwd=fresh,stdout=log,stderr=log,check=True)
 actual={'aspect-runner':sha(fresh/'build/aspect-runner/ASPECT.EXE'),'aspect-compiler-dos':sha(fresh/'build/aspect-compiler-dos/ASPCOMP.EXE'),matched.name:sha(fresh/'build/matched/ASPECT.EXE')};assert actual==expected
 test=json.loads((fresh/'build/clock-dos/result.json').read_text());assert test['passed'] and test['cases']==372 and test['same_process_rounds']==31
 for n in overlays:assert sha(ROOT/n)==inventory[n]==sha(fresh/n),n
 result=dict(passed=True,products=actual,source_files=len(inventory),exported_inventory_sha256=hashlib.sha256(json.dumps(inventory,sort_keys=True).encode()).hexdigest(),overlay_sources={n:sha(ROOT/n) for n in sorted(overlays)},DOS_cases=test['cases'],DOS_checks=test['checks'],DOS_result_sha256=sha(fresh/'build/clock-dos/result.json'),base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),original_inputs=[],scope=__doc__+' Public HEAD plus explicitly declared source overlay. No original executable, private configuration, prior object, REA database or Git metadata. Pinned Nix environment supplied by caller; this does not retest its bootstrap. Exact ordinary/matched ASPECT and ASPCOMP hashes, then372 actual DOS clock VM cases.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS cold clock source rebuild:',len(inventory),'files;',test['cases'],'DOS cases')
if __name__=='__main__':main()
