#!/usr/bin/env python3
"""Execute linked external UI/baseline/queue lifecycle with declared service boundaries."""
import argparse,json,struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
from check_directory_identity import Identity
from build_path_session import ROOT,sha

class External(Identity):
 def __init__(self,binary):
  super().__init__(binary);self.ready=1;self.admission=0;self.execute_status=0;self.commands=[]
  self.uc.hook_add(UC_HOOK_CODE,self.boundary);self.state=self.symbols['_terminal_external_viewer_state']
  self.put('csi_column_count',80);self.put('ui_window_rows',25)
 def boundary(self,u,address,size,data):
  values={self.symbols['_recording_ui_ready']:self.ready,self.symbols['_external_program_queue']:self.admission}
  if address==self.symbols['_program_execute_external']:
   sp=u.reg_read(UC_X86_REG_SP);command,result=struct.unpack('<2H',u.mem_read(self.data_base+sp+4,4))
   self.commands.append(bytes(u.mem_read(self.data_base+command,114)).split(b'\0',1)[0])
   u.mem_write(self.data_base+result,struct.pack('<4H',self.execute_status,0,0,0));values[address]=self.execute_status
  if address not in values:return
  sp=u.reg_read(UC_X86_REG_SP);ip,cs=struct.unpack('<2H',u.mem_read(self.data_base+sp,4));u.reg_write(UC_X86_REG_AX,values[address]);u.reg_write(UC_X86_REG_SP,sp+4);u.reg_write(UC_X86_REG_CS,cs);u.reg_write(UC_X86_REG_IP,ip)
 def publish(self,command):
  image=bytearray(1264);image[0x35d:0x35d+len(command)]=command
  p=self.stage_near(bytes(image));assert self.bank('_hook_baseline_publish',[p,1],far=True)==0
 def call(self,name,args=()):return self.bank('_viewer_external_'+name,args,far=True)
 def event(self,event,key=0):return self.call('event',[event,key,0,0xb800])
 def words(self):return struct.unpack('<7H',self.uc.mem_read(self.state,14))
 def open(self,command=b'D:\\VTEST.COM'):
  self.publish(command);assert self.call('select')==1;assert self.event(0)==1
 def type(self,text):
  for c in text:assert self.event(1,c)==1

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ['terminal','output']:p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();binary=a.terminal.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();manifest=json.loads(binary.with_name('manifest.json').read_text());assert manifest['experimental_external_viewer'] and sha(binary)==manifest['binary_sha256']
 frozen=dict(manifest['sources']);names=['standalone/check_viewer_external_linked.py','standalone/check_directory_identity.py','standalone/dos_image.py'];frozen.update({n:sha(ROOT/n) for n in names})
 for n,h in frozen.items():assert sha(ROOT/n)==h,n
 cases=[]
 for name,command,want in [('no-baseline',None,0),('disabled',b'',0),('configured',b'D:\\VTEST.COM',1),('unterminated',b'X'*65,2)]:
  m=External(binary)
  if command is not None:m.publish(command)
  assert m.call('select')==want
  cases.append(dict(case=name,passed=True))
 for name,ready,key in [('Escape',1,27),('stop',1,None),('not-ready',0,13)]:
  m=External(binary);m.publish(b'D:\\VTEST.COM');assert m.call('select')==1;m.ready=ready;m.event(0)
  assert m.event(4) ==0 if key is None else m.event(1,key)==0
  assert m.call('queued')==0 and m.call('owned')==0 and not m.commands
  cases.append(dict(case=name,passed=True))
 for name,admission,changed,status in [('success',0,False,0),('queue-busy',2,False,0),('changed-baseline',0,True,0),('child-error',0,False,3)]:
  m=External(binary);m.open();m.type(b'ONE TWO');assert m.event(1,13)==0 and m.call('owned')==0 and m.call('queued')==1
  m.admission=admission;assert m.call('start')==admission
  if not admission:
   if changed:m.publish(b'D:\\OTHER.COM')
   m.execute_status=status;result=m.stage_near(bytes(8));actual=m.call('execute',[result]);assert actual==(1 if changed else status)
   assert m.commands==([] if changed else [b'D:\\VTEST.COM ONE TWO'])
  assert m.call('queued')==0
  cases.append(dict(case=name,passed=True))
 m=External(binary);m.open();m.event(1,13);m.call('cancel');assert m.call('queued')==0 and m.call('start')==1;cases.append(dict(case='cancel-queued',passed=True))
 m=External(binary);m.open();m.type(b'A'*49);assert m.words()[3:6]==(47,0,1);assert m.call('cursor')==0x0c48;m.event(1,13);assert m.call('queued')==1
 result=m.stage_near(bytes(8));assert m.call('execute',[result])==0 and m.commands==[b'D:\\VTEST.COM '+b'A'*48];cases.append(dict(case='full-parameter-latch',passed=True))
 out.mkdir();(out/'result.json').write_text(json.dumps(dict(passed=True,binary_sha256=sha(binary),cases=cases,sources=frozen,scope=__doc__+' Real linked8086 FILE_CODE and actual sealed baseline publication/copy. Recording readiness and PROGRAM queue/child calls are modeled far boundaries; no actual DOS child, hardware or whole PROGRAM acceptance.'),indent=2)+'\n');print('PASS',len(cases),'linked external lifecycle cases')
if __name__=='__main__':main()
