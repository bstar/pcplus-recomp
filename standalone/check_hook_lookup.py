#!/usr/bin/env python3
"""Replay linked HOOK filename policy; optionally compare genuine native code.

Filesystem/EXEC calls are modeled boundaries. Real DOS integration is separate.
"""
import argparse,hashlib,json,re,struct,sys
from pathlib import Path
from unicorn import UC_HOOK_CODE,UC_HOOK_INTR
from unicorn.x86_const import *
from dos_image import DosImage
ROOT=Path(__file__).resolve().parents[1]
FOLDER='terminal-directory-keys-process-bank-session-capture-projection-bound-registers-controls-return-execute-modem-input-apply-lookup-guarded-traps'
TAIL=b' PCPLUS 1 2 3 3'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def cstring(u,at):return bytes(u.mem_read(at,1024)).split(b'\0')[0]
class Linked(DosImage):
 def __init__(self,name,env,files,errors):
  base=ROOT/'build'/FOLDER;super().__init__(base/'TERMINAL.EXE',base/'terminal.map')
  segment,offset=re.search(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+_hook_lookup_run\s*$',(base/'terminal.map').read_text(),re.M|re.I).groups()
  self.target_segment=self.base_segment+int(segment,16);self.target_offset=int(offset,16)
  self.files=set(files);self.errors=errors;self.events=[];self.psp=0xff0
  self.put('process_psp',self.psp);self.put('process_keep_paragraphs',24686)
  raw=b'\0'.join(env)+b'\0\0';segment=0x8000
  self.uc.mem_write((segment-1)*16,b'M'+struct.pack('<HH',self.psp,(len(raw)+15)//16)+bytes(11))
  self.uc.mem_write(segment*16,raw);self.uc.mem_write(self.psp*16+0x2c,struct.pack('<H',segment))
  self.path=self.stage_near(name+b'\0'+bytes(64-len(name)-1)+TAIL+b'\0'+bytes(48-len(TAIL)-1)+b'R'*8)
  self.tail=self.path+64;self.result=self.path+112
  self.uc.hook_add(UC_HOOK_INTR,self.interrupt);self.uc.hook_add(UC_HOOK_CODE,self.raw)
 def carry(self,error):
  f=self.uc.reg_read(UC_X86_REG_EFLAGS);self.uc.reg_write(UC_X86_REG_EFLAGS,f|1 if error else f&~1)
  self.uc.reg_write(UC_X86_REG_AX,error)
 def interrupt(self,u,n,_):
  assert n==0x21;ah=u.reg_read(UC_X86_REG_AX)>>8
  if ah==0x51:u.reg_write(UC_X86_REG_BX,self.psp);return
  if ah==0x3e:self.events.append(('close',));self.carry(0);return
  if ah in(0x3d,0x43):
   name=cstring(u,self.data_base+u.reg_read(UC_X86_REG_DX));exists=name in self.files
   self.events.append(('probe'if ah==0x3d else'access',name,exists));self.carry(0 if exists else 2)
   if ah==0x3d and exists:u.reg_write(UC_X86_REG_AX,7)
   return
  raise AssertionError(('unexpected DOS boundary',hex(ah)))
 def raw(self,u,at,size,_):
  if at!=self.symbols['_hook_lookup_raw']:return
  sp=u.reg_read(UC_X86_REG_SP);ip,path,tail,result=struct.unpack('<4H',u.mem_read(self.data_base+sp,8))
  name=cstring(u,self.data_base+path);command=cstring(u,self.data_base+tail)
  error=self.errors.get(name,0 if name in self.files else 2)
  self.events.append(('exec',name,command));u.mem_write(self.data_base+result,struct.pack('<4H',3 if error else 0,error,0 if error else 37,24686))
  u.reg_write(UC_X86_REG_AX,3 if error else 0);u.reg_write(UC_X86_REG_SP,sp+2);u.reg_write(UC_X86_REG_IP,ip)
 def run(self,arguments=None,flags=0x202,foreign=False):
  u=self.uc;address=self.symbols['_hook_lookup_run'];cs=self.target_segment;ip=self.target_offset
  sp=self.offset('terminal_stack_top')-10
  u.mem_write(self.data_base+sp,struct.pack('<5H',self.return_offset,self.code_segment,*(arguments or(self.path,self.tail,self.result))))
  regs={UC_X86_REG_CS:cs,UC_X86_REG_IP:ip,UC_X86_REG_DS:self.ds+int(foreign),UC_X86_REG_SS:self.ds,UC_X86_REG_SP:sp,
   UC_X86_REG_EFLAGS:flags,UC_X86_REG_BP:0xbabe,UC_X86_REG_SI:0x1234,UC_X86_REG_DI:0x5678}
  for reg,value in regs.items():u.reg_write(reg,value)
  self.returned=False;u.emu_start(address,0,count=1000000)
  assert self.returned and u.reg_read(UC_X86_REG_SP)==sp+4
  for reg in(UC_X86_REG_DS,UC_X86_REG_SS,UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI):assert u.reg_read(reg)==regs[reg]
  result=struct.unpack('<4H',u.mem_read(self.data_base+self.result,8));self.status=u.reg_read(UC_X86_REG_AX)
  if result!=(0x5252,)*4:assert self.status==result[0]
  return result
def original(name,env,files,errors):
 from check_program_exec import Program
 class Native(Program):
  def interrupt(self,u,n,data):
   if u.reg_read(UC_X86_REG_AX)>>8==0x4b:
    path=self.cstring(u.reg_read(UC_X86_REG_DX));self.exec_error=errors.get(path,0 if path in self.files else 2)
   super().interrupt(u,n,data)
 m=Native(original=True);m.files=set(files);m.environment(env);m.symbols['resolver']=0x1353d
 def probe(u,at,size,_):
  if at not in(0x1841a,0x18318):return
  if at==0x18318:m.events.append(('close',));m.return_service(value=0);return
  sp=u.reg_read(UC_X86_REG_SP);pointer=struct.unpack('<H',u.mem_read(m.data_base+sp+2,2))[0]
  path=m.cstring(pointer);exists=path in m.files;m.events.append(('probe',path,exists));m.return_service(value=0x7400 if exists else 0)
 m.uc.hook_add(UC_HOOK_CODE,probe)
 source=m.string(name);resolved=m.call('resolver',[source]);selected=m.cstring(resolved)
 argv=m.argv([selected,TAIL]);result=m.call('program_spawn_search',[0,resolved,argv,0],limit=2000000)
 events=[]
 for event in m.events:
  if event[0]=='exec':events.append(event[:3])
  elif event[0]in('probe','access','close'):events.append(event)
 return result,events,selected
def vectors():
 return [
  ('exact-before-PCPLUS',b'HELP.EXE',[b'PCPLUS=P'],[b'HELP.EXE',b'P\\HELP.EXE'],{},b'HELP.EXE'),
  ('PCPLUS-prefix',b'HELP.EXE',[b'PCPLUS=P'],[b'P\\HELP.EXE'],{},b'P\\HELP.EXE'),
  ('PCPLUS-trailing-backslash',b'HELP.EXE',[b'PCPLUS=P\\'],[b'P\\HELP.EXE'],{},b'P\\HELP.EXE'),
  ('prefix-before-extension',b'HELP',[b'PCPLUS=P'],[b'HELP.exe',b'P\\HELP.com'],{},b'P\\HELP.com'),
  ('COM-priority',b'HELP',[],[b'HELP.com',b'HELP.exe'],{},b'HELP.com'),
  ('EXE-priority',b'HELP',[],[b'HELP.exe',b'HELP.bat'],{},b'HELP.exe'),
  ('batch-COMSPEC',b'HELP',[b'COMSPEC=C:\\COMMAND.COM'],[b'HELP.bat',b'C:\\COMMAND.COM'],{},b'C:\\COMMAND.COM'),
  ('explicit-mixed-batch',b'HELP.BaT',[b'COMSPEC=C:\\COMMAND.COM'],[b'HELP.BaT',b'C:\\COMMAND.COM'],{},b'C:\\COMMAND.COM'),
  ('PATH-second',b'HELP',[b'PATH=P;Q'],[b'Q\\HELP.exe'],{},b'Q\\HELP.exe'),
  ('PATH-explicit-extension',b'HELP.EXE',[b'PATH=P;Q'],[b'Q\\HELP.EXE'],{},b'Q\\HELP.EXE'),
  ('PCPLUS-blocks-PATH',b'HELP.EXE',[b'PCPLUS=P',b'PATH=Q'],[b'Q\\HELP.EXE'],{},None),
  ('explicit-path-blocks-PATH',b'P\\HELP.EXE',[b'PATH=Q'],[b'Q\\P\\HELP.EXE'],{},None),
  ('drive-blocks-PATH',b'C:HELP.EXE',[b'PATH=Q'],[b'Q\\C:HELP.EXE'],{},None),
  ('PATH-empty-first-stops',b'HELP.EXE',[b'PATH=;Q'],[b'Q\\HELP.EXE'],{},None),
  ('PATH-repeated-separators',b'HELP.EXE',[b'PATH=P;;Q'],[b'Q\\HELP.EXE'],{},b'Q\\HELP.EXE'),
  ('PATH-forward-slash',b'HELP.EXE',[b'PATH=P/'],[b'P/HELP.EXE'],{},b'P/HELP.EXE'),
  ('PATH-drive-root',b'HELP.EXE',[b'PATH=C:'],[b'C:\\HELP.EXE'],{},b'C:\\HELP.EXE'),
  ('missing-COMSPEC',b'HELP.bat',[],[b'HELP.bat'],{},None),
  ('bad-COM-stops-EXE',b'HELP',[],[b'HELP.com',b'HELP.exe'],{b'HELP.com':11},b'HELP.com'),
  ('explicit-unknown-extension',b'HELP.BIN',[],[b'HELP.BIN'],{},b'HELP.BIN'),
  ('UNC-error-continues',b'HELP.EXE',[b'PATH=\\\\HOST\\BIN;Q'],[b'\\\\HOST\\BIN\\HELP.EXE',b'Q\\HELP.EXE'],{b'\\\\HOST\\BIN\\HELP.EXE':5},b'Q\\HELP.EXE'),
  ('local-access-error-stops',b'HELP.EXE',[b'PATH=P;Q'],[b'P\\HELP.EXE',b'Q\\HELP.EXE'],{b'P\\HELP.EXE':5},b'P\\HELP.EXE'),
  ('prefix-explicit-name',b'C:\\HELP.EXE',[b'PCPLUS=P'],[],{},None),
  ('readable-stem-still-extensions',b'HELP',[b'PCPLUS=P'],[b'HELP',b'HELP.exe',b'P\\HELP.com'],{},b'HELP.exe'),
  ('first-PCPLUS-wins',b'HELP.EXE',[b'PCPLUS=P',b'PCPLUS=Q'],[b'P\\HELP.EXE',b'Q\\HELP.EXE'],{},b'P\\HELP.EXE'),
  ('lowercase-environment-ignored',b'HELP.EXE',[b'pcplus=P',b'PATH=Q'],[b'P\\HELP.EXE',b'Q\\HELP.EXE'],{},b'Q\\HELP.EXE'),
  ('PCPLUS-forward-slash',b'HELP.EXE',[b'PCPLUS=P/'],[b'P/\\HELP.EXE'],{},b'P/\\HELP.EXE'),
  ('empty-PATH',b'HELP.EXE',[b'PATH='],[],{},None),
 ]
def bounds():
 results=[]
 for kind in('IF0','DF1','foreign-DS','null-name','null-tail','null-result','overlap-result','wrapped-result','long-name','line-break','bad-environment','large-prefix','pending-cancel','cancel-during-search'):
  m=Linked(b'HELP.EXE',[b'PATH=P;Q'],[],{});args=None;flags=0x202;foreign=False
  if kind=='IF0':flags=2
  if kind=='DF1':flags=0x602
  if kind=='foreign-DS':foreign=True
  if kind=='null-name':args=(0,m.tail,m.result)
  if kind=='null-tail':args=(m.path,0,m.result)
  if kind=='null-result':args=(m.path,m.tail,0)
  if kind=='overlap-result':args=(m.path,m.tail,m.path)
  if kind=='wrapped-result':args=(m.path,m.tail,65530)
  if kind=='long-name':m.uc.mem_write(m.data_base+m.path,b'A'*64+b'\0')
  if kind=='line-break':m.uc.mem_write(m.data_base+m.path,b'HELP\r.EXE\0')
  if kind=='bad-environment':m.uc.mem_write(0x7fff0,b'?')
  if kind=='large-prefix':m=Linked(b'HELP.EXE',[b'PCPLUS='+b'P'*260],[],{})
  if kind in('pending-cancel','cancel-during-search'):
   if kind=='cancel-during-search':m=Linked(b'HELP',[b'PATH=P;Q'],[],{})
   m.put('terminal_trap_phase',1)
   if kind=='pending-cancel':m.put('terminal_trap_pending',1)
   else:
    def inject(u,at,size,data):
     if at==m.symbols['_hook_lookup_access']:m.put('terminal_trap_pending',1)
    m.uc.hook_add(UC_HOOK_CODE,inject)
  result=m.run(args,flags,foreign)
  expected=5 if kind=='bad-environment'else 6 if kind=='large-prefix'else 7 if kind in('pending-cancel','cancel-during-search')else 1
  assert m.status==expected,(kind,m.status,result,m.events)
  assert not any(e[0]=='exec'for e in m.events),kind
  if expected==1:assert result==(0x5252,)*4 and not m.events,kind
  if expected==7:assert m.get('terminal_quit')==1
  results.append(dict(case=kind,status=m.status,events=m.events))
 return results
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--original',action='store_true');p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build')and not out.exists();out.mkdir(parents=True)
 base=ROOT/'build'/FOLDER;m=json.loads((base/'manifest.json').read_text());assert m['experimental_hook_lookup']and sha(base/'TERMINAL.EXE')==m['binary_sha256']
 for name,digest in m['sources'].items():assert sha(ROOT/name)==digest,name
 results=[]
 for label,name,env,files,errors,expected in vectors():
  machine=Linked(name,env,files,errors);result=machine.run();executions=[e for e in machine.events if e[0]=='exec']
  if expected is None:assert result[0]!=0,(label,result,machine.events)
  else:assert executions and executions[-1][1]==expected,(label,result,machine.events)
  record=dict(case=label,result=list(result),events=machine.events)
  if a.original:
   status,events,resolved=original(name,env,files,errors)
   # Native argv serialization prefixes an extra blank before its one tail
   # argument. Compare the actual child command after leading delimiters only.
   def canonical(items):return[(e[0],e[1],e[2].lstrip())if e[0]=='exec'else e for e in items]
   if label in('batch-COMSPEC','explicit-mixed-batch'):
    # Native65ca overwrites the batch suffix while appending the first argv
    # delimiter. Keep the selected .BAT target in the maintained route rather
    # than letting COMMAND resolve a different same-stem COM/EXE file.
    left=canonical(machine.events);right=canonical(events)
    assert left[:-1]==right[:-1]and left[-1][:2]==right[-1][:2]
    suffix=left[-1][2].index(b' PCPLUS')
    native_tail=left[-1][2][:suffix-4].replace(b'/c .\\',b'/c ',1)+b' '+TAIL
    assert right[-1][2]==native_tail,(label,left,right)
    record['native_deviation']='Retain selected batch suffix and qualify relative targets against built-ins; native65ca overwrites the suffix. Native argv also adds a delimiter before its one tail argument.'
    record['original_events']=events
   else:assert canonical(machine.events)==canonical(events),(label,machine.events,events,resolved)
   assert(result[0]==0)==(status!=65535),(label,result,status)
   record.update(original_status=status,original_resolved=resolved)
  results.append(record)
 def serial(value):
  if isinstance(value,bytes):return {'hex':value.hex()}
  raise TypeError(type(value).__name__)
 sources=dict(m['sources']);sources['standalone/check_hook_lookup.py']=sha(Path(__file__))
 for name in ['standalone/dos_image.py',*(['standalone/check_program_exec.py','reconstruction/check_ansi_freeze.py','reconstruction/program_exec/recover.py','reconstruction/program_exec/provenance.json']if a.original else[])]:sources[name]=sha(ROOT/name)
 original_inputs={name:sha(ROOT/name)for name in(['analysis/pcplus-originals/PCPLUS-main-2.01.EXE','analysis/pcplus-overlays/manifest.json','build/program-exec/EXECUTOR.EXE','build/program-exec/program_exec.map']if a.original else[])}
 report=dict(passed=True,cases=results,bounds=bounds(),original_comparison=a.original,original_inputs=original_inputs,binary_sha256=m['binary_sha256'],sources=sources,
  scope=__doc__+' Path choice, extension precedence, environment ordering and failure stops; native status remains distinct from the maintained process_result ABI. Leading argument delimiters are normalized explicitly.')
 (out/'result.json').write_text(json.dumps(report,indent=2,default=serial)+'\n');print('PASS linked helper lookup:',len(results),'cases,',len(report['bounds']),'bounds/cancellation; original comparison',a.original)
if __name__=='__main__':main()
