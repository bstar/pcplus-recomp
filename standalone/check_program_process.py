#!/usr/bin/env python3
"""Linked C/assembly PROGRAM policy, explicit DOSkernel and environment memory."""
import hashlib,json,struct
from unicorn.x86_const import UC_X86_REG_AX,UC_X86_REG_DX
from check_process import Kernel,OUT
class Program(Kernel):
 def __init__(self,success=b'Z:\\COMMAND.COM',failure=2,**kwargs):
  super().__init__(program_image=True,**kwargs)
  self.success=success;self.failure=failure
  self.environment(b'COMSPEC=Z:\\COMMAND.COM\0PATH=Z:\\\0\0')
 def environment(self,data,paragraphs=None,signature=b'M',segment=0x7000):
  self.uc.mem_write(self.get('process_psp')*16+0x2c,struct.pack('<H',segment))
  if not segment:return
  paragraphs=paragraphs if paragraphs is not None else (len(data)+15)//16
  self.uc.mem_write((segment-1)*16,signature+b'\0\0'+struct.pack('<H',paragraphs))
  self.uc.mem_write(segment*16,data)
 def interrupt(self,u,number,unused):
  if number==0x21 and u.reg_read(UC_X86_REG_AX)==0x4b00:
   at=self.data_base+u.reg_read(UC_X86_REG_DX);path=[]
   while byte:=u.mem_read(at,1)[0]:path.append(byte);at+=1
   self.exec_error=0 if bytes(path)==self.success else self.failure
  return super().interrupt(u,number,unused)
 def program(self,command=b'CHILD.COM /Q',result=0x9200,command_at=0x9000,write_command=True):
  if write_command:self.uc.mem_write(self.data_base+command_at,command+b'\0')
  if result<=0xfff8:self.uc.mem_write(self.data_base+result,b'\xa5'*8)
  status=self.call('_program_execute',[command_at,result],limit=3000000)
  return status,bytes(self.uc.mem_read(self.data_base+result,8)) if result<=0xfff8 else None
def main():
 cases=[]
 def check(name,fn):n=fn();cases.append({'case':name,'inputs':n,'passed':True});print(name,'passed',n,flush=True)
 def comspec():
  for command in (b'CHILD.COM /Q',b'^M~^@UNCHANGED',b'X'*51,b'\x80\xff'):
   for child in (0,37,0x0123):
    p=Program(child_status=child,clobber=True);status,result=p.program(command)
    assert status==0 and struct.unpack('<4H',result)==(0,0,child,0x1000)
    assert p.children==[{'path':b'Z:\\COMMAND.COM','tail':b' /c '+command}]
  return 12
 check('COMSPEC-literal-command-no-TEXT-expansion-full-status-and-clobbered-context',comspec)
 def fallback():
  n=0
  for error in (2,3,5):
   p=Program(success=b'Z:\\COMMAND.COM',failure=error)
   p.environment(b'COMSPEC=C:\\ABSENT.COM\0PATH=D:\\ABSENT;;Z:\\\0\0')
   status,result=p.program();assert status==0
   assert [c['path'] for c in p.children]==[b'C:\\ABSENT.COM',b'COMMAND.COM',b'D:\\ABSENT\\COMMAND.COM',b'Z:\\COMMAND.COM'];n+=1
  for error in (8,10,11,13):
   p=Program(success=None,failure=error);status,result=p.program()
   assert status==3 and struct.unpack('<4H',result)[:3]==(3,error,0)
   assert len(p.children)==1;n+=1
  for env in (b'PATH=Z:\\\0\0',b'COMSPEC=\0PATH=Z:\\\0\0',b'comspec=BAD.COM\0PATH=Z:\\\0\0'):
   p=Program();p.environment(env);assert p.program()[0]==0
   assert [c['path'] for c in p.children]==[b'COMMAND.COM',b'Z:\\COMMAND.COM'];n+=1
  for entry,wanted in [(b'Z:',b'Z:COMMAND.COM'),(b'.\\TOOLS',b'.\\TOOLS\\COMMAND.COM'),(b'C:/TOOLS/',b'C:/TOOLS/COMMAND.COM')]:
   p=Program(success=wanted);p.environment(b'PATH='+entry+b'\0\0');assert p.program()[0]==0
   assert [c['path'] for c in p.children]==[b'COMMAND.COM',wanted];n+=1
  p=Program(success=b'COMMAND.COM');p.environment(b'\0\0');assert p.program()[0]==0 and len(p.children)==1;n+=1
  p=Program(success=b'COMMAND.COM');p.environment(b'',segment=0);assert p.program()[0]==0;n+=1
  p=Program(success=None);status,result=p.program();assert status==3 and struct.unpack('<4H',result)[:3]==(3,2,0);n+=1
  return n
 check('native-errno-equivalent-DOS2-3-5-fallback-PATH-relative-forms-case-sensitive-names-and-missing-processor',fallback)
 def environments():
  n=0
  for raw,paragraphs,signature in [(b'X'*16,1,b'M'),(b'COMSPEC=X'*2,1,b'M'),(b'A=ONE\0' + b'X'*10,1,b'M'),(b'\0\0',0,b'M'),(b'\0\0',1,b'Q')]:
   p=Program();p.environment(raw,paragraphs,signature)
   status,result=p.program();assert status==5 and struct.unpack('<4H',result)==(5,0,0,0) and not p.calls;n+=1
  p=Program();p.environment(b'COMSPEC='+b'X'*128+b'\0\0');assert p.program()[0]==5 and not p.calls;n+=1
  # A syntactically complete64K allocation still has bounded field/candidate reads.
  p=Program(success=b'COMMAND.COM');p.environment(b'PATH='+b'X'*(65536-7)+b'\0\0',4096)
  assert p.program()[0]==0 and len(p.children)==1;n+=1
  # Final valid PATH candidate127 chars fits; one more char must be skipped.
  for prefix,accepted in [(b'X'*115,True),(b'X'*115+b'\\',True),(b'X'*116,False)]:
   wanted=prefix+(b'' if prefix.endswith(b'\\') else b'\\')+b'COMMAND.COM'
   p=Program(success=wanted);p.environment(b'PATH='+prefix+b'\0\0');status,_=p.program()
   assert status==(0 if accepted else 3) and len(p.children)==(2 if accepted else 1);n+=1
  return n
 check('owned-environment-MCB-string-terminator-and-128-byte-path-capacity-bounds',environments)
 def arguments():
  n=0
  for command in (b'',b'X'*52,b'A\rB',b'A\nB'):
   p=Program();status,result=p.program(command);assert status==1 and result==b'\xa5'*8 and not p.calls;n+=1
  for result in (0,0xfff9):
   p=Program();status,_=p.program(result=result);assert status==1 and not p.calls;n+=1
  for offset in (0xfffe,0xffff):
   p=Program();p.uc.mem_write(p.data_base+offset,b'X'*(65536-offset))
   status,result=p.program(command_at=offset,write_command=False);assert status==1 and result==b'\xa5'*8 and not p.calls;n+=1
  for offset in range(10):
   p=Program();p.uc.mem_write(p.data_base+0x9000,b'CHILD.COM\0');before=bytes(p.uc.mem_read(p.data_base+0x9000,20))
   status=p.call('_program_execute',[0x9000,0x9000+offset]);assert status==1 and bytes(p.uc.mem_read(p.data_base+0x9000,20))==before and not p.calls;n+=1
  p=Program();p.put('process_busy',1);status,result=p.program();assert status==4 and struct.unpack('<4H',result)==(4,0,0,0) and not p.calls;n+=1
  return n
 check('near-arguments-overlap-wrap-long-command-CR-LF-and-busy-before-child',arguments)
 proof={'passed':True,'inputs':sum(c['inputs'] for c in cases),'cases':cases,'binary_sha256':hashlib.sha256((OUT/'PROGRAM.EXE').read_bytes()).hexdigest(),'scope':'Actual linked C/8086 COMSPEC/environment/PATH policy and maintainedEXEC backend. Synthetic parentMCB/environment and explicitDOSkernel callbacks only; no product service replaced. Missing-processor/path-order tested independently of DOSBoxvirtualCOMMAND.COM. Native recovered executor is a separate exact-byte diagnostic; live UI/UART handoff not included.'}
 (OUT/'program-checks.json').write_text(json.dumps(proof,indent=2)+'\n');print('PROGRAM policy:',proof['inputs'],'inputs passed')
if __name__=='__main__':main()
