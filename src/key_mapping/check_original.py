#!/usr/bin/env python3
"""Optional original key IO replay over synthetic in-memory FILE services only."""
import argparse,hashlib,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'standalone'))
from check_directory_dial_original import Original,DATA,EXPECTED
from unicorn.x86_const import UC_X86_REG_SP,UC_X86_REG_IP,UC_X86_REG_AX

class Files(Original):
 def __init__(self,image,overlays,files):
  super().__init__(image,overlays);self.files=dict(files);self.handles={};self.next_handle=10;self.io=[]
  for at,value in [(0x465f,b'.KBD'),(0x4664,b'rb'),(0x4667,b'PCPLUS.KBD'),(0x4672,b'rb'),(0x6032,b'.KEY'),(0x6037,b'rb'),(0x603a,b'wb')]:self.uc.mem_write(DATA+at,value+b'\0')
 def hook(self,u,at,size,_):
  if at==self.stop:u.emu_stop();return
  if at not in (0x1353d,0x1841a,0x1853a,0x1845a,0x186ac,0x18318,0x1427f):return
  sp=u.reg_read(UC_X86_REG_SP);words=struct.unpack('<5H',u.mem_read(DATA+sp,10));ret=words[0];a=words[1:];result=0
  if at==0x1353d:result=a[0] # Explicit path-resolver model; no implicit host search.
  elif at==0x1841a:
   name=self.string(a[0]);mode=self.string(a[1]);self.io.append(('open',name.decode(),mode.decode()))
   if mode==b'wb':self.files[name]=b''
   if name in self.files:
    result=self.next_handle;self.next_handle+=1;self.handles[result]=[name,0]
  elif at==0x1853a:
   handle,lo,hi,origin=a;assert origin==0;self.handles[handle][1]=lo|hi<<16;self.io.append(('seek',lo|hi<<16))
  elif at==0x1845a:
   dest,size,count,handle=a;name,pos=self.handles[handle];raw=self.files[name][pos:pos+size*count]
   if raw:u.mem_write(DATA+dest,raw)
   self.handles[handle][1]+=len(raw);result=len(raw)//size;self.io.append(('read',dest,size,count,len(raw)))
  elif at==0x186ac:
   source,size,count,handle=a;name,pos=self.handles[handle];raw=bytes(u.mem_read(DATA+source,size*count));old=self.files[name];self.files[name]=old[:pos]+raw+old[pos+len(raw):];self.handles[handle][1]+=len(raw);result=count;self.io.append(('write',source,size,count))
  elif at==0x18318:self.handles.pop(a[0]);self.io.append(('close',))
  else:self.io.append(('ui-error',))
  u.reg_write(UC_X86_REG_AX,result);u.reg_write(UC_X86_REG_SP,sp+2);u.reg_write(UC_X86_REG_IP,ret)

def main():
 p=argparse.ArgumentParser();p.add_argument('original',type=Path);a=p.parse_args();image=a.original.read_bytes();assert hashlib.sha256(image).hexdigest()==EXPECTED
 overlays=[x for x in json.loads((ROOT/'analysis/pcplus-overlays/manifest.json').read_text())['overlays'] if x['id']==3];cases=[]
 table=b''.join(bytes([profile])*948 for profile in range(33))
 for profile in range(33):
  o=Files(image,overlays,{b'SYN.KBD':table});o.uc.mem_write(DATA+0x3262,b'SYN\0');o.put(0x1d18,profile);o.call(0xcd2)
  assert o.uc.reg_read(UC_X86_REG_AX)==1 and bytes(o.uc.mem_read(DATA+0x3378,948))==bytes([profile])*948
  assert ('seek',profile*948) in o.io and ('read',0x3378,948,1,948) in o.io and not o.handles
  cases.append({'case':'profile-block-seek-and-read','profile':profile})
 o=Files(image,overlays,{b'PCPLUS.KBD':table});o.uc.mem_write(DATA+0x3262,b'MISSING\0');o.put(0x1d18,6);o.call(0xcd2);assert o.string(0x3262)==b'PCPLUS.KBD' and o.uc.reg_read(UC_X86_REG_AX)==1;cases.append({'case':'missing-named-KBD-falls-back-to-PCPLUS'})
 for n in [0,1,947,948,949]:
  raw=bytes([0x41])*n;o=Files(image,overlays,{b'SYN.KBD':raw});o.uc.mem_write(DATA+0x3262,b'SYN.KBD\0');o.uc.mem_write(DATA+0x3378,b'X'*948);o.put(0x1d18,0);o.call(0xcd2)
  assert o.uc.reg_read(UC_X86_REG_AX)==1 and bytes(o.uc.mem_read(DATA+0x3378,948))==raw[:948]+b'X'*(948-min(n,948));cases.append({'case':'KBD-short-read-unchecked-and-suffix-ignored','file_bytes':n})
 for n in [0,1,539,540,541]:
  raw=bytes([0x41])*n;o=Files(image,overlays,{b'SYN.KEY':raw});o.uc.mem_write(DATA+0x5000,b'SYN.KEY\0');o.uc.mem_write(DATA+0x3756,b'X'*540);o.call(0xe1cc,[0x5000])
  assert o.uc.reg_read(UC_X86_REG_AX)==1 and bytes(o.uc.mem_read(DATA+0x3756,540))==raw[:540]+b'X'*(540-min(n,540));assert ('read',0x3756,54,10,min(n,540)) in o.io;cases.append({'case':'KEY-record-read-short-unchecked-suffix-ignored','file_bytes':n})
 o=Files(image,overlays,{});o.uc.mem_write(DATA+0x21d8,b'new\0');o.uc.mem_write(DATA+0x3756,b'X'*540);o.call(0xe18a)
 want=(b'\x03\0\0'+b'X'*51)*10;assert o.files[b'NEW.KEY']==want and o.string(0x21d8)==b'NEW.KEY';assert ('write',0x3756,54,10) in o.io;cases.append({'case':'missing-KEY-default-text-slots-preserve-tail-and-create540bytes'})
 result={'passed':True,'source_sha256':EXPECTED,'cases':cases,'scope':'Actual original KBD loader/KEY load-save-default routines over synthetic memory-only FILE/path/UI services. No installedKBD/KEY/PRM or private macros read; original errors intentionally demonstrated.'};out=ROOT/'build/key-mapping/original-replay.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2)+'\n');print('Passed',len(cases),'actual original key-file cases')
if __name__=='__main__':main()
