#!/usr/bin/env python3
"""Execute recovered PROGRAM/CRT code; optional genuine-original comparison.

DOS21 process/filesystem and unresolved heap/UI/serial services are explicitly
modeled boundaries. Separate DOS test really launches the owned child.
"""
import argparse,hashlib,importlib.util,json,struct,sys
from pathlib import Path
from unicorn import UC_HOOK_CODE,UC_HOOK_INTR
from unicorn.x86_const import *
from dos_image import DosImage
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/program-exec';CORE=ROOT/'reconstruction/program_exec';PROOF=json.loads((CORE/'provenance.json').read_text())
spec=importlib.util.spec_from_file_location('program_recovery',CORE/'recover.py');recovery=importlib.util.module_from_spec(spec);spec.loader.exec_module(recovery)
ERROR_MAP=bytes([0,22,2,2,24,13,9,12,12,12,7,8,22,22,255,2,13,18,2,255])
class Program(DosImage):
 def __init__(self,original=False):
  super().__init__(OUT/'EXECUTOR.EXE',OUT/'program_exec.map');self.original=original
  if original:
   sys.path.insert(0,str(ROOT/'reconstruction'));from check_ansi_freeze import load_image
   data=(ROOT/'analysis/pcplus-originals/PCPLUS-main-2.01.EXE').read_bytes();assert hashlib.sha256(data).hexdigest()==PROOF['source_sha256']
   self.uc=load_image(data);self.ds=0x1fb7;self.data_base=self.ds*16
   self.symbols={v:self.data_base+int(k,16) for k,v in PROOF['state'].items()}
   self.symbols.update({v:0x10000+k for k,v in recovery.FUNCTIONS.items()})
   self.symbols.update({v:0x10000+int(k,16) for k,v in PROOF['services'].items()})
   for name in ['program_saved_sp','program_saved_ss','program_saved_pair_low','program_saved_pair_high','program_saved_ds']:self.symbols[name]=0x10000+next(k for k,v in recovery.STATE.items() if v==name)
   self.uc.hook_add(UC_HOOK_CODE,self._stop)
  self.events=[];self.allocated=[];self.arena=0x9500;self.exec_error=0;self.child_status=37;self.clobber=False;self.files=None;self.heap_fail=False;self.dos_calls=[]
  # Only known public synthetic defaults. Never execute original install data.
  for name in PROOF['state'].values():
   if name.startswith('program_saved_'):continue
   self.put(name,0)
  for name,data in [('program_comspec_name',b'COMSPEC'),('program_comspec_name2',b'COMSPEC'),('program_switch_c',b'/c'),('program_default_shell',b'command.com'),('program_batch_prefix',b'/c '),('program_ext_bat',b'.bat'),('program_ext_exe',b'.exe'),('program_ext_com',b'.com'),('program_path_name',b'PATH'),('program_state_7dc9',b'\\'),('program_state_7b00',b'_C_FILE_INFO=')]:self.write(self.offset(name),data+b'\0')
  self.write(self.offset('program_error_map'),ERROR_MAP);self.put('program_dos_major',5,1)
  self.put('program_exec_fcb1',self.offset('program_fcb1'));self.put('program_exec_fcb2',self.offset('program_fcb2'))
  self.put('program_extensions',self.offset('program_ext_bat'));self.put('program_extension1',self.offset('program_ext_exe'));self.put('program_extension2',self.offset('program_ext_com'))
  self.put('program_pair_low',0x1234);self.put('program_pair_high',0x5678)
  self.put('program_state_7a72',80);self.put('program_state_7a74',25);self.put('program_state_7a8a',15);self.put('program_state_7a88',6)
  self.strings={};self.next_input=0x5000;self.environment([])
  self.uc.hook_add(UC_HOOK_CODE,self.service);self.uc.hook_add(UC_HOOK_INTR,self.interrupt)
 def write(self,off,data):self.uc.mem_write(self.data_base+off,data)
 def string(self,value):
  at=self.next_input;self.next_input+=len(value)+1;self.write(at,value+b'\0');return at
 def cstring(self,off):return bytes(self.uc.mem_read(self.data_base+off,32768 if off<32768 else 65536-off)).split(b'\0')[0]
 def environment(self,entries):
  pointers=[self.string(x) for x in entries];self.write(0x7200,struct.pack('<'+'H'*(len(pointers)+1),*pointers,0));self.put('program_environ',0x7200)
 def argv(self,strings):
  pointers=[self.string(x) for x in strings];self.write(0x7000,struct.pack('<'+'H'*(len(pointers)+1),*pointers,0));return 0x7000
 def return_service(self,cleanup=0,value=None,dx=None):
  uc=self.uc;sp=uc.reg_read(UC_X86_REG_SP);ip=struct.unpack('<H',uc.mem_read(self.data_base+sp,2))[0]
  uc.reg_write(UC_X86_REG_SP,sp+2+cleanup);uc.reg_write(UC_X86_REG_IP,ip)
  if value is not None:uc.reg_write(UC_X86_REG_AX,value)
  if dx is not None:uc.reg_write(UC_X86_REG_DX,dx)
 def service(self,u,address,size,_):
  reverse={self.symbols[name]:int(k,16) for k,name in PROOF['services'].items()}
  if address not in reverse:return
  service=reverse[address];sp=u.reg_read(UC_X86_REG_SP);args=struct.unpack('<8H',u.mem_read(self.data_base+sp+2,16))
  if service==0x92a8:
   size=args[0];at=self.arena;self.arena=(self.arena+size+15)&0xfff0
   self.events.append(('heap-alloc',size))
   if not self.heap_fail:self.allocated.append(at)
   self.return_service(value=0 if self.heap_fail else at);return
  if service==0x92a4:
   self.events.append(('heap-free',));assert args[0] in self.allocated;self.allocated.remove(args[0]);self.return_service();return
  if service==0x860f:self.events.append(('farheap-unavailable',args[0]));self.return_service(value=0,dx=0);return
  if service in (0x8224,0x93ca):raise AssertionError(('Unrecovered exceptional service reached',hex(service)))
  cleanup={0x76b4:2,0x6f60:2,0x6e78:2,0x7508:2,0x4870:4,0x76ea:6}.get(service,0)
  if service==0x82b6:self.write(args[0],b'FORMAT-FIXTURE\0')
  self.events.append(('service',f'{service:04x}'))
  self.return_service(cleanup,value=0x7400 if service==0x6bbe else None,dx=self.ds if service==0x6bbe else None)
 def flag(self,carry):
  value=self.uc.reg_read(UC_X86_REG_EFLAGS);self.uc.reg_write(UC_X86_REG_EFLAGS,value|1 if carry else value&~1)
 def interrupt(self,u,n,_):
  assert n==0x21,n
  ax=u.reg_read(UC_X86_REG_AX);ah=ax>>8
  self.dos_calls.append(ah)
  if ah==0x29:u.reg_write(UC_X86_REG_AX,ax&0xff00);return # controlled FCB parse boundary
  if ah==0x0b:return
  if ah==0x43:
   name=self.cstring(u.reg_read(UC_X86_REG_DX)) if u.reg_read(UC_X86_REG_DX) else b'';exists=bool(name) and (self.files is None or name in self.files)
   self.events.append(('access',name,exists));self.flag(not exists);u.reg_write(UC_X86_REG_AX,0 if exists else 2);return
  if ah==0x4b:
   assert ax&255 in (0,4);assert self.get('program_exec_active')==1
   path=self.cstring(u.reg_read(UC_X86_REG_DX));block=u.reg_read(UC_X86_REG_BX);assert block==self.offset('program_exec_block')
   envseg,tailoff,tailseg=struct.unpack('<3H',u.mem_read(self.data_base+block,6));assert tailseg==self.ds
   length=u.mem_read(self.data_base+tailoff,1)[0];tail=bytes(u.mem_read(self.data_base+tailoff+1,length+1));assert tail[-1:]==b'\r'
   environment=bytes(u.mem_read(envseg*16,4096)).split(b'\0\0')[0]
   self.events.append(('exec',path,tail[:-1],environment,ax&255));self.flag(bool(self.exec_error));u.reg_write(UC_X86_REG_AX,self.exec_error)
   if self.clobber:
    u.reg_write(UC_X86_REG_DS,0x1111);u.reg_write(UC_X86_REG_SS,0x2222);u.reg_write(UC_X86_REG_SP,0xaaaa)
   return
  if ah==0x4d:u.reg_write(UC_X86_REG_AX,self.child_status);self.flag(False);return
  raise AssertionError(('Unexpected DOS service',hex(ax)))
 def tail(self,args,env=None):
  self.environment([] if env is None else env);argv=self.argv(args)
  result=self.call('program_environment_tail',[argv,0,0x7400,0x7402,0x7500,0,0])
  if result==0xffff:return result,None,None
  pointer=int.from_bytes(self.uc.mem_read(self.data_base+0x7402,2),'little');allocated=int.from_bytes(self.uc.mem_read(self.data_base+0x7400,2),'little');length=self.uc.mem_read(self.data_base+0x7500,1)[0]
  raw=bytes(self.uc.mem_read(self.data_base+0x7501,length+1));assert raw[-1:]==b'\r'
  return result,raw[:-1],bytes(self.uc.mem_read(self.data_base+pointer,512)).split(b'\0\0')[0]

def run(original=False):
 count=0;compares=0;groups=[]
 def both(fn):
  nonlocal count,compares
  left=fn(Program());count+=1
  if original:
   right=fn(Program(True));assert left==right,(left,right);compares+=1
 for args,want in [([b'child.exe'],b''),([b'child.exe',b'/Q',b'SYNTH'],b' /Q SYNTH'),([b'child.exe',b'X'*124],b' '+b'X'*124),([b'child.exe',b'X'*125],None),([b'child.exe',b'X'*126],None),([b'child.exe',b'',b'A'],b'  A')]:
  def tail(m,args=args,want=want):
   status,actual,environment=m.tail(args,[b'LABVAR=OWNED']);assert actual==want,(status,actual,want)
   if want is None:assert status==0xffff and m.get('program_errno')==7 and m.get('program_dos_error')==10
   else:assert environment==b'LABVAR=OWNED'
   return status,actual,environment
  both(tail)
 def heap_failure(m):
  m.heap_fail=True;result,tail,environment=m.tail([b'CHILD.COM',b'/Q'],[b'LABVAR=OWNED'])
  assert result==0xffff and tail is None and m.get('program_errno')==12 and m.get('program_dos_error')==8 and m.get('program_heap_mode')==0
  assert not m.allocated;return result,m.events
 both(heap_failure)
 groups.append('actual-environment-builder-argv-tail125-byte-boundary-and-CR')
 for name,value in [(b'COMSPEC',b'C:\\COMMAND.COM'),(b'PATH',b'C:\\BIN'),(b'comspec',None),(b'ABSENT',None)]:
  def env(m,name=name,value=value):
   m.environment([b'COMSPEC=C:\\COMMAND.COM',b'PATH=C:\\BIN']);result=m.call('program_getenv',[m.string(name)]);actual=m.cstring(result) if result else None;assert actual==value;return actual
  both(env)
 groups.append('actual-case-sensitive-environment-name-equals-matching')
 for mode,error,clobber in [(0,0,False),(0,0,True),(0,2,True),(0,8,False),(1,0,True),(2,0,False)]:
  def execute(m,mode=mode,error=error,clobber=clobber):
   m.exec_error=error;m.clobber=clobber;name=m.string(b'CHILD.COM');m.write(0x7500,b'\x03 /Q\r');m.write(0x7600,b'LABVAR=OWNED\0\0')
   result=m.call('program_exec',[mode,name,0x7500,0x7600]);assert result==(0xffff if error or mode==2 else 37)
   assert m.get('program_pair_low')==0x1234 and m.get('program_pair_high')==0x5678 and m.get('program_exec_active')==0
   assert m.uc.reg_read(UC_X86_REG_DS)==m.ds and m.uc.reg_read(UC_X86_REG_SS)==m.ds
   if mode==2:assert not m.dos_calls and m.get('program_errno')==22
   else:assert (0x4d in m.dos_calls)==(error==0)
   return result,m.events,m.get('program_errno'),m.get('program_dos_error')
  both(execute)
 for raw,expected in [(1,22),(2,2),(3,2),(4,24),(5,13),(6,9),(7,12),(8,12),(9,12),(10,7),(11,8),(12,22),(13,22),(14,0xffff),(15,2),(16,13),(17,18),(18,2),(19,0xffff),(32,13),(33,13),(34,0xffff),(0x0d00,13)]:
  def errors(m,raw=raw,expected=expected):
   m.uc.reg_write(UC_X86_REG_AX,raw);m.call('program_map_error');assert m.get('program_errno')==expected,(raw,m.get('program_errno'),expected)
   assert m.get('program_dos_error',1)==raw&255;return m.get('program_errno'),m.get('program_dos_error',1)
  both(errors)
 groups.append('actual-EXEC-mode-child-return-DOSerror-CS-stack-DS-pair-restoration')
 for comspec,error in [(True,0),(False,0),(True,2),(True,13),(True,5)]:
  def shell(m,comspec=comspec,error=error):
   m.environment(([b'COMSPEC=CUSTOM.COM'] if comspec else [])+[b'LABVAR=OWNED']);m.exec_error=error
   result=m.call('program_system',[m.string(b'ECHO SYNTH')]);events=[x for x in m.events if x[0]=='exec']
   expected=2 if comspec and error in (2,5) else 1;assert len(events)==expected,(result,events,m.events)
   assert all(x[2]==b' /c ECHO SYNTH' for x in events),events
   assert events[0][1]==(b'CUSTOM.COM' if comspec else b'command.com')
   assert not m.allocated
   return result,events
  both(shell)
 for present in (False,True):
  def shell_query(m,present=present):
   m.environment([b'COMSPEC=CUSTOM.COM'] if present else []);result=m.call('program_system',[0]);assert result==int(present)
   assert not any(e[0]=='exec' for e in m.events);return result
  both(shell_query)
 def search_path(m):
  m.environment([b'PATH=C:\\TOOLS;D:\\BIN',b'COMSPEC=CUSTOM.COM']);m.files={b'C:\\TOOLS\\CHILD.exe'}
  argv=m.argv([b'CHILD',b'/Q']);result=m.call('program_spawn_search',[0,m.string(b'CHILD'),argv,0]);assert result==37
  events=[e for e in m.events if e[0]=='exec'];assert len(events)==1 and events[0][1:3]==(b'C:\\TOOLS\\CHILD.exe',b' /Q'),events
  assert not m.allocated;return result,m.events
 both(search_path)
 def batch(m):
  m.environment([b'COMSPEC=CUSTOM.COM']);argv=m.argv([b'OWNED.BAT',b'/Q']);result=m.call('program_spawnv',[0,m.string(b'OWNED.BAT'),argv,0]);assert result==37
  events=[e for e in m.events if e[0]=='exec'];assert len(events)==1 and events[0][1:3]==(b'CUSTOM.COM',b'/c OWNED /Q'),events
  return result,events
 both(batch)
 groups.append('COMSPEC-shell-c-switch-default-and-only-errno2-or13-fallback')
 # High-level UI/serial boundaries are recorded, never claimed reconstructed.
 for shell_mode,wait,save in [(1,1,1),(1,0,0),(0,0,0)]:
  def application(m,shell_mode=shell_mode,wait=wait,save=save):
   m.environment([b'COMSPEC=CUSTOM.COM']);result=m.call('program_execute',[m.string(b'CHILD.COM'),m.string(b'/Q'),shell_mode,wait,save]);assert result==37 and m.get('program_busy',1)==0
   services=[event[1] for event in m.events if event[0]=='service'];assert '03a7' in services and '6d1a' in services and '76ea' in services
   assert ('3745' in services)==bool(wait)
   return result,[e for e in m.events if e[0] in ('exec','service')]
  both(application)
 for invalid,busy,want in [(b'',0,1),(b'[NONE]',0,1),(b'CHILD.COM',1,0xffff)]:
  def early(m,invalid=invalid,busy=busy,want=want):
   m.put('program_busy',busy,1);result=m.call('program_execute',[m.string(invalid),0,1,1,1]);assert result==want and not any(e[0]=='exec' for e in m.events);return result,m.events
  both(early)
 groups.append('application-routing-UI-wait-save-serial-resume-and-busy-name-guards')
 (OUT/'cpu-results.json').write_text(json.dumps({'passed':True,'binary_sha256':hashlib.sha256((OUT/'EXECUTOR.EXE').read_bytes()).hexdigest(),'cases':count,'genuine_original_comparisons':compares,'groups':groups,'fixtures':'DOS21 functions modeled; unresolved nearheap allocator/free and UI/mouse/vector/serial services explicitly recorded. No synthetic original executable launched.','limitations':PROOF['limitations']},indent=2)+'\n')
 print('Native PROGRAM:',len(groups),'groups,',count,'cases,',compares,'genuineoriginal comparisons passed')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--original',action='store_true');run(p.parse_args().original)
