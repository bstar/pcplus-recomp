#!/usr/bin/env python3
"""Validate the actual linked startup handoff and reject damaged ABI controls."""
import argparse,hashlib,json,re,struct,tempfile
from pathlib import Path
from terminal_memory import inspect_terminal_memory
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
 binary=args.terminal.resolve();listing=binary.parent/'terminal.map';manifest=json.loads((binary.parent/'manifest.json').read_text())
 assert manifest['experimental_directory_resource_cli'] and sha(binary)==manifest['binary_sha256']
 for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 out=args.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 memory=inspect_terminal_memory(binary,listing);assert memory['directory_resource_cli_startup_order_verified']
 symbols={n:(int(s,16),int(o,16)) for s,o,n in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',listing.read_text(),re.M|re.I)}
 image=binary.read_bytes();header=struct.unpack_from('<14H',image);start=header[4]*16
 seg,off=symbols['terminal_resource_cli_startup'];site=seg*16+off
 def control(name,mutation):
  damaged=bytearray(image);mutation(damaged);path=out/(name+'.analysis.exe');path.write_bytes(damaged)
  try:inspect_terminal_memory(path,listing)
  except AssertionError as error:return dict(case=name,rejected=True,reason=str(error),sha256=sha(path))
  raise AssertionError('Damaged startup accepted: '+name)
 def word_at(data,at,value):struct.pack_into('<H',data,at,value)
 def remove_relocation(data):
  locations=[(i,s*16+o) for i,(o,s) in enumerate(struct.unpack_from('<HH',data,header[12]+j*4) for j in range(header[3]))]
  indexes=[i for i,address in locations if address==site+3];assert len(indexes)==1
  struct.pack_into('<HH',data,header[12]+indexes[0]*4,0,0)
 cases=[control('wrong-bind-target',lambda d:word_at(d,start+site+1,0)),
  control('missing-bind-relocation',remove_relocation),
  control('reversed-bind-status',lambda d:d.__setitem__(start+site+7,0x75)),
  control('wrong-error-return',lambda d:word_at(d,start+site+10,0)),
  control('wrong-directory-target',lambda d:word_at(d,start+site+13,0))]
 result=dict(passed=True,binary_sha256=sha(binary),memory=memory,damaged_controls=cases,original_inputs=[],
  sources={n:sha(ROOT/n) for n in ['standalone/check_directory_resource_cli.py','standalone/terminal_memory.py','src/terminal/main.asm']},
  scope='Linked startup order/ABI/relocations and five rejected non-executable controls; functional binding is covered by separate DOS and package tests.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS linked CLI startup and',len(cases),'damaged controls')
if __name__=='__main__':main()
