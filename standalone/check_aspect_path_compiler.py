#!/usr/bin/env python3
"""Frozen original-compiler accepted/rejected grammar, without original inputs."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/aspect'))
from compiler import compile_source,CompileError

def main():
 fixture=ROOT/'standalone/fixtures/aspect_path_compiler_vectors.json';d=json.loads(fixture.read_text());accepted=0;rejected=0
 for case in d['cases']:
  assert hashlib.sha256(case['source'].encode('cp437')).hexdigest()==case['source_sha256']
  try:result=compile_source(case['source'])
  except CompileError:
   assert not case['success'],case['label'];rejected+=1
  else:
   assert case['success'] and result==bytes.fromhex(case['hex']) and hashlib.sha256(result).hexdigest()==case['asx_sha256'],case['label'];accepted+=1
 assert (accepted,rejected)==(24,32)
 out=ROOT/'build/aspect-paths';out.mkdir(parents=True,exist_ok=True)
 (out/'compiler-checks.json').write_text(json.dumps(dict(passed=True,accepted=accepted,rejected=rejected,fixture_sha256=hashlib.sha256(fixture.read_bytes()).hexdigest(),compiler_sha256=hashlib.sha256((ROOT/'src/aspect/compiler.py').read_bytes()).hexdigest(),checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),original_inputs=[],scope='Exact accepted ASX and rejected source behavior for56 frozen authored compiler cases, independent of DOS runtime/filesystem semantics.'),indent=2)+'\n');print('Path compiler:',accepted,'accepted,',rejected,'rejected PASS')
if __name__=='__main__':main()
