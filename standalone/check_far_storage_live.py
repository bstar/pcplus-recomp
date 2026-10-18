#!/usr/bin/env python3
"""Linked far metadata/history, RIS and retained EXEC floor; hardware-only models."""
import argparse,hashlib,json,struct,re
from pathlib import Path
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--binary',type=Path,default=ROOT/'build/terminal/TERMINAL.EXE');p.add_argument('--map',type=Path);a=p.parse_args();a.map=a.map or a.binary.parent/'terminal.map'
import check_transport
check_transport.BINARY=a.binary;check_transport.MAP=a.map
from check_program_actions_live import LiveProgram
from check_terminal_reset_live import Live as ResetLive
class SafeStack:
 def call(self,name,arguments=(),*,ax=0,cleanup=0,irq=False,limit=200000):
  u=self.uc
  for register,value in [(UC_X86_REG_CS,self.base_segment),(UC_X86_REG_DS,self.ds),(UC_X86_REG_SS,self.ds),(UC_X86_REG_ES,0xb800),(UC_X86_REG_EFLAGS,0x202),(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678),(UC_X86_REG_AX,ax)]:u.reg_write(register,value)
  words=([self.return_offset,self.base_segment,0x202] if irq else [self.return_offset])+list(arguments)
  sp=self.offset('terminal_stack_top')-len(words)*2;u.mem_write(self.data_base+sp,struct.pack('<'+'H'*len(words),*words));u.reg_write(UC_X86_REG_SP,sp)
  self.returned=False;u.emu_start(self.symbols[name],0,count=limit);assert self.returned,(name,'instruction bound')
  assert u.reg_read(UC_X86_REG_SP)==sp+(6 if irq else 2)+cleanup,(name,'stack')
  return u.reg_read(UC_X86_REG_AX)
class FarProgram(SafeStack,LiveProgram):
 def interrupt(self,u,n,data):
  if n==0x21 and u.reg_read(UC_X86_REG_AX)>>8==0x4a:
   end=self.get('process_psp')*16+u.reg_read(UC_X86_REG_BX)*16
   assert end>=self.symbols['terminal_far_storage_end'],'EXEC freed owned far storage'
   assert end>=self.symbols['terminal_snapshot_image_end'],'EXEC freed frozen screen storage'
  return super().interrupt(u,n,data)
class FarReset(SafeStack,ResetLive):pass

def read(m,name,n):return bytes(m.uc.mem_read(m.symbols[name],n))
def put(m,name,data):m.uc.mem_write(m.symbols[name],bytes(data))
def main():
 cases=[]
 def check(name,fn):fn();cases.append({'case':name,'passed':True});print(name,'passed',flush=True)
 def pointers():
  m=FarReset();shadow=m.get('erase_shadow_segment')*16+m.get('erase_shadow_offset');history=m.get('terminal_history_pointer',4)
  assert shadow==m.symbols['erase_shadow_cells'] and m.get('erase_shadow_segment')!=m.ds
  assert (history>>16)*16+(history&65535)==m.symbols['terminal_history_buffer']
  assert m.get('terminal_history_start')==(history&65535) and m.get('terminal_history_end')-m.get('terminal_history_start')==63000
  assert m.symbols['terminal_history_buffer']>=shadow+8192 and m.symbols['terminal_far_storage_end']-m.symbols['terminal_history_buffer']==63000
  assert shadow>=m.data_base+m.offset('terminal_stack_top')
  snapshot_offset=int(re.search(r'^[0-9a-f]{4}:([0-9a-f]{4})[*+ ]+\s+terminal_snapshot_image\s*$',a.map.read_text(),re.M|re.I)[1],16)
  assert m.get('terminal_snapshot_image_segment')*16+snapshot_offset==m.symbols['terminal_snapshot_image']
  assert m.symbols['terminal_snapshot_image_end']-m.symbols['terminal_snapshot_image']==2000
 check('actual-linker-far-relocations-and-full-storage-extents-outside-DGROUP',pointers)
 def native_far():
  m=FarReset();put(m,'erase_shadow_cells',b'\xa5'*8192);put(m,'terminal_history_buffer',b'\x5a'*63000);seg=m.get('erase_shadow_segment');off=m.get('erase_shadow_offset')
  m.call('erase_far_fill',[8,0x3412,off,seg],cleanup=8);assert read(m,'erase_shadow_cells',16)==b'\x34\x12'*8
  m.call('erase_far_move',[8,off,seg,off+4,seg],cleanup=10);assert read(m,'erase_shadow_cells',20)==b'\x34\x12'*10
  assert read(m,'terminal_history_buffer',63000)==b'\x5a'*63000
 check('actual-native-far-fill-overlapping-move-segment-differs-fromDS',native_far)
 def history():
  m=FarReset();put(m,'erase_shadow_cells',b'\xa5'*8192);put(m,'terminal_history_buffer',b'\x5a'*63000)
  for byte,count in [(65,63000),(66,17)]:
   for _ in range(count):m.call('terminal_history_character',[byte],cleanup=2)
  assert read(m,'terminal_history_buffer',63000)==b'B'*17+b'A'*(63000-17)
  assert m.get('terminal_history_pointer')==m.get('terminal_history_start')+17 and m.get('terminal_history_wrapped')==1
  assert read(m,'erase_shadow_cells',8192)==b'\xa5'*8192
 check('actual-history-LES-ring-full63000-and-wrap-with-shadow-canary',history)
 def reset():
  m=FarReset();m.call('csi_clear_tabs',[1]);m.call('terminal_clear_home');assert m.call('terminal_reset_capture')==0
  put(m,'erase_shadow_cells',b'\xa5'*8192);put(m,'terminal_history_buffer',b'\x5a'*63000);m.feed(b'\x1bc')
  assert read(m,'erase_shadow_cells',8192)==bytes(8192) and read(m,'terminal_history_buffer',63000)==b'\x5a'*63000
 check('real-RIS-far-shadow-clear-preserves-full-history',reset)
 def retain():
  m=FarProgram([0x1c0d]);shadow=bytes((i*13)%256 for i in range(8192));history=bytes((i*17)%256 for i in range(63000));put(m,'erase_shadow_cells',shadow);put(m,'terminal_history_buffer',history)
  frozen=bytes((i*19)%256 for i in range(2000));put(m,'terminal_snapshot_image',frozen)
  expected=(max(m.symbols['terminal_stack_top'],m.symbols['terminal_far_storage_end'],m.symbols['terminal_snapshot_image_end'])+15)//16-m.get('process_psp')
  assert m.get('process_keep_paragraphs')==m.get('process_minimum_paragraphs')==expected
  assert m.queue(b'OWNED.COM')==0;m.safe();assert len(m.children)==1 and 0x4a in m.calls
  assert read(m,'erase_shadow_cells',8192)==shadow and read(m,'terminal_history_buffer',63000)==history
  assert read(m,'terminal_snapshot_image',2000)==frozen
  m.restored()
 check('real-PROGRAM-resize-EXEC-return-max-static-floor-and-full-far-canaries',retain)
 result={'passed':True,'binary_sha256':hashlib.sha256(a.binary.read_bytes()).hexdigest(),'cases':cases,'scope':'Actual linked far relocations, native far movers/history, maintained RIS and PROGRAM retained-memory initializer/EXEC path. Only BIOS/UART/DOS-kernel boundaries modeled; test stack uses actual linked STACK end. No product service replacement.'}
 out=ROOT/'build/far-storage';out.mkdir(parents=True,exist_ok=True);(out/'linked-checks.json').write_text(json.dumps(result,indent=2)+'\n');print('Passed',len(cases),'far-storage groups')
if __name__=='__main__':main()
