#!/usr/bin/env python3
"""Actual linked snapshot/bounds instructions with memory and CGA-port fixtures."""
from pathlib import Path
import hashlib,json,random,struct
from unicorn import UC_HOOK_INSN
from unicorn.x86_const import *
from dos_image import DosImage
ROOT=Path(__file__).resolve().parents[1]
BINARY=ROOT/'build/ui-windows/WINDOWS.EXE'
class Windows(DosImage):
 def __init__(self):
  super().__init__(BINARY,ROOT/'build/ui-windows/ui_windows.map')
  self.video=0xb8000;self.reads=0
  self.uc.hook_add(UC_HOOK_INSN,self.status,None,1,0,UC_X86_INS_IN)
 def status(self,uc,port,size,_):
  assert (port,size)==(0x3da,1)
  value=self.reads%2;self.reads+=1;return value
 def invoke(self,name,args,callee_cleanup=True):
  uc=self.uc
  for reg,value in [(UC_X86_REG_CS,self.base_segment),(UC_X86_REG_DS,self.ds),(UC_X86_REG_SS,self.ds),(UC_X86_REG_EFLAGS,0x202),(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678)]:uc.reg_write(reg,value)
  words=[0xf000]+list(args);sp=0xe000-len(words)*2
  uc.mem_write(self.data_base+sp,struct.pack('<'+'H'*len(words),*words));uc.reg_write(UC_X86_REG_SP,sp)
  self.returned=False;uc.emu_start(self.symbols[name],self.base+0x10000,count=500000)
  assert self.returned and uc.reg_read(UC_X86_REG_SP)==(0xe000 if callee_cleanup else sp+2),(name,'RET cleanup')
  for reg,value in [(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678)]:assert uc.reg_read(reg)==value,(name,reg)
  return uc.reg_read(UC_X86_REG_AX)
 def data(self,name='window_buffer',size=4096):return bytes(self.uc.mem_read(self.symbols[name],size))
 def memory(self):return bytes(self.uc.mem_read(self.video,4000))
 def rect(self,name,top,left,height,width,capacity=None,buffer=None):
  return self.invoke(name,[top,left,height,width,self.offset('window_buffer') if buffer is None else buffer,2*height*width if capacity is None else capacity])

def run():
 cases=[]
 def check(name,fn):fn();cases.append({'case':name,'passed':True});print(name,'passed',flush=True)
 def raw():
  a=Windows();rng=random.Random(201);pattern=bytes(rng.randrange(256) for _ in range(4000));a.uc.mem_write(a.video,pattern)
  at=a.offset('window_buffer');a.invoke('pcplus_screen_save',[2000,0,at])
  assert a.data(size=4000)==b''.join(pattern[i:i+2][::-1] for i in range(0,4000,2))
  a.uc.mem_write(a.video,b'\xcc'*4000);a.invoke('pcplus_screen_restore',[2000,0,at]);assert a.memory()==pattern
  before=a.data();a.invoke('pcplus_screen_save',[0,4000,at]);assert a.data()==before
  a.invoke('pcplus_screen_restore',[0,4000,at]);assert a.memory()==pattern
 check('original-flat-ABI-full-screen-packed-order-zero-count',raw)
 def nested():
  a=Windows();pattern=bytes(i%256 for i in range(4000));a.uc.mem_write(a.video,pattern)
  assert a.rect('ui_window_save',1,2,3,4)==0
  painted=bytearray(pattern)
  for row in range(1,4):painted[row*160+4:row*160+12]=b'X\x4f'*4
  a.uc.mem_write(a.video,bytes(painted))
  inner=a.offset('window_buffer')+100
  assert a.rect('ui_window_save',2,3,1,2,buffer=inner)==0
  a.uc.mem_write(a.video+326,b'Y\x2e'*2)
  assert a.rect('ui_window_restore',2,3,1,2,buffer=inner)==0 and a.memory()==painted
  assert a.rect('ui_window_restore',1,2,3,4)==0 and a.memory()==pattern
  assert a.data()[24:100]==b'\xa5'*76 and a.data()[104:]==b'\xa5'*(4096-104)
  assert a.rect('ui_window_save',24,79,1,1)==0
  assert a.rect('ui_window_restore',24,79,1,1)==0 and a.memory()==pattern
 check('nested-rectangles-stride-edges-LIFO-and-buffer-canaries',nested)
 def invalid():
  bad=[(0,0,0,1,None,None),(0,0,1,0,None,None),(25,0,1,1,None,None),(0,80,1,1,None,None),(24,79,2,1,None,None),(24,79,1,2,None,None),(65535,0,2,1,None,None),(0,65535,1,2,None,None),(0,0,2,3,11,None),(0,0,1,2,None,65534)]
  for name in ['ui_window_save','ui_window_restore']:
   for top,left,height,width,capacity,buffer in bad:
    a=Windows();a.uc.mem_write(a.video,b'\x5a'*4000);before=a.data()
    assert a.rect(name,top,left,height,width,capacity,buffer)==1,(name,top,left,height,width)
    assert a.memory()==b'\x5a'*4000 and a.data()==before
   for cols,rows in [(0,25),(256,25),(80,0),(80,128)]:
    a=Windows();a.put('screen_columns',cols);a.put('ui_window_rows',rows)
    assert a.rect(name,0,0,1,1)==1
 check('invalid-overflow-small-buffer-and-invalid-screen-rejected-before-I-O',invalid)
 def cga():
  a=Windows();a.put('text_cga_status_port',0x3da);a.uc.mem_write(a.video,b'A\x1eB\x2f')
  assert a.rect('ui_window_save',0,0,1,2)==0 and a.reads==8
  a.uc.mem_write(a.video,b'\0'*4);assert a.rect('ui_window_restore',0,0,1,2)==0
  assert a.memory()[:4]==b'A\x1eB\x2f' and a.reads==12
 check('real-recovered-CGA-byte-read-and-word-write-polling',cga)
 result={'passed':True,'binary_sha256':hashlib.sha256(BINARY.read_bytes()).hexdigest(),'cases':cases,'scope':'Actual linked recovered cell helpers plus maintained rectangle checks. CGA input fixture alternates low/high; cursor BIOS ownership checked separately in DOS.'}
 (ROOT/'build/ui-windows/checks.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':run()
