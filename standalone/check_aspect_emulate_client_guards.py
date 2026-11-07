#!/usr/bin/env python3
"""Current linked EMULATE child guards; scalar far parent and DOS/UART modeled."""
import argparse,json,re,struct
from pathlib import Path
from unicorn.x86_const import *
import check_aspect_render_client as fixture
from check_aspect_render_client import sha
ROOT=fixture.q.ROOT

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--product',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 product=a.product.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(exist_ok=False)
 fixture.q.BINARY=product/'ASPECT.EXE';fixture.q.MAP=product/'ASPECT.map'
 manifest=json.loads((product/'manifest.json').read_text());assert sha(fixture.q.BINARY)==manifest['binary_sha256']
 assert manifest.get('experimental_emulate_VM')
 for name,digest in manifest['sources'].items():assert sha(ROOT/name)==digest,name
 listing=fixture.q.MAP.read_text();stack=re.search(r'^STACK\s+STACK\s+DGROUP\s+([0-9a-f]+):([0-9a-f]+)\s+([0-9a-f]+)',listing,re.M|re.I);assert stack
 class Client(fixture.Client):
  def __init__(self):
   super().__init__()
   self.low=self.base+int(stack[1],16)*16+int(stack[2],16)-self.data_base
   self.top=self.low+int(stack[3],16)
   self.put('__STACKLOW',self.low);self.put('__STACKTOP',self.top)
   self.words[22]=20;self.publish()
  def call(self,name,arguments=(),limit=250000,sp=None,**unused):
   u=self.uc
   for reg,val in [(UC_X86_REG_CS,self.base_segment),(UC_X86_REG_DS,self.ds),(UC_X86_REG_SS,self.ds),(UC_X86_REG_EFLAGS,0x202)]:u.reg_write(reg,val)
   words=[0xf000]+list(arguments);sp=self.top-64-len(words)*2 if sp is None else sp
   u.mem_write(self.data_base+sp,struct.pack('<'+'H'*len(words),*words));u.reg_write(UC_X86_REG_SP,sp)
   self.returned=False;u.emu_start(self.symbols[name],0,count=limit);assert self.returned,name
   assert u.reg_read(UC_X86_REG_SP)==sp+2,(name,'stack')
   return u.reg_read(UC_X86_REG_AX)
 cases=[]
 def done(name,**kw):cases.append(dict(case=name,passed=True,**kw))
 for version in sorted(set(range(22))|{255,256,65535}):
  m=Client();m.words[22]=version;m.publish();answer=m.open()
  assert answer==(0 if version==20 else 1),(version,answer)
  if version!=20:assert not m.writes and not m.requests
  done('descriptor-capability',version=version,result=answer)
 for extent in (7679,7680,8192):
  m=Client();m.put('__STACKTOP',m.low+extent)
  assert m.call('_aspect_render_client_prepare')==(10 if extent<7680 else 0)
  done('usable-stack-extent',bytes=extent)
 # Calls enter the actual assembly guard at modeled near/cdecl frames. Its two
 # register pushes cost4 bytes at prepare,2 at check. Test adjacent SP bytes.
 for delta in (-1,0,1):
  m=Client();sp=m.low+2048+512+4+delta
  assert m.call('_aspect_render_client_prepare',sp=sp)==(10 if delta<0 else 0)
  done('prepare-live-SP-boundary',delta=delta)
 for delta in (-1,0,1):
  m=Client();assert m.open()==0;sp=m.low+2048+256+2+delta
  assert m.call('_aspect_render_client_check',sp=sp)==(10 if delta<0 else 0)
  done('check-live-SP-boundary',delta=delta)
 for offset in (0,2,2044,2046):
  m=Client();assert m.open()==0;m.requests.clear();at=m.data_base+m.low+offset
  before=bytes(m.uc.mem_read(at,2));m.uc.mem_write(at,b'\0\0')
  assert m.call('_aspect_render_emulate',[6])==10 and not m.requests
  m.uc.mem_write(at,before);assert m.call('_aspect_render_emulate',[6])==0 and m.requests==[(20,6)]
  done('redzone-reject-and-repaired-same-process-retry',offset=offset)
 for active in (0,2):
  m=Client();assert m.open()==0;m.requests.clear();m.put('_aspect_serial_active',active)
  assert m.call('_aspect_render_emulate',[6])==14 and not m.requests
  m.put('_aspect_serial_active',1);assert m.call('_aspect_render_emulate',[6])==0
  done('requires-exact-live-serial-owner',active=active)
 for selector in (0,4,6,255,256,65535):
  m=Client();assert m.open()==0;m.requests.clear();answer=m.call('_aspect_render_emulate',[selector])
  assert answer==(7 if selector>255 else 0)
  assert m.requests==([] if selector>255 else [(20,selector)])
  done('scalar-selector-bound',selector=selector,result=answer)
 for result in (0,1,3,5,7,10,14,15,65531,65532,65533,65534,65535):
  m=Client();assert m.open()==0;m.requests.clear()
  m.uc.mem_write(0x61100,b'\xb8'+struct.pack('<H',result)+b'\xcb');m.uc.ctl_remove_cache(0x61100,0x61104)
  assert m.call('_aspect_render_emulate',[6])==(result if result<=14 else 10)
  m.uc.mem_write(0x61100,b'\xb8\0\0\xcb');m.uc.ctl_remove_cache(0x61100,0x61104)
  assert m.call('_aspect_render_emulate',[4])==0 and m.requests==[(20,6),(20,4)]
  done('typed-parent-result-and-same-process-retry',result=result)
 report=dict(passed=True,cases=cases,child_sha256=sha(fixture.q.BINARY),manifest_sha256=sha(product/'manifest.json'),sources={str(path.relative_to(ROOT)):sha(path) for path in [Path(__file__),ROOT/'standalone/check_aspect_render_client.py',ROOT/'standalone/check_uart.py']},stack=dict(low=m.low,top=m.top),original_inputs=[],limitations=['Actual linked child instructions, declared8192-byte stack extent and modeled near/cdecl SP frames. CRT startup does not execute here; usable bounds are authored from linker allocation.','Scalar far endpoint always admits BEGIN; DOS PSP/MCB, UART and BIOS are modeled by the inherited fixture. No actual parent renderer, bridge, DOS EXEC, callback latency or physical acceptance claim.','Returning a typed error here does not exercise VM fatal reset, WHEN unwinding or native abort paths.'])
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS EMULATE linked child guards',len(cases),'cases')
if __name__=='__main__':main()
