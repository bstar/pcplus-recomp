#!/usr/bin/env python3
"""Bind serviced redisplay to current linked, real-DOS and Nix rebuild evidence."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def sources(report,key='sources'):
 for p,h in report.get(key,{}).items():assert sha(p)==h,p
def main():
 runtime=sha('build/terminal/TERMINAL.EXE');manifest=read('build/terminal/manifest.json');sources(manifest)
 assert manifest['binary_sha256']==runtime
 linked=read('build/terminal/redisplay-checks.json');dos=read('build/redisplay-dos/checks.json')
 for r in [linked,dos]:assert r['passed'] and r['binary_sha256']==runtime;sources(r)
 assert linked['inputs']==39 and len(linked['cases'])==7
 assert all(dos['checks'].values())
 memory=manifest['memory_layout']
 assert memory['history_bytes']==memory['redisplay_snapshot_bytes']==63000
 assert memory['far_ui_storage_bytes']==20000 and memory['redisplay_bridge_pairs_verified']==4
 assert memory['far_code_bridge_pairs_verified']==87 and memory['configuration_bridge_pairs_verified']==38
 frames=read('build/terminal/config-far-checks.json')
 assert frames['passed'] and frames['binary_sha256']==runtime and len(frames['rejected_mutations'])==187
 native=read('build/far-storage/linked-checks.json');child=read('build/far-storage-dos/checks.json')
 for r in [native,child]:assert r['passed'] and r['binary_sha256']==runtime
 assert all(child['checks'].values()) and child['linker_defines']['FAR_END_OFFSET']-child['linker_defines']['HISTORY_OFFSET']==63000
 regression=read('build/terminal/setup-profile-regression.json')
 expected=subprocess.check_output(['make','-n','test-terminal'],cwd=ROOT,text=True).splitlines()
 assert len(expected)==77 and regression['passed'] and regression['complete'] and regression['binary_sha256']==runtime
 assert [c['command'] for c in regression['commands']]==expected and all(c['exit_code']==0 for c in regression['commands'])
 proof=read('docs/validation/application-components-source-build.json')
 assert proof['passed'] and proof['output_count']==64 and proof['outputs']['terminal/TERMINAL.EXE']['sha256']==runtime
 export=read('docs/validation/history-export.json');assert export['passed'] and export['binary_sha256']==runtime
 artifacts=['build/terminal/redisplay-checks.json','build/redisplay-dos/checks.json','build/far-storage/linked-checks.json','build/far-storage-dos/checks.json','build/terminal/setup-profile-regression.json','build/terminal/setup-profile-regression.log']
 folder=ROOT/'build/connection-dos/redisplay-live'
 artifacts.extend(str(p.relative_to(ROOT)) for p in sorted(folder.iterdir()) if p.is_file())
 inputs=['standalone/record_redisplay.py','standalone/check_redisplay_live.py','standalone/test_redisplay_dos.py','standalone/redisplay_watch.asm','standalone/test_connection_dos.py','standalone/check_far_storage_live.py','standalone/test_far_storage_dos.py','standalone/far_storage_child.asm','standalone/terminal_memory.py','standalone/build_terminal.py']
 result=dict(passed=True,binary_sha256=runtime,memory_layout=memory,linked=linked,actual_DOS=dos,history_export=dict(report='docs/validation/history-export.json',linked_inputs=27,actual_DOS_cases=3),native_history=native,actual_DOS_child=child,call_frames=frames,terminal_regression=regression,runtime_sources=manifest['sources'],sources={p:sha(p) for p in inputs},retained_artifacts={p:sha(p) for p in artifacts},source_rebuild=dict(report='docs/validation/application-components-source-build.json',source_snapshot_sha256=proof['source_snapshot_sha256'],output_count=64),scope='Maintained live redisplay,63000-byte native ring and frozen copy, line/page/Home/End browsing, ASCII case-insensitive incremental search/F3, live input and cursor replies during browsing, cancellation and restoration.39 linked inputs, one independent actual DOS observer workflow, native full-capacity/wrap and DOS child allocation evidence,77-command terminal regression and64 byte-identical Nix outputs. Clipboard transfer prompts, original complete UI, other video modes and physical serial/video remain open; F11 is not closed.')
 (ROOT/'docs/validation/redisplay-live.json').write_text(json.dumps(result,indent=2)+'\n');print('Recorded serviced redisplay',runtime)
if __name__=='__main__':main()
