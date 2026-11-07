#!/usr/bin/env python3
"""Rebuild the EMULATE parent and optional child from public source and repeat declared checks."""
import argparse,io,json,shutil,subprocess,sys,tarfile
from pathlib import Path
from build_context_help import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('parent','test','output'):p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--runner',type=Path)
 a=p.parse_args();parent=a.parent.resolve();test=a.test.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(exist_ok=False)
 m=json.loads((parent/'manifest.json').read_text());t=json.loads((test/'result.json').read_text());assert t['passed'] and m['experimental_aspect_emulate_policy']
 expected=sha(parent/'TERMINAL.EXE');assert m['binary_sha256']==t['parent_sha256']==expected
 sources={**m['sources'],**t['sources']}
 expected_child=None;child_emulate=False
 if a.runner:
  runner=a.runner.resolve();child_manifest=json.loads((runner.parent/'manifest.json').read_text());expected_child=sha(runner)
  assert child_manifest['binary_sha256']==expected_child
  child_emulate=bool(child_manifest.get('experimental_emulate_VM'))
  sources.update(child_manifest['sources'])
 for n in ('standalone/prove_aspect_emulate_parent_source.py','standalone/alarm_connection_candidate_recipe.json','standalone/test_script_device_compact_dos.py','standalone/test_script_word_compact_dos.py','standalone/test_script_buffers_compact_dos.py','standalone/test_aspect_heap_startup_dos.py','standalone/test_render_response_equivalence_dos.py'):sources[n]=sha(ROOT/n)
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
  for name in ('device','word','buffers'):
   run(['standalone/test_script_'+name+'_compact_dos.py','--output','build/'+name])
  if child_emulate:run(['standalone/test_render_response_equivalence_dos.py','--output','build/responses'])
  if expected_child:
   code='from pathlib import Path;import sys;sys.path.insert(0,"standalone");from build_aspect_process import main;main(parent_render=True,output=Path.cwd()/"build/child",notice_bank=True,notice_sound=True,notice_input=True,notice_help=True,help_resource=True,serial_bank=True,register_handoff=True,custom_irq=True,snapshot_lease=True,defer_script_buffers=True,alarm_vm=True)'
   code=code.replace('alarm_vm=True)','alarm_vm=True,emulate_vm='+repr(child_emulate)+')')
   run(['-c',code]);assert sha(fresh/'build/child/ASPECT.EXE')==expected_child
   run(['standalone/test_aspect_heap_startup_dos.py','--terminal','build/parent/TERMINAL.EXE','--runner','build/child/ASPECT.EXE','--output','build/capacity','--nested-program','--streams-around-child','--held-streams','--clock-queries']+(['--emulate-profile-switch','--cpu','386']if child_emulate else []))
 actual=json.loads((fresh/'build/tests/result.json').read_text());assert actual['passed'] and actual['cases']==t['cases']
 results={}
 for name in ('device','word','buffers')+(('responses',)if child_emulate else ())+ (('capacity',) if expected_child else ()):
  path=fresh/'build'/name/'result.json';r=json.loads(path.read_text());assert r['passed'],name
  results[name]=dict(sha256=sha(path),cases=r.get('cases',len(r.get('checks',{}))))
 for n,h in sources.items():assert sha(ROOT/n)==sha(fresh/n)==h,n
 (out/'inventory.json').write_text(json.dumps(inventory,sort_keys=True,indent=2)+'\n')
 report=dict(passed=True,sources=sources,source_base_commit=base,source_files=len(inventory),inventory_sha256=sha(out/'inventory.json'),parent_sha256=expected,child_sha256=expected_child,repeated_suites=results,cases=len(actual['cases']),repeated_result_sha256=sha(fresh/'build/tests/result.json'),original_inputs=[],scope=__doc__+' Public HEAD plus declared input overlays. No originals/private configuration/prior objects/Git ancestry. Exact parent and complete linked owner matrix; its DOS/BIOS/UART boundaries modeled. Also repeats actual DOS8086 device/word/buffer source comparisons; with --runner, rebuilds the normal child and repeats real DOS held-stream/nested-child capacity. Does not prove child RPC/opcode, profile-switch latency, BBS or physical acceptance. Default/installed profile remains unchanged.')
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS cold EMULATE parent:',len(inventory),'public files;',len(actual['cases']),'cases')
if __name__=='__main__':main()
