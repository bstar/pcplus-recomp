#!/usr/bin/env python3
"""Optional actual original directory-dial replay; synthetic bytes only.

Explicit SHA-verified EXE input, never opens DIR/PRM/contact/password files.
Selected-record loading, port reconfiguration and two UI boundaries modeled.
Original uppercase/atoi/strlen/strncat/strcpy/strcat instructions execute.
"""
import argparse,hashlib,json,random,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_CS,UC_X86_REG_DS,UC_X86_REG_SS,UC_X86_REG_ES,UC_X86_REG_SP,UC_X86_REG_IP,UC_X86_REG_AX,UC_X86_REG_BP
ROOT=Path(__file__).resolve().parents[1];EXPECTED='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904';DATA=0x40000

def upper(data):return bytes(x-32 if 97<=x<=122 else x for x in data)
def atoi16(data):
 i=0
 while i<len(data) and data[i] in (9,32):i+=1
 sign=1
 if i<len(data) and data[i] in (43,45):sign=-1 if data[i]==45 else 1;i+=1
 n=0
 while i<len(data) and 48<=data[i]<=57:n=n*10+data[i]-48;i+=1
 n=(sign*n)&65535;return n if n<32768 else n-65536
class Original:
 def __init__(self,image,overlays):
  self.uc=Uc(UC_ARCH_X86,UC_MODE_16);self.uc.mem_map(0,0x100000);self.uc.mem_write(0x10000,image[0x1200:0xe2d0])
  for o in overlays:
   start=o['relative_load_segment']*16;pos=o['source_file_offset'];self.uc.mem_write(0x10000+start,image[pos:pos+o['initialized_bytes']])
  for r,v in [(UC_X86_REG_CS,0x1000),(UC_X86_REG_DS,DATA>>4),(UC_X86_REG_SS,DATA>>4),(UC_X86_REG_ES,DATA>>4)]:self.uc.reg_write(r,v)
  self.records={};self.events=[];self.dial_result=0;self.stop=0x1f000;self.uc.hook_add(UC_HOOK_CODE,self.hook)
 def put(self,at,value):self.uc.mem_write(DATA+at,struct.pack('<H',value))
 def get(self,at):return struct.unpack('<H',self.uc.mem_read(DATA+at,2))[0]
 def string(self,at,size=128):return bytes(self.uc.mem_read(DATA+at,size)).split(b'\0')[0]
 def hook(self,u,at,size,_):
  if at==self.stop:u.emu_stop();return
  if at not in (0x1ddb6,0x1adba,0x103a7,0x1e2a9,0x14015,0x1e8ad):return
  sp=u.reg_read(UC_X86_REG_SP);ret,arg=struct.unpack('<2H',u.mem_read(DATA+sp,4));cleanup=0
  result=0
  if at==0x1e8ad:result=self.dial_result;self.events.append(('modem-attempt',arg))
  elif at==0x1ddb6:
   assert 1<=arg<=200;u.mem_write(DATA+0xe650,self.records[arg]);self.events.append(('load',arg))
  elif at in (0x1adba,0x103a7):self.events.append(('close' if at==0x1adba else 'configure',[self.get(x) for x in (0x1b84,0x1b86,0x1b88,0x1b8a,0x1b8c,0x1d1a)]))
  elif at==0x1e2a9:cleanup=2
  u.reg_write(UC_X86_REG_AX,result);u.reg_write(UC_X86_REG_SP,sp+2+cleanup);u.reg_write(UC_X86_REG_IP,ret)
 def call(self,entry,args=(),stop=0xf000):
  self.stop=0x10000+stop;self.uc.reg_write(UC_X86_REG_SP,0xd000);self.uc.reg_write(UC_X86_REG_BP,0xc000);self.uc.mem_write(DATA+0xd000,struct.pack('<'+'H'*(len(args)+1),stop,*args));self.uc.emu_start(0x10000+entry,0x20000,count=300000);assert self.uc.reg_read(UC_X86_REG_IP)==stop

def expected(token,number,codes,record_numbers):
 token=upper(token);out=b'';pos=0
 while pos<len(token) and 65<=token[pos]<=74 and len(out)<60:out=(out+codes[token[pos]-65])[:60];pos+=1
 index=atoi16(token[pos:])
 if not 0<=index<=200:return 201,out
 number=upper(record_numbers[index] if index else number)
 for ch in number:
  if len(out)>=60:break
  out=(out+(codes[ch-65] if 65<=ch<=74 else bytes([ch])))[:60]
 while pos<len(token) and 48<=token[pos]<=57:pos+=1
 while pos<len(token) and 65<=token[pos]<=74 and len(out)<60:out=(out+codes[token[pos]-65])[:60];pos+=1
 return index,out

def main():
 p=argparse.ArgumentParser();p.add_argument('original',type=Path);p.add_argument('--manifest',type=Path,default=ROOT/'analysis/pcplus-overlays/manifest.json');a=p.parse_args();image=a.original.read_bytes();assert hashlib.sha256(image).hexdigest()==EXPECTED
 manifest=json.loads(a.manifest.read_text());overlays=[x for x in manifest['overlays'] if x['id'] in (4,5)];cases=[];rng=random.Random(201)
 tokens=[b'',b'0',b'1',b'a1b',b'200',b'201',b'-1',b'65537',b'65536',b' 1B',b'1:AB',b'AB1CJ',b'AB',b'1ZB',b'+1B']+[str(rng.randrange(201)).encode() for _ in range(100)]
 for token in tokens:
  o=Original(image,overlays);codes=[bytes(rng.choice(b'abJ^~012345') for _ in range(rng.randrange(25))) for _ in range(10)];number=b'bbs.example';numbers={i:f'55{i:03}b'.encode() for i in range(1,201)}
  for index,n in numbers.items():record=bytearray(114);record[25:25+len(n)+1]=n+b'\0';o.records[index]=bytes(record)
  o.uc.mem_write(DATA+0xe669,number+b'\0');o.uc.mem_write(DATA+0x70b4,token+b'\0');o.uc.mem_write(DATA+0xe484,b''.join(x+b'\0'*(25-len(x)) for x in codes));o.call(0xec61,[0,0x5000]);got=o.uc.reg_read(UC_X86_REG_AX);want,output=expected(token,number,codes,numbers);assert got==want and o.string(0x5000,61)==output,(token,got,want,o.string(0x5000,61),output);cases.append({'case':'quickdial','token_hex':token.hex(),'return_index':got,'output_length':len(output)})
 for override,oldport in [(0,2),(3,2),(4,2),(255,2)]:
  o=Original(image,overlays);record=bytearray(114);struct.pack_into('<H',record,46,6);record[48:52]=bytes([2,7,2,1]);record[104]=override;o.uc.mem_write(DATA+0xe650,bytes(record))
  for address,value in zip((0x1b84,0x1b86,0x1b88,0x1b8a,0x1b8c,0x1d1a),(oldport,1,0,1,8,0)):o.put(address,value)
  o.call(0xe6ea,stop=0xe72c);newport=oldport if override==0 else (override-1 if override<128 else (override-257)&65535);want=[newport,6,2,2,7,1];assert o.events[-1]==('configure',want);assert sum(x[0]=='close' for x in o.events)==int(override!=0 and override!=oldport+1);cases.append({'case':'serial-apply','override':override,'events':o.events})
 for mode,result in [(0,0),(0,1),(1,0),(255,0)]:
  o=Original(image,overlays);o.uc.mem_write(DATA+0xe69a,bytes([mode]));o.dial_result=result;o.call(0xe7de,stop=0xe7f2)
  assert o.uc.reg_read(UC_X86_REG_AX)==(result if mode==0 else 1) and len(o.events)==int(mode==0)
  cases.append({'case':'modem-direct-control','stored_mode':mode,'attempt_result':result,'actual_result':o.uc.reg_read(UC_X86_REG_AX)})
 for meta,key,script,flags in [(b'',b'',b'',0),(b'meta',b'mixKey',b'myscript',3),(b' x',b' x',b' x',0),(b'\tmeta',b'key',b'',2)]:
  o=Original(image,overlays);record=bytearray(114);record[0x49]=4;record[0x48]=7
  for at,value in [(0x5f,meta),(0x56,key),(0x34,script)]:record[at:at+len(value)+1]=value+b'\0'
  o.uc.mem_write(DATA+0xe650,bytes(record));o.uc.mem_write(DATA+0x661c,b'.KEY\0');o.put(0xc000-6,12);o.put(0xc000-10,0);o.call(0xd96d,stop=0xda05)
  assert o.get(0x1d18)==4 and o.get(0x3996)==7 and o.get(0xc000-10)==flags
  assert o.string(0x3262)==(meta if meta[:1] not in (b'',b' ') else b'')
  assert o.string(0x21d8)==(upper(key+b'.KEY') if key[:1] not in (b'',b' ') else b'')
  assert o.string(0xce6a)==(script if script[:1] not in (b'',b' ') else b'');cases.append({'case':'postconnect-bindings','flags':flags})
 output={'passed':True,'source_sha256':EXPECTED,'cases':cases,'scope':'Actual original ec61/stdlib, selected serial apply and postconnection binding fragments with synthetic records/codes. Record lookup, port services and two UI calls modeled; no private DIR/PRM or hardware.'};out=ROOT/'build/directory-dial/original-replay.json';out.write_text(json.dumps(output,indent=2)+'\n');print('Passed',len(cases),'actual original quickdial/serial/binding cases')
if __name__=='__main__':main()
