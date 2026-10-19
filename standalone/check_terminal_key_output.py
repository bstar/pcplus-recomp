#!/usr/bin/env python3
"""Execute shared product key output; echo/cursor endpoints are declared fixtures."""
import hashlib,json,struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
from dos_image import DosImage
from check_keyboard_mapping_raw import KEYS
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/terminal-key-output'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
class Machine(DosImage):
 def __init__(self):
  super().__init__(ROOT/'build/terminal/TERMINAL.EXE',ROOT/'build/terminal/terminal.map')
  manifest=json.loads((ROOT/'build/terminal/manifest.json').read_text())
  self.segment=self.base_segment+next(s['relative_segment'] for s in manifest['memory_layout']['code_segments'] if s['name']=='ASPECT_CODE')
  self.events=[];self.echo_counts=[];self.uc.hook_add(UC_HOOK_CODE,self.endpoint)
 def endpoint(self,uc,address,size,_):
  kind={self.symbols['terminal_key_echo_far']:'echo',self.symbols['terminal_key_cursor_far']:'cursor'}.get(address)
  if not kind:return
  self.events.append((kind,uc.reg_read(UC_X86_REG_AX)))
  self.echo_counts.append(self.get('terminal_tx_count'))
  sp=uc.reg_read(UC_X86_REG_SP);ip,cs=struct.unpack('<HH',uc.mem_read(self.data_base+sp,4))
  uc.reg_write(UC_X86_REG_SP,sp+4);uc.reg_write(UC_X86_REG_CS,cs);uc.reg_write(UC_X86_REG_IP,ip)
 def run(self,key,duplex=0):
  uc=self.uc;sp=self.offset('terminal_stack_top')-4
  for reg,value in [(UC_X86_REG_CS,self.segment),(UC_X86_REG_DS,self.ds),(UC_X86_REG_SS,self.ds),(UC_X86_REG_SP,sp),(UC_X86_REG_AX,key),(UC_X86_REG_BX,duplex),(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678),(UC_X86_REG_ES,0x7200),(UC_X86_REG_EFLAGS,0x202)]:uc.reg_write(reg,value)
  uc.mem_write(self.data_base+sp,struct.pack('<HH',self.return_offset,self.base_segment));self.returned=False
  uc.emu_start(self.symbols['terminal_key_output'],0,count=100000)
  assert self.returned and uc.reg_read(UC_X86_REG_SP)==sp+4
  assert [uc.reg_read(r) for r in (UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI,UC_X86_REG_ES)]==[0xbabe,0x1234,0x5678,0x7200]
  assert uc.reg_read(UC_X86_REG_DS)==uc.reg_read(UC_X86_REG_SS)==self.ds
  return uc.reg_read(UC_X86_REG_AX)
 def wire(self):
  at=self.get('terminal_tx_head');count=self.get('terminal_tx_count');start=self.symbols['terminal_tx_buffer']
  return bytes(self.uc.mem_read(start+((at+i)&1023),1)[0] for i in range(count))
 def clear(self):
  for name in ('terminal_tx_head','terminal_tx_tail','terminal_tx_count','terminal_quit','terminal_exit_code'):self.put(name,0)
  self.events=[];self.echo_counts=[]
def main():
 OUT.mkdir(exist_ok=True);m=Machine();cases=0
 half_unsupported={7,8,9,54,55}
 string_echo=set(range(7))|set(range(28,38))|{78}
 cursor={50:1,72:1,51:2,73:2,52:3,74:3,53:4,75:4,76:5}
 for profile in (4,6):
  m.put('csi_terminal_id',profile)
  bindings={slot:('P%dK%02d'%(profile,slot)).encode()+b'\xffZ' for slot in range(79)}
  for slot,value in bindings.items():m.uc.mem_write(m.symbols['terminal_keymap']+slot*12,value+b'\0'*(12-len(value)))
  for half in (0,1):
   for slot,key in sorted(KEYS.items()):
    m.clear();result=m.run(key,half);expected=3 if half and slot in half_unsupported else 0
    assert result==expected,(profile,half,slot,result)
    assert m.wire()==(b'' if expected else bindings[slot].replace(b'\xff',b'\0'))
    events=[]
    if half and not expected:
     if slot in string_echo:events=[('echo',b) for b in bindings[slot]]
     elif slot==10:events=[('echo',8)]
     elif slot in cursor:events=[('cursor',cursor[slot])]
    assert m.events==events,(profile,half,slot,m.events,events)
    assert m.echo_counts==[len(m.wire())]*len(events)
    assert not m.get('terminal_quit');cases+=1
 for byte in range(1,256):
  if byte in (9,13,28,29,31):continue
  for half in (0,1):
   m.clear();assert m.run(byte,half)==0 and m.wire()==bytes([byte])
   assert m.events==([('echo',byte)] if half and byte!=27 else []);cases+=1
   assert m.echo_counts==([0] if half and byte!=27 else [])
 for raw in (0x1ce0,0x35e0):
  m.clear();slot=5 if raw==0x1ce0 else 4
  assert m.run(raw)==0 and m.wire()==bindings[slot].replace(b'\xff',b'\0');cases+=1
 for raw in (0x7800,0x2c00,0x7000,0x8300,0xfe00,28,29,31):
  m.clear();assert m.run(raw)==3 and not m.wire() and not m.events;cases+=1
 m.clear();m.put('keyboard_mapping_hook_enabled',1);m.put('keyboard_mapping_hook_character',ord('x'),1)
 assert m.run(ord('x'))==3 and not m.wire();cases+=1;m.put('keyboard_mapping_hook_enabled',0)
 for raw in (0,0x8b00,0x8c00,0x9200,0xffff):
  m.clear();assert m.run(raw)==0 and not m.wire() and not m.events;cases+=1
 for half in (0,1):
  m.clear();m.uc.mem_write(m.symbols['terminal_keymap']+16*12,b'X'*12)
  assert m.run(KEYS[16],half)==7 and not m.wire() and not m.events;cases+=1
 m.clear();m.put('terminal_tx_count',1020);m.uc.mem_write(m.symbols['terminal_tx_buffer'],b'Q'*1024)
 before=m.wire();assert m.run(KEYS[0])==14 and m.wire()==before
 assert m.get('terminal_quit')==1 and m.get('terminal_exit_code')==3;cases+=1
 m.clear();m.put('modes_value_1d1a',1);assert m.run(ord('k'),65535)==0 and m.events==[('echo',ord('k'))];cases+=1
 m.clear();assert m.run(ord('k'),256)==7 and not m.wire() and not m.events;cases+=1
 report=dict(passed=True,cases=cases,all79_slots=True,profiles=[4,6],duplex=[0,1],binary_sha256=sha(ROOT/'build/terminal/TERMINAL.EXE'),checker_sha256=sha(Path(__file__)),original_inputs=[],scope='Actual product far key core, raw classifier, bindings and queue instructions. Echo/cursor scalar endpoints are explicit recording fixtures; actual renderer and child UART covered separately. Full/half, FF wire/echo distinction, literal/control, native no-op/local rejection, aliases, malformed binding and atomic capacity failure. Half reverse-tab/insert/delete remain unsupported before output.')
 (OUT/'checks.json').write_text(json.dumps(report,indent=2)+'\n');print('Shared terminal key output',cases,'cases PASS')
if __name__=='__main__':main()
