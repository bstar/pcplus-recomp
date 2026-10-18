#!/usr/bin/env python3
"""Run actual linked recovered keyboard instructions against a BIOS oracle."""
import hashlib,json
from pathlib import Path
from unicorn import UC_HOOK_INTR
from unicorn.x86_const import UC_X86_REG_AX,UC_X86_REG_EFLAGS,UC_X86_REG_BP,UC_X86_REG_SI
from dos_image import DosImage
ROOT=Path(__file__).resolve().parents[1]
class Keyboard(DosImage):
 def __init__(self,keys=()):
  super().__init__(ROOT/'build/keyboard/KEYBOARD.EXE',ROOT/'build/keyboard/keyboard.map')
  self.keys=list(keys);self.calls=[]
  self.uc.hook_add(UC_HOOK_INTR,self.interrupt)
 def interrupt(self,uc,number,_):
  assert number==0x16,number
  function=uc.reg_read(UC_X86_REG_AX)>>8;self.calls.append(function)
  assert function in (0,1,16,17),function
  if function in (0,16):
   assert self.keys,'unexpected blocking BIOS read'
   uc.reg_write(UC_X86_REG_AX,self.keys.pop(0))
  else:
   flags=uc.reg_read(UC_X86_REG_EFLAGS)
   uc.reg_write(UC_X86_REG_EFLAGS,(flags&~0x40) if self.keys else flags|0x40)
   if self.keys:uc.reg_write(UC_X86_REG_AX,self.keys[0])
def run():
 cases=[]
 def check(name,fn):fn();cases.append({'case':name,'passed':True});print(name,'passed')
 def normalization():
  k=Keyboard()
  # Expectations derive from the recovered signed comparison and explicit cases.
  for raw,want in [(0x1e61,0x61),(0x3920,0x20),(0x0e08,0x0e08),(0x0e7f,0x0e7f),(0x372a,0x372a),(0x4800,0x4800),(0x48e0,0x48e0),(0xe02f,0xe02f),(0x8061,0x61)]:
   assert k.call('keyboard_key_from_bios',[raw])==want,(raw,want)
  for raw,want in [(0x48e0,0x4800),(0x4800,0x4800),(0x1e61,0x61),(0x0e08,0x0e08),(0xe02f,0x2f)]:
   assert k.call('keyboard_key_for_extended',[raw])==want,(raw,want)
 check('callee-cleanup-normalization-through-caller-cleanup-ABI',normalization)
 def bios():
  for mode in (0,16):
   k=Keyboard([0x1e61]);k.put('keyboard_bios_mode',mode,1)
   assert k.call('keyboard_bios_peek')==0x1e61 and k.keys==[0x1e61]
   assert k.call('keyboard_read')==0x61 and not k.keys
   assert k.call('keyboard_bios_peek')==0
   assert k.calls==[mode+1,mode+1,mode,mode+1]
   assert k.uc.reg_read(UC_X86_REG_BP)==0xbabe and k.uc.reg_read(UC_X86_REG_SI)==0x1234
  k=Keyboard([0]);assert k.call('keyboard_bios_peek')==0x100
 check('standard-and-enhanced-BIOS-read-peek-and-empty-sentinel',bios)
 def queue():
  k=Keyboard();k.put('keyboard_queue_count',1);k.put('keyboard_queue_index',3);k.put('keyboard_queue_active',1)
  k.uc.mem_write(k.symbols['keyboard_queue_peek']+6,b'\x00\x48')
  k.uc.mem_write(k.symbols['keyboard_queue_values']+6,b'\x00\x4d')
  assert k.call('keyboard_peek')==0x4800 and k.get('keyboard_queue_count')==1
  assert k.call('keyboard_read')==0x4d00 and k.get('keyboard_queue_count')==0
  assert k.get('keyboard_queue_index')==3 and k.get('keyboard_queue_active')==0 and not k.calls
  assert k.uc.reg_read(UC_X86_REG_EFLAGS)&0x200
 check('queue-distinct-peek-dequeue-bases-and-state',queue)
 def debug():
  k=Keyboard([0x2c00,0x1e61]);k.put('keyboard_debug_gate',0)
  assert k.call('keyboard_poll')==0 and k.get('keyboard_debug_count')==1 and k.keys==[0x1e61]
  assert k.call('keyboard_read')==0x61 and not k.keys
  k=Keyboard([0x2c00]);assert k.call('keyboard_poll')==0x2c00 and k.keys==[0x2c00]
 check('debug-hotkey-consumption-and-gating',debug)
 def extended():
  k=Keyboard([0x48e0]);k.put('keyboard_bios_mode',16,1)
  assert k.call('keyboard_read_extended')==0x4800 and k.calls==[17,16]
 check('enhanced-E0-arrow-end-to-end-normalization',extended)
 out=ROOT/'build/keyboard/cpu-results.json';out.write_text(json.dumps({'passed':True,'binary_sha256':hashlib.sha256((ROOT/'build/keyboard/KEYBOARD.EXE').read_bytes()).hexdigest(),'cases':cases},indent=2)+'\n')
if __name__=='__main__':run()
