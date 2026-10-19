#!/usr/bin/env python3
"""Compare authored DOS/RUN/SHELL sources to frozen original output."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/aspect'))
import compiler

def main():
 fixture=ROOT/'standalone/fixtures/aspect_external_compiler_vectors.json'
 proof=json.loads(fixture.read_text());accepted=rejected=0
 for case in proof['cases']:
  assert hashlib.sha256(case['source'].encode('cp437')).hexdigest()==case['source_sha256']
  try:actual=compiler.compile_source(case['source'])
  except compiler.CompileError:
   assert not case['success'],case['label'];rejected+=1
  else:
   assert case['success'],case['label']
   assert actual==bytes.fromhex(case['hex']),case['label'];accepted+=1
 report=dict(passed=True,accepted=accepted,rejected=rejected,fixture_sha256=hashlib.sha256(fixture.read_bytes()).hexdigest(),compiler_sha256=hashlib.sha256((ROOT/'src/aspect/compiler.py').read_bytes()).hexdigest(),checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),original_inputs=[])
 out=ROOT/'build/aspect-external';out.mkdir(parents=True,exist_ok=True)
 (out/'compiler-checks.json').write_text(json.dumps(report,indent=2)+'\n')
 print('External compiler:',accepted,'accepted exact,',rejected,'rejected PASS')
if __name__=='__main__':main()
