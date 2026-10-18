#!/usr/bin/env python3
"""Record the tested static far-code ABI and actual DOS retention checkpoint."""
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
 assert layout==manifest['memory_layout']
 cpu=read('build/terminal/far-code-live-checks.json')
 for p,want in cpu['source_sha256'].items():assert sha(p)==want,p
 child=read('build/far-storage-dos/checks.json')
 regression=read('build/terminal/far-code-final-regression.json')
 ymodem=read('build/terminal/terminal-ymodem-live-checks.json')
 source=read('docs/validation/terminal-source-build.json')
 for data in (cpu,child,regression,ymodem,source):assert data['passed'] and data['binary_sha256']==runtime
 expected=(ROOT/'Makefile').read_text().split('test-terminal: terminal\n',1)[1].split('\n\n',1)[0].splitlines()
 assert [c['command'] for c in regression['commands']]==[c.strip() for c in expected]
 assert all(c['exit_code']==0 for c in regression['commands'])
 assert child['checks']['far_code_sum_and_extent_survive_child_allocation_fill']
 assert source['matches_workspace_manifest'] and source['matches_workspace_binary']
 inputs=['standalone/record_far_code.py','standalone/check_far_code_live.py','standalone/terminal_memory.py','standalone/dos_image.py','standalone/check_transport.py','standalone/check_terminal_capture_live.py','standalone/far_storage_child.asm','standalone/test_far_storage_dos.py','standalone/build_terminal.py','src/terminal/far_bridge.inc','src/terminal/controller_abi.inc','src/terminal/controller_bridge.asm','src/terminal/print_controller.asm']
 paths=['build/terminal/far-code-live-checks.json','build/far-storage-dos/checks.json','build/far-storage-dos/FARTEST.COM','build/connection-dos/far-storage/FARTEST.BIN','build/terminal/far-code-final-regression.json','build/terminal/far-code-final-regression.log','build/terminal/terminal-ymodem-live-checks.json']
 result=dict(passed=True,binary_sha256=runtime,memory_layout=layout,linked_checks=cpu,DOS_child=child,terminal_regression=regression,YMODEM_inputs=ymodem['inputs'],source_rebuild=dict(report='docs/validation/terminal-source-build.json',binary_sha256=source['binary_sha256'],source_snapshot_sha256=source['source_snapshot_sha256']),source_sha256={p:sha(p) for p in inputs},retained_artifacts={p:sha(p) for p in paths},development_findings=[dict(case='caller fixture beyond STACK overwrote new far code',fix='Stage fixture bytes in the unused bottom of the real stack; reject execution into that caller region and allow the distinct DOS EXEC stack.'),dict(binary_sha256='54cb72d4604b46f312db268892dc216fc341fc466b160f342f61a6fde06ab026',case='raw PRN stack parameter read bridge frame; all256 oracle saw repeated A0',fix='Explicit AX-to-near-stack adapter; all256 actual DOS and linked byte checks pass on the selected current build.'),dict(binary_sha256='e93baa024f0fcdfbffa1edbeb9b50693962632843f34e7e0a368c4a3e593db20',case='ordered AUTO grouping retained one CS',fix='Explicit PRINT_GROUP and paragraph alignment; independent structural/runtime checks require a distinct CS.')],scope='Static source-built far controller code with resident near ABI, explicit register/no-argument service bridges and one AX-to-stack PRN adapter. DOS child extent and before/after far-code byte sum verified under actual allocation/fill; linked tests execute real UART ISR/IRET and reject malformed MZ/maps. Not general stack-argument forwarding, dynamic overlay loading, complete application segmentation or physical hardware validation.')
 (ROOT/'docs/validation/terminal-far-code.json').write_text(json.dumps(result,indent=2)+'\n')
 print('Recorded static far-code checkpoint',runtime)
if __name__=='__main__':main()
