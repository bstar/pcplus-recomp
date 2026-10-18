#!/usr/bin/env python3
"""Actual linked monitor, UART ISR, renderer, keyboard and checked file owners.
Only DOS filesystem/BIOS/UART boundaries are modeled; no product callback skips.
"""
import hashlib,json,struct
from unicorn.x86_const import *
from check_terminal_capture_live import Capture
from check_meta_actions_live import ROOT,BINARY,DAY
class Monitor(Capture):
 def __init__(self,*,fault=None):
  super().__init__(fault=fault)
  assert self.call('_monitor_file_initialize')==0
  assert self.call('_snapshot_file_initialize')==0
  self.uc.mem_write(0x484,b'\x18')
 def interrupt(self,u,n,d):
  if n==0x10 and u.reg_read(UC_X86_REG_AX)>>8==6:
   ax=u.reg_read(UC_X86_REG_AX);cx=u.reg_read(UC_X86_REG_CX);dx=u.reg_read(UC_X86_REG_DX)
   top,left,bottom,right=cx>>8,cx&255,dx>>8,dx&255
   assert 0<=top<=bottom<25 and 0<=left<=right<80
   lines=ax&255;fill=bytes([32,(u.reg_read(UC_X86_REG_BX)>>8)&255])*(right-left+1)
   old=bytes(u.mem_read(0xb8000,4000))
   for row in range(top,bottom+1):
    start=(row*80+left)*2;source=((row+lines)*80+left)*2
    u.mem_write(0xb8000+start,old[source:source+len(fill)] if lines and row+lines<=bottom else fill)
   return
  if n==0x21 and u.reg_read(UC_X86_REG_AX)>>8==0x3c:
   name=self.path(u.reg_read(UC_X86_REG_DS),u.reg_read(UC_X86_REG_DX))
   if self.capture_fault=='open':u.reg_write(UC_X86_REG_AX,5);self.set_carry(True);return
   self.files[name]=bytearray();h=next(i for i in range(5,64) if i not in self.handles)
   self.handles[h]=name;self.positions[h]=0;u.reg_write(UC_X86_REG_AX,h);self.set_carry(False)
   self.capture_calls.append((0x3c,name,0,h));return
  super().interrupt(u,n,d)
 def key(self,key):
  self.keys.append(key);self.call('terminal_poll_io')
 def enter(self,answer=ord('Y')):
  self.key(0x2b1c);assert self.get('terminal_monitor_active')==2
  self.key(answer);assert self.get('terminal_monitor_active')==1
 def feed(self,data):
  self.rx.extend(data);values=[]
  while self.rx or self.get('uart_rx_count'):
   value=self.call('uart_receive_byte')
   if value==65535:continue
   self.call('terminal_monitor_filter',ax=value)
   assert self.uc.reg_read(UC_X86_REG_EFLAGS)&0x201==0x201
   for reg,want in [(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678),(UC_X86_REG_ES,0xb800)]:assert self.uc.reg_read(reg)==want
   values.append(value)
  return bytes(values)
 def dump(self):return bytes(self.files.get('PCPLUS.DMP',b''))
 def stop(self):self.key(0x011b);assert not self.get('terminal_monitor_active')

def main():
 groups=[]
 def check(name,fn):
  n=fn();groups.append(dict(case=name,inputs=n,passed=True));print(name,'PASS',n,flush=True)
 def raw():
  m=Monitor();m.files['PCPLUS.DMP']=bytearray(b'OLD\x1aLONGSUFFIX');m.enter()
  data=bytes(range(256));assert m.feed(data)==data
  want=bytes(48 if x==0 else 63 if x==255 else x for x in range(256))
  video=bytes(m.uc.mem_read(0xb8000,512));assert video[::2]==want,(video[::2],want)
  assert video[1::2]==bytes(15 if x in (0,27,255) else 7 for x in range(256))
  assert m.dump()==data and m.get('terminal_monitor_buffer_count')==0
  m.feed(b'\r\n\x1b[2J\0\x1a\xff');m.stop()
  assert m.dump()==data+b'\r\n\x1b[2J\0\x1a\xff' and not m.handles
  assert m.call('terminal_monitor_shutdown')==0
  return 256
 check('all256-UART-ISR-bytes-native-renderer-special-attributes-binary-replace-and-close',raw)
 def prompts():
  for key in (ord('n'),ord('N'),13,27):
   m=Monitor();m.files['PCPLUS.DMP']=bytearray(b'KEEP');m.enter(key);m.feed(b'\0\xff');m.stop()
   assert m.dump()==b'KEEP' and not m.capture_calls and not m.get('terminal_quit')
  m=Monitor();m.key(0x2b1c);m.rx.extend(b'QUEUED\0\xff');m.call('terminal_poll_io')
  assert m.get('uart_rx_count')==8 and m.get('terminal_monitor_active')==2
  m.key(ord('y'));assert m.feed(b'')==b'QUEUED\0\xff';m.stop();assert m.dump()==b'QUEUED\0\xff'
  return 5
 check('N-Enter-promptEscape-viewonly-and-prompt-keeps-UART-data-queued',prompts)
 def timers():
  for start in (0,0xfffb,DAY-5):
   m=Monitor();m.enter();m.tick=start;m.feed(b'PENDING')
   m.tick=(start+17)%DAY;m.call('terminal_monitor_poll');assert m.dump()==b''
   m.tick=(start+18)%DAY;m.call('terminal_monitor_poll');assert m.dump()==b'PENDING'
   m.stop()
  return 3
 check('18-full-BIOS-ticks-flush-lowword-and-midnight-wrap',timers)
 def dequeue_policy():
  data=bytes(range(256))
  for software,mask in [(0,127),(1,255)]:
   m=Monitor();m.enter();m.put('uart_software_flow',software);m.put('uart_rx_mask',mask)
   expected=bytes(x&mask for x in data if not software or x not in (17,19))
   assert m.feed(data)==expected;m.stop();assert m.dump()==expected
  return 2
 check('actual-UART-mask-and-software-XON-XOFF-consumption-before-monitor-boundary',dequeue_policy)
 def coexist():
  for held in (0,1):
   m=Monitor();assert m.begin()==0;m.log(b'BEFORE')
   if held:m.call('_capture_session_pause')
   m.enter();m.feed(bytes(range(256)));m.stop();m.log(b'AFTER');m.call('_capture_session_stop')
   assert m.contents()==(b'BEFORE' if held else b'BEFOREAFTER') and m.dump()==bytes(range(256))
  for path in (b'PCPLUS.DMP',b'C:\\PCPLUS.DMP'):
   m=Monitor();assert m.begin(path)==0;m.log(b'KEEP');m.call('_capture_session_flush')
   state=bytes(m.uc.mem_read(m.symbols['_capture_file_result'],96));m.enter();m.feed(b'LOST');m.stop()
   assert m.dump()==b'KEEP' and not m.get('terminal_monitor_failed')
   assert bytes(m.uc.mem_read(m.symbols['_capture_file_result'],96))==state
  m=Monitor();m.files['PCPLUS.DMP']=bytearray(b'LOCKED');m.attributes['PCPLUS.DMP']=1;m.enter();m.feed(b'X');m.stop()
  assert m.dump()==b'LOCKED' and m.call('terminal_monitor_shutdown')==0
  return 5
 check('independent-active-held-textcapture-canonical-alias-and-readonly-denial',coexist)
 def failures():
  for fault in ('write','short','close'):
   m=Monitor(fault=fault);m.enter();m.feed(b'FAIL');m.stop()
   assert m.get('terminal_monitor_failed')==(9 if fault=='close' else 8)
   assert len([x for x in m.capture_calls if x[0]==0x3e])==1
   assert m.call('terminal_monitor_shutdown')!=0
   assert len([x for x in m.capture_calls if x[0]==0x3e])==1
   if fault=='close':
    prior=list(m.capture_calls);m.key(0x2b1c);assert m.get('terminal_monitor_active')==0 and m.capture_calls==prior
    assert m.queue(b'ECHO CHILD')==0;m.safe();assert not m.children
  return 3
 check('write-short-close-sticky-partial-no-retry-and-uncertain-child-block',failures)
 def open_and_carrier():
  m=Monitor(fault='open');m.files['PCPLUS.DMP']=bytearray(b'KEEP');m.enter();m.feed(b'VIEW');m.stop()
  assert m.dump()==b'KEEP' and not m.get('terminal_monitor_failed') and m.call('terminal_monitor_shutdown')==0
  m=Monitor();m.put('connection_state',6);m.enter();m.feed(b'ONLINE');m.put('connection_state',0);m.call('terminal_monitor_poll')
  assert not m.get('terminal_monitor_active') and m.dump()==b'ONLINE' and not m.handles
  m=Monitor();m.key(0x2b1c);m.key(0x2d00)
  assert not m.get('terminal_monitor_active') and m.get('terminal_quit') and not m.capture_calls
  return 3
 check('unacquired-open-failure-viewonly-carrier-loss-and-prompt-AltX-close',open_and_carrier)
 def keyboard():
  m=Monitor();m.enter();m.key(0x2b1c);assert m.get('terminal_monitor_active')==1
  for key in (0x1300,0x1f00,0x2200,0x6800,0x7800):m.key(key)
  assert not m.get('terminal_transfer_pending') and not m.get('terminal_macro_active') and not m.get('terminal_quit')
  assert m.call('terminal_program_start',ax=0)==2
  assert m.call('terminal_macro_start',ax=0)==4
  m.key(ord('K'));m.drain();assert bytes(m.tx)==b'K'
  m.feed(b'RAW');m.key(0x2d00);assert m.get('terminal_quit') and not m.get('terminal_monitor_active') and m.dump()==b'RAW'
  return 9
 check('repeatCtrl-ordinaryTX-nested-owner-denial-AltX-closes-before-quit',keyboard)
 def rejects():
  tests=[('terminal_parser_active',1),('terminal_macro_active',1),('terminal_program_pending',1),('terminal_program_active',1),('terminal_ansi_wait_active',1),('terminal_transfer_pending',1),('terminal_transfer_active',1),('terminal_snapshot_active',1),('connection_state',3),('text_cga_status_port',0x3da),('text_video_segment',0xb000),('screen_attribute_row_bytes',132),('screen_video_row_bytes',264),('ui_flow_region_cells',132),('screen_viewport_enabled',1)]
  for name,n in tests:
   m=Monitor();m.put(name,n);m.call('terminal_monitor_start');assert not m.get('terminal_monitor_active') and not m.capture_calls
   assert m.get('terminal_monitor_last_action')==2 and m.uc.reg_read(UC_X86_REG_EFLAGS)&0x200
  for kind in ('mode','page','height'):
   m=Monitor()
   if kind=='mode':m.mode=0x13
   elif kind=='page':m.page=1
   else:m.uc.mem_write(0x484,b'\x31')
   m.call('terminal_monitor_start');assert not m.get('terminal_monitor_active') and not m.capture_calls
  return len(tests)+3
 check('parser-owner-geometry-CGA-rejections-are-bounded-no-fileIO',rejects)
 report=dict(passed=True,binary_sha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),cases=groups,scope='Actual linked monitor, renderer, UART ISR, keyboard/transport, canonical file owners and PROGRAM guard. Kernel/BIOS/hardware boundaries only are models. Dedicated actual DOS checks remain separate. No physical-wire, modem timing or complete original UI/HOOK claim.')
 (ROOT/'build/terminal/terminal-monitor-live-checks.json').write_text(json.dumps(report,indent=2)+'\n')
 print('Live monitor:',len(groups),'groups',sum(x['inputs'] for x in groups),'inputs PASS')
if __name__=='__main__':main()
