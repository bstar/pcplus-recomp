#!/usr/bin/env python3
"""Actual DOS8086 editor model: lossless fields, validation and atomic edits."""
import hashlib,json,os,struct,subprocess
from pathlib import Path
from unicorn import UC_HOOK_INTR,UC_HOOK_INSN
from unicorn.x86_const import UC_X86_INS_IN,UC_X86_INS_OUT,UC_X86_REG_ES,UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI,UC_X86_REG_DS,UC_X86_REG_SS
from dos_image import DosImage
from check_modem_import import fixture
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/setup-model'
SOURCES=['src/config/setup_model.c','src/config/transfer_import.c','src/config/terminal_import.c','src/config/modem_import.c','src/config/prm_dos.c','standalone/setup_model_host.c']
RATES=[300,1200,2400,4800,9600,19200,38400,57600,115200]
def image():
 raw=bytearray(fixture());raw[0x31c]=0;struct.pack_into('<H',raw,0x42c,0)
 for at,v in [(0,0),(2,1),(4,0),(6,1),(8,8),(0x1e0,0),(0x4ea,13),(0x194,4),(0x198,0),(0x19a,1),(0x19c,1),(0x19e,1),*[(0x1ae+i*2,7+i) for i in range(5)],*[(0x174+i*2,v) for i,v in enumerate([0x3f8,0x2f8,0x3e8,0x2e8])],*[(0x184+i*2,v) for i,v in enumerate([4,3,4,3])]]:struct.pack_into('<H',raw,at,v)
 return bytes(raw)
def build():
 OUT.mkdir(parents=True,exist_ok=True)
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-s','-w4','-we','-k8192','-i='+str(ROOT/'src/config'),'-fm=setup.map','-fe=MODEL.EXE',*[str(ROOT/p) for p in SOURCES]],cwd=OUT,check=True)
class Model(DosImage):
 def __init__(self):
  super().__init__(OUT/'MODEL.EXE',OUT/'setup.map')
  self.a=self.offset('_setup_baseline');self.b=self.offset('_setup_staged');self.t=self.offset('_setup_text');self.bad=self.offset('_setup_bad')
  self.uc.reg_write(UC_X86_REG_ES,self.ds)
  self.uc.hook_add(UC_HOOK_INTR,self.forbid)
  for ins in (UC_X86_INS_IN,UC_X86_INS_OUT):self.uc.hook_add(UC_HOOK_INSN,self.forbid,None,1,0,ins)
  self.reset()
 def call(self,name,arguments=(),limit=100000):
  result=super().call(name,arguments,limit)
  for reg,value in [(UC_X86_REG_ES,self.ds),(UC_X86_REG_DS,self.ds),(UC_X86_REG_SS,self.ds),(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678)]:assert self.uc.reg_read(reg)==value,(name,reg)
  return result
 def forbid(self,*args):raise AssertionError('Editor model attempted DOS/BIOS/UART IO')
 def reset(self,raw=None):
  raw=image() if raw is None else bytes(raw)
  self.uc.mem_write(self.data_base+self.a,raw);self.uc.mem_write(self.data_base+self.b,raw)
 def raw(self,ptr=None):return bytes(self.uc.mem_read(self.data_base+(self.b if ptr is None else ptr),1264))
 def get(self,i,cap=64,out=None):
  self.uc.mem_write(self.data_base+self.t,b'\xcc'*64)
  status=self.call('_setup_get',[self.b,i,self.t if out is None else out,cap],limit=400000)
  text=bytes(self.uc.mem_read(self.data_base+self.t,64)).split(b'\0')[0]
  if status:assert text==b'\xcc'*64
  return status,text
 def set(self,i,text):
  assert len(text)<=64
  self.uc.mem_write(self.data_base+self.t,text+b'\0'*(64-len(text)))
  before=self.raw();baseline=self.raw(self.a)
  status=self.call('_setup_set',[self.a,self.b,i,self.t],limit=400000)
  assert self.raw(self.a)==baseline
  if status:assert self.raw()==before
  return status
 def validate(self):
  before=self.raw();status=self.call('_setup_validate',[self.b,self.bad],limit=1000000)
  assert before==self.raw();return status,self.get_word()
 def get_word(self):return int.from_bytes(self.uc.mem_read(self.data_base+self.bad,2),'little')
def main():
 build();m=Model();cases=[]
 def record(name,n):cases.append({'case':name,'inputs':n,'passed':True});print(name,n,flush=True)
 assert m.validate()==(0,65535)
 for i in range(48):
  m.reset();status,text=m.get(i);assert status==0,(i,status)
  assert m.set(i,text)==0 and m.raw()==image(),i
 record('all48-fields-get-set-byte-identical-with-opaque-tail-data',48)
 for index,values in [(0,[b'1',b'2',b'3',b'4']),(1,[str(v).encode() for v in RATES]),(2,[b'7',b'8']),(3,[bytes([c]) for c in b'NOEMSnoems']),(4,[b'1',b'2']),(9,[b'4',b'6']),(26,[b'0',b'350',b'65535'])]:
  for text in values:
   m.reset();assert m.set(index,text)==0,(index,text)
   assert m.validate()==(0,65535),(index,text,m.validate())
   if index==1:
    # Match existing decoder's real rate, not just a round-trip in the editor.
    ptr=m.t
    assert m.call('_terminal_import_decode',[m.b,ptr])==0
    plan=bytes(m.uc.mem_read(m.data_base+ptr,44));assert struct.unpack_from('<I',plan,2)[0]==int(text)
 record('serial-profile-and-BREAK-values-agree-with-existing-importers',32)
 invalid={0:[b'0',b'5',b'-1'],1:[b'600',b'57601',b'4294967296'],2:[b'6',b'9'],3:[b'X',b'NN'],4:[b'0',b'3'],5:[b'2'],6:[b'2'],7:[b'2F8',b'FFFF'],8:[b'3',b'0'],9:[b'5'],10:[b'2'],11:[b'2'],12:[b'100',b'GG'],17:[b'0',b'32768'],18:[b'32768'],19:[b'2'],20:[b'2'],21:[b'256'],22:[b'2'],23:[b'32768'],24:[b'32768'],25:[b'256'],26:[b'65536',b'115200',b'99999999999999999999']}
 count=0
 for i,values in invalid.items():
  for text in values:
   m.reset();assert m.set(i,text)==2,(i,text);count+=1
 for i in range(48):
  m.reset();assert m.set(i,b'Z'*64)==2;count+=1
 record('invalid-numeric-parity-and-unterminated-edits-entire-image-atomic',count)
 count=0
 for i,at,size in [(27,0x18,47),*[(28+j,0x47+j*25,25) for j in range(5)]]:
  for text in [b'',b'A'*(size-1),b'^M^^^',b'^^',b'^@\xff']:
   m.reset();assert m.set(i,text)==0
   expected=bytearray(image());expected[at:at+len(text)+1]=text+b'\0';assert m.raw()==expected
   original=m.get(i)[1];assert original==text
   # Revert a longer/shorter edit including every byte after the terminator.
   m.uc.mem_write(m.data_base+m.b,image());original=m.get(i)[1]
   assert m.set(i,b'CHANGED^M')==0 and m.set(i,original)==0 and m.raw()==image();count+=1
  for text in [b'A'*size,b'^',b'^^^^']:
   m.reset();assert m.set(i,text)==2;count+=1
 record('six-command-caret-grammar-capacities-tail-preservation-and-revert',count)
 count=0
 for i in range(33,44):
  at=0xc4+(i-33)*16
  for text,decoded in [(b'',b''),(b'1B 5B FF 01 5E',b'\x1b[\xff\x01^'),(b' '.join([b'FF']*15),b'\xff'*15)]:
   m.reset();assert m.set(i,text)==0
   expected=bytearray(image());expected[at:at+len(decoded)+1]=decoded+b'\0';assert m.raw()==expected
   assert m.validate()==(0,65535);count+=1
  for text in [b'00',b'0',b'GG',b'41 ',b' 41',b'4142',b'41  42',b' '.join([b'41']*16)]:
   m.reset();assert m.set(i,text)==2;count+=1
 record('11-expanded-response-slots-lossless-hex-and-invalid-input-atomic',count)
 # Corrupt every field independently; viewing must not repair it, validation
 # must focus the field, and an explicit edit must repair it.
 count=0
 for i,at in [(0,0),(1,2),(2,8),(3,4),(4,6),(5,0x198),(6,0x19a),(7,0x174),(8,0x184),(9,0x194),(10,0x19c),(11,0x19e),*[(12+j,0x1ae+j*2) for j in range(5)],(17,0xa),(18,0xc),(19,0xe),(20,0x10),(22,0x14),(23,0x16),(24,0x1e4),(44,0x1e0)]:
  m.reset();original=m.get(i)[1];raw=bytearray(image());raw[at:at+2]=b'\xff\xff';m.reset(raw)
  assert m.get(i)[0]==3 and m.raw()==raw
  assert m.validate()==(3,i),(i,m.validate())
  assert m.set(i,original)==0 and m.validate()==(0,65535);count+=1
 for i,at,size in [(27,0x18,47),*[(28+j,0x47+j*25,25) for j in range(5)],*[(33+j,0xc4+j*16,16) for j in range(11)]]:
  m.reset();original=m.get(i)[1];raw=bytearray(image());raw[at:at+size]=b'X'*size;m.reset(raw)
  assert m.get(i)[0]==3 and m.validate()==(3,i)
  assert m.set(i,original)==0 and m.validate()==(0,65535);count+=1
 record('malformed-loaded-fields-view-without-normalizing-and-explicit-repair',count)
 m.reset()
 for args in [(0,m.b,0,m.t),(m.a,m.a,0,m.t),(m.a,m.b,0,m.b),(m.a,m.b,0,0xffe0),(m.a,m.b,48,m.t),(0xfc00,m.b,0,m.t)]:
  before=m.raw();assert m.call('_setup_set',args)==1 and m.raw()==before
 for args in [(0,0,m.t,64),(m.b,0,m.b,64),(m.b,0,m.t,0),(m.b,0,m.t,1),(m.b,0,0xffe0,64),(m.b,48,m.t,64)]:assert m.call('_setup_get',args)==1
 for args in [(0,m.bad),(m.b,m.b),(m.b,0),(m.b,0xffff)]:assert m.call('_setup_validate',args)==1
 record('near-cdecl-null-overlap-capacity-and-segment-wrap',16)
 # Transfer configuration is independent of the live serial-settings ABI.
 transfer=m.offset('_setup_transfer');count=0
 def decoded(want_status=0):
  original=m.raw();m.uc.mem_write(m.data_base+transfer,b'\xcc'*66)
  status=m.call('_transfer_import_decode',[m.b,transfer],limit=400000)
  result=bytes(m.uc.mem_read(m.data_base+transfer,66))
  assert status==want_status and original==m.raw()
  if status:assert result==b'\xcc'*66
  return result
 for value in (0,1,2,255,256,65535):
  m.reset();assert m.set(46,str(value).encode())==0
  assert m.get(46)==(0,str(value).encode()) and m.validate()==(0,65535)
  plan=decoded();assert int.from_bytes(plan[:2],'little')==bool(value) and plan[2:]==b'.'+bytes(63)
  expected=bytearray(image());struct.pack_into('<H',expected,0x42c,value);assert m.raw()==expected;count+=1
 record('Auto-Download-word-lossless-edit-nonzero-enables-decoded-flag',count)
 paths=[b'',b'.',b'.\\',b'c:',b'c:.',b'C:.\\',b'/',b'\\',b'c:\\',b'c:/',b'c:games',b'A:B',b'\\GAMES\\DOS/',b'Games.old',b'GAMES.OLD/NEW',b'/'.join([b'A'*8]*7)+b'/']
 for path in paths:
  m.reset();assert m.set(47,path)==0,path
  expected=bytearray(image());expected[0x31c:0x31c+len(path)+1]=path+b'\0'
  assert m.raw()==expected and m.get(47)==(0,path) and m.validate()==(0,65535)
  plan=decoded();assert plan[2:].split(b'\0')[0]==(path or b'.')
  assert m.set(47,b'OTHER')==0 and m.set(47,path)==0 and m.raw()==expected
  assert m.set(47,b'')==0 and m.raw()==image()
 record('download-path-roots-drive-relative-empty-63-byte-tail-preservation-and-revert',len(paths))
 bad_paths=[b'..',b'../',b'GAMES/../DOS',b'COM1',b'aux.txt',b'NUL',b'con',b'LPT9',b'CLOCK$',b'A B',b'A//B',b'//SERVER',b'A'*9,b'A.1234',b'A.',b'ABC:D',b'1:',b'C::A',b'A*',b'A?',b'A|B',b'A<B',b'A>B',b'A"B',b'A\x1bB',b'A\xffB']
 for path in bad_paths:
  m.reset();assert m.set(47,path)==2,path
  raw=bytearray(image());raw[0x31c:0x31c+len(path)+1]=path+b'\0';m.reset(raw)
  assert m.get(47)[0]==3 and m.validate()==(3,47),path
  decoded(2)
  assert m.set(47,b'')==0 and m.validate()==(0,65535)
 raw=bytearray(image());raw[0x31c:0x35c]=b'X'*64;m.reset(raw)
 assert m.get(47)[0]==3 and m.validate()==(3,47);decoded(2)
 record('invalid-loaded-path-rejected-without-mutation-and-explicit-repair',len(bad_paths)+1)
 m.reset()
 for args in [(0,transfer),(m.b,0),(m.b,m.b),(0xfc00,transfer),(m.b,0xffc0)]:
  before=m.raw();assert m.call('_transfer_import_decode',args)==1 and m.raw()==before
 for pointer,capacity in [(0,64),(m.t,0),(m.t,65),(0xffe0,64)]:
  assert m.call('_transfer_import_path',[pointer,capacity])==0
 record('transfer-settings-near-null-alias-wrap-and-capacity',9)

 (OUT/'VALID.PRM').write_bytes(image());before=hashlib.sha256(image()).hexdigest()
 for name in ['PASS.TXT','FAIL.TXT','LOG.TXT']:(OUT/name).unlink(missing_ok=True)
 (OUT/'dosbox.conf').write_text(f'[sdl]\noutput=surface\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "{OUT}"\nc:\nMODEL >LOG.TXT\nif errorlevel 1 goto fail\necho PASS>PASS.TXT\ngoto done\n:fail\necho FAIL>FAIL.TXT\n:done\nexit\n')
 with (OUT/'dosbox.log').open('w') as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(OUT/'dosbox.conf')],stdout=log,stderr=log,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),timeout=35,check=True)
 assert (OUT/'PASS.TXT').exists() and b'SETUP MODEL PASS' in (OUT/'LOG.TXT').read_bytes(),(OUT/'LOG.TXT').read_bytes()
 assert hashlib.sha256((OUT/'VALID.PRM').read_bytes()).hexdigest()==before
 record('actual-DOS-c-runtime-model-and-no-file-rewrites',1)
 sources=SOURCES+['src/config/transfer_import.h','src/config/setup_model.h','src/config/terminal_import.h','src/config/modem_import.h','src/config/prm_dos.h','standalone/check_setup_model.py']
 result={'passed':True,'cases':cases,'binary_sha256':hashlib.sha256((OUT/'MODEL.EXE').read_bytes()).hexdigest(),'sources':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sources},'scope':'Actual source-built DOS8086 C. Synthetic settings only. Pure API replay forbids interrupts and port I/O; separate DOS run checks C runtime and no rewrite. Field model only, no settings UI, save ownership or original PCSETUP child compatibility.'}
 (OUT/'checks.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
