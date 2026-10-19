#!/usr/bin/env python3
"""Bind the keyboard acquisition checkpoint to current products and regressions."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(path):return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
def read(path):return json.loads((ROOT/path).read_text())
def main():
 runner=read('build/aspect-runner/manifest.json');digest=sha('build/aspect-runner/ASPECT.EXE')
 assert runner['binary_sha256']==digest and not runner['original_inputs']
 for path,h in runner['sources'].items():assert sha(path)==h,path
 for leaf,h in runner['objects'].items():assert sha('build/aspect-runner/'+leaf)==h,leaf
 keyboard=read('build/aspect-keyboard/checks.json')
 assert keyboard['passed'] and keyboard['runner_sha256']==digest
 assert keyboard['checker_sha256']==sha('standalone/check_aspect_keyboard.py')
 assert keyboard['manifest_sha256']==sha('build/aspect-runner/manifest.json')
 assert keyboard['CPU_words']==keyboard['DOS_words']==65536
 assert keyboard['DOS_summary']=='ASPECT_KEYBOARD 65536 words 131132 checks 0 failures'
 assert keyboard['words_corrected_from_previous_reader']==19011
 for leaf,h in keyboard['objects'].items():assert runner['objects'][leaf]==h
 for leaf,h in keyboard['test_inputs'].items():assert sha('build/aspect-keyboard/'+leaf)==h
 reports={}
 for name,path,checker,field in [
  ('runtime','build/aspect-runtime/checks.json','standalone/check_aspect_runtime.py','check_sha256'),
  ('CLI','build/aspect-runner/checks.json','standalone/check_aspect_runner.py','checker_sha256'),
  ('source','build/aspect-source-compile/checks.json','standalone/check_aspect_source_compile.py','checker_sha256'),
  ('serial','build/aspect-source-serial-dos/checks.json','standalone/check_aspect_source_serial_dos.py','checker_sha256')]:
  r=read(path);assert r['passed'] and r[field]==sha(checker)
  if name=='CLI':assert r['binary_sha256']==digest
  if name in ('source','serial'):assert r['runner_sha256']==digest
  if name=='runtime':assert r['binary_sha256']==sha('build/aspect-runtime/EXECUTE.EXE')
  reports[name]=dict(path=path,sha256=sha(path),summary=r.get('DOS_summary',r.get('scope')))
 baseline=read('build/keyboard/manifest.json')
 assert not baseline.get('original_inputs')
 for p,h in baseline['sources'].items():assert sha(p)==h,p
 for i,region in enumerate(baseline['baseline_regions']):
  path='build/keyboard/baseline-'+str(i)+'.bin'
  assert sha(path)==region['sha256'] and (ROOT/path).stat().st_size==region['size']
 proof=read('docs/validation/application-components-source-build.json')
 assert proof['passed'] and proof['output_count']==153
 assert all(v['matches_workspace'] for v in proof['outputs'].values())
 assert proof['outputs']['aspect-runner/ASPECT.EXE']['sha256']==digest
 assert proof['outputs']['aspect-runtime/EXECUTE.EXE']['sha256']==sha('build/aspect-runtime/EXECUTE.EXE')
 assert read('build/dos-package/manifest.json')['files']['ASPECT.EXE']==digest
 bbs=[]
 for server,label in [('synchronet','keyboard-normalizer-sync-01'),('enigma','keyboard-normalizer-enigma30-01')]:
  path='build/bbs-lab/script-login/'+label+'/checks.json';r=read(path)
  assert r['passed'] and all(r['checks'].values()) and r['runner_sha256']==digest
  assert r['checks']['source_compilation']
  assert r['checks']['draft_aborted' if server=='synchronet' else 'no_post_saved']
  assert r['terminal_sha256']==sha('build/terminal/TERMINAL.EXE')
  stage='build/bbs-lab/script-login/'+label+'/'
  for leaf,h in r['staged'].items():assert sha(stage+leaf)==h,leaf
  for p,h in r['sources'].items():assert sha(p)==h,p
  bbs.append(dict(server=server,path=path,sha256=sha(path),checks=r['checks'],packet_delay_ms=r.get('modem_packet_delay_ms',0)))
 result=dict(passed=True,recorder_sha256=sha('standalone/record_aspect_keyboard.py'),runner_sha256=digest,keyboard=keyboard,
  reports=reports,BBS=bbs,native_baseline_regions=baseline['baseline_regions'],
  source_proof_sha256=sha('docs/validation/application-components-source-build.json'),reproduced_outputs=153,
  REA_evidence=['ev_cb670ed8c108fd2f8a4d03d1d83765074271c3cae5e31f2e0ac94f3c59873699','ev_8e40cf9d5f190f977da1b135d35970d1fcab5cac3261658c9dabbd80eb7dfbd6'],
  original_inputs=[],whole_application_gates_closed=[],
  limitations=['Acquisition only: ordinary script-time dispatch remains unsupported; native confirmation and full profile/macro/hotkey/UI services are unfinished.',
   'CPU INT16 and DOS temporary BIOS vector are declared models; no physical BIOS/keyboard or Wi-Fi modem validation.',
   'BIOS enhanced-mode inheritance remains unfinished.',
   'ENiGMA passing editor case uses explicit30ms buffering; the historical immediate-forwarding Home-key failure is unresolved.'])
 (ROOT/'docs/validation/aspect-keyboard.json').write_text(json.dumps(result,indent=2)+'\n')
 print('Bound exhaustive ASPECT keyboard acquisition and current DOS/BBS regressions')
if __name__=='__main__':main()
