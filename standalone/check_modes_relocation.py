#!/usr/bin/env python3
"""Shift code/data independently to verify actual mode tables and parameter pointers."""
import hashlib,json,struct,subprocess
from pathlib import Path
from unicorn import UC_HOOK_INTR
from dos_image import DosImage
from check_modes import Modes,ROOT
OUT=ROOT/'build/modes-relocation'
class RelocatedModes(Modes):
 def __init__(self,binary,mapping):
  DosImage.__init__(self,binary,mapping)
  self.positions=[];self.uc.hook_add(UC_HOOK_INTR,self.interrupt)
 def parameters(self,values):
  self.put('ansi_parameter_count',len(values));self.uc.mem_write(self.symbols['ansi_parameters'],struct.pack('<'+'H'*len(values),*values))
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 manifest=json.loads((ROOT/'build/modes/manifest.json').read_text());sources=[ROOT/p for p in manifest['sources'] if p.endswith('.asm')];objects=[]
 for i,source in enumerate(sources):
  obj=OUT/f'unit-{i}.obj';objects.append(str(obj))
  subprocess.run(['nasm','-f','obj','-DMODES_OMF','-DSCREEN_OMF','-I',str(ROOT/'reconstruction/uart')+'/',str(source),'-o',str(obj)],check=True)
 results=[]
 for code_pad,data_pad in [(0,0),(0x137,0x251),(0x2137,0x1234)]:
  case=OUT/f'{code_pad:x}-{data_pad:x}';case.mkdir(exist_ok=True)
  pad=case/'padding.asm';pad.write_text(f'BITS16\nSEGMENT _TEXT public class=CODE use16\ntimes {code_pad} db 0xcc\nSEGMENT _DATA public align=16 class=DATA use16\ntimes {data_pad} db 0xa5\n'.replace('BITS16','BITS 16'))
  obj=case/'padding.obj';subprocess.run(['nasm','-f','obj',str(pad),'-o',str(obj)],check=True)
  binary=case/'MODES.EXE';mapping=case/'modes.map'
  subprocess.run(['wlink','system','dos','option','quiet','option','map='+str(mapping),'name',str(binary),'file',','.join([str(obj)]+objects)],check=True)
  m=RelocatedModes(binary,mapping);m.parameters([4,7,18,19,0,65535]);m.run()
  names=['terminal_mode_372c','cursor_state_value_1d20','modes_value_3980','modes_value_3982']
  assert [m.get(n) for n in names]==[1,1,1,0]
  m.run(True);assert [m.get(n) for n in names]==[0,0,0,1]
  m.parameters([6]);m.put('csi_scroll_top',4);m.put('csi_scroll_bottom',19);m.run();m.run(True)
  assert m.positions==[0x0400,0]
  m.parameters([1]);assert m.missing()==(0xb4e,0x4f)
  results.append({'code_padding':code_pad,'data_padding':data_pad,'mode_entry':m.symbols['csi_set_modes']-m.base,'parameter_offset':m.offset('ansi_parameters'),'binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'passed':True})
  print('mode relocation',hex(code_pad),hex(data_pad),'passed')
 assert len({c['mode_entry'] for c in results})==3 and len({c['parameter_offset'] for c in results})==3
 (OUT/'result.json').write_text(json.dumps({'passed':True,'cases':results,'scope':'Actual recovered mode switch table relocations, parameter pointers,state writes,BIOS cursor calls and explicit dependency boundaries at independent code/data offsets.'},indent=2)+'\n')
if __name__=='__main__':main()
