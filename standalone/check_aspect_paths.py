#!/usr/bin/env python3
"""Actual native path command/DOS-result instructions with explicit kernel inputs."""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_CODE,UC_HOOK_INTR
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/aspect-paths';DATA=0x30000

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
class Machine:
 def __init__(self,original=None):
  self.u=Uc(UC_ARCH_X86,UC_MODE_16);self.u.mem_map(0,0x100000)
  d=json.loads((OUT/'manifest.json').read_text());self.units=d['units']
  for unit in self.units:
   code=original[unit.get('file_start',unit.get('file_offset')):unit.get('file_start',unit.get('file_offset'))+unit['bytes']] if original else (ROOT/unit['output']).read_bytes()
   assert hashlib.sha256(code).hexdigest()==unit['sha256'];self.u.mem_write(0x10000+unit['start'],code)
  prior=json.loads((ROOT/'reconstruction/program_exec/provenance.json').read_text())
  for name in ('error_access','error_exec','map_error'):
   unit=next(u for u in prior['units'] if Path(u['file']).stem==name)
   code=original[unit.get('file_start',unit.get('file_offset')):unit.get('file_start',unit.get('file_offset'))+unit['bytes']] if original else (OUT/(name+'.bin')).read_bytes()
   assert hashlib.sha256(code).hexdigest()==unit['sha256'];self.u.mem_write(0x10000+unit['start'],code)
  self.map=(OUT/'error_map.bin').read_bytes();self.u.hook_add(UC_HOOK_CODE,self.hook);self.u.hook_add(UC_HOOK_INTR,self.kernel)
 def hook(self,u,at,size,data):
  self.visited.add(at)
  if at==0x1df04:
   assert not self.reads;self.reads+=1;sp=u.reg_read(UC_X86_REG_SP);ret=int.from_bytes(u.mem_read(DATA+sp,2),'little');u.reg_write(UC_X86_REG_AX,0x5000);u.reg_write(UC_X86_REG_SP,sp+2);u.reg_write(UC_X86_REG_IP,ret)
  elif at==0x1f800:self.returned=True;u.emu_stop()
 def kernel(self,u,n,data):
  assert n==0x21
  ax=u.reg_read(UC_X86_REG_AX);dx=u.reg_read(UC_X86_REG_DX);ah=ax>>8
  if ah==0x0e:self.drives.append(dx&255);u.reg_write(UC_X86_REG_AX,(ax&0xff00)|3);return
  assert ah==self.function and dx==0x5000,(ah,dx)
  path=bytes(u.mem_read(DATA+dx,81)).split(b'\0')[0];assert path==self.path;self.calls.append(ah)
  u.reg_write(UC_X86_REG_AX,self.error if self.error else 0xbeef)
  flags=u.reg_read(UC_X86_REG_EFLAGS);u.reg_write(UC_X86_REG_EFLAGS,(flags|1) if self.error else flags&~1)
 def run(self,kind,path,error,major):
  u=self.u;self.path=path;self.error=error;self.function={'chdir':0x3b,'mkdir':0x39,'rmdir':0x3a,'delete':0x41}[kind];self.reads=0;self.calls=[];self.drives=[];self.visited=set();self.returned=False
  u.mem_write(DATA,b'\xa5'*65536);u.mem_write(DATA+0x5000,(path+b'\0').ljust(81,b'\0'));u.mem_write(DATA+0x7b56,self.map)
  for at,n,width in [(0x7b1c,0x1357,2),(0x7b27,0x55,1),(0x7b24,major,1),(0xd124,0x9abc,2),(0xf200,0xf800,2)]:u.mem_write(DATA+at,n.to_bytes(width,'little'))
  before=bytearray(u.mem_read(DATA,65536))
  for r,v in [(UC_X86_REG_CS,0x1000),(UC_X86_REG_DS,0x3000),(UC_X86_REG_SS,0x3000),(UC_X86_REG_SP,0xf200),(UC_X86_REG_ES,0x4321),(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678),(UC_X86_REG_EFLAGS,0x202)]:u.reg_write(r,v)
  entry={'chdir':0xe681,'mkdir':0xe8a0,'rmdir':0xe8e3,'delete':0xe69a}[kind];u.emu_start(0x10000+entry,0,count=10000)
  assert self.returned and self.reads==1 and self.calls==[self.function]
  fallback=bool(len(path)==2 and path[1:]==b':' and 65<=path[0]<128)
  okay=not error or (kind=='chdir' and fallback)
  status=0 if okay else error if kind=='rmdir' else 1 if kind=='chdir' else 65535
  assert u.reg_read(UC_X86_REG_AX)==status,(kind,path,error,hex(u.reg_read(UC_X86_REG_AX)),status)
  if kind!='chdir':before[0xd124:0xd126]=status.to_bytes(2,'little')
  if kind in ('mkdir','delete') and error:
   before[0x7b27]=error&255
   high=error>>8;low=error&255
   if high:errno=high
   else:
    index=5 if major>=3 and low in (32,33) else min(low,19);errno=self.map[index]
   errno=errno if errno<128 else errno|0xff00;before[0x7b1c:0x7b1e]=errno.to_bytes(2,'little')
  assert self.drives==([((path[0]&0xdf)-65)&255] if kind=='chdir' and okay and len(path)>1 and path[1]==58 else [])
  after=bytes(u.mem_read(DATA,65536));assert after[:0xf100]==before[:0xf100] and after[0xf202:]==before[0xf202:],(kind,path,error,'data outside owned stack')
  assert u.reg_read(UC_X86_REG_SP)==0xf202
  assert [u.reg_read(r) for r in (UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI)]==[0xbabe,0x1234,0x5678]
  assert u.reg_read(UC_X86_REG_DS)==u.reg_read(UC_X86_REG_SS)==0x3000 and not u.reg_read(UC_X86_REG_EFLAGS)&0x400
  return (status,bytes(after[0x7b1c:0x7b70]),bytes(after[0xd124:0xd126]),self.calls,self.drives)

def main():
 p=argparse.ArgumentParser();p.add_argument('--original',type=Path);a=p.parse_args();raw=a.original.read_bytes() if a.original else None
 if raw:assert hashlib.sha256(raw).hexdigest()=='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
 models=[Machine()]+([Machine(raw)] if raw else []);count=0;seen=set()
 def case(kind,path,error,major=3):
  nonlocal count
  outputs=[m.run(kind,path,error,major) for m in models];assert all(o==outputs[0] for o in outputs);seen.update(models[0].visited);count+=1
 for kind in ('mkdir','rmdir','delete'):
  for major in (2,3):
   for error in [0,*range(1,256),256,0x7fff,0x8001,0xffff]:case(kind,b'OWNED',error,major)
 for path in (b'',b'DIR',b'C:',b'a:',b'1:',b'[:',b'\x82:',b'C:\\DIR',b'X:\\NOPE'):
  for error in (0,3):case('chdir',path,error)
 for unit in models[0].units:assert 0x10000+unit['start'] in seen
 report=dict(passed=True,cases=count,original_comparisons=count if raw else 0,checker_sha256=sha(Path(__file__)),manifest_sha256=sha(OUT/'manifest.json'),instruction_addresses=len(seen),scope='Actual source-built flat native handlers/services and reused CRT error code; string operand is a declared source pointer fixture, DOS21 kernel returns are explicit. Complete non-stack data, error/status, drive fallback/select and BP/SI/DI/DS=SS/DF/stack checks; all8-bit DOS errors, extended errors and pre3/3+ mapping. Optional actual-original-byte replay is separate from real DOS filesystem/runtime tests.')
 (OUT/('native-checks.json' if raw else 'checks.json')).write_text(json.dumps(report,indent=2)+'\n');print('Native ASPECT paths:',count,'cases,',report['original_comparisons'],'original comparisons PASS')
if __name__=='__main__':main()
