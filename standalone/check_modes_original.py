#!/usr/bin/env python3
"""Compare original and linked modes; stop explicitly before unresolved effects."""
import argparse,hashlib,json,struct,sys
from pathlib import Path
from unicorn import UC_HOOK_CODE,UC_HOOK_INTR
from unicorn.x86_const import UC_X86_REG_AX,UC_X86_REG_DX,UC_X86_REG_SS,UC_X86_REG_SP
from check_modes import Modes,MissingEffect,ROOT
sys.path.insert(0,str(ROOT/'reconstruction'))
from check_ansi_freeze import load_image
PROOF=json.loads((ROOT/'reconstruction/modes/provenance.json').read_text())
SCREEN=json.loads((ROOT/'reconstruction/screen/provenance.json').read_text())['state']
STATE={int(at,16):name for at,name in SCREEN.items() if name not in ('screen_line_flags','screen_attributes_base')}
STATE.update({int(at,16):name for at,name in PROOF['state'].items() if name!='ansi_parameters'})
ARGS={0xb4e,0x2a6e,0x20a4,0x2f78}
BOUNDARIES=ARGS|{0x2fb8,0x482a,0x4850,0x2adc,0x12c8}
def original(image,initial,parameters,reset):
 uc=load_image(image)
 for at,name in STATE.items():uc.mem_write(0x1fb70+at,struct.pack('<H',initial[name]))
 uc.mem_write(0x1fb70+0xcb3c,struct.pack('<16H',*(parameters+[0]*(16-len(parameters)))))
 uc.mem_write(0x1fb70+0xf2a0,struct.pack('<H',0xfff0))
 positions=[];effect=[];returned=[]
 def interrupt(machine,number,_):
  assert number==0x10 and machine.reg_read(UC_X86_REG_AX)>>8==2
  positions.append(machine.reg_read(UC_X86_REG_DX))
 def stop(machine,address,size,_):
  at=address-0x10000
  if at==0xfff0:returned.append(True);machine.emu_stop()
  elif at in BOUNDARIES:
   arg=None
   if at in ARGS:
    stack=machine.reg_read(UC_X86_REG_SS)*16+machine.reg_read(UC_X86_REG_SP)
    arg=struct.unpack('<H',machine.mem_read(stack+2,2))[0]
   effect.extend([at,arg]);machine.emu_stop()
 uc.hook_add(UC_HOOK_INTR,interrupt);uc.hook_add(UC_HOOK_CODE,stop)
 uc.emu_start(0x1df7e if reset else 0x1de98,0,count=100000);assert returned or effect
 return {name:struct.unpack('<H',uc.mem_read(0x1fb70+at,2))[0] for at,name in STATE.items()},positions,effect

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--original',type=Path,required=True);args=parser.parse_args()
 image=args.original.read_bytes();digest=hashlib.sha256(image).hexdigest();assert digest==PROOF['original_sha256']
 cases=[]
 def compare(parameters,private,reset,gate=0,count=None):
  c=Modes(parameters,private,gate)
  for name,value in [('cursor_state_value_1d20',0x5555),('modes_cursor_flags',0xa503),('modes_value_1d1a',0x5555),('modes_value_3980',0x5555),('modes_value_3982',0x5555),('terminal_mode_372c',0x5555),('csi_wrap_pending',0x1234),('csi_scroll_top',4),('csi_scroll_bottom',19)]:c.put(name,value)
  if count is not None:c.put('ansi_parameter_count',count)
  initial={name:c.get(name) for name in STATE.values()}
  expected,positions,effect=original(image,initial,list(parameters),reset)
  actual_effect=[]
  try:c.run(reset)
  except MissingEffect as error:
   at,arg=error.args;actual_effect=[at,arg if at in ARGS else None]
  actual={name:c.get(name) for name in STATE.values()}
  assert actual==expected,(parameters,private,reset,{k:(actual[k],expected[k]) for k in actual if actual[k]!=expected[k]})
  assert positions==c.positions and actual_effect==effect,(parameters,private,reset,effect,actual_effect)
  cases.append({'parameters':list(parameters),'private':private,'reset':reset,'gate':gate,'count_override':count,'effect_boundary':effect,'matched':True})
 for reset in (False,True):
  for private in (0,1):
   for mode in list(range(28))+[65535]:compare([mode],private,reset)
   for parameters in [[],[4,7,18,19,0,65535],[7]*16]:compare(parameters,private,reset)
   compare([7],private,reset,gate=1);compare([7],private,reset,count=0xffff)
 result={'passed':True,'case_count':len(cases),'original_sha256':digest,'source_sha256':hashlib.sha256((ROOT/'build/modes/MODES.EXE').read_bytes()).hexdigest(),'cases':cases,'scope':'Actual original/source mode handlers and real screen path compare state, BIOS positions and unresolved effect arguments; stop before external effects rather than claiming them implemented.'}
 (ROOT/'build/modes/original-comparison.json').write_text(json.dumps(result,indent=2)+'\n');print(len(cases),'original/source mode comparisons passed')
if __name__=='__main__':main()
