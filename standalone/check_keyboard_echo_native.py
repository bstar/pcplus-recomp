#!/usr/bin/env python3
"""Observe echo-service choices in exact recovered dispatcher instructions."""
import hashlib,itertools,json,struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_SP,UC_X86_REG_IP,UC_X86_REG_BX
from check_keyboard_mapping_raw import Raw,KEYS,ROOT
def main():
 rows=[]
 proof=json.loads((ROOT/'build/keyboard-mapping/manifest.json').read_text())
 for path,digest in proof['sources'].items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest,path
 strings=set(range(7))|set(range(28,38))|{78}
 cursors={50:'1efc',72:'1efc',51:'1e0c',73:'1e0c',52:'1e30',74:'1e30',53:'1ea0',75:'1ea0',76:'1bbe'}
 edits={7:['0bc0'],8:['b9f7'],54:['b9f7'],9:['ba03'],55:['ba03']}
 for profile,half in itertools.product((4,6),(0,1)):
  for slot,key in sorted(KEYS.items()):
   m=Raw();trace=[]
   for name,value in [('keyboard_mapping_key',key),('keyboard_state_1d1a',half),('keyboard_state_373c',0),('keyboard_state_900c',0),('keyboard_mapping_scrollback_mode',0),('keyboard_mapping_hook_enabled',0)]:m.put(name,value)
   m.put('keyboard_state_1d18',profile)
   for i in range(79):m.uc.mem_write(m.symbols['terminal_keymap']+i*12,b'K\0'+b'\0'*10)
   services={address:name[-4:] for name,address in m.symbols.items() if name.startswith('keyboard_service_')}
   emitted=[]
   def ret(uc,cleanup=0):
    sp=uc.reg_read(UC_X86_REG_SP);ip=int.from_bytes(uc.mem_read(m.data_base+sp,2),'little')
    uc.reg_write(UC_X86_REG_SP,sp+2+cleanup);uc.reg_write(UC_X86_REG_IP,ip)
   def hook(uc,address,size,_):
    if address==m.symbols['keyboard_mapping_emit']:
     emitted.append((uc.reg_read(UC_X86_REG_BX)-m.offset('terminal_keymap'))//12);ret(uc)
    elif address in services:
     service=services[address];trace.append(service)
     if service in ('3adb','0610'):
      sp=uc.reg_read(UC_X86_REG_SP);arg=int.from_bytes(uc.mem_read(m.data_base+sp+2,2),'little')
      assert arg==(m.offset('terminal_keymap')+slot*12 if service=='3adb' else 8)
     ret(uc,2 if service=='ab0b' else 0)
   m.uc.hook_add(UC_HOOK_CODE,hook);m.call('keyboard_mapping_dispatch')
   assert emitted==[slot]
   echo=[s for s in trace if s not in ('0ca2','0cb4','2f78','2fb8')]
   want=[]
   if half:
    want=['3adb'] if slot in strings else ['0610'] if slot==10 else [cursors[slot]] if slot in cursors else edits.get(slot,[])
   assert echo==want,(half,slot,echo,want)
   rows.append(dict(profile=profile,slot=slot,key=key,half=half,echo=echo,all_services=trace))
 out=ROOT/'build/terminal-key-output/native-echo.json'
 out.parent.mkdir(parents=True,exist_ok=True)
 report=dict(passed=True,cases=len(rows),dispatcher_binary_sha256=proof['binary_sha256'],checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),native_baseline_bytes=proof['exact_bytes'],rows=rows,original_inputs=[],scope='Exact recovered OMF dispatcher instructions select emit slot and echo services for all79keys with duplex0/1, private hook/cursor-wrap/373C flags0. Emitter and every external service are declared recording boundaries. UI/status/reset services remain listed rather than treated as reconstructed; no actual echo execution, physical keyboard or complete native dispatcher claim.')
 out.write_text(json.dumps(report,indent=2)+'\n');print('Native keyboard echo',len(rows),'cases PASS')
if __name__=='__main__':main()
