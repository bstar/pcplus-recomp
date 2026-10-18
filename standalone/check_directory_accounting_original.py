#!/usr/bin/env python3
"""Optional SHA-bound original replay: synthetic memory-only record and FILE."""
import argparse,hashlib,json,struct
from pathlib import Path
from check_directory_dial_original import Original,DATA,EXPECTED
from unicorn import UC_HOOK_INTR
from unicorn.x86_const import UC_X86_REG_AX,UC_X86_REG_AH,UC_X86_REG_AL,UC_X86_REG_CX,UC_X86_REG_DX,UC_X86_REG_SP,UC_X86_REG_IP
ROOT=Path(__file__).resolve().parents[1]
class Accounting(Original):
 def __init__(self,image,overlays,year,count,index):
  super().__init__(image,overlays);self.record=bytearray((x*13)&255 for x in range(114));struct.pack_into('<H',self.record,70,count);self.year=year;self.index=index;self.writes=[];self.position=None
  self.uc.mem_write(DATA+0x4729,b'%2.2d/%2.2d/%2.2d\0');self.uc.hook_add(UC_HOOK_INTR,self.intr)
 def intr(self,u,n,_):
  assert n==0x21 and u.reg_read(UC_X86_REG_AH)==0x2a
  u.reg_write(UC_X86_REG_CX,self.year);u.reg_write(UC_X86_REG_DX,0x0a11);u.reg_write(UC_X86_REG_AL,6)
 def hook(self,u,at,size,_):
  if at==self.stop:u.emu_stop();return
  if at not in (0x1ddb6,0x1dd94,0x1853a,0x186ac,0x18c54):return
  sp=u.reg_read(UC_X86_REG_SP);words=struct.unpack('<5H',u.mem_read(DATA+sp,10));ret=words[0];args=words[1:];result=0
  if at==0x1ddb6:
   assert args[0]==self.index;u.mem_write(DATA+0xe650,bytes(self.record));self.events.append('load')
  elif at==0x1dd94:self.record[:]=u.mem_read(DATA+0xe650,114);self.events.append('cache-store')
  elif at==0x1853a:
   assert args[3]==0;self.position=args[1]|args[2]<<16;self.events.append('seek')
  elif at==0x186ac:
   source,size,count,file=args;self.writes.append({'offset':self.position,'bytes_hex':bytes(u.mem_read(DATA+source,size*count)).hex(),'size':size,'count':count});result=count;self.events.append('write')
  else:self.events.append('flush')
  u.reg_write(UC_X86_REG_AX,result);u.reg_write(UC_X86_REG_SP,sp+2);u.reg_write(UC_X86_REG_IP,ret)
def main():
 p=argparse.ArgumentParser();p.add_argument('original',type=Path);a=p.parse_args();image=a.original.read_bytes();assert hashlib.sha256(image).hexdigest()==EXPECTED
 manifest=json.loads((ROOT/'analysis/pcplus-overlays/manifest.json').read_text());overlays=[x for x in manifest['overlays'] if x['id']==4];cases=[]
 for year in [1980,1999,2000,2026,2099]:
  for count in [0,1,255,256,65535]:
   o=Accounting(image,overlays,year,count,3);o.put(0xc000-6,3);o.call(0xd943,stop=0xd96d)
   date=f'10/17/{year-1900:02}'.encode()+b'\0';want=bytearray((x*13)&255 for x in range(114));struct.pack_into('<H',want,70,(count+1)&65535);want[61:61+len(date)]=date
   assert o.record==want,(year,count,o.record[61:72],want[61:72]);assert o.events==['load','cache-store','load','seek','write','flush'];assert o.writes==[{'offset':136+114*3+61,'bytes_hex':bytes(want[61:72]).hex(),'size':11,'count':1}]
   cases.append({'case':'original-success-date-and-partial-write','year':year,'old_count':count,'stored_count':struct.unpack_from('<H',o.record,70)[0],'date_and_count_hex':bytes(o.record[61:72]).hex()})
 for selected,stop in [(0,0xd96d),(65535,0xd548)]:
  o=Accounting(image,overlays,2026,7,3);o.put(0xc000-6,selected);o.call(0xd934,stop=stop);assert not o.events and not o.writes;cases.append({'case':'zero-or-cancel-bypasses-accounting','selected_return':selected})
 for flag in [0,1]:
  o=Accounting(image,overlays,1999,7,3);o.call(0xdd28,[3,flag]);assert o.writes[0]['offset']==136+114*3+(61 if flag==0 else 0);assert o.writes[0]['size']==(11 if flag==0 else 114);cases.append({'case':'writer-full-vs-partial','flag':flag})
 result={'passed':True,'source_sha256':EXPECTED,'cases':cases,'scope':'Actual original date/getdate/sprintf/strcpy, successful accounting fragment and dd28 writer instructions. DOS date interrupt and in-memory cache/FILE services explicitly modeled; no private DIR/PRM or disk writes.'};out=ROOT/'build/directory-accounting/original-replay.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2)+'\n');print('Passed',len(cases),'actual original accounting cases; Y2K count-byte corruption confirmed')
if __name__=='__main__':main()
