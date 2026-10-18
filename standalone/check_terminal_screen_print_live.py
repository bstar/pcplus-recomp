#!/usr/bin/env python3
"""Actual CSI screen-print/queue/device instructions; only kernel/hardware modeled."""
import hashlib,json,struct
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
from check_terminal_printer_live import Printer
from check_meta_actions_live import ROOT,BINARY
class ExplicitGap(Exception):pass
class ScreenPrint(Printer):
 def __init__(self,**kw):
  super().__init__(**kw)
  self.put('ui_flow_suppressed',1);self.put('modes_value_3980',0)
  self.uc.reg_write(UC_X86_REG_DX,0);self.call('screen_set_cursor',ax=0)
  self.raw=bytes((i*29+i//80)%256 for i in range(2000))
  video=b''.join(bytes((c,1+i%15)) for i,c in enumerate(self.raw))
  self.uc.mem_write(0xb8000,video)
  self.reads=0;self.mutate_frozen=False;self.inject_key=None;self.injected=False
  self.uc.hook_add(UC_HOOK_CODE,self.observe_screen)
 def observe_screen(self,u,address,size,_):
  if address==self.symbols['ui_read_byte'] and self.get('terminal_screen_print_active'):self.reads+=1
  if address==self.symbols['terminal_abort']:raise ExplicitGap(u.reg_read(UC_X86_REG_AX))
 def interrupt(self,u,n,d):
  ax=u.reg_read(UC_X86_REG_AX)
  if n==0x21 and ax>>8==0x40 and u.reg_read(UC_X86_REG_BX)==63:
   if self.mutate_frozen:
    assert self.reads==2000,'complete view must freeze before device IO'
    self.uc.mem_write(0xb8000,b'Z\x4f'*2000);self.mutate_frozen=False
   if self.inject_key is not None and not self.injected:self.keys.append(self.inject_key);self.injected=True
  super().interrupt(u,n,d)
 def expected(self,first=0,last=25,ff=False):
  return b''.join(self.raw[y*80:(y+1)*80]+b'\r\n' for y in range(first,last))+(b'\x0c' if ff else b'')
 def print_screen(self,mode):
  regs={UC_X86_REG_AX:mode,UC_X86_REG_BX:0x1111,UC_X86_REG_CX:0x2222,UC_X86_REG_DX:0x3333,UC_X86_REG_BP:0xbabe,UC_X86_REG_SI:0x1234,UC_X86_REG_DI:0x5678,UC_X86_REG_ES:0xb800}
  for r,v in regs.items():self.uc.reg_write(r,v)
  self.call('terminal_screen_print',ax=mode,limit=3000000)
  for r,v in regs.items():assert self.uc.reg_read(r)==v,('screen print register',r,self.uc.reg_read(r),v)
  assert self.uc.reg_read(UC_X86_REG_EFLAGS)&0x200
  assert not self.get('terminal_screen_print_active')
 def csi(self,data):
  self.rx.extend(data)
  while self.rx or self.get('uart_rx_count'):
   value=self.call('uart_receive_byte')
   if value!=65535:self.call('terminal_receive_character',[value],limit=3000000)
  assert not self.get('csi_unimplemented_service')

def main():
 digest=hashlib.sha256(BINARY.read_bytes()).hexdigest();groups=[]
 def check(name,fn):
  n=fn();groups.append(dict(case=name,inputs=n,passed=True));print(name,'PASS',n,flush=True)
 def raw():
  m=ScreenPrint();m.mutate_frozen=True;m.print_screen(1)
  assert m.device_bytes==m.expected() and m.reads>=2000
  assert m.get('terminal_screen_print_action')==1 and not m.device_live and m.owner()[10]==1
  assert m.owner()[12]==2050 and not m.get('terminal_printer_count')
  assert not m.get('terminal_sink_3988_enabled')
  return 2000
 check('all25x80-raw-characters-NUL-SUB-FF-attributes-stripped-frozen-before-deviceIO',raw)
 def modes():
  m=ScreenPrint();m.put('csi_scroll_top',3);m.put('csi_scroll_bottom',5);m.print_screen(2)
  assert m.device_bytes==m.expected(3,6)
  m=ScreenPrint();m.uc.reg_write(UC_X86_REG_DX,17);m.call('screen_set_cursor',ax=7);m.print_screen(3)
  assert m.device_bytes==m.expected(7,8)
  assert (m.get('screen_cursor_row'),m.get('screen_cursor_column'))==(7,17)
  for command,ff in [(b'\x1b[i',False),(b'\x1b[0i',True)]:
   m=ScreenPrint();m.put('modes_value_3980',int(ff));m.put('modes_value_3982',0);m.csi(command)
   assert m.device_bytes==m.expected(ff=ff)
  m=ScreenPrint();m.put('modes_value_3980',1);m.put('modes_value_3982',1);m.put('csi_scroll_top',4);m.put('csi_scroll_bottom',6);m.csi(b'\x1b[i')
  assert m.device_bytes==m.expected(4,7,True)
  m=ScreenPrint();m.put('modes_value_3980',1);m.uc.reg_write(UC_X86_REG_DX,9);m.call('screen_set_cursor',ax=11);m.csi(b'\x1b[1i')
  assert m.device_bytes==m.expected(11,12)
  return 6
 check('real-CSI-omitted-zero-currentrow-native-selected-region-and-optional-formfeed',modes)
 def stream():
  m=ScreenPrint();m.csi(b'\x1b[?5i');assert m.device_live and m.get('terminal_sink_3988_enabled')
  calls=list(m.device_calls);m.csi(b'\x1b[?5i');assert m.device_calls==calls
  m.log(b'PREFIX');m.print_screen(3);assert m.device_bytes==b'PREFIX'+m.expected(0,1)
  assert m.device_live and m.get('terminal_sink_3988_enabled') and not m.owner()[10]
  m.log(b'SUFFIX');m.finish();m.csi(b'\x1b[?4i');m.finish()
  assert m.device_bytes==b'PREFIX'+m.expected(0,1)+b'SUFFIX' and m.owner()[10]==1
  calls=list(m.device_calls);m.csi(b'\x1b[?4i');assert m.device_calls==calls
  m=ScreenPrint();m.csi(b'\x1b[4i');assert not m.device_calls
  m=ScreenPrint()
  try:m.csi(b'\x1b[5i')
  except ExplicitGap as gap:assert gap.args[0]==0xd0d0
  else:assert m.get('csi_unimplemented_service')==0xd0d0
  assert not m.device_calls
  return 6
 check('real-CSI-private-copy-onoff-idempotence-existing-queue-order-and-standard5-gap',stream)
 def geometry():
  vectors=[('mode',0x13),('columns',40),('page',1),('text_cga_status_port',0x3da),('text_video_segment',0xb000),('screen_video_row_bytes',158),('screen_columns',79),('csi_row_count',24),('screen_viewport_enabled',1)]
  for name,value in vectors:
   m=ScreenPrint()
   if name in ('mode','columns','page'):setattr(m,name,value)
   else:m.put(name,value)
   m.print_screen(1);assert m.get('terminal_screen_print_action')==2 and not m.reads and not m.device_calls,name
  m=ScreenPrint();m.uc.mem_write(0x484,b'\x31');m.print_screen(1)
  assert m.get('terminal_screen_print_action')==2 and not m.reads and not m.device_calls
  return len(vectors)+1
 check('unsupported-mode-page-height-CGA-source-width-denied-before-read-or-device',geometry)
 def cancellation():
  for key,quit in [(0x011b,0),(0x2d00,1)]:
   m=ScreenPrint();m.inject_key=key;m.print_screen(1)
   assert m.injected and m.get('terminal_screen_print_action')==3 and m.get('terminal_quit')==quit
   assert 0<len(m.device_bytes)<2050 and m.expected().startswith(m.device_bytes)
   assert not m.device_live and m.owner()[10]==1
  m=ScreenPrint();m.inject_key=ord('q');m.print_screen(1)
  assert m.device_bytes==m.expected() and m.call('terminal_take_deferred_key')==ord('q')
  assert not m.uc.reg_read(UC_X86_REG_EFLAGS)&1
  return 3
 check('mid-output-Escape-AltX-bounded-cancel-checked-prefix-and-otherkey-deferred',cancellation)
 def native_flags():
  m=ScreenPrint();m.put('csi_scroll_top',2);m.put('csi_scroll_bottom',3)
  m.csi(b'\x1b[18l\x1b[19h\x1b[i')
  assert m.get('modes_value_3980')==0 and m.get('modes_value_3982')==0 and m.device_bytes==m.expected()
  m=ScreenPrint();m.put('csi_scroll_top',2);m.put('csi_scroll_bottom',3)
  m.csi(b'\x1b[?18h\x1b[?19l\x1b[i')
  assert m.get('modes_value_3980')==1 and m.get('modes_value_3982')==1 and m.device_bytes==m.expected(2,4,True)
  return 2
 check('actual-native-mode18-formfeed-mode19-region-standard-and-private-prefix',native_flags)
 def metadata():
  m=ScreenPrint();m.print_screen(3);assert m.get('terminal_screen_print_bytes')==82
  before=list(m.device_calls);m.print_screen(0)
  assert m.get('terminal_screen_print_action')==2 and m.get('terminal_screen_print_bytes')==0 and m.device_calls==before
  m.put('terminal_screen_print_active',1);m.put('terminal_screen_print_action',1);m.put('terminal_screen_print_bytes',123)
  frame=bytes(m.uc.mem_read(m.symbols['terminal_snapshot_image'],2000));m.call('terminal_screen_print',ax=1)
  assert m.get('terminal_screen_print_active')==1 and m.get('terminal_screen_print_action')==1 and m.get('terminal_screen_print_bytes')==123
  assert bytes(m.uc.mem_read(m.symbols['terminal_snapshot_image'],2000))==frame and m.device_calls==before
  return 2
 check('new-denied-request-clears-bytecount-active-reentry-leaves-current-frame-metadata',metadata)
 def busy_and_active_cancel():
  m=ScreenPrint();m.device_ready=0;m.advance_ticks=True;m.print_screen(3)
  assert m.get('terminal_screen_print_action')==4 and m.get('terminal_printer_sticky')==14
  assert not m.device_live and not m.device_bytes and m.owner()[10]==1
  m=ScreenPrint();m.toggle();m.queue(b'PREFIX');m.inject_key=0x011b;m.print_screen(1)
  assert m.get('terminal_screen_print_action')==3 and m.get('terminal_sink_3988_enabled') and m.device_live
  m.finish();prefix=bytes(m.device_bytes);assert prefix.startswith(b'PREFIX') and len(prefix)<2056 and m.owner()[10]==0
  m.log(b'AFTER');m.finish();assert m.device_bytes==prefix+b'AFTER'
  m.toggle();m.finish();assert m.owner()[10]==1
  return 2
 check('busy-device-bounded-no-progress-and-active-stream-Escape-keeps-handle',busy_and_active_cancel)
 def failures():
  for reason,status in [('open',0),('write',9),('short',9),('close',11),('close-drop',11)]:
   m=ScreenPrint(printer_fault=reason);m.print_screen(1)
   assert m.get('terminal_screen_print_action')==(2 if reason=='open' else 4)
   assert m.get('terminal_printer_sticky')==status
   assert sum(c[0]>>8==0x3e for c in m.device_calls)==(0 if reason=='open' else 1)
   before=list(m.device_calls)
   if reason.startswith('close'):
    m.print_screen(1);assert m.device_calls==before and m.get('terminal_screen_print_action')==2
  m=ScreenPrint();m.toggle();m.queue(b'X');m.printer_fault='write';m.poll_printer();assert m.get('terminal_printer_sticky')==9
  m.printer_fault=None;m.print_screen(3)
  assert m.device_bytes==m.expected(0,1) and m.get('terminal_screen_print_action')==1 and m.get('terminal_printer_sticky')==9
  return 6
 check('checked-open-write-short-close-uncertainty-and-success-after-priorsticky',failures)
 assert hashlib.sha256(BINARY.read_bytes()).hexdigest()==digest
 result=dict(binary_sha256=digest,passed=True,groups=groups,scope='Actual linked parser/media-copy/row reader/frozen-frame/queue/device code. Only DOS device/filesystem, BIOS and UART hardware modeled; no physical printer or driver-time-bound claim.')
 path=ROOT/'build/terminal/terminal-screen-print-live-checks.json';path.write_text(json.dumps(result,indent=2)+'\n');print(path)
if __name__=='__main__':main()
