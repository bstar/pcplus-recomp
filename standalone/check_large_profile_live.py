#!/usr/bin/env python3
"""Execute full-height SETUP/profile adoption through actual EXEC and return owners.
Kernel, BIOS and UART boundaries modeled; not actual DOS child or BBS acceptance.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn.x86_const import *
import check_transport as transport
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 binary=a.terminal.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 mfest=json.loads((binary.parent/'manifest.json').read_text());assert mfest['experimental_program_display_owner'] and sha(binary)==mfest['binary_sha256']
 for n,h in mfest['sources'].items():assert sha(ROOT/n)==h,n
 transport.BINARY=binary;transport.MAP=binary.parent/'terminal.map'
 from program_display_model import Program
 from check_live_setup_profile import Profile as SettingsBoundary
 from check_directory_live import word
 from check_recording_rx_live import ordinary
 class Profile(Program,SettingsBoundary):
  def __init__(self):
   super().__init__();raw=bytearray(self.raw);struct.pack_into("<HH",raw,0x4e4,8,8);self.raw=bytes(raw)
  def interrupt(self,u,n,d):
   if n==0x21:
    ax=u.reg_read(UC_X86_REG_AX);ah=ax>>8;handle=u.reg_read(UC_X86_REG_BX)
    if ax==0x6000 or ah==0x3d or ah==0x3f and handle in (7,8) or ah==0x3e and handle in (7,8) or ah==0x42 and handle==8:
     return SettingsBoundary.interrupt(self,u,n,d)
   return super().interrupt(u,n,d)
  def launch_at_height(self,rows,hidden,target,choice=ord('Y'),explicit=False):
   if explicit:self.explicit()
   self.setup(rows,hidden);self.prompt_key_sent=True
   self.put('modes_value_1d1a',1)
   before=bytes(self.uc.mem_read(0xb8000,rows*160));history=bytes(self.uc.mem_read(self.symbols['terminal_history_buffer'],63000))
   self.after_raw=word(self.raw,0x194,target);self.keys.extend([0x7100,choice]);self.poll()
   assert self.get('terminal_program_pending') and self.get('terminal_program_kind')==1
   self.safe()
   assert not self.get('terminal_quit') and not self.get('terminal_program_active') and not self.get('terminal_program_pending')
   assert self.vrows==self.get('ui_window_rows')==rows and self.get('ui_flow_suppressed')==hidden
   assert self.get('csi_row_count')==rows-(0 if hidden else 1)
   assert bytes(self.uc.mem_read(self.symbols['terminal_history_buffer'],63000))==history
   return before
 cases=[]
 def done(name,n):cases.append(dict(case=name,inputs=n,passed=True));print(name,n,'PASS',flush=True)
 count=0
 for rows in [25,28,43,50]:
  for hidden in [0,1]:
   for explicit in [False,True]:
    m=Profile()
    for target in [6,4,6]:
     before=m.launch_at_height(rows,hidden,target,explicit=explicit)
     assert m.get('terminal_setup_profile_status')==1 and m.get('csi_terminal_id')==target,(rows,hidden,explicit,target,{n:m.get(n) for n in ['terminal_setup_profile_status','csi_terminal_id','terminal_setup_apply_status','terminal_program_status','terminal_setup_binding_status','terminal_setup_keyboard_bound','terminal_option_mask']},bytes(m.uc.mem_read(m.symbols['terminal_setup_outcome'],8)).hex(),m.file_calls[-8:],m.local_text)
     effective=rows-(0 if hidden else 1)
     assert bytes(m.uc.mem_read(0xb8000,effective*160))==b' \x07'*(effective*80)
     if not hidden:assert bytes(m.uc.mem_read(0xb8000+effective*160,160))==before[effective*160:rows*160]
     assert m.value('csi_row_count')==effective and m.get('screen_cursor_row')==m.get('screen_cursor_column')==0
     assert not m.get('_program_display_ready') and not m.get('terminal_setup_profile_ready') and not m.keys
     expected=m.keyboard_file[target*948:(target+1)*948] if explicit else None
     if expected is not None:assert m.keymap()==expected
     # Real subsequent RIS must retain the new profile AND accepted geometry.
     ordinary(m,b'\x1b[25;60H\x1bc\x1b[0c');m.drain()
     assert m.get('csi_terminal_id')==target and m.get('csi_row_count')==effective
     assert bytes(m.tx).endswith(b'\x1b[?1;2c' if target==6 else b'\x1b[?62;2c')
     if expected is not None:assert m.keymap()==expected
     count+=1
 done('all-heights-status-states-default-explicit-keyboards-confirmed-profile-and-following-RIS',count)
 for rows in [25,28,43,50]:
  for choice in [ord('N'),27,13]:
   m=Profile();profile=m.get('csi_terminal_id');before=m.launch_at_height(rows,0,6 if profile==4 else 4,choice)
   assert m.get('terminal_setup_profile_status')==2 and m.get('csi_terminal_id')==profile
   assert bytes(m.uc.mem_read(0xb8000,rows*160))==before
 done('declined-profiles-retain-entire-large-parent-frame-and-profile',12)
 for n,h in mfest['sources'].items():assert sha(ROOT/n)==h,n
 inputs=[Path(__file__),ROOT/'standalone/program_display_model.py',ROOT/'standalone/check_live_setup_profile.py',ROOT/'standalone/live_setup_kernel.py']
 report=dict(passed=True,terminal_sha256=sha(binary),manifest_sha256=sha(binary.parent/'manifest.json'),inputs=sum(c['inputs'] for c in cases),cases=cases,sources={str(p.relative_to(ROOT)):sha(p) for p in inputs},scope=__doc__)
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
