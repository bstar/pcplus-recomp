#!/usr/bin/env python3
"""Linked live PRN queue/native logger/device owner; only kernel/hardware models.
No product callback is patched, skipped or manually returned from. No PRN IO.
"""
import hashlib,json,struct
from unicorn.x86_const import *
from check_terminal_monitor_live import Monitor
from check_meta_actions_live import ROOT,BINARY,DAY
class Printer(Monitor):
 def __init__(self,*,printer_fault=None,mode=0x8080):
  super().__init__()
  self.printer_fault=printer_fault;self.device_mode=mode;self.device_ready=255
  self.device_live=False;self.device_bytes=bytearray();self.device_calls=[];self.printer_exec_admissions=[]
  assert self.call('_printer_device_initialize')==0
 def interrupt(self,u,n,d):
  ax=u.reg_read(UC_X86_REG_AX);ah=ax>>8;bx=u.reg_read(UC_X86_REG_BX)
  if n==0x21 and ax==0x4b00:
   assert not self.device_live and not self.get('terminal_printer_count') and not self.owner()[5] and not self.owner()[6], 'PRN ownership inherited by DOS EXEC'
   assert self.device_calls[-1][0]>>8==0x3e, 'PRN close must precede EXEC'
   self.printer_exec_admissions.append(dict(device_closed=True,pending_bytes=0,close_calls=self.owner()[10]))
  opening=n==0x21 and ax==0x3d01 and self.path(u.reg_read(UC_X86_REG_DS),u.reg_read(UC_X86_REG_DX))=='PRN'
  if n!=0x21 or not(opening or bx==63 and (ah in (0x44,0x40,0x3e))):return super().interrupt(u,n,d)
  error=answer=0
  if opening:
   assert not self.device_live
   if self.printer_fault=='open':error=2
   else:self.device_live=True;self.handles[63]='PRN';answer=63
  elif not self.device_live:error=6
  elif ax==0x4400:
   if self.printer_fault=='identity':error=1
   else:u.reg_write(UC_X86_REG_DX,self.device_mode)
  elif ax==0x4401:
   mode=u.reg_read(UC_X86_REG_DX);assert mode<256,'4401 DH must be zero'
   if self.printer_fault=='mode' or self.printer_fault=='restore' and not mode&32:error=1
   else:self.device_mode=(self.device_mode&0xff00)|mode
   answer=mode
  elif ax==0x4407:
   if self.printer_fault=='ready':error=5
   else:answer=self.device_ready
  elif ah==0x40:
   count=u.reg_read(UC_X86_REG_CX);assert count==1,'only exact single-byte writes admitted'
   if self.printer_fault=='write':error=112
   elif self.printer_fault!='short':
    answer=1;self.device_bytes.extend(u.mem_read(u.reg_read(UC_X86_REG_DS)*16+u.reg_read(UC_X86_REG_DX),1))
  elif ah==0x3e:
   if self.printer_fault in ('close','close-drop'):
    error=6
    if self.printer_fault=='close-drop':self.device_live=False;del self.handles[63]
   else:self.device_live=False;del self.handles[63]
  else:raise AssertionError(('Unexpected printer syscall',hex(ax)))
  self.device_calls.append((ax,error,answer));u.reg_write(UC_X86_REG_AX,error or answer);self.set_carry(bool(error))
 def preserved(self,name,ax=0x4444):
  regs={UC_X86_REG_AX:ax,UC_X86_REG_BX:0x1111,UC_X86_REG_CX:0x2222,UC_X86_REG_DX:0x3333,UC_X86_REG_BP:0xbabe,UC_X86_REG_SI:0x1234,UC_X86_REG_DI:0x5678,UC_X86_REG_ES:0xb800}
  for r,v in regs.items():self.uc.reg_write(r,v)
  self.call(name,ax=ax)
  for r,v in regs.items():assert self.uc.reg_read(r)==v,(name,'register',r,self.uc.reg_read(r),v)
  assert self.uc.reg_read(UC_X86_REG_EFLAGS)&0x200==0x200
 def toggle(self):self.preserved('terminal_printer_toggle')
 def poll_printer(self):self.preserved('terminal_printer_poll')
 def queue(self,data):
  for value in data:self.call('terminal_sink_36fc',[value])
 def finish(self):
  for _ in range(20):
   if not self.get('terminal_printer_count') and not self.get('terminal_printer_closing'):return
   self.poll_printer()
  raise AssertionError('Printer failed to drain')
 def owner(self):return struct.unpack('<12H2I',bytes(self.uc.mem_read(self.symbols['_printer_device_result'],32)))

def main():
 digest=hashlib.sha256(BINARY.read_bytes()).hexdigest();groups=[]
 def check(name,fn):
  count=fn();groups.append(dict(case=name,inputs=count,passed=True));print(name,'PASS',count,flush=True)
 def binary():
  m=Printer();m.toggle();assert m.get('terminal_sink_3988_enabled')==1
  assert m.device_mode&32
  for block in (bytes(range(128)),bytes(range(128,256))):
   m.queue(block);assert m.get('terminal_printer_count')==128
   before=len(m.device_bytes);m.poll_printer();assert len(m.device_bytes)-before==16
   m.finish()
  assert m.device_bytes==bytes(range(256)) and m.owner()[12]==256
  m.toggle();m.finish();assert not m.device_live and not m.get('terminal_sink_3988_enabled')
  assert m.device_mode==0x8080 and m.owner()[10]==1
  assert m.device_calls[-2][0]==0x4401 and m.device_calls[-1][0]>>8==0x3e
  return 256
 check('all256-byte-queue-ringwrap-max16-write-poll-preserved-registers-mode-restore',binary)
 def native():
  for crlf in (0,1):
   m=Printer();assert m.begin()==0;m.toggle();m.put('terminal_cr_adds_lf',crlf)
   m.log(b'A\r\n\x7f\xffB');m.finish()
   assert m.device_bytes==b'A\r'+b'\n'*(crlf+1)+b'B'
   assert m.call('_capture_session_stop')==0 and m.contents()==b'A'+b'\r\n'*(crlf+1)+b'B'
   m.enter();m.feed(b'RAW\0\xff');m.stop();m.finish()
   assert m.dump()==b'RAW\0\xff' and m.device_bytes==b'A\r'+b'\n'*(crlf+1)+b'B'
   m.toggle();m.finish()
  return 2
 check('actual09b6-printerCR-LF-FF-DEL-textcapture-and-rawmonitor-coexistence',native)
 def holds():
  m=Printer();m.toggle();m.device_ready=0;m.queue(b'Q'*126)
  assert m.call('terminal_printer_receive_hold')==0
  m.log(b'\r');assert m.get('terminal_printer_count')==127 and m.call('terminal_printer_receive_hold')==1
  before=list(m.device_calls);m.poll_printer();assert not m.device_bytes and m.get('terminal_printer_count')==127
  assert len(m.device_calls)>len(before) and not m.get('terminal_printer_sticky')
  m.device_ready=255;m.finish();assert m.device_bytes==b'Q'*126+b'\r'
  m.toggle();m.finish();return 3
 check('receive-backpressure-reserves-two-native-output-bytes-busy-keeps-queue',holds)
 def timeout():
  for initial in (0,0xfff8,DAY-8):
   m=Printer();m.tick=initial;m.toggle();m.device_ready=0;m.queue(b'KEPT')
   m.tick=(initial+17)%DAY;m.poll_printer();assert not m.get('terminal_printer_sticky') and m.device_live
   m.tick=(initial+18)%DAY;m.poll_printer();assert m.get('terminal_printer_sticky')==14 and not m.device_live
   calls=list(m.device_calls);m.poll_printer();assert m.device_calls==calls and not m.device_bytes
  return 3
 check('18-full-BIOS-tick-no-progress-lowword-and-midnight-timeout',timeout)
 def errors():
  for fault,status in [('ready',8),('write',9),('short',9),('restore',10),('close',11),('close-drop',11)]:
   m=Printer();m.toggle();m.printer_fault=fault;assert m.get('terminal_sink_3988_enabled')
   m.queue(b'X')
   if fault in ('restore','close','close-drop'):m.poll_printer();m.toggle()
   m.poll_printer();assert m.get('terminal_printer_sticky')==status,(fault,m.get('terminal_printer_sticky'))
   before=list(m.device_calls);m.poll_printer();m.call('terminal_printer_shutdown')
   assert m.device_calls==before and sum(c[0]>>8==0x3e for c in m.device_calls)==1
   assert m.call('terminal_printer_before_program')==(1 if fault.startswith('close') else 0)
   m.printer_fault=None;m.toggle()
   if fault.startswith('close'):assert m.device_calls==before and not m.get('terminal_sink_3988_enabled')
   else:
    assert m.get('terminal_sink_3988_enabled');m.queue(b'R');m.poll_printer();assert m.device_bytes.endswith(b'R') and m.get('terminal_printer_sticky')==status
    m.toggle();m.finish()
  return 6
 check('ready-short-write-restore-close-errors-firststicky-no-retry-child-uncertainty',errors)
 def denied():
  for fault,mode in [('open',0x8080),('identity',0x8080),(None,0),('mode',0x8080)]:
   m=Printer(printer_fault=fault,mode=mode);m.toggle();assert not m.get('terminal_sink_3988_enabled') and not m.device_live
   assert m.get('terminal_printer_sticky')==(0 if fault=='open' else 6 if fault=='identity' or not mode else 7)
  return 4
 check('denied-open-UI-only-acquired-identity-mode-errors-sticky-close-once',denied)
 def gates():
  m=Printer();m.toggle();m.queue(b'AB');assert m.call('terminal_printer_barrier')==2
  assert m.get('terminal_sink_3988_enabled') and not m.get('terminal_printer_closing')
  m.poll_printer();assert m.call('terminal_printer_barrier')==0
  m.queue(b'CD');assert m.call('terminal_printer_before_program')==2
  assert m.get('terminal_printer_closing') and not m.get('terminal_sink_3988_enabled')
  m.finish();assert m.call('terminal_printer_before_program')==0 and not m.device_live and m.device_bytes==b'ABCD'
  m=Printer();m.toggle();m.device_ready=0;m.queue(b'STALLED');m.advance_ticks=True
  assert m.call('terminal_printer_shutdown',limit=500000)==14 and not m.device_live and m.tick<=40
  assert not m.device_bytes
  return 3
 check('transfer-barrier-preserves-enabled-PROGRAM-drains-closes-shutdown-bounded',gates)
 def admission():
  names=('terminal_monitor_active','terminal_parser_active','terminal_ansi_wait_active','terminal_macro_active','terminal_program_pending','terminal_transfer_active','terminal_transfer_pending','connection_state')
  for name in names:
   m=Printer();m.put(name,1);m.toggle()
   assert not m.device_calls and not m.get('terminal_sink_3988_enabled') and not m.get('terminal_printer_sticky'),name
  m=Printer();m.key(0x2600);assert m.get('terminal_sink_3988_enabled')
  m.queue(b'KEY');m.key(0x2600);m.finish();assert m.device_bytes==b'KEY' and not m.device_live
  return len(names)+1
 check('actual-AltL-key-route-and-owner-admission-no-printer-IO-on-denial',admission)
 def actual_program():
  for fault in (None,'close','close-drop'):
   m=Printer();m.toggle();m.queue(b'PRINT BEFORE CHILD');m.device_ready=0
   m.record(0,b'ECHO PRN',1);assert m.start()==0 and m.get('terminal_program_pending')
   command=bytes(m.uc.mem_read(m.symbols['terminal_program_command'],52)) if 'terminal_program_command' in m.symbols else None
   m.safe();assert m.get('terminal_program_pending') and m.get('terminal_printer_closing')
   assert not m.children and not m.printer_exec_admissions and not m.get('terminal_sink_3988_enabled')
   m.poll_printer();m.safe()
   assert m.get('terminal_program_pending') and m.get('terminal_printer_count')==18 and not m.children
   if command is not None:assert bytes(m.uc.mem_read(m.symbols['terminal_program_command'],52))==command
   m.device_ready=255;m.printer_fault=fault;m.finish()
   assert m.device_bytes==b'PRINT BEFORE CHILD' and m.owner()[10]==1
   m.safe()
   if fault:
    assert not m.children and not m.printer_exec_admissions and not m.get('terminal_program_pending')
    before=list(m.device_calls);m.safe();m.poll_printer();assert m.device_calls==before
    assert m.owner()[6] and m.get('terminal_printer_sticky')==11
   else:
    assert m.children==[{'path':b'Z:\\COMMAND.COM','tail':b' /c ECHO PRN'}]
    assert m.printer_exec_admissions==[dict(device_closed=True,pending_bytes=0,close_calls=1)]
    assert not m.get('terminal_program_pending') and not m.get('terminal_program_active')
  return 3
 check('actual-PROGRAM-safe-point-AX2-retry-drain-close-before-EXEC-uncertain-cancels',actual_program)
 def actual_transfer_barrier():
  m=Printer();m.toggle();m.queue(b'PENDING');m.put('terminal_transfer_pending',1)
  m.put('terminal_transfer_cleanup_status',0x7777);m.put('terminal_transfer_fault',0x5555)
  before=(list(m.device_calls),list(m.fs_calls),list(m.capture_calls),list(m.calls),bytes(m.uc.mem_read(0xb8000,4000)))
  for _ in range(3):m.call('terminal_transfer_poll')
  assert m.get('terminal_transfer_pending')==1 and not m.get('terminal_transfer_active')
  assert m.get('terminal_transfer_cleanup_status')==0x7777 and m.get('terminal_transfer_fault')==0x5555
  assert m.get('terminal_sink_3988_enabled') and not m.get('terminal_printer_closing')
  after=(m.device_calls,m.fs_calls,m.capture_calls,m.calls,bytes(m.uc.mem_read(0xb8000,4000)))
  assert before==after and not m.tx and not m.keys
  m.poll_printer();assert m.device_bytes==b'PENDING' and m.call('terminal_printer_barrier')==0
  # This scope proves the pending admission barrier; existing transfer engine
  # diagnostics independently exercise the full post-drain protocol owner.
  m.put('terminal_transfer_pending',0);m.toggle();m.finish()
  return 3
 check('actual-pending-transfer-poll-printer-barrier-before-UI-state-DOS-or-wire',actual_transfer_barrier)
 def overflow():
  m=Printer();m.toggle();m.device_ready=0;m.queue(b'A'*128);m.queue(b'Z')
  assert m.get('terminal_printer_sticky')==13 and not m.get('terminal_sink_3988_enabled')
  m.poll_printer();assert not m.device_live and not m.device_bytes and m.owner()[10]==1
  return 1
 check('queue-overflow-explicit-sticky-never-overwrites-or-writes-prefix',overflow)
 assert hashlib.sha256(BINARY.read_bytes()).hexdigest()==digest
 result=dict(binary_sha256=digest,passed=True,groups=groups,scope='Actual linked native logger, live queue/foreground policy, checked C owner and DOS IOCTL boundary instructions. Only DOS device/filesystem, BIOS ticks/keyboard and UART hardware modeled; no physical PRN or driver timing claim.')
 path=ROOT/'build/terminal/terminal-printer-live-checks.json';path.write_text(json.dumps(result,indent=2)+'\n');print(path)
if __name__=='__main__':main()
