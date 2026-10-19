#!/usr/bin/env python3
"""Actual linked parent BREAK bracket/native notice/cursor; BIOS/CRT modeled."""
import json,struct
from pathlib import Path
from unicorn import UC_HOOK_INSN
from unicorn.x86_const import *
import check_status_live as status

class UI(status.Status):
 def __init__(self,bios=0):
  self.outputs=[];self.bios_cursor=0x0609;self.bios_ops=[]
  super().__init__();self.put('screen_use_bios_cursor',bios)
  self.uc.mem_write(0x450,struct.pack('<H',self.bios_cursor))
  self.uc.mem_write(0x463,struct.pack('<H',0x3d4))
  self.uc.hook_add(UC_HOOK_INSN,self.output,None,1,0,UC_X86_INS_OUT)
 def output(self,u,p,size,value,d):
  assert p in (0x3d4,0x3d5) and size==1
  self.outputs.append((p,value))
 def interrupt(self,u,n,d):
  assert n==0x10
  op=u.reg_read(UC_X86_REG_AX)>>8;assert op in (2,3)
  assert not u.reg_read(UC_X86_REG_BX)&0xff00
  self.bios_ops.append(op)
  if op==3:u.reg_write(UC_X86_REG_DX,self.bios_cursor)
  else:self.bios_cursor=u.reg_read(UC_X86_REG_DX)
 def bracket(self,phase,name="terminal_break_ui"):
  u=self.uc;target=self.symbols[name]
  memory=json.loads((status.BINARY.parent/'manifest.json').read_text())['memory_layout']
  segment=self.base_segment+next(s['relative_segment'] for s in memory['code_segments'] if self.base+s['relative_segment']*16<=target<self.base+s['relative_segment']*16+s['bytes'])
  sp=self.offset('terminal_stack_top')-4
  for reg,value in [(UC_X86_REG_CS,segment),(UC_X86_REG_DS,self.ds),(UC_X86_REG_SS,self.ds),(UC_X86_REG_SP,sp),(UC_X86_REG_BX,phase),(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678),(UC_X86_REG_EFLAGS,0x202)]:u.reg_write(reg,value)
  u.mem_write(self.data_base+sp,struct.pack('<HH',self.return_offset,self.base_segment))
  self.returned=False;u.emu_start(target,0,count=250000);assert self.returned
  assert u.reg_read(UC_X86_REG_SP)==sp+4 and u.reg_read(UC_X86_REG_BP)==0xbabe
  assert u.reg_read(UC_X86_REG_SI)==0x1234 and u.reg_read(UC_X86_REG_DI)==0x5678
  assert u.reg_read(UC_X86_REG_DS)==self.ds==u.reg_read(UC_X86_REG_SS)
  assert u.reg_read(UC_X86_REG_EFLAGS)&0x600==0x200
  return u.reg_read(UC_X86_REG_AX)

def main():
 cases=[]
 for bios in (0,1):
  for hidden in (0,1):
   m=UI(bios);m.put('ui_flow_suppressed',hidden)
   assert m.bracket(0)==0 and m.get('script_break_ui_active')==1
   assert m.get('script_break_ui_cursor')==0x0609
   before=bytes(m.uc.mem_read(0xb8000,4004))
   if hidden:assert before==b'\xcc'*4004
   else:
    assert before[:3840]==b'\xcc'*3840 and before[3870:]==b'\xcc'*(4004-3870)
    assert before[3840:3870:2]==b' *** BREAK *** '
    assert before[3841:3870:2]==bytes([0x1e])*15
   assert m.bracket(0)==10 and bytes(m.uc.mem_read(0xb8000,4004))==before
   m.bios_cursor=0x0102;m.uc.mem_write(0x450,b'\x02\x01')
   assert m.bracket(1)==0 and not m.get('script_break_ui_active')
   if bios:assert m.bios_cursor==0x0609 and m.bios_ops==[3,2] and not m.outputs
   else:
    assert bytes(m.uc.mem_read(0x450,2))==b'\x09\x06'
    assert m.outputs==[(0x3d4,14),(0x3d5,1),(0x3d4,15),(0x3d5,0xe9)]
   assert bytes(m.uc.mem_read(0xb8000,4004))==b"\xcc"*4004
   count=(len(m.outputs),len(m.bios_ops));assert m.bracket(1)==0
   assert (len(m.outputs),len(m.bios_ops))==count
   assert not m.inputs
   cases.append(dict(name=f'native-notice-bios{bios}-hidden{hidden}',passed=True))
 m=UI();assert m.bracket(0)==0
 assert m.bracket(0,'terminal_render_revoke')==0
 assert not m.get('script_break_ui_active')
 assert bytes(m.uc.mem_read(0xb8000,4004))==b'\xcc'*4004 and not m.inputs
 cases.append(dict(name='abrupt-child-retirement-restores-underlay-without-callback-or-UART',passed=True))
 for name,value in [('ui_flow_region_cells',79),('ui_flow_video_base',0),('ui_flow_coordinate_base',0),('screen_columns',132)]:
  m=UI();m.put(name,value);assert m.bracket(0)==3
  assert not m.get('script_break_ui_active') and bytes(m.uc.mem_read(0xb8000,4004))==b'\xcc'*4004
  assert not m.outputs and not m.bios_ops and not m.inputs
  cases.append(dict(name='reject-'+name,passed=True))
 m=UI();assert m.bracket(2)==7 and not m.outputs and not m.bios_ops
 cases.append(dict(name='reject-phase',passed=True))
 sha=status.hashlib.sha256
 report=dict(passed=True,cases=cases,binary_sha256=sha(status.BINARY.read_bytes()).hexdigest(),checker_sha256=sha(Path(__file__).read_bytes()).hexdigest(),scope='Actual linked parent native31BB notice and798E/6E78 cursor services with maintained single ownership bracket. BIOS/CRT boundary inputs modeled; no UART access allowed. ASIO RPC admission and actual DOS scheduling separately required.')
 (status.BINARY.parent/'aspect-break-ui-checks.json').write_text(json.dumps(report,indent=2)+'\n')
 print('BREAK UI',len(cases),'cases PASS')
if __name__=='__main__':main()
