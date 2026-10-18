#!/usr/bin/env python3
"""Bind the pre-connect setup workflow to current runtime and full regression."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(path):return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
def read(path):return json.loads((ROOT/path).read_text())
def main():
 runtime=sha('build/terminal/TERMINAL.EXE');editor=sha('build/setup/PRMEDIT.EXE')
 manifest=read('build/terminal/manifest.json')
 assert manifest['binary_sha256']==runtime
 for path,want in manifest['sources'].items():assert sha(path)==want,path
 linked=read('build/setup-startup/linked.json');dos=read('build/setup-startup/checks.json')
 assert linked['passed'] and linked['binary_sha256']==runtime
 assert dos['passed'] and dos['terminal_sha256']==runtime and dos['editor_sha256']==editor
 for report in (linked,dos):
  for path,want in report['sources'].items():assert sha(path)==want,path
 assert len(dos['cases'])==12 and all(c['passed'] and all(c['checks'].values()) for c in dos['cases'])
 regression=read('build/terminal/setup-profile-regression.json')
 assert regression['passed'] and regression['complete'] and regression['binary_sha256']==runtime
 expected=subprocess.check_output(['make','-n','test-terminal'],cwd=ROOT,text=True).splitlines()
 assert [c['command'] for c in regression['commands']]==expected
 assert all(c['exit_code']==0 for c in regression['commands'])
 source=read('docs/validation/terminal-source-build.json')
 assert source['passed'] and source['binary_sha256']==runtime and source['matches_workspace_binary'] and source['matches_workspace_manifest']
 options=read('build/terminal-options/checks.json');assert options['passed'] and options['binary_sha256']==runtime
 flags=read('build/terminal/modem-far-checks.json');assert flags['passed'] and flags['binary_sha256']==runtime
 artifacts=['build/setup-startup/linked.json','build/setup-startup/checks.json','build/terminal/setup-profile-regression.json','build/terminal/setup-profile-regression.log','build/terminal/setup-startup-regression-attempt1.json','build/terminal/setup-startup-regression-attempt1.log','build/terminal/modem-far-checks.json','build/terminal-options/checks.json']
 result=dict(passed=True,binary_sha256=runtime,editor_sha256=editor,memory_layout=manifest['memory_layout'],linked_inputs=sum(c['inputs'] for c in linked['cases']),DOS_workflow_groups=len(dos['cases']),CLI_parser_inputs=options['inputs'],terminal_regression=regression,source_rebuild=dict(report='docs/validation/terminal-source-build.json',source_snapshot_sha256=source['source_snapshot_sha256']),retained_artifacts={p:sha(p) for p in artifacts},recorder_sha256=sha('standalone/record_setup_startup.py'),initial_regression_failure='Retained attempt1 stopped at a near/far expander PF inequality. The expander ABI guarantees CF; internal ADD SP,4 makes incidental flags depend on the actual frame address. No runtime bridge was changed. Current test compares declared CF across frames and separately observes every actual target RET to require complete FLAGS preservation through the bridge.',scope='Maintained explicit direct editor child before UART acquisition, then normal validated import and CLI overrides. Actual DOS editor, independent hardware/video/timer/protocol evidence, linked scheduler, full current terminal regressions and isolated source rebuild are separate checks. No live connected setup, original PCSETUP shared parent protocol, defaults, complete schema/application or physical modem claim.')
 for name,data in [('setup-startup-linked.json',linked),('setup-startup-dos.json',dos),('setup-startup.json',result)]:
  (ROOT/'docs/validation'/name).write_text(json.dumps(data,indent=2)+'\n')
 print('Recorded setup startup',runtime,len(regression['commands']),'regression commands')
if __name__=='__main__':main()
