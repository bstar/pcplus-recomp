#!/usr/bin/env python3
"""Actual child label lifetime and callback code; declared parent scalar endpoint."""
import json,struct
from pathlib import Path
import check_aspect_render_client as client
class Label(client.Client):
 def endpoint(self,indices):
  callback=self.call('_aspect_render_callback_offset');body=b''
  for index in indices:
   body+=b'\xb8\x07\0\xbb'+struct.pack('<H',index)+b'\x9a'+struct.pack('<HH',callback,self.base_segment)
  wire=b'\x83\xf8\x06\x74\x03\x31\xc0\xcb'+body+b'\x31\xc0\xcb'
  self.uc.mem_write(0x61100,wire);self.uc.ctl_remove_cache(0x61100,0x61900)
 def publish_label(self,path,duplex=65535):
  self.uc.mem_write(self.data_base+0xb080,path+b'\0')
  return self.call('_aspect_render_script_label',[0xb080,duplex])
def main():
 cases=[]
 for path in [b'A.ASX',b'12345678.ASX',b'C:\\BBS.V2\\NEXT.ASX',b'C:NEXT.ASX',b'\x82.ASX']:
  leaf=path.replace(b':',b'\\').split(b'\\')[-1]
  for duplex in [0,1,255,65535]:
   m=Label();assert m.open()==0;m.endpoint(range(len(leaf)+1));m.requests.clear()
   assert m.publish_label(path,duplex)==0
   assert m.requests==[(6,duplex)]
   assert m.callback(7,0)==65535
   cases.append(dict(name=path.hex()+':duplex'+str(duplex),passed=True))
 for indices in [[],[0],[1],[0,0],list(range(6))+[6],list(range(13))]:
  m=Label();assert m.open()==0;m.endpoint(indices)
  # A.ASX has six bytes including its terminator; extra pulls are refused.
  assert m.publish_label(b'A.ASX')==10,indices
  cases.append(dict(name='incomplete-or-invalid-pull-'+str(indices),passed=True))
 for path in [b'',b'.ASX',b'LONGSTEM9.ASX',b'A.ASP',b'A.asx',b'A..ASX',b'BAD/FILE.ASX',b'A\x01.ASX',b'A\x7f.ASX',b'X'*82]:
  m=Label();assert m.open()==0;m.requests.clear()
  assert m.publish_label(path)==7 and not m.requests,path
  cases.append(dict(name='reject-'+path.hex(),passed=True))
 m=Label();assert m.open()==0;m.requests.clear()
 assert m.publish_label(b'A.ASX',256)==7 and not m.requests
 assert m.call('_aspect_serial_close')==0
 assert m.publish_label(b'A.ASX')==14
 assert m.call('_aspect_render_finish')==0
 assert m.publish_label(b'A.ASX')==10
 cases.append(dict(name='duplex-and-lease-admission',passed=True))
 report=dict(passed=True,cases=cases,binary_sha256=client.sha(client.q.BINARY),checker_sha256=client.sha(Path(__file__)),scope='Actual child label API/sequential synchronous callback and near DS=SS stack lifetime, explicit scalar parent endpoint. Parent validation/drawing and DOS chaining separately proved.')
 (client.q.ROOT/'build/aspect-runner/script-label-client-checks.json').write_text(json.dumps(report,indent=2)+'\n')
 print('Script label client',len(cases),'cases PASS')
if __name__=='__main__':main()
