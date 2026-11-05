#!/usr/bin/env python3
"""Execute the linked direct-COMSPEC policy with modeled filesystem/EXEC edges."""
import argparse,json,struct
from pathlib import Path
from unicorn.x86_const import *
import check_hook_lookup as shared
ROOT=shared.ROOT
sha=shared.sha
class Gateway(shared.Linked):
 def __init__(self,env,files=(),errors=None):
  super().__init__(b'UNUSED',env,files,errors or {})
  import re
  seg,off=re.search(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+_gateway_lookup_run\s*$',(ROOT/'build'/shared.FOLDER/'terminal.map').read_text(),re.M|re.I).groups()
  self.target_segment=self.base_segment+int(seg,16);self.target_offset=int(off,16)
 def run_gateway(self,result=None,flags=0x202,foreign=False):
  u=self.uc;sp=self.offset('terminal_stack_top')-6
  u.mem_write(self.data_base+sp,struct.pack('<3H',self.return_offset,self.code_segment,self.result if result is None else result))
  regs={UC_X86_REG_CS:self.target_segment,UC_X86_REG_IP:self.target_offset,UC_X86_REG_DS:self.ds+int(foreign),UC_X86_REG_SS:self.ds,UC_X86_REG_SP:sp,UC_X86_REG_EFLAGS:flags,UC_X86_REG_BP:0xbabe,UC_X86_REG_SI:0x1234,UC_X86_REG_DI:0x5678}
  for reg,value in regs.items():u.reg_write(reg,value)
  self.returned=False;u.emu_start(self.symbols['_gateway_lookup_run'],0,count=2000000)
  assert self.returned and u.reg_read(UC_X86_REG_SP)==sp+4
  for reg in (UC_X86_REG_DS,UC_X86_REG_SS,UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI):assert u.reg_read(reg)==regs[reg]
  return u.reg_read(UC_X86_REG_AX),struct.unpack('<4H',u.mem_read(self.data_base+self.result,8))
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 binary=a.terminal.resolve();out=a.output.resolve();assert binary.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build') and not out.exists()
 m=json.loads(binary.with_name('manifest.json').read_text());assert m['experimental_gateway_lookup'] and not m['diagnostic_gateway_probe'] and sha(binary)==m['binary_sha256']
 shared.FOLDER=str(binary.parent.relative_to(ROOT/'build'));out.mkdir(parents=True);cases=[]
 recipes=[
 ('qualified',[b'COMSPEC=C:\\DOS\\COMMAND.COM'],[b'C:\\DOS\\COMMAND.COM'],{},0,0,[b'C:\\DOS\\COMMAND.COM']),
 ('PATH',[b'COMSPEC=SHELL.COM',b'PATH=C:\\BAD;D:\\BIN'],[b'D:\\BIN\\SHELL.COM'],{},0,0,[b'SHELL.COM',b'C:\\BAD\\SHELL.COM',b'D:\\BIN\\SHELL.COM']),
 ('extension-order',[b'COMSPEC=SHELL'],[b'SHELL.exe'],{},0,0,[b'SHELL.exe']),
 ('qualified-extension',[b'COMSPEC=D:\\DOS\\SHELL',b'PCPLUS=C:\\DECOY'],[b'D:\\DOS\\SHELL.exe'],{},0,0,[b'D:\\DOS\\SHELL.exe']),
 ('missing',[],[b'COMMAND.COM'],{},5,0,[]),('empty',[b'COMSPEC='],[b'COMMAND.COM'],{},5,0,[]),
 ('lowercase',[b'comspec=SHELL.COM'],[b'SHELL.COM'],{},5,0,[]),
 ('duplicate',[b'COMSPEC=FIRST.COM',b'COMSPEC=SECOND.COM'],[b'FIRST.COM',b'SECOND.COM'],{},0,0,[b'FIRST.COM']),
 ('CR',[b'COMSPEC=BAD\r.COM'],[],{},5,0,[]),('LF',[b'COMSPEC=BAD\n.COM'],[],{},5,0,[]),('control',[b'COMSPEC=BAD\x01.COM'],[],{},5,0,[]),
 ('oversized',[b'COMSPEC='+b'A'*260],[],{},5,0,[]),('no-extension-room',[b'COMSPEC='+b'A'*256],[],{},6,0,[]),
 ('leading-bracket',[b'COMSPEC=[SCRIPT]'],[],{},6,0,[]),
 ('no-system-fallback',[b'COMSPEC=MISSING.COM'],[b'COMMAND.COM'],{},3,2,[b'MISSING.COM']),
 ('qualified-no-PATH',[b'COMSPEC=C:\\MISSING.COM',b'PATH=D:\\BIN'],[b'D:\\BIN\\MISSING.COM'],{},3,2,[b'C:\\MISSING.COM']),
 ('drive-relative',[b'COMSPEC=C:SHELL.COM',b'PATH=D:\\BIN'],[b'D:\\BIN\\C:SHELL.COM'],{},3,2,[b'C:SHELL.COM']),
 ('access-denied',[b'COMSPEC=SHELL.COM',b'PATH=D:\\BIN'],[],{b'SHELL.COM':5},3,5,[b'SHELL.COM']),
 ('PATH-access-denied',[b'COMSPEC=SHELL.COM',b'PATH=C:\\BAD;D:\\BIN'],[b'D:\\BIN\\SHELL.COM'],{b'C:\\BAD\\SHELL.COM':5},3,5,[b'SHELL.COM',b'C:\\BAD\\SHELL.COM']),
 ('initial-empty-PATH',[b'COMSPEC=SHELL.COM',b'PATH=;D:\\BIN'],[b'D:\\BIN\\SHELL.COM'],{},3,2,[b'SHELL.COM']),
 ('repeat-delimiter',[b'COMSPEC=SHELL.COM',b'PATH=C:\\BAD;;D:\\BIN'],[b'D:\\BIN\\SHELL.COM'],{},0,0,[b'SHELL.COM',b'C:\\BAD\\SHELL.COM',b'D:\\BIN\\SHELL.COM']),
 ('PATH-control',[b'COMSPEC=SHELL.COM',b'PATH=BAD\n'],[],{},5,0,[b'SHELL.COM']),
 ('batch-rejected',[b'COMSPEC=SHELL.BAT'],[b'SHELL.BAT'],{},6,0,[]),
 ('batch-extension-rejected',[b'COMSPEC=SHELL'],[b'SHELL.bat'],{},6,0,[])]
 for name,env,files,errors,status,dos,attempts in recipes:
  model=Gateway(env,files,errors);actual,r=model.run_gateway();execs=[e for e in model.events if e[0]=='exec']
  checks=dict(status=actual==status and r[0]==status,error=r[1]==dos,attempt_order=[e[1] for e in execs]==attempts,
   empty_tail=all(e[2]==b'' for e in execs),no_resource_probe=not any(e[0]=='probe' for e in model.events),child_status=r[2]==(37 if status==0 else 0))
  case=dict(case=name,passed=all(checks.values()),checks=checks,result=list(r),events=[list(e) for e in model.events]);cases.append(case)
  print(name,{k:v for k,v in checks.items() if not v},flush=True);assert case['passed'],case
 for name,kwargs in [('IF0',dict(flags=2)),('DF1',dict(flags=0x602)),('foreignDS',dict(foreign=True)),('null-result',dict(result=0)),('wrapped-result',dict(result=0xfffc))]:
  model=Gateway([b'COMSPEC=SHELL.COM'],[b'SHELL.COM']);status,r=model.run_gateway(**kwargs)
  assert status==1 and r==(0x5252,)*4 and not model.events,(name,status,r,model.events)
  cases.append(dict(case=name,passed=True))
 for name,change,status in [('cancel',lambda g:g.put('terminal_quit',1),7),('missing-ENV',lambda g:g.uc.mem_write(g.psp*16+0x2c,b'\0\0'),5),('bad-MCB',lambda g:g.uc.mem_write(0x7fff0,b'?'),5),('unterminated',lambda g:g.uc.mem_write(0x80000,b'A'*16),5)]:
  model=Gateway([b'COMSPEC=X']);change(model);actual,r=model.run_gateway();assert actual==status and r[0]==status and not model.events,(name,actual,r,model.events)
  cases.append(dict(case=name,passed=True))
 for c in cases:
  if 'events' in c:c['events']=[[v.decode('ascii') if isinstance(v,bytes) else v for v in e] for e in c['events']]
 sources=('standalone/check_gateway_lookup.py','standalone/check_hook_lookup.py','standalone/dos_image.py')
 report=dict(passed=True,binary_sha256=sha(binary),cases=cases,sources={n:sha(ROOT/n) for n in sources},scope=__doc__+' Actual loaded/relocated C and DOS-boundary instructions, modeled filesystem and EXEC. No foreground/UART/file-ownership/interactive-shell acceptance.')
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS',len(cases),'linked Gateway cases')
if __name__=='__main__':main()
