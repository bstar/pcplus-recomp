#!/usr/bin/env python3
"""Linked8086 CRC/framing with independent checksum oracle; optional original."""
import argparse,binascii,hashlib,json,random,struct,sys
from pathlib import Path
from dos_image import DosImage
from unicorn.x86_const import UC_X86_REG_ES,UC_X86_REG_AX,UC_X86_REG_SP,UC_X86_REG_IP,UC_X86_REG_BP
ROOT=Path(__file__).resolve().parents[1];BINARY=ROOT/'build/transfer-blocks/BLOCKS.EXE'
def expected(data,block,crc):
 tail=binascii.crc_hqx(data,0).to_bytes(2,'big') if crc else bytes([sum(data)&255])
 return bytes([1 if len(data)==128 else 2,block,255-block])+data+tail
class Blocks(DosImage):
 def __init__(self,data=b''):
  super().__init__(BINARY,BINARY.parent/'transfer_blocks.map');self.uc.reg_write(UC_X86_REG_ES,self.ds);self.uc.mem_write(self.symbols['transfer_block_input'],data)
 def crc(self,n,source=None):return self.call('_transfer_crc16',[self.offset('transfer_block_input') if source is None else source,n,self.offset('transfer_crc_result')],limit=3000000)
 def output(self):return bytes(self.uc.mem_read(self.symbols['transfer_block_output'],1040))
def main():
 p=argparse.ArgumentParser();p.add_argument('--original',type=Path);a=p.parse_args();rng=random.Random(201);groups=[]
 data_cases=[b'',b'123456789',bytes(range(256)),bytes(128),b'\xff'*1024,bytes(range(256))*128]+[bytes(rng.randrange(256) for _ in range(rng.randrange(2049))) for _ in range(64)]
 for data in data_cases:
  m=Blocks(data);assert m.crc(len(data))==0 and m.get('transfer_crc_result')==binascii.crc_hqx(data,0)
 groups.append({'case':'CRC-reference-empty-known-binary-random-and32768-byte-boundary','inputs':len(data_cases),'passed':True})
 frames=[]
 for size in [128,1024]:
  for crc in [0,1]:
   for block in [0,1,127,128,255]:
    data=bytes(rng.randrange(256) for _ in range(size));m=Blocks(data);old=m.output();assert m.call('_transfer_block_encode',[m.offset('transfer_block_input'),size,block,crc,m.offset('transfer_block_output'),1040],limit=3000000)==0
    want=expected(data,block,crc);assert m.output()==want+old[len(want):];frames.append((data,block,crc,want))
 groups.append({'case':'SOH-STX-block-complement-checksum-and-big-endian-CRC','inputs':len(frames),'passed':True})
 for difference in [-1,0,1,127]:
  data=bytes(range(128));m=Blocks(data);source=m.offset('transfer_block_input');assert m.call('_transfer_block_encode',[source,128,7,1,source+difference,133])==0;assert bytes(m.uc.mem_read(m.data_base+source+difference,133))==expected(data,7,1)
 groups.append({'case':'overlapping-framing-buffers-stage-before-commit','inputs':4,'passed':True})
 m=Blocks();old=m.get('transfer_crc_result')
 for source,count,out,want in [(0,0,m.offset('transfer_crc_result'),0),(0,1,m.offset('transfer_crc_result'),1),(65535,2,m.offset('transfer_crc_result'),1),(m.offset('transfer_block_input'),1,65535,1),(m.offset('transfer_block_input'),32769,m.offset('transfer_crc_result'),2)]:
  before=m.get('transfer_crc_result');status=m.call('_transfer_crc16',[source,count,out],limit=3000000);assert status==want
  if status:assert m.get('transfer_crc_result')==before
 for field,value,want in [(1,127,2),(2,256,2),(3,2,2),(5,132,3),(4,65535,1),(0,65535,1)]:
  m=Blocks(bytes(128));args=[m.offset('transfer_block_input'),128,1,1,m.offset('transfer_block_output'),1040];args[field]=value;old=m.output();assert m.call('_transfer_block_encode',args)==want and m.output()==old
 groups.append({'case':'invalid-count-mode-capacity-and-extents-no-output-mutation','inputs':11,'passed':True})
 if a.original:
  from check_directory_dial_original import Original,DATA,EXPECTED
  image=a.original.read_bytes();assert hashlib.sha256(image).hexdigest()==EXPECTED
  for data in data_cases:
   o=Original(image,[]);o.uc.mem_write(DATA+0x39fc,image[153936+0x39fc:153936+0x3bfc]);o.uc.mem_write(DATA+0x4000,data)
   o.uc.reg_write(UC_X86_REG_SP,0xd000);o.uc.reg_write(UC_X86_REG_BP,0xc000);o.uc.mem_write(DATA+0xd000,struct.pack('<3H',0xf000,0x4000,len(data)));o.uc.emu_start(0x15c77,0x20000,count=3000000)
   assert o.uc.reg_read(UC_X86_REG_IP)==0xf000 and o.uc.reg_read(UC_X86_REG_AX)==binascii.crc_hqx(data,0)
  groups.append({'case':'actual-original-CRC-instructions-against-independent-oracle','inputs':len(data_cases),'passed':True})
  class OriginalFrame(Original):
   def __init__(self,*args):super().__init__(*args);self.wire=bytearray()
   def hook(self,u,at,size,_):
    if at==self.stop:u.emu_stop();return
    if at not in (0x1ab0b,0x1ab92):return
    sp=u.reg_read(UC_X86_REG_SP);ret,first,second=struct.unpack('<3H',u.mem_read(DATA+sp,6))
    if at==0x1ab0b:self.wire.append(first&255);cleanup=2
    else:self.wire.extend(u.mem_read(DATA+second,first));cleanup=4
    u.reg_write(UC_X86_REG_SP,sp+2+cleanup);u.reg_write(UC_X86_REG_IP,ret)
  overlays=[x for x in json.loads((ROOT/'analysis/pcplus-overlays/manifest.json').read_text())['overlays'] if x['id']==21]
  for data,block,crc,want in frames:
   o=OriginalFrame(image,overlays);o.uc.mem_write(DATA+0x39fc,image[153936+0x39fc:153936+0x3bfc]);o.uc.mem_write(DATA+0x5000,data)
   for address,value in [(0x39c0,0x5000),(0xcd34,0),(0xcb5e,len(data)),(0xcc9a,block),(0xc000-12,1 if len(data)==128 else 2),(0xc000-8,crc)]:o.put(address,value)
   o.call(0xe12c,stop=0xe1b6);assert bytes(o.wire)==want
  groups.append({'case':'actual-original-transmit-fragment-wire-equality','inputs':len(frames),'passed':True})
 result={'passed':True,'binary_sha256':hashlib.sha256(BINARY.read_bytes()).hexdigest(),'cases':groups,'scope':'Actual linked93byte CRC and maintained bounded memory-only frame encoder; independent binascii/poly oracle. Optional original explicitly SHAverified; no private data/UART/files/peer transfer.'};(BINARY.parent/'checks.json').write_text(json.dumps(result,indent=2)+'\n');print('Passed',sum(g['inputs'] for g in groups),'CRC/block cases')
if __name__=='__main__':main()
