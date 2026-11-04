"""Shared declared BIOS/UART/DOS boundaries for full-height PROGRAM checks.
Actual product code is never replaced; configure check_transport paths before import.
"""
import struct
from unicorn.x86_const import *
from check_row_geometry_live import Geometry
class Program(Geometry):
 def __init__(self):
  self.break_flag=0;self.dos_psp=0xff0;super().__init__();self.mutate_child=True;assert self.far_entry('terminal_trap_open')==0
 def interrupt(self,u,n,d):
  if n==0x21:
   ax=u.reg_read(UC_X86_REG_AX)
   if ax>>8==0x30:u.reg_write(UC_X86_REG_AX,6);return
   if ax>>8==0x62:u.reg_write(UC_X86_REG_BX,self.dos_psp);return
   if ax>>8==0x50:self.dos_psp=u.reg_read(UC_X86_REG_BX);return
   if ax==0x3300:u.reg_write(UC_X86_REG_DX,self.break_flag);return
   if ax==0x3301:self.break_flag=u.reg_read(UC_X86_REG_DX)&255;return
  request=u.reg_read(UC_X86_REG_AX)
  cursor_fault=n==0x10 and request>>8==1 and u.reg_read(UC_X86_REG_CX)==0x2000 and getattr(self,'cursor_bp_fault',False)
  result=super().interrupt(u,n,d)
  if cursor_fault:self.cursor_bp_events+=1;u.reg_write(UC_X86_REG_BP,0xdead)
  if n==0x21 and request==0x4b00 and self.mutate_child and not self.exec_error:
   assert list(self.rx)==[ord('R')];self.rx.clear();self.pending_return_byte=True
   if getattr(self,'child_direction_flag',False):u.reg_write(UC_X86_REG_EFLAGS,u.reg_read(UC_X86_REG_EFLAGS)|0x400)
  return result
 def tick_hook(self,u,address,size,d):
  if address==self.symbols.get('process_child_quiet_site') and getattr(self,'pending_return_byte',False):
   assert not u.reg_read(UC_X86_REG_EFLAGS)&0x200
   assert u.reg_read(UC_X86_REG_DS)==u.reg_read(UC_X86_REG_SS)==self.ds
   self.pending_return_byte=False;self.rx.append(ord('R'))
  return super().tick_hook(u,address,size,d)
 def far_entry(self,name,flags=0x202):
  u=self.uc;seg,_=self.entries[name];sp=self.offset('terminal_stack_top')-4
  u.mem_write(self.data_base+sp,struct.pack('<HH',self.return_offset,self.code_segment))
  for r,v in [(UC_X86_REG_CS,self.base_segment+seg),(UC_X86_REG_DS,self.ds),(UC_X86_REG_SS,self.ds),(UC_X86_REG_SP,sp),(UC_X86_REG_EFLAGS,flags),(UC_X86_REG_BP,0xbabe)]:u.reg_write(r,v)
  self.returned=False;u.emu_start(self.symbols[name],0,count=3000000)
  assert self.returned and u.reg_read(UC_X86_REG_SP)==sp+4 and u.reg_read(UC_X86_REG_BP)==0xbabe
  assert u.reg_read(UC_X86_REG_DS)==u.reg_read(UC_X86_REG_SS)==self.ds
  return u.reg_read(UC_X86_REG_AX)
 def setup(self,rows,hidden=0):
  assert self.set_rows(rows)==0
  if hidden:
   # Use the public saved-display transaction to establish hidden geometry.
   from check_display_transaction_live import Transaction
   Transaction.saved(self,1,2,rows,0);assert Transaction.invoke(self,entry='_terminal_display_apply_saved')==0
  for i in range(4000):self.uc.mem_write(0xb8000+i*2,struct.pack('<H',0x0700+65+i%26))
  self.expected=bytes(self.uc.mem_read(0xb8000,rows*160));self.parent_logical=self.full()['words']
  self.parent_shape=self.shape;self.parent_cursor=self.cursor
  self.prompt_key_sent=False
 def verify(self,rows):
  assert not self.get('terminal_quit') and not self.get('_program_display_ready')
  assert self.mode==3 and self.vrows==rows and self.columns==80 and self.page==0
  assert bytes(self.uc.mem_read(0xb8000,rows*160))==self.expected
  assert self.cursor==self.parent_cursor and self.shape==self.parent_shape
  assert self.full()['words']==self.parent_logical
  assert self.vector_value()==self.parent_vector and (self.lcr,self.mcr,self.ier,self.dll,self.dlm)==(3,0xb,1,3,0)
  assert not self.pic&self.irq_mask and not self.get('terminal_program_active') and not self.get('terminal_program_pending')
  assert {n:self.get(n,1 if n.startswith('uart_saved_') else 2) for n in self.baseline}==self.baseline
