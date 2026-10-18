#!/usr/bin/env python3
"""Replay the real Synchronet failure wire and recovered FF branches in DOS code."""
import argparse,hashlib,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'standalone'))
from dos_image import DosImage
from check_render import Render
from unicorn import UC_HOOK_CODE,UC_HOOK_INTR
from unicorn.x86_const import UC_X86_REG_AX,UC_X86_REG_SP,UC_X86_REG_IP
class MissingService(Exception):pass
class Terminal(Render):
 def __init__(self,binary,map_path):
  DosImage.__init__(self,binary,map_path);self.positions=[];self.calls=[];self.video=0xb8000;self.data=b'';self.index=0
  self.uc.mem_write(self.video,b'X\x07'*2000);self.uc.hook_add(UC_HOOK_INTR,self.interrupt);self.uc.hook_add(UC_HOOK_CODE,self.hook)
 def hook(self,u,address,length,_):
  if address==self.symbols['terminal_abort']:raise MissingService(u.reg_read(UC_X86_REG_AX),self.index)
  if address in (self.symbols['ansi_next_byte'],self.symbols['ansi_unread_byte']):
   if address==self.symbols['ansi_unread_byte']:self.index-=1;value=0
   else:
    value=self.data[self.index] if self.index<len(self.data) else 0xffff
    if value!=0xffff:self.index+=1
   sp=u.reg_read(UC_X86_REG_SP);target=struct.unpack('<H',u.mem_read(self.data_base+sp,2))[0]
   u.reg_write(UC_X86_REG_AX,value);u.reg_write(UC_X86_REG_SP,sp+2);u.reg_write(UC_X86_REG_IP,target)
 def feed(self,data):
  self.data=data;self.index=0
  while self.index<len(data):
   value=data[self.index];self.index+=1;self.call('terminal_receive_character',(value,),limit=500000)

def main():
 p=argparse.ArgumentParser();p.add_argument('--binary',type=Path,default=ROOT/'build/terminal/TERMINAL.EXE');p.add_argument('--map',type=Path,default=ROOT/'build/terminal/terminal.map');p.add_argument('--wire',type=Path,help='Optional explicitly selected private captured serial stream');a=p.parse_args();cases=[]
 def check(name,fn):fn();cases.append({'case':name,'passed':True});print(name,'passed')
 def synthetic_wire():
  t=Terminal(a.binary,a.map);data=b'HELLO\r\n\x1b[s\x1b[0c\x1b[255B\x1b[255C\x1b[6n\x1b[u\x1b[2J\x1b[H\x0cREADY'
  t.feed(data);assert t.index==len(data) and not t.get('csi_unimplemented_service')
 check('synthetic-query-clearhome-formfeed-through-real-input-dispatch',synthetic_wire)
 if a.wire:
  def wire():
   t=Terminal(a.binary,a.map);data=a.wire.read_bytes();t.feed(data)
   assert t.index==len(data) and not t.get('csi_unimplemented_service')
  check('explicitly-selected-captured-wire-consumed',wire)
 def branches():
  for profile,color,mode8ff8,want in [(4,1,0,(6,7)),(4,0,1,(6,7)),(20,1,0,(5,8)),(4,0,0,(0,0))]:
   t=Terminal(a.binary,a.map);t.put('csi_terminal_id',profile);t.put('attributes_monochrome',0);t.put('attributes_color_mode',color);t.put('terminal_tab_mode_8ff8',mode8ff8);t.position(5,7)
   before=t.cells();t.feed(b'\x0c');assert (t.get('screen_cursor_row'),t.get('screen_cursor_column'))==want
   if want==(0,0):assert t.cells()==[0x0720]*2000
   else:assert t.cells()==before
 check('original-profile4-linefeed-highprofile-right-and-clearhome-branches',branches)
 def flags():
  for flag in (0,1):
   t=Terminal(a.binary,a.map);t.put('attributes_monochrome',0);t.put('attributes_color_mode',0);t.put('terminal_newline_mode_9020',flag);t.put('attributes_bold_active',1);t.feed(b'\x0c')
   assert t.get('attributes_bold_active')==(0 if flag else 1)
 check('attribute-normalization-condition',flags)
 def ansi_clear():
  for profile in (6,7):
   for origin in (0,3):
    for attribute in (7,0x1e,0x70):
     t=Terminal(a.binary,a.map);t.put('csi_terminal_id',profile);t.put('attributes_monochrome',1);t.put('attributes_current',attribute);t.put('csi_origin_row',origin);t.position(8,17)
     t.feed(b'\x0c')
     assert t.cells()==[(attribute<<8)|32]*2000,(profile,origin,attribute)
     assert (t.get('screen_cursor_row'),t.get('screen_cursor_column'))==(origin,0)
  # Direct CSI helper selects erase attribute for non-ANSI profiles.
  t=Terminal(a.binary,a.map);t.put('attributes_monochrome',0);t.put('attributes_current',0x1e);t.uc.mem_write(t.symbols['csi_erase_attribute'],b'\x70');t.call('csi_service_da12')
  assert t.cells()==[0x7020]*2000
 check('recovered-ansi-ibmpc-fullscreen-erase-attribute-and-origin-home',ansi_clear)
 def profiles():
  for profile,da in [(4,b'\x1b[?62;2c'),(6,b'\x1b[?1;2c')]:
   t=Terminal(a.binary,a.map);t.put('csi_terminal_id',profile);t.put('attributes_monochrome',int(profile==6));t.put('terminal_dec_keys',1)
   t.call('terminal_initialize_keymap')
   t.position(9,19);t.feed(b'\x1b[0c\x1b[5n\x1b[6n')
   reply=bytes(t.uc.mem_read(t.symbols['terminal_tx_buffer'],t.get('terminal_tx_count')))
   assert reply==da+b'\x1b[0n\x1b[10;20R',(profile,reply)
   # Original startup calls keyboard_mode('['); both profiles are DEC-key enabled.
   t.call('terminal_keyboard_mode',[ord('[')])
   for slot in (50,72):assert bytes(t.uc.mem_read(t.symbols['terminal_keymap']+slot*12,4))==b'\x1b[A\0'
   t.feed(b'\x1b[?1h')
   for slot in (50,72):assert bytes(t.uc.mem_read(t.symbols['terminal_keymap']+slot*12,4))==b'\x1bOA\0'
   t.feed(b'\x1b[?1l')
   for slot in (50,72):assert bytes(t.uc.mem_read(t.symbols['terminal_keymap']+slot*12,4))==b'\x1b[A\0'
 check('vt220-and-ansi-profile-da-status-cursor-and-decckm-real-paths',profiles)
 out=ROOT/'build/bbs-lab/synchronet/formfeed-build';out.mkdir(parents=True,exist_ok=True)
 result={'binary_sha256':hashlib.sha256(a.binary.read_bytes()).hexdigest(),'cases':cases,'wire_capture':str(a.wire) if a.wire else 'not selected; public tests use synthetic data','scope':'Actual linked input-dispatch/control/renderer DOS instructions and declared BIOS model. Profile4(VT220) FF linefeeds; profiles6/7(ANSI/IBM PC) clear the physical screen and home to origin. Source-owned state fixtures cover these specific branches; full profile initialization is not recovered.'}
 (out/'checks.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
