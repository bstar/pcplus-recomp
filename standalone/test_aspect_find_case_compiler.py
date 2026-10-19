#!/usr/bin/env python3
"""Original-free FIND/SWITCH bounded conformance and novel graph emission."""
import hashlib,json,re,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/aspect'))
import compiler

def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 fixture=ROOT/'standalone/fixtures/aspect_find_case_compiler_vectors.json';c=json.loads(fixture.read_text());counts=dict(accepted=0,rejected=0,accepted_variants=0,rejected_variants=0,novel_emission=0)
 def alter(source):
  changed=re.sub(r'"[^"\r\n]*"|[a-zA-Z_$][a-zA-Z_0-9$]*',lambda m:m[0]if m[0].startswith('"')else({'result':'matched_offset','target':'selected_value','haystack':'search_buffer'}.get(m[0].lower(),m[0])).upper(),source)
  return '\n'.join('\t '+line+'  'for line in changed.splitlines())
 for v in c['vectors']:
  assert sha(v['source'].encode('cp437'))==v['source_sha256'];expected=bytes.fromhex(v['hex']);assert sha(expected)==v['asx_sha256'];assert compiler.compile_source(v['source'])==expected,v['label'];counts['accepted']+=1;assert compiler.compile_source(alter(v['source']))==expected,v['label'];counts['accepted_variants']+=1
 for v in c['rejected']:
  assert sha(v['source'].encode('cp437'))==v['source_sha256']
  for key,source in [('rejected',v['source']),('rejected_variants',alter(v['source']))]:
   try:compiler.compile_source(source)
   except compiler.CompileError:counts[key]+=1
   else:raise AssertionError(('Unexpectedaccept',v['label'],key))
 # Novel sourceconstants with independently specified fixedlayout.
 for value in (0,5,127,128,255):
  selected=(value+1)&255;answer=value+200
  source=f'integer answer\nproc main\nswitch {value}\ncase {selected}\nanswer={answer}\nendcase\nendswitch\nendproc\n'
  expected=bytes.fromhex('00 cf b8 b5')+bytes([value])+struct.pack('<I',9)+bytes([15])+struct.pack('<I',28)+bytes([181,selected])+bytes.fromhex('5b00 8d00 ab')+struct.pack('<H',answer)+bytes([98])+struct.pack('<I',28)+bytes([148]);assert compiler.compile_source(source)==expected;counts['novel_emission']+=1
 source='string buffer_a,buffer_b\ninteger match_at\nproc main\nfind buffer_a buffer_b match_at\nendproc\n';assert compiler.compile_source(source)==bytes.fromhex('02cf3b8c008c01018d0094');counts['novel_emission']+=1
 # RealCASE/default/end targets crossing16-bit boundary, no substituted VM.
 source='integer answer\nproc main\nswitch 1\ncase 1\n'+'answer=1\n'*10000+'endcase\ndefault\nanswer=2\nendcase\nendswitch\nendproc\n';wire=compiler.compile_source(source);assert len(wire)==70034;assert int.from_bytes(wire[5:9],'little')==9;assert int.from_bytes(wire[10:14],'little')==70021;assert wire[70016]==0x62 and int.from_bytes(wire[70017:70021],'little')==70033;assert wire[70028]==0x62 and int.from_bytes(wire[70029:70033],'little')==70033;counts['novel_emission']+=1
 out=ROOT/'build/aspect-find-case-compiler';out.mkdir(parents=True,exist_ok=True);report=dict(passed=True,original_inputs=[],compiler_sha256=sha(Path(compiler.__file__).read_bytes()),checker_sha256=sha(Path(__file__).read_bytes()),fixture_sha256=sha(fixture.read_bytes()),counts=counts,scope='Compilergrammar/emission only; not runtime FIND/SWITCH/BREAK availability or complete ASPECTcompilercoverage.');(out/'checks.json').write_text(json.dumps(report,indent=2)+'\n');print('FIND/SWITCHcompiler',counts,'PASS')
if __name__=='__main__':main()
