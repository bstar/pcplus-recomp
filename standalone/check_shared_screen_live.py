#!/usr/bin/env python3
"""Check exclusive chooser/PROGRAM screen storage in the actual optional parent."""
import argparse,hashlib,json
from pathlib import Path
from unicorn.x86_const import *
from check_program_actions_live import LiveProgram
from terminal_memory import inspect_terminal_memory
from directory_fixtures import directory
from check_redisplay_live import Redisplay
import check_transport
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
class Screen(LiveProgram):
 def interrupt(self,u,n,d):
  if n==0x10:
   ax=u.reg_read(UC_X86_REG_AX);bx=u.reg_read(UC_X86_REG_BX)
   if ax>>8==6:u.mem_write(0xb8000,bytes([32,bx>>8])*2000);return
   if ax>>8==9:
    row,col=divmod(self.cursor,256);assert row<25 and col<80
    u.mem_write(0xb8000+(row*80+col)*2,bytes([ax&255,bx&255]));return
  if n==0x21 and u.reg_read(UC_X86_REG_AX)>>8==0x3d:
   # External DOS open failure, after the real chooser has saved its screen.
   u.reg_write(UC_X86_REG_AX,2);self.set_carry(True);return
  return super().interrupt(u,n,d)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);a=p.parse_args();binary=a.terminal.resolve()
 mft=json.loads((binary.parent/'manifest.json').read_text());assert sha(binary)==mft['binary_sha256']
 for name,digest in mft['sources'].items():assert sha(ROOT/name)==digest,name
 memory=inspect_terminal_memory(binary,binary.parent/'terminal.map');assert memory['program_browser_screen_overlay']and memory['editor_viewer_screen_overlay']and memory['far_ui_storage_bytes']==12000
 check_transport.BINARY=binary;check_transport.MAP=binary.parent/'terminal.map';refusals=0
 for owner in('terminal_program_pending','terminal_program_active','terminal_browser_screen_owned','terminal_editor_screen_owned','_redisplay_active'):
  width=1 if owner.endswith('screen_owned')else 2
  m=Screen();m.put(owner,1,width)
  saved=bytes(m.uc.mem_read(m.symbols['browser_screen'],4000));screen=bytes(m.uc.mem_read(0xb8000,4000))
  assert m.call('terminal_directory_choose')==2,owner
  assert bytes(m.uc.mem_read(m.symbols['browser_screen'],4000))==saved and bytes(m.uc.mem_read(0xb8000,4000))==screen
  assert m.get(owner,width)==1
  refusals+=1
 m=Screen();m.put('terminal_browser_screen_owned',1,1);saved=bytes(m.uc.mem_read(m.symbols['program_screen'],4000))
 m.record(0,b'OWNED.COM',1)
 assert m.call('terminal_program_start',ax=m.offset('terminal_action_definitions')+2)==2 and not m.get('terminal_program_pending')and not m.children
 assert bytes(m.uc.mem_read(m.symbols['program_screen'],4000))==saved;refusals+=1
 for owner in('_redisplay_active','terminal_program_pending','terminal_program_active','terminal_editor_screen_owned'):
  m=Screen();width=1 if owner.endswith('screen_owned')else 2;m.put(owner,1,width)
  saved=bytes(m.uc.mem_read(m.symbols['ed_screen'],4000));screen=bytes(m.uc.mem_read(0xb8000,4000))
  assert m.call('terminal_directory_edit',[m.offset('terminal_action_definitions')])==0
  assert m.get(owner,width)==1 and bytes(m.uc.mem_read(m.symbols['ed_screen'],4000))==saved
  assert bytes(m.uc.mem_read(0xb8000,4000))==screen;refusals+=1
 for owner in('terminal_browser_screen_owned','terminal_editor_screen_owned'):
  m=Redisplay();m.put(owner,1,1);saved=bytes(m.uc.mem_read(m.symbols['redisplay_live'],4000));screen=bytes(m.uc.mem_read(0xb8000,4000))
  m.call('terminal_redisplay_key',ax=0x8400)
  assert m.uc.reg_read(UC_X86_REG_EFLAGS)&1 and not m.get('_redisplay_active')
  assert m.get(owner,1)==1 and bytes(m.uc.mem_read(m.symbols['redisplay_live'],4000))==saved and bytes(m.uc.mem_read(0xb8000,4000))==screen;refusals+=1
 editor_cycles=0
 for key in(27,0x4400):
  m=Screen([key]);record=m.symbols['terminal_action_definitions'];m.uc.mem_write(record,directory()[250:364])
  if 'terminal_trap_phase'in m.symbols:m.put('terminal_trap_phase',1)
  m.put('terminal_browser_screen_owned',1,1)
  browser=bytes(m.uc.mem_read(m.symbols['browser_screen'],4000))
  assert m.call('terminal_directory_edit',[m.offset('terminal_action_definitions')],limit=5000000)==int(key==0x4400)
  assert not m.get('terminal_editor_screen_owned',1)and m.get('terminal_browser_screen_owned',1)==1
  assert bytes(m.uc.mem_read(0xb8000,4000))==m.original_screen and bytes(m.uc.mem_read(m.symbols['browser_screen'],4000))==browser
  editor_cycles+=1
 viewer=Redisplay();viewer.seed(b'Before editor\rAfter editor\r');screen=bytes(viewer.uc.mem_read(0xb8000,4000));viewer.open();viewer.key(27)
 assert bytes(viewer.uc.mem_read(0xb8000,4000))==screen and not viewer.get('_redisplay_active')
 cycles=0
 for error in(0,2,8):
  m=Screen(exec_error=error,mutate_child=not error)
  # The real open-error branch acquires, paints and releases the chooser's
  # snapshot before another modal owner may reuse the same physical cells.
  assert m.call('terminal_directory_choose',limit=3000000)==2
  assert not m.get('terminal_browser_screen_owned',1)
  assert bytes(m.uc.mem_read(0xb8000,4000))==m.original_screen
  assert m.queue()==0;m.safe();m.restored()
  assert bytes(m.uc.mem_read(m.symbols['program_screen'],4000))==m.original_screen
  assert not m.get('terminal_program_active')and not m.get('terminal_program_pending')
  assert m.call('terminal_directory_choose',limit=3000000)==2
  assert not m.get('terminal_browser_screen_owned',1)and bytes(m.uc.mem_read(0xb8000,4000))==m.original_screen
  cycles+=1
 report=dict(passed=True,binary_sha256=sha(binary),owner_refusals=refusals,restore_cycles=cycles,editor_restore_cycles=editor_cycles,viewer_restore_cycles=1,reclaimed_bytes=8000,sources=mft['sources'],checker_sha256=sha(Path(__file__)),original_inputs=[],scope=__doc__+' Bidirectional chooser/editor/viewer/PROGRAM refusals, editor cancel/accept and viewer screen restoration. Real chooser open-error acquisition/restoration and actual PROGRAM/child/error restoration. DOS open and child execution are modeled kernel boundaries; real DOS nested launches are separate.')
 (binary.parent/'shared-screen-checks.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS shared screen:',refusals,'owner refusals,',cycles,'PROGRAM,',editor_cycles,'editor and1 viewer restore cycles, 8000 bytes reclaimed')
if __name__=='__main__':main()
