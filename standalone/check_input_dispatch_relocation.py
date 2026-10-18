#!/usr/bin/env python3
"""Exercise both inline input tables and startup DS pointers after relocation."""
from pathlib import Path
import json,subprocess,hashlib
from unicorn import UC_HOOK_INTR
from check_input_dispatch import Input
from dos_image import DosImage
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/input-dispatch-relocation'
class RelocatedInput(Input):
 def __init__(self,binary,mapping):
  DosImage.__init__(self,binary,mapping)
  self.positions=[];self.calls=[];self.video=0xb8000
  self.uc.mem_write(self.video,b'\xa5'*4000);self.uc.hook_add(UC_HOOK_INTR,self.interrupt)
  self.call('csi_clear_tabs',(1,))
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 manifest=json.loads((ROOT/'build/input_dispatch/manifest.json').read_text())
 sources=[ROOT/name for name in manifest['sources'] if name.endswith('.asm')]
 objects=[]
 for index,source in enumerate(sources):
  obj=OUT/f'unit-{index}.obj';objects.append(str(obj));flags=[]
  if source.parent.parent==ROOT/'reconstruction':flags=['-D'+source.parent.name.upper()+'_OMF']
  subprocess.run(['nasm','-f','obj',*flags,'-I',str(ROOT/'reconstruction/uart')+'/', '-I',str(ROOT/'reconstruction/ansi')+'/',str(source),'-o',str(obj)],check=True)
 cases=[]
 for codepad,datapad in [(0,0),(0x333,0x555),(0x2111,0x1234)]:
  out=OUT/f'{codepad:x}-{datapad:x}';out.mkdir(exist_ok=True)
  asm=out/'pad.asm';obj=out/'pad.obj'
  asm.write_text(f'BITS 16\nSEGMENT _TEXT public class=CODE use16\ntimes {codepad} db 0xcc\nSEGMENT _DATA public align=16 class=DATA use16\ntimes {datapad} db 0xa5\n')
  subprocess.run(['nasm','-f','obj',str(asm),'-o',str(obj)],check=True)
  binary=out/'INPUT.EXE';mapping=out/'input.map'
  subprocess.run(['wlink','system','dos','option','quiet','option','map='+str(mapping),'name',str(binary),'file',','.join([str(obj)]+objects)],check=True)
  c=RelocatedInput(binary,mapping);c.feed(b'A\x1b[31mB\r\nC\tD\x08E')
  assert c.cell(0,0)==b'A\x07' and c.cell(0,1)==b'B\x04' and c.cell(1,0)==b'C\x04' and c.cell(1,8)==b'E\x04'
  assert c.history()==b'AB\rCDE'
  # Exercise the distinct low-control CS jump table rather than DS control table.
  m=RelocatedInput(binary,mapping);m.put('attributes_monochrome',1);m.feed(b'\x01')
  assert m.cell(0,0)==b'\x01\x07' and m.get('screen_cursor_column')==1
  # C1 table's ordinary branch: sourcebyte0x86 indexes the second inline table.
  q=RelocatedInput(binary,mapping);q.put('terminal_input_mode_8fe8',1);q.put('terminal_c1_enabled',1);q.feed(b'\x86')
  assert q.cell(0,0)==b'\x86\x07'
  cases.append({'code_padding':codepad,'data_padding':datapad,'entry_offset':c.symbols['terminal_receive_character']-c.base,'pointer_table_offset':c.offset('terminal_control_dispatch_table'),'binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'passed':True})
  print('input relocation',hex(codepad),hex(datapad),'passed',flush=True)
 assert len({c['entry_offset'] for c in cases})==3 and len({c['pointer_table_offset'] for c in cases})==3
 result={'passed':True,'cases':cases,'scope':'Actual both input CS tables and startup DS function pointers plus nestedANSI/render/control/history calls after independent code/data padding.'}
 (OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n');return result
if __name__=='__main__':main()
