#!/usr/bin/env python3
"""Rebuild the unbound parent EMULATE owner from public source and repeat its matrix."""
import argparse,io,json,shutil,subprocess,sys,tarfile
from pathlib import Path
from build_context_help import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('parent','test','output'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();parent=a.parent.resolve();test=a.test.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(exist_ok=False)
 m=json.loads((parent/'manifest.json').read_text());t=json.loads((test/'result.json').read_text());assert t['passed'] and m['experimental_aspect_emulate_policy']
 expected=sha(parent/'TERMINAL.EXE');assert m['binary_sha256']==t['parent_sha256']==expected
 sources={**m['sources'],**t['sources']}
 for n in ('standalone/prove_aspect_emulate_parent_source.py','standalone/alarm_connection_candidate_recipe.json'):sources[n]=sha(ROOT/n)
 fresh=out/'source';fresh.mkdir();base=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
 with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive',base],cwd=ROOT)))as tar:
  tar.extractall(fresh,members=[x for x in tar.getmembers()if x.name.split('/')[0]not in ('analysis','build','.git')],filter='data')
 for n,h in sources.items():
  assert not Path(n).is_absolute() and '..'not in Path(n).parts and Path(n).parts[0]not in ('analysis','build','.git')
  assert sha(ROOT/n)==h,n
  dst=fresh/n;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/n,dst)
 assert not any((fresh/n).exists()for n in ('analysis','build','.git'))
 inventory={str(f.relative_to(fresh)):sha(f)for f in fresh.rglob('*')if f.is_file()}
 flags=json.loads((fresh/'standalone/alarm_connection_candidate_recipe.json').read_text())['terminal_flags']
 with(out/'build.log').open('w')as log:
  def run(args):subprocess.run([sys.executable,*args],cwd=fresh,stdout=log,stderr=log,check=True)
  run(['standalone/build_terminal.py',*flags,'--aspect-emulate-policy','--output-dir','build/parent'])
  assert sha(fresh/'build/parent/TERMINAL.EXE')==expected
  run(['standalone/check_aspect_emulate_parent.py','--product','build/parent','--output','build/tests'])
 actual=json.loads((fresh/'build/tests/result.json').read_text());assert actual['passed'] and actual['cases']==t['cases']
 for n,h in sources.items():assert sha(ROOT/n)==sha(fresh/n)==h,n
 (out/'inventory.json').write_text(json.dumps(inventory,sort_keys=True,indent=2)+'\n')
 report=dict(passed=True,sources=sources,source_base_commit=base,source_files=len(inventory),inventory_sha256=sha(out/'inventory.json'),parent_sha256=expected,cases=len(actual['cases']),repeated_result_sha256=sha(fresh/'build/tests/result.json'),original_inputs=[],scope=__doc__+' Public HEAD plus declared input overlays. No originals/private configuration/prior objects/Git ancestry. Exact parent and complete linked owner matrix; only DOS/BIOS/UART modeled. Does not prove child RPC/opcode, real DOS latency/capacity/BBS/physical acceptance. Default/installed profile remains unchanged.')
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS cold EMULATE parent:',len(inventory),'public files;',len(actual['cases']),'cases')
if __name__=='__main__':main()
