#!/usr/bin/env python3
"""Run actual child key RPC lifecycle against a declared scalar parent endpoint."""
import json,struct
from pathlib import Path
import check_aspect_render_client as client
class Key(client.Client):
 def endpoint(self,reads=1,result=0,callback_value=0,polls=0,poll_value=0,window_state=None):
  off=self.call('_aspect_render_callback_offset')
  call=b'\xb8\x09\0\xbb'+struct.pack('<H',callback_value)+b'\x9a'+struct.pack('<HH',off,self.base_segment)+b'\x2e\xa3\x00\x02'
  poll=b'\xb8\x0a\0\xbb'+struct.pack('<H',poll_value)+b'\x9a'+struct.pack('<HH',off,self.base_segment)+b'\x2e\xa3\x02\x02'
  state=b'' if window_state is None else b'\xb8\x0b\0\xbb'+struct.pack('<H',window_state)+b'\x9a'+struct.pack('<HH',off,self.base_segment)
  wire=b'\x83\xf8\x08\x74\x03\x31\xc0\xcb'+call*reads+poll*polls+state+b'\xb8'+struct.pack('<H',result)+b'\xcb'
  self.uc.mem_write(0x61100,wire);self.uc.ctl_remove_cache(0x61100,0x61200)
 def duplex(self):return int.from_bytes(self.uc.mem_read(0x61200,2),'little')
def main():
 cases=[]
 for changed,value,wanted in [(0,1,65535),(1,0,0),(1,1,1),(1,255,255)]:
  m=Key();assert m.open()==0;m.endpoint();m.put('_runtime_set_duplex_changed',changed);m.put('_runtime_serial_local_echo',value)
  for key in (ord('a'),0x0e08,0x48e0,0x8500,0x8a00):
   assert m.call('_aspect_render_key',[key])==0 and m.requests[-1]==(8,key)
   assert m.duplex()==wanted
  cases.append(dict(name='duplex-%d-%d'%(changed,value),passed=True))
 for reads,value in [(0,0),(2,0),(1,1)]:
  m=Key();assert m.open()==0;m.endpoint(reads=reads,callback_value=value)
  assert m.call('_aspect_render_key',[ord('a')])==10
  m.endpoint();assert m.call('_aspect_render_key',[ord('b')])==0
  cases.append(dict(name='invalid-policy-%d-%d'%(reads,value),passed=True))
 for result in (3,7,13,14,65534):
  m=Key();assert m.open()==0;m.endpoint(reads=0,result=result)
  assert m.call('_aspect_render_key',[ord('a')])==(result if result<=14 else 10)
  cases.append(dict(name='parent-error-'+str(result),passed=True))
 m=Key();assert m.open()==0;m.put('_runtime_set_duplex_changed',1);m.put('_runtime_serial_local_echo',1)
 assert m.callback(9,0)==65535 and m.get('_runtime_serial_local_echo')==1
 assert m.call('_aspect_serial_close')==0
 assert m.call('_aspect_render_key',[ord('a')])==14
 cases.append(dict(name='unsolicited-and-closed-key-request',passed=True))
 m=Key();assert m.open()==0;m.endpoint(polls=3,window_state=1)
 m.put('uart_rx_count',3);m.put('uart_software_flow',1);m.put('uart_flow_pending',0x13,1)
 before=len(m.tx)
 assert m.call('_aspect_render_key',[0x2c00])==0
 assert m.get('uart_rx_count')==3 and m.tx[before:]==[0x13] and not m.get('uart_flow_pending',1)
 cases.append(dict(name='window-poll-services-XOFF-without-dequeue',passed=True))
 for reads,value in [(0,0),(1,1)]:
  m=Key();assert m.open()==0;m.endpoint(reads=reads,polls=1,poll_value=value)
  assert m.call('_aspect_render_key',[0x2c00])==10
  cases.append(dict(name='reject-window-poll-order-value-%d-%d'%(reads,value),passed=True))
 m=Key();assert m.open()==0
 assert m.callback(10,0)==10 and not m.get('uart_rx_count')
 cases.append(dict(name='reject-unsolicited-window-poll',passed=True))
 for version in (1,2,3,4,5,6,7,8,9):
  m=Key();m.words[-1]=version;m.publish();assert m.open()==1 and not m.writes
 cases.append(dict(name='old-capabilities-before-hardware',passed=True))
 # WINDOW_STATE is legal exactly once, during Alt-Z after duplex projection,
 # or during a dedicated WINDOW_SERVICE. It is not a general writable flag.
 for state in (0,1):
  m=Key();assert m.open()==0;m.endpoint(window_state=state)
  assert m.call('_aspect_render_key',[0x2c00])==0
  assert m.call('_aspect_render_window_active')==state
  assert m.callback(11,1)==10
  cases.append(dict(name='Alt-Z-owned-state-'+str(state),passed=True))
 for key,state in [(ord('a'),1),(0x2c00,2)]:
  m=Key();assert m.open()==0;m.endpoint(window_state=state)
  assert m.call('_aspect_render_key',[key])==10
  cases.append(dict(name='reject-unexpected-window-state-%d-%d'%(key,state),passed=True))
 for count,state,wanted in [(0,0,10),(1,0,0),(1,1,0),(2,1,10),(1,2,10)]:
  m=Key();assert m.open()==0
  off=m.call('_aspect_render_callback_offset')
  callback=b'\xb8\x0b\0\xbb'+struct.pack('<H',state)+b'\x9a'+struct.pack('<HH',off,m.base_segment)
  m.uc.mem_write(0x61100,callback*count+b'\x31\xc0\xcb');m.uc.ctl_remove_cache(0x61100,0x61200)
  assert m.call('_aspect_render_window_service')==wanted
  assert m.requests[-1]==(11,1)
  cases.append(dict(name='window-service-state-%d-%d'%(count,state),passed=True))
 m=Key();assert m.open()==0;m.endpoint(window_state=1)
 assert m.call('_aspect_render_key',[0x2c00])==0
 assert m.call('_aspect_serial_close')==0 and m.call('_aspect_render_window_service')==14
 assert m.call('_aspect_render_finish')==0 and m.call('_aspect_render_window_active')==0
 cases.append(dict(name='window-closed-UART-and-END-retirement',passed=True))
 report=dict(passed=True,cases=cases,runner_sha256=client.sha(client.q.BINARY),checker_sha256=client.sha(Path(__file__)),reused_checker_sha256=client.sha(Path(client.__file__)),original_inputs=[],scope='Actual child key request/callback code and guarded stacks; explicit scalar parent boundary. Exact16bit key, inherited/changed duplex, one callback per request, missing/duplicate/nonzero selector, typed errors, retry cleanup, unsolicited/closed/old capability rejection. Actual parent profile/UART/echo tested separately.')
 (client.q.ROOT/'build/aspect-keyboard/key-client-checks.json').write_text(json.dumps(report,indent=2)+'\n');print('ASPECT key client',len(cases),'cases PASS')
if __name__=='__main__':main()
