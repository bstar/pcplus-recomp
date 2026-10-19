#!/usr/bin/env python3
"""Execute linked child BREAK owner, ISR, flow API and both close paths.

Only the UART/DOS environment is modeled; this is not pulse-duration or
physical-hardware evidence. No original binary or synthetic native stubs.
"""
import hashlib,json
from pathlib import Path
import check_aspect_serial as serial
from unicorn.x86_const import *
ROOT=serial.ROOT;OUT=serial.OUT

class Machine(serial.Serial):
 def _output(self,u,p,size,value,data):
  if getattr(self,'checking_break',False):
   assert p==self.port_base+3,(p,value)
   assert not u.reg_read(UC_X86_REG_EFLAGS)&512
  return super()._output(u,p,size,value,data)

def main():
 cases=[]
 def done(name,n):
  cases.append(dict(case=name,inputs=n,passed=True));print(name,n,flush=True)
 def invoke(m,name,flags=0x202):
  regs={UC_X86_REG_BX:0x1234,UC_X86_REG_SI:0x5678,UC_X86_REG_DI:0x9abc,
        UC_X86_REG_BP:0x7777,UC_X86_REG_ES:0x3333}
  for reg,value in regs.items():m.uc.reg_write(reg,value)
  m.checking_break=True
  try:result=m.call('_aspect_serial_break_'+name,eflags=flags)
  finally:m.checking_break=False
  assert bool(m.uc.reg_read(UC_X86_REG_EFLAGS)&512)==bool(flags&512)
  for reg,value in regs.items():assert m.uc.reg_read(reg)==value
  assert m.uc.reg_read(UC_X86_REG_DS)==m.ds==m.uc.reg_read(UC_X86_REG_SS)
  return result
 for flags in (2,0x202):
  m=Machine()
  for name,result in [('reserve',4),('assert',4),('release',0)]:
   assert invoke(m,name,flags)==result and not m.writes
 done('closed-no-port-write-callee-registers-DS-SS-IF',6)
 for lcr in range(0xc0,0x100):
  # Also test bit40 alone and bit80 alone below.
  m=Machine();m.registers[0x3fb]=lcr
  assert m.open()==8 and not m.writes and m.registers[0x3fb]==lcr
 for lcr in (0x43,0x83):
  m=Machine();m.registers[0x3fb]=lcr
  assert m.open()==8 and not m.writes
 done('foreign-BREAK-DLAB-lease-admission-before-first-write',66)
 for flags in (2,0x202):
  for lcr in range(256):
   m=Machine();assert m.open()==0
   m.registers[0x3fb]=lcr;before=len(m.writes)
   result=invoke(m,'reserve',flags)
   assert len(m.writes)==before
   if lcr&0xc0:
    assert result==8 and not m.get('serial_break_state') and not m.get('uart_break_hold')
    assert invoke(m,'release',flags)==0 and len(m.writes)==before
    assert m.registers[0x3fb]==lcr
   else:
    assert result==0 and m.get('serial_break_state')==m.get('uart_break_hold')==1
    assert invoke(m,'reserve',flags)==2
    assert invoke(m,'assert',flags)==0
    assert m.registers[0x3fb]==lcr|0x40 and m.get('serial_break_state')==2
    assert m.writes[before:]==[(0x3fb,lcr|0x40)]
    assert invoke(m,'assert',flags)==4
    # Simulate a framing/DLAB change: release must preserve every other bit.
    changed=lcr^0xa7;m.registers[0x3fb]=changed|0x40
    assert invoke(m,'release',flags)==0
    assert m.registers[0x3fb]==changed&~0x40
    assert not m.get('serial_break_state') and not m.get('uart_break_hold')
    after=len(m.writes);assert invoke(m,'release',flags)==0 and len(m.writes)==after
 done('all-LCR-values-admission-owned-assert-framing-preservation-idempotence-IF0and1',512)
 for flags in (2,0x202):
  for lsr in (0,0x20,0x40,0x60):
   m=Machine();assert m.open()==0;assert invoke(m,'reserve',flags)==0
   m.registers[0x3fd]=lsr;before=len(m.writes)
   assert invoke(m,'assert',flags)==(0 if lsr&0x40 else 7)
   assert m.writes[before:]==([(0x3fb,0x43)] if lsr&0x40 else [])
   assert invoke(m,'release',flags)==0
 done('TEMT-not-THRE-assertion-and-release-reservation-on-drain-cancel',8)
 for flags in (2,0x202):
  for phase in (1,2):
   for lcr in (0x43,0x83,0xc3):
    m=Machine();assert m.open()==0;assert invoke(m,'reserve',flags)==0
    if phase==2:assert invoke(m,'assert',flags)==0
    else:
     m.registers[0x3fb]=lcr;before=len(m.writes)
     assert invoke(m,'assert',flags)==8 and len(m.writes)==before
    before=len(m.writes);assert invoke(m,'release',flags)==0
    if phase==1:assert len(m.writes)==before and m.registers[0x3fb]==lcr
    else:assert m.registers[0x3fb]==3
 done('foreign-line-change-after-reserve-remains-untouched-on-cancel',12)
 for flags in (2,0x202):
  for phase in (1,2):
   for flow in (b'S',b'H',b'B'):
    m=Machine();assert m.open(b'/S1:0003:03:'+flow)==0
    m.call('_aspect_serial_poll');m.tx.clear()
    assert invoke(m,'reserve',flags)==0
    if phase==2:assert invoke(m,'assert',flags)==0
    before=list(m.tx);assert m.call('_aspect_serial_try_write',[65])==1
    m.receive_irq(b'R'*3073)
    assert m.get('uart_rx_count')==3073
    if flow!=b'H':assert m.get('uart_flow_pending',1)==0x13
    if flow==b'H':assert not m.registers[0x3fc]&2
    # Native combined flow gives software branch priority; no new RTS claim.
    assert m.call('_aspect_serial_poll')==0 and m.tx==before
    assert invoke(m,'release',flags)==0;m.call('_aspect_serial_poll')
    assert m.tx==before+([] if flow==b'H' else [0x13])
    assert bytes(m.call('_aspect_serial_read') for _ in range(3073))==b'R'*3073
    m.call('_aspect_serial_poll')
    if flow!=b'H':assert m.tx[-1]==0x11
    if flow==b'H':assert m.registers[0x3fc]&2
    assert m.call('_aspect_serial_try_write',[65])==0
    assert m.call('_aspect_serial_close')==0;m.restored()
 done('actual-ISR-RX-hardware-RTS-software-queued-XOFF-held-TX-until-release',12)
 for phase in (1,2):
  for fatal in (0,5):
   for close in ('_aspect_serial_close','_aspect_serial_backend_close'):
    m=Machine();assert m.open(b'/S1:0003:03:S')==0
    m.call('_aspect_serial_poll');assert invoke(m,'reserve')==0
    if phase==2:assert invoke(m,'assert')==0
    m.put('_aspect_serial_status',fatal);before=len(m.writes)
    assert m.call(close)==fatal;m.restored()
    assert not m.get('serial_break_state') and not m.get('uart_break_hold')
    writes=m.writes[before:]
    if phase==2:assert writes[0]==(0x3fb,3),writes
    assert invoke(m,'release')==0
 done('both-close-paths-release-before-flow-drain-and-restore-even-on-fatal-status',8)
 for error in (5,8):
  m=Machine();assert m.open()==0;m.put('_aspect_serial_status',error);before=len(m.writes)
  assert invoke(m,'reserve')==error and len(m.writes)==before
  m.put('_aspect_serial_status',0);assert invoke(m,'reserve')==0
  m.put('_aspect_serial_status',error);assert invoke(m,'assert')==error and len(m.writes)==before
  assert invoke(m,'release')==0 and not m.get('uart_break_hold')
 done('fatal-admission-and-assert-no-hardware-change-cleanup-reservation',2)
 result=dict(passed=True,groups=cases,inputs=sum(c['inputs'] for c in cases),
  binary_sha256=hashlib.sha256(serial.uart.BINARY.read_bytes()).hexdigest(),
  checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
  original_inputs=[],limitations=['UART/PIC/DOS modeled; actual linked DOS instructions execute.',
   'Low-level lease only: no calibrated duration, opcode dispatch, parent configuration or status UI claim.',
   'Concurrent changes modeled between calls; every owner port write checks IF=0 and LCR-only access.'])
 (OUT/'break-owner-checks.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
