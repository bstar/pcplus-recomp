#!/usr/bin/env python3
"""Confirmed4/6 profiles, explicit KBD transaction and clean RIS baseline."""
import hashlib,json,struct
from unicorn.x86_const import *
from check_live_setup_link import Link
from check_directory_live import word
from check_scroll import Scroll
from check_program_actions_live import ROOT,BINARY
class Profile(Link):
 def __init__(self):
  self.keyboard_file=b''.join(b''.join(('P%d-%02d'%(profile,slot)).encode().ljust(12,b'\0') for slot in range(79)) for profile in range(7))
  self.key_position=0;self.key_open_error=self.key_read_error=self.key_close_error=self.key_seek_error=0;self.key_limit=None
  super().__init__()
 def cells(self):return list(struct.unpack('<2000H',self.uc.mem_read(0xb8000,4000)))
 def interrupt(self,u,n,data):
  ax=u.reg_read(UC_X86_REG_AX);ah=ax>>8;handle=u.reg_read(UC_X86_REG_BX)
  if n==0x10 and ah in (6,7):return Scroll.interrupt(self,u,n,data)
  if n==0x21 and ah==0x3d and self.string(u.reg_read(UC_X86_REG_DS),u.reg_read(UC_X86_REG_DX)).upper().endswith(b'.KBD'):
   path=self.string(u.reg_read(UC_X86_REG_DS),u.reg_read(UC_X86_REG_DX));self.file_calls.append(('key-open',path));self.key_position=0
   u.reg_write(UC_X86_REG_AX,self.key_open_error or 8);self.set_carry(bool(self.key_open_error));return
  if n==0x21 and ah==0x42 and handle==8:
   offset=(u.reg_read(UC_X86_REG_CX)<<16)|u.reg_read(UC_X86_REG_DX)
   self.key_position=(len(self.keyboard_file) if ax&255==2 else 0)+offset
   self.file_calls.append(('key-seek',self.key_position))
   u.reg_write(UC_X86_REG_AX,self.key_seek_error or self.key_position&65535);u.reg_write(UC_X86_REG_DX,self.key_position>>16);self.set_carry(bool(self.key_seek_error));return
  if n==0x21 and ah==0x3f and handle==8:
   end=self.key_position+u.reg_read(UC_X86_REG_CX)
   if self.key_limit is not None:end=min(end,self.key_limit)
   block=self.keyboard_file[self.key_position:end];self.file_calls.append(('key-read',len(block)))
   if not self.key_read_error:u.mem_write(u.reg_read(UC_X86_REG_DS)*16+u.reg_read(UC_X86_REG_DX),block);self.key_position+=len(block)
   u.reg_write(UC_X86_REG_AX,self.key_read_error or len(block));self.set_carry(bool(self.key_read_error));return
  if n==0x21 and ah==0x3e and handle==8:
   self.file_calls.append(('key-close',8));u.reg_write(UC_X86_REG_AX,self.key_close_error);self.set_carry(bool(self.key_close_error));return
  return super().interrupt(u,n,data)
 def explicit(self):
  self.put('terminal_option_mask',self.get('terminal_option_mask')|512)
  self.uc.mem_write(self.symbols['terminal_keyboard_path'],b'TEST.KBD\0')
  assert self.call('terminal_load_keyboard')==0
  assert self.call('terminal_reset_capture')==0
  self.call('terminal_setup_profile_bind');assert self.get('terminal_setup_keyboard_bound')==1
  return self
 def keymap(self):return bytes(self.uc.mem_read(self.symbols['terminal_keymap'],948))
 def intact(self):
  assert self.vector_value()==self.parent_vector and (self.dll,self.dlm,self.lcr,self.mcr,self.ier)==(3,0,3,0xb,1)
  assert {n:self.get(n,1 if n.startswith('uart_saved_') else 2) for n in self.baseline}==self.baseline
  assert self.data_reads==0 and bytes(self.rx)==b'R' and not self.tx
 def feed(self,wire):
  self.receive_irq(wire)
  while self.get('uart_rx_count'):
   byte=self.call('uart_receive_byte');self.call('terminal_receive_character',[byte],limit=1500000)
  for _ in range(100):
   if not self.get('terminal_tx_count'):return
   self.poll()
  raise AssertionError('TX did not drain')
def main():
 cases=[]
 def done(name,n):cases.append(dict(case=name,inputs=n,passed=True));print(name,n,flush=True)
 for explicit in (False,True):
  m=Profile();m.explicit() if explicit else None;original=m.keymap()
  for target in [6,4,6]:
   m.data_reads=0
   # Dirty peer state must not become the target profile's reset defaults.
   m.put('csi_origin_mode',1);m.put('csi_origin_row',3);m.put('csi_origin_bottom',20);m.put('attributes_bold_active',1);m.put('attributes_current',0x2f)
   m.uc.mem_write(m.symbols['terminal_tab_stops'],b'\xaa'*30);m.uc.mem_write(m.symbols['terminal_keymap'],b'\xbb'*948)
   m.launch(word(m.raw,0x194,target));assert m.get('terminal_setup_profile_status')==1 and m.get('csi_terminal_id')==target
   assert m.get('attributes_monochrome')==int(target==6) and m.get('attributes_current')==7 and m.get('attributes_bold_active')==0
   assert m.get('screen_cursor_row')==m.get('screen_cursor_column')==m.get('csi_origin_mode')==m.get('csi_origin_row')==0
   assert m.get('csi_origin_bottom')==24 and m.cells()==[0x0720]*2000
   expected=m.keyboard_file[target*948:(target+1)*948] if explicit else original
   assert m.keymap()==expected and bytes(m.uc.mem_read(m.symbols['terminal_tab_stops'],30))!=b'\xaa'*30
   m.intact();m.feed(b'\x1b[0c');assert bytes(m.tx)==(b'\x1b[?1;2c' if target==6 else b'\x1b[?62;2c')
   m.tx.clear();m.uc.mem_write(m.symbols['terminal_keymap'],b'\xcc'*948);m.put('csi_terminal_id',4 if target==6 else 6)
   m.feed(b'\x1bc');assert m.get('csi_terminal_id')==target and m.keymap()==expected and m.cells()==[0x0720]*2000
 done('both-directions-default-and-explicit-mappings-clean-state-fresh-DA-and-new-RIS',6)
 for choice in [ord('N'),27,32,13]:
  m=Profile().explicit();old=m.keymap();m.launch(word(m.raw,0x194,6),choice)
  assert m.get('csi_terminal_id')==4 and m.get('terminal_setup_profile_status')==2 and m.keymap()==old
  assert bytes(m.uc.mem_read(0xb8000,4000))==m.original_screen;m.intact()
 done('declined-profile-preserves-screen-cursor-keymap-and-connection',4)
 for error in ['open','seek','read','close','size','short','slot']:
  m=Profile().explicit();old=m.keymap()
  if error in ['open','seek','read','close']:setattr(m,'key_'+error+'_error',5)
  elif error=='size':m.keyboard_file=m.keyboard_file[:-1]
  elif error=='short':m.key_limit=6*948+100
  else:m.keyboard_file=m.keyboard_file[:6*948]+b'X'*12+m.keyboard_file[6*948+12:]
  m.launch(word(word(m.raw,0x194,6),0x1a4,65535))
  assert m.get('terminal_setup_profile_status')==3 and m.get('csi_terminal_id')==4 and m.keymap()==old
  assert m.get('terminal_break_delay_units')==65535 and b'Could not load profile keyboard' in m.local_text
  assert bytes(m.uc.mem_read(0xb8000,4000))==m.original_screen;m.intact()
 done('explicit-keyboard-open-seek-read-close-size-short-and-slot-failures-no-fallback',7)
 m=Profile().explicit();m.child_cwd=b'D:\\OTHER';m.file_calls.clear();m.launch(word(m.raw,0x194,6))
 assert ('key-open',b'D:\\WORK\\TEST.KBD') in m.file_calls and m.get('csi_terminal_id')==6;m.intact()
 m=Profile().explicit();m.cwd=b'D:\\'+b'A'*62;m.call('terminal_setup_profile_bind');assert m.get('terminal_setup_keyboard_bound')==0
 m.cwd=b'D:\\WORK';m.file_calls.clear();m.launch(word(m.raw,0x194,6))
 assert not any(c[0]=='key-open' for c in m.file_calls) and m.get('terminal_setup_profile_status')==3;m.intact()
 done('startup-canonical-keyboard-binding-and-overlong-absolute-path-denial',2)
 for profile_yes in (False,True):
  for serial_yes in (False,True):
   m=Profile();m.after_raw=word(word(m.raw,0x194,6),2,8)
   m.keys.extend([0x7100,ord('Y' if profile_yes else 'N'),ord('Y' if serial_yes else 'N')]);m.poll();m.safe()
   assert not m.keys and m.get('csi_terminal_id')==(6 if profile_yes else 4)
   assert (m.dll,m.dlm)==((1,0) if serial_yes else (3,0))
   assert m.get('terminal_setup_profile_status')==(1 if profile_yes else 2) and m.get('terminal_setup_link_status')==(1 if serial_yes else 2)
   assert m.vector_value()==m.parent_vector and m.data_reads==0 and bytes(m.rx)==b'R'
 done('profile-and-serial-confirmations-are-independent-and-consume-only-their-answers',4)
 m=Profile().explicit();m.key_open_error=5;m.after_raw=word(word(m.raw,0x194,6),2,8)
 m.keys.extend([0x7100,ord('Y'),13]);m.poll();m.safe()
 assert not m.keys and m.get('csi_terminal_id')==4 and m.get('terminal_setup_profile_status')==3 and (m.dll,m.dlm)==(1,0)
 done('profile-import-failure-can-retain-profile-and-apply-confirmed-serial',1)
 m=Profile();m.child_busy=True;m.after_raw=word(word(m.raw,0x194,6),2,8)
 m.keys.extend([0x7100,ord('Y'),ord('Y'),13]);m.poll();m.safe()
 assert not m.keys and m.get('csi_terminal_id')==6 and m.get('terminal_setup_link_status')==3 and (m.dll,m.dlm)==(3,0)
 done('busy-serial-gate-can-retain-link-and-apply-confirmed-profile',1)
 m=Profile();m.put('connection_state',6);m.launch(word(m.raw,0x194,6));m.intact()
 assert m.get('connection_state')==6;m.feed(b'\x1b[0c');assert bytes(m.tx)==b'\x1b[?1;2c' and m.get('connection_state')==6
 done('established-session-stays-online-with-new-profile-DA-and-pending-input',1)
 m=Profile();before=m.keymap()
 for ptr in (0,65535,65536-947):assert m.call('terminal_build_keymap',ax=ptr)==1 and m.keymap()==before
 ptr=m.stage_near(bytes(948));assert m.call('terminal_build_keymap',ax=ptr)==0
 assert bytes(m.uc.mem_read(m.data_base+ptr,948))==before and m.keymap()==before
 done('default-builder-rejects-null-wrap-and-stages-in-caller-owned-stack',4)
 m=Profile();before=m.keymap();assert m.call('terminal_setup_profile_stage',ax=5)==2 and m.keymap()==before
 m.put('terminal_parser_active',1);assert m.call('terminal_setup_profile_stage',ax=6)==2 and m.keymap()==before
 done('unsupported-profile-and-active-parser-denied-before-staging',2)
 result=dict(passed=True,binary_sha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),inputs=sum(c['inputs'] for c in cases),cases=cases,scope='Actual linked profile proposal, confirmation, strict KBD import/canonical binding, renderer/reset, keymaps, new DA responses and subsequent RIS. Kernel/BIOS/UART boundaries modeled; no product function mocked. Supported maintained profiles4/6 only, source-owned defaults rather than original profile loader; actual DOS editor tests remain separate.')
 (ROOT/'build/terminal/live-setup-profile-checks.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
