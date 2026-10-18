#!/usr/bin/env python3
"""Bind the far PROGRAM policy to current CPU, DOS and source-rebuild evidence."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(path):return json.loads((ROOT/path).read_text())
def sha(path):return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
def main():
 runtime=sha('build/terminal/TERMINAL.EXE');manifest=read('build/terminal/manifest.json')
 assert manifest['binary_sha256']==runtime
 for path,digest in manifest['sources'].items():assert sha(path)==digest,path
 memory=manifest['memory_layout']
 assert memory['resident_code_bytes']==64516 and memory['resident_code_spare_bytes']==1020
 assert memory['near_bytes']==62848 and memory['configuration_bridge_pairs_verified']==34
 assert memory['far_code_bridge_pairs_verified']==82
 linked=read('build/terminal/program-actions-live-checks.json')
 dos=read('build/program-actions-dos/checks.json')
 retention=read('build/far-storage-dos/checks.json')
 frames=read('build/terminal/config-far-checks.json')
 for report in (linked,dos,retention,frames):assert report['passed'] and report['binary_sha256']==runtime
 assert linked['inputs']==60 and len(linked['cases'])==9
 assert linked['cases'][0]['inputs']==4 and linked['cases'][0]['passed']
 assert len(dos['cases'])==4 and all(all(c['checks'].values()) for c in dos['cases'])
 assert all(retention['checks'].values()) and len(frames['rejected_mutations'])==167
 regression=read('build/terminal/setup-profile-regression.json')
 expected=subprocess.check_output(['make','-n','test-terminal'],cwd=ROOT,text=True).splitlines()
 assert len(expected)==70 and regression['passed'] and regression['complete'] and regression['binary_sha256']==runtime
 assert [c['command'] for c in regression['commands']]==expected and all(c['exit_code']==0 for c in regression['commands'])
 proof=read('docs/validation/application-components-source-build.json')
 assert proof['passed'] and proof['output_count']==63 and proof['outputs']['terminal/TERMINAL.EXE']['sha256']==runtime
 sources=['src/process/program.c','src/process/dos_exec.h','src/process/dos_exec.asm','src/terminal/config_abi.inc','src/terminal/program_actions.asm','standalone/build_terminal.py','standalone/terminal_memory.py','standalone/check_program_actions_live.py','standalone/test_program_actions_dos.py','standalone/record_program_far.py']
 artifacts=['build/terminal/program-actions-live-checks.json','build/program-actions-dos/checks.json','build/far-storage-dos/checks.json','build/terminal/config-far-checks.json','build/terminal/setup-profile-regression.json']
 result=dict(passed=True,binary_sha256=runtime,memory_layout=memory,linked=linked,actual_DOS=dos,retention=retention,call_frames=frames,terminal_regression=regression,sources={p:sha(p) for p in sources},retained_artifacts={p:sha(p) for p in artifacts},source_rebuild=dict(report='docs/validation/application-components-source-build.json',source_snapshot_sha256=proof['source_snapshot_sha256'],output_count=63),scope='Maintained PROGRAM command policy placement in CONFIG_CODE with unchanged near-cdecl API and resident DOS EXEC backend. Four actual C-return FLAGS observations include child-context clobber, EXEC failures and resize failure;60 linked inputs,4 actual DOS workflows,retained far-code child allocation,167 rejected bridge/layout mutations,70 terminal commands and63 byte-identical Nix outputs. Complete original PROGRAM/ASPECT/UI and physical hardware remain open.')
 (ROOT/'docs/validation/program-far-code.json').write_text(json.dumps(result,indent=2)+'\n')
 print('Recorded PROGRAM far-code checkpoint',runtime)
if __name__=='__main__':main()
