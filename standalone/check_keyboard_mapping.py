#!/usr/bin/env python3
"""Actual linked classifier/recovered-emitter ABI tests, optional true-original replay.

CPU hooks are declared UART/status/UI boundary fixtures, never a reconstructed
application service. Optional original mode reads the ignored SHA-pinned MZ.
"""
import argparse,hashlib,json,struct,sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
from dos_image import DosImage
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/keyboard-mapping'
class Mapping(DosImage):
 def __init__(self):super().__init__(OUT/'MAPPING.EXE',OUT/'mapping.map')
 def classify(self,key,scroll=0,hook=0,character=0):
  self.put('keyboard_mapping_scrollback_mode',scroll);self.put('keyboard_mapping_hook_enabled',hook);self.put('keyboard_mapping_hook_character',character,1)
  self.uc.reg_write(UC_X86_REG_AX,key);self.uc.reg_write(UC_X86_REG_ES,0xbeef)
  result=self.call('keyboard_classify')
  assert [self.uc.reg_read(r) for r in (UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI,UC_X86_REG_ES)]==[0xbabe,0x1234,0x5678,0xbeef]
  return result

def run(original=False):
 model=Mapping();count=0;groups=[]
 def check(key,want,scroll=0,hook=0,character=0):
  nonlocal count
  got=model.classify(key,scroll,hook,character);assert got==want,(hex(key),hex(got),hex(want),scroll);count+=1
 # Expectations here follow key identity and documented slot ABI, not the source table.
 for byte in range(1,256):check(byte,{9:6,13:78,28:0xfffe,29:0xfffe,31:0xfffe}.get(byte,0x100|byte))
 for key,slot in [(0x0e08,10),(0x0e7f,15),(0x0f00,7),(0x4700,76),(0x4f00,77),(0x5200,8),(0x5300,9),(0x4800,72),(0x5000,73),(0x4b00,74),(0x4d00,75),(0x7700,11),(0x7500,12)]:check(key,slot)
 groups.append('ASCII-BIOS-specials-edit-navigation-and-register-ABI')
 for first,base in ((0x3b,16),(0x54,38),(0x5e,60)):
  for index in range(10):check((first+index)<<8,base+index)
 for scan,slot in [(0x85,26),(0x86,27),(0x87,48),(0x88,49),(0x89,70),(0x8a,71)]:check(scan<<8,slot)
 for scan in range(0x78,0x82):check(scan<<8,0xfffe)
 for scan in list(range(0x68,0x72))+[0x8b,0x8c,0x92,0x93,0xff]:
  check(scan<<8,0xffff if scan in (0x70,0x8b,0x8c,0x92,0x93,0xff) else 0xfffe)
 groups.append('F1-F12-three-modifier-banks-and-local-macro-boundaries')
 for scroll in (0,1,0xffff):
  for key,slot in ((0x4900,13),(0x5100,14)):check(key,slot if not scroll else 0xfffe,scroll)
  for key,slot in ((0x8400,13),(0x7600,14)):check(key,slot if scroll else 0xfffe,scroll)
 check(ord('x'),0xfffe,hook=1,character=ord('x'));check(ord('x'),0x178,hook=0,character=ord('x'))
 check(0x1b,0xfffe,hook=1,character=0x1b);check(0xff,0x1ff,hook=1,character=0xff) # original CBW signed byte
 groups.append('original-scrollback-and-hotkey-precedence')
 # Run the actual recovered linked emitter with a recording UART callee fixture.
 model=Mapping();wire=[];sp_reg=UC_X86_REG_SP
 def fixture(uc,address,size,_):
  if address==model.symbols['keyboard_service_ab0b']:
   sp=uc.reg_read(sp_reg);at=model.data_base+sp;ip,value=struct.unpack('<HH',uc.mem_read(at,4));wire.append(value)
   uc.reg_write(sp_reg,sp+4);uc.reg_write(UC_X86_REG_IP,ip)
 model.uc.hook_add(UC_HOOK_CODE,fixture)
 for value,want in [(b'',[]),(b'\x1b[1~',[27,91,49,126]),(b'A\xffB',[65,0,66])]:
  wire.clear();at=model.symbols['terminal_keymap'];model.uc.mem_write(at,value+b'\0');model.put('keyboard_state_1d68',0)
  model.uc.reg_write(UC_X86_REG_BX,at-model.data_base);model.call('keyboard_mapping_emit');assert wire==want,(wire,want)
 groups.append('recovered-emitter-actual-instructions-FF-to-NUL-and-empty-bindings')
 original_cases=0
 if original:
  sys.path.insert(0,str(ROOT/'reconstruction'));from check_ansi_freeze import load_image
  image=(ROOT/'analysis/pcplus-originals/PCPLUS-main-2.01.EXE').read_bytes()
  proof=json.loads((ROOT/'reconstruction/keyboard_mapping/provenance.json').read_text());assert hashlib.sha256(image).hexdigest()==proof['source_sha256']
  def observe(key,scroll):
   uc=load_image(image);data=0x1fb70
   for off,val in [(0xcffa,key),(0x1d74,scroll),(0x1d6e,0),(0x1d1a,0),(0x373c,0),(0x900c,0)]:uc.mem_write(data+off,struct.pack('<H',val))
   uc.mem_write(data+0xf2a0,struct.pack('<H',0xfff0));result=[]
   def boundary(machine,address,size,_):
    if address==0x10a62:
     result.append(machine.reg_read(UC_X86_REG_BX));machine.emu_stop()
    elif address==0x1ab0b:
     sp=machine.reg_read(UC_X86_REG_SP);result.append(0x100|struct.unpack('<H',machine.mem_read(data+sp+2,2))[0]);machine.emu_stop()
    elif address in (0x12f78,0x12fb8):
     sp=machine.reg_read(UC_X86_REG_SP);ip=struct.unpack('<H',machine.mem_read(data+sp,2))[0];machine.reg_write(UC_X86_REG_SP,sp+2);machine.reg_write(UC_X86_REG_IP,ip)
    elif address==0x1fff0:result.append(0xffff);machine.emu_stop()
    elif address==0x10e06:result.append(0xfffe);machine.emu_stop()
   uc.hook_add(UC_HOOK_CODE,boundary);uc.emu_start(0x11604,0,count=5000);assert result,key
   value=result[0]
   return (value-0x3378)//12 if 0x3378<=value<=0x3720 else value
  def linked_observe(key,scroll):
   model=Mapping();uc=model.uc
   for name,value in [('keyboard_mapping_key',key),('keyboard_mapping_scrollback_mode',scroll),('keyboard_mapping_hook_enabled',0),('keyboard_state_1d1a',0),('keyboard_state_373c',0),('keyboard_state_900c',0)]:model.put(name,value)
   uc.reg_write(UC_X86_REG_CS,0x1000);uc.reg_write(UC_X86_REG_DS,model.ds);uc.reg_write(UC_X86_REG_SS,model.ds);uc.reg_write(UC_X86_REG_SP,0xf000)
   uc.mem_write(model.data_base+0xf000,struct.pack('<H',0xeff0));result=[]
   def boundary(machine,address,size,_):
    if address==model.symbols['keyboard_mapping_emit']:
     result.append((machine.reg_read(UC_X86_REG_BX)-model.offset('terminal_keymap'))//12);machine.emu_stop()
    elif address==model.symbols['keyboard_service_ab0b']:
     sp=machine.reg_read(UC_X86_REG_SP);result.append(0x100|struct.unpack('<H',machine.mem_read(model.data_base+sp+2,2))[0]);machine.emu_stop()
    elif address==model.symbols['keyboard_service_0e06']:result.append(0xfffe);machine.emu_stop()
    elif address in (model.symbols['keyboard_service_2f78'],model.symbols['keyboard_service_2fb8']):
     sp=machine.reg_read(UC_X86_REG_SP);ip=struct.unpack('<H',machine.mem_read(model.data_base+sp,2))[0];machine.reg_write(UC_X86_REG_SP,sp+2);machine.reg_write(UC_X86_REG_IP,ip)
    elif address==0x1eff0:result.append(0xffff);machine.emu_stop()
   uc.hook_add(UC_HOOK_CODE,boundary);uc.emu_start(model.symbols['keyboard_mapping_dispatch'],0,count=5000);assert result,key
   return result[0]
  model=Mapping()
  keys=[x for x in range(1,256) if x not in (28,29,31)]+[0x0e08,0x0e7f]+[scan<<8 for scan in range(141) if model.classify(scan<<8)<79]+[0x4900,0x5100,0x8400,0x7600]
  for scroll in (0,1):
   for key in keys:
    want=observe(key,scroll);got=model.classify(key,scroll);linked=linked_observe(key,scroll);assert got==want==linked,(hex(key),scroll,hex(got),hex(want),hex(linked));original_cases+=1
  groups.append('optional-genuine-original-and-OMF-dispatch-key-to-slot-or-literal-comparison')
 (OUT/'cpu-results.json').write_text(json.dumps({'passed':True,'binary_sha256':hashlib.sha256((OUT/'MAPPING.EXE').read_bytes()).hexdigest(),'classifier_cases':count,'original_cases':original_cases,'groups':groups,'fixtures':'UART recording callee, status callbacks bypassed only for original observation; UI application routines not executed.'},indent=2)+'\n')
 print(f'Keyboard mapping: {len(groups)} groups, {count} classifier ABI cases, {original_cases} original comparisons passed')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--original',action='store_true');run(p.parse_args().original)
