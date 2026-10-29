#!/usr/bin/env python3
"""Execute linked canonical-path staging and accounting refusals; DOS60 modeled."""
import argparse,hashlib,json,re,struct
from pathlib import Path
from unicorn import UC_HOOK_CODE,UC_HOOK_INTR
from unicorn.x86_const import *
from dos_image import DosImage
from terminal_memory import inspect_terminal_memory
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
class Identity(DosImage):
 def __init__(self,binary,reply=b'd:\\base\\test.dir',error=0):
  super().__init__(binary,binary.parent/'terminal.map')
  self.entries={n:(self.base_segment+int(s,16),int(o,16)) for s,o,n in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',(binary.parent/'terminal.map').read_text(),re.M|re.I)}
  self.reply=reply;self.error=error;self.calls=[];self.waiting=None
  self.uc.hook_add(UC_HOOK_INTR,self.interrupt);self.uc.hook_add(UC_HOOK_CODE,self.stop)
 def stop(self,u,address,size,data):
  if self.waiting and u.reg_read(UC_X86_REG_CS)==self.waiting[0] and address==self.waiting[1]:u.emu_stop()
 def interrupt(self,u,number,data):
  assert number==0x21 and u.reg_read(UC_X86_REG_AX)==0x6000,'Only DOS canonicalization is modeled'
  assert u.reg_read(UC_X86_REG_DS)==u.reg_read(UC_X86_REG_SS)==u.reg_read(UC_X86_REG_ES)==self.ds
  src=self.data_base+u.reg_read(UC_X86_REG_SI);self.calls.append(bytes(u.mem_read(src,64)).split(b'\0',1)[0].decode('ascii'))
  if not self.error:u.mem_write(self.data_base+u.reg_read(UC_X86_REG_DI),self.reply+(b'\0' if len(self.reply)<128 else b''))
  u.reg_write(UC_X86_REG_AX,self.error);flags=u.reg_read(UC_X86_REG_EFLAGS);u.reg_write(UC_X86_REG_EFLAGS,flags|1 if self.error else flags&~1)
 def bank(self,name,args=(),far=False):
  u=self.uc;seg,off=self.entries[name];cs=self.code_segment if far else seg;stop=self.return_offset if far else 0xfffe
  for r,v in [(UC_X86_REG_CS,seg),(UC_X86_REG_DS,self.ds),(UC_X86_REG_SS,self.ds),(UC_X86_REG_ES,0xb800),(UC_X86_REG_EFLAGS,0x202),(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678)]:u.reg_write(r,v)
  words=([stop,cs] if far else [stop])+list(args);sp=self.offset('terminal_stack_top')-2*len(words)
  u.mem_write(self.data_base+sp,struct.pack('<'+'H'*len(words),*words));u.reg_write(UC_X86_REG_SP,sp)
  self.waiting=(cs,cs*16+stop);u.emu_start(self.symbols[name],0,count=400000)
  assert u.reg_read(UC_X86_REG_CS)==cs and u.reg_read(UC_X86_REG_IP)==stop and u.reg_read(UC_X86_REG_SP)==sp+(4 if far else 2),(name,'return/stack')
  for r,v in [(UC_X86_REG_DS,self.ds),(UC_X86_REG_SS,self.ds),(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678)]:assert u.reg_read(r)==v,(name,'callee ABI')
  self.waiting=None;return u.reg_read(UC_X86_REG_AX)
 def configured(self):
  self.uc.mem_write(self.symbols['terminal_config_path'],b'TEST.PRM\0'+bytes(55))
  self.uc.mem_write(self.symbols['terminal_directory_path'],b'TEST.DIR\0'+bytes(55))
  context=bytearray(496);struct.pack_into('<H',context,0,1);context[368:432]=b'TEST.PRM\0'+bytes(55);context[432:496]=b'TEST.DIR\0'+bytes(55)
  self.uc.mem_write(self.symbols['terminal_directory_context'],bytes(context));self.put('terminal_directory_entry',1);self.put('terminal_directory_context_valid',1)
  self.put('hardware_active',0,1);self.put('vector_active',0,1)
 def context(self):return bytes(self.uc.mem_read(self.symbols['terminal_directory_context'],496))
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
 binary=a.terminal.resolve();manifest=json.loads((binary.parent/'manifest.json').read_text());assert manifest['experimental_directory_resource_owner'] and sha(binary)==manifest['binary_sha256']
 for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True);cases=[]
 recipes=[('fold',b'test.dir',b'd:\\base\\test.dir',0,None,0),('slashes',b'test.dir',b'd:/base/test.dir',0,None,0),
 ('DOS-error',b'test.dir',b'',5,None,3),('relative-result',b'test.dir',b'TEST.DIR',0,None,4),('device',b'test.dir',b'D:\\CON.DIR',0,None,4),
 ('wildcard',b'test.dir',b'D:\\T*.DIR',0,None,4),('bad-drive',b'test.dir',b'1:\\TEST.DIR',0,None,4),
 ('over63',b'test.dir',b'D:\\'+b'ABCDEFG\\'*8+b'TEST.DIR',0,None,4),('unterminated-result',b'test.dir',b'X'*128,0,None,4),
 ('empty',b'',b'',0,None,1),('unterminated-input',b'A'*64,b'',0,None,1),('same-buffer',b'test.dir',b'',0,'same',1),
 ('overlap',b'test.dir',b'',0,'overlap',1),('source-wrap',b'test.dir',b'',0,'source-wrap',1),('output-wrap',b'test.dir',b'',0,'output-wrap',1)]
 for name,path,reply,error,mutation,want in recipes:
  m=Identity(binary,reply,error);blob=path.ljust(64,b'\0')+b'Z'*64;pointer=m.stage_near(blob);dest=pointer+64;args=[pointer,dest]
  if mutation=='same':args[1]=pointer
  elif mutation=='overlap':args[1]=pointer+1
  elif mutation=='source-wrap':args[0]=65535
  elif mutation=='output-wrap':args[1]=65535
  status=m.bank('_directory_identity_path',args);assert status==want,(name,status,want)
  actual=bytes(m.uc.mem_read(m.data_base+pointer,128));assert actual[:64]==blob[:64]
  if want:assert actual==blob
  else:assert actual[64:]==b'D:\\BASE\\TEST.DIR\0'+bytes(47)
  assert len(m.calls)==(0 if want==1 else 1),(name,m.calls)
  cases.append(dict(case='path-'+name,status=status,DOS_calls=len(m.calls),passed=True))
 for fault in ('none','invalid-context','different-entry','zero-entry','entry201','relative','device','wildcard','unterminated'):
  m=Identity(binary);m.configured();path=b'D:\\BASE\\TEST.DIR\0'+bytes(47);m.uc.mem_write(m.symbols['terminal_directory_context']+432,path)
  if fault=='invalid-context':m.put('terminal_directory_context_valid',0)
  elif fault=='different-entry':m.put('terminal_directory_entry',2)
  elif fault in ('zero-entry','entry201'):
   n=0 if fault=='zero-entry' else 201;m.put('terminal_directory_entry',n);m.put('terminal_directory_context',n)
  elif fault in ('relative','device','wildcard','unterminated'):
   text={'relative':b'TEST.DIR','device':b'D:\\CON','wildcard':b'D:\\T*.DIR','unterminated':b'A'*64}[fault];m.uc.mem_write(m.symbols['terminal_directory_context']+432,text.ljust(64,b'\0'))
  before=m.context();status=m.bank('_terminal_directory_account_identity',far=True)
  assert status==(m.offset('terminal_directory_context')+432 if fault=='none' else 0) and m.context()==before and not m.calls,(fault,status)
  if fault!='none':
   for previous_error in (0,7):
    m.put('directory_pending',1,1);m.put('directory_pending_count',3);m.put('terminal_exit_code',previous_error)
    m.uc.mem_write(m.symbols['directory_account_result']+12,struct.pack('<H',1))
    assert m.call('terminal_directory_flush_accounting')==1 and not m.calls
    assert m.get('directory_pending',1)==1 and m.get('directory_pending_count')==3 and m.get('terminal_exit_code')==(previous_error or 9)
    assert m.get('directory_account_status')==1 and m.get('directory_account_result')==1
  cases.append(dict(case='accounting-'+fault,refused=fault!='none',DOS_calls=0,passed=True))
 memory=inspect_terminal_memory(binary,binary.parent/'terminal.map');entries=Identity(binary).entries;header=struct.unpack_from('<14H',binary.read_bytes());start=header[4]*16
 for name,symbol,delta,value in [('wrong-account-target','terminal_directory_account_path_site',1,None),('wrong-account-argument','terminal_directory_account_argument_site',0,0x50)]:
  seg,offset=entries[symbol];at=start+(seg-0x1000)*16+offset+delta;data=bytearray(binary.read_bytes());value=data[at]^1 if value is None else value;assert data[at]!=value;data[at]=value
  target=out/(name+'.analysis.exe');target.write_bytes(data)
  try:inspect_terminal_memory(target,binary.parent/'terminal.map')
  except AssertionError:cases.append(dict(case=name,damaged_control_rejected=True,passed=True))
  else:raise AssertionError(name)
 result=dict(passed=True,binary_sha256=sha(binary),inputs=len(cases),cases=cases,memory=memory,original_inputs=[],
  sources={n:sha(ROOT/n) for n in ['standalone/check_directory_identity.py','standalone/dos_image.py','standalone/terminal_memory.py','src/terminal/directory_identity.c','src/terminal/directory_identity.h','src/config/terminal_preferences.c','src/terminal/directory_accounting.asm']},
  scope=__doc__+' Actual bank/resident path, context checks, ABI and early accounting refusals execute; only canonicalization replies/errors are modeled. Two synthetic damaged executables are inspected, never executed. Native child/CWD/accounting evidence is separate.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS',len(cases),'directory identity inputs')
if __name__=='__main__':main()
