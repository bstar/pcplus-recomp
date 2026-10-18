#!/usr/bin/env python3
"""Exercise actual linked mode tables, state branches, cursor code and traps."""
from pathlib import Path
import hashlib,json,struct
from unicorn import UC_HOOK_INTR
from unicorn.x86_const import UC_X86_REG_AX,UC_X86_REG_DX,UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI
from dos_image import DosImage
ROOT=Path(__file__).resolve().parents[1]
class MissingEffect(Exception):pass
class Modes(DosImage):
 def __init__(self,parameters=(7,),private=0,gate=0):
  super().__init__(ROOT/'build/modes/MODES.EXE',ROOT/'build/modes/modes.map')
  assert len(parameters)<=16
  self.put('ansi_parameter_count',len(parameters));self.put('ansi_private',private);self.put('csi_report_private_prefix',gate)
  if parameters:self.uc.mem_write(self.symbols['ansi_parameters'],struct.pack('<'+'H'*len(parameters),*parameters))
  self.positions=[];self.uc.hook_add(UC_HOOK_INTR,self.interrupt)
 def interrupt(self,uc,number,_):
  if number==3:raise MissingEffect(self.get('modes_dependency_id'),self.get('modes_dependency_argument'))
  assert number==0x10 and uc.reg_read(UC_X86_REG_AX)>>8==2
  self.positions.append(uc.reg_read(UC_X86_REG_DX))
 def run(self,reset=False):
  self.call('csi_reset_modes' if reset else 'csi_set_modes')
  assert self.uc.reg_read(UC_X86_REG_BP)==0xbabe and self.uc.reg_read(UC_X86_REG_SI)==0x1234 and self.uc.reg_read(UC_X86_REG_DI)==0x5678
  return self
 def missing(self,reset=False):
  try:self.run(reset)
  except MissingEffect as error:return error.args
  raise AssertionError('Expected unresolved mode side effect to fail explicitly')
def main():
 cases=[]
 def check(name,fn):fn();cases.append({'case':name,'passed':True});print(name,'passed')
 def states():
  for private in (0,1):
   for reset in (False,True):
    for mode,name,set_value,reset_value in [(4,'terminal_mode_372c',1,0),(7,'cursor_state_value_1d20',1,0),(18,'modes_value_3980',1,0),(19,'modes_value_3982',0,1)]:
     m=Modes([mode],private);m.put(name,0x5555);m.put('csi_wrap_pending',0x1234);m.run(reset)
     want=(0x5555 if mode==4 and private else reset_value if reset else set_value)
     assert m.get(name)==want,(mode,private,reset)
     assert m.get('csi_wrap_pending')==(0 if mode==7 and reset else 0x1234)
 check('direct-mode-state-private-gates-and-wrap-clear',states)
 def origin():
  for private in (0,1):
   m=Modes([6],private);m.put('csi_scroll_top',4);m.put('csi_scroll_bottom',19)
   m.run();assert (m.get('csi_origin_mode'),m.get('csi_origin_row'),m.get('csi_origin_bottom'))==(1,4,19)
   assert m.positions==[0x0400] and m.get('screen_cursor_row')==4
   m.run(True);assert (m.get('csi_origin_mode'),m.get('csi_origin_row'),m.get('csi_origin_bottom'))==(0,0,24)
   assert m.positions==[0x0400,0] and m.get('screen_cursor_row')==0
 check('mode6-real-origin-state-screen-offsets-and-BIOS',origin)
 def bounds():
  for reset in (False,True):
   for parameters,count,gate in [([],0,0),([7],0xffff,0),([7],1,1)]:
    m=Modes(parameters,gate=gate);m.put('ansi_parameter_count',count);m.put('cursor_state_value_1d20',0x5555);m.run(reset)
    assert m.get('cursor_state_value_1d20')==0x5555 and not m.positions
   m=Modes([0,5,8,9,10,11,13,14,15,16,17,20,21,22,26,65535]);m.put('cursor_state_value_1d20',0x5555);m.run(reset)
   assert m.get('cursor_state_value_1d20')==0x5555
  m=Modes([4,7,18,19,0,65535]);m.run()
  assert [m.get(n) for n in ['terminal_mode_372c','cursor_state_value_1d20','modes_value_3980','modes_value_3982']]==[1,1,1,0]
  m.run(True);assert [m.get(n) for n in ['terminal_mode_372c','cursor_state_value_1d20','modes_value_3980','modes_value_3982']]==[0,0,0,1]
 check('parameter-array-iteration-empty-signed-count-gate-and-unsupported-modes',bounds)
 def effects():
  for reset in (False,True):
   m=Modes([1]);assert m.missing(reset)==(0xb4e,0x5b if reset else 0x4f)
   m=Modes([3],1);assert m.missing(reset)==(0x2a6e,0 if reset else 1)
   Modes([3],0).run(reset)
   m=Modes([25]);m.put('modes_cursor_flags',0xa503)
   value=0xa503 if reset else 0xa507
   assert m.missing(reset)==(0x2f78,value) and m.get('modes_cursor_flags')==value
  m=Modes([2],1);assert m.missing(True)==(0x20a4,1)
  assert m.get('csi_previous_terminal_id')==4 and m.get('csi_terminal_id')==1
  Modes([2],0).run(True);Modes([2],1).run()
  for private in (0,1):
   m=Modes([12],private);assert m.missing()[0]==0x2fb8 and m.get('modes_value_1d1a')==0
  m=Modes([12]);assert m.missing(True)[0]==0x2fb8 and m.get('modes_value_1d1a')==1
  m=Modes([12],1);m.put('modes_value_1d1a',0x5555);m.run(True);assert m.get('modes_value_1d1a')==0x5555
 check('explicit-mode-side-effect-boundaries-and-original-argument-ABI',effects)
 result={'passed':True,'binary_sha256':hashlib.sha256((ROOT/'build/modes/MODES.EXE').read_bytes()).hexdigest(),'cases':cases,'scope':'Actual recovered mode handler/table/state instructions plus actual screen cursor; unresolved mode effects trap rather than succeed.'}
 (ROOT/'build/modes/cpu-results.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
