#!/usr/bin/env python3
"""Bind native reverse-tab component evidence without claiming integration."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def read(p):return json.loads((ROOT/p).read_text())
def main():
 path='build/keyboard-reverse-tab/checks.json';checks=read(path)
 assert checks['passed'] and checks['cases']==3846
 assert checks['checker_sha256']==sha('standalone/check_keyboard_reverse_tab.py')
 assert checks['native_recursion_counterexample']['real_recovered_cursor_left']
 manifest=read('build/keyboard-reverse-tab/manifest.json')
 assert checks['manifest_sha256']==sha('build/keyboard-reverse-tab/manifest.json')
 for p,h in manifest['sources'].items():assert sha(p)==h,p
 proof_path='docs/validation/application-components-source-build.json';proof=read(proof_path)
 assert proof['passed'] and proof['output_count']>=156
 assert all(v['matches_workspace'] for v in proof['outputs'].values())
 for leaf in ('reverse_tab.bin','reverse_tab.obj','left-oracle.bin'):
  p='keyboard-reverse-tab/'+leaf
  assert proof['outputs'][p]['sha256']==sha('build/'+p)
 live_path='build/terminal-key-output/reverse-tab-checks.json';live=read(live_path)
 assert live['passed'] and live['cases']==630
 assert live['checker_sha256']==sha('standalone/check_terminal_reverse_tab.py')
 assert live['binary_sha256']==sha('build/terminal/TERMINAL.EXE')
 assert proof['outputs']['terminal/TERMINAL.EXE']['sha256']==live['binary_sha256']
 dos_path='build/aspect-keys-dos/reverse-tab-01/checks.json';dos=read(dos_path)
 assert dos['passed'] and len(dos['cases'])==16
 assert dos['terminal_sha256']==live['binary_sha256']
 assert dos['checker_sha256']==sha('standalone/test_aspect_keys_dos.py')
 assert all(c['passed'] and all(c['checks'].values()) for c in dos['cases'])
 report=dict(passed=True,production_integration=True,recorder_sha256=sha(Path(__file__).relative_to(ROOT)),
  builder_sha256=sha('standalone/build_keyboard_reverse_tab.py'),checks=checks,
  report_path=path,report_sha256=sha(path),provenance=read('reconstruction/keyboard_reverse_tab/provenance.json'),
  source_build_outputs=proof['output_count'],source_build_proof_sha256=sha(proof_path),
  linked=dict(path=live_path,sha256=sha(live_path),checks=live),DOS=dict(path=dos_path,sha256=sha(dos_path),cases=16),
  original_inputs=[],whole_application_gates_closed=[],
  remaining=['Complete protected scrolling/repair and general viewport services; their unsafe paths remain pre-wire rejections.',
             'Complete original audio/settings behavior; the notice currently uses the maintained BIOS bell provider.',
             'Finish local-key UI/macros, all application gates and physical-machine/modem validation.'])
 (ROOT/'docs/validation/keyboard-reverse-tab.json').write_text(json.dumps(report,indent=2)+'\n')
 print('Bound native reverse-tab production integration, DOS scenarios and source-only rebuild; whole-application gates remain open')
if __name__=='__main__':main()
