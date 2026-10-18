#!/usr/bin/env python3
"""Actual linked recovered decoder and maintained validation, synthetic input only."""
import hashlib,json,random,sys
from pathlib import Path
from unicorn.x86_const import UC_X86_REG_EFLAGS,UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI
from dos_image import DosImage
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/config'))
from prm import expand_modem_command
BINARY=ROOT/'build/modem-commands/MODEMCMD.EXE'
class Commands(DosImage):
 def __init__(self):super().__init__(BINARY,BINARY.parent/'modem_commands.map')
 def run(self,data,src_capacity=None,dst_capacity=130,source=None,destination=None):
  source=self.offset('modem_source') if source is None else source;destination=self.offset('modem_destination') if destination is None else destination
  self.uc.mem_write(self.data_base+source,data)
  before=bytes(self.uc.mem_read(self.data_base,65536))
  ax=self.call('modem_expand_bounded',[source,destination,len(data) if src_capacity is None else src_capacity,dst_capacity])
  for register,value in [(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678)]:assert self.uc.reg_read(register)==value
  return ax,bool(self.uc.reg_read(UC_X86_REG_EFLAGS)&1),before,source,destination

def main():
 cases=[]
 def check(name,fn):count=fn();cases.append({'case':name,'passed':True,'inputs':count});print(name,'passed',count)
 def expansion():
  rng=random.Random(201);inputs=[b'',b'AT^M',b'^^',b'^^^',b'A^`B']+[b'^'+bytes([i]) for i in range(1,256)]
  inputs += [bytes(rng.randrange(1,256) for _ in range(rng.randrange(127)))+b'A' for _ in range(256)];count=0
  for data in inputs:
   try:expected=expand_modem_command(data)
   except ValueError:continue
   c=Commands();ax,carry,_,_,dst=c.run(data+b'\0')
   assert not carry and ax==len(expected),(data,ax,carry)
   assert bytes(c.uc.mem_read(c.data_base+dst,len(expected)+1))==expected+b'\0'
   assert bytes(c.uc.mem_read(c.data_base+dst-2,2))==b'\x5a\xa5'
   assert bytes(c.uc.mem_read(c.data_base+dst+130,2))==b'\xa5\x5a';count+=1
  return count
 check('actual-recovered-core-via-bounded-near-abi-all-caret-bytes-and-random-inputs',expansion)
 def rejected():
  inputs=[(b'A\0',0,130,None,None,1),(b'A\0',130,130,None,None,1),(b'AAAAA',5,130,None,None,2),(b'BAD^\0',5,130,None,None,3),(b'AT^M\0',5,3,None,None,4),(b'A\0',2,0,None,None,1),(b'A\0',2,32,None,0xfff0,1),(b'A\0',32,130,0xfff0,None,1)]
  for data,src_size,dst_size,src,dst,want in inputs:
   c=Commands();ax,carry,before,source,destination=c.run(data,src_size,dst_size,src,dst)
   assert carry and ax==want,(data,src_size,dst_size,ax,carry)
   extent=min(dst_size,130,65536-destination)
   assert bytes(c.uc.mem_read(c.data_base+destination,extent))==before[destination:destination+extent]
  return len(inputs)
 check('validation-errors-leave-destination-unchanged',rejected)
 def edges():
  for size in (0,1,24,46,127,128):
   c=Commands();ax,carry,_,_,dst=c.run(b'X'*size+b'\0',dst_capacity=size+1)
   assert not carry and ax==size and bytes(c.uc.mem_read(c.data_base+dst,size+1))==b'X'*size+b'\0'
  return 6
 check('exact-source-and-destination-capacity-edges',edges)
 def overlap():
  for displacement in (-1,0,1,2):
   c=Commands();src=c.offset('modem_source');dst=src+displacement
   ax,carry,before,_,_=c.run(b'ABC\0',destination=dst,dst_capacity=4)
   assert carry and ax==5
   assert bytes(c.uc.mem_read(c.data_base+dst,4))==before[dst:dst+4]
  return 4
 check('overlapping-source-destination-rejected-before-mutation',overlap)
 result={'passed':True,'binary_sha256':hashlib.sha256(BINARY.read_bytes()).hexdigest(),'cases':cases,'scope':'Actual relocated source-only DOS87-byte original decoder plus maintained bounded wrapper. Synthetic inputs and CPU execution; no UART or DOS side effects.'}
 (BINARY.parent/'cpu-results.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
