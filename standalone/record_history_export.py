#!/usr/bin/env python3
"""Record the maintained serviced history append feature and its verification."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(path):return json.loads((ROOT/path).read_text())
def sha(path):return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
def sources(report):
 for path,digest in report.get('sources',{}).items():assert sha(path)==digest,path
def main():
 runtime=sha('build/terminal/TERMINAL.EXE');manifest=read('build/terminal/manifest.json');sources(manifest)
 linked=read('build/terminal/history-export-checks.json');dos=read('build/history-export-dos/checks.json')
 for report in (linked,dos):assert report['passed'] and report['binary_sha256']==runtime;sources(report)
 assert linked['inputs']==27 and len(linked['cases'])==9
 assert len(dos['cases'])==3 and all(all(c['checks'].values()) for c in dos['cases'])
 frames=read('build/terminal/config-far-checks.json');assert frames['passed'] and frames['binary_sha256']==runtime
 assert frames['configuration_bridge_pairs_verified']==36 and len(frames['rejected_mutations'])==173
 owners=read('build/capture-owners/result.json');monitor=read('build/monitor-file/result.json')
 for report in (owners,monitor):assert report['passed'] and report['static_state_bytes']==920;sources(report)
 regression=read('build/terminal/setup-profile-regression.json')
 expected=subprocess.check_output(['make','-n','test-terminal'],cwd=ROOT,text=True).splitlines()
 assert len(expected)==75 and regression['passed'] and regression['complete'] and regression['binary_sha256']==runtime
 assert [c['command'] for c in regression['commands']]==expected and all(c['exit_code']==0 for c in regression['commands'])
 proof=read('docs/validation/application-components-source-build.json')
 assert proof['passed'] and proof['output_count']==64 and proof['outputs']['terminal/TERMINAL.EXE']['sha256']==runtime
 inputs=['standalone/record_history_export.py','standalone/check_history_export_live.py','standalone/test_history_export_dos.py','standalone/check_capture_owners.py','standalone/check_monitor_file.py','standalone/test_connection_dos.py','standalone/redisplay_watch.asm']
 artifacts=['build/terminal/history-export-checks.json','build/history-export-dos/checks.json','build/terminal/config-far-checks.json','build/capture-owners/result.json','build/monitor-file/result.json','build/terminal/setup-profile-regression.json']
 for name in ('history-create','history-append-repeat','history-denied'):
  folder=ROOT/'build/connection-dos'/name
  artifacts.extend(str(p.relative_to(ROOT)) for p in sorted(folder.iterdir()) if p.is_file())
 result=dict(passed=True,binary_sha256=runtime,memory_layout=manifest['memory_layout'],linked=linked,actual_DOS=dos,call_frames=frames,shared_owners=dict(capture_and_snapshot=owners,monitor=monitor),terminal_regression=regression,runtime_sources=manifest['sources'],sources={p:sha(p) for p in inputs},retained_artifacts={p:sha(p) for p in artifacts},source_rebuild=dict(report='docs/validation/application-components-source-build.json',source_snapshot_sha256=proof['source_snapshot_sha256'],output_count=64),scope='W in maintained redisplay appends its frozen chronological history. Exclusive missing-file creation, same-handle DWORD append, CRLF expansion including125998-byte full-ring output,128-source-byte foreground write budget, continued native receive, cancellation/partial prefixes, canonical four-owner exclusion and exact-once ambiguous close.27 linked inputs,3 actual DOS workflows,173 malformed frames/layouts,75 terminal commands and64 byte-identical Nix outputs. Original clipboard/full UI, physical disk timing/serial throughput and crash-atomic append remain open.')
 (ROOT/'docs/validation/history-export.json').write_text(json.dumps(result,indent=2)+'\n');print('Recorded serviced history export',runtime)
if __name__=='__main__':main()
