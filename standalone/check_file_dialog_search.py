#!/usr/bin/env python3
"""Execute linked listing lifecycle with modeled DOS searches and a near-memory canary."""
import argparse,json,struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
from check_directory_identity import Identity,ROOT,sha

class Search(Identity):
 def __init__(self,binary,count=22,error=0):
  super().__init__(binary);self.dta=(0x7000,0x100);self.foreign=self.dta;self.index=0;self.count=count;self.error=error;self.ready=1;self.searches=[]
  self.returns={self.symbols[n]:v for n,v in [('_recording_ui_ready',1),('_path_session_quarantined',0),('_recording_terminal_inspect',0),('_capture_file_child_handle',0xffff),('_printer_device_child_handle',0xffff)]}
  self.uc.hook_add(UC_HOOK_CODE,self.boundary)
  self.put('csi_column_count',80);self.put('ui_window_rows',25)
  self.state=self.symbols['_terminal_file_dialog_state']
  self.near_size=self.offset('terminal_stack_top')-self.stack_bytes
  self.near=bytes(self.uc.mem_read(self.data_base,self.near_size))
 def boundary(self,u,address,size,data):
  if address not in self.returns:return
  value=self.ready if address==self.symbols['_recording_ui_ready'] else self.returns[address]
  sp=u.reg_read(UC_X86_REG_SP);ss=u.reg_read(UC_X86_REG_SS);ip,cs=struct.unpack('<HH',bytes(u.mem_read(ss*16+sp,4)))
  u.reg_write(UC_X86_REG_AX,value);u.reg_write(UC_X86_REG_SP,sp+4);u.reg_write(UC_X86_REG_CS,cs);u.reg_write(UC_X86_REG_IP,ip)
 def interrupt(self,u,n,data):
  ax=u.reg_read(UC_X86_REG_AX);ah=ax>>8;assert n==0x21 and ah in [0x2f,0x1a,0x4e,0x4f],(n,hex(ax))
  if ah==0x2f:u.reg_write(UC_X86_REG_ES,self.dta[0]);u.reg_write(UC_X86_REG_BX,self.dta[1]);return
  if ah==0x1a:self.dta=(u.reg_read(UC_X86_REG_DS),u.reg_read(UC_X86_REG_DX));return
  assert self.dta!=self.foreign
  if ah==0x4e:
   self.index=0;at=u.reg_read(UC_X86_REG_DS)*16+u.reg_read(UC_X86_REG_DX)
   self.spec=bytes(u.mem_read(at,68)).split(b'\0',1)[0];assert u.reg_read(UC_X86_REG_CX)==0x10
  else:self.index+=1
  self.searches.append(ah)
  error=self.error or (18 if self.index>=self.count else 0)
  if not error:
   dta=bytearray(43);dta[30:38]=('F%02d.TXT'%self.index).encode()+b'\0'
   struct.pack_into('<HHI',dta,22,(14<<11)|(32<<5)|5,((1993-1980)<<9)|(7<<5)|9,self.index+1)
   u.mem_write(self.dta[0]*16+self.dta[1],bytes(dta))
  u.reg_write(UC_X86_REG_AX,error);flags=u.reg_read(UC_X86_REG_EFLAGS);u.reg_write(UC_X86_REG_EFLAGS,flags|1 if error else flags&~1)
 def event(self,event,key=0):
  before=len(self.searches);result=self.bank('_file_dialog_event',[event,key,0,0xb800],far=True)
  assert len(self.searches)-before<=1 and self.dta==self.foreign
  assert bytes(self.uc.mem_read(self.data_base,self.near_size))==self.near,'Listing wrote outside FILE_CODE/stack'
  return result
 def head(self):return struct.unpack('<13H',bytes(self.uc.mem_read(self.state,26)))
 def load(self):
  for _ in range(150):
   if self.head()[2]!=2:return
   self.event(3)
  raise AssertionError('Search did not reach page/notice')

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ['terminal','output']:p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 binary=a.terminal.resolve();m=json.loads(binary.with_name('manifest.json').read_text());assert m['experimental_file_directory'] and sha(binary)==m['binary_sha256']
 cases=[]
 for spec,want in [(b'',b'*.*'),(b'FILES\\',b'FILES\\*.*'),(b'C:',b'C:*.*'),(b'FILES\\*.TXT',b'FILES\\*.TXT'),(b'X'*63+b'\\',b'X'*63+b'\\*.*')]:
  s=Search(binary);s.event(0);s.uc.mem_write(s.state+26,spec.ljust(64,b' ')+b'\0');s.event(1,13)
  s.ready=0;prior=s.head();s.event(3);assert s.head()==prior and not s.searches;s.ready=1
  s.load();assert s.spec==want and s.head()[2]==3 and s.head()[7:10]==(15,1,1)
  frame=bytes(s.uc.mem_read(0xb8000,4000));assert frame[(4*80+22)*2:(4*80+29)*2:2]==b'F00.TXT'
  s.event(1,32);s.load();assert s.head()[7:10]==(7,0,0)
  frame=bytes(s.uc.mem_read(0xb8000,4000));assert frame[(4*80+22)*2:(4*80+29)*2:2]==b'F15.TXT'
  assert frame[(11*80+22)*2:(11*80+60)*2:2]==b' '*38
  assert s.event(1,32)==0 and not s.head()[1]
  assert s.uc.mem_read(s.symbols['_file_find_storage'],2)==b'\0\0'
  cases.append(dict(spec=spec.decode(),passed=True,search_calls=len(s.searches)))
 for error in [2,3,5,18]:
  s=Search(binary,error=error);s.event(0);s.event(1,13);s.load();assert s.head()[2]==4 and s.head()[12]==error
  text=bytes(s.uc.mem_read(0xb8000+1664,36))[::2]
  want=b'File search failed' if error==5 else b'File(s) not found'
  assert text.startswith(want),(error,text)
  assert s.event(1,32)==0 and s.uc.mem_read(s.symbols['_file_find_storage'],2)==b'\0\0';cases.append(dict(error=error,passed=True))
 for refusal in ['busy','geometry','foreign-owner']:
  s=Search(binary)
  if refusal=='busy':s.ready=0
  elif refusal=='geometry':s.put('csi_column_count',132);s.near=bytes(s.uc.mem_read(s.data_base,s.near_size))
  else:s.uc.mem_write(s.symbols['_file_find_storage'],b'\1\0')
  s.event(0);assert s.head()[2]==4 and not s.searches
  want=b'View unavailable' if refusal=='geometry' else b'Operation pending'
  assert bytes(s.uc.mem_read(0xb8000+1664,36))[::2].startswith(want)
  s.event(1,27);assert s.uc.mem_read(s.symbols['_file_find_storage'],2)==(b'\1\0' if refusal=='foreign-owner' else b'\0\0')
  cases.append(dict(refusal=refusal,passed=True))
 for stop in [1,4]:
  s=Search(binary);s.event(0);s.event(1,13);s.event(3);assert s.head()[11]==1
  assert s.event(stop,27)==0 and s.uc.mem_read(s.symbols['_file_find_storage'],2)==b'\0\0';cases.append(dict(cancel_event=stop,passed=True))
 for rows,count in [(25,1),(25,15),(25,16),(50,40),(50,41)]:
  s=Search(binary,count=count);s.put('ui_window_rows',rows);s.near=bytes(s.uc.mem_read(s.data_base,s.near_size))
  s.event(0);s.event(1,13);s.load();head=s.head()
  assert head[7]==min(count,rows-10) and head[8]==int(count>rows-10),(rows,count,head)
  frame=bytes(s.uc.mem_read(0xb8000,rows*160));assert frame[((rows-4)*80+20)*2:((rows-4)*80+20)*2+2]==bytes([200,7])
  s.event(1,27);cases.append(dict(physical_rows=rows,count=count,passed=True))
 sources=['standalone/check_file_dialog_search.py','standalone/check_directory_identity.py','standalone/dos_image.py','standalone/terminal_memory.py']
 out.mkdir(parents=True);(out/'result.json').write_text(json.dumps(dict(passed=True,cases=cases,binary_sha256=sha(binary),sources={n:sha(ROOT/n) for n in sources},scope=__doc__+' Actual relocated bank code, one DOS search per event, DTA restoration, whole non-stack DGROUP unchanged, page contents/clear, default and maximum specification, readiness pause, failures and cancel/stop. DOS records and owner-readiness replies are explicit boundary models; actual serial/DOS tests remain separate.'),indent=2)+'\n');print('PASS',len(cases),'linked search/near-memory cases')
if __name__=='__main__':main()
