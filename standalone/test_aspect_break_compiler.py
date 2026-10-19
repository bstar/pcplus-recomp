#!/usr/bin/env python3
"""Original-free BREAK/SET BREAK/FETCH BREAK grammar/encoding checks."""
from pathlib import Path
import hashlib,json,re,struct,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/aspect'))
import compiler

def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 path=ROOT/'standalone/fixtures/aspect_break_compiler_vectors.json';c=json.loads(path.read_text());counts=dict(accepted=0,presentation=0,rejected=0,unsupported=0,novel=0)
 for v in c['vectors']:
  source=v['source'];expected=bytes.fromhex(v['hex']);assert sha(source.encode('cp437'))==v['source_sha256']and sha(expected)==v['asx_sha256'];assert compiler.compile_source(source)==expected,v['label'];counts['accepted']+=1
  changed=re.sub(r'"[^"\r\n]*"|[a-zA-Z_$][a-zA-Z_0-9$]*',lambda m:m[0]if m[0].startswith('"')else({'duration':'retained_delay','delay_units':'child_delay'}.get(m[0].lower(),m[0])).upper(),source);changed='\n'.join('\t '+line+'  'for line in changed.splitlines());assert compiler.compile_source(changed)==expected,v['label'];counts['presentation']+=1
 for key in ['rejected','unsupported']:
  for v in c[key]:
   assert sha(v['source'].encode('cp437'))==v['source_sha256']
   try:compiler.compile_source(v['source'])
   except compiler.CompileError:counts[key]+=1
   else:raise AssertionError((v['label'],'unexpectedaccept'))
 for value in [1,255,256,1000,32767,-2]:
  source=f'proc main\nset break {value}\nendproc\n';operand=bytes([181,value])if 0<=value<=255 else bytes([171])+struct.pack('<H',value&65535);assert compiler.compile_source(source)==bytes.fromhex('00cf9e09')+operand+bytes([148]);counts['novel']+=1
 source='integer other,saved_delay\nproc main\nfetch break saved_delay\nset break 7\nbreak\nset break saved_delay\nendproc\n';assert compiler.compile_source(source)==bytes.fromhex('00cf37098d019e09b5070d9e098d0194');counts['novel']+=1
 out=ROOT/'build/aspect-break-compiler';out.mkdir(parents=True,exist_ok=True);r=dict(passed=True,original_inputs=[],counts=counts,compiler_sha256=sha(Path(compiler.__file__).read_bytes()),checker_sha256=sha(Path(__file__).read_bytes()),fixture_sha256=sha(path.read_bytes()),scope='Compileronly. Nativebounds0..32767; negativeconstantscompilebutnativeboundsreject. FETCHDISPLAYunsupported; no claimof UARTBREAK/runtimeintegration.');(out/'checks.json').write_text(json.dumps(r,indent=2)+'\n');print('BREAKcompiler',counts,'PASS')
if __name__=='__main__':main()
