#!/usr/bin/env python3
"""Execute the banked decoder with far page/state buffers, ABI and no-DOS guards."""
import argparse,json,re,struct
from pathlib import Path
from unicorn import UC_HOOK_INTR
from unicorn.x86_const import *
from dos_image import DosImage
from test_viewer_decode_dos import vectors
from build_path_session import ROOT,sha

class Decoder(DosImage):
 def __init__(self,binary):
  super().__init__(binary,binary.with_name('DECODE.map'))
  self.entries={n:(self.base_segment+int(s,16),int(o,16)) for s,o,n in
   re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',binary.with_name('DECODE.map').read_text(),re.M|re.I)}
  self.uc.hook_add(UC_HOOK_INTR,lambda *args: (_ for _ in ()).throw(AssertionError('Decoder executed an interrupt')))
 def bank(self,name,args):
  u=self.uc;seg,off=self.entries['_viewer_decode_'+name]
  for r,v in [(UC_X86_REG_CS,seg),(UC_X86_REG_DS,self.ds),(UC_X86_REG_SS,self.ds),
    (UC_X86_REG_ES,0xb800),(UC_X86_REG_EFLAGS,0x202),(UC_X86_REG_BP,0xbabe),
    (UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678)]:u.reg_write(r,v)
  words=[self.return_offset,self.code_segment]+args;sp=0xe000-2*len(words)
  u.mem_write(self.data_base+sp,struct.pack('<'+'H'*len(words),*words));u.reg_write(UC_X86_REG_SP,sp)
  self.returned=False;u.emu_start(seg*16+off,0,count=500000)
  assert self.returned and u.reg_read(UC_X86_REG_SP)==sp+4,(name,'return/stack')
  for r,v in [(UC_X86_REG_DS,self.ds),(UC_X86_REG_SS,self.ds),(UC_X86_REG_BP,0xbabe),
    (UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678)]:assert u.reg_read(r)==v,(name,'ABI')
  return u.reg_read(UC_X86_REG_AX)

S=[0x100,0x7000];P=[0x200,0x8000];I=[0x300,0x9000];U=[0x100,0x6000]
linear=lambda p:p[1]*16+p[0]

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ['program','output']:p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();binary=a.program.resolve();out=a.output.resolve()
 assert out.is_relative_to(ROOT/'build') and not out.exists()
 manifest=json.loads(binary.with_name('manifest.json').read_text());assert sha(binary)==manifest['binary_sha256']
 for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 results=[]
 for v in [v for v in vectors() if v['block']==256]:
  m=Decoder(binary);u=m.uc;size=v['width']*v['rows']
  for ptr,n in [(S,26),(P,6468),(I,4096),(U,2)]:u.mem_write(linear(ptr)-16,b'\xa5'*(n+32))
  u.mem_write(linear(I),v['data']);source=bytes(u.mem_read(linear(I)-16,4128))
  dgroup=bytes(u.mem_read(m.data_base,0xd000))
  assert m.bank('init',S+P+[6468,v['width'],v['rows'],v['start']&65535,v['start']>>16])==0
  at=0;status=0
  while at<len(v['data']) and status==0:
   n=min(256,len(v['data'])-at);u.mem_write(linear(U),b'\xaa\xaa')
   status=m.bank('feed',S+[I[0]+at,I[1],n]+U);used=int.from_bytes(u.mem_read(linear(U),2),'little')
   assert 0<=used<=n and (used or status);at+=used
  if not status:status=m.bank('finish',S)
  state=bytes(u.mem_read(linear(S),26))
  assert (at,status,struct.unpack_from('<L',state,18)[0])==(v['used'],v['status'],v['next']),v['name']
  assert bytes(u.mem_read(linear(P),size))==v['page'],v['name']
  for ptr,n,used in [(S,26,26),(P,6468,size),(U,2,2)]:
   assert bytes(u.mem_read(linear(ptr)-16,16))==b'\xa5'*16
   assert bytes(u.mem_read(linear(ptr)+used,n-used+16))==b'\xa5'*(n-used+16)
  assert bytes(u.mem_read(linear(I)-16,4128))==source
  assert bytes(u.mem_read(m.data_base,0xd000))==dgroup
  results.append(dict(case=v['name'],width=v['width'],rows=v['rows'],status=status,passed=True))
 m=Decoder(binary);u=m.uc
 for ptr,n in [(S,26),(P,6468),(I,4096),(U,2)]:u.mem_write(linear(ptr)-16,b'\xa5'*(n+32))
 assert m.bank('init',S+P+[6468,80,24,0,0])==0
 initial=bytes(u.mem_read(linear(S),26))
 state_alias=[S[0]+16,S[1]-1];page_alias=[P[0]+16,P[1]-1]
 recipes=[('init-capacity','init',S+P+[1919,80,24,0,0]),
  ('init-paragraph-alias','init',S+state_alias+[1,1,1,0,0]),
  ('init-segment-wrap','init',S+[0xffff,0x8000,1920,80,24,0,0]),
  ('init-over-1MB','init',S+[0x10,0xffff,1920,80,24,0,0]),
  ('feed-page-alias','feed',S+page_alias+[1]+U),
  ('feed-state-alias','feed',S+state_alias+[1]+U),
  ('feed-used-page-alias','feed',S+I+[1]+page_alias),
  ('feed-used-state-alias','feed',S+I+[1]+state_alias),
  ('feed-source-used-overlap','feed',S+I+[2,I[0]+1,I[1]]),
  ('feed-used-wrap','feed',S+I+[1,0xffff,0x6000]),
  ('feed-count257','feed',S+I+[257]+U)]
 for name,fn,args in recipes:
  before=[bytes(u.mem_read(linear(ptr)-16,n+32)) for ptr,n in [(S,26),(P,6468),(I,4096),(U,2)]]
  assert m.bank(fn,args)==3,name
  after=[bytes(u.mem_read(linear(ptr)-16,n+32)) for ptr,n in [(S,26),(P,6468),(I,4096),(U,2)]]
  assert after==before,name;results.append(dict(case=name,argument_rejected_without_changes=True,passed=True))
 for offset,value in [(0,0),(2,0),(2,133),(4,50),(6,25),(8,133),(10,81),(12,1),(14,2),(16,3)]:
  corrupt=bytearray(initial);struct.pack_into('<H',corrupt,offset,value);u.mem_write(linear(S),bytes(corrupt))
  before=bytes(u.mem_read(linear(P),6468));used=bytes(u.mem_read(linear(U),2))
  assert m.bank('feed',S+I+[1]+U)==3 and m.bank('finish',S)==3
  assert bytes(u.mem_read(linear(S),26))==corrupt and bytes(u.mem_read(linear(P),6468))==before and bytes(u.mem_read(linear(U),2))==used
  results.append(dict(case='damaged-state',offset=offset,value=value,argument_rejected_without_changes=True,passed=True))
 names=['standalone/check_viewer_decode_linked.py','standalone/test_viewer_decode_dos.py','standalone/dos_image.py']
 r=dict(passed=True,binary_sha256=sha(binary),cases=results,inputs=len(results),original_inputs=[],
  sources={**manifest['sources'],**{n:sha(ROOT/n) for n in names}},
  scope=__doc__+' Actual linked Watcom8086 decoder with independent far segments, all non-stack DGROUP bytes unchanged, buffer guards, preserved DS=SS/BP/SI/DI and exact cdecl stack. Any interrupt fails. Includes paragraph aliases, segment/address wraps and damaged-state no-change refusals. Component evidence; no file owner, UI or physical acceptance.')
 out.mkdir(parents=True);(out/'result.json').write_text(json.dumps(r,indent=2)+'\n');print('PASS',len(results),'linked decoder cases,far buffers,ABI and no-interrupt guards')
if __name__=='__main__':main()
