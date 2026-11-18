#!/usr/bin/env python3
"""Linked8086 screen transaction module; admission/scope/platform are modeled."""
import argparse
import hashlib
import json
import re
import struct
import subprocess
from pathlib import Path
from unicorn import UC_HOOK_CODE,UC_HOOK_INTR,UC_HOOK_MEM_WRITE
from unicorn.x86_const import *
from dos_image import DosImage

ROOT=Path(__file__).resolve().parents[1]
HELPERS=['scroll','draw_box','reset_attribute','clear_home','set_cursor','read_attribute','write_attribute','home']
ARITY=[4,3,1,0,2,1,2,0]


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


class Fixture(DosImage):
 def __init__(self,out):
  super().__init__(out/'RPC.EXE',out/'RPC.map')
  self.events=[];self.admission=0;self.admits=0;self.calls=0;self.stopped=False
  binding=re.search(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+terminal_screen_request\s*$',(out/'RPC.map').read_text(),re.M|re.I)
  self.bank=self.base_segment+int(binding[1],16)
  self.bankbase=self.bank*16
  listing=(out/'rpc.lst').read_text()
  self.state={n:self.symbols['terminal_screen_request']+int(re.search(r'^\s*\d+\s+([0-9A-F]+)\s+.*\b'+n+r':',listing,re.M)[1],16)
              for n in ['screen_phase','screen_primitive','screen_count','screen_arguments']}
  self.peers={self.symbols['terminal_screen_'+n]:n for n in HELPERS+['admit','scope_begin','scope_end']}
  self.uc.hook_add(UC_HOOK_CODE,self.code)
  self.uc.hook_add(UC_HOOK_INTR,lambda *args:(_ for _ in ()).throw(AssertionError('Unexpected interrupt')))
  self.uc.hook_add(UC_HOOK_MEM_WRITE,self.write)
  self.stack=0x1800
  # Modeled stack occupies the source-built DOS program's8192-byte DGROUP.
  assert self.stack<self.stack_bytes
  self.put('attributes_normal_value',0x1234);self.put('screen_attribute_row_bytes',80)
  self.put('ui_window_rows',25);self.put('screen_columns',80);self.put('screen_video_row_bytes',160)
 def stateword(self,n):return int.from_bytes(self.uc.mem_read(self.state[n],2),'little')
 def staged(self):return bytes(self.uc.mem_read(self.state['screen_phase'],14))
 def ret(self,value=None,cleanup=0):
  u=self.uc;sp=u.reg_read(UC_X86_REG_SP);ip=int.from_bytes(u.mem_read(self.data_base+sp,2),'little')
  if value is not None:u.reg_write(UC_X86_REG_AX,value)
  u.reg_write(UC_X86_REG_SP,sp+2+cleanup);u.reg_write(UC_X86_REG_IP,ip)
 def code(self,u,address,size,unused):
  if address==self.bankbase+0xf000:self.stopped=True;u.emu_stop();return
  if address not in self.peers:return
  name=self.peers[address]
  if name=='admit':
   self.admits+=1
   for reg in (UC_X86_REG_BX,UC_X86_REG_CX,UC_X86_REG_DX):u.reg_write(reg,0xa55a)
   self.ret(self.admission);return
  assert self.stateword('screen_phase')==self.stateword('screen_count')==0,'Helper saw active transaction'
  if name.startswith('scope_'):
   self.events.append((name,));self.ret();return
  n={'scroll':4,'draw_box':3,'reset_attribute':0,'clear_home':0,'set_cursor':0,'read_attribute':1,'write_attribute':2,'home':0}[name]
  sp=u.reg_read(UC_X86_REG_SP);args=tuple(struct.unpack('<'+'H'*n,u.mem_read(self.data_base+sp+2,n*2))) if n else ()
  if name=='reset_attribute':args=(u.reg_read(UC_X86_REG_AX),)
  if name=='set_cursor':args=(u.reg_read(UC_X86_REG_AX),u.reg_read(UC_X86_REG_DX))
  self.events.append((name,*args));self.ret(0x5a if name=='read_attribute' else None,2*n)
 def write(self,u,access,address,size,value,unused):
  # Product code may change only its CS transaction words and the caller stack.
  state=self.state['screen_phase']
  assert state<=address and address+size<=state+14 or self.data_base+self.stack-128<=address and address+size<=self.data_base+self.stack+12,(hex(address),size)
 def request(self,op,value=0):
  self.calls+=1;self.events=[];self.admits=0;self.stopped=False;self.returned=False;u=self.uc
  for r,v in [(UC_X86_REG_CS,self.bank),(UC_X86_REG_DS,self.ds),(UC_X86_REG_SS,self.ds),
              (UC_X86_REG_BP,0x1357),(UC_X86_REG_SI,0x2468),(UC_X86_REG_DI,0x369c),
              (UC_X86_REG_AX,op),(UC_X86_REG_BX,value),(UC_X86_REG_SP,self.stack),(UC_X86_REG_EFLAGS,0x202)]:u.reg_write(r,v)
  # Outside emulation setup uses mem_write and does not invoke the write hook.
  frame=struct.pack('<H',0xf000)+b'CALLER-CANARY';u.mem_write(self.data_base+self.stack,frame)
  u.emu_start(self.symbols['terminal_screen_request'],0,count=3000)
  assert (self.stopped or self.returned) and self.admits==1 and u.reg_read(UC_X86_REG_SP)==self.stack+2,(op,value,self.stopped,self.returned,self.admits,u.reg_read(UC_X86_REG_SP),self.events)
  assert [u.reg_read(r) for r in (UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI)]==[0x1357,0x2468,0x369c]
  assert u.reg_read(UC_X86_REG_DS)==self.ds and u.reg_read(UC_X86_REG_SS)==self.ds
  assert bytes(u.mem_read(self.data_base+self.stack,len(frame)))==frame
  return u.reg_read(UC_X86_REG_AX)
 def transaction(self,primitive,args):
  assert self.request(33,primitive)==0
  for value in args:assert self.request(34,value)==0
  return self.request(35)


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 names=['src/terminal/script_screen_rpc.asm','standalone/check_script_screen_rpc.py','standalone/dos_image.py'];sources={n:sha(ROOT/n) for n in names}
 peers=['BITS 16','CPU 8086','SEGMENT ASPECT_CODE public align=16 class=FARCODE use16']
 for name in HELPERS+['admit','scope_begin','scope_end']:peers+=['global terminal_screen_'+name,'terminal_screen_'+name+': ret']
 peers+=['SEGMENT _DATA public class=DATA use16','GROUP DGROUP _DATA']
 for name in ['attributes_normal_value','screen_attribute_row_bytes','ui_window_rows','screen_columns','screen_video_row_bytes']:peers+=['global '+name,name+': dw 0']
 (out/'peers.asm').write_text('\n'.join(peers)+'\n');(out/'main.c').write_text('int main(void){return 0;}\n')
 subprocess.run(['nasm','-fobj',str(ROOT/names[0]),'-l','rpc.lst','-o','rpc.obj'],cwd=out,check=True)
 subprocess.run(['nasm','-fobj','peers.asm','-o','peers.obj'],cwd=out,check=True)
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-k8192','-fm=RPC.map','-fe=RPC.EXE','main.c','rpc.obj','peers.obj'],cwd=out,check=True)
 f=Fixture(out);cases=0
 def case():
  nonlocal cases;cases+=1;assert f.request(36)==0
 # Every metadata WORD byte, including queries during a partially staged command.
 for value in (0,1,14,127,128,255,256,0x1234,0x8000,0xffff):
  for index,field in [(0,'attributes_normal_value'),(2,'ui_window_rows'),(3,'ui_window_rows'),(4,'screen_columns'),(5,'screen_video_row_bytes')]:
   for high in (0,1):
    case();assert f.request(33,0)==0 and f.request(34,0x1234)==0
    f.put(field,value);before=f.staged();result=value-(index in (3,4));result&=65535
    assert f.request(32,index|(high<<8))==0xf000|((result>>(high*8))&255)
    assert f.staged()==before and not f.events
 for value in (0,80,131,132,133,0xffff):
  case();f.put('screen_attribute_row_bytes',value);assert f.request(32,1)==0xf000|(value==132)
 f.put('ui_window_rows',25);f.put('screen_columns',80);f.put('screen_video_row_bytes',160);f.put('screen_attribute_row_bytes',80)
 valid=[[255,0x070b,0x0203,25],[255,0x070b,0x0203],[255],[],[24,79],[3999],[3999,255],[]]
 for primitive,args in enumerate(valid):
  case();assert f.transaction(primitive,args)==(0xf05a if primitive==5 else 0)
  expected=[(HELPERS[primitive],*args)]
  assert f.events==expected if primitive==5 else f.events==[('scope_begin',),*expected,('scope_end',)]
 # Native finite zero and reversed rectangle spans are admitted unchanged.
 for primitive in (0,1):
  for corners in [(0x0203,0x0203),(0x0203,0x070b)]:
   case();args=[7,*corners]+([0] if primitive==0 else []);assert f.transaction(primitive,args)==0
 for primitive,arity in enumerate(ARITY):
  for count in range(5):
   if count==arity:continue
   case();assert f.request(33,primitive)==0
   for value in [0]*count:assert f.request(34,value)==0
   assert f.request(35)==7 and not f.events and f.stateword('screen_phase')==0
 invalid={0:[[256,0,0,0],[7,0x1900,0,0],[7,0x0050,0,0],[7,0,0,26]],
          1:[[256,0,0],[7,0,0x1900],[7,0,0x0050]],2:[[256],[65535]],
          4:[[25,0],[0,80],[0,0x8000]],5:[[0],[3998],[4001],[65535]],
          6:[[0,7],[4001,7],[3999,256]]}
 for primitive,inputs in invalid.items():
  for args in inputs:
   case();assert f.transaction(primitive,args)==7 and not f.events and f.stateword('screen_phase')==0
 for width in (80,132):
  for col in (79,80,131,132,65535):
   case();f.put('screen_attribute_row_bytes',width);result=f.transaction(4,[24,col]);assert result==(0 if col<(132 if width==132 else 80) else 7)
 f.put('screen_attribute_row_bytes',80)
 for rows in (25,50):
  case();f.put('ui_window_rows',rows);assert f.transaction(5,[rows*160-1])==0xf05a
  case();assert f.transaction(5,[rows*160+1])==7
 f.put('ui_window_rows',25)
 # Bounds are checked again at COMMIT against the current admitted geometry.
 for primitive,args,field,value in [(4,[24,79],'ui_window_rows',24),
                                    (1,[7,0x174f,0x0000],'screen_columns',79),
                                    (5,[3999],'ui_window_rows',24)]:
  case();assert f.request(33,primitive)==0
  for arg in args:assert f.request(34,arg)==0
  old=f.get(field);f.put(field,value);assert f.request(35)==7 and not f.events;f.put(field,old)
 for op in (0,31,37,255,65535):case();assert f.request(op)==7 and not f.events
 for arg in (6,255,262,512,65535):case();assert f.request(32,arg)==7 and not f.events
 for arg in (8,65535):case();assert f.request(33,arg)==7 and not f.events
 for op,arg in [(34,0),(35,0),(35,1),(36,1)]:case();assert f.request(op,arg)==7 and not f.events
 case();assert f.request(33,0)==0 and f.request(33,0)==7 and not f.events
 case();assert f.request(33,0)==0
 for i in range(4):assert f.request(34,i)==0
 assert f.request(34,4)==7 and not f.events
 # Each operation independently re-admits and retires on admission failure.
 for op in range(32,37):
  for refusal in range(1,15):
   case();assert f.request(33,0)==0 and f.request(34,7)==0;f.admission=refusal
   assert f.request(op)==refusal and not f.events and f.stateword('screen_phase')==f.stateword('screen_count')==0
   f.admission=0
 # The outer renderer's retirement entry does not admit or change AX/FLAGS.
 for value,flags in [(0,2),(0xffff,0x202),(0x1234,0xed7)]:
  case();assert f.request(33,0)==0 and f.request(34,0xbeef)==0
  before=f.staged();u=f.uc;u.reg_write(UC_X86_REG_SP,f.stack);u.mem_write(f.data_base+f.stack,struct.pack('<H',0xf000))
  u.reg_write(UC_X86_REG_AX,value);u.reg_write(UC_X86_REG_EFLAGS,flags);actual_flags=u.reg_read(UC_X86_REG_EFLAGS)
  f.returned=f.stopped=False;f.events=[];f.admits=0
  u.emu_start(f.symbols['terminal_screen_retire'],0,count=100)
  assert (f.returned or f.stopped) and u.reg_read(UC_X86_REG_SP)==f.stack+2
  assert u.reg_read(UC_X86_REG_AX)==value and u.reg_read(UC_X86_REG_EFLAGS)==actual_flags and not f.admits and not f.events
  assert f.stateword('screen_phase')==f.stateword('screen_count')==0
  assert f.staged()[2:4]==before[2:4] and f.staged()[6:]==before[6:]
 assert all(sha(ROOT/n)==digest for n,digest in sources.items())
 result=dict(passed=True,cases=cases,requests=f.calls,sources=sources,
  artifacts={p.name:sha(p) for p in out.iterdir() if p.is_file()},scope=__doc__,
  limitations=['Actual linked module instructions execute, with near imports replaced by explicit admission, scope and primitive observation peers.',
   'No outer renderer identity/client handshake, actual private-owner implementation, real screen kernels, BIOS/DOS, child parser or whole-program integration is claimed.'])
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS',cases,'screen RPC cases',f.calls,'authenticated operations')


if __name__=='__main__':main()
