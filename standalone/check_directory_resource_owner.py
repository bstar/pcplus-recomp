#!/usr/bin/env python3
"""Check linked resource callbacks, exact PROGRAM scheduling and EXEC gating."""
import argparse,hashlib,json,re,struct
from pathlib import Path
from terminal_memory import inspect_terminal_memory
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
 binary=args.terminal.resolve();listing=binary.parent/'terminal.map';manifest=json.loads((binary.parent/'manifest.json').read_text())
 assert manifest['experimental_directory_resource_owner'] and sha(binary)==manifest['binary_sha256']
 for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 out=args.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 symbols={n:(int(s,16),int(o,16)) for s,o,n in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',listing.read_text(),re.M|re.I)}
 address=lambda n:symbols[n][0]*16+symbols[n][1]
 image=binary.read_bytes();header=struct.unpack_from('<14H',image);start=header[4]*16
 process=address('terminal_process_code_start');end=address('terminal_process_code_end');target=symbols['_directory_resources_exec_allowed']
 pattern=b'\x9a'+struct.pack('<HH',target[1],target[0])+b'\x09\xc0'
 def verify(path):
  memory=inspect_terminal_memory(path,listing);data=path.read_bytes()
  q=address('_directory_resources_program_queue');body=data[start+q:start+q+17]
  assert body[:1]==b'\xb8' and body[3]==0xe8
  assert q+6+struct.unpack_from('<h',body,4)[0]==address('terminal_program_start')
  assert body[6:]==b'\x09\xc0\x75\x06\xc7\x06'+struct.pack('<H',symbols['terminal_program_kind'][1])+b'\x06\x00\xcb','Queue must set kind6 only after successful PROGRAM admission'
  body=data[start+process:start+end];assert body.count(pattern)==1,'Resource EXEC predicate must be called once'
  at=body.index(pattern);tail=body[at+7:at+12];assert tail[:3]==b'\x75\x03\xe9'
  busy=at+12+struct.unpack('<h',tail[3:5])[0];assert body[busy:busy+8]==b'\xb8\x04\x00\x07\x5f\x5e\x5d\xc3'
  reloc=[(i,s*16+o) for i,(o,s) in enumerate(struct.unpack_from('<HH',data,header[12]+j*4) for j in range(header[3]))]
  assert sum(a==process+at+3 for i,a in reloc)==1,'Resource EXEC predicate segment relocation'
  assert memory['configuration_bridge_pairs_verified']==102 and memory['directory_resource_bundle_bytes']==(2024 if manifest.get('experimental_directory_scripts') else 1948 if manifest.get('experimental_directory_translation') else 1624)
  return memory,process+at,next(i for i,a in reloc if a==process+at+3)
 memory,gate,reloc=verify(binary);cases=[]
 variants=[('defaults-caller-word',start+address('_directory_resources_defaults')+5,8),
  ('keymap-forwarded-word',start+address('_config_resource_keymap_resident')+5,12),
  ('wrong-PROGRAM-kind',start+address('_directory_resources_program_queue')+14,4),
  ('reversed-resource-EXEC-condition',start+gate+7,0x74),
  ('wrong-loan-restore-call',start+address('process_loan_end_site')+1,0),
  ('wrong-child-UART-quiet-call',start+address('process_child_quiet_site')+1,0),
  ('wrong-actual-transfer-caller-word',start+address('_directory_resource_capture')+10,10),
  ('wrong-critical-retention-store',start+address('terminal_program_critical_site')+1,0)]
 for name,at,value in variants:
  data=bytearray(image);assert data[at]!=value,(name,'control must change a byte');data[at]=value
  path=out/(name+'.analysis.exe');path.write_bytes(data)
  try:verify(path)
  except AssertionError:cases.append(dict(case=name,rejected=True,sha256=sha(path)))
  else:raise AssertionError(('Damaged owner accepted',name))
 data=bytearray(image);struct.pack_into('<HH',data,header[12]+reloc*4,0,0);path=out/'missing-resource-EXEC-relocation.analysis.exe';path.write_bytes(data)
 try:verify(path)
 except AssertionError:cases.append(dict(case='missing-resource-EXEC-relocation',rejected=True,sha256=sha(path)))
 else:raise AssertionError('Damaged resource relocation accepted')
 result=dict(passed=True,binary_sha256=sha(binary),memory=memory,damaged_controls=cases,original_inputs=[],
  sources={n:sha(ROOT/n) for n in ['standalone/check_directory_resource_owner.py','standalone/terminal_memory.py','src/terminal/config_abi.inc']},
  scope='Actual linked ABI/scheduling/ownership/retention bytes and nine rejected non-executable controls. Native DOS separately checks real UART quiescence and exact staged resources.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS resource owner ABI/retention and',len(cases),'damaged controls')
if __name__=='__main__':main()
