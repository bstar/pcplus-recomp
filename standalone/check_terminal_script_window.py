#!/usr/bin/env python3
"""Execute the retained blocking-window component and native keyboard loop."""
import json,struct,hashlib,argparse
from pathlib import Path
from unicorn import UC_HOOK_CODE,UC_HOOK_INTR,UC_HOOK_INSN
from unicorn.x86_const import *
from dos_image import DosImage
ROOT=Path(__file__).resolve().parents[1]
PRODUCT='terminal'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

class Window(DosImage):
 def __init__(self,keys,delay=0,error=0):
  super().__init__(ROOT/'build'/PRODUCT/'TERMINAL.EXE',ROOT/'build'/PRODUCT/'terminal.map')
  self.keys=list(keys);self.delay=delay;self.error=error;self.polls=0;self.reads=[];self.pages=set();self.cursor=0x111f;self.shape=0x0607
  self.put('terminal_aspect_active',1);self.put('keyboard_debug_gate',65535)
  self.frame=bytes((i*13+9)&255 for i in range(4000));self.uc.mem_write(0xb8000,self.frame)
  self.uc.hook_add(UC_HOOK_CODE,self.observe);self.uc.hook_add(UC_HOOK_INTR,self.interrupt)
  for instruction in (UC_X86_INS_IN,UC_X86_INS_OUT):
   self.uc.hook_add(UC_HOOK_INSN,self.forbidden,None,1,0,instruction)
 def forbidden(self,*unused):raise AssertionError('Window touched an undeclared parent device port')
 def observe(self,u,address,size,_):
  if u.reg_read(UC_X86_REG_EFLAGS)&0x200:
   assert u.reg_read(UC_X86_REG_DS)==u.reg_read(UC_X86_REG_SS),'foreign DS visible to interrupts'
  if address!=self.symbols['terminal_script_window_poll']:return
  self.polls+=1;assert self.get('terminal_script_window_active')==1 and self.get('keyboard_debug_gate')==0x29
  text=bytes(u.mem_read(0xb8000,4000))[::2]
  if b'TERMINAL KEYS' in text:self.pages.add('reference')
  if b'SCRIPT KEYBOARD HELP' in text:self.pages.add('help')
  u.mem_write(0x46c,struct.pack('<I',self.polls*2))
  sp=u.reg_read(UC_X86_REG_SP);ip=struct.unpack('<H',u.mem_read(self.data_base+sp,2))[0]
  u.reg_write(UC_X86_REG_AX,self.error);u.reg_write(UC_X86_REG_SP,sp+2);u.reg_write(UC_X86_REG_IP,ip)
 def interrupt(self,u,number,_):
  ah=u.reg_read(UC_X86_REG_AX)>>8
  if number==0x10:
   if ah==3:u.reg_write(UC_X86_REG_DX,self.cursor);u.reg_write(UC_X86_REG_CX,self.shape)
   elif ah==2:self.cursor=u.reg_read(UC_X86_REG_DX)
   elif ah==1:self.shape=u.reg_read(UC_X86_REG_CX)
   else:raise AssertionError(('video',ah))
  else:
   assert number==0x16 and ah in (0,1,16,17),(number,ah)
   if ah in (0,16):
    assert self.keys;raw=self.keys.pop(0);self.reads.append(raw);u.reg_write(UC_X86_REG_AX,raw)
   else:
    ready=self.keys and self.polls>self.delay;flags=u.reg_read(UC_X86_REG_EFLAGS)
    u.reg_write(UC_X86_REG_EFLAGS,(flags&~0x40) if ready else flags|0x40)
    u.reg_write(UC_X86_REG_AX,self.keys[0] if ready else 0x7777)
 def run(self,interrupts=True):
  u=self.uc;segment=self.symbols['terminal_script_window']//16
  # Near return trampoline belongs to the actual ASPECT code segment.
  m=json.loads((ROOT/'build'/PRODUCT/'manifest.json').read_text())
  segment=self.base_segment+next(c['relative_segment'] for c in m['memory_layout']['code_segments'] if c['name']=='ASPECT_CODE')
  u.mem_write(segment*16+0xfff0,b'\xcb');sp=self.offset('terminal_stack_top')-6
  for reg,value in [(UC_X86_REG_CS,segment),(UC_X86_REG_DS,self.ds),(UC_X86_REG_SS,self.ds),(UC_X86_REG_SP,sp),
    (UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678),(UC_X86_REG_ES,0x7200),(UC_X86_REG_EFLAGS,0x202 if interrupts else 2)]:u.reg_write(reg,value)
  u.mem_write(self.data_base+sp,struct.pack('<3H',0xfff0,self.return_offset,self.code_segment))
  u.emu_start(self.symbols['terminal_script_window'],0,count=1000000)
  assert self.returned and u.reg_read(UC_X86_REG_SP)==sp+6
  assert [u.reg_read(r) for r in (UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI,UC_X86_REG_ES)]==[0xbabe,0x1234,0x5678,0x7200]
  assert bytes(u.mem_read(0xb8000,4000))==self.frame
  assert (self.cursor,self.shape)==(0x111f,0x0607)
  assert self.get('keyboard_debug_gate')==65535
  return u.reg_read(UC_X86_REG_AX)

def main():
 global PRODUCT
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--mouse',action='store_true');a=p.parse_args()
 if a.mouse:PRODUCT='terminal-mouse'
 cases=[]
 for mode in (0,16):
  for name,keys,delay,error,left,reads,pages in [
    ('dismiss',[0x1e61],0,0,[],[0x1e61],{'reference'}),
    ('Escape-dismiss',[0x011b],0,0,[],[0x011b],{'reference'}),
    ('extended-retained',[0x3b00],0,0,[0x3b00],[],{'reference'}),
    ('repeat-help',[0x2c00,0x011b],0,0,[],[0x2c00,0x011b],{'reference','help'}),
    ('long-wait',[0x011b],100,0,[],[0x011b],{'reference'}),
    ('transport-error',[0x1e61],0,14,[0x1e61],[],{'reference'})]:
   w=Window(keys,delay,error);w.put('keyboard_bios_mode',mode,1)
   assert w.run()==error and w.keys==left and w.reads==reads and w.pages==pages,(name,mode,w.keys,w.reads,w.pages)
   assert not w.get('terminal_script_window_active') and not w.get('terminal_tx_count') and not w.get('terminal_quit')
   cases.append(dict(name=name,mode=mode,passed=True,polls=w.polls))
 for field,value in [('terminal_script_window_active',1),('terminal_aspect_active',0),('_redisplay_active',1),('_command_menu_active',1)]:
  w=Window([0x011b]);w.put(field,value);assert w.run()==10 and not w.polls and w.keys==[0x011b]
  cases.append(dict(name='reject-'+field,passed=True))
 w=Window([0x011b]);assert w.run(interrupts=False)==10 and not w.polls
 cases.append(dict(name='reject-interrupts-disabled',passed=True))
 out=ROOT/'build'/('terminal-script-window-mouse' if a.mouse else 'terminal-script-window');out.mkdir(exist_ok=True)
 r=dict(passed=True,cases=cases,terminal_sha256=sha(ROOT/'build'/PRODUCT/'TERMINAL.EXE'),checker_sha256=sha(Path(__file__)),
  scope='Retained native176-byte blocking-window component, maintained video/owner services, far keyboard adapters and recovered keyboard code. BIOS and child transport-poll endpoint are modeled. Full4000-byte frame, cursor/shape, key retention, repeat help, Escape, long wait, errors, DS=SS with IF and owner rejection are checked. Actual child UART and DOS tested separately.')
 (out/'cpu-results.json').write_text(json.dumps(r,indent=2)+'\n');print('Product script window',len(cases),'cases PASS')

if __name__=='__main__':main()
