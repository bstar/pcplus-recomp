#!/usr/bin/env python3
"""Run linked maintained EXEC instructions with a declared DOS kernel model."""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn import UC_HOOK_INTR
from unicorn.x86_const import (UC_X86_REG_AX,UC_X86_REG_BX,UC_X86_REG_CX,
 UC_X86_REG_DX,UC_X86_REG_SI,UC_X86_REG_DI,UC_X86_REG_DS,UC_X86_REG_ES,
 UC_X86_REG_SS,UC_X86_REG_SP,UC_X86_REG_BP,UC_X86_REG_EFLAGS)
from dos_image import DosImage
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/process'
class Kernel(DosImage):
 def __init__(self,resize_error=0,exec_error=0,child_status=37,clobber=False,program_image=False):
  super().__init__(OUT/('PROGRAM.EXE' if program_image else 'PROCESS.EXE'),OUT/('program.map' if program_image else 'process.map'))
  self.calls=[];self.children=[];self.resize_error=resize_error;self.exec_error=exec_error
  self.child_status=child_status;self.clobber=clobber
  self.uc.hook_add(UC_HOOK_INTR,self.interrupt)
  self.put('process_psp',0xff0);self.put('process_keep_paragraphs',0x1000);self.put('process_minimum_paragraphs',0x1000)
 def set_carry(self,carry):
  f=self.uc.reg_read(UC_X86_REG_EFLAGS);self.uc.reg_write(UC_X86_REG_EFLAGS,(f|1) if carry else (f&~1))
 def interrupt(self,u,number,_):
  assert number==0x21,('Unexpected interrupt',number)
  ax=u.reg_read(UC_X86_REG_AX);function=ax>>8;self.calls.append(function)
  if function==0x4a:
   assert u.reg_read(UC_X86_REG_ES)==self.get('process_psp')
   assert u.reg_read(UC_X86_REG_BX)==self.get('process_keep_paragraphs')
   u.reg_write(UC_X86_REG_AX,self.resize_error);self.set_carry(bool(self.resize_error));return
  if function==0x29:
   assert ax==0x2901 and u.reg_read(UC_X86_REG_ES)==self.ds
   di=u.reg_read(UC_X86_REG_DI)
   assert di in (self.offset('process_fcb1'),self.offset('process_fcb2'))
   # A DOS-parser boundary fixture only: actual FCB parsing is tested in DOS.
   u.mem_write(self.data_base+di,bytes(range(16)));return
  if function==0x4b:
   assert ax==0x4b00
   assert u.reg_read(UC_X86_REG_ES)==u.reg_read(UC_X86_REG_DS)==self.ds
   address=self.data_base+u.reg_read(UC_X86_REG_BX)
   env,tail,tailseg,fcb1,fcb1seg,fcb2,fcb2seg=struct.unpack('<7H',u.mem_read(address,14))
   assert env==0 and tailseg==fcb1seg==fcb2seg==self.ds
   assert (tail,fcb1,fcb2)==tuple(self.offset(n) for n in ('process_command_tail','process_fcb1','process_fcb2'))
   n=u.mem_read(self.data_base+tail,1)[0]
   command=bytes(u.mem_read(self.data_base+tail+1,n+1));assert n<=126 and command[-1:]==b'\r'
   path=[];at=self.data_base+u.reg_read(UC_X86_REG_DX)
   while byte:=u.mem_read(at,1)[0]:path.append(byte);at+=1
   self.children.append({'path':bytes(path),'tail':command[:-1]})
   if self.clobber:
    for reg,value in [(UC_X86_REG_DS,0x2222),(UC_X86_REG_ES,0x3333),(UC_X86_REG_SS,0x4444),(UC_X86_REG_SP,0x8888),(UC_X86_REG_BP,0x1111),(UC_X86_REG_SI,0x5555),(UC_X86_REG_DI,0x6666),(UC_X86_REG_BX,0x7777),(UC_X86_REG_CX,0x9999),(UC_X86_REG_DX,0xaaaa)]:u.reg_write(reg,value)
   u.reg_write(UC_X86_REG_AX,self.exec_error);self.set_carry(bool(self.exec_error));return
  if function==0x4d:
   u.reg_write(UC_X86_REG_AX,self.child_status);return
  raise AssertionError(('Unexpected DOS call',hex(ax)))
 def run(self,path=b'CHILD.COM',tail=b' /Q SYNTH',result=0x9200,path_at=0x9000,tail_at=0x9100):
  if path is not None:self.uc.mem_write(self.data_base+path_at,path+b'\0')
  if tail is not None:self.uc.mem_write(self.data_base+tail_at,tail+b'\0')
  if result:self.uc.mem_write(self.data_base+result,b'\xa5'*8)
  self.uc.reg_write(UC_X86_REG_ES,0x4321)
  answer=self.call('process_run',[path_at,tail_at,result],limit=100000)
  for reg,value in [(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678),(UC_X86_REG_DS,self.ds),(UC_X86_REG_SS,self.ds),(UC_X86_REG_ES,0x4321)]:assert self.uc.reg_read(reg)==value,('ABI',reg)
  return answer,bytes(self.uc.mem_read(self.data_base+result,8)) if result else None

def main():
 global OUT
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--banked',action='store_true');args=parser.parse_args()
 OUT=ROOT/('build/process-bank' if args.banked else 'build/process')
 manifest=json.loads((OUT/'manifest.json').read_text())
 for name,digest in manifest['sources'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
 cases=[]
 def check(name,fn):n=fn();cases.append({'case':name,'inputs':n,'passed':True});print(name,'passed',n,flush=True)
 def normal():
  for clobber in (False,True):
   for status in (0,37,255,0x0123,0x032a):
    k=Kernel(child_status=status,clobber=clobber);answer,result=k.run()
    assert answer==0 and struct.unpack('<4H',result)==(0,0,status,0x1000)
    assert k.calls==[0x4a,0x29,0x29,0x4b,0x4d] and k.children==[{'path':b'CHILD.COM','tail':b' /Q SYNTH'}]
    assert k.get('process_memory_released')==1 and not k.get('process_busy')
  return 10
 check('actual-instructions-DOS-parameter-block-inherited-env-child-status-and-clobbered-context',normal)
 def errors():
  n=0
  for error in (2,3,5,8,10,11):
   k=Kernel(exec_error=error,clobber=True);answer,result=k.run()
   assert answer==3 and struct.unpack('<4H',result)==(3,error,0,0x1000)
   assert k.calls==[0x4a,0x29,0x29,0x4b] and not k.get('process_busy');n+=1
  for error in (7,8,9):
   k=Kernel(resize_error=error);answer,result=k.run()
   assert answer==2 and struct.unpack('<4H',result)==(2,error,0,0x1000)
   assert k.calls==[0x4a] and not k.children and not k.get('process_memory_released') and not k.get('process_busy');n+=1
  return n
 check('DOS-resize-and-EXEC-errors-preserve-first-error-no-stale-child-and-no-child-after-resize-failure',errors)
 def bounds():
  recipes=[dict(path=b''),dict(path=b'P'*128),dict(path=b'X\rY'),dict(path=b'X\nY'),dict(tail=b'T'*127),dict(tail=b'X\rY'),dict(tail=b'X\nY'),dict(path=None,path_at=0),dict(result=0xfff9)]
  for options in recipes:
   k=Kernel();result=options.get('result',0x9200)
   if result>0xfff8:options['result']=0 # Wrapping result supplied directly below.
   if result>0xfff8:
    k.uc.mem_write(k.data_base+0x9000,b'CHILD.COM\0');answer=k.call('process_run',[0x9000,0,result]);assert answer==1
   else:
    answer,stored=k.run(**options);assert answer==1 and stored==b'\xa5'*8
   assert not k.calls and not k.children
  for field,value in [('process_psp',0),('process_keep_paragraphs',15),('process_keep_paragraphs',0xfff),('process_minimum_paragraphs',0)]:
   k=Kernel();k.put(field,value);answer,stored=k.run();assert answer==1 and stored==b'\xa5'*8 and not k.calls
  k=Kernel();k.put('process_busy',1);answer,stored=k.run();assert answer==4 and stored==b'\xa5'*8 and not k.calls and k.get('process_busy')==1
  for path,tail in [(b'P',b''),(b'P'*127,b'T'*126),(b'\x80.APP',b'\x80\xff')]:
   k=Kernel();answer,result=k.run(path,tail);assert answer==0 and k.children[0]=={'path':path,'tail':tail}
  return len(recipes)+4+1+3
 check('empty-max-CP437-CR-LF-overlong-null-path-wrapping-result-and-invalid-host-state-before-IO',bounds)
 def aliases():
  n=0
  for source in ('path','tail'):
   for result in range(0x9000 if source=='path' else 0x9100,(0x9000 if source=='path' else 0x9100)+10):
    k=Kernel();k.uc.mem_write(k.data_base+0x9000,b'CHILD.COM\0');k.uc.mem_write(k.data_base+0x9100,b' /Q SYNTH\0')
    before=bytes(k.uc.mem_read(k.data_base+0x9000,0x200));answer=k.call('process_run',[0x9000,0x9100,result])
    assert answer==1 and bytes(k.uc.mem_read(k.data_base+0x9000,0x200))==before and not k.calls;n+=1
  for field in ('process_keep_paragraphs','process_command_tail','process_parameters','process_fcb1'):
   k=Kernel();result=k.offset(field);k.uc.mem_write(k.data_base+0x9000,b'CHILD.COM\0')
   before=bytes(k.uc.mem_read(k.data_base+result,8));answer=k.call('process_run',[0x9000,0,result])
   assert answer==1 and bytes(k.uc.mem_read(k.data_base+result,8))==before and not k.calls;n+=1
  for offset in (0xffff,0xfffe):
   k=Kernel();k.uc.mem_write(k.data_base+offset,b'X'*(0x10000-offset));answer,_=k.run(path=None,path_at=offset)
   assert answer==1 and not k.calls;n+=1
  k=Kernel();answer,result=k.run(path=b'P'*127,path_at=0xff80,result=0xff00)
  assert answer==0 and k.children[0]['path']==b'P'*127;n+=1
  k=Kernel();answer,result=k.run(result=0xfff8);assert answer==0 and struct.unpack('<4H',result)==(0,0,37,0x1000);n+=1
  return n
 check('near-region-aliases-owned-backend-state-last-byte-NUL-and-exact-64K-result-edge',aliases)
 def reuse():
  k=Kernel();assert k.run(tail=b'LONG PRIVATE STRING')[0]==0
  k.calls.clear();assert k.run(tail=None,tail_at=0,result=0)[0]==0
  assert k.calls==[0x29,0x29,0x4b,0x4d] and k.children[-1]['tail']==b''
  assert bytes(k.uc.mem_read(k.symbols['process_command_tail'],128))==b'\0\r'+bytes(126)
  k.exec_error=8;assert k.run()[0]==3;k.exec_error=0;assert k.run()[0]==0
  assert not k.get('process_busy') and k.get('process_child_status')==37
  return 4
 check('repeated-execution-resizes-once-optional-pointers-cleared-tail-and-failed-child-recovery',reuse)
 proof={'passed':True,'banked_process':args.banked,'inputs':sum(c['inputs'] for c in cases),'cases':cases,'binary_sha256':hashlib.sha256((OUT/'PROCESS.EXE').read_bytes()).hexdigest(),'checker_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'loader_sha256':hashlib.sha256((ROOT/'standalone/dos_image.py').read_bytes()).hexdigest(),'scope':'Actual linked maintained public near EXEC/bounds/context entry; optional far body. Only DOS4A/29/4B/4D kernel boundary modeled. Context-clobber model changes DS/ES/SS/SP/registers before real restoration instructions. Real DOS/FCB/child execution separately tested; no live UART handoff.'}
 (OUT/'checks.json').write_text(json.dumps(proof,indent=2)+'\n');print('Maintained process boundary:',proof['inputs'],'inputs passed')
if __name__=='__main__':main()
