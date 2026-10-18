#!/usr/bin/env python3
"""Bind clipboard core/original/live/DOS evidence to the current source build."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(path):return json.loads((ROOT/path).read_text())
def sha(path):return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
def sources(report):
 for path,digest in report.get('sources',{}).items():assert sha(path)==digest,path

def main():
 runtime=sha('build/terminal/TERMINAL.EXE');manifest=read('build/terminal/manifest.json');sources(manifest)
 core_manifest=read('build/clipboard/manifest.json');sources(core_manifest)
 core_digest=sha('build/clipboard/CLIPCORE.EXE');assert core_manifest['binary_sha256']==core_digest
 core=read('build/clipboard/linked-checks.json');original=read('build/clipboard/original-checks.json');core_dos=read('build/clipboard/dos-checks.json')
 for r in (core,original,core_dos):assert r['passed'] and r['binary_sha256']==core_digest;sources(r)
 assert core['inputs']==original['inputs']==614 and original['original_comparisons']==321
 assert core_dos['checks']==559 and not core_dos['failures']
 linked=read('build/terminal/clipboard-live-checks.json');dos=read('build/clipboard-live-dos/checks.json')
 for r in (linked,dos):assert r['passed'] and r['binary_sha256']==runtime;sources(r)
 assert linked['inputs']==46 and len(linked['groups'])==8
 assert len(dos['cases'])==2 and all(all(c['checks'].values()) for c in dos['cases'])
 frames=read('build/terminal/config-far-checks.json');assert frames['passed'] and frames['binary_sha256']==runtime and len(frames['rejected_mutations'])==187
 assert manifest['memory_layout']['configuration_bridge_pairs_verified']==38 and manifest['memory_layout']['far_code_bridge_pairs_verified']==87
 regression=read('build/terminal/setup-profile-regression.json')
 expected=subprocess.check_output(['make','-n','test-terminal'],cwd=ROOT,text=True).splitlines()
 assert len(expected)==77 and regression['passed'] and regression['complete'] and regression['binary_sha256']==runtime
 assert [c['command'] for c in regression['commands']]==expected and all(c['exit_code']==0 for c in regression['commands'])
 proof=read('docs/validation/application-components-source-build.json');assert proof['passed'] and proof['output_count']==64
 for name,digest in [('terminal/TERMINAL.EXE',runtime),('clipboard/CLIPCORE.EXE',core_digest)]:
  assert proof['outputs'][name]['sha256']==digest and proof['outputs'][name]['matches_workspace']
 paths=['build/clipboard/manifest.json','build/clipboard/linked-checks.json','build/clipboard/original-checks.json','build/clipboard/dos-checks.json','build/terminal/clipboard-live-checks.json','build/clipboard-live-dos/checks.json','build/terminal/config-far-checks.json','build/terminal/setup-profile-regression.json']
 for name in ('clipboard-live-list','clipboard-live-cut'):
  paths.extend('build/connection-dos/'+name+'/'+p for p in ['dosbox.conf','serial.bin','SCREEN.BIN','CWATCH.BIN','BEFORE.BIN','AFTER.BIN'])
 inputs=['standalone/record_clipboard.py','standalone/check_clipboard.py','standalone/check_clipboard_live.py','standalone/test_clipboard_dos.py','standalone/test_clipboard_live_dos.py','standalone/clipboard_watch.asm','standalone/clipboard_self_test.c','standalone/clipboard_host.asm','standalone/build_clipboard.py']
 result=dict(passed=True,binary_sha256=runtime,core_binary_sha256=core_digest,memory_layout=manifest['memory_layout'],core=core,original=original,core_actual_DOS=core_dos,linked=linked,actual_DOS=dos,call_frames=frames,terminal_regression=regression,runtime_sources=manifest['sources'],sources={p:sha(p) for p in inputs},retained_artifacts={p:sha(p) for p in paths},source_rebuild=dict(report='docs/validation/application-components-source-build.json',source_snapshot_sha256=proof['source_snapshot_sha256'],output_count=64),scope='Maintained serviced15-entry filename clipboard over redisplay frame ownership. Original extraction/list/packet semantics preserved with bounded row/field handling; edited holes retain separator behavior. Whole-packet empty-ring admission, actual UART-write Single commit, partial cancel preserving later replies and connection-queue-discard failure.614 core inputs,321 controlled genuine-original comparisons,559 actual8086 DOS core assertions,46 linked application inputs,two independent DOS UI/peer workflows,187 rejected configuration ABI mutations,77-command terminal regression and64 source-only byte-identical outputs. Saved separator adoption/persistence is recorded in clipboard-settings.json. Original complete UI, transfer prompt workflows, other geometries and physical UART remain open; F11 is not closed.')
 (ROOT/'docs/validation/clipboard.json').write_text(json.dumps(result,indent=2)+'\n');print('Recorded clipboard',runtime)
if __name__=='__main__':main()
