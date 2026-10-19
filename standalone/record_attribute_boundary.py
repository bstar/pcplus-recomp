#!/usr/bin/env python3
"""Bind recovered attribute navigation to checked far application integration."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def main():
 component_path='build/attribute-boundary/checks.json';component=read(component_path)
 assert component['passed'] and component['cases']==718
 assert component['checker_sha256']==sha('standalone/check_attribute_boundary.py')
 assert component['manifest_sha256']==sha('build/attribute-boundary/manifest.json')
 manifest=read('build/attribute-boundary/manifest.json')
 for p,h in manifest['sources'].items():assert sha(p)==h,p
 live_path='build/terminal-key-output/reverse-tab-checks.json';live=read(live_path)
 assert live['passed'] and live['checker_sha256']==sha('standalone/check_terminal_reverse_tab.py')
 assert live['binary_sha256']==sha('build/terminal/TERMINAL.EXE')
 proof_path='docs/validation/application-components-source-build.json';proof=read(proof_path)
 assert proof['passed'] and proof['output_count']>=164 and all(v['matches_workspace'] for v in proof['outputs'].values())
 assert proof['outputs']['terminal/TERMINAL.EXE']['sha256']==live['binary_sha256']
 for name in ('boundary','position','offset','divide'):
  for suffix in ('bin','obj'):
   p='attribute-boundary/'+name+'.'+suffix
   assert proof['outputs'][p]['sha256']==sha('build/'+p)
 layout=read('build/terminal/manifest.json')['memory_layout']
 assert all(s['bytes']<=65536 for s in layout['code_segments'])
 result=dict(passed=True,production_integration=True,recorder_sha256=sha(Path(__file__).relative_to(ROOT)),
  builder_sha256=sha('standalone/build_attribute_boundary.py'),provenance=read('reconstruction/attribute_boundary/provenance.json'),
  component=dict(path=component_path,sha256=sha(component_path),checks=component),
  linked=dict(path=live_path,sha256=sha(live_path),checks=live),code_segments=layout['code_segments'],
  source_build_outputs=proof['output_count'],source_build_proof_sha256=sha(proof_path),original_inputs=[],whole_application_gates_closed=[],
  limitations=['Application admission supports consistent80-column,1..25-row B800 geometry; viewport ownership is unfinished.',
               'The notice uses the maintained BIOS bell provider, rather than original PIT tone timing/settings.',
               'Protected scrolling now binds native repair2D98; general viewport services and original line-edit metadata ownership remain unfinished.',
               'Component cursor/notice endpoints and application BIOS/CRT hardware are explicitly modeled; physical machine/modem/audio validation remains open.'])
 (ROOT/'docs/validation/attribute-boundary.json').write_text(json.dumps(result,indent=2)+'\n')
 print('Bound exact attribute routines and checked far production navigation; no whole-application gates closed')
if __name__=='__main__':main()
