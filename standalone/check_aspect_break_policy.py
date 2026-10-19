#!/usr/bin/env python3
"""Actual child policy callback/stack code; explicit synchronous parent boundary."""
import json,struct
from pathlib import Path
from unicorn.x86_const import *
import check_aspect_render_client as client

class Policy(client.Client):
 def endpoint(self,value=350,duplicate=False,missing=False):
  callback=self.call('_aspect_render_callback_offset')
  call=b'\xb8\x06\0\xbb'+struct.pack('<H',value)+b'\x9a'+struct.pack('<HH',callback,self.base_segment)
  body=b'\x31\xc0' if missing else call+(call if duplicate else b'')
  # BEGIN/END/EMIT success model; POLICY invokes the actual checked child.
  wire=b'\x83\xf8\x04\x74\x03\x31\xc0\xcb'+body+b'\xcb'
  self.uc.mem_write(0x61100,wire);self.uc.ctl_remove_cache(0x61100,0x61200)

def main():
 cases=[]
 for value in (0,1,350,32767,32768,65535):
  m=Policy();assert m.open()==0;m.endpoint(value)
  m.call('_runtime_serial_reset');assert m.get('_runtime_serial_break_units')==350
  assert m.call('_aspect_render_policy_inherit')==0 and m.get('_runtime_serial_break_units')==value
  before=len(m.requests);m.endpoint(value^0xffff)
  assert m.call('_aspect_render_policy_inherit')==0 and len(m.requests)==before
  assert m.get('_runtime_serial_break_units')==value
  m.call('_runtime_serial_reset');assert m.call('_aspect_render_policy_inherit')==0
  assert m.get('_runtime_serial_break_units')==value^0xffff
  assert m.uc.reg_read(UC_X86_REG_DS)==m.ds==m.uc.reg_read(UC_X86_REG_SS)
  cases.append(dict(name='raw-word-%d-once-per-reset'%value,passed=True))
 for duplicate,missing in [(True,False),(False,True)]:
  m=Policy();assert m.open()==0;m.endpoint(350,duplicate,missing)
  assert m.call('_aspect_render_policy_inherit')==10
  cases.append(dict(name='duplicate' if duplicate else 'missing',passed=True))
 m=Policy();assert m.open()==0;m.put('_runtime_serial_break_units',1234)
 assert m.callback(6,999)==10 and m.get('_runtime_serial_break_units')==1234
 assert m.call('_aspect_serial_close')==0
 assert m.call('_aspect_render_policy_inherit')==14
 assert m.call('_aspect_render_break_notice',[0])==14
 cases.append(dict(name='unsolicited-value-and-closed-lease-rejected',passed=True))
 for old in (1,2,3,4):
  m=Policy();m.words[-1]=old;m.publish();assert m.open()==1 and not m.writes
 cases.append(dict(name='old-capabilities-before-hardware',passed=True))
 m=Policy();assert m.open()==0;m.requests.clear()
 assert m.call('_aspect_render_break_notice',[2])==7 and not m.requests
 assert m.call('_aspect_render_break_notice',[0])==0 and m.requests[-1]==(5,0)
 assert m.call('_aspect_render_break_notice',[1])==0 and m.requests[-1]==(5,1)
 cases.append(dict(name='notice-scalar-validation',passed=True))
 report=dict(passed=True,cases=cases,binary_sha256=client.sha(client.q.BINARY),
  checker_sha256=client.sha(Path(__file__)),scope='Actual child policy lifetime, checked callback and IF/DS=SS stack paths with explicit parent scalar endpoint; no parent engine or DOS scheduling claim.')
 (client.q.ROOT/'build/aspect-runner/break-policy-checks.json').write_text(json.dumps(report,indent=2)+'\n')
 print('BREAK policy',len(cases),'cases PASS')
if __name__=='__main__':main()
