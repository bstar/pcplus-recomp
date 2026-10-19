#!/usr/bin/env python3
"""Execute the production child carrier API/native UART helper, modeling only
DOS/BIOS/UART boundaries. An MSR IN clears delta bits0..3 in this model; it is
not a pure DCD read. No binary or product source is rebuilt or modified."""
import hashlib,json
from pathlib import Path
from unicorn.x86_const import *
from check_aspect_render_client import Client,q
ROOT=q.ROOT;OUT=ROOT/'build/aspect-when-carrier'
class Carrier(Client):
 def __init__(self):
  super().__init__();self.port_base=0x3f8;self.msr=0x90;self.msr_reads=[];self.native_calls=0
  self.vectors[11]=(0x4321,0xf000)
 def _code(self,u,a,s,d):
  if a==self.symbols['uart_carrier_detect']:self.native_calls+=1
  return super()._code(u,a,s,d)
 def _input(self,u,p,s,d):
  if p==self.port_base+6:
   value=self.msr;self.msr_reads.append((p,value));self.msr&=0xf0
   return value
  mapped=0x3f8+p-self.port_base if self.port_base<=p<self.port_base+8 else p
  return super()._input(u,mapped,s,d)
 def _output(self,u,p,s,v,d):
  mapped=0x3f8+p-self.port_base if self.port_base<=p<self.port_base+8 else p
  return super()._output(u,mapped,s,v,d)
 def open_port(self,port):
  self.port_base=[0x3f8,0x2f8,0x3e8,0x2e8][port-1]
  self.uc.mem_write(self.data_base+0xb000,('/S%d:0003:03:N'%port).encode()+b'\0')
  return self.call('_aspect_serial_open',[0xb000])
 def probe(self,flags):
  kept={'bx':0x1357,'si':0x2468,'di':0x3579,'bp':0x468a,'es':0x579b}
  answer=self.call('_aspect_serial_carrier',eflags=flags,**kept)
  for name,value in kept.items():assert self.uc.reg_read(globals()['UC_X86_REG_'+name.upper()])==value,name
  assert self.uc.reg_read(UC_X86_REG_DS)==self.ds==self.uc.reg_read(UC_X86_REG_SS)
  assert self.uc.reg_read(UC_X86_REG_EFLAGS)&0x600==flags&0x600
  return answer

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
 digest=sha(q.BINARY);cases=[]
 def done(name,inputs):cases.append(dict(case=name,inputs=inputs,passed=True));print(name,inputs,flush=True)
 m=Carrier()
 for flags in [0x2,0x202,0x402,0x602]:
  before=(len(m.msr_reads),len(m.writes),m.native_calls,dict(m.polls));m.msr=0xff
  assert m.probe(flags)==0xffff
  assert (len(m.msr_reads),len(m.writes),m.native_calls,dict(m.polls))==before and m.msr==0xff
 done('inactive-FFFF-no-port-IO-no-native-read-preserves-callee-ABI-IF-DF',4)
 for port in range(1,5):
  m=Carrier();assert m.open_port(port)==0
  assert m.get('uart_port_msr')==m.port_base+6
  baseline=m.native_calls
  for value in range(256):
   m.msr=value;reads=len(m.msr_reads);writes=len(m.writes)
   assert m.probe(0x602 if value&1 else 0x2)==value&0x80
   assert m.msr_reads[reads:]==[(m.port_base+6,value)]
   assert m.msr==value&0xf0 and len(m.writes)==writes
  assert m.native_calls==baseline+256
 done('all-256-MSR-bytes-all-four-standard-ports-native-bit7-only-delta-clear-callee-ABI',1024)
 m=Carrier();assert m.open_port(1)==0
 for high in [False,True]:
  for other in [0,0x10,0x20,0x40,0x70]:
   m.msr=(0x80 if high else 0)|other|0x0f
   assert m.probe(0x202)==(0x80 if high else 0)
   assert m.msr==((0x80 if high else 0)|other)
   assert m.probe(0x202)==(0x80 if high else 0)
 done('consecutive-MSR-reads-consume-deltas-without-changing-CTS-DSR-RI-or-DCD',20)
 m=Carrier();assert m.open_port(1)==0;assert m.call('_aspect_serial_close')==0
 before=(len(m.msr_reads),len(m.writes),m.native_calls,dict(m.polls));m.msr=0x8f
 assert m.probe(0x202)==0xffff
 assert (len(m.msr_reads),len(m.writes),m.native_calls,dict(m.polls))==before and m.msr==0x8f
 done('resolved-close-retires-carrier-IO-with-no-device-read-or-reopen',1)
 aliases=[['aspect_dispatch_paused','uart_rx_count','aspect_serial_rx_count','_aspect_serial_rx_count'],
          ['aspect_when_active_count','aspect_receive_policy_pattern_count','_runtime_receive_pattern_count','aspect_dispatch_seek_enabled'],
          ['aspect_flow_wait_gate','_runtime_wait_gate','aspect_receive_suppress_echo','_runtime_receive_suppress_echo','aspect_dispatch_wait_disabled']]
 addresses={}
 for group in aliases:
  actual=[m.symbols[name] for name in group];assert len(set(actual))==1,(group,actual)
  addresses.update({name:hex(m.symbols[name]) for name in group})
  for value in [0,1,3,0xffff]:
   m.put(group[0],value);assert all(m.get(name)==value for name in group)
 done('production-map-8E20-E2F8-E382-physical-word-aliases-observe-identical-writes',12)
 report=dict(passed=True,binary_sha256=digest,manifest_sha256=sha(ROOT/'build/aspect-runner/manifest.json'),checker_sha256=sha(Path(__file__)),harness_sources={p:sha(ROOT/p) for p in ['standalone/check_aspect_render_client.py','standalone/check_uart.py']},original_inputs=[],cases=cases,inputs=sum(c['inputs'] for c in cases),alias_addresses=addresses,limitations=['Actual linked API, native carrier instructions, real open/close owner and register ABI execute; DOS/BIOS/UART state is modeled.','MSR model explicitly clears hardware delta bits0..3 on each IN; modem control input bits4..7 remain unchanged. Reading MSR has this observable side effect.','Standard COM1..4 and IRQ3/4 mappings modeled; no physical modem/DCD timing, transient-edge retention or real hardware proof.'])
 assert sha(q.BINARY)==digest
 OUT.mkdir(parents=True,exist_ok=True);(OUT/'checks.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
