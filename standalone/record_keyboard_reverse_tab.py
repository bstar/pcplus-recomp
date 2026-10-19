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
 report=dict(passed=True,production_integration=False,recorder_sha256=sha(Path(__file__).relative_to(ROOT)),
  builder_sha256=sha('standalone/build_keyboard_reverse_tab.py'),checks=checks,
  report_path=path,report_sha256=sha(path),provenance=read('reconstruction/keyboard_reverse_tab/provenance.json'),
  source_build_outputs=proof['output_count'],source_build_proof_sha256=sha(proof_path),
  original_inputs=[],whole_application_gates_closed=[],
  remaining=['Bind actual cursor/attribute/division/protected-home services.',
             'Validate table termination/bounds and inconsistent mode combinations before any keyboard wire/echo effect.',
             'Exercise actual DOS display, child-owned UART and error cleanup before enabling production half-duplex reverse Tab.',
             'Recover full Insert/Delete echo services; finish all application gates.'])
 (ROOT/'docs/validation/keyboard-reverse-tab.json').write_text(json.dumps(report,indent=2)+'\n')
 print('Bound reverse-tab component and source-only rebuild; production integration remains open')
if __name__=='__main__':main()
