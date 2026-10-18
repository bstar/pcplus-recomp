#!/usr/bin/env python3
"""Linked original matcher with bounded owned-byte source; no serial/clock mocking."""
import hashlib,json,random,struct
from pathlib import Path
from unicorn.x86_const import UC_X86_REG_EFLAGS,UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI,UC_X86_REG_BX,UC_X86_REG_DX,UC_X86_REG_CX
from dos_image import DosImage
ROOT=Path(__file__).resolve().parents[1];BINARY=ROOT/'build/modem-responses/MODEMRSP.EXE'
class Responses(DosImage):
 def __init__(self,slots):
  super().__init__(BINARY,BINARY.parent/'modem_responses.map');assert len(slots)==11
  self.slots=slots
  self.uc.mem_write(self.symbols['modem_response_slots'],b''.join(x+b'\0'*(16-len(x)) for x in slots));self.reset()
 def reset(self):
  result=self.call('modem_responses_reset_bounded');assert result==0 and not self.carry
 @property
 def carry(self):return bool(self.uc.reg_read(UC_X86_REG_EFLAGS)&1)
 def feed(self,ch):
  preserved=[(UC_X86_REG_BX,0x4242),(UC_X86_REG_CX,0x4343),(UC_X86_REG_DX,0x4444)]
  for r,w in preserved:self.uc.reg_write(r,w)
  result=self.call('modem_responses_feed_bounded',[ch]);assert not self.carry
  for r,w in [(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678)]+preserved:assert self.uc.reg_read(r)==w
  assert self.get('modem_response_available')==0
  return result
 def state(self):return bytes(self.uc.mem_read(self.symbols['modem_response_slots'],201))
 def cursors(self):
  base=self.offset('modem_response_slots');return [v-base-i*16 for i,v in enumerate(struct.unpack('<11H',self.uc.mem_read(self.symbols['modem_response_cursors'],22)))]
def model(slots,state,ch):
 for i,slot in enumerate(slots):
  pos=state[i]
  if pos==len(slot):continue
  if ch==slot[pos]:
   state[i]+=1
   if state[i]==len(slot):return i
  else:state[i]=int(bool(slot) and ch==slot[0])
 return 65535

def main():
 cases=[]
 def check(name,fn):n=fn();cases.append({'case':name,'inputs':n,'passed':True});print(name,'passed',n)
 def examples():
  inputs=[([b'OK']+[b'']*10,b'noise\r\nOKsuffix',0),([b'OK']+[b'']*10,b'ok',65535),([b'ABABAC']+[b'']*10,b'ABABABAC',65535),([b'LONGER',b'LONG']+[b'']*9,b'LONG',1),([b'']*4+[b'OK']+[b'']*3+[b'OK']+[b'']*2,b'OK',4),([b'']*11,b'\0OK\r\n',65535),([b'ABC']+[b'']*10,b'AB\0C',65535)]
  for slots,data,want in inputs:
   r=Responses(slots);got=65535
   for ch in data:
    got=r.feed(ch)
    if got!=65535:break
   assert got==want,(data,got,want)
  return len(inputs)
 check('case-sensitive-no-framing-short-prefix-tie-and-limited-fallback',examples)
 def random_streams():
  rng=random.Random(201);n=0
  for _ in range(100):
   slots=[bytes(rng.randrange(1,6) for _ in range(rng.randrange(16))) for _ in range(11)];state=[0]*11;r=Responses(slots)
   for __ in range(128):
    ch=rng.randrange(256) if __%3==0 else rng.randrange(1,6);want=model(slots,state,ch);got=r.feed(ch)
    assert got==want and r.cursors()==state,(slots,ch,want,got,state,r.cursors());n+=1
  return n
 check('all-eleven-slots-random-binary-streams-and-cursor-state',random_streams)
 def partial():
  r=Responses([b'CONNECT']+[b'']*10)
  for ch in b'CON':assert r.feed(ch)==65535
  assert r.cursors()[0]==3
  for ch in b'NEC':assert r.feed(ch)==65535
  assert r.feed(ord('T'))==0
  assert r.feed(ord('!'))==65535 # completed slot stays at terminator until reset
  r.reset();assert r.cursors()==[0]*11
  return 9
 check('partial-match-persistence-completed-slot-and-reset',partial)
 def rejected():
  for scenario,error in [('slot',1),('cursor',2),('byte',3)]:
   r=Responses([b'OK']+[b'']*10)
   if scenario=='slot':r.uc.mem_write(r.symbols['modem_response_slots']+160,b'X'*16)
   if scenario=='cursor':r.put('modem_response_cursors',65535)
   before=r.state();got=r.call('modem_responses_feed_bounded',[256 if scenario=='byte' else ord('O')]);assert r.carry and got==error and r.state()==before
  r=Responses([b'OK']+[b'']*10);r.uc.mem_write(r.symbols['modem_response_slots']+160,b'X'*16);before=r.state();assert r.call('modem_responses_reset_bounded')==1 and r.carry and r.state()==before
  return 4
 check('bounded-errors-preserve-all-matcher-state',rejected)
 def classify():
  count=0;r=Responses([b'']*11)
  for index in [65535]+list(range(11)):
   for baud in range(9):
    for auto in range(2):
     out=r.call('modem_response_classify',[index,baud,auto]);change=index<7 and auto and index!=baud
     assert not r.carry and out==(65535 if index==65535 else 1 if index<7 else 0)
     assert r.uc.reg_read(UC_X86_REG_DX)==(index if change else baud) and r.uc.reg_read(UC_X86_REG_BX)==bool(change);count+=1
  for args,error in [([11,0,0],1),([65534,0,0],1),([0,0,2],2),([0,9,0],3)]:assert r.call('modem_response_classify',args)==error and r.carry
  return count+4
 check('connect-failure-pending-and-autobaud-action-classification',classify)
 result={'passed':True,'binary_sha256':hashlib.sha256(BINARY.read_bytes()).hexdigest(),'cases':cases,'scope':'Actual source-only recovered138-byte matcher, maintained bounded one-byte source and action classifier. No live UART or timeout engine.'}
 (BINARY.parent/'cpu-results.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
