#!/usr/bin/env python3
"""Actual linked browser+DOS reader instructions; explicit BIOS/DOS OS fixtures."""
from pathlib import Path
import hashlib,json,struct
from unicorn import UC_HOOK_INTR,UC_HOOK_CODE,UC_HOOK_INSN
from unicorn.x86_const import *
from dos_image import DosImage
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/directory-browser'
def fixture():
 data=bytearray(23050)
 for index in range(200):
  at=250+index*114
  name=(f'Board{index+1:03d}').encode().ljust(24,b' ');number=(f'bbs{index+1}.local:23').encode().ljust(20,b' ')
  data[at:at+24]=name;data[at+25:at+45]=number;data[at+75:at+85]=b'SECRET-PW!'
 data[250:274]=b'A\x1b\xdb'+b'X'*21
 return bytes(data)
class Browser(DosImage):
 def __init__(self,keys,mode=3,page=0,error=False):
  super().__init__(OUT/'BROWSER.EXE',OUT/'browser.map')
  self.keys=list(keys);self.mode=mode;self.page=page;self.video=(0xb0000 if mode==7 else 0xb8000)+page*4096
  self.pattern=bytes((i*17+3)%256 for i in range(4000));self.uc.mem_write(self.video,self.pattern)
  self.uc.mem_write(0x44e,struct.pack('<H',page*4096));self.cursor=0x0711;self.shape=0x060f;self.rendered=bytearray();self.frames=[];self.opens=0;self.closes=0;self.offset_read=0;self.pages=[];self.error=error;self.data=fixture()
  self.uc.hook_add(UC_HOOK_INTR,self.interrupt);self.uc.hook_add(UC_HOOK_CODE,self.trace)
  self.uc.hook_add(UC_HOOK_INSN,self.no_ports,None,1,0,UC_X86_INS_IN)
  self.uc.hook_add(UC_HOOK_INSN,self.no_ports,None,1,0,UC_X86_INS_OUT)
 def no_ports(self,*args):raise AssertionError("Browser attempted port IO")
 def trace(self,uc,address,size,_):
  if address==self.symbols['_directory_dos_page']:
   base=uc.reg_read(UC_X86_REG_SS)*16+uc.reg_read(UC_X86_REG_SP)
   self.pages.append(struct.unpack('<H',uc.mem_read(base+4,2))[0])
 def interrupt(self,uc,number,_):
  ax=uc.reg_read(UC_X86_REG_AX);ah=ax>>8;bx=uc.reg_read(UC_X86_REG_BX);cx=uc.reg_read(UC_X86_REG_CX);dx=uc.reg_read(UC_X86_REG_DX)
  if number==0x10:
   if ah==15:uc.reg_write(UC_X86_REG_AX,80*256+self.mode);uc.reg_write(UC_X86_REG_BX,self.page*256)
   elif ah==3:uc.reg_write(UC_X86_REG_CX,self.shape);uc.reg_write(UC_X86_REG_DX,self.cursor)
   elif ah==2:self.cursor=dx
   elif ah==1:self.shape=cx
   elif ah==6:self.uc.mem_write(self.video,bytes([32,bx>>8])*2000)
   elif ah==9:
    assert bx>>8==self.page and cx==1
    row,col=divmod(self.cursor,256);assert row<25 and col<80
    self.uc.mem_write(self.video+(row*80+col)*2,bytes([ax&255,bx&255]));self.rendered.append(ax&255)
   else:raise AssertionError(('BIOS',hex(ax)))
  elif number==0x16:
   assert ah==0 and self.keys,'Unexpected blocking key read'
   self.frames.append(bytes(self.uc.mem_read(self.video,4000)))
   uc.reg_write(UC_X86_REG_AX,self.keys.pop(0))
  elif number==0x21:
   assert ah in (0x3d,0x3f,0x3e),('Unexpected DOS IO',hex(ax))
   flags=uc.reg_read(UC_X86_REG_EFLAGS)&~1
   if ah==0x3d:
    assert ax&255==0,'File opened for writing'
    self.opens+=1;self.offset_read=0
    if self.error:uc.reg_write(UC_X86_REG_AX,2);flags|=1
    else:uc.reg_write(UC_X86_REG_AX,7)
   elif ah==0x3f:
    assert bx==7
    data=self.data[self.offset_read:self.offset_read+cx];self.offset_read+=len(data)
    uc.mem_write(uc.reg_read(UC_X86_REG_DS)*16+dx,data or b'\0')
    uc.reg_write(UC_X86_REG_AX,len(data))
   else:self.closes+=1;assert bx==7;uc.reg_write(UC_X86_REG_AX,0)
   uc.reg_write(UC_X86_REG_EFLAGS,flags)
  else:raise AssertionError(('Unexpected interrupt',number,hex(ax)))
 def choose(self):
  before=self.get('text_video_segment');entry=self.get('terminal_directory_entry');self.uc.reg_write(UC_X86_REG_ES,0x6666);result=self.call('terminal_directory_choose',limit=2000000)
  assert self.uc.reg_read(UC_X86_REG_ES)==0x6666
  assert self.uc.reg_read(UC_X86_REG_BP)==0xbabe and self.uc.reg_read(UC_X86_REG_SI)==0x1234 and self.uc.reg_read(UC_X86_REG_DI)==0x5678
  assert bytes(self.uc.mem_read(self.video,4000))==self.pattern
  assert self.cursor==0x0711 and self.shape==0x060f and self.get('text_video_segment')==before
  if result:assert self.get('terminal_directory_entry')==entry
  return result

def main():
 cases=[]
 def check(name,test):test();cases.append({'case':name,'passed':True});print(name,'passed')
 def navigation():
  a=Browser([0x4f00,0x4900,0x4700,0x5000,0x5100,0x4800,0x1c0d]);assert a.choose()==0 and a.get('terminal_directory_entry')==11
  assert a.pages==[1,191,181,1,11] and a.opens==a.closes==5
  assert b'SECRET-PW!' not in a.rendered and b'LITERAL targets // E edits selected entry' in a.rendered
  assert b'\x1b' not in a.rendered and b'\xdb' in a.rendered
 check('all-navigation-keys-real-reader-pages-sanitized-fields-no-password',navigation)
 def cancel():
  for mode,page in [(3,0),(3,2),(7,1)]:
   a=Browser([0x011b],mode=mode,page=page);a.put('terminal_directory_codes',1);assert a.choose()==1
   assert a.opens==a.closes==1 and b'LEGACY A..J' in a.rendered
  a=Browser([0x5000,0x011b]);a.put('terminal_directory_entry',49);assert a.choose()==1 and a.get('terminal_directory_entry')==49 and a.pages==[41]
 check('cancel-color-monochrome-active-page-and-cursor-shape-restore',cancel)
 def boundary():
  a=Browser([0x4800,0x4900,0x4f00,0x5000,0x5100,0x1c0d]);assert a.choose()==0 and a.get('terminal_directory_entry')==200 and a.pages==[1,191]
 check('home-end-and-page-edges-clamp-without-entry-zero-or201',boundary)
 def errors():
  a=Browser([],error=True);assert a.choose()==2 and a.opens==1 and not a.closes
  a=Browser([],mode=0x13);assert a.choose()==2 and not a.opens
 check('file-error-and-unsupported-mode-restore-with-no-selection',errors)
 result={'passed':True,'binary_sha256':hashlib.sha256((OUT/'BROWSER.EXE').read_bytes()).hexdigest(),'cases':cases,'scope':'Actual linked browser, original snapshots and real compiled directory reader. BIOS keys/video and DOS read-only filecalls are explicit OS fixtures; no UART or private files.'}
 (OUT/'checks.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
