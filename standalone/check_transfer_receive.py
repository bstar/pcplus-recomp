#!/usr/bin/env python3
"""Linked exact receiver replay with synthetic explicit UART/time/UI boundaries."""
import argparse,binascii,hashlib,json,random,struct
from pathlib import Path
from dos_image import DosImage
from check_transfer_blocks import expected
from unicorn.x86_const import UC_X86_REG_AX,UC_X86_REG_SP,UC_X86_REG_IP,UC_X86_REG_BP,UC_X86_REG_DI
ROOT=Path(__file__).resolve().parents[1];BINARY=ROOT/'build/transfer-receive/RECEIVE.EXE'
class Receive(DosImage):
 def __init__(self):super().__init__(BINARY,BINARY.parent/'transfer_receive.map')
 def run(self,frame,crc=1,previous=0,protocol=4):
  self.uc.mem_write(self.symbols['receive_input'],frame)
  self.put('receive_protocol',protocol)
  result=self.call('_transfer_receive_probe',[self.offset('receive_input'),len(frame),crc,previous],limit=1000000)
  return {'result':result,'wire':bytes(self.uc.mem_read(self.symbols['receive_wire'],self.get('receive_wire_count'))).hex(),'accepted':self.get('receive_blocks_accepted'),'last':self.get('receive_last_block'),'used':self.get('receive_buffer_used'),'errors':self.get('receive_error_count'),'status':self.get('receive_status_code'),'payload':bytes(self.uc.mem_read(self.symbols['receive_payload'],max(self.get('receive_buffer_used'),128))).hex(),'cancel':self.get('receive_cancel_code'),'total':self.get('receive_total_low')+65536*self.get('receive_total_high')}
def cases():
 rng=random.Random(2101);result=[]
 for size in [128,1024]:
  for crc in [0,1]:
   for previous in [0,1,127,254,255,256,511,65535]:
    block=(previous+1)&255;data=bytes(rng.randrange(256) for _ in range(size));frame=expected(data,block,crc)
    result.append((f'valid-{size}-{crc}-{previous}',frame,crc,previous,4,0,b'\x06',data,0))
    result.append((f'duplicate-{size}-{crc}-{previous}',expected(data,previous&255,crc),crc,previous,4,1,b'\x06',None,0))
    result.append((f'sequence-{size}-{crc}-{previous}',expected(data,(previous+2)&255,crc),crc,previous,4,2,b'\x15',None,1))
    bad=bytearray(frame);bad[2]^=1;result.append((f'complement-{size}-{crc}-{previous}',bytes(bad),crc,previous,4,3,b'\x15',None,1))
    bad=bytearray(frame);bad[-1]^=1;result.append((f'trailer-{size}-{crc}-{previous}',bytes(bad),crc,previous,4,4,b'\x15',None,1))
    for cut in [3,17,len(frame)-3]:result.append((f'truncated-{size}-{crc}-{previous}-{cut}',frame[:cut],crc,previous,4,4 if cut>=size+2 else 5,b'\x15',None,1))
 # A timeout after the *last payload read* is stored as FF and counted as full.
 # Cover that historical quirk separately rather than equating it to early timeout.
 for crc in [0,1]:
  frame=expected(bytes(128),1,crc)
  result.append((f'missing-trailer-{crc}',frame[:-1],crc,0,4,4,b'\x15',None,1))
 result.append(('EOT-NAK-timeout-confirmation-ACK',b'\x04',1,0,4,6,b'\x15\x06',None,0))
 for protocol,crc in [(3,0),(5,1),(11,1)]:
  result.append((f'batch-block0-explicit-metadata-boundary-{protocol}',expected(bytes(128),0,crc),crc,0,protocol,10,b'',None,0))
 syn=bytearray(expected(bytes(128),1,1));syn[0]=0x16
 result.append(('SYN-128-byte-header',bytes(syn),1,0,4,0,b'\x06',bytes(128),0))
 result.append(('double-CAN-modeled-longjmp7-boundary',b'\x55\x18\x18',1,0,4,15,b'',None,0))
 result.append(('unknown-start-timeout-retry',b'\x55',1,0,4,14,b'\x15',None,1))
 return result

def main():
 p=argparse.ArgumentParser();p.add_argument('--original',type=Path);a=p.parse_args();groups=[];vectors=cases();observed=[]
 for name,frame,crc,previous,protocol,result,wire,data,errors in vectors:
  m=Receive();got=m.run(frame,crc,previous,protocol)
  assert got['result']==result,(name,got)
  assert got['wire']==wire.hex() and got['errors']==errors,(name,got)
  if data is not None:assert got['accepted']==1 and got['used']==len(data) and got['last']==((previous+1)&65535) and got['total']==len(data) and bytes.fromhex(got['payload'])==data,(name,got)
  else:assert got['accepted']==0 and got['used']==0 and got['last']==previous and got['total']==0,(name,got)
  observed.append(got)
 groups.append({'case':'actual-frame-payload-CRC-checksum-sequence-duplicate-complement-timeout-EOT','inputs':len(vectors),'passed':True})
 for pointer,count,crc,previous in [(0,1,1,0),(65535,2,1,0),(None,0,1,0),(None,1030,1,0),(None,1,2,0),(-1,1,1,0)]:
  m=Receive();pointer=m.offset('receive_input') if pointer is None else m.offset('receive_input')+1 if pointer==-1 else pointer;m.put('receive_wire_count',0xcccc);assert m.call('_transfer_receive_probe',[pointer,count,crc,previous])==8 and m.get('receive_wire_count')==0xcccc
 groups.append({'case':'bounded-fixture-invalid-input-no-UART-effect','inputs':6,'passed':True})
 if a.original:
  from check_directory_dial_original import Original,DATA,EXPECTED
  image=a.original.read_bytes();assert hashlib.sha256(image).hexdigest()==EXPECTED
  overlays=[x for x in json.loads((ROOT/'analysis/pcplus-overlays/manifest.json').read_text())['overlays'] if x['id']==21]
  class OriginalReceive(Original):
   def __init__(self,frame):super().__init__(image,overlays);self.remaining=bytearray(frame[1:]);self.wire=bytearray()
   def hook(self,u,at,size,_):
    if at in (0x1dc28,0x1dcfd,0x1d734,0x1db2a) or (at==0x1da31 and self.get(0xc000-14)) :u.emu_stop();return
    if at not in (0x15ca0,0x1aad9,0x1abca,0x1e498,0x1e322,0x16b72,0x1ab0b,0x19065):return
    sp=u.reg_read(UC_X86_REG_SP);ret,first=struct.unpack('<2H',u.mem_read(DATA+sp,4));cleanup=0
    if at in (0x15ca0,0x1aad9):
     u.reg_write(UC_X86_REG_AX,self.remaining.pop(0) if self.remaining else 65535);self.put(0x8e20,len(self.remaining));cleanup=2 if at==0x1aad9 else 0
    elif at==0x1abca:self.remaining.clear();self.put(0x8e20,0)
    elif at==0x1e498:self.put(0x6000,first)
    elif at==0x1ab0b:self.wire.append(first&255);cleanup=2
    elif at==0x16b72:cleanup=2
    elif at==0x19065:self.put(0x6002,struct.unpack('<H',u.mem_read(DATA+sp+4,2))[0])
    u.reg_write(UC_X86_REG_SP,sp+2+cleanup);u.reg_write(UC_X86_REG_IP,ret)
  for vector,want in zip(vectors,observed):
   name,frame,crc,previous,protocol,*_=vector;o=OriginalReceive(frame)
   o.uc.mem_write(DATA+0x39fc,image[153936+0x39fc:153936+0x3bfc]);o.uc.mem_write(DATA+0x5000,b'\xcc'*2048)
   for at,value in [(0x39c0,0x5000),(0xcd34,0),(0xcb5e,128),(0xcc9a,previous),(0x3996,protocol),(0xcdcc,0),(0xcd80,0),(0xcd8a,0),(0x8ffa,0),(0x8ffc,0),(0xcb2c,0),(0xcb2e,0),(0x6000,0),(0x6002,0),(0x8e20,len(frame)-1),(0xc000-2,65535),(0xc000-4,0),(0xc000-14,0),(0xc000-16,frame[0]),(0xc000-20,0)]:o.put(at,value)
   o.uc.reg_write(UC_X86_REG_SP,0xbf00);o.uc.reg_write(UC_X86_REG_BP,0xc000);o.uc.reg_write(UC_X86_REG_DI,crc)
   o.uc.emu_start(0x1dc6a,0x20000,count=1000000)
   assert o.uc.reg_read(UC_X86_REG_IP) in (0xdc28,0xdcfd,0xd734,0xdb2a,0xda31),(name,hex(o.uc.reg_read(UC_X86_REG_IP)))
   got={'wire':bytes(o.wire).hex(),'accepted':o.get(0xcd80),'last':o.get(0xcc9a),'used':o.get(0xcd34),'errors':o.get(0xcd8a),'status':o.get(0x6000),'payload':bytes(o.uc.mem_read(DATA+0x5000,max(o.get(0xcd34),128))).hex(),'cancel':o.get(0x6002),'total':o.get(0x8ffa)+65536*o.get(0x8ffc)}
   assert got=={key:value for key,value in want.items() if key!='result'},(name,got,want)
  groups.append({'case':'SHA-verified-original-receiver-instruction-replay-equality','inputs':len(vectors),'passed':True})
 result={'passed':True,'binary_sha256':hashlib.sha256(BINARY.read_bytes()).hexdigest(),'cases':groups,'scope':'Exact source receiver fragments and real CRC/ACK/NAK instructions, explicitly modeled memory UART/time/UI. Not a complete transfer, live peer or DOS file write.'};(BINARY.parent/'checks.json').write_text(json.dumps(result,indent=2)+'\n');print('Passed',sum(g['inputs'] for g in groups),'receiver cases')
if __name__=='__main__':main()
