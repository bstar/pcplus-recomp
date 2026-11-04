#!/usr/bin/env python3
"""Run Alt-J's native wrapper and compose it with native sender/expansion."""
import argparse,hashlib,itertools,json,struct,subprocess,sys
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src/config'))
from prm import modem_command_events
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--original',type=Path);a=p.parse_args()
out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
units=[('init',ROOT/'reconstruction/local_controls/init_modem.asm',0x3a25,48,'1a348a267f2ed7ae39340f19cc86f395f2539b2ab2244b6fc61311ae064c9e3b'),('send',ROOT/'reconstruction/modem_send/send.asm',0x48cc,104,'e007929f4330589b441dd73a6e2c1356e470a269d9a1f1c7dd2650620deb1fbb'),('expand',ROOT/'reconstruction/modem_commands/expand.asm',0x4934,87,'008b9051520b45049c2a7c95767686eb48fa3951da532a8abc18de9ead0f9b43')]
original=a.original.read_bytes() if a.original else None
if original:
 assert hashlib.sha256(original).hexdigest()=='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
 assert struct.unpack_from('<H',original,153936+0x44e0+0x24*2)[0]==0x3a25
code={}
for name,source,entry,size,digest in units:
 binary=out/(name+'.bin');subprocess.run(['nasm','-fbin','-I'+str(ROOT/'reconstruction/uart')+'/',str(source),'-o',str(binary)],check=True)
 data=binary.read_bytes();assert len(data)==size and hashlib.sha256(data).hexdigest()==digest
 if original:assert data==original[0x1200+entry:0x1200+entry+size]
 code[entry]=data
subprocess.run(['nasm','-fobj','-DINIT_MODEM_OMF','-I'+str(ROOT/'reconstruction/uart')+'/',str(units[0][1]),'-o',str(out/'init.obj')],check=True)

def effective(value):return value if 30<=value<0x8000 else 30
class Native:
 def __init__(self,composed=False):
  self.u=u=Uc(UC_ARCH_X86,UC_MODE_16);u.mem_map(0,0x100000);u.mem_write(0x13a25,code[0x3a25])
  self.composed=composed
  if composed:
   u.mem_write(0x148cc,code[0x48cc]);u.mem_write(0x14934,code[0x4934])
   for entry,size in [(0xab0b,2),(0x6b72,2),(0x6b98,2),(0x610,0)]:u.mem_write(0x10000+entry,b'\xc2'+struct.pack('<H',size) if size else b'\xc3')
  else:u.mem_write(0x148cc,b'\xc3')
  u.hook_add(UC_HOOK_CODE,self.observe)
 def observe(self,u,at,size,_):
  sp=u.reg_read(UC_X86_REG_SP)
  def arg():return struct.unpack('<H',u.mem_read(0x50000+sp+2,2))[0]
  if at==0x148cc:
   assert struct.unpack('<H',u.mem_read(0x51d1a,2))[0]==0
   assert arg()==0x1b9c;self.calls+=1
   assert struct.unpack('<H',u.mem_read(0x51d68,2))[0]==effective(self.pace)
   if not self.composed:
    for r,v in [(UC_X86_REG_AX,0xbeef),(UC_X86_REG_BX,0x1234),(UC_X86_REG_CX,0x5678),(UC_X86_REG_DX,0x9abc)]:u.reg_write(r,v)
  elif at in (0x1ab0b,0x16b72,0x16b98,0x10610):
   kind={0x1ab0b:'transmit',0x16b72:'character_delay_units',0x16b98:'pause_bios_tick_changes',0x10610:'echo'}[at]
   self.events.append((kind,arg()+1 if at==0x16b98 else arg()))
  elif at==0x1f000:self.returned=True;u.emu_stop()
 def call(self,duplex,pace,payload=b'ATZ^M',pause=126):
  self.pace=pace;self.calls=0;self.events=[];self.returned=False;u=self.u
  u.mem_write(0x51d1a,struct.pack('<H',duplex));u.mem_write(0x51d68,struct.pack('<H',pace));u.mem_write(0x51d66,bytes([pause]));u.mem_write(0x51b9c,payload+b'\0')
  u.mem_write(0x5dffe,struct.pack('<H',0xf000));u.mem_write(0x5df30,b'GUARD!')
  for r,v in [(UC_X86_REG_CS,0x1000),(UC_X86_REG_DS,0x5000),(UC_X86_REG_SS,0x5000),(UC_X86_REG_SP,0xdffe),(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0xcafe),(UC_X86_REG_DI,0xabcd)]:u.reg_write(r,v)
  u.emu_start(0x13a25,0,count=10000)
  assert self.returned and self.calls==1 and u.reg_read(UC_X86_REG_SP)==0xe000
  assert u.reg_read(UC_X86_REG_DS)==u.reg_read(UC_X86_REG_SS)==0x5000
  assert u.reg_read(UC_X86_REG_BP)==0xbabe and u.reg_read(UC_X86_REG_SI)==0xcafe and u.reg_read(UC_X86_REG_DI)==0xabcd
  assert struct.unpack('<H',u.mem_read(0x51d1a,2))[0]==duplex and struct.unpack('<H',u.mem_read(0x51d68,2))[0]==pace
  assert bytes(u.mem_read(0x5df30,6))==b'GUARD!'
  assert bytes(u.mem_read(0x51b9c,len(payload)+1))==payload+b'\0'
  if self.composed:assert tuple(self.events)==modem_command_events(payload,pause,effective(pace)),(payload,pause,pace,self.events)

# Exhaust every WORD value, preserving the original signed JGE policy.
m=Native()
for pace in range(65536):m.call(1,pace)
print('PASS all65536 native pacing words',flush=True)
variants=[b'',b'ATZ^M',b'AT&F^MAT&C1&D2^M',b'~~~AT^@^M',b'A^^B^M',b'\xffA^M',b'A^`B']
m=Native(True);count=0
for duplex,pace,pause,payload in itertools.product((0,1,2,0x7fff,0x8000,0xffff),(0,1,29,30,31,0x7fff,0x8000,0xffff),(0,13,126,255),variants):
 m.call(duplex,pace,payload,pause);count+=1
print('PASS composed native init/send/expand:',count,'cases',flush=True)
files=[Path(__file__).resolve(),ROOT/'src/config/prm.py',ROOT/'reconstruction/uart/encodings.inc']+[u[1] for u in units]
r=dict(passed=True,native_wrapper_bytes=48,composed_native_bytes=239,original_compared=original is not None,cases=dict(all_pacing_words=65536,composed_send_expand=count),sources={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},scope=__doc__+' Exact48+104+87 instructions, signed clamp, settings/stack ABI and byte/pause/NUL/echo plan. UART and calibrated/BIOS delays are explicit modeled boundaries. No timing-unit-to-ms conversion, active call safety, maintained nonblocking owner, actual DOS/modem or physical acceptance.')
(out/'result.json').write_text(json.dumps(r,indent=2)+'\n');print('PASS original Init Modem recovery')
