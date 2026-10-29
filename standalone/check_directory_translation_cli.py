#!/usr/bin/env python3
"""Execute linked original-CLI XLT binding, atomic publication and request ABI."""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn.x86_const import *
from check_directory_identity import Identity
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
class CLI(Identity):
 def __init__(self,binary):super().__init__(binary);self.fault=None;self.answer=None
 def interrupt(self,u,n,data):
  source=bytes(u.mem_read(self.data_base+u.reg_read(UC_X86_REG_SI),64)).split(b'\0',1)[0]
  self.reply=self.answer if self.answer is not None else b'c:\\base\\'+source
  self.error=5 if source==self.fault else 0
  super().interrupt(u,n,data)
 def snapshot(self):return bytes(self.uc.mem_read(self.symbols['_directory_resource_cli'],202))
 def fixture(self):
  blob=b'board.kbd\0'.ljust(64,b'\0')+b'board.key\0'.ljust(64,b'\0')+b'board.xlt\0'.ljust(64,b'\0')+b'\xcc'*314+bytes(114)
  at=self.stage_near(blob);return at,at+64,at+128,at+192,at+506
 def bind(self,mask,args):return self.bank('_directory_resource_cli_bind',[mask,*args[:3]])
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
 binary=a.terminal.resolve();manifest=json.loads((binary.parent/'manifest.json').read_text());assert manifest['experimental_directory_translation'] and sha(binary)==manifest['binary_sha256']
 for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True);cases=[]
 def done(name):cases.append(dict(case=name,passed=True))
 for bits in range(8):
  mask=(512 if bits&1 else 0)|(4096 if bits&2 else 0)|(16384 if bits&4 else 0)|3
  m=CLI(binary);args=m.fixture();assert m.bank('_directory_resource_cli_initialize')==0 and m.bind(mask,args)==0
  state=m.snapshot();assert struct.unpack_from('<5H',state)==(2,mask,0,0,0)
  paths=[b'C:\\BASE\\BOARD.KBD',b'C:\\BASE\\BOARD.KEY',b'C:\\BASE\\BOARD.XLT']
  expected=b''.join(p.ljust(64,b'\0') if bits&(1<<i) else bytes(64) for i,p in enumerate(paths));assert state[10:]==expected
  assert len(m.calls)==sum(bool(bits&(1<<i)) for i in range(3))
  assert m.bank('_directory_resource_cli_request',[args[4],6,0x100,args[3]])==0
  request=bytes(m.uc.mem_read(m.data_base+args[3],314));assert request[:114]==bytes(114) and struct.unpack_from('<3H',request,114)==(6,mask&20992,0x100)
  assert request[120:248]==expected[:128] and request[248:250]==bytes(2) and request[250:]==expected[128:]
  calls=len(m.calls);assert m.bank('_directory_resource_cli_initialize')==0 and m.bind(0,args)==2
  assert m.snapshot()==state and len(m.calls)==calls
  done('original-mask-'+str(mask))
 for kind in ['canonical-error','bad-canonical','bad-input','input-wrap','owner-alias']:
  m=CLI(binary);args=list(m.fixture());assert m.bank('_directory_resource_cli_initialize')==0
  expected=4
  if kind=='canonical-error':m.fault=b'board.xlt';expected=3
  elif kind=='bad-canonical':m.answer=b'C:\\CON.XLT'
  elif kind=='bad-input':m.uc.mem_write(m.data_base+args[2],b'bad*.xlt\0')
  elif kind=='input-wrap':args[2]=0xffe0;expected=1
  elif kind=='owner-alias':args[2]=m.offset('_directory_resource_cli');expected=1
  assert m.bind(16384,args)==expected
  state=m.snapshot()
  if expected==1:assert state==bytes(202) and not m.calls
  else:
   assert struct.unpack_from('<5H',state)==(3,16384,expected,5 if kind=='canonical-error' else 0,16384) and state[10:]==bytes(192)
   calls=len(m.calls);assert m.bank('_directory_resource_cli_initialize')==0 and m.bind(0,args)==2 and m.snapshot()==state and len(m.calls)==calls
  done(kind)
 for fail in [False,True]:
  m=CLI(binary);m.fixture();m.put('terminal_option_mask',20992)
  originals={name:value.ljust(64,b'\0') for name,value in [('terminal_keyboard_path',b'board.kbd'),('terminal_actions_path',b'board.key'),('terminal_translation_path',b'board.xlt')]}
  for name,raw in originals.items():m.uc.mem_write(m.symbols[name],raw)
  if fail:m.fault=b'board.xlt'
  assert m.bank('_terminal_resource_cli_bind',far=True)==(11 if fail else 0)
  assert len(m.calls)==3
  for name,raw in originals.items():assert bytes(m.uc.mem_read(m.symbols[name],64))==(raw if fail else (b'C:\\BASE\\'+raw.split(b'\0',1)[0].upper()).ljust(64,b'\0'))
  if fail:assert m.snapshot()[10:]==bytes(192)
  done('actual-startup-atomic-failure' if fail else 'actual-startup-three-identities')
 result=dict(passed=True,binary_sha256=sha(binary),inputs=len(cases),cases=cases,original_inputs=[],sources={n:sha(ROOT/n) for n in ['standalone/check_directory_translation_cli.py','standalone/check_directory_identity.py','standalone/dos_image.py']},scope=__doc__+' All product instructions execute; only DOS60 canonicalization replies are modeled. Actual DOS CLI/CWD behavior is covered separately.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS',len(cases),'linked CLI translation cases')
if __name__=='__main__':main()
