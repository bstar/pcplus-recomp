#!/usr/bin/env python3
"""Run actual linked calibrated child BREAK service; model BIOS/UART inputs.
No function bodies are skipped. This does not test opcode dispatch/status UI.
"""
import json,struct
from pathlib import Path
from unicorn.x86_const import *
import check_aspect_txpace_linked as pacing

class Break(pacing.Pacing):
 def __init__(self):
  self.pulse_units=0;self.cancel_at=None;self.overflow_at=None;self.foreign=None
  self.freeze_ticks=False;self.lcr_writes=[];self.temt_at=None;self.assert_calls=0
  super().__init__()
 def _code(self,u,a,s,d):
  if a==self.symbols['_aspect_txpace_native_one'] and self.get('serial_break_state')==2:
   self.pulse_units+=1
  if self.cancel_at is not None and self.get('serial_break_state') and self.pulse_units>=self.cancel_at:
   self.cancel_now=True
  if self.overflow_at is not None and self.get('serial_break_state')==2 and self.pulse_units>=self.overflow_at:
   self.put('uart_rx_dropped',1)
  if a==self.symbols['_aspect_serial_break_assert']:
   self.assert_calls+=1
   if self.foreign is not None:self.registers[0x3fb]=self.foreign
   if self.temt_at is not None and self.assert_calls>=self.temt_at:self.registers[0x3fd]=0x60
  super()._code(u,a,s,d)
  if a==self.symbols['_aspect_serial_ticks'] and self.freeze_ticks:u.mem_write(0x46c,struct.pack('<I',0))
 def _output(self,u,p,s,v,d):
  if p==0x3fb and hasattr(self,'symbols') and 'serial_break_state' in self.symbols:
   self.lcr_writes.append((v,self.get('serial_break_state'),bool(u.reg_read(UC_X86_REG_EFLAGS)&512)))
  return super()._output(u,p,s,v,d)
 def prepared(self):
  assert self.open()==0
  assert self.call('_runtime_serial_prepare_pacing',limit=500000)==0
  # Explicit fast calibration input for exhaustive16-bit unit-count tests.
  # The normal74-count calibrated path is separately exercised below.
  self.put('_aspect_txpace_count',1)
  self.writes.clear();self.lcr_writes.clear()
 def check(self,units,result=0,limit=500000):
  assert self.call('_runtime_serial_break',[units],limit=limit)==result
  assert self.get('_runtime_error')==result
  assert not self.get('serial_break_state') and not self.get('uart_break_hold')
  assert self.uc.reg_read(UC_X86_REG_DS)==self.ds==self.uc.reg_read(UC_X86_REG_SS)
  assert self.uc.reg_read(UC_X86_REG_EFLAGS)&512

def main():
 cases=[]
 def done(name,m):
  cases.append(dict(name=name,passed=True,pulse_units=m.pulse_units,
   serial_error=m.get('_runtime_serial_error'),pacing_error=m.get('_runtime_serial_pacing_error')))
  print(name,'PASS',flush=True)
 for units in (0,1,350,999,1000,32767,32768,65535):
  m=Break();m.prepared();m.check(units,limit=12000000)
  assert m.pulse_units==units
  assert m.lcr_writes==[(0x43,2,False),(3,2,False)]
  assert all(p==0x3fb for p,v in m.writes)
  assert m.registers[0x3fb]==3 and not m.tx
  done('full-word-calibrated-units-%d'%units,m)
 m=Break();assert m.open()==0;m.writes.clear();m.lcr_writes.clear()
 m.check(350,limit=2000000)
 assert m.get('_aspect_txpace_count')==74 and m.units==358 and m.pulse_units==350
 assert m.lcr_writes==[(0x43,2,False),(3,2,False)]
 done('actual-calibration-before-350-unit-pulse',m)
 for when in (0,1,999,1000):
  m=Break();m.prepared();m.cancel_at=when;m.check(2000,13,limit=1000000)
  assert m.pulse_units==when and m.registers[0x3fb]==3
  assert m.get('_runtime_serial_pacing_error')==(0 if not when else 6)
  done('cancel-at-unit-%d'%when,m)
 for when in (1,999,1000):
  m=Break();m.prepared();m.overflow_at=when;m.check(2000,14,limit=1000000)
  assert m.pulse_units==when and m.get('_runtime_serial_error')==5
  assert m.registers[0x3fb]==3
  done('overflow-at-unit-%d'%when,m)
 for initial in (0,1573035):
  m=Break();m.prepared();m.tick=initial;m.registers[0x3fd]=0x20
  m.check(350,14)
  assert m.get('_runtime_serial_error')==7 and not m.pulse_units and not m.lcr_writes
  assert m.tick-initial<=21
  done('TEMT-drain-timeout-start-%d'%initial,m)
 m=Break();m.prepared();m.registers[0x3fd]=0x20;m.temt_at=5;m.check(1)
 assert m.assert_calls==5 and m.pulse_units==1
 done('TEMT-drain-eventually-ready',m)
 m=Break();m.prepared();m.freeze_ticks=True;m.registers[0x3fd]=0x20
 m.check(1,14,limit=20000000)
 assert m.assert_calls==65535 and m.get('_runtime_serial_error')==7 and not m.lcr_writes
 done('stopped-BIOS-clock-finite-independent-drain-bound',m)
 for lcr in (0x43,0x83):
  m=Break();assert m.open()==0;m.registers[0x3fb]=lcr
  m.put('uart_software_flow',1);m.put('uart_flow_pending',0x11,1)
  before=list(m.writes);m.check(350,14)
  assert m.writes==before and not m.tx and not m.units
  done('foreign-before-calibration-no-flow-TX-%02x'%lcr,m)
 for lcr in (0x43,0x83,0xc3):
  m=Break();m.prepared();m.registers[0x3fb]=lcr;m.check(1,14)
  assert m.get('_runtime_serial_error')==8 and m.registers[0x3fb]==lcr and not m.lcr_writes
  done('foreign-before-reserve-%02x'%lcr,m)
  m=Break();m.prepared();m.foreign=lcr;m.check(1,14)
  assert m.get('_runtime_serial_error')==8 and m.registers[0x3fb]==lcr and not m.lcr_writes
  done('foreign-after-reserve-%02x'%lcr,m)
 for units in (0,350):
  m=Break();assert m.open()==0;before=list(m.writes)
  assert m.call('_runtime_serial_break',[units],eflags=2)==14
  assert m.get('_runtime_serial_pacing_error')==3 and m.writes==before
  assert not m.get('serial_break_state') and not m.get('uart_break_hold')
  assert not m.uc.reg_read(UC_X86_REG_EFLAGS)&512
  done('IF0-admission-%d'%units,m)
 m=Break();assert m.call('_runtime_serial_break',[350])==3 and not m.writes
 done('no-owned-UART-rejected',m)
 report=dict(passed=True,binary_sha256=pacing.render.sha(pacing.render.q.BINARY),
  checker_sha256=pacing.render.sha(Path(__file__)),cases=cases,
  scope='Actual linked child transport, native6B72 busyloop, IRQ-live calibration, TEMT drain, cancellation, overflow and owned LCR cleanup. BIOS/UART/tick inputs modeled. Full-word count tests use explicit calibrated word1 after real preparation; separate350-unit test uses actual measured74. No opcode/UI/parent inheritance or physical pulse timing claim.')
 out=pacing.ROOT/'build/aspect-runner/break-linked-checks.json';out.write_text(json.dumps(report,indent=2)+'\n')
 print('Linked BREAK:',len(cases),'cases PASS')
if __name__=='__main__':main()
