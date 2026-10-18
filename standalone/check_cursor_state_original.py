#!/usr/bin/env python3
"""Optional actual-original vs linked-source save/restore state comparison."""
import argparse,hashlib,json,random,struct,sys
from pathlib import Path
from unicorn import UC_HOOK_CODE,UC_HOOK_INTR
from unicorn.x86_const import UC_X86_REG_AX,UC_X86_REG_DX
from check_cursor_state import CursorState,ROOT,PROOF,PAIRS
sys.path.insert(0,str(ROOT/'reconstruction'))
from check_ansi_freeze import load_image
SCREEN=json.loads((ROOT/'reconstruction/screen/provenance.json').read_text())['state']
STATE={int(at,16):name for at,name in PROOF['state'].items()}
STATE.update({int(at,16):name for at,name in SCREEN.items() if name not in ('screen_line_flags','screen_attributes_base')})
def original(image,state,entry,mode):
 uc=load_image(image)
 for at,name in STATE.items():uc.mem_write(0x1fb70+at,struct.pack('<H',state[name]))
 uc.mem_write(0x1fb70+0xf2a0,struct.pack('<HH',0xfff0,mode))
 positions=[];returned=[]
 def interrupt(machine,number,_):
  assert number==0x10 and machine.reg_read(UC_X86_REG_AX)>>8==2
  positions.append(machine.reg_read(UC_X86_REG_DX))
 def stop(machine,address,size,_):
  if address==0x1fff0:returned.append(True);machine.emu_stop()
 uc.hook_add(UC_HOOK_INTR,interrupt);uc.hook_add(UC_HOOK_CODE,stop)
 uc.emu_start(entry,0,count=100000);assert returned
 return {name:struct.unpack('<H',uc.mem_read(0x1fb70+at,2))[0] for at,name in STATE.items()},positions
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--original',type=Path,required=True);args=parser.parse_args()
 image=args.original.read_bytes();digest=hashlib.sha256(image).hexdigest();assert digest==PROOF['original_sha256']
 rng=random.Random(201);cases=[]
 for routine,entry in [('csi_save_cursor',0x1dd74),('csi_restore_cursor',0x1ddbc)]:
  for mode in (0,1,0xffff):
   for iteration in range(8):
    c=CursorState()
    for name in list(PAIRS)+list(PAIRS.values()):c.put(name,rng.randrange(65536))
    for name,bound in [('screen_cursor_row',25),('screen_cursor_column',80),('csi_saved_row',25),('csi_saved_column',80)]:c.put(name,rng.randrange(bound))
    initial={name:c.get(name) for name in STATE.values()}
    expected,positions=original(image,initial,entry,mode)
    c.call_state(routine,mode)
    actual={name:c.get(name) for name in STATE.values()}
    assert actual==expected,(routine,mode,iteration,{k:(actual[k],expected[k]) for k in actual if actual[k]!=expected[k]})
    assert positions==c.positions
    cases.append({'routine':routine,'mode':mode,'iteration':iteration,'matched':True,'BIOS_positions':positions})
 result={'passed':True,'case_count':len(cases),'original_sha256':digest,'source_sha256':hashlib.sha256((ROOT/'build/cursor-state/CSTATE.EXE').read_bytes()).hexdigest(),'cases':cases,'scope':'Save/restore plus actual original/source screen cursor path; state words and BIOS positions compared. No renderer or hardware.'}
 (ROOT/'build/cursor-state/original-comparison.json').write_text(json.dumps(result,indent=2)+'\n');print(len(cases),'original/source cursor-state comparisons passed')
if __name__=='__main__':main()
