#!/usr/bin/env python3
"""Measure a real DOS CPR query while the script-time window is open."""
import json,re,socket,struct,sys,time,types
from pathlib import Path
import test_aspect_keys_dos as keys
import test_aspect_script_window_dos as window
ROOT=keys.ROOT;BASE=ROOT/'build/aspect-window-query-dos'
ESC=b'\x1b';QUERY=ESC+b'[6n';REPLY=ESC+b'[1;22R'

def definitions():
 source='proc main\nwaitfor "LOGIN:" 5\nset duplex full\ntransmit "KEYREADY"\nwaitfor "END" 30\nif waitfor\ntransmit $D_PWORD\ntransmit "^M"\npause 1\nendif\nendproc\n'
 return [dict(name='window-query-4',source=source,profile=4,bios_policy='STANDARD',custom=False,success=True,
  banner=ESC+b'[2J'+ESC+b'[HFIRST BYTE SAFE'+QUERY+ESC+b'[0cLOGIN:',
  keys='p1800 k e y s p200 a-z p5500 escape p300 d o n e p2500 space p700 r e a d y p700 a-x',
  key_wire=b'keys'+REPLY+b'done',post=QUERY,post_reply=ESC+b'[1;25R',extra_reply=REPLY,
  screen=[(0,0,'FIRST BYTE SAFE'),(0,21,'END')])]

class TracedSocket:
 def __init__(self,wrapped,events):self.wrapped=wrapped;self.events=events
 def __getattr__(self,name):return getattr(self.wrapped,name)
 def __enter__(self):self.wrapped.__enter__();return self
 def __exit__(self,*args):return self.wrapped.__exit__(*args)
 def accept(self):
  conn,address=self.wrapped.accept();return TracedSocket(conn,self.events),address
 def sendall(self,data):
  self.events.append(dict(kind='send',time=time.monotonic(),hex=data.hex()));return self.wrapped.sendall(data)
 def recv(self,*args):
  data=self.wrapped.recv(*args);self.events.append(dict(kind='receive',time=time.monotonic(),hex=data.hex()));return data

def main():
 original=keys.adapter;renderer=keys.renderer;original_observer=renderer.observer;events=[]
 def adapter():
  module=original();run=module.run
  module.socket=types.SimpleNamespace(socket=lambda:TracedSocket(socket.socket(),events),timeout=socket.timeout)
  def staged(*args,**kwargs):kwargs['online_updates']=[(3.0,QUERY)];return run(*args,**kwargs)
  module.run=staged;return module
 keys.OUT=BASE;keys.definitions=definitions;keys.adapter=adapter
 renderer.observer=window.make_observer(original_observer,window.symbols(ROOT/'build/terminal/terminal.map'),window.symbols(ROOT/'build/aspect-runner/ASPECT.map'),render_progress=True)
 keys.main();folder=BASE/sys.argv[sys.argv.index('--label')+1]
 (folder/'peer-events.json').write_text(json.dumps(events,indent=2)+'\n')
 report=json.loads((folder/'checks.json').read_text());case=report['cases'][0]
 assert report['passed'] and case['passed']
 raw=(folder/case['case']/'RENDER.BIN').read_bytes();first_render_tick,render_advanced,*observation=struct.unpack('<7H',raw[-14:])
 sends=[row for row in events if row['kind']=='send' and row['hex']==QUERY.hex()];assert len(sends)==2
 query=sends[0];received=bytearray();reply=None
 for event in events:
  if event['kind']=='receive' and event['time']>=query['time']:
   received.extend(bytes.fromhex(event['hex']))
   if REPLY in received:reply=event;break
 assert reply is not None
 delay=reply['time']-query['time'];checks=dict(DOS_functional_checks=report['passed'],window_observed=observation[0]==1,
  window_stays_open_beyond_deadline=observation[2]>72,live_render_advances_while_window_open=render_advanced==1,reply_matches_logical_BBS_cursor=REPLY in received,
  peer_complete_reply_within_one_second=delay<=1.0)
 result=dict(passed=all(checks.values()),checks=checks,reply_delay_seconds=delay,window_observation=observation,first_render_tick=first_render_tick,render_advanced=render_advanced,
  parent_sha256=report['terminal_sha256'],runner_sha256=report['runner_sha256'],
  captures_sha256={str(p.relative_to(folder)):renderer.sha(p) for p in folder.rglob('*') if p.is_file()},
  checker_sha256=renderer.sha(Path(__file__)),
  scope='Actual DOS parent/ASPECT/cooperative window and emulated UART. Passive timer witnesses render-start advancement while the window remains visible. Owned socket peer sends CPR three seconds after connect while the window is open; complete reply timing is measured at that same peer. This is a declared one-second compatibility deadline, not a claim about every BBS timeout or physical modem.')
 (folder/'query-checks.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(dict(passed=result['passed'],checks=checks,reply_delay_seconds=delay,window_observation=observation)))
 return 0 if result['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
