#!/usr/bin/env python3
"""Exercise the actual modem CS, copied-word adapters, IRQs and MZ guards.

Only CPU calling frames and hardware/BIOS/kernel boundaries are supplied. Every
product thunk, target and return instruction executes unchanged.
"""
import hashlib,json,re,struct,tempfile
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
from check_connection import Connection
from check_terminal_print_controller_live import Controller
from check_meta_actions_live import ROOT,BINARY
from terminal_memory import inspect_terminal_memory
MAP=ROOT/'build/terminal/terminal.map'
class Modem(Connection):
 def __init__(self,**kw):
  self.dll=0x44;self.dlm=0x22
  super().__init__(**kw)
 def output_port(self,u,port,size,value,data):
  if self.lcr&0x80:
   if port==self.get('uart_port_thr'):self.dll=value;return
   if port==self.get('uart_port_ier'):self.dlm=value;return
  return super().output_port(u,port,size,value,data)
 def invoke(self,name,args=(),far=False,si=0x1234):
  u=self.uc;cs=self.symbols['terminal_modem_code_start']//16 if far else self.base_segment
  for reg,value in ((UC_X86_REG_CS,cs),(UC_X86_REG_DS,self.ds),(UC_X86_REG_SS,self.ds),(UC_X86_REG_ES,0xb800),(UC_X86_REG_EFLAGS,0x202),(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,si),(UC_X86_REG_DI,0x5678),(UC_X86_REG_AX,0),(UC_X86_REG_BX,0x1111),(UC_X86_REG_CX,0x2222),(UC_X86_REG_DX,0x3333)):u.reg_write(reg,value)
  sentinel=0xfffe if far else self.return_offset
  words=[sentinel,*args];sp=self.offset('terminal_stack_top')-2*len(words)
  u.mem_write(self.data_base+sp,struct.pack('<'+'H'*len(words),*words));u.reg_write(UC_X86_REG_SP,sp)
  returned=[False];self.returned=False
  def stop(cpu,address,size,_):
   if cpu.reg_read(UC_X86_REG_CS)==cs and address==cs*16+sentinel:returned[0]=True;cpu.emu_stop()
  hook=u.hook_add(UC_HOOK_CODE,stop) if far else None
  try:u.emu_start(self.symbols[name],0,count=300000)
  finally:
   if hook is not None:u.hook_del(hook)
  assert (returned[0] if far else self.returned) and u.reg_read(UC_X86_REG_CS)==cs
  assert u.reg_read(UC_X86_REG_SP)==sp+2
  assert bytes(u.mem_read(self.data_base+sp+2,len(args)*2))==struct.pack('<'+'H'*len(args),*args),'Original caller argument slots mutated'
  return tuple(u.reg_read(r) for r in (UC_X86_REG_AX,UC_X86_REG_BX,UC_X86_REG_CX,UC_X86_REG_DX,UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI,UC_X86_REG_ES,UC_X86_REG_EFLAGS))

def main():
 groups=[]
 def check(name,fn):
  detail=fn();groups.append(dict(case=name,passed=True,detail=detail));print(name,'PASS',flush=True)
 def frames():
  samples=[]
  for text,cap,outcap in [(b'AT^M\0',5,129),(b'^@^^^\0',6,129),(b'A'*51+b'\0',52,129),(b'BAD^\0',5,129),(b'NO-NUL',6,129),(b'AT^M\0',5,1)]:
   results=[];outputs=[]
   for far in (False,True):
    m=Modem();src=m.stage_near(text);dst=m.offset('terminal_tx_buffer');m.uc.mem_write(m.data_base+dst,b'\xcc'*129)
    results.append(m.invoke('connection_expand_service' if far else 'modem_expand_bounded',[src,dst,cap,outcap],far))
    outputs.append(bytes(m.uc.mem_read(m.data_base+dst,129)))
   assert results[0]==results[1] and outputs[0]==outputs[1],(text,results)
   samples.append(dict(source_hex=text.hex(),status=results[1][0],carry=bool(results[1][-1]&1)))
  for value in (0,ord('C'),255,256,65535):
   answers=[];cursors=[]
   for far in (False,True):
    m=Modem();answers.append(m.invoke('connection_responses_feed_service' if far else 'modem_responses_feed_bounded',[value],far))
    cursors.append(bytes(m.uc.mem_read(m.symbols['modem_response_cursors'],22)))
   assert answers[0]==answers[1] and cursors[0]==cursors[1]
  for index in (*range(12),0xffff):
   for current in range(10):
    for auto in (0,1,2):
     results=[]
     for far in (False,True):
      m=Modem();results.append(m.invoke('connection_classify_service' if far else 'modem_response_classify',[index,current,auto],far))
     assert results[0]==results[1],(index,current,auto,results)
  for baud in (300,1200,2400,4800,9600,19200,38400,57600,115200):
   values=[];registers=[]
   for far in (False,True):
    m=Modem();result=m.invoke('connection_set_baud_service' if far else 'uart_set_baud_divisor',[baud&65535,baud>>16],far)
    # Baud setter's BX is volatile and retains a byte of its actual frame SP.
    registers.append(result[:1]+result[2:]);values.append((m.dll,m.dlm,m.lcr))
   assert values[0]==values[1]==((115200//baud)&255,(115200//baud)>>8,3) and registers[0]==registers[1],(baud,values,registers)
  return dict(copied_word_counts=[1,2,3,4],expansion_samples=samples,classification_inputs=390,response_inputs=5,baud_inputs=9,returned_registers='AX/BX/CX/DX/BP/SI/DI/ES/FLAGS identical to direct target; volatile BX excluded for UART divisor setter',original_argument_slots_unchanged=True)
 check('real-one-through-four-word-adapters-arguments-errors-registers-FLAGS',frames)
 def runtime():
  m=Modem(autobaud=1);seen=set();minimum=[m.offset('terminal_stack_top')]
  cs=m.symbols['terminal_modem_code_start']//16
  entries=['terminal_connection_prepare','terminal_connection_start','terminal_connection_poll','terminal_connection_receive','terminal_connection_cancel','terminal_connection_exit','terminal_modem_send_start','terminal_modem_send_poll']
  def observe(u,address,size,_):
   if u.reg_read(UC_X86_REG_CS)==cs:
    assert u.reg_read(UC_X86_REG_DS)==u.reg_read(UC_X86_REG_SS)==m.ds
    minimum[0]=min(minimum[0],u.reg_read(UC_X86_REG_SP))
    for name in entries:
     if address==m.symbols[name+'_far']:seen.add(name)
  m.uc.hook_add(UC_HOOK_CODE,observe)
  assert m.call('terminal_connection_prepare')==0
  m.connect(b'CON19200');assert m.get('connection_baud_index')==5
  m.call('terminal_connection_cancel',ax=1)
  for _ in range(70):m.poll()
  m.call('terminal_connection_exit')
  # These are public diagnostic entries too; internal modem-to-sender calls
  # correctly remain near within MODEM_CODE instead of bouncing via residence.
  pointer=m.stage_near(b'\0')
  m.invoke('terminal_modem_send_start',si=pointer);m.invoke('terminal_modem_send_poll')
  assert seen==set(entries),seen
  assert bytes(m.tx).startswith(b'ATZ\rATDLocal.Example:2323\r')
  return dict(far_entries=sorted(seen),observed_stack_bytes=m.offset('terminal_stack_top')-minimum[0],actual_command_prefix=True)
 check('all-eight-public-entry-frames-real-dial-response-autobaud-hangup',runtime)
 def irq_and_nested():
  m=Controller();seen=set();frames=[];injected=[False]
  modem_cs=m.symbols['terminal_modem_code_start']//16;print_cs=m.symbols['terminal_controller_code_start']//16
  def observe(u,address,size,_):
   if u.reg_read(UC_X86_REG_CS) in (modem_cs,print_cs):seen.add(u.reg_read(UC_X86_REG_CS))
   if address==m.symbols['terminal_connection_poll_impl'] and not injected[0]:injected[0]=True;m.rx.append(ord('R'))
   if address==m.symbols['uart_receive_interrupt']:
    sp=u.reg_read(UC_X86_REG_SP);frames.append(struct.unpack('<3H',u.mem_read(m.data_base+sp,6)))
  m.uc.hook_add(UC_HOOK_CODE,observe)
  m.start_controller();m.keys.append(0x2d00)
  m.call('terminal_controller_run')
  assert injected[0] and any(cs==modem_cs for ip,cs,flags in frames),frames
  assert seen=={modem_cs,print_cs} and m.get('terminal_quit')
  m.call('terminal_controller_shutdown')
  assert m.uc.reg_read(UC_X86_REG_CS)==m.base_segment
  value=m.call('uart_receive_byte');buffered=bytes([value]) if value<=255 else b''
  assert bytes(m.device_bytes)+buffered==b'R' and m.call('uart_receive_byte')==0xffff,'IRQ byte lost or duplicated across nested CS return'
  return dict(actual_IRQ_frames=[list(f) for f in frames],modem_CS=modem_cs,controller_CS=print_cs,resumed_near_CS=m.base_segment)
 check('nested-print-resident-modem-CS-and-real-UART-ISR-IRET',irq_and_nested)
 def invalid():
  image=BINARY.read_bytes();listing=MAP.read_text();h=struct.unpack_from('<14H',image);start=h[4]*16
  syms={name:(int(seg,16),int(off,16)) for seg,off,name in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',listing,re.M|re.I)}
  def at(name):seg,off=syms[name];return start+seg*16+off
  mutations=[]
  for name,delta in [('terminal_connection_poll',3),('terminal_connection_poll_far',3),('connection_expand_resident',5),('connection_classify_resident',11),('connection_set_baud_resident',12),('connection_responses_feed_resident',3)]:
   bad=bytearray(image);bad[at(name)+delta]^=1;mutations.append((name,bad,listing))
  bad=bytearray(image);wanted=at('terminal_connection_poll')-start+3
  for i in range(h[3]):
   off,seg=struct.unpack_from('<HH',bad,h[12]+i*4)
   if seg*16+off==wanted:struct.pack_into('<HH',bad,h[12]+i*4,0,0);break
  else:raise AssertionError('No modem far relocation')
  mutations.append(('missing-modem-MZ-relocation',bad,listing))
  for kind,replacement in [('oversized',r'\g<1>00010001'),('missing-class',None)]:
   text=re.sub(r'(?m)^(MODEM_CODE\s+FARCODE\s+\S+\s+\S+\s+)\w+',replacement,listing) if replacement else listing.replace('MODEM_CODE','UNRECOGNIZED_MODEM_CODE')
   assert text!=listing;mutations.append((kind,image,text))
  with tempfile.TemporaryDirectory() as directory:
   exe=Path(directory)/'BAD.EXE';mp=Path(directory)/'BAD.MAP'
   for label,binary,mptext in mutations:
    exe.write_bytes(binary);mp.write_text(mptext)
    try:inspect_terminal_memory(exe,mp)
    except AssertionError:pass
    else:raise AssertionError(('Invalid modem frame accepted',label))
  return dict(rejected=[row[0] for row in mutations])
 check('nine-malformed-modem-frames-relocations-and-layouts-rejected',invalid)
 result=dict(passed=True,binary_sha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),groups=groups,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['standalone/check_modem_far_live.py','standalone/terminal_memory.py','src/terminal/far_bridge.inc','src/terminal/modem_abi.inc','src/terminal/modem_bridge.asm','src/terminal/connection.asm','src/terminal/modem_sender.asm']},scope='Actual linked static modem CS, near public entries, named resident callbacks and explicit1..4-word caller-cleaned adapters. Direct-target comparisons isolate ABI effects; existing independent connection tests supply behavior oracles. Nested PRINT/MODEM transitions and actual UART ISR/IRET execute under modeled hardware; DOS child retention remains separate. No general C callback/function-pointer ABI, callee-cleaned stack forwarding, dynamic overlays or physical modem proof.')
 (ROOT/'build/terminal/modem-far-checks.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
