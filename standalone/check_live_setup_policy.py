#!/usr/bin/env python3
"""Explicit same-port candidate policy and acknowledged source-baud lifetime."""
import hashlib,json,struct
from check_live_setup_owner import Owner,ROOT,OUT,word
def finish(m,mask):
 m.uc.mem_write(m.data_base+m.destination,b'\xcc'*626);m.uc.mem_write(m.data_base+m.result,b'\xdd'*8)
 status=m.invoke('_live_setup_finish_policy',[m.destination,m.result,mask])
 if status:assert m.output()==b'\xcc'*626
 return status,struct.unpack('<4H',m.uc.mem_read(m.data_base+m.result,8))
def acknowledge(m,mask):return m.invoke('_live_setup_acknowledge',[mask])
def main():
 cases=[]
 def done(name,n):cases.append(dict(case=name,inputs=n,passed=True));print(name,n,flush=True)
 for allowed in range(0,32,2):
  m=Owner().ready()
  for at,value in [(2,8),(4,1),(6,2),(8,7),(0x198,1),(0x19a,0),(0x194,6)]:m.raw=word(m.raw,at,value)
  assert finish(m,allowed)==(0,(0,0,allowed,30^allowed))
  output=m.output();assert output[:2]==m.initial[:2] and output[16:18]==(b'\x06\0' if allowed&16 else m.initial[16:18]) and output[32:36]==m.initial[32:36]
  assert output[2:6]==(struct.pack('<HH',49664,1) if allowed&2 else m.initial[2:6])
  assert output[6:12]==(struct.pack('<HHH',1,7,2) if allowed&4 else m.initial[6:12])
  assert output[12:16]==(struct.pack('<HH',1,0) if allowed&8 else m.initial[12:16])
 done('every-permitted-serial-profile-combination-keeps-port-owned',16)
 m=Owner().ready()
 for at,value in [(0,1),(2,8),(4,1),(0x198,1),(0x194,6)]:m.raw=word(m.raw,at,value)
 assert finish(m,30)==(0,(0,0,0,31));assert m.output()[:42]==m.initial[:42]
 done('port-change-defers-all-dependent-serial-categories-together',1)
 m=Owner().ready();m.raw=word(m.raw,2,8);assert finish(m,14)==(0,(0,0,2,0));assert acknowledge(m,2)==0
 m.uc.mem_write(m.data_base+m.active,m.output());assert m.begin()==0;m.raw=word(m.raw,2,1)
 assert finish(m,14)==(0,(0,0,2,0)) and m.output()[2:6]==struct.pack('<HH',1200,0);assert acknowledge(m,2)==0
 active=word(m.output(),2,38400);m.uc.mem_write(m.data_base+m.active,active);assert m.begin()==0
 assert finish(m,14)==(0,(0,0,0,0)) and m.output()[2:6]==struct.pack('<HH',38400,0)
 assert acknowledge(m,0)==0 and acknowledge(m,2)==7
 done('acknowledged-rate-can-revert-and-subsequent-autobaud-remains-preserved',3)
 for allowed in [32,33,0x8000,65535]:
  m=Owner().ready();assert finish(m,allowed)[0]==1 and finish(m,14)[0]==0
 done('invalid-policy-rejects-before-pending-consumption',4)
 m=Owner().ready();m.raw=word(m.raw,2,8);assert finish(m,14)[0]==0
 assert acknowledge(m,1)==1 and acknowledge(m,0)==0 and acknowledge(m,2)==7
 assert m.begin()==0 and finish(m,14)==(0,(0,0,2,0))
 assert m.begin()==0 and acknowledge(m,2)==7 and finish(m,14)[0]==0 and acknowledge(m,2)==0
 done('decline-invalid-ack-and-superseded-offer-cannot-advance-rate-baseline',3)
 for allowed in range(1,32,2):
  m=Owner().ready()
  for at,value in [(0,1),(2,8),(4,1),(6,2),(8,7),(0x198,1),(0x19a,0),(0x194,6)]:m.raw=word(m.raw,at,value)
  assert finish(m,allowed)==(0,(0,0,allowed,31^allowed))
  assert m.output()[:2]==b'\x02\0' and m.output()[32:36]==struct.pack('<HH',0x2f8,3)
  assert m.output()[2:6]==(struct.pack('<HH',49664,1) if allowed&2 else m.initial[2:6])
 done('every-explicit-port-permission-combination-stages-corresponding-categories',16)
 for mask in [0,1,2,3]:
  m=Owner();m.uc.mem_write(m.data_base+m.active,word(m.initial,2,38400));assert m.bind()==0 and m.begin(mask)==0
  m.raw=word(m.raw,0,1);assert finish(m,31)==(0,(0,0,(1 if not mask&1 else 0)|(2 if not mask&2 and not mask&1 else 0),0))
  assert m.output()[2:6]==struct.pack('<HH',1200 if not mask&3 else 38400,0)
 done('new-port-uses-source-baud-while-CLI-port-or-baud-override-preserves-active-rate',4)
 result=dict(passed=True,binary_sha256=hashlib.sha256((OUT/'TERMINAL.EXE').read_bytes()).hexdigest(),inputs=sum(c['inputs'] for c in cases),cases=cases,scope='Actual far-C owner policy/acknowledgment APIs with independent byte/range oracles. Canonical/PRM reads modeled by Owner; native decoders/expansion and bridge code execute. Permission to stage a serial proposal is not UART application; foreground choice/hardware tests are separate.')
 (OUT/'live-setup-policy-checks.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
