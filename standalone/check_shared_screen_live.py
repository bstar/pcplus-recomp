#!/usr/bin/env python3
"""Check exclusive chooser/PROGRAM screen storage in the actual optional parent."""
import argparse,hashlib,json
from pathlib import Path
from unicorn.x86_const import *
from check_program_actions_live import LiveProgram
from terminal_memory import inspect_terminal_memory
import check_transport
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
class Screen(LiveProgram):
 def interrupt(self,u,n,d):
  if n==0x21 and u.reg_read(UC_X86_REG_AX)>>8==0x3d:
   # External DOS open failure, after the real chooser has saved its screen.
   u.reg_write(UC_X86_REG_AX,2);self.set_carry(True);return
  return super().interrupt(u,n,d)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);a=p.parse_args();binary=a.terminal.resolve()
 mft=json.loads((binary.parent/'manifest.json').read_text());assert sha(binary)==mft['binary_sha256']
 for name,digest in mft['sources'].items():assert sha(ROOT/name)==digest,name
 memory=inspect_terminal_memory(binary,binary.parent/'terminal.map');assert memory['program_browser_screen_overlay']and memory['far_ui_storage_bytes']==16000
 check_transport.BINARY=binary;check_transport.MAP=binary.parent/'terminal.map';refusals=0
 for owner in('terminal_program_pending','terminal_program_active','terminal_browser_screen_owned'):
  m=Screen();m.put(owner,1,1 if owner=='terminal_browser_screen_owned'else 2)
  saved=bytes(m.uc.mem_read(m.symbols['browser_screen'],4000));screen=bytes(m.uc.mem_read(0xb8000,4000))
  assert m.call('terminal_directory_choose')==2,owner
  assert bytes(m.uc.mem_read(m.symbols['browser_screen'],4000))==saved and bytes(m.uc.mem_read(0xb8000,4000))==screen
  assert m.get(owner,1 if owner=='terminal_browser_screen_owned'else 2)==1
  refusals+=1
 m=Screen();m.put('terminal_browser_screen_owned',1,1);saved=bytes(m.uc.mem_read(m.symbols['program_screen'],4000))
 m.record(0,b'OWNED.COM',1)
 assert m.call('terminal_program_start',ax=m.offset('terminal_action_definitions')+2)==2 and not m.get('terminal_program_pending')and not m.children
 assert bytes(m.uc.mem_read(m.symbols['program_screen'],4000))==saved;refusals+=1
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
 report=dict(passed=True,binary_sha256=sha(binary),owner_refusals=refusals,restore_cycles=cycles,reclaimed_bytes=4000,sources=mft['sources'],checker_sha256=sha(Path(__file__)),original_inputs=[],scope=__doc__+' Real chooser open-error acquisition/restoration and actual PROGRAM/child/error restoration. DOS open and child execution are modeled kernel boundaries; real DOS nested launches are separate.')
 (binary.parent/'shared-screen-checks.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS shared screen:',refusals,'owner refusals,',cycles,'restore cycles, 4000 bytes reclaimed')
if __name__=='__main__':main()
