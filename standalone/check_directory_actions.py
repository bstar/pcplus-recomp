#!/usr/bin/env python3
"""Actual linked directory C/ASM accounting; replacement and DOS calendar modeled."""
import argparse,hashlib,json,random,struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import (UC_X86_REG_AX,UC_X86_REG_BX,UC_X86_REG_CX,UC_X86_REG_DX,UC_X86_REG_ES,UC_X86_REG_DS,UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI,UC_X86_REG_SP,UC_X86_REG_IP,UC_X86_REG_EFLAGS)
from check_terminal_options import Options
ROOT=Path(__file__).resolve().parents[1];BINARY=ROOT/'build/terminal/TERMINAL.EXE';MAP=ROOT/'build/terminal/terminal.map'
def patch(raw,date,delta):
 year,month,day=date;out=bytearray(raw);out[61:70]=f'{month:02}/{day:02}/{year%100:02}'.encode()+b'\0';struct.pack_into('<H',out,70,(int.from_bytes(raw[70:72],'little')+delta)&65535);return bytes(out)
class Actions(Options):
 def __init__(self):
  super().__init__(BINARY,MAP);self.calls=[];self.calendar=(2026,10,17);self.calendar_calls=0;self.status=0;self.installed=1
  self.path=self.offset('terminal_directory_path');self.baseline=self.offset('terminal_directory_plan')+100;self.result=self.offset('directory_account_result');self.other=self.offset('screen_attribute_cells')
  self.uc.mem_write(self.data_base+self.path,b'C:\\SUB\\TEST.DIR\0');self.put('terminal_directory_entry',3)
  self.raw=random.Random(201).randbytes(114);self.uc.mem_write(self.data_base+self.baseline,self.raw);self.put('terminal_option_mask',64)
  self.uc.hook_add(UC_HOOK_CODE,self.replacement)
 def interrupt(self,uc,number,unused):
  if number==0x21 and uc.reg_read(UC_X86_REG_AX)>>8==0x60 and '_directory_storage_result' in self.symbols:
   source=uc.reg_read(UC_X86_REG_DS)*16+uc.reg_read(UC_X86_REG_SI)
   path=bytes(uc.mem_read(source,64)).split(b'\0')[0]
   assert path==b'C:\\SUB\\TEST.DIR'
   uc.mem_write(uc.reg_read(UC_X86_REG_ES)*16+uc.reg_read(UC_X86_REG_DI),path+b'\0')
   uc.reg_write(UC_X86_REG_AX,0);uc.reg_write(UC_X86_REG_EFLAGS,uc.reg_read(UC_X86_REG_EFLAGS)&~1);return
  if number!=0x21 or uc.reg_read(UC_X86_REG_AX)>>8!=0x2a:raise AssertionError('Unexpected DOS/BIOS IO during directory actions')
  year,month,day=self.calendar;uc.reg_write(UC_X86_REG_CX,year);uc.reg_write(UC_X86_REG_DX,month<<8|day);uc.reg_write(UC_X86_REG_AX,0x2a00);self.calendar_calls+=1
 def cstring(self,offset):return bytes(self.uc.mem_read(self.data_base+offset,64)).split(b'\0',1)[0]
 def replacement(self,uc,address,size,unused):
  if address!=self.symbols['_directory_replace_record']:return
  sp=uc.reg_read(UC_X86_REG_SP);ret,target,stage,backup,entry,expected,replacement,result=struct.unpack('<8H',uc.mem_read(self.data_base+sp,16))
  assert self.cstring(target)==b'C:\\SUB\\TEST.DIR' and self.cstring(stage)==b'C:\\SUB\\PCPSTG.$$$' and self.cstring(backup)==b'C:\\SUB\\PCPBAK.$$$' and entry==3
  self.calls.append({'expected':bytes(uc.mem_read(self.data_base+expected,114)),'replacement':bytes(uc.mem_read(self.data_base+replacement,114)),'entry':entry,'result':result})
  if result:
   uc.mem_write(self.data_base+result,struct.pack('<10H',self.status,5 if self.status else 0,0,5 if self.status==13 else 0,0,23050,self.installed,int(self.status==13),0,23050))
  uc.reg_write(UC_X86_REG_AX,self.status);uc.reg_write(UC_X86_REG_SP,sp+2);uc.reg_write(UC_X86_REG_IP,ret)
 def baseline_bytes(self):return bytes(self.uc.mem_read(self.data_base+self.baseline,114))
 def save(self,date=(2026,10,17),delta=1,result=None,arguments=None):
  self.uc.reg_write(UC_X86_REG_ES,self.ds)
  args=[self.path,3,self.baseline,*date,delta,self.result if result is None else result]
  status=self.call('_directory_save_accounting',args if arguments is None else arguments,limit=300000)
  for reg,want in ((UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678)):assert self.uc.reg_read(reg)==want
  return status
 def note(self):
  saved={UC_X86_REG_AX:0xabcd,UC_X86_REG_BX:0x3456,UC_X86_REG_CX:0x4567,UC_X86_REG_DX:0x5678,UC_X86_REG_ES:0x7777}
  for reg,value in saved.items():self.uc.reg_write(reg,value)
  result=self.call('terminal_directory_note_connected');assert result==0xabcd
  for reg,value in saved.items():assert self.uc.reg_read(reg)==value
 def flush(self):return self.call('terminal_directory_flush_accounting',limit=400000)

def main():
 global BINARY,MAP
 parser=argparse.ArgumentParser();parser.add_argument('--binary',type=Path,default=BINARY);parser.add_argument('--map',type=Path,default=MAP);parser.add_argument('--expect-sha256');args=parser.parse_args();BINARY,MAP=args.binary,args.map
 digest=hashlib.sha256(BINARY.read_bytes()).hexdigest()
 if args.expect_sha256:assert digest==args.expect_sha256
 cases=[]
 def done(name,count):cases.append({'case':name,'inputs':count,'passed':True});print(name,'passed',count,flush=True)
 for status,installed in ((0,1),(13,1),(6,0),(8,0),(12,0)):
  for date,delta in (((2026,10,17),3),((2000,2,29),65535)):
   c=Actions();c.status=status;c.installed=installed;prefix=bytes(c.uc.mem_read(c.symbols['terminal_directory_plan'],100));assert c.save(date,delta)==status
   assert len(c.calls)==1 and c.calls[0]['expected']==c.raw and c.calls[0]['replacement']==patch(c.raw,date,delta)
   assert c.baseline_bytes()==(patch(c.raw,date,delta) if installed else c.raw)
   assert bytes(c.uc.mem_read(c.symbols['terminal_directory_plan'],100))==prefix
   assert struct.unpack('<H',c.uc.mem_read(c.data_base+c.result,2))[0]==status
 done('actual-C-and-patch-ASM-install-status-calendar-modular-count-and-baseline-commit',10)
 badargs=[(0,0),(1,0),(1,201),(2,0),(2,65500),(7,65530)]
 for index,value in badargs:
  c=Actions();arguments=[c.path,3,c.baseline,2026,10,17,1,c.result];arguments[index]=value
  before=c.baseline_bytes();assert c.save(arguments=arguments)==1 and c.baseline_bytes()==before and not c.calls
 for source in ('baseline','path'):
  c=Actions();assert c.save(result=c.baseline if source=='baseline' else c.path)==1 and c.baseline_bytes()==c.raw and not c.calls
 for date in ((1979,1,1),(2100,1,1),(2026,2,29),(2000,2,30),(2026,13,1)):
  c=Actions();assert c.save(date)==1 and c.baseline_bytes()==c.raw and not c.calls
 c=Actions();assert c.save(result=0)==0 and c.baseline_bytes()==patch(c.raw,c.calendar,1)
 done('near-C-null-extent-alias-invalid-date-and-optional-result',len(badargs)+8)
 c=Actions();c.put('terminal_option_mask',0);c.note();assert c.calendar_calls==0 and not c.get('directory_pending',1) and not c.get('directory_pending_count')
 assert c.flush()==0 and not c.calls
 done('non-directory-session-never-captures-calendar-or-persists',1)
 c=Actions();c.note();c.calendar=(2000,2,29);c.note();assert c.calendar_calls==2 and c.get('directory_pending_count')==2 and c.get('directory_pending',1)==1 and not c.calls
 assert c.flush()==0 and len(c.calls)==1 and c.calls[0]['replacement']==patch(c.raw,c.calendar,2)
 assert c.baseline_bytes()==patch(c.raw,c.calendar,2) and c.get('directory_pending_count')==0 and not c.get('directory_pending',1)
 assert c.flush()==0 and len(c.calls)==1
 done('RAM-only-success-notes-capture-latest-date-and-flush-one-aggregate-delta-once',1)
 for old_exit in (0,6):
  c=Actions();c.note();c.note();c.status=8;c.installed=0;c.put('terminal_exit_code',old_exit)
  assert c.flush()==1 and c.get('terminal_exit_code')==(9 if old_exit==0 else old_exit) and c.baseline_bytes()==c.raw
  assert c.get('directory_pending_count')==2 and c.get('directory_pending',1)==1
  c.status=0;c.installed=1;assert c.flush()==0 and c.baseline_bytes()==patch(c.raw,c.calendar,2) and len(c.calls)==2
  assert c.flush()==0 and len(c.calls)==2
 done('failed-install-preserves-baseline-pending-delta-and-existing-errorlevel-until-successful-retry',2)
 c=Actions();c.note();c.note();c.status=13;c.installed=1
 assert c.flush()==1 and c.baseline_bytes()==patch(c.raw,c.calendar,2) and c.get('terminal_exit_code')==9
 assert not c.get('directory_pending',1) and c.get('directory_pending_count')==0
 assert c.flush()==0 and len(c.calls)==1 and c.baseline_bytes()==patch(c.raw,c.calendar,2)
 done('installed-cleanup-warning-consumes-pending-and-cannot-double-increment',1)
 c=Actions();c.put('directory_pending_count',65535);c.note();assert c.get('directory_pending_count')==0 and c.get('directory_pending',1)==1
 assert c.flush()==0 and c.calls[0]['replacement']==patch(c.raw,c.calendar,0) and not c.get('directory_pending',1)
 done('pending-delta-wrap-preserves-original-modular-counter-and-updates-date',1)
 if '_directory_storage_result' in Actions().symbols:
  c=Actions();c.note();c.status=13;c.installed=1
  assert c.flush()==1 and not c.get('directory_pending',1)
  baseline=c.baseline_bytes();assert len(c.calls)==1
  c.note();assert c.get('directory_pending_count')==1
  assert c.flush()==1 and c.get('directory_pending',1)==1 and c.get('directory_pending_count')==1
  assert c.baseline_bytes()==baseline and len(c.calls)==1
  raw=bytes(c.uc.mem_read(c.symbols['directory_account_result'],20))
  assert raw==struct.pack('<H',15)+bytes(18),'Refusal leaked a previous installed flag'
  c.put('process_psp',c.base_segment-16);c.put('process_keep_paragraphs',16);c.put('process_minimum_paragraphs',16)
  path=c.stage_near(b'C:\\CHILD.COM\0'+bytes(3)+b'\xa5'*8);result=path+16
  assert c.call('_process_run',[path,0,result],limit=500000)==4
  assert bytes(c.uc.mem_read(c.data_base+result,8))==b'\xa5'*8 and not c.get('process_busy')
  done('held-owner-refuses-new-accounting-without-stale-installed-flag-and-blocks-EXEC-before-DOS',2)
 # Reuse the declared UART/BIOS-keyboard/tick model to execute real controller
 # transitions; no controller, transport, matcher or note callback is skipped.
 import check_transport
 check_transport.BINARY,check_transport.MAP=BINARY,MAP
 from check_connection import Connection
 class DirectoryConnection(Connection):
  def __init__(self):
   self.calendar_calls=0;super().__init__();self.put('terminal_option_mask',80)
  def interrupt(self,uc,number,data):
   if number==0x21 and uc.reg_read(UC_X86_REG_AX)>>8==0x2a:
    self.calendar_calls+=1;uc.reg_write(UC_X86_REG_CX,2026);uc.reg_write(UC_X86_REG_DX,0x0a11);uc.reg_write(UC_X86_REG_AX,0x2a00);return
   return super().interrupt(uc,number,data)
 m=DirectoryConnection();m.connect();assert m.calendar_calls==1 and m.get('directory_pending_count')==1
 m.receive(b'CONNECT repeated online text');m.poll(10);assert m.calendar_calls==1 and m.get('directory_pending_count')==1
 m.carrier=False;m.poll();assert m.state()==0 and m.calendar_calls==1
 m.carrier=True;m.connect();assert m.calendar_calls==2 and m.get('directory_pending_count')==2
 m=DirectoryConnection();m.put('terminal_directory_mode',1);assert m.call('terminal_connection_prepare')==0;m.start()
 assert m.state()==6 and m.calendar_calls==1 and m.get('directory_pending_count')==1
 m.receive(b'ordinary direct text');m.poll(10);assert m.calendar_calls==1
 m.carrier=False;m.poll();assert m.state()==0;m.carrier=True;m.start()
 assert m.state()==6 and m.calendar_calls==2 and m.get('directory_pending_count')==2
 m=DirectoryConnection();m.start();m.waiting();m.receive(b'BUSY');m.poll(40)
 assert m.state()==0 and m.calendar_calls==0 and m.get('directory_pending_count')==0
 m=DirectoryConnection();m.cts=False;m.start();m.poll(120)
 assert m.state()==0 and m.calendar_calls==0 and m.get('directory_pending_count')==0
 done('actual-MODEM-DIRECT-success-transitions-note-once-per-connection-and-never-on-failure',4)
 assert hashlib.sha256(BINARY.read_bytes()).hexdigest()==digest
 result={'passed':True,'binary_sha256':digest,'inputs':sum(case['inputs'] for case in cases),'cases':cases,'scope':'Actual linked C save helpers, pure date/count patch ASM and deferred accounting ASM. Transactional replacement entry, DOS calendar and (for the guarded variant) DOS canonicalization are modeled. Guard, reservation registry and bank adapters execute normally. Held-owner EXEC refusal must return before any DOS memory/EXEC call; result stays exact. Additional MODEM/DIRECT transitions use declared UART/keyboard/tick models. Real DOS backend is tested separately.'}
 output=BINARY.parent/'directory-actions-checks.json';output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
