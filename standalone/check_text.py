#!/usr/bin/env python3
"""Replay actual linked video stores and CGA polling with bounded fixtures."""
from pathlib import Path
import hashlib,json
from unicorn import UC_HOOK_INSN
from unicorn.x86_const import UC_X86_REG_AX,UC_X86_REG_CX,UC_X86_REG_DX,UC_X86_INS_IN
from dos_image import DosImage
ROOT=Path(__file__).resolve().parents[1]
BINARY=ROOT/'build/text/TEXT.EXE'
class Text(DosImage):
 def __init__(self):
  super().__init__(BINARY,ROOT/'build/text/text.map');self.video=0xb8000;self.reads=0
  self.uc.mem_write(self.video,b'\xa5'*4000)
  self.uc.hook_add(UC_HOOK_INSN,self.status,None,1,0,UC_X86_INS_IN)
 def status(self,uc,port,size,data):
  assert port==0x3da and size==1
  value=self.reads%2;self.reads+=1;return value
 def output(self,name,offset,character,attribute=0,count=None):
  for register,value in [(UC_X86_REG_AX,offset),(UC_X86_REG_CX,character),(UC_X86_REG_DX,attribute if count is None else count)]:self.uc.reg_write(register,value)
  return self.call(name)
 def memory(self,offset,size):return bytes(self.uc.mem_read(self.video+offset,size))
def run():
 cases=[]
 def check(name,fn):fn();cases.append({'case':name,'passed':True});print(name,'passed',flush=True)
 def cells():
  a=Text()
  for index in range(256):
   a.output('text_put_cell',index*2,index,255-index)
   assert a.memory(index*2,2)==bytes([index,255-index])
  assert a.memory(512,2)==b'\xa5\xa5'
 check('all-character-and-attribute-bytes',cells)
 def character():
  a=Text();a.output('text_put_char',2,0x42);assert a.memory(0,6)==b'\xa5\xa5\x42\xa5\xa5\xa5'
  a.output('text_put_packed',4,0x431e);assert a.memory(4,2)==b'C\x1e'
 check('char-preserves-attribute-and-packed-swaps-bytes',character)
 def fill():
  a=Text();a.output('text_fill',2,0x442f,count=0);assert a.memory(0,10)==b'\xa5'*10
  a.output('text_fill',2,0x442f,count=3);assert a.memory(0,10)==b'\xa5\xa5'+b'D\x2f'*3+b'\xa5\xa5'
 check('zero-and-multiple-cell-fill-with-canaries',fill)
 def cga():
  a=Text();a.put('text_cga_status_port',0x3da)
  a.output('text_put_packed',0,0x411e);assert a.memory(0,2)==b'A\x1e' and a.reads==2
  a.output('text_put_char',2,0x42);assert a.memory(2,2)==b'B\xa5' and a.reads==4
  a.output('text_fill',4,0x432f,count=3);assert a.memory(4,6)==b'C\x2f'*3 and a.reads==10
  a.output('text_fill',10,0x432f,count=0);assert a.reads==10 and a.memory(10,2)==b'\xa5\xa5'
 check('actual-cga-synchronization-paths',cga)
 result={'passed':True,'binary_sha256':hashlib.sha256(BINARY.read_bytes()).hexdigest(),'cases':cases,'scope':'Actual linked recovered video store/CGA instructions in Unicorn; synthetic CGA status port alternates low/high. BIOS output separately tested in DOSBox-X.'}
 (ROOT/'build/text/checks.json').write_text(json.dumps(result,indent=2)+'\n');return result
if __name__=='__main__':run()
