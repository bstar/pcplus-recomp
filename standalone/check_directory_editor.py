#!/usr/bin/env python3
"""Actual linked editor+far snapshots, explicit BIOS keys/video fixtures."""
from pathlib import Path
import hashlib,json,struct
from unicorn import UC_HOOK_INTR,UC_HOOK_INSN
from unicorn.x86_const import *
from dos_image import DosImage
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/directory-editor'
ESC=0x011b;F10=0x4400;TAB=0x0f09;DEL=0x5300;HOME=0x4700;END=0x4f00
TEXT=[(0,24),(25,20),(52,8),(75,10),(86,8),(95,8),(105,8)]
NUMBERS=[(2,46,2,0,8),(3,48,1,0,4),(4,49,1,7,8),(5,50,1,1,2),(6,51,1,0,1),(12,73,1,0,255),(13,72,1,0,255),(14,74,1,0,1),(15,104,1,0,8)]
def typed(value):return list(value.encode('ascii'))
class Editor(DosImage):
 def __init__(self,keys,mode=3,page=0):
  super().__init__(OUT/'EDITOR.EXE',OUT/'editor.map');self.keys=list(keys);self.mode=mode;self.page=page;self.video=(0xb0000 if mode==7 else 0xb8000)+page*4096
  self.pattern=bytes(i%256 for i in range(4000));self.uc.mem_write(self.video,self.pattern);self.uc.mem_write(0x44e,struct.pack('<H',page*4096));self.cursor=0x0711;self.shape=0x060f;self.rendered=bytearray();self.frames=[]
  self.original=bytes(self.uc.mem_read(self.symbols['editor_record'],114));self.uc.hook_add(UC_HOOK_INTR,self.interrupt)
  for instruction in [UC_X86_INS_IN,UC_X86_INS_OUT]:self.uc.hook_add(UC_HOOK_INSN,self.no_ports,None,1,0,instruction)
 def no_ports(self,*args):raise AssertionError('Editor attempted port IO')
 def interrupt(self,uc,number,_):
  ax=uc.reg_read(UC_X86_REG_AX);ah=ax>>8;bx=uc.reg_read(UC_X86_REG_BX);cx=uc.reg_read(UC_X86_REG_CX);dx=uc.reg_read(UC_X86_REG_DX)
  assert number in (0x10,0x16),('Editor attempted DOS/non-BIOS IO',number)
  if number==0x16:
   assert ah==0 and self.keys,'Unexpected blocking input'
   # Before every input the caller must remain unmodified, even after staged edits.
   assert bytes(uc.mem_read(self.symbols['editor_record'],114))==self.original
   self.frames.append(bytes(uc.mem_read(self.video,4000)));uc.reg_write(UC_X86_REG_AX,self.keys.pop(0));return
  if ah==15:uc.reg_write(UC_X86_REG_AX,80*256+self.mode);uc.reg_write(UC_X86_REG_BX,self.page*256)
  elif ah==3:uc.reg_write(UC_X86_REG_CX,self.shape);uc.reg_write(UC_X86_REG_DX,self.cursor)
  elif ah==2:self.cursor=dx
  elif ah==1:self.shape=cx
  elif ah==6:self.uc.mem_write(self.video,bytes([32,bx>>8])*2000)
  elif ah==9:
   assert bx>>8==self.page and cx==1
   row,col=divmod(self.cursor,256);assert row<25 and col<80
   uc.mem_write(self.video+(row*80+col)*2,bytes([ax&255,bx&255]));self.rendered.append(ax&255)
  else:raise AssertionError(('Unexpected BIOS function',hex(ax)))
 def run(self):
  old=self.get('text_video_segment');self.uc.reg_write(UC_X86_REG_ES,0x6666)
  result=self.call('terminal_directory_edit',[self.offset('editor_record')],limit=10000000)
  for register,value in [(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678),(UC_X86_REG_ES,0x6666)]:assert self.uc.reg_read(register)==value
  assert bytes(self.uc.mem_read(self.video,4000))==self.pattern and self.cursor==0x0711 and self.shape==0x060f and self.get('text_video_segment')==old
  record=bytes(self.uc.mem_read(self.symbols['editor_record'],114));assert b'Secret123' not in self.rendered and b'Xecret123' not in self.rendered
  if not result:assert record==self.original
  return result,record

def main():
 cases=[];checks=0
 def check(name,test):test();cases.append({'case':name,'passed':True});print(name,'passed',flush=True)
 def atomic():
  for keys,status in [([F10],1),(typed('Changed')+[TAB]+typed('New')+[ESC],0),([0x0f00,TAB,0x4800,0x5000,ESC],0)]:
   a=Editor(keys);result,record=a.run();assert result==status and record==a.original
  a=Editor(typed('X')+[F10]);status,record=a.run();assert status==1 and record==b'X'+a.original[1:]
 check('accept-cancel-full114-atomicity-opaque-tails-and-field-navigation',atomic)
 def editing():
  a=Editor([0x4d00,0x5200]+typed('Z')+[DEL,0x0e08,END]+typed('!')+[F10]);status,record=a.run()
  assert status==1 and record[:9]==b'Oiginal!\0' and record[9:]==a.original[9:]
  a=Editor([END]+typed('012345678901234567890123456789')+[F10]);status,record=a.run();assert status==1 and record[:25]==b'Original0123456789012345\0' and record[25:]==a.original[25:]
  # NumLock keypad ASCII must type digits, not act as navigation keys.
  a=Editor([0x4737,F10]);status,record=a.run();assert status==1 and record[0]==ord('7')
 check('insert-overwrite-delete-backspace-home-end-bounds-and-keypad-ASCII',editing)
 def strings_password():
  for field,(offset,width) in zip([0,1,7,8,9,10,11],TEXT):
   a=Editor([TAB]*field+typed('X')+[F10]);status,record=a.run();assert status==1 and record[offset]==88 and record[:offset]==a.original[:offset] and record[offset+1:]==a.original[offset+1:]
   assert b'*********' in a.rendered
 check('all-text-fields-bounded-password-always-masked',strings_password)
 def numeric():
  for field,offset,width,lo,hi in NUMBERS:
   for value in (lo,hi):
    a=Editor([TAB]*field+[HOME]+[DEL]*5+typed(str(value))+[F10]);status,record=a.run();assert status==1,(field,value)
    expected=bytearray(a.original);expected[offset:offset+width]=value.to_bytes(width,'little');assert record==expected
   for value in (hi+1,65537):
    a=Editor([TAB]*field+[HOME]+[DEL]*5+typed(str(value))+[F10,ESC]);status,record=a.run();assert status==0 and b'INVALID VALUE' in a.rendered
  a=Editor([TAB]*4+[HOME]+[DEL]*5+typed('6')+[TAB,ESC]);assert a.run()[0]==0 and b'INVALID VALUE' in a.rendered
 check('all-numeric-ranges-overflow-and-invalid-input-never-accepted',numeric)
 def legacy_invalid():
  a=Editor([F10,ESC]);record=bytearray(a.original);record[0:25]=b'X'*25;a.uc.mem_write(a.symbols['editor_record'],bytes(record));a.original=bytes(record)
  assert a.run()[0]==0 and b'INVALID VALUE' in a.rendered
  a=Editor([F10,ESC]);record=bytearray(a.original);record[49]=6;a.uc.mem_write(a.symbols['editor_record'],bytes(record));a.original=bytes(record);assert a.run()[0]==0
 check('untouched-malformed-storage-rejected-unless-cancelled',legacy_invalid)
 def context():
  for mode,page in [(3,2),(7,1)]:assert Editor([ESC],mode,page).run()[0]==0
  a=Editor([],0x13);assert a.run()[0]==0 and not a.rendered
 check('active-pages-monochrome-unsupported-mode-and-complete-display-restore',context)
 result={'passed':True,'binary_sha256':hashlib.sha256((OUT/'EDITOR.EXE').read_bytes()).hexdigest(),'cases':cases,'scope':'Actual linked maintained editor, maintained far snapshots and recovered packed cells. Explicit BIOS keyboard/video fixture, all DOS/port IO forbidden. Caller114bytes checked unchanged before everykey; synthetic secrets only.'}
 (OUT/'checks.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
