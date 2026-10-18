#!/usr/bin/env python3
"""Bind pure candidate checks, shared-loader regressions and isolated builds."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(path):return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
def read(path):return json.loads((ROOT/path).read_text())
def verify_sources(report):
 for path,want in report['sources'].items():assert sha(path)==want,path

def main():
 terminal=read('build/terminal/manifest.json');candidate=read('build/live-configuration/manifest.json')
 assert terminal['binary_sha256']==sha('build/terminal/TERMINAL.EXE')
 assert candidate['binary_sha256']==sha('build/live-configuration/LIVE.EXE')
 verify_sources(terminal);verify_sources(candidate)
 checks=read('build/live-configuration/checks.json');verify_sources(checks)
 assert checks['passed'] and checks['inputs']==389 and checks['binary_sha256']==candidate['binary_sha256']
 assert checks['maximum_CPU_call_stack_bytes']<8192
 directory=read('build/terminal/directory-live-checks.json')
 assert directory['passed'] and directory['inputs']==311 and directory['binary_sha256']==terminal['binary_sha256']
 current=read('build/live-configuration/terminal-checks.json');verify_sources(current)
 assert current['passed'] and current['inputs']==389 and current['binary_sha256']==terminal['binary_sha256']
 regression=read('build/terminal/setup-profile-regression.json')
 assert regression['passed'] and regression['complete'] and regression['binary_sha256']==terminal['binary_sha256']
 assert [c['command'] for c in regression['commands']]==subprocess.check_output(['make','-n','test-terminal'],cwd=ROOT,text=True).splitlines()
 assert all(c['exit_code']==0 for c in regression['commands'])
 proof=read('docs/validation/application-components-source-build.json')
 assert proof['passed']
 for name,digest in [('terminal/TERMINAL.EXE',terminal['binary_sha256']),('live-configuration/LIVE.EXE',candidate['binary_sha256'])]:
  assert proof['outputs'][name]['matches_workspace'] and proof['outputs'][name]['sha256']==digest
 listing=(ROOT/'build/terminal/terminal.map').read_text()
 assert '_directory_live_decode' in listing and '_live_configuration_decode' in listing
 setup=read('docs/validation/setup-live.json')
 assert setup['passed'] and setup['binary_sha256']==terminal['binary_sha256']
 paths=['build/live-configuration/checks.json','build/live-configuration/manifest.json','build/live-configuration/terminal-checks.json','build/terminal/directory-live-checks.json','build/terminal/setup-profile-regression.json','build/terminal/setup-profile-regression.log','docs/validation/setup-live.json']
 report=dict(passed=True,terminal_sha256=terminal['binary_sha256'],diagnostic_sha256=candidate['binary_sha256'],candidate_linked_into_terminal=True,shared_directory_decoder_linked_into_terminal=True,candidate_checks=checks,terminal_candidate_checks=current,directory_regression=directory,terminal_regression=regression,terminal_memory_layout=terminal['memory_layout'],live_application=dict(report='docs/validation/setup-live.json',owner_inputs=setup['transaction_owner']['inputs'],selective_inputs=setup['selective_application']['inputs'],profile_inputs=setup['profile_switching']['inputs'],port_DOS_cases=len(setup['port_actual_DOS']['cases'])),source_rebuild=dict(report='docs/validation/application-components-source-build.json',source_snapshot_sha256=proof['source_snapshot_sha256'],output_count=proof['output_count']),retained_artifacts={p:sha(p) for p in paths},recorder_sha256=sha('standalone/record_live_configuration.py'),scope='Pure validated626-byte candidate linked into CONFIG_CODE and used by the canonical live setup transaction owner. Independent389-case near diagnostic and389-case actual-terminal replay, retained directory selection/CLI precedence and full terminal regression. Selective commits, supported-profile resets and confirmed same-port/idle-COM handoffs are bound through the separate current setup report. Live XLT resource/mode switching, connected COM moves, other emulations, complete application and physical modem remain open.')
 (ROOT/'docs/validation/live-configuration-plan.json').write_text(json.dumps(report,indent=2)+'\n')
 print('Recorded candidate',checks['inputs'],'inputs; directory',directory['inputs'],'inputs; full regression',len(regression['commands']),'commands')
if __name__=='__main__':main()
