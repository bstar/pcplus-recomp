#!/usr/bin/env python3
"""Execute the product's checked scalar BIOS inheritance and lease lifetime."""
import json,struct
from pathlib import Path
import check_aspect_render_client as client
class Policy(client.Client):
 def endpoint(self,values=(0,)):
  offset=self.call('_aspect_render_callback_offset')
  body=b''.join(b'\xb8\x08\0\xbb'+struct.pack('<H',value)+b'\x9a'+struct.pack('<HH',offset,self.base_segment) for value in values)
  wire=b'\x83\xf8\x07\x74\x03\x31\xc0\xcb'+body+b'\x31\xc0\xcb'
  self.uc.mem_write(0x61100,wire);self.uc.ctl_remove_cache(0x61100,0x61200)
def main():
 cases=[]
 for mode in (0,16):
  m=Policy();assert m.open()==0;m.endpoint((mode,));m.put('_runtime_keyboard_mode',mode^16)
  assert m.call('_aspect_render_keyboard_inherit')==0
  assert m.get('_runtime_keyboard_mode')==mode
  before=len(m.requests);m.endpoint((mode^16,))
  m.call('_runtime_when_file_reset')
  assert m.call('_aspect_render_keyboard_inherit')==0 and len(m.requests)==before
  assert m.get('_runtime_keyboard_mode')==mode
  m.call('_runtime_serial_reset')
  assert m.call('_aspect_render_keyboard_inherit')==0
  assert m.get('_runtime_keyboard_mode')==mode^16
  cases.append(dict(name='mode-%d-once-until-session-reset'%mode,passed=True))
 for values in ((),(0,0),(16,16),(1,),(17,),(65535,)):
  m=Policy();assert m.open()==0;m.endpoint(values);m.put('_runtime_keyboard_mode',16)
  assert m.call('_aspect_render_keyboard_inherit')==10
  if not values or values[0] not in (0,16):assert m.get('_runtime_keyboard_mode')==16
  cases.append(dict(name='bad-callback-'+str(values),passed=True))
 m=Policy();assert m.open()==0;m.put('_runtime_keyboard_mode',16)
 assert m.callback(8,0)==10 and m.get('_runtime_keyboard_mode')==16
 assert m.call('_aspect_serial_close')==0
 assert m.call('_aspect_render_keyboard_inherit')==14
 cases.append(dict(name='unsolicited-and-closed-lease',passed=True))
 for old in (1,2,3,4,5):
  m=Policy();m.words[-1]=old;m.publish()
  assert m.open()==1 and not m.writes and not m.get('_aspect_serial_active')
 cases.append(dict(name='capabilities-1-to-5-before-hardware',passed=True))
 report=dict(passed=True,cases=cases,runner_sha256=client.sha(client.q.BINARY),checker_sha256=client.sha(Path(__file__)),reused_checker_sha256=client.sha(Path(client.__file__)),scope='Actual child code and checked callback stacks with explicit synchronous parent endpoint. Modes0/16, once per invocation, retained file-reset selection, duplicate/missing/out-of-range/unsolicited/closed rejection, and old capabilities before UART. Actual terminal policy tested separately.')
 out=client.q.ROOT/'build/aspect-keyboard/policy-checks.json';out.write_text(json.dumps(report,indent=2)+'\n')
 print('ASPECT keyboard policy',len(cases),'cases PASS')
if __name__=='__main__':main()
