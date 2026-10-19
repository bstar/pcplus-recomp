#!/usr/bin/env python3
"""Bind real compiler EXEC, UART ownership, BBS/UI and reproducible builds."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(path):return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
def read(path):return json.loads((ROOT/path).read_text())
def main():
 runner=read('build/aspect-runner/manifest.json');compiler=read('build/aspect-compiler-dos/manifest.json')
 rh=sha('build/aspect-runner/ASPECT.EXE');ch=sha('build/aspect-compiler-dos/ASPCOMP.EXE');th=sha('build/terminal/TERMINAL.EXE')
 for manifest,digest in ((runner,rh),(compiler,ch)):
  assert manifest['binary_sha256']==digest and not manifest['original_inputs']
  for p,h in manifest['sources'].items():assert sha(p)==h,p
 reports={}
 for name,path,checker in [
  ('source','build/aspect-source-compile/checks.json','standalone/check_aspect_source_compile.py'),
  ('serial','build/aspect-source-serial-dos/checks.json','standalone/check_aspect_source_serial_dos.py'),
  ('flow','build/aspect-compile-flow-dos/checks.json','standalone/test_aspect_compile_flow_dos.py'),
  ('runtime','build/aspect-runtime/checks.json','standalone/check_aspect_runtime.py'),
  ('CLI','build/aspect-runner/checks.json','standalone/check_aspect_runner.py'),
  ('UART_CPU','build/aspect-serial/checks.json','standalone/check_aspect_serial.py'),
  ('UART_DOS','build/aspect-serial/dos-checks.json','standalone/test_aspect_serial_dos.py')]:
  r=read(path);assert r['passed'] and r['check_sha256' if name=='runtime' else 'checker_sha256']==sha(checker),(name,path)
  reports[name]=dict(path=path,sha256=sha(path),summary=r.get('DOS_summary',r.get('scope',name)))
  if name in ('source','serial'):assert r['runner_sha256']==rh and r['compiler_sha256']==ch
  if name=='source':
   assert r['DOS_summary']=='SOURCE_EXEC 22 cases 223 checks 0 failures' and r['recompilation_cycles']==20
   for p,h in r['test_inputs'].items():assert sha('build/aspect-source-compile/tests/'+p)==h
  if name=='serial':
   assert len(r['cases'])==7 and all(c['passed'] and c['binary_sha256']==rh for c in r['cases'])
   assert r['reused_checker_sha256']==sha('standalone/test_aspect_script_serial_dos.py')
   for c in r['cases']:
    folder='build/aspect-source-serial-dos/'+c['name']+'/'
    leaf='REALCOMP.EXE' if c['name'].startswith('pressure') else 'ASPCOMP.EXE'
    assert sha(folder+leaf)==ch
  if name=='flow':
   assert len(r['cases'])==4 and all(c['passed'] for c in r['cases'])
   for p,h in r['sources'].items():assert sha(p)==h,p
  if name=='runtime':assert r['DOS_summary']=='ASPECT_RUNTIME 1146 cases 26309 checks 0 failures'
  if name=='CLI':assert r['binary_sha256']==rh and r['DOS_summary']=='RUNNER 21 cases 105 checks 0 failures'
  if name.startswith('UART_'):assert r['binary_sha256']==sha('build/aspect-serial/SERIAL.EXE')
 bbs=[]
 for server,label in [('synchronet','compiler-source-sync-04'),('enigma','compiler-source-enigma30-03')]:
  stage='build/bbs-lab/script-login/'+label+'/';r=read(stage+'checks.json');p=read(stage+'predictions.json')
  assert r['passed'] and all(r['checks'].values()) and r['checks']['source_compilation']
  assert p['compile_in_DOS'] and 'LOGON.ASX' not in r['staged']
  assert r['staged']['ASPCOMP.EXE']==ch and r['runner_sha256']==rh and r['terminal_sha256']==th
  assert sha(stage+'LOGON.ASX')==p['expected_ASX_sha256']
  for path,digest in r['sources'].items():assert sha(path)==digest,path
  for leaf,digest in r['staged'].items():assert sha(stage+leaf)==digest,leaf
  bbs.append(dict(server=server,label=label,passed=True,report_sha256=sha(stage+'checks.json'),predictions_sha256=sha(stage+'predictions.json'),compiled_asx_sha256=sha(stage+'LOGON.ASX'),checks=r['checks'],packet_delay_ms=r.get('modem_packet_delay_ms',0)))
 historical='build/bbs-lab/script-login/compiler-source-enigma0-01/checks.json';failed=read(historical)
 assert not failed['passed'] and failed['checks']['source_compilation'] and failed['checks']['authenticated_server_log']
 assert failed['checks']['no_post_saved'] and not failed['checks']['resumed_parent_editor']
 proof=read('docs/validation/application-components-source-build.json')
 assert proof['passed'] and proof['output_count']==153 and all(v['matches_workspace'] for v in proof['outputs'].values())
 for path,digest in [('aspect-runner/ASPECT.EXE',rh),('aspect-compiler-dos/ASPCOMP.EXE',ch),('terminal/TERMINAL.EXE',th)]:assert proof['outputs'][path]['sha256']==digest
 package=read('build/dos-package/manifest.json');assert package['files']['ASPECT.EXE']==rh and package['files']['ASPCOMP.EXE']==ch
 result=dict(passed=True,recorder_sha256=sha('standalone/record_aspect_source_compile.py'),runner_sha256=rh,compiler_sha256=ch,terminal_sha256=th,reports=reports,BBS=bbs,
  retained_immediate_ENiGMA_failure=dict(report_sha256=sha(historical),runner_sha256=failed['runner_sha256'],checks=failed['checks'],scope='Earlier source-enabled binary in this checkpoint family compiled and authenticated, then retained the known stock Home-key failure. No immediate-forwarding fix is claimed.'),
  source_proof_sha256=sha('docs/validation/application-components-source-build.json'),reproduced_outputs=153,
  compiler_port_validation_sha256=sha('docs/validation/aspect-dos-compiler.json'),original_inputs=[],
  implemented=['explicit ASP compilation and missing-ASX sibling fallback, with compiled-name precedence','sibling compiler location, captured diagnostics and immutable source/failed old-ASX preservation','neutral compiler INT0 scope, parent PSP/vector restoration and foreign-DS CPU-fault isolation','cancellation before EXEC and queued Escape after child return','live UART IRQ, proactive owned XOFF/RTS pause, checked resume and retained unread bytes','combined-flow RTS low-water recovery including full preloaded queues','EXECUTE retained numeric/settings state and current compiled-file label','actual DOS terminal directory-bound source compilation, login and unsaved editor return on recorded Synchronet/ENiGMA configurations'],
  limitations=['Compiler language remains the maintained host subset; full native language, recorder and original compiler/error UI remain unfinished.','Compilation is synchronous. Escape queued during the child is handled on return, not by asynchronously interrupting compiler work.','No source fallback replaces an existing invalid or unreadable ASX.','ENiGMA Home-key behavior with immediate byte forwarding remains unresolved; the passing network-profile run uses explicit30ms buffering.','Physical modems/386 and timing outside the recorded emulator cases remain unverified.','No F01-F16 whole-application gate is closed.'],whole_application_gates_closed=[])
 (ROOT/'docs/validation/aspect-source-compile.json').write_text(json.dumps(result,indent=2)+'\n');print('Bound source compilation:22 offline cases,7 live UART cases,4 preload flow cases,2 successful BBS/UI workflows; immediate ENiGMA failure retained')
if __name__=='__main__':main()
