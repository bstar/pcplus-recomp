#!/usr/bin/env python3
"""Compiler conformance for authored WHEN source and native flow expectations.

No original executable or oracle report is read. --native composes emitted ASX
with source-built exact native components, not the parent/runner application.
"""
import argparse,hashlib,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/aspect'))
import compiler
from compiler import compile_source,CompileError

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--native',action='store_true');a=p.parse_args();counts=dict(accepted=0,rejected=0,presentation=0,authored_rejected=0,native_compositions=0)
 files=[ROOT/'standalone/fixtures/aspect_when_vectors.json',ROOT/'standalone/fixtures/aspect_when_compiler_vectors.json'];corpora=[json.loads(p.read_text()) for p in files]
 for corpus in corpora:
  for vector in corpus['vectors']:
   source=vector['source'];expected=bytes.fromhex(vector['asx_hex']);assert hashlib.sha256(source.encode('cp437')).hexdigest()==vector['source_sha256'];assert hashlib.sha256(expected).hexdigest()==vector['asx_sha256']
   got=compile_source(source);assert got==expected,(vector['name'],got.hex(),expected.hex());counts['accepted']+=1
   changed=re.sub(r'"[^"\r\n]*"|[a-zA-Z_$][a-zA-Z_0-9$]*',lambda m:m[0] if m[0].startswith('"') else {'index':'slot_id','pattern':'trigger_text','response':'answer_text','worker':'handler'}.get(m[0].lower(),m[0]).upper(),source)
   changed='\n'.join('\t '+line+'  ' for line in changed.splitlines());assert compile_source(changed)==expected,vector['name'];counts['presentation']+=1
  for vector in corpus['compiler_rejected']:
   try:compile_source(vector['source'])
   except CompileError:counts['rejected']+=1
   else:raise AssertionError(('Rejected original source compiled',vector['name']))
 for body in ['when 0 "P" call missing','when 0 "P" transmit 1','when 0 1 transmit "R"','when 1L "P" transmit "R"','when 0 "P" call handler with 1','when 0 "P" call handler extra','cwhen 0 extra','set whencase on extra','set whencase flag','set unknown on']:
  source='integer flag\nproc main\n'+body+'\nendproc\nproc handler\nendproc\n'
  try:compile_source(source)
  except CompileError:counts['authored_rejected']+=1
  else:raise AssertionError(('Invalid authored source compiled',body))
 # A novel absolute WHEN target crosses64KiB, with the real procedure frame
 # opcode selected from declarations. This is not a frozen-output lookup.
 source='integer answer\nproc main\nwhen 2 "NEW" call handler\n'+'answer = 91\n'*10000+'endproc\nproc handler\ninteger local_value\nlocal_value = 7\nendproc\n'
 wire=compile_source(source);marker=wire.index(bytes.fromhex('07 c8'));target=int.from_bytes(wire[marker+2:marker+6],'little');assert target>65535 and wire[target:target+4]==bytes.fromhex('d2 02 00 cf')
 native_bindings={}
 if a.native:
  manifest_path=ROOT/'build/aspect-when/manifest.json';manifest=json.loads(manifest_path.read_text())
  assert sha(ROOT/'src/aspect/when.asm')==manifest['source_sha256']
  native_bindings[str(manifest_path.relative_to(ROOT))]=sha(manifest_path)
  native_bindings['standalone/check_aspect_when.py']=sha(ROOT/'standalone/check_aspect_when.py')
  for unit in manifest['units']:
   path=ROOT/f"build/aspect-when/unit{unit['unit']}.bin";assert sha(path)==unit['sha256'];native_bindings[str(path.relative_to(ROOT))]=sha(path)
  for unit in manifest['helpers']+manifest['composition']:
   path=ROOT/f"build/aspect-when/{unit['name']}.bin";assert sha(path)==unit['sha256'] and sha(ROOT/unit['source'])==unit['source_sha256'];native_bindings[str(path.relative_to(ROOT))]=sha(path)
  for path,digest in manifest['source_dependencies'].items():assert sha(ROOT/path)==digest
  sys.path.insert(0,str(ROOT/'standalone'));from check_aspect_when import Composed
  for name,expected in corpora[0]['flow_cases'].items():
   vector=next(v for v in corpora[0]['vectors'] if v['name']==name);wire=compile_source(vector['source']);m=Composed(wire,bytes.fromhex(expected['rx_hex']));m.run()
   assert bytes(m.tx).hex()==expected['tx_hex'] and bytes(m.display).hex()==expected['display_hex'];assert m.get(0xe37a)==0 and m.get(0xe13c)==0x7000 and m.get(0xe13a)==0x6800 and m.get(0xe382)==0
   counts['native_compositions']+=1
 report=dict(passed=True,original_inputs=[],scope='Compiler grammar/encoding only; native flag runs four controlled native source component compositions with explicit FILE/platform boundaries. No production WHEN integration claim.',compiler_sha256=sha(Path(compiler.__file__)),checker_sha256=sha(Path(__file__)),fixtures={str(p.relative_to(ROOT)):sha(p) for p in files},native_bindings=native_bindings,counts=counts)
 out=ROOT/'build/aspect-when-compiler';out.mkdir(parents=True,exist_ok=True);(out/('checks-native-source.json' if a.native else 'checks.json')).write_text(json.dumps(report,indent=2)+'\n');print('WHEN compiler:',counts,'PASS')
if __name__=='__main__':main()
