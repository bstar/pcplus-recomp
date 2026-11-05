#!/usr/bin/env python3
"""Run linked private-JFT and sink-owner queries; DOS/FS endpoints are modeled."""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn.x86_const import *
from check_directory_identity import Identity
from build_path_session import object_segments
from terminal_memory import inspect_terminal_memory
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

class Handles(Identity):
 def __init__(self,binary):
  super().__init__(binary)
  self.owner=0x800;self.table=0x9000;self.capacity=20;self.calls=[]
  self.uc.mem_write(self.owner*16,b'\xcd\x20')
  self.uc.mem_write(self.owner*16+0x32,struct.pack('<HHH',self.capacity,0,self.table//16))
  self.original=bytes(range(20));self.uc.mem_write(self.table,self.original)
  self.pointer=self.stage_near(struct.pack('<7H',5,6,7,8,9,10,11))
 def interrupt(self,u,number,data):
  assert number==0x21 and u.reg_read(UC_X86_REG_AX)>>8==0x62
  self.calls.append(0x62);u.reg_write(UC_X86_REG_BX,self.owner)
 def run(self,action,args=()):return self.bank('_process_handles_'+action,args,far=True)
 def context_refusal(self,action,args,flags,foreign):
  u=self.uc;name='_process_handles_'+action;seg,off=self.entries[name]
  words=[self.return_offset,self.code_segment,*args];sp=self.offset('terminal_stack_top')-2*len(words)
  u.mem_write(self.data_base+sp,struct.pack('<'+'H'*len(words),*words))
  regs={UC_X86_REG_CS:seg,UC_X86_REG_DS:self.ds+int(foreign),UC_X86_REG_SS:self.ds,UC_X86_REG_SP:sp,UC_X86_REG_EFLAGS:flags,UC_X86_REG_BP:0xbabe,UC_X86_REG_SI:0x1234,UC_X86_REG_DI:0x5678}
  for r,v in regs.items():u.reg_write(r,v)
  self.waiting=(self.code_segment,self.code_base+self.return_offset);u.emu_start(self.symbols[name],0,count=400000)
  assert u.reg_read(UC_X86_REG_CS)==self.code_segment and u.reg_read(UC_X86_REG_IP)==self.return_offset and u.reg_read(UC_X86_REG_SP)==sp+4
  for r in (UC_X86_REG_DS,UC_X86_REG_SS,UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI):assert u.reg_read(r)==regs[r]
  self.waiting=None;return u.reg_read(UC_X86_REG_AX)
 def state(self):return self.symbols['_process_handles_storage']
 def snapshot(self):return bytes(self.uc.mem_read(self.table,self.capacity))

class Files(Handles):
 """Model only DOS file endpoints; execute the real application sink owners."""
 def __init__(self,binary):
  super().__init__(binary);self.files={};self.opened={};self.events=[]
  self.uc.mem_write(self.table,bytes(range(5))+b'\xff'*15)
 def string(self,segment,offset):return bytes(self.uc.mem_read(segment*16+offset,128)).split(b'\0',1)[0]
 def interrupt(self,u,number,data):
  assert number==0x21
  ax=u.reg_read(UC_X86_REG_AX);ah=ax>>8;bx=u.reg_read(UC_X86_REG_BX);dx=u.reg_read(UC_X86_REG_DX);cx=u.reg_read(UC_X86_REG_CX);ds=u.reg_read(UC_X86_REG_DS)
  if ah==0x62:return super().interrupt(u,number,data)
  self.events.append(ax);error=0;answer=0
  if ax==0x6000:
   path=self.string(ds,u.reg_read(UC_X86_REG_SI));path=path if b':' in path else b'C:\\'+path
   u.mem_write(u.reg_read(UC_X86_REG_ES)*16+u.reg_read(UC_X86_REG_DI),path+b'\0')
  elif ah==0x43:error=2
  elif ah in (0x5b,0x3c,0x3d):
   path=self.string(ds,dx);assert ah!=0x3d or path==b'PRN'
   answer=next(i for i in range(5,20) if self.uc.mem_read(self.table+i,1)==b'\xff')
   self.files.setdefault(path,bytearray());self.opened[answer]=[path,0];self.uc.mem_write(self.table+answer,bytes([answer+40]))
  elif ah==0x40:
   assert bx in self.opened and self.uc.mem_read(self.table+bx,1)!=b'\xff'
   path,pos=self.opened[bx];value=bytes(u.mem_read(ds*16+dx,cx));self.files[path][pos:pos+cx]=value;self.opened[bx][1]+=cx;answer=cx
  elif ah==0x3e:
   assert bx in self.opened;del self.opened[bx];self.uc.mem_write(self.table+bx,b'\xff')
  elif ax==0x4400:u.reg_write(UC_X86_REG_DX,0xa1)
  elif ax==0x4407:answer=255
  else:raise AssertionError(('Unmodeled DOS endpoint',hex(ax)))
  u.reg_write(UC_X86_REG_AX,error or answer);flags=u.reg_read(UC_X86_REG_EFLAGS);u.reg_write(UC_X86_REG_EFLAGS,flags|1 if error else flags&~1)

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
 binary=a.terminal.resolve();manifest=json.loads((binary.parent/'manifest.json').read_text());assert manifest['experimental_gateway_handles'] and sha(binary)==manifest['binary_sha256']
 for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True);cases=[]
 def record(name,**details):cases.append(dict(case=name,passed=True,**details))
 for count in (1,2,7):
  m=Handles(binary);assert m.run('active_query')==0
  assert m.run('begin',(m.pointer,count))==0
  expected=bytearray(m.original);expected[5:5+count]=b'\xff'*count
  assert m.snapshot()==expected and m.run('active_query')==1
  assert m.run('begin',(m.pointer,count))==1 and m.snapshot()==expected
  assert m.run('end')==0 and m.snapshot()==m.original and m.run('active_query')==0
  assert m.run('end')==1 and m.run('recover')==0
  record('lease-'+str(count),DOS_calls=len(m.calls))
 for fault in ('null','zero','eight','duplicate','closed','out-of-range','near-wrap','bad-PSP','zero-PSP','PSP-wrap','zero-capacity','large-capacity','null-table','table-wrap','physical-wrap','self-table','bad-cookie'):
  m=Handles(binary);pointer=m.pointer;count=2
  if fault=='null':pointer=0
  elif fault=='zero':count=0
  elif fault=='eight':count=8
  elif fault=='duplicate':m.uc.mem_write(m.data_base+pointer,struct.pack('<HH',5,5))
  elif fault=='closed':m.uc.mem_write(m.table+6,b'\xff')
  elif fault=='out-of-range':m.uc.mem_write(m.data_base+pointer,struct.pack('<H',20))
  elif fault=='near-wrap':pointer=65535
  elif fault=='bad-PSP':m.uc.mem_write(m.owner*16,b'NO')
  elif fault=='zero-PSP':m.owner=0
  elif fault=='PSP-wrap':m.owner=0xfffd
  elif fault in ('zero-capacity','large-capacity'):m.uc.mem_write(m.owner*16+0x32,struct.pack('<H',0 if fault=='zero-capacity' else 256))
  elif fault in ('null-table','table-wrap','physical-wrap','self-table'):
   off,seg={'null-table':(0,0),'table-wrap':(65530,0x900),'physical-wrap':(0,65535),'self-table':(m.entries['_process_handles_storage'][1],m.entries['_process_handles_storage'][0])}[fault]
   m.uc.mem_write(m.owner*16+0x34,struct.pack('<HH',off,seg))
  elif fault=='bad-cookie':m.uc.mem_write(m.state(),b'XX')
  before=m.snapshot();assert m.run('begin',(pointer,count))==1 and m.snapshot()==before,fault
  record('refuse-'+fault,DOS_calls=len(m.calls))
 for fault in ('owner','table','capacity','foreign-entry','partial-mask','partial-unmask','corrupt-count','corrupt-slot','corrupt-value'):
  m=Handles(binary);assert m.run('begin',(m.pointer,2))==0;recovery=fault.startswith('partial')
  if fault=='owner':m.owner+=1
  elif fault=='table':m.uc.mem_write(m.owner*16+0x34,struct.pack('<HH',1,m.table//16))
  elif fault=='capacity':m.uc.mem_write(m.owner*16+0x32,struct.pack('<H',21))
  elif fault=='foreign-entry':m.uc.mem_write(m.table+5,b'\x77')
  elif recovery:m.uc.mem_write(m.table+(5 if fault=='partial-mask' else 6),bytes([5 if fault=='partial-mask' else 6]))
  elif fault.startswith('corrupt'):
   saved=bytes(m.uc.mem_read(m.state(),36));off={'corrupt-count':6,'corrupt-slot':8,'corrupt-value':22}[fault]
   m.uc.mem_write(m.state()+off,b'\xff\xff' if fault!='corrupt-value' else b'\xff')
   masked=m.snapshot();assert m.run('end')==1 and m.snapshot()==masked and m.run('active_query')==1
   m.uc.mem_write(m.state(),saved);assert m.run('recover')==0 and m.snapshot()==m.original
   record(fault+'-quarantine');continue
  assert m.run('recover' if recovery else 'end')==(0 if recovery else 1),fault
  assert m.snapshot()==m.original and m.run('active_query')==0
  record('restore-'+fault)
 for context,flags,foreign in [('IF0',2,False),('DF1',0x602,False),('foreignDS',0x202,True)]:
  for action in ('begin','end','recover'):
   m=Handles(binary)
   if action!='begin':assert m.run('begin',(m.pointer,2))==0
   before=m.snapshot();state=bytes(m.uc.mem_read(m.state(),36));calls=len(m.calls)
   assert m.context_refusal(action,(m.pointer,2) if action=='begin' else (),flags,foreign)==1
   assert m.snapshot()==before and bytes(m.uc.mem_read(m.state(),36))==state and len(m.calls)==calls
   if action!='begin':assert m.run('recover')==0 and m.snapshot()==m.original
   record(context+'-'+action,DOS_calls=0)
 m=Files(binary)
 assert m.bank('_capture_file_child_handle',(4,),far=True)==0xfffe
 for index in range(4):assert m.bank('_capture_file_child_handle',(index,),far=True)==0xffff
 assert m.bank('_printer_device_child_handle',far=True)==0xffff and not m.events
 for index,prefix in enumerate(('capture','snapshot','monitor')):
  assert m.call('_'+prefix+'_file_initialize')==0
  pointer=m.stage_near(('FILE'+str(index)+'.DAT').encode()+b'\0')
  assert m.call('_'+prefix+'_file_begin',(pointer,1))==0
  assert m.bank('_capture_file_child_handle',(index,),far=True)==index+5
 pointer=m.stage_near(b'HISTORY.DAT\0');assert m.call('_history_file_event',(0,pointer,0))==0
 assert m.bank('_capture_file_child_handle',(3,),far=True)==8
 assert m.call('_printer_device_initialize')==0 and m.call('_printer_device_begin')==0
 assert m.bank('_printer_device_child_handle',far=True)==9
 record('actual-owner-descriptor-queries',modeled_DOS_calls=len(m.events))
 snapshots=[('_capture_file_result',96),('_snapshot_file_result',96),('_monitor_file_result',96),('_history_file_result',96),('_printer_device_result',32)]
 for symbol,n in snapshots:
  base=m.symbols[symbol];saved=bytes(m.uc.mem_read(base,n));index=[s[0] for s in snapshots].index(symbol)
  for label,offset,value in [('uncertain',12,1),('broken-state',0,3),('failed-owner',2,9)]:
   m.uc.mem_write(base+offset,struct.pack('<H',value));before=bytes(m.uc.mem_read(base,n));events=len(m.events)
   status=m.bank('_capture_file_child_handle',(index,),far=True) if index<4 else m.bank('_printer_device_child_handle',far=True)
   assert status==0xfffe and bytes(m.uc.mem_read(base,n))==before and len(m.events)==events
   m.uc.mem_write(base,saved);record(symbol+'-'+label)
 m.uc.mem_write(m.symbols['_capture_reservation']+6,b'\1\0');events=len(m.events)
 assert m.bank('_capture_file_child_handle',(0,),far=True)==0xfffe and len(m.events)==events
 m.uc.mem_write(m.symbols['_capture_reservation']+6,b'\0\0');record('reservation-busy-query')
 before=[bytes(m.uc.mem_read(m.symbols[s],n)) for s,n in snapshots];original=m.snapshot();events=len(m.events)
 pointer=m.stage_near(struct.pack('<5H',5,6,7,8,9));assert m.run('begin',(pointer,5))==0
 assert m.snapshot()[5:10]==b'\xff'*5 and len(m.events)==events
 assert m.run('end')==0 and m.snapshot()==original
 assert before==[bytes(m.uc.mem_read(m.symbols[s],n)) for s,n in snapshots]
 for index,prefix in enumerate(('capture','snapshot','monitor')):
  pointer=m.stage_near(b'AB');assert m.call('_'+prefix+'_file_append',(pointer,2))==0
  assert m.files[b'C:\\FILE'+str(index).encode()+b'.DAT']==b'AB'
  assert m.call('_'+prefix+'_file_close')==0 and m.bank('_capture_file_child_handle',(index,),far=True)==0xffff
 pointer=m.stage_near(b'AB');assert m.call('_history_file_event',(1,pointer,2))==0 and m.files[b'C:\\HISTORY.DAT']==b'AB'
 assert m.call('_history_file_event',(2,0,0))==0 and m.bank('_capture_file_child_handle',(3,),far=True)==0xffff
 assert m.call('_printer_device_write',(65,))==0 and m.files[b'PRN']==b'A'
 assert m.call('_printer_device_close')==0 and m.bank('_printer_device_child_handle',far=True)==0xffff
 record('five-actual-owners-retain-state-and-write-after-lease')
 segments=object_segments(binary.parent/'process_handles.obj')
 assert segments['FILE_CODE']['class']=='FARCODE' and all(not v['bytes'] for k,v in segments.items() if k!='FILE_CODE'),segments
 memory=inspect_terminal_memory(binary,binary.parent/'terminal.map')
 result=dict(passed=True,binary_sha256=sha(binary),inputs=len(cases),cases=cases,object_segments=segments,memory=memory,
  original_inputs=[],scope=__doc__+' Exercises far ABI, lifetime masking, restoration and quarantine. No child or actual DOS inheritance runs in this test.',
  sources={n:sha(ROOT/n) for n in ['standalone/check_gateway_handles.py','standalone/check_directory_identity.py','standalone/dos_image.py','standalone/build_path_session.py','standalone/terminal_memory.py','src/process/process_handles.c','src/process/process_handles.h']})
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS',len(cases),'private JFT cases')
if __name__=='__main__':main()
