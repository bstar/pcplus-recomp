#!/usr/bin/env python3
"""Independent actual linked startup C/ASM checks, synthetic PRM loader boundary.

No original/private configuration, DOS or UART IO. This does not replace real DOS
file IO tests: only prm_dos_load is modeled, after verifying actual call arguments.
"""
import argparse,hashlib,itertools,json,struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_AX,UC_X86_REG_IP,UC_X86_REG_SP,UC_X86_REG_ES,UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI
from check_terminal_options import Options,SERIAL_FIELDS
from terminal_config_fixtures import image as terminal_fixture,change,RATES,BASES,IRQS
from check_modem_import import fixture as modem_fixture,expected as modem_expected
ROOT=Path(__file__).resolve().parents[1]
BINARY=ROOT/'build/terminal/TERMINAL.EXE';MAP=ROOT/'build/terminal/terminal.map'
def fixture():
 raw=bytearray(modem_fixture());serial=terminal_fixture()
 for at,size in [(0,10),(0x174,32),(0x194,12),(0x1ae,10),(0x1e0,2)]:raw[at:at+size]=serial[at:at+size]
 return bytes(raw)
def terminal_expected(raw):
 words=lambda at:struct.unpack_from('<H',raw,at)[0]
 port=words(0);rate=RATES[words(2)]
 return struct.pack('<21H',port+1,rate&65535,rate>>16,words(4),words(8),words(6),words(0x198),words(0x19a),words(0x194),*(words(at) for at in (0x1ae,0x1b0,0x1b2,0x1b4,0x1b6,0x19c,0x19e)),words(0x174+port*2),words(0x184+port*2),raw[0x1e2],words(0x1e4),words(0x1e0))
class Startup(Options):
 def __init__(self):
  super().__init__(BINARY,MAP);self.calls=[];self.payload=fixture();self.load_status=0
  self.serial=self.offset('terminal_configuration_values');self.modem=self.offset('terminal_modem_settings');self.result=self.offset('terminal_configuration_io');self.path=self.offset('terminal_config_path')
  self.uc.mem_write(self.data_base+self.path,b'SYN.PRM\0')
  self.uc.hook_add(UC_HOOK_CODE,self.load)
 def load(self,u,address,size,unused):
  if address!=self.symbols['_prm_dos_load']:return
  sp=u.reg_read(UC_X86_REG_SP);ret,path,image,io=struct.unpack('<4H',u.mem_read(self.data_base+sp,8))
  name=bytes(u.mem_read(self.data_base+path,8));assert name==b'SYN.PRM\0'
  self.calls.append({'path':path,'image':image,'io':io,'status':self.load_status})
  # This boundary stands for the separately DOS-tested exact-size read backend.
  if not self.load_status:u.mem_write(self.data_base+image,self.payload)
  if io:u.mem_write(self.data_base+io,struct.pack('<4H',self.load_status,5 if self.load_status else 0,0,0 if self.load_status else 1264))
  u.reg_write(UC_X86_REG_AX,self.load_status);u.reg_write(UC_X86_REG_SP,sp+2);u.reg_write(UC_X86_REG_IP,ret)
 def plans(self):return bytes(self.uc.mem_read(self.data_base+self.serial,42)),bytes(self.uc.mem_read(self.data_base+self.modem,368))
 def poison(self):
  self.uc.mem_write(self.data_base+self.serial,b'\xcc'*42);self.uc.mem_write(self.data_base+self.modem,b'\xdd'*368)
 def startup(self,arguments=None):
  self.uc.reg_write(UC_X86_REG_ES,self.ds)
  status=self.call('_terminal_startup_read',arguments or [self.path,self.serial,self.modem,self.result],limit=300000)
  for reg,want in ((UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678)):assert self.uc.reg_read(reg)==want
  return status

def main():
 global BINARY,MAP
 parser=argparse.ArgumentParser();parser.add_argument("--binary",type=Path,default=BINARY);parser.add_argument("--map",type=Path,default=MAP);parser.add_argument('--expect-sha256');parser.add_argument('--check-invalid-abi',action='store_true',help='Require range/overlap rejection by combined public C entry');args=parser.parse_args()
 BINARY,MAP=args.binary,args.map
 digest=hashlib.sha256(BINARY.read_bytes()).hexdigest()
 if args.expect_sha256:assert digest==args.expect_sha256
 groups=[]
 def done(name,count):groups.append({'case':name,'inputs':count,'passed':True});print(name,'passed',count,flush=True)
 c=Startup();c.poison();assert c.startup()==0
 assert c.plans()==(terminal_expected(c.payload),modem_expected(c.payload));assert len(c.calls)==1
 done('actual-combined-C-one-load-both-plans-exact-and-cdecl-preserved',1)
 cases=[(0,4,2),(2,9,2),(0x198,2,3),(0x194,7,4),(0x1ae,256,5),(0x0a,0,7),(0x0e,2,7),(0x1e4,32768,7)]
 for at,value,want in cases:
  c=Startup();c.payload=change(c.payload,at,value);c.poison();before=c.plans();assert c.startup()==want
  assert c.plans()==before and len(c.calls)==1,(at,value)
 c=Startup();raw=bytearray(c.payload);raw[0x18:0x47]=b'X'*47;c.payload=bytes(raw);c.poison();before=c.plans();assert c.startup()==7 and c.plans()==before and len(c.calls)==1
 c=Startup();raw=bytearray(c.payload);raw[0xc4:0xd4]=b'X'*16;c.payload=bytes(raw);c.poison();before=c.plans();assert c.startup()==7 and c.plans()==before and len(c.calls)==1
 for status in (1,2,3,4,5,6):
  c=Startup();c.load_status=status;c.poison();before=c.plans();assert c.startup()==1 and c.plans()==before and len(c.calls)==1
 done('serial-modem-IO-rejections-leave-both-destinations-unchanged',len(cases)+8)
 for index in (1,2):
  c=Startup();c.poison();before=c.plans();arguments=[c.path,c.serial,c.modem,c.result];arguments[index]=0
  assert c.startup(arguments)==6 and c.plans()==before and not c.calls
 done('null-plan-arguments-rejected-before-loading',2)
 for mask in range(16):
  c=Startup();c.payload=change(change(change(c.payload,0x194,4),0x198,1),0x19a,1)
  tokens=[b'@SYN.PRM',b'/D:Example.Net:23']+[token for bit,token in ((1,b'COM3'),(2,b'115200'),(4,b'7E2'),(8,b'NONE')) if mask&bit]
  assert c.parse(b' '.join(tokens))==(0,0);c.poison();c.uc.reg_write(UC_X86_REG_ES,c.ds)
  assert c.call('terminal_load_configuration',limit=400000)==0
  assert len(c.calls)==1 and c.plans()==(terminal_expected(c.payload),modem_expected(c.payload))
  assert c.get('terminal_break_delay_units')==struct.unpack_from('<H',c.payload,0x1a4)[0]
  port=3 if mask&1 else 2;rate=115200 if mask&2 else 19200
  expected={'terminal_port_number':port,'terminal_baud_low':rate&65535,'terminal_baud_high':rate>>16,'terminal_parity':2 if mask&4 else 0,'terminal_data_bits':7 if mask&4 else 8,'terminal_stop_bits':2 if mask&4 else 1,'uart_software_flow':0 if mask&8 else 1,'uart_hardware_flow':0 if mask&8 else 1,'uart_port_rbr':BASES[port-1],'uart_irq_indices':IRQS[port-1],'csi_terminal_id':4,'attributes_monochrome':0,'attributes_current':0x1e}
  assert all(c.get(k)==v for k,v in expected.items()),(mask,expected)
  assert bytes(c.uc.mem_read(c.symbols['terminal_dial_target'],15)).split(b'\0',1)[0]==b'Example.Net:23'
 done('actual-ASM-loader-prepare-and-all16-CLI-category-overrides',16)
 c=Startup();assert c.parse(b'/D:Example.Net:23')==(0,0);before={k:c.get(k) for k in SERIAL_FIELDS};c.poison();plans=c.plans()
 assert c.call('terminal_load_configuration')==7 and not c.calls and c.plans()==plans
 assert {k:c.get(k) for k in SERIAL_FIELDS}==before
 c=Startup();assert c.parse(b'@SYN.PRM')==(0,0)
 raw=bytearray(c.payload);raw[0x18:0x47]=b'X'*47;c.payload=bytes(raw);c.poison()
 assert c.call('terminal_load_configuration',limit=300000)==0 and len(c.calls)==1
 done('dial-requires-selector-while-serial-only-does-not-decode-unused-modem',2)
 if args.check_invalid_abi:
  count=0
  for serial,modem,io in ((0xffff,None,None),(None,0xffff,None),(None,'serial',None),(None,None,'serial'),(None,None,'modem')):
   c=Startup();c.poison();before=c.plans();serial=c.serial if serial is None else serial;modem=c.modem if modem is None else (c.serial if modem=='serial' else modem);io=c.result if io is None else (c.serial if io=='serial' else c.modem)
   assert c.startup([c.path,serial,modem,io])==6 and c.plans()==before and not c.calls,(serial,modem,io)
   count+=1
  for kind in ('new40-wrap','overlap-appended-metadata','io-overlap-appended-metadata'):
   c=Startup();c.poison();before=c.plans();serial,modem,io=c.serial,c.modem,c.result
   if kind=='new40-wrap':serial=0xffdc
   elif kind=='overlap-appended-metadata':serial=modem-36
   else:io=serial+36
   assert c.startup([c.path,serial,modem,io])==6 and c.plans()==before and not c.calls,kind
   count+=1
  done('invalid-near-extents-and-overlapping-output-IO-buffers-rejected',count)
 assert hashlib.sha256(BINARY.read_bytes()).hexdigest()==digest,'Shared executable changed during tests'
 result={'passed':True,'binary_sha256':digest,'inputs':sum(g['inputs'] for g in groups),'cases':groups,'scope':'Actual linked combined C + assembly configuration/connection preparation and CLI parser. Only exact-size PRM load is explicitly modeled with synthetic bytes; no original/private data or interrupts/UART/DOS IO. Read backend separately tested under DOS.','invalid_abi_guards_required':args.check_invalid_abi}
 output=ROOT/'build/terminal/startup-import-checks.json';output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
