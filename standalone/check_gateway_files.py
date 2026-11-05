#!/usr/bin/env python3
"""Execute linked Gateway/file composition with modeled DOS/FS and raw EXEC."""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
from check_gateway_handles import Files
from terminal_memory import inspect_terminal_memory
from build_path_session import object_segments
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
class Broker(Files):
 def __init__(self,binary,env=b'COMSPEC=D:\\SHELL.COM',fault='',error=0):
  super().__init__(binary);self.execs=[];self.fault=fault;self.error=error;self.psp_queries=0
  self.keep=json.loads(binary.with_name('manifest.json').read_text())['memory_layout']['retained_parent_paragraphs']
  self.put('process_psp',self.owner);self.put('process_keep_paragraphs',self.keep)
  raw=env+b'\0\0';segment=0xa000
  self.uc.mem_write((segment-1)*16,b'M'+struct.pack('<HH',self.owner,(len(raw)+15)//16)+bytes(11))
  self.uc.mem_write(segment*16,raw);self.uc.mem_write(self.owner*16+0x2c,struct.pack('<H',segment))
  self.result=self.offset('terminal_program_result');self.uc.hook_add(UC_HOOK_CODE,self.raw)
 def interrupt(self,u,n,data):
  if n==0x21 and u.reg_read(UC_X86_REG_AX)>>8==0x51:self.psp_queries+=1;u.reg_write(UC_X86_REG_BX,self.owner);return
  if self.fault=='flush-error' and n==0x21 and u.reg_read(UC_X86_REG_AX)>>8==0x40:
   self.events.append('failed-flush');u.reg_write(UC_X86_REG_AX,112);u.reg_write(UC_X86_REG_EFLAGS,u.reg_read(UC_X86_REG_EFLAGS)|1);return
  super().interrupt(u,n,data)
 def raw(self,u,at,size,data):
  if at!=self.symbols['_hook_lookup_raw']:return
  sp=u.reg_read(UC_X86_REG_SP);ip,path,tail,result=struct.unpack('<4H',u.mem_read(self.data_base+sp,8))
  self.execs.append(dict(path=self.string(self.ds,path).decode(),tail=self.string(self.ds,tail).decode(),JFT=list(self.snapshot())))
  assert all(self.snapshot()[h]==255 for h in self.opened),self.snapshot()
  if self.fault=='foreign-entry':u.mem_write(self.table+5,b'\x77')
  elif self.fault=='capacity':u.mem_write(self.owner*16+0x32,struct.pack('<H',21))
  elif self.fault=='corrupt-lease':u.mem_write(self.symbols['_process_handles_storage']+6,b'\xff\xff')
  elif self.fault in ('corrupt-owner','lost-active','unexpected-recovery'):
   off,value={'corrupt-owner':(0,0),'lost-active':(2,0),'unexpected-recovery':(4,1)}[self.fault]
   u.mem_write(self.symbols['_gateway_files_storage']+off,struct.pack('<H',value))
  elif self.fault=='reentry':
   # The exported ownership predicate is independently executed in normal tests;
   # this observation proves the lease is published before the execution edge.
   assert int.from_bytes(u.mem_read(self.symbols['_gateway_files_storage']+2,2),'little')==1
  u.mem_write(self.data_base+result,struct.pack('<4H',3 if self.error else 0,self.error,0 if self.error else 37,self.keep))
  u.reg_write(UC_X86_REG_AX,3 if self.error else 0);u.reg_write(UC_X86_REG_SP,sp+2);u.reg_write(UC_X86_REG_IP,ip)
 def open_owners(self,hold=False):
  assert self.call('_capture_session_initialize')==0
  pointer=self.stage_near(b'CAPTURE.DAT\0');assert self.call('_capture_session_begin',(pointer,0,0))==0
  assert self.call('_capture_session_put',(65,0))==65
  for prefix,name in [('snapshot',b'SNAP.DAT'),('monitor',b'MON.DAT')]:
   assert self.call('_'+prefix+'_file_initialize')==0;pointer=self.stage_near(name+b'\0');assert self.call('_'+prefix+'_file_begin',(pointer,1))==0
  pointer=self.stage_near(b'HISTORY.DAT\0');assert self.call('_history_file_event',(0,pointer,0))==0
  assert self.call('_printer_device_initialize')==0 and self.call('_printer_device_begin')==0
  if hold:assert self.call('_capture_session_pause')==0
 def invoke(self,pointer=None):return self.bank('_gateway_files_run',(self.result if pointer is None else pointer,),far=True)
 def context_run(self,flags,foreign):
  u=self.uc;name='_gateway_files_run';seg,off=self.entries[name];sp=self.offset('terminal_stack_top')-6
  u.mem_write(self.data_base+sp,struct.pack('<3H',self.return_offset,self.code_segment,self.result))
  regs={UC_X86_REG_CS:seg,UC_X86_REG_DS:self.ds+int(foreign),UC_X86_REG_SS:self.ds,UC_X86_REG_SP:sp,UC_X86_REG_EFLAGS:flags,UC_X86_REG_BP:0xbabe,UC_X86_REG_SI:0x1234,UC_X86_REG_DI:0x5678}
  for r,v in regs.items():u.reg_write(r,v)
  self.waiting=(self.code_segment,self.code_base+self.return_offset);u.emu_start(self.symbols[name],0,count=400000)
  assert u.reg_read(UC_X86_REG_CS)==self.code_segment and u.reg_read(UC_X86_REG_IP)==self.return_offset and u.reg_read(UC_X86_REG_SP)==sp+4
  for r in (UC_X86_REG_DS,UC_X86_REG_SS,UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI):assert u.reg_read(r)==regs[r]
  self.waiting=None;return u.reg_read(UC_X86_REG_AX)
 def owned(self):return self.bank('_gateway_files_owned',far=True)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
 binary=a.terminal.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();m=json.loads(binary.with_name('manifest.json').read_text())
 assert m['experimental_gateway_files'] and not m['diagnostic_gateway_probe'] and sha(binary)==m['binary_sha256']
 for n,h in m['sources'].items():assert sha(ROOT/n)==h,n
 out.mkdir(parents=True);cases=[]
 def record(name,**info):cases.append(dict(case=name,passed=True,**info))
 for hold in (False,True):
  for error in (0,2,5):
   b=Broker(binary,error=error);b.open_owners(hold);before=b.snapshot();enabled=b.get('terminal_sink_398a_enabled');paused=b.get('terminal_sink_398c_disabled')
   assert b.invoke()==(3 if error else 0) and b.snapshot()==before and b.owned()==0
   assert len(b.execs)==1 and b.execs[0]['tail']=='' and b.files[b'C:\\CAPTURE.DAT']==b'A' and b.get('_capture_session_buffered')==0
   assert b.get('terminal_sink_398a_enabled')==enabled and b.get('terminal_sink_398c_disabled')==paused
   if hold:assert b.call('_capture_session_pause')==0
   assert b.call('_capture_session_put',(66,0))==66 and b.call('_capture_session_flush')==0 and b.files[b'C:\\CAPTURE.DAT']==b'AB'
   assert b.invoke()==(3 if error else 0) and b.owned()==0 and b.snapshot()==before and len(b.execs)==2
   record('open-five-'+('hold' if hold else 'enabled')+'-DOS'+str(error),executions=len(b.execs))
 for env,status in [(b'',5),(b'COMSPEC=',5),(b'COMSPEC=D:\\BAD.BAT',6),(b'COMSPEC='+b'A'*260,5)]:
  b=Broker(binary,env);b.open_owners();before=b.snapshot();assert b.invoke()==status and not b.execs and b.snapshot()==before and b.owned()==0
  record('pre-exec-error-'+str(len(cases)),status=status)
 b=Broker(binary);before=b.snapshot();assert b.invoke()==0 and b.snapshot()==before and b.owned()==0;record('no-open-sinks')
 for pointer in (0,65535,'snapshot'):
  b=Broker(binary);b.open_owners();arg=b.offset('_capture_file_result') if pointer=='snapshot' else pointer
  before=b.snapshot();events=len(b.events);assert b.invoke(arg)==1 and b.snapshot()==before and not b.execs and len(b.events)==events and b.owned()==0
  record('refuse-result-'+str(pointer))
 for label,flags,foreign in [('IF0',2,False),('DF1',0x602,False),('foreignDS',0x202,True)]:
  b=Broker(binary);b.open_owners();before=b.snapshot();events=len(b.events)
  b.uc.mem_write(b.data_base+b.result,b'R'*8)
  assert b.context_run(flags,foreign)==1 and b.snapshot()==before and not b.execs and len(b.events)==events and not b.psp_queries and not b.calls
  assert bytes(b.uc.mem_read(b.data_base+b.result,8))==b'R'*8 and b.owned()==0
  record('refuse-context-'+label)
 b=Broker(binary);b.open_owners();b.owner+=1;before=b.snapshot();assert b.invoke()==1 and b.snapshot()==before and not b.execs and b.owned()==0
 record('refuse-foreign-current-PSP')
 for fault in ('printer-count','printer-closing','capture-uncertain','capture-broken','snapshot-uncertain','history-uncertain','printer-uncertain','call-log-open','call-log-recovery','capture-reservation','existing-lease','broker-active','broker-cookie','broker-recovery'):
  b=Broker(binary);b.open_owners()
  if fault in ('printer-count','printer-closing'):b.put('terminal_printer_'+('count' if fault=='printer-count' else 'closing'),1)
  elif fault.startswith('call-log'):assert b.bank('_phone_log_file_initialize')==0;b.uc.mem_write(b.symbols['_phone_log_file_result']+(10 if fault=='call-log-open' else 14),b'\1\0')
  elif fault=='capture-reservation':b.uc.mem_write(b.symbols['_capture_reservation']+6,b'\1\0')
  elif fault=='existing-lease':pointer=b.stage_near(struct.pack('<H',5));assert b.run('begin',(pointer,1))==0
  elif fault.startswith('broker-'):
   off={'broker-active':2,'broker-cookie':0,'broker-recovery':4}[fault];b.uc.mem_write(b.symbols['_gateway_files_storage']+off,b'\1\0')
  else:
   symbol={'capture-uncertain':'_capture_file_result','capture-broken':'_capture_file_result','snapshot-uncertain':'_snapshot_file_result','history-uncertain':'_history_file_result','printer-uncertain':'_printer_device_result'}[fault]
   b.uc.mem_write(b.symbols[symbol]+(0 if fault=='capture-broken' else 12),struct.pack('<H',3 if fault=='capture-broken' else 1))
  before=b.snapshot();events=len(b.events);want=8 if fault in ('broker-cookie','broker-recovery') else 4
  assert b.invoke()==want and b.snapshot()==before and not b.execs and len(b.events)==events,fault
  record('refuse-'+fault,status=want)
 b=Broker(binary,fault='flush-error');b.open_owners();assert b.invoke()==4 and not b.execs and not b.calls and b.owned()==0
 assert b.get('_capture_session_failed') and b.get('terminal_sink_398a_enabled')==0 and b.snapshot()[5]==255
 record('failed-capture-flush-before-lease')
 for fault in ('foreign-entry','capacity','corrupt-lease','corrupt-owner','lost-active','unexpected-recovery','reentry'):
  b=Broker(binary,fault=fault);b.open_owners();before=b.snapshot();status=b.invoke()
  assert status==(0 if fault=='reentry' else 8) and len(b.execs)==1
  if fault=='reentry':assert b.owned()==0 and b.snapshot()==before
  else:
   assert b.owned()!=0;events=len(b.events);assert b.invoke()==8 and len(b.execs)==1 and len(b.events)==events
   if fault!='corrupt-lease':assert b.snapshot()==before
   else:assert b.snapshot()[5:10]==b'\xff'*5
  record('child-return-'+fault,status=status)
 segments=object_segments(binary.parent/'gateway_files.obj');assert segments['FILE_CODE']['class']=='FARCODE' and all(not v['bytes'] for k,v in segments.items() if k!='FILE_CODE'),segments
 sources=['standalone/check_gateway_files.py','standalone/check_gateway_handles.py','standalone/check_directory_identity.py','standalone/dos_image.py','standalone/terminal_memory.py']
 result=dict(passed=True,binary_sha256=sha(binary),inputs=len(cases),cases=cases,object_segments=segments,memory=inspect_terminal_memory(binary,binary.with_name('terminal.map')),original_inputs=[],sources={n:sha(ROOT/n) for n in sources},scope=__doc__+' Actual owners, flush, lease, resolver and quarantine code execute. The raw EXEC edge and DOS filesystem replies are modeled; no UART/foreground or hardware acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS',len(cases),'Gateway file composition cases')
if __name__=='__main__':main()
