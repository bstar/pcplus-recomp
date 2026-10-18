#!/usr/bin/env python3
"""Run recovered save/restore through actual source-built screen instructions."""
from pathlib import Path
import hashlib,json,random,struct
from unicorn import UC_HOOK_INTR
from unicorn.x86_const import UC_X86_REG_AX,UC_X86_REG_DX,UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI
from dos_image import DosImage
ROOT=Path(__file__).resolve().parents[1]
PROOF=json.loads((ROOT/'reconstruction/cursor_state/provenance.json').read_text())
PAIRS=PROOF['pairs']
class CursorState(DosImage):
 def __init__(self):
  super().__init__(ROOT/'build/cursor-state/CSTATE.EXE',ROOT/'build/cursor-state/cursor_state.map')
  self.positions=[];self.uc.hook_add(UC_HOOK_INTR,self.interrupt)
 def interrupt(self,uc,number,_):
  assert number==0x10 and uc.reg_read(UC_X86_REG_AX)>>8==2,number
  self.positions.append(uc.reg_read(UC_X86_REG_DX))
 def snapshot(self):
  return {name:self.get(name) for name in list(PAIRS)+list(PAIRS.values())+['screen_cursor_row','screen_cursor_column','csi_saved_row','csi_saved_column']}
 def call_state(self,name,mode):
  self.call(name,[mode])
  assert self.uc.reg_read(UC_X86_REG_BP)==0xbabe
  assert self.uc.reg_read(UC_X86_REG_SI)==0x1234 and self.uc.reg_read(UC_X86_REG_DI)==0x5678

def main():
 cases=[]
 def check(name,fn):fn();cases.append({'case':name,'passed':True});print(name,'passed')
 def save():
  rng=random.Random(201)
  for mode in (0,1,0xffff):
   c=CursorState()
   for name in PAIRS:c.put(name,rng.randrange(65536))
   c.put('screen_cursor_row',9);c.put('screen_cursor_column',19)
   before=c.snapshot();c.call_state('csi_save_cursor',mode)
   assert c.get('csi_saved_row')==9 and c.get('csi_saved_column')==19
   for live,saved in PAIRS.items():assert c.get(saved)==(before[live] if mode==0 else 0),(mode,live)
   assert not c.positions
 check('save-full-versus-position-only-mode-and-caller-cleanup',save)
 def restore():
  rng=random.Random(201)
  for mode in (0,1,0xffff):
   c=CursorState()
   c.put('csi_saved_row',9);c.put('csi_saved_column',19)
   for name in PAIRS.values():c.put(name,rng.randrange(65536))
   before=c.snapshot();c.call_state('csi_restore_cursor',mode)
   assert (c.get('screen_cursor_row'),c.get('screen_cursor_column'))==(9,19)
   assert c.positions==[9*256+19]
   assert c.get('screen_video_offset')==9*160+19*2 and c.get('screen_attribute_offset')==9*80+19
   for live,saved in PAIRS.items():assert c.get(live)==(before[saved] if mode==0 else before[live]),(mode,live)
 check('restore-full-versus-position-only-through-real-screen-and-BIOS',restore)
 def cycles():
  c=CursorState()
  for row,col in [(0,0),(24,79),(12,40),(3,2),(24,0)]:
   c.put('screen_cursor_row',row);c.put('screen_cursor_column',col)
   # Keep previous/offset state coherent before the actual restore calls.
   c.put('screen_previous_row',row);c.put('screen_visible_column',col)
   c.put('screen_video_offset',row*160+col*2);c.put('screen_attribute_offset',row*80+col)
   for i,name in enumerate(PAIRS):c.put(name,i+1)
   c.call_state('csi_save_cursor',0)
   for name in PAIRS:c.put(name,0)
   c.call_state('csi_restore_cursor',0)
   assert c.positions[-1]==row*256+col
   for i,name in enumerate(PAIRS):assert c.get(name)==i+1
 check('repeated-edge-and-middle-position-full-state-roundtrips',cycles)
 result={'passed':True,'binary_sha256':hashlib.sha256((ROOT/'build/cursor-state/CSTATE.EXE').read_bytes()).hexdigest(),'cases':cases,'scope':'Actual recovered save/restore and linked screen instructions; BIOS position calls recorded, optional unresolved screen services trap.'}
 (ROOT/'build/cursor-state/cpu-results.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
