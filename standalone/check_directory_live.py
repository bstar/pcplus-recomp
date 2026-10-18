#!/usr/bin/env python3
"""Independent linked directory C/ASM transaction tests; only file IO is modeled."""
import argparse,hashlib,itertools,json,struct,sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_AX,UC_X86_REG_IP,UC_X86_REG_SP,UC_X86_REG_ES,UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI
from check_terminal_options import Options,SERIAL_FIELDS
from check_startup_import import fixture as prm_fixture,terminal_expected
from check_modem_import import expected as modem_expected
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/directory'))
from codec import DirectoryRecord201
BINARY=ROOT/'build/terminal/TERMINAL.EXE';MAP=ROOT/'build/terminal/terminal.map'
def record():
 return (DirectoryRecord201.default().with_string('name',b'Local node').with_string('number',b'MiXeD.Host:23')
  .with_integer('baud_index',6).with_integer('parity_index',2).with_integer('data_bits',7)
  .with_integer('stop_bits',2).with_integer('terminal_id',4).with_integer('protocol_index',7).to_bytes())
def word(raw,at,value):
 out=bytearray(raw);struct.pack_into('<H',out,at,value);return bytes(out)
def text(raw,at,size,value):
 assert len(value)<size;out=bytearray(raw);out[at:at+size]=value+b'\0'+bytes(size-len(value)-1);return bytes(out)
def serial_expected(prm,raw):
 port=raw[0x68];prm=bytearray(prm)
 for at,value in [(0,port-1 if port else int.from_bytes(prm[:2],'little')),(2,int.from_bytes(raw[0x2e:0x30],'little')),(4,raw[0x30]),(6,raw[0x32]),(8,raw[0x31]),(0x194,raw[0x49])]:struct.pack_into('<H',prm,at,value)
 return terminal_expected(prm)
def plan_expected(entry,raw,codes,target):
 name=raw[:25];return struct.pack('<5H',entry,raw[0x4a],raw[0x48],raw[0x33],codes)+name+target+bytes(64-len(target))+b'\0'
class Live(Options):
 def __init__(self):
  super().__init__(BINARY,MAP);self.prm=prm_fixture();self.record=record();self.header=bytes(250);self.entry=1;self.codes=0;self.prm_status=0;self.directory_status=0;self.calls=[];self.modem_calls=0;self.number_calls=0
  raw=bytearray(self.prm)
  for i,(base,irq) in enumerate(zip((0x3f8,0x2f8,0x3e8,0x2e8),(4,3,4,3))):struct.pack_into('<H',raw,0x174+i*2,base);struct.pack_into('<H',raw,0x184+i*2,irq)
  self.prm=bytes(raw)
  self.serial=self.offset('terminal_configuration_values');self.modem=self.offset('terminal_modem_settings');self.plan=self.offset('terminal_directory_plan');self.result=self.offset('terminal_directory_io');self.prm_path=self.offset('terminal_config_path');self.directory_path=self.offset('terminal_directory_path')
  self.uc.mem_write(self.data_base+self.prm_path,b'SYN.PRM\0');self.uc.mem_write(self.data_base+self.directory_path,b'SYN.DIR\0')
  self.uc.hook_add(UC_HOOK_CODE,self.boundary)
 def boundary(self,u,address,size,unused):
  if address==self.symbols['_modem_import_decode']:self.modem_calls+=1
  if address==self.symbols['_directory_number_expand']:self.number_calls+=1
  if address not in (self.symbols['_prm_dos_load'],self.symbols['_directory_dos_read']):return
  sp=u.reg_read(UC_X86_REG_SP)
  if address==self.symbols['_prm_dos_load']:
   ret,path,image,io=struct.unpack('<4H',u.mem_read(self.data_base+sp,8));assert bytes(u.mem_read(self.data_base+path,8))==b'SYN.PRM\0'
   status=self.prm_status;self.calls.append(('prm',path,image,io));assert io
   if not status:u.mem_write(self.data_base+image,self.prm)
   u.mem_write(self.data_base+io,struct.pack('<4H',status,5 if status else 0,6 if status else 0,123 if status else 1264))
  else:
   ret,path,entry,selection,io=struct.unpack('<5H',u.mem_read(self.data_base+sp,10));assert bytes(u.mem_read(self.data_base+path,8))==b'SYN.DIR\0' and entry==self.entry
   status=self.directory_status;self.calls.append(('directory',path,entry,selection,io));assert io
   if not status:u.mem_write(self.data_base+selection,struct.pack('<H',entry)+self.header+self.record)
   u.mem_write(self.data_base+io,struct.pack('<4H',status,5 if status else 0,6 if status else 0,456 if status else 23050))
  u.reg_write(UC_X86_REG_AX,status);u.reg_write(UC_X86_REG_SP,sp+2);u.reg_write(UC_X86_REG_IP,ret)
 def poison(self):
  for at,size,value in ((self.serial,36,0xaa),(self.modem,366,0xbb),(self.plan,100,0xcc)):self.uc.mem_write(self.data_base+at,bytes([value])*size)
 def outputs(self):return tuple(bytes(self.uc.mem_read(self.data_base+at,size)) for at,size in ((self.serial,36),(self.modem,366),(self.plan,100)))
 def arguments(self):return [self.prm_path,self.directory_path,self.entry,self.codes,self.serial,self.modem,self.plan,self.result]
 def read(self,args=None):
  self.uc.reg_write(UC_X86_REG_ES,self.ds);status=self.call('_directory_live_read',self.arguments() if args is None else args,limit=400000)
  for reg,value in ((UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678)):assert self.uc.reg_read(reg)==value
  return status
 def result_words(self):return struct.unpack('<5H',self.uc.mem_read(self.data_base+self.result,10))
def main():
 global BINARY,MAP
 parser=argparse.ArgumentParser();parser.add_argument('--binary',type=Path,default=BINARY);parser.add_argument('--map',type=Path,default=MAP);parser.add_argument('--expect-sha256');args=parser.parse_args();BINARY,MAP=args.binary,args.map
 digest=hashlib.sha256(BINARY.read_bytes()).hexdigest()
 if args.expect_sha256:assert digest==args.expect_sha256
 groups=[]
 def done(name,count):groups.append({'case':name,'inputs':count,'passed':True});print(name,'passed',count,flush=True)
 for entry in range(1,201):
  c=Live();c.entry=entry;c.poison();assert c.read()==0
  assert c.outputs()==(serial_expected(c.prm,c.record),modem_expected(c.prm),plan_expected(entry,c.record,0,b'MiXeD.Host:23'))
  assert [call[0] for call in c.calls]==['prm','directory'] and c.modem_calls==1 and c.number_calls==1
  assert c.result_words()==(0,0,0,0,0)
 done('all200-entry-numbers-eight-cdecl-arguments-and-exact-three-plan-bytes',200)
 count=0
 for port in range(5):
  c=Live();raw=bytearray(c.record);raw[0x68]=port;c.record=bytes(raw);c.poison();assert c.read()==0
  assert c.outputs()[0]==serial_expected(c.prm,c.record);count+=1
 for field,values in [('baud',range(9)),('parity',range(5)),('bits',(7,8)),('stop',(1,2)),('profile',(4,6))]:
  for value in values:
   c=Live();raw=bytearray(c.record)
   if field=='baud':struct.pack_into('<H',raw,0x2e,value)
   else:raw[{'parity':0x30,'bits':0x31,'stop':0x32,'profile':0x49}[field]]=value
   c.record=bytes(raw);assert c.read()==0 and c.outputs()[0]==serial_expected(c.prm,c.record);count+=1
 done('record-overrides-all-line-settings-and-DEFAULT-retains-only-PRM-port',count)
 count=0
 for codes,number,header,want in [(0,b'MiXeD.Host:23',b'X'*250,b'MiXeD.Host:23'),(1,b'a55b',b'9,\0'.ljust(25,b'\0')+b'-\0'.ljust(25,b'\0')+bytes(200),b'9,55-'),(1,b'A'*20,b'123\0'.ljust(25,b'\0')+bytes(225),b'123'*20)]:
  c=Live();c.codes=codes;c.header=header;c.record=text(c.record,25,21,number);assert c.read()==0
  assert c.outputs()[2]==plan_expected(1,c.record,codes,want);count+=1
 done('actual-ASM-number-helper-literal-case-and-explicit-legacy-sixty-byte-expansion',count)
 c=Live();raw=bytearray(c.record);raw[0x4a]=1;raw[25:46]=bytes(21);c.record=bytes(raw);bad=bytearray(c.prm);bad[0x18:0x47]=b'X'*47;bad[0xc4:0xd4]=b'X'*16;c.prm=bytes(bad);assert c.read()==0
 assert c.modem_calls==0 and c.number_calls==0 and c.outputs()[1]==bytes(366) and c.outputs()[2]==plan_expected(1,c.record,0,b'')
 done('DIRECT-empty-target-skips-modem-decode-and-number-expansion',1)
 mutations=[(0x2e,b'\x09\0',4),(0x30,b'\x05',4),(0x31,b'\x06',4),(0x32,b'\0',4),(0x49,b'\x07',4),(0x68,b'\x05',4),(0x4a,b'\x02',9),(0x33,b'\x01',10),(0x33,b'\xff',10),(0,b'X'*25,6),(25,b'X'*21,6)]
 for offset,size in ((0x34,9),(0x4b,11),(0x56,9),(0x5f,9)):
  mutations.extend([(offset,b'X\0',7),(offset,b'X'*size,6)])
 for at,value,want in mutations:
  c=Live();raw=bytearray(c.record);raw[at:at+len(value)]=value;c.record=bytes(raw);c.poison();before=c.outputs();assert c.read()==want and c.outputs()==before,(at,value,want)
 for number,codes,header in [(b'',0,bytes(250)),(b'AT^M',0,bytes(250)),(b'A'*20,1,b'1234\0'.ljust(25,b'\0')+bytes(225)),(b'K',1,b'X'*250),(b'A',1,b'^\0'.ljust(25,b'\0')+bytes(225))]:
  c=Live();c.codes=codes;c.header=header;c.record=text(c.record,25,21,number);c.poison();before=c.outputs();assert c.read()==8 and c.outputs()==before
 for at,value in ((0x0a,0),(0x0e,2),(0x1e4,32768)):
  c=Live();c.prm=word(c.prm,at,value);c.poison();before=c.outputs();assert c.read()==5 and c.outputs()==before
 done('unsupported-bindings-half-mode-serial-malformed-fields-target-and-modem-atomic-rejections',len(mutations)+8)
 for kind,values,want in [('prm',range(1,7),2),('directory',range(1,6),3)]:
  for value in values:
   c=Live();setattr(c,kind+'_status',value);c.poison();before=c.outputs();assert c.read()==want and c.outputs()==before
   assert c.result_words()==(want,value,5,6,123 if kind=='prm' else 456)
   assert len(c.calls)==(1 if kind=='prm' else 2)
 done('both-file-boundary-status-details-close-errors-and-three-plan-rollback',11)
 badargs=[(0,0),(1,0),(2,0),(2,201),(3,2),(4,0),(5,0),(6,0),(4,0xfff0),(5,0xff00),(6,0xfff0),(7,0xfffc)]
 for index,value in badargs:
  c=Live();c.poison();before=c.outputs();arguments=c.arguments();arguments[index]=value;assert c.read(arguments)==1 and c.outputs()==before and not c.calls,(index,value)
 for dst,source in ((4,5),(4,6),(5,6),(7,4),(7,5),(7,6),(7,0),(7,1)):
  c=Live();c.poison();before=c.outputs();arguments=c.arguments();arguments[dst]=arguments[source]
  assert c.read(arguments)==1 and c.outputs()==before and not c.calls,(dst,source)
 c=Live();arguments=c.arguments();arguments[7]=0;assert c.read(arguments)==0
 done('null-near-wrap-and-overlapping-output-result-path-guards-plus-optional-result',len(badargs)+9)
 for mask in range(16):
  c=Live();tokens=[b'@SYN.PRM',b'/E:SYN.DIR',b'/N:97']+[token for bit,token in ((1,b'COM3'),(2,b'115200'),(4,b'8N1'),(8,b'NONE')) if mask&bit]
  assert c.parse(b' '.join(tokens))==(0,0);c.entry=97;c.poison();before_record=c.record
  assert c.call('terminal_select_directory')==0
  c.uc.reg_write(UC_X86_REG_ES,c.ds);assert c.call('terminal_load_configuration',limit=500000)==0
  expected={'terminal_port_number':3 if mask&1 else 2,'terminal_baud_low':49664 if mask&2 else 38400,'terminal_baud_high':1 if mask&2 else 0,'terminal_parity':0 if mask&4 else 2,'terminal_data_bits':8 if mask&4 else 7,'terminal_stop_bits':1 if mask&4 else 2,'uart_software_flow':0,'uart_hardware_flow':0 if mask&8 else 1,'csi_terminal_id':4}
  assert all(c.get(k)==v for k,v in expected.items()),(mask,expected)
  assert c.outputs()[0]==serial_expected(c.prm,before_record) and c.outputs()[2]==plan_expected(97,c.record,0,b'MiXeD.Host:23')
  assert bytes(c.uc.mem_read(c.symbols['terminal_dial_target'],64)).split(b'\0',1)[0]==b'MiXeD.Host:23'
 done('actual-CLI-plus-directory-loader-and-all16-category-override-combinations',16)
 for number in (b'0',b'201',b'65537',b'99999999999'):
  c=Live();assert c.parse(b'@SYN.PRM /E:SYN.DIR /N:'+number)==(2,1)
 done('per-digit-entry-range-check-rejects-long-or-out-of-range-numbers',4)
 assert hashlib.sha256(BINARY.read_bytes()).hexdigest()==digest
 result={'passed':True,'binary_sha256':digest,'inputs':sum(group['inputs'] for group in groups),'cases':groups,'scope':'Actual linked directory_live C, serial/modem validators, bounded number ASM, CLI and configuration/connection preparation. Only explicit PRM/directory IO calls modeled; synthetic records/header/PRM, every interrupt and port IO forbidden. Real DOS readers/browser tested separately.'}
 path=ROOT/'build/terminal/directory-live-checks.json';path.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
