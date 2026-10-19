#!/usr/bin/env python3
"""Record exact source recovery, CPU replay and an independent clean rebuild."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def read(p):return json.loads((ROOT/p).read_text())
def main():
 manifest=read('build/attribute-repair/manifest.json');checks=read('build/attribute-repair/checks.json')
 assert checks['passed'] and checks['cases']==1928 and checks['groups']==dict(repair=1860,advance=32,write=36)
 assert checks['checker_sha256']==sha('standalone/check_attribute_repair.py')
 assert checks['manifest_sha256']==sha('build/attribute-repair/manifest.json')
 for p,h in manifest['sources'].items():assert sha(p)==h,p
 proof=read('docs/validation/application-components-source-build.json')
 assert proof['passed'] and proof['output_count']>=178
 for p,h in manifest['outputs'].items():
  assert sha(p)==h and proof['outputs'][str(Path(p).relative_to('build'))]['sha256']==h,p
 result=dict(passed=True,production_integration=False,builder_sha256=sha('standalone/build_attribute_repair.py'),
  recorder_sha256=sha(Path(__file__).relative_to(ROOT)),provenance=read('reconstruction/attribute_repair/provenance.json'),
  checks=checks,sources=manifest['sources'],outputs=manifest['outputs'],source_build_outputs=proof['output_count'],
  source_build_proof_sha256=sha('docs/validation/application-components-source-build.json'),original_inputs=[],whole_application_gates_closed=[],
  limitations=['Component is not yet bound to application2D98; existing protected-path pre-wire admission is unchanged.',
   'Viewport advance caches native visibility until left/physical-width/row boundaries; arbitrary right edges and inactive-left0 quirks are characterized, not fixed.',
   'Only CGA retrace input is modeled; physical display, modem and timing validation remain open.'])
 (ROOT/'docs/validation/attribute-repair.json').write_text(json.dumps(result,indent=2)+'\n')
 print('Recorded exact399-byte attribute repair and1928 CPU cases; no application gate closed')
if __name__=='__main__':main()
