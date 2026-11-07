#!/usr/bin/env python3
"""Linked parent profile owner, keyboard staging and clean reset; hardware modeled."""
import argparse,json,struct,hashlib,sys
from pathlib import Path
from unicorn.x86_const import *
import check_transport as transport
ROOT=transport.ROOT
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--product',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 product=a.product.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(exist_ok=False)
 transport.BINARY=product/'TERMINAL.EXE';transport.MAP=product/'terminal.map'
 from check_live_setup_profile import Profile
 manifest=json.loads((product/'manifest.json').read_text());assert sha(transport.BINARY)==manifest['binary_sha256']
 for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 class Parent(Profile):
  def far(self,selector,flags=0x202):
   u=self.uc;target=self.symbols['terminal_script_emulate'];segments=manifest['memory_layout']['code_segments']
   segment=self.base_segment+next(s['relative_segment'] for s in segments if self.base+s['relative_segment']*16<=target<self.base+s['relative_segment']*16+s['bytes'])
   sp=self.offset('terminal_stack_top')-4
   keep=[(UC_X86_REG_BX,0x1111),(UC_X86_REG_CX,0x2222),(UC_X86_REG_DX,0x3333),(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678),(UC_X86_REG_ES,0xb800)]
   for r,v in [(UC_X86_REG_CS,segment),(UC_X86_REG_DS,self.ds),(UC_X86_REG_SS,self.ds),(UC_X86_REG_SP,sp),(UC_X86_REG_AX,selector),(UC_X86_REG_EFLAGS,flags)]+keep:u.reg_write(r,v)
   u.mem_write(self.data_base+sp,struct.pack('<HH',self.return_offset,self.code_segment));self.returned=False
   u.emu_start(target,0,count=3000000);assert self.returned,'owner did not return'
   for r,v in keep+[(UC_X86_REG_DS,self.ds),(UC_X86_REG_SS,self.ds),(UC_X86_REG_SP,sp+4),(UC_X86_REG_EFLAGS,flags)]:assert u.reg_read(r)==v,(r,u.reg_read(r),v)
   return u.reg_read(UC_X86_REG_AX)
  def lease(self):
   self.uc.mem_write(0x449,b'\x03\x50\x00');self.uc.mem_write(0x462,b'\0');self.uc.mem_write(0x484,b'\x18')
   self.put('terminal_program_active',1);self.put('terminal_program_kind',4);self.put('terminal_program_pending',0);self.put('connection_state',6);return self
  def view(self):
   return bytes(self.uc.mem_read(0xb8000,4000)),self.keymap(),self.get('csi_terminal_id'),bytes(self.uc.mem_read(self.symbols['terminal_configuration_values'],44))
 cases=[]
 for explicit in (False,True):
  m=Parent();m.explicit() if explicit else None;m.lease();original=m.keymap()
  for target in (6,4,4,6):
   m.put('attributes_current',0x2f);m.put('csi_origin_row',3);m.put('csi_origin_bottom',20)
   m.uc.mem_write(m.symbols['terminal_tab_stops'],b'\xaa'*30)
   before=(m.dll,m.dlm,m.lcr,m.mcr,m.ier,m.pic,m.vector_value(),bytes(m.rx),bytes(m.tx))
   answer=m.far(target);assert answer==0,(explicit,target,answer)
   assert m.get('csi_terminal_id')==target and m.get('connection_state')==6
   assert m.get('screen_cursor_row')==m.get('screen_cursor_column')==0
   assert m.get('attributes_current')==7 and m.cells()[:80*m.get('csi_row_count')]==[0x0720]*(80*m.get('csi_row_count'))
   expected=m.keyboard_file[target*948:(target+1)*948] if explicit else original
   assert m.keymap()==expected and m.get('terminal_setup_profile_ready')==0
   assert before==(m.dll,m.dlm,m.lcr,m.mcr,m.ier,m.pic,m.vector_value(),bytes(m.rx),bytes(m.tx))
   cases.append(dict(case='profile-reset',explicit=explicit,target=target,result=answer))
 # The compact owner uses SI/DI for its target/status and clears DF locally.
 # Verify its promised caller-register/FLAGS restoration across those paths.
 for explicit in (False,True):
  for flags in (0x202,0x602,0x002):
   for target in (4,6):
    m=Parent();m.explicit() if explicit else None;m.lease()
    assert m.far(target,flags=flags)==0 and m.get('csi_terminal_id')==target
    cases.append(dict(case='compact-owner-ABI',explicit=explicit,target=target,flags=flags,result=0))
 # Unsupported selectors and malformed scalar requests are rejected before I/O.
 m=Parent().lease();original=m.view();calls=list(m.file_calls)
 for target in list(range(256))+[256,65535]:
  if target in (4,6):continue
  expected=3 if target<=255 else 7
  assert m.far(target)==expected and m.view()==original and m.file_calls==calls
  cases.append(dict(case='unsupported-selector',target=target,result=expected))
 for field,value,expected,width in [
  ('terminal_program_active',0,3,2),('terminal_program_kind',3,3,2),
  ('terminal_program_pending',1,3,2),('terminal_parser_active',1,3,2),
  ('terminal_aspect_active',1,3,2),('terminal_ansi_wait_active',1,3,2),
  ('connection_state',2,3,2),('reset_ready',0,3,2),
  ('terminal_setup_profile_ready',1,10,2),('terminal_script_window_active',1,10,2),
  ('terminal_script_confirm_active',1,10,2),('terminal_editor_screen_owned',1,10,1),
  ('terminal_browser_screen_owned',1,10,1),('_command_menu_active',1,10,2),
  ('_redisplay_active',1,10,2),('terminal_quit',1,10,2)]:
  m=Parent().lease();m.put(field,value,width);original=m.view();calls=list(m.file_calls)
  assert m.far(6)==expected and m.view()==original and m.file_calls==calls,field
  cases.append(dict(case='owner-guard',field=field,result=expected))
 for failure in ('open','seek','read','close','short','invalid','unbound'):
  m=Parent().explicit().lease();original=m.view()
  if failure in ('open','seek','read','close'):setattr(m,'key_'+failure+'_error',5)
  elif failure=='short':m.key_limit=6*948+947
  elif failure=='invalid':m.keyboard_file=m.keyboard_file[:6*948]+b'X'*948
  else:m.put('terminal_setup_keyboard_bound',0)
  before=(m.dll,m.dlm,m.lcr,m.mcr,m.ier,m.pic,m.vector_value())
  assert m.far(6)==5 and m.view()==original and m.get('terminal_setup_profile_ready')==0,failure
  assert before==(m.dll,m.dlm,m.lcr,m.mcr,m.ier,m.pic,m.vector_value())
  cases.append(dict(case='keyboard-stage-failure',failure=failure,result=5))
  # Retrying after a supported import failure does not require process exit.
  if failure in ('open','seek','read'):
   setattr(m,'key_'+failure+'_error',0);assert m.far(6)==0
   cases.append(dict(case='keyboard-stage-retry',failure=failure,result=0))
  if failure=='close':
   m.key_close_error=0;calls=list(m.file_calls)
   assert m.far(6)==10 and m.view()==original and m.file_calls==calls
   cases.append(dict(case='uncertain-close-quarantine',result=10))
 m=Parent().explicit().lease();m.key_seek_error=5;m.key_close_error=6;original=m.view()
 assert m.far(6)==5 and m.view()==original
 m.key_seek_error=m.key_close_error=0;calls=list(m.file_calls)
 assert m.far(4)==10 and m.view()==original and m.file_calls==calls
 cases.append(dict(case='primary-error-plus-uncertain-close-quarantine',result=10))
 for target in (4,6):
  m=Parent().lease();assert m.far(target)==0
  # Resume the parent's ordinary terminal path after the script lifetime.
  m.put('terminal_program_active',0);m.put('terminal_program_kind',0)
  m.rx.clear();m.data_reads=0;m.tx.clear();m.feed(b'\x1b[0c')
  assert bytes(m.tx)==(b'\x1b[?1;2c' if target==6 else b'\x1b[?62;2c')
  m.tx.clear();m.uc.mem_write(m.symbols['terminal_keymap'],b'\xbb'*948)
  m.feed(b'\x1bc')
  assert m.keymap()!=b'\xbb'*948 and m.get('csi_terminal_id')==target
  cases.append(dict(case='post-return-DA-and-RIS',target=target,result=0))
 sources=dict(manifest['sources'])
 for module in tuple(sys.modules.values()):
  name=getattr(module,'__file__',None)
  if name:
   path=Path(name).resolve()
   if path.is_relative_to(ROOT/'standalone'):sources[str(path.relative_to(ROOT))]=sha(path)
 result=dict(passed=True,cases=cases,parent_sha256=sha(transport.BINARY),sources=sources,original_inputs=[],scope=__doc__+' Actual linked owner/admission/stage/default and explicit KBD/reset/capture code. No product function substituted. No child RPC/opcode, real DOS, receive-service latency or physical acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS parent EMULATE owner',len(cases),'cases')
if __name__=='__main__':main()
