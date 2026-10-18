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
 regression=read('build/terminal/live-configuration-regression.json')
 assert regression['passed'] and regression['complete'] and regression['binary_sha256']==terminal['binary_sha256']
 assert [c['command'] for c in regression['commands']]==subprocess.check_output(['make','-n','test-terminal'],cwd=ROOT,text=True).splitlines()
 assert all(c['exit_code']==0 for c in regression['commands'])
 proof=read('docs/validation/application-components-source-build.json')
 assert proof['passed']
 for name,digest in [('terminal/TERMINAL.EXE',terminal['binary_sha256']),('live-configuration/LIVE.EXE',candidate['binary_sha256'])]:
  assert proof['outputs'][name]['matches_workspace'] and proof['outputs'][name]['sha256']==digest
 listing=(ROOT/'build/terminal/terminal.map').read_text()
 assert '_directory_live_decode' in listing and '_live_configuration_decode' not in listing
 paths=['build/live-configuration/checks.json','build/live-configuration/manifest.json','build/terminal/directory-live-checks.json','build/terminal/live-configuration-regression.json','build/terminal/live-configuration-regression.log']
 report=dict(passed=True,terminal_sha256=terminal['binary_sha256'],diagnostic_sha256=candidate['binary_sha256'],candidate_linked_into_terminal=False,shared_directory_decoder_linked_into_terminal=True,candidate_checks=checks,directory_regression=directory,terminal_regression=regression,terminal_memory_layout=terminal['memory_layout'],source_rebuild=dict(report='docs/validation/application-components-source-build.json',source_snapshot_sha256=proof['source_snapshot_sha256'],output_count=proof['output_count']),retained_artifacts={p:sha(p) for p in paths},recorder_sha256=sha('standalone/record_live_configuration.py'),scope='Pure validated candidate and semantic change classification with retained directory selection and CLI precedence. Shared decoder used by current terminal file owner with full regression and isolated rebuild. Diagnostic candidate API is not yet wired into running-terminal setup, commit/rollback, UART/profile handoff or reset-baseline ownership. No complete application or physical modem claim.')
 (ROOT/'docs/validation/live-configuration-plan.json').write_text(json.dumps(report,indent=2)+'\n')
 print('Recorded candidate',checks['inputs'],'inputs; directory',directory['inputs'],'inputs; full regression',len(regression['commands']),'commands')
if __name__=='__main__':main()
