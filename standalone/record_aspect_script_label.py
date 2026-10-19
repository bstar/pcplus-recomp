#!/usr/bin/env python3
"""Bind current label ownership, DOS rendering, compatibility and rebuild evidence."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def read(p):return json.loads((ROOT/p).read_text())
def main():
 parent=sha('build/terminal/TERMINAL.EXE');child=sha('build/aspect-runner/ASPECT.EXE');reports={}
 def evidence(path,binary=None):
  data=read(path);assert data['passed'],path
  if binary:assert data['binary_sha256']==binary,path
  reports[path]=dict(sha256=sha(path),report=data);return data
 for path,digest in [('build/terminal/manifest.json',parent),('build/aspect-runner/manifest.json',child)]:
  manifest=read(path);assert manifest['binary_sha256']==digest
  for source,value in manifest['sources'].items():assert sha(source)==value,source
 client=evidence('build/aspect-runner/script-label-client-checks.json',child);assert len(client['cases'])==37
 server=evidence('build/terminal/script-label-parent-checks.json',parent);assert len(server['cases'])==29
 status=evidence('build/terminal/status-live-checks.json',parent);assert len(status['cases'])==85
 admission=evidence('build/terminal/aspect-render-parent-client-checks.json',parent);assert len(admission['cases'])==23
 evidence('build/aspect-render-client/checks.json',child)
 evidence('build/aspect-runner/break-policy-checks.json',child)
 fixture=evidence('build/aspect-render-client-dos/checks.json',child)
 assert len(fixture['cases'])==5 and all(all(c['checks'].values()) for c in fixture['cases'])
 runtime=evidence('build/aspect-runtime/checks.json');assert runtime['DOS_summary']=='ASPECT_RUNTIME 1146 cases 26309 checks 0 failures'
 runner=evidence('build/aspect-runner/checks.json',child);assert runner['DOS_summary']=='RUNNER 21 cases 105 checks 0 failures'
 dos=evidence('build/aspect-chain-status-dos/label-final-pass/checks.json')
 assert dos['terminal_sha256']==parent and dos['runner_sha256']==child and len(dos['cases'])==2
 for case in dos['cases']:
  assert all(case['checks'].values()) and case['checks']['target_label_displayed']
  assert case['status_characters'].startswith(' NEXT.ASX')
 vt=evidence('build/aspect-status-dos/label-final-vt220/checks.json')
 assert vt['terminal_sha256']==parent and vt['runner_sha256']==child and len(vt['cases'])==1
 assert all(all(c['checks'].values()) for c in vt['cases'])
 proof=evidence('docs/validation/application-components-source-build.json')
 assert proof['output_count']==149 and all(v['matches_workspace'] for v in proof['outputs'].values())
 for name,digest in [('terminal/TERMINAL.EXE',parent),('aspect-runner/ASPECT.EXE',child)]:assert proof['outputs'][name]['sha256']==digest
 for name,digest in [('TERMINAL.EXE',parent),('ASPECT.EXE',child)]:assert sha('build/dos-package/'+name)==digest
 for label,cancel in [('label-final-sync','draft_aborted'),('label-final-enigma30','no_post_saved')]:
  bbs=evidence('build/bbs-lab/script-login/'+label+'/checks.json')
  assert bbs['terminal_sha256']==parent and bbs['runner_sha256']==child
  assert all(bbs['checks'].values()) and bbs['editor']['passed'] and bbs['editor']['checks'][cancel]
 failure='build/aspect-render-client-history/label-cap4-pacing-limit-diagnosis'
 diagnosis=read(failure+'/diagnosis.json');assert diagnosis['initial_callbacks_pass']
 initial=read(failure+'/checks.json');assert not initial['passed']
 callback=next(c for c in initial['cases'] if c['case']=='callback')
 assert b'pacing 5' in bytes.fromhex(callback['emitted_hex'])
 result=dict(passed=True,capability_version=4,ASIO_version=4,ASIO_bytes=48,terminal_sha256=parent,runner_sha256=child,
  recorder_sha256=sha('standalone/record_aspect_script_label.py'),reports=reports,
  retained_rebuild_observation=read('build/application-source-proof-history/label-stale-UART-diagnostic/diagnosis.json'),
  retained_failed_observation=dict(path=failure,checks_sha256=sha(failure+'/checks.json'),diagnosis_sha256=sha(failure+'/diagnosis.json'),diagnosis=diagnosis),
  limitations=['Unconstrained emulator max cycles can hit existing bounded end-wait pacing5; fixed12000 fixture is an explicit measured clock.',
   'Native admission policy, DOS62/MSR and scalar peers are explicit CPU test boundaries; actual DOS parent/child evidence is separate.',
   'DOS ASP compilation/fallback, remaining command/compiler/recorder/UI/services and physical Wi-Fi modem validation remain required.',
   'ENiGMA stock immediate forwarding remains unresolved; the successful regression uses explicit30ms modem buffering.'],whole_application_gates_closed=[])
 (ROOT/'docs/validation/aspect-script-label.json').write_text(json.dumps(result,indent=2)+'\n')
 print('Bound',len(reports),'current reports; capability4 label operation; no application gate closed')
if __name__=='__main__':main()
