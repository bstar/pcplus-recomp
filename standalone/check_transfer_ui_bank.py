#!/usr/bin/env python3
"""Challenge static UI entry/callback targets, returns and MZ relocations."""
import argparse,hashlib,json,re,struct,tempfile
from pathlib import Path
from terminal_memory import inspect_terminal_memory
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--binary',type=Path,default=ROOT/'build/terminal/TERMINAL.EXE');p.add_argument('--output',type=Path);a=p.parse_args()
 binary=a.binary.resolve();assert binary.is_relative_to(ROOT/'build');listing=binary.parent/'terminal.map'
 output=a.output.resolve() if a.output else binary.parent/'terminal-transfer-ui-bank.json'
 assert output.is_relative_to(ROOT/'build')
 before=sha(binary);memory=inspect_terminal_memory(binary,listing)
 assert memory['transfer_ui_far_entries_verified']==4 and memory['transfer_ui_resident_callbacks_verified']==3
 image=binary.read_bytes();header=struct.unpack_from('<14H',image);start=header[4]*16
 symbols={name:int(seg,16)*16+int(off,16) for seg,off,name in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',listing.read_text(),re.M|re.I)}
 cases=[dict(name='complete_entry_callback_and_relocation_baseline',passed=True)]
 with tempfile.TemporaryDirectory(prefix='ui-bank-controls-',dir=ROOT/'build') as folder:
  def reject(label,name,change):
   altered=bytearray(image);change(altered);path=Path(folder)/(label+'.bin');path.write_bytes(altered)
   try:inspect_terminal_memory(path,listing)
   except AssertionError as e:
    error=str(e);passed=name in error
   else:error='Invalid bridge accepted';passed=False
   cases.append(dict(name=label,passed=passed,error=error,mutant_sha256=sha(path)))
  for suffix in ('open','receiving','progress','restore'):
   name='terminal_transfer_ui_'+suffix;at=start+symbols[name]
   reject(suffix+'_wrong_far_target',name,lambda b,at=at:b.__setitem__(at+1,b[at+1]^1))
   reject(suffix+'_wrong_near_return',name,lambda b,at=at:b.__setitem__(at+5,0xcb))
   relocation=next(header[12]+i*4 for i in range(header[3]) if (lambda q:q[1]*16+q[0])(struct.unpack_from('<HH',image,header[12]+i*4))==symbols[name]+3)
   reject(suffix+'_missing_segment_relocation',name,lambda b,r=relocation:struct.pack_into('<HH',b,r,0,0))
  for suffix in ('service','keyboard','read'):
   name='terminal_transfer_ui_'+suffix+'_far';at=start+symbols[name]
   reject(suffix+'_wrong_resident_callback',name,lambda b,at=at:b.__setitem__(at+1,b[at+1]^1))
   reject(suffix+'_wrong_far_return',name,lambda b,at=at:b.__setitem__(at+3,0xc3))
 assert sha(binary)==before
 result=dict(passed=all(c['passed'] for c in cases),binary_sha256=before,cases=cases,
  resident_code_bytes=memory['resident_code_bytes'],resident_code_spare_bytes=memory['resident_code_spare_bytes'],far_entries=4,resident_callbacks=3,
  inputs={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__).resolve(),ROOT/'standalone/terminal_memory.py',ROOT/'src/terminal/transfer_ui.asm',ROOT/'src/terminal/transfer_ui_bridge.asm']},
  map_sha256=sha(listing),scope='Static full MZ/map memory validation plus18 invalid UI far targets/returns/segment relocations and resident callback targets/returns. Invalid images are never executed. Behavioral and hardware acceptance require separate linked and actual DOS tests.')
 output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=result['passed'],cases=len(cases),binary=str(binary),resident_spare=result['resident_code_spare_bytes'])));assert result['passed']

if __name__=='__main__':main()
