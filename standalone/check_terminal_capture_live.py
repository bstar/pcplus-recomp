#!/usr/bin/env python3
"""Execute actual linked native logger, capture owner, file bridge and PROGRAM.

Only DOS filesystem/BIOS/UART boundaries are modeled. No application callback
is patched, skipped or manually returned from. All data and paths are synthetic.
"""
import hashlib,json,struct
from unicorn.x86_const import *
from check_terminal_transfer_live import LiveTransfer
from check_program_actions_live import LiveProgram
from check_meta_actions_live import ROOT,BINARY,DAY

class Capture(LiveTransfer):
 def __init__(self,*,fault=None):
  super().__init__(peer=False)
  self.capture_fault=fault;self.positions={};self.capture_calls=[];self.attributes={}
  # This composition tests file ownership at EXEC. UART-mutating children use
  # LiveProgram's separate hardware model and regression, not this peer ISR.
  self.mutate_child=False
  self.advance_ticks=False
  assert self.call('_capture_session_initialize')==0
 def interrupt(self,u,number,data):
  ax=u.reg_read(UC_X86_REG_AX);ah=ax>>8
  if number==0x21 and ah==0x43:
   path=self.path(u.reg_read(UC_X86_REG_DS),u.reg_read(UC_X86_REG_DX))
   if path.startswith('Z:'):return LiveProgram.interrupt(self,u,number,data)
  # PROGRAM's executable/environment syscalls remain in the existing kernel.
  capture=number==0x21 and (ah in (0x43,0x5b,0x40,0x3e,0x42) or ah==0x3d and ax==0x3d01)
  if not capture:return super().interrupt(u,number,data)
  ds=u.reg_read(UC_X86_REG_DS);dx=u.reg_read(UC_X86_REG_DX)
  bx=u.reg_read(UC_X86_REG_BX);cx=u.reg_read(UC_X86_REG_CX)
  error=0;answer=0;name=None
  if ah in (0x43,0x5b,0x3d):name=self.path(ds,dx)
  else:name=self.handles.get(bx)
  if ah==0x43:
   if name not in self.files:error=2
   else:u.reg_write(UC_X86_REG_CX,self.attributes.get(name,0))
  elif ah==0x5b:
   if name in self.files:error=80
   else:
    self.files[name]=bytearray();answer=5;self.handles[5]=name;self.positions[5]=0
  elif ah==0x3d:
   if name not in self.files:error=2
   else:answer=5;self.handles[5]=name;self.positions[5]=0
  elif ah==0x42:
   if name is None:error=6
   else:
    assert ax==0x4202 and not cx and not dx
    answer=len(self.files[name]);self.positions[bx]=answer;u.reg_write(UC_X86_REG_DX,answer>>16);answer&=65535
  elif ah==0x40:
   if name is None:error=6
   elif self.capture_fault=='write':error=5
   else:
    answer=1 if self.capture_fault=='short' and cx else cx
    at=self.positions[bx];self.files[name][at:at+answer]=u.mem_read(ds*16+dx,answer);self.positions[bx]+=answer
  elif ah==0x3e:
   if name is None:error=6
   elif self.capture_fault=='close':error=6
   else:del self.handles[bx];del self.positions[bx]
  self.capture_calls.append((ah,name,error,answer))
  u.reg_write(UC_X86_REG_AX,error or answer)
  flags=u.reg_read(UC_X86_REG_EFLAGS);u.reg_write(UC_X86_REG_EFLAGS,flags|1 if error else flags&~1)
 def begin(self,path=b'LOG.TXT',tick=0):
  pointer=self.offset('terminal_stack_top')+16
  self.uc.mem_write(self.data_base+pointer,path+b'\0')
  return self.call('_capture_session_begin',[pointer,tick&65535,tick>>16])
 def log(self,data):
  for value in data:self.call('terminal_log_character',[value])
 def contents(self,name='LOG.TXT'):return bytes(self.files[name])

def main():
 digest=hashlib.sha256(BINARY.read_bytes()).hexdigest();groups=[]
 def check(name,fn):
  count=fn();groups.append({'case':name,'inputs':count,'passed':True});print(name,'PASS',count,flush=True)
 def filtering():
  for crlf in (0,1):
   m=Capture();assert m.begin()==0;m.put('terminal_cr_adds_lf',crlf)
   m.log(b'A\r\n\x7f\xffB');assert m.call('_capture_session_stop')==0
   assert m.contents()==b'A'+b'\r\n'*(1+crlf)+b'B'
   assert not m.handles and m.get('terminal_exit_code')==0
  return 2
 check('actual-native09b6-CR-LF-FF-DEL-with-checked-text-translation',filtering)
 def pause_append():
  m=Capture();m.files['LOG.TXT']=bytearray(b'old\x1a');assert m.begin()==0
  m.log(b'one');assert m.call('_capture_session_pause')==0 and m.contents()==b'old\x1aone'
  m.log(b'HELD');assert m.call('_capture_session_pause')==0;m.log(b'two')
  assert m.call('_capture_session_stop')==0 and m.contents()==b'old\x1aonetwo'
  assert m.begin()==0;m.log(b'new');assert m.call('_capture_session_shutdown')==0
  assert m.contents()==b'old\x1aonetwonew' and not m.handles
  return 1
 check('append-keeps-textEOF-pause-flushes-no-heldbytes-repeat-open',pause_append)
 def timer():
  for start in (0,0xfff8,DAY-8):
   m=Capture();assert m.begin(tick=start)==0;m.log(b'CLOCK')
   for delay in (17,18):
    now=(start+delay)%DAY;m.call('_capture_session_poll',[now&65535,now>>16])
    assert m.contents()==(b'' if delay==17 else b'CLOCK')
  return 3
 check('foreground18tick-flush-with-lowword-wrap-and-BIOS-midnight',timer)
 def errors():
  for reason in ('write','short'):
   for cr in (False,True):
    m=Capture(fault=reason);assert m.begin()==0
    m.log(b'X'*(255 if cr else 256))
    if cr:m.put('terminal_cr_adds_lf',1);m.log(b'\r')
    assert not m.get('terminal_sink_398a_enabled') and not m.handles
    assert m.get('_capture_session_failed')==8 and m.get('_capture_session_notice')==4
    assert m.contents()==(b'X' if reason=='short' else b'')
    calls=len(m.capture_calls);m.log(b'MUST NOT WRITE');assert len(m.capture_calls)==calls
    assert m.call('_capture_session_shutdown')==8
    assert len([c for c in m.capture_calls if c[0]==0x3e])==1
    assert not m.get('terminal_quit') and not m.get('terminal_exit_code')
  return 4
 check('ordinary-and-native-unchecked-CR-errors-close-once-no-viewport-trap',errors)
 def uncertain():
  m=Capture(fault='close');assert m.begin()==0;m.log(b'KEPT')
  assert m.call('_capture_session_stop')==9 and m.contents()==b'KEPT'
  before=list(m.capture_calls)
  assert m.begin()==11 and m.call('_capture_session_shutdown')==9
  assert m.capture_calls==before and m.get('_capture_file_result')==4
  return 1
 check('uncertain-close-never-retried-or-reopened-sticky-error',uncertain)
 def admission():
  for state in (1,2,3,4,5,7,8):
   m=Capture();m.put('connection_state',state);m.call('terminal_capture_toggle')
   assert not m.capture_calls and m.get('_capture_session_notice')==5
  for flag in ('terminal_macro_active','terminal_program_pending','terminal_ansi_wait_active'):
   m=Capture();m.put(flag,1);m.call('terminal_capture_toggle');assert not m.capture_calls
  m=Capture();m.call('terminal_capture_pause');assert not m.capture_calls
  return 11
 check('prompt-rejects-other-owners-no-fileIO-and-inactive-pause-noop',admission)
 def child():
  m=Capture();assert m.begin()==0;m.log(b'PARENT');assert m.queue(b'ECHO CHILD')==0
  m.safe();assert len(m.children)==1 and not m.handles and m.contents()==b'PARENT'
  assert not m.get('terminal_sink_398a_enabled')
  m=Capture(fault='close');assert m.begin()==0;m.log(b'PARENT');assert m.queue(b'ECHO CHILD')==0
  m.safe();assert not m.children and not m.get('terminal_program_pending')
  assert len([c for c in m.capture_calls if c[0]==0x3e])==1
  return 2
 check('PROGRAM-flush-close-before-EXEC-uncertain-close-cancels-child',child)
 result={'passed':True,'binary_sha256':digest,'cases':groups,'scope':'Actual linked native09b6, maintained capture session/file/UI bridges and PROGRAM code; only DOSfilesystem/BIOS/UART hardware modeled. Synthetic data. Actual full UART DOS/UI and FSfault diagnostics are separate evidence.'}
 (ROOT/'build/terminal/terminal-capture-live-checks.json').write_text(json.dumps(result,indent=2)+'\n')
 print('Live capture:',len(groups),'groups,',sum(g['inputs'] for g in groups),'inputs PASS')
if __name__=='__main__':main()
