#!/usr/bin/env python3
"""Actual DOS16 candidate transaction: precedence, changes and failure atomicity."""
import argparse,hashlib,json,os,struct,subprocess
from pathlib import Path
from unicorn import UC_HOOK_CODE,UC_HOOK_INTR,UC_HOOK_INSN
from unicorn.x86_const import UC_X86_INS_IN,UC_X86_INS_OUT,UC_X86_REG_ES,UC_X86_REG_SP,UC_X86_REG_SS,UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI,UC_X86_REG_EFLAGS
from dos_image import DosImage
from check_setup_model import image
from check_directory_live import record,serial_expected,plan_expected,text,word
from check_modem_import import expected as modem_expected
from check_startup_import import terminal_expected
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/live-configuration';SIZE=626
MAX_STACK=[0]
class Model(DosImage):
 terminal=False
 def __init__(self,directory=False):
  host=ROOT/'build/terminal' if self.terminal else OUT
  super().__init__(host/('TERMINAL.EXE' if self.terminal else 'LIVE.EXE'),host/('terminal.map' if self.terminal else 'live.map'));self.directory=directory
  self.stack_top=self.offset('terminal_stack_top') if self.terminal else 0xe000
  if self.terminal:
   # Test caller owns the bottom of the actual 8 KiB stack, never a product
   # global or memory beyond DGROUP. DosImage checks every executed instruction
   # for collision with the complete fixture; remaining stack is >4 KiB.
   assert self.stack_bytes==8192
   pointer=self.stack_top-self.stack_bytes+16
   for name,size in [('im',1264),('sel',366),('active',626),('dest',626),('result',4),('serial',42),('modem',368),('plan',214),('dr',10)]:
    setattr(self,name,pointer);pointer+=size
   self.fixture_scratch_end=pointer
   assert pointer<self.stack_top-self.stack_bytes//2
  else:
   self.im=self.offset('_live_image');self.sel=self.offset('_live_selection');self.active=self.offset('_live_active');self.dest=self.offset('_live_candidate');self.result=self.offset('_live_result')
   self.serial=self.offset('_live_serial');self.modem=self.offset('_live_modem');self.plan=self.offset('_live_directory');self.dr=self.offset('_live_directory_result')
  self.raw=image();self.record=record();self.header=bytes(250);self.entry=17
  self.uc.reg_write(UC_X86_REG_ES,self.ds)
  self.uc.hook_add(UC_HOOK_CODE,self.stack)
  self.uc.hook_add(UC_HOOK_INTR,self.forbid)
  for ins in (UC_X86_INS_IN,UC_X86_INS_OUT):self.uc.hook_add(UC_HOOK_INSN,self.forbid,None,1,0,ins)
  assert self.decode(initial=True)[0]==0;self.baseline=self.output();self.uc.mem_write(self.data_base+self.active,self.baseline)
 def stack(self,uc,address,size,_):
  assert uc.reg_read(UC_X86_REG_SS)==self.ds
  used=self.stack_top-uc.reg_read(UC_X86_REG_SP);MAX_STACK[0]=max(MAX_STACK[0],used)
  assert 0<=used<8192,'Candidate API exceeds the parent terminal stack budget'
 def forbid(self,*args):raise AssertionError('Pure candidate decoder attempted interrupt/DOS/UART IO')
 def call(self,name,arguments=(),limit=100000):
  if not self.terminal:return super().call(name,arguments,limit)
  entry=[None];returned_flags=[]
  def observe(uc,address,size,_):
   if address==self.symbols[name+'_impl']:entry[0]=uc.reg_read(UC_X86_REG_SP)
   if entry[0] is not None and uc.reg_read(UC_X86_REG_SP)==entry[0] and bytes(uc.mem_read(address,1))==b'\xc3':returned_flags.append(uc.reg_read(UC_X86_REG_EFLAGS))
  hook=self.uc.hook_add(UC_HOOK_CODE,observe)
  try:status=super().call(name,arguments,limit)
  finally:self.uc.hook_del(hook)
  assert len(returned_flags)==1 and returned_flags[0]==self.uc.reg_read(UC_X86_REG_EFLAGS),'Entry bridge changed actual implementation RET flags'
  assert bytes(self.uc.mem_read(self.data_base+self.stack_top-len(arguments)*2,len(arguments)*2))==struct.pack('<'+'H'*len(arguments),*arguments),'Entry bridge changed original caller argument slots'
  return status
 def output(self):return bytes(self.uc.mem_read(self.data_base+self.dest,SIZE))
 def inputs(self):return bytes(self.uc.mem_read(self.data_base+self.im,1264)),bytes(self.uc.mem_read(self.data_base+self.sel,366)),bytes(self.uc.mem_read(self.data_base+self.active,SIZE))
 def decode(self,mask=0,codes=0,initial=False,args=None):
  self.uc.mem_write(self.data_base+self.im,self.raw);self.uc.mem_write(self.data_base+self.sel,struct.pack('<H',self.entry)+self.header+self.record)
  self.uc.mem_write(self.data_base+self.dest,b'\xcc'*SIZE);self.uc.mem_write(self.data_base+self.result,b'\xdd'*4)
  before=self.inputs()
  values=[self.im,self.sel if self.directory else 0,codes,mask,0 if initial else self.active,self.dest,self.result] if args is None else args
  status=self.call('_live_configuration_decode',values,limit=2000000)
  assert bytes(self.uc.mem_read(self.data_base+self.stack_top-len(values)*2,len(values)*2))==struct.pack('<'+'H'*len(values),*values),'Caller argument slots changed'
  assert self.inputs()==before
  for reg,value in [(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678),(UC_X86_REG_ES,self.ds)]:assert self.uc.reg_read(reg)==value
  if status:assert self.output()==b'\xcc'*SIZE
  return status,struct.unpack('<2H',self.uc.mem_read(self.data_base+self.result,4))
 def change(self):return struct.unpack_from('<H',self.output(),624)[0]
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--terminal',action='store_true',help='Replay the normal terminal far-C implementation with caller-owned stack fixtures')
 Model.terminal=parser.parse_args().terminal
 MAX_STACK[0]=0
 cases=[]
 def done(name,n):cases.append(dict(case=name,inputs=n,passed=True));print(name,n,flush=True)
 for directory in (False,True):
  m=Model(directory)
  expected=(serial_expected(m.raw,m.record)+modem_expected(m.raw)+plan_expected(17,m.record,0,b'MiXeD.Host:23') if directory else terminal_expected(m.raw)+modem_expected(m.raw)+bytes(214))+bytes(2)
  assert m.baseline==expected
  assert m.decode()==(0,(0,0)) and m.output()==m.baseline
 done('exact626-byte-initial-plan-and-unchanged-transition-with-and-without-directory',4)
 count=0
 for directory in (False,True):
  for mask in range(16):
   m=Model(directory)
   # Change all four categories. Directory overrides line/baud/profile, port1
   # explicitly selects COM1; choose source record values distinct from active.
   m.raw=word(word(word(word(word(m.raw,0,1),2,8),4,1),6,2),8,7)
   m.raw=word(word(m.raw,0x198,1),0x19a,0)
   if directory:
    r=bytearray(m.record);r[0x68]=2;struct.pack_into('<H',r,0x2e,8);r[0x30]=1;r[0x31]=8;r[0x32]=1;m.record=bytes(r)
   assert m.decode(mask)==(0,(0,0))
   expected_serial=bytearray(serial_expected(m.raw,m.record) if directory else terminal_expected(m.raw))
   for bit,spans in [(1,[(0,2),(32,4)]),(2,[(2,4)]),(4,[(6,6)]),(8,[(12,4)])]:
    if mask&bit:
     for at,n in spans:expected_serial[at:at+n]=m.baseline[at:at+n]
   assert m.output()[:42]==expected_serial,(directory,mask)
   assert m.change()&15==15^mask,(directory,mask,m.change())
   count+=1
 done('all16-CLI-category-combinations-after-global-and-directory-validation',count)
 changes=[(0,1,1),(2,8,2),(4,1,4),(6,2,4),(8,7,4),(0x198,1,8),(0x19a,0,8),(0x194,6,16),(0x1ae,14,32),(0x1b0,14,32),(0x1b2,14,32),(0x1b4,14,32),(0x1b6,14,32),(0x19c,0,32),(0x19e,0,32),(0x1e4,31,64|128),(0xa,46,128),(0xc,3,128),(0xe,0,128),(0x10,0,128),(0x14,1,128),(0x16,4,128),(0x1a4,65535,512)]
 for at,value,flag in changes:
  m=Model();m.raw=word(m.raw,at,value);assert m.decode()[0]==0 and m.change()==flag,(hex(at),m.change(),flag)
 for at,value,flag in [(0x12,27,128),(0x1e2,ord('!'),64|128)]:
  m=Model();raw=bytearray(m.raw);raw[at]=value;m.raw=bytes(raw);assert m.decode()[0]==0 and m.change()==flag
 done('exact-change-flags-for-every-mapped-scalar-category',len(changes)+2)
 count=0
 for at,size in [(0x18,47),*[(0x47+i*25,25) for i in range(5)],*[(0xc4+i*16,16) for i in range(11)]]:
  m=Model();raw=bytearray(m.raw);raw[at:at+2]=b'Z\0';m.raw=bytes(raw);assert m.decode()[0]==0 and m.change()==128;count+=1
  m=Model();raw=bytearray(m.raw);end=raw.index(0,at,at+size);raw[end+1:at+size]=b'\xa5'*(at+size-end-1);m.raw=bytes(raw)
  assert m.decode()[0]==0 and m.change()==0;count+=1
 m=Model();raw=bytearray(m.raw);raw[0x400]^=1;m.raw=bytes(raw);assert m.decode()[0]==0 and m.change()==0
 done('all17-semantic-string-changes-ignore-after-NUL-and-opaque-PRM-bytes',count+1)
 for entry in range(1,201):
  m=Model(True);m.entry=entry;assert m.decode()[0]==0
  assert struct.unpack_from('<H',m.output(),410)[0]==entry
  assert m.change()==(0 if entry==17 else 256)
 done('retained-selection-all200-record-numbers-and-metadata-classification',200)
 m=Model(True);m.record=text(m.record,25,21,b'NEW.EXAMPLE:23');assert m.decode()[0]==0 and m.change()==(256|1024)
 m=Model(True);r=bytearray(m.record);r[0x4b:0x4b+3]=b'pw\0';m.record=bytes(r);assert m.decode()[0]==0 and m.change()==256
 m=Model(True);m.header=b'9,\0'.ljust(25,b'\0')+bytes(225);m.record=text(m.record,25,21,b'A55');assert m.decode(codes=1)[0]==0 and m.output()[445:449]==b'9,55'
 m=Model(True);r=bytearray(m.record);r[0x4a]=1;r[25:46]=bytes(21);m.record=bytes(r);m.raw=word(m.raw,0x1a4,65535);raw=bytearray(m.raw);raw[0x18:0x47]=b'X'*47;raw[0xc4:0xd4]=b'X'*16;m.raw=bytes(raw)
 assert m.decode()[0]==0 and m.output()[42:408]==bytes(366) and m.output()[408:410]==b'\xff\xff'
 done('target-private-metadata-legacy-header-and-DIRECT-modem-skip-with-BREAK',4)
 count=0
 for directory in (False,True):
  for at,value in [(0,4),(2,9),(4,5),(6,0),(8,6),(0x198,2),(0x19a,2),(0x194,5),(0x1ae,256)]:
   m=Model(directory);m.raw=word(m.raw,at,value);assert m.decode(mask=15)[0]==(4 if directory else 2);count+=1
  for at,size in [(0x18,47),(0xc4,16)]:
   m=Model(directory);raw=bytearray(m.raw);raw[at:at+size]=b'X'*size;m.raw=bytes(raw);assert m.decode(mask=15)[0]==(4 if directory else 3);count+=1
 for at,value in [(0x68,5),(0x30,5),(0x49,5),(0x4a,2),(0x33,1)]:
  m=Model(True);raw=bytearray(m.record);raw[at]=value;m.record=bytes(raw);assert m.decode()[0]==4;count+=1
 m=Model(True);m.record=text(m.record,0x34,9,b'RUN');assert m.decode()[0]==4;count+=1
 for at,value in [(0,0),(2,123),(4,1),(6,5),(12,2),(16,5),(18,256),(32,0),(34,0),(36,256)]:
  m=Model();raw=bytearray(m.baseline);struct.pack_into('<H',raw,at,value);m.uc.mem_write(m.data_base+m.active,bytes(raw));assert m.decode()[0]==5;count+=1
 done('invalid-global-record-modem-and-active-state-never-commit-or-hide-behind-CLI',count)
 m=Model(True);args=[m.im,m.sel,0,0,m.active,m.dest,m.result];count=0
 for index,value in [(0,0),(0,0xfc00),(1,0xff00),(4,0xff00),(5,0),(5,0xff00),(6,0),(6,0xffff),(5,m.im),(5,m.sel),(5,m.active),(6,m.im),(6,m.sel),(6,m.active),(6,m.dest),(4,m.im),(1,m.im),(3,16),(3,65535),(2,2)]:
  values=args.copy();values[index]=value;assert m.decode(args=values)[0]==1,(index,value);count+=1
 m=Model();assert m.decode(mask=1,initial=True)[0]==1;assert m.decode(codes=1)[0]==1
 done('near-extent-alias-null-selector-and-unbound-override-rejection',count+2)
 # Exercise the newly public pure directory API's own guards, independently
 # of the outer candidate decoder. Every rejected call preserves all plans.
 m=Model(True);normal=[m.im,m.sel,0,m.serial,m.modem,m.plan,m.dr];count=0
 for index,value in [(0,0),(0,0xfc00),(1,0),(1,0xff00),(1,m.im),(2,2),(3,0),(3,0xfff0),(4,0),(4,0xff00),(5,0),(5,0xff80),(6,0xffff),*[(i,v) for i in (3,4,5,6) for v in (m.im,m.sel)],(4,m.serial),(5,m.serial),(5,m.modem),(6,m.serial),(6,m.modem),(6,m.plan)]:
  args=normal.copy();args[index]=value
  before=m.inputs()
  for ptr,n in [(m.serial,42),(m.modem,368),(m.plan,214)]:m.uc.mem_write(m.data_base+ptr,b'\xcc'*n)
  assert m.call('_directory_live_decode',args,limit=1000000)==1,(index,value)
  assert m.inputs()==before
  for ptr,n in [(m.serial,42),(m.modem,368),(m.plan,214)]:assert bytes(m.uc.mem_read(m.data_base+ptr,n))==b'\xcc'*n
  count+=1
 args=normal.copy();args[-1]=0;assert m.call('_directory_live_decode',args,limit=1000000)==0
 assert bytes(m.uc.mem_read(m.data_base+m.serial,42))==serial_expected(m.raw,m.record)
 done('pure-directory-API-own-null-wrap-input-output-result-alias-guards-and-optional-result',count+1)
 # Actual DOS also compares the refactored file owner and pure transaction.
 (OUT/'VALID.PRM').write_bytes(image());raw=bytes(250)+b''.join(record() for _ in range(200));assert len(raw)==23050;(OUT/'VALID.DIR').write_bytes(raw)
 original={n:hashlib.sha256((OUT/n).read_bytes()).hexdigest() for n in ['VALID.PRM','VALID.DIR']}
 for n in ['PASS.TXT','FAIL.TXT','LOG.TXT']:(OUT/n).unlink(missing_ok=True)
 (OUT/'dosbox.conf').write_text(f'[sdl]\noutput=surface\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "{OUT}"\nc:\nLIVE >LOG.TXT\nif errorlevel 1 goto fail\necho PASS>PASS.TXT\ngoto done\n:fail\necho FAIL>FAIL.TXT\n:done\nexit\n')
 with (OUT/'dosbox.log').open('w') as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(OUT/'dosbox.conf')],stdout=log,stderr=log,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),check=True,timeout=30)
 assert (OUT/'PASS.TXT').exists() and b'LIVE CONFIGURATION PASS' in (OUT/'LOG.TXT').read_bytes(),(OUT/'LOG.TXT').read_bytes()
 assert original=={n:hashlib.sha256((OUT/n).read_bytes()).hexdigest() for n in original}
 done('actual-DOS-file-owner-equals-pure-decode-and-no-fixture-rewrites',1)
 inputs=['src/config/live_configuration.c','src/config/live_configuration.h','src/directory/directory_live.c','src/directory/directory_live.h','standalone/check_live_configuration.py','standalone/live_configuration_host.c','standalone/check_setup_model.py','standalone/check_directory_live.py','standalone/check_modem_import.py','standalone/check_startup_import.py','standalone/dos_image.py','src/directory/codec.py','standalone/terminal_config_fixtures.py']
 binary=ROOT/'build/terminal/TERMINAL.EXE' if Model.terminal else OUT/'LIVE.EXE'
 result={'passed':True,'inputs':sum(c['inputs'] for c in cases),'cases':cases,'binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'host':'terminal-far-C' if Model.terminal else 'standalone-near-C','maximum_CPU_call_stack_bytes':MAX_STACK[0],'DOS_fixture_sha256':original,'DOS_equivalence_binary_sha256':hashlib.sha256((OUT/'LIVE.EXE').read_bytes()).hexdigest(),'sources':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in inputs},'scope':'Actual source-built DOS8086 pure candidate decoder and shared directory transaction. All interrupts/IN/OUT forbidden during CPU replay; separate diagnostic DOS C-runtime/file-owner equivalence test uses synthetic PRM/DIR only. Candidate/active/source atomicity and classification, not live application commit, UART/profile handoff or setup invocation.'}
 (OUT/('terminal-checks.json' if Model.terminal else 'checks.json')).write_text(json.dumps(result,indent=2)+'\n');print('Candidate checks passed',result['inputs'])
if __name__=='__main__':main()
