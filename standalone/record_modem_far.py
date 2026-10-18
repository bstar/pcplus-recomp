#!/usr/bin/env python3
"""Bind modem far ABI, actual DOS retention, regression and source-only build."""
import hashlib,json
from pathlib import Path
from terminal_memory import inspect_terminal_memory
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def main():
 runtime=sha('build/terminal/TERMINAL.EXE');manifest=read('build/terminal/manifest.json')
 assert manifest['binary_sha256']==runtime
 for p,want in manifest['sources'].items():assert sha(p)==want,p
 layout=inspect_terminal_memory(ROOT/'build/terminal/TERMINAL.EXE',ROOT/'build/terminal/terminal.map')
 assert layout==manifest['memory_layout'] and layout['far_code_bridge_pairs_verified']==44
 assert layout['controller_bridge_pairs_verified']==layout['modem_bridge_pairs_verified']==22
 cpu=read('build/terminal/modem-far-checks.json');printer=read('build/terminal/far-code-live-checks.json')
 child=read('build/far-storage-dos/checks.json');regression=read('build/terminal/modem-far-final-regression.json')
 source=read('docs/validation/terminal-source-build.json')
 for data in (cpu,printer,child,regression,source):assert data['passed'] and data['binary_sha256']==runtime
 for data in (cpu,printer):
  for p,want in data['source_sha256'].items():assert sha(p)==want,p
 expected=(ROOT/'Makefile').read_text().split('test-terminal: terminal\n',1)[1].split('\n\n',1)[0].splitlines()
 assert [c['command'] for c in regression['commands']]==[c.strip() for c in expected]
 assert all(not c['exit_code'] for c in regression['commands'])
 assert child['checks']['modem_far_code_sum_and_extent_survive_child_allocation_fill'] and child['checks']['far_code_sum_and_extent_survive_child_allocation_fill']
 assert len(bytes.fromhex(child['sample_hex']))==56
 assert source['matches_workspace_binary'] and source['matches_workspace_manifest']
 scripts=['standalone/record_modem_far.py','standalone/check_modem_far_live.py','standalone/terminal_memory.py','standalone/dos_image.py','standalone/check_connection.py','standalone/check_transport.py','standalone/test_far_storage_dos.py','standalone/far_storage_child.asm','standalone/build_terminal.py','src/terminal/far_bridge.inc','src/terminal/modem_abi.inc','src/terminal/modem_bridge.asm','src/terminal/connection.asm','src/terminal/modem_sender.asm']
 paths=['build/terminal/modem-far-checks.json','build/terminal/far-code-live-checks.json','build/far-storage-dos/checks.json','build/far-storage-dos/FARTEST.COM','build/connection-dos/far-storage/FARTEST.BIN','build/terminal/modem-far-final-regression.json','build/terminal/modem-far-final-regression.log']
 result=dict(passed=True,binary_sha256=runtime,baseline=dict(commit='30585e2',binary_sha256='c0a9cbaa6c129cc7473b6ddfcc9dc599369634b09ae6dfef946fe8b6ee9b686d',resident_code_bytes=63490,loaded_module_bytes=93786,near_bytes=52384),memory_layout=layout,resident_code_bytes_freed=63490-layout['resident_code_bytes'],loaded_module_bytes_added=layout['loaded_module_bytes']-93786,modem_linked_checks=cpu,printer_linked_checks=printer,DOS_child=child,terminal_regression=regression,source_rebuild=dict(report='docs/validation/terminal-source-build.json',binary_sha256=source['binary_sha256'],source_snapshot_sha256=source['source_snapshot_sha256']),source_sha256={p:sha(p) for p in scripts},retained_artifacts={p:sha(p) for p in paths},scope='Separate static real-mode modem controller/sender CS with unchanged near public names and DS=SS data ABI. Eight entries, ten namespaced register callbacks and four declared1..4-word cdecl adapters; actual target equality/error/FLAGS checks, nested printer/resident/modem calls, real ISR/IRET and malformed-image rejection. Actual DOS child allocation/fill preserves both complete relocated code sums, native storage and three UI screens. Full current terminal regression and independent source-only rebuild are separate evidence. No generic callbacks, callee-cleaned forwarding, dynamic overlays, complete application or physical modem claim.')
 (ROOT/'docs/validation/terminal-modem-far-code.json').write_text(json.dumps(result,indent=2)+'\n')
 print('Recorded modem far code',runtime,'freed',result['resident_code_bytes_freed'],'resident bytes')
if __name__=='__main__':main()
