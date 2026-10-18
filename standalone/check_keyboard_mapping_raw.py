#!/usr/bin/env python3
"""Cover all79 original KBD slots using raw keyboard_read words and real code."""
import argparse,hashlib,json,struct,sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
from check_keyboard_mapping import Mapping,ROOT,OUT
# Key identities from original CS1604 branch labels and DS44e0 helper targets.
KEYS={0:0x372a,1:0x4a2d,2:0x4e2b,3:0x532e,4:0xe02f,5:0xe00d,6:9,7:0xf00,8:0x5200,9:0x5300,10:0xe08,11:0x7700,12:0x7500,13:0x4900,14:0x5100,15:0xe7f,26:0x8500,27:0x8600,48:0x8700,49:0x8800,50:0x48e0,51:0x50e0,52:0x4be0,53:0x4de0,54:0x52e0,55:0x53e0,56:0x47e0,57:0x4fe0,58:0x49e0,59:0x51e0,70:0x8900,71:0x8a00,72:0x4800,73:0x5000,74:0x4b00,75:0x4d00,76:0x4700,77:0x4f00,78:13}
for first,base in [(0x3b,16),(0x54,38),(0x5e,60)]:
 for i in range(10):KEYS[base+i]=(first+i)<<8
for digit,key in enumerate([0x5230,0x4f31,0x5032,0x5133,0x4b34,0x4c35,0x4d36,0x4737,0x4838,0x4939]):KEYS[28+digit]=key
assert set(KEYS)==set(range(79))
class Raw(Mapping):
 def classify_raw(self,key,scroll=0,enabled=True):
  self.put('keyboard_mapping_scrollback_mode',scroll);self.put('keyboard_mapping_hook_enabled',0)
  self.uc.mem_write(self.symbols['terminal_keymap']+58*12,bytes([27 if enabled else 0]));self.uc.mem_write(self.symbols['terminal_keymap']+59*12,bytes([27 if enabled else 0]))
  self.uc.reg_write(UC_X86_REG_AX,key);self.uc.reg_write(UC_X86_REG_ES,0xbeef)
  value=self.call('keyboard_classify_raw')
  assert [self.uc.reg_read(r) for r in [UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI,UC_X86_REG_ES]]==[0xbabe,0x1234,0x5678,0xbeef]
  return value

def observed(model,key,scroll,enabled,profile,original_image=None):
 if original_image:
  sys.path.insert(0,str(ROOT/'reconstruction'));from check_ansi_freeze import load_image
  uc=load_image(original_image);ds=0x1fb7;data=ds*16;entry=0x11604;emit=0x10a62;tx=0x1ab0b;local=0x10e06;status=[0x12f78,0x12fb8];keymap=0x3378
  for off,value in [(0xcffa,key),(0x1d74,scroll),(0x1d6e,0),(0x1d18,profile),(0x1d1a,0),(0x373c,0),(0x900c,0)]:uc.mem_write(data+off,struct.pack('<H',value))
 else:
  uc=model.uc;ds=model.ds;data=model.data_base;entry=model.symbols['keyboard_mapping_dispatch'];emit=model.symbols['keyboard_mapping_emit'];tx=model.symbols['keyboard_service_ab0b'];local=model.symbols['keyboard_service_0e06'];status=[model.symbols['keyboard_service_2f78'],model.symbols['keyboard_service_2fb8']];keymap=model.offset('terminal_keymap')
  for name,value in [('keyboard_mapping_key',key),('keyboard_mapping_scrollback_mode',scroll),('keyboard_mapping_hook_enabled',0),('keyboard_state_1d18',profile),('keyboard_state_1d1a',0),('keyboard_state_373c',0),('keyboard_state_900c',0)]:model.put(name,value)
 for slot in (58,59):uc.mem_write(data+keymap+slot*12,bytes([27 if enabled else 0]))
 uc.reg_write(UC_X86_REG_CS,0x1000);uc.reg_write(UC_X86_REG_DS,ds);uc.reg_write(UC_X86_REG_SS,ds);uc.reg_write(UC_X86_REG_SP,0xe000);uc.mem_write(data+0xe000,struct.pack('<H',0xeff0));result=[]
 def boundary(machine,address,size,_):
  if address==emit:result.append((machine.reg_read(UC_X86_REG_BX)-keymap)//12);machine.emu_stop()
  elif address==tx:
   sp=machine.reg_read(UC_X86_REG_SP);result.append(0x100|struct.unpack('<H',machine.mem_read(data+sp+2,2))[0]);machine.emu_stop()
  elif address==local:result.append(0xfffe);machine.emu_stop()
  elif address in status:
   sp=machine.reg_read(UC_X86_REG_SP);ip=struct.unpack('<H',machine.mem_read(data+sp,2))[0];machine.reg_write(UC_X86_REG_SP,sp+2);machine.reg_write(UC_X86_REG_IP,ip)
  elif address==0x1eff0:result.append(0xffff);machine.emu_stop()
 uc.hook_add(UC_HOOK_CODE,boundary);uc.emu_start(entry,0,count=10000);assert result,(key,scroll,enabled);return result[0]

def run(original=False):
 image=(ROOT/'analysis/pcplus-originals/PCPLUS-main-2.01.EXE').read_bytes() if original else None
 if image:assert hashlib.sha256(image).hexdigest()==json.loads((ROOT/'reconstruction/keyboard_mapping/provenance.json').read_text())['source_sha256']
 count=0;original_count=0;slots=set()
 for profile in (4,6):
  for scroll in (0,1):
   for enabled in (False,True):
    for slot,key in sorted(KEYS.items()):
     want=slot
     if slot in (13,14) and scroll:want=0xfffe
     if slot in (58,59) and not enabled:want=0xfffe
     got=Raw().classify_raw(key,scroll,enabled);linked=observed(Raw(),key,scroll,enabled,profile)
     assert got==linked==want,(slot,hex(key),profile,scroll,enabled,got,linked,want)
     if image:
      actual=observed(None,key,scroll,enabled,profile,image);assert got==actual,(slot,hex(key),profile,scroll,enabled,got,actual);original_count+=1
     if got<79:slots.add(got)
     count+=1
 assert slots==set(range(79))
 for key in [0x1ce0,0x35e0,0x1c01,0x372b,0x4738,0x8b00,0x8c00,0x9200,0x9300]:assert Raw().classify_raw(key)==0xffff
 for key in [0x73e0,0x74e0]:assert Raw().classify_raw(key)==0xfffe
 (OUT/'raw-cpu-results.json').write_text(json.dumps({'passed':True,'binary_sha256':hashlib.sha256((OUT/'MAPPING.EXE').read_bytes()).hexdigest(),'all_79_slots_covered':True,'key_profile_mode_binding_cases':count,'original_comparisons':original_count,'unknown_alias_cases':9,'known_local_cases':2,'scope':'Actual linked raw classifier vs actual recovered OMF dispatcher and optional genuine-original instructions; capture at binding-emitter entry observes slots even when empty. UI/status callbacks are explicit boundaries.'},indent=2)+'\n')
 print('Raw keyboard mapping:',count,'mode/profile/binding cases, all79slots,',original_count,'original comparisons passed')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--original',action='store_true');run(p.parse_args().original)
