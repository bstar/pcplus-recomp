#!/usr/bin/env python3
"""Read-only linked pane admission with controlled ASPECT ownership states.

This guard matrix does not establish a genuine renderer lease; actual DOS
parent/child workflows establish that separately.
"""
import argparse,hashlib,itertools,json
from pathlib import Path
from unicorn.x86_const import UC_X86_REG_EFLAGS
import check_transport
from check_reset_live import ROOT,fixture

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',required=True,type=Path);a=p.parse_args()
 binary=a.terminal.resolve();manifest=json.loads((binary.parent/'manifest.json').read_text())
 assert sha(binary)==manifest['binary_sha256']
 for name,digest in manifest['sources'].items():assert sha(ROOT/name)==digest,name
 check_transport.BINARY=binary;check_transport.MAP=binary.parent/'terminal.map'
 m,address=fixture();assert m.call('terminal_native_width',ax=1,limit=3000000)==0
 names=['terminal_program_active','terminal_program_kind','terminal_aspect_active','render_attached','resident_bridge_busy','terminal_script_overlay_visible','_redisplay_active','_command_menu_active','_redisplay_live_ready']
 baseline=bytes(m.uc.mem_read(0xb8000,4000))+bytes(m.uc.mem_read(address,8192))+bytes(m.uc.mem_read(m.symbols['screen_attribute_cells'],4096))+bytes(m.uc.mem_read(m.symbols['erase_attribute_values'],4096))
 cases=accepted=0
 for active,kind in itertools.product((1,2),(0,4,5)):
  for aspect,attached,busy,overlay,viewer,menu,ready in itertools.product((0,1),repeat=7):
   state=[active,kind,aspect,attached,busy,overlay,viewer,menu,ready]
   for name,value in zip(names,state):m.put(name,value)
   m.call('terminal_viewport_admit')
   actual=not(m.uc.reg_read(UC_X86_REG_EFLAGS)&1)
   expected=state==[1,4,1,1,1,0,0,0,0]
   assert actual==expected,(state,actual,expected)
   after=bytes(m.uc.mem_read(0xb8000,4000))+bytes(m.uc.mem_read(address,8192))+bytes(m.uc.mem_read(m.symbols['screen_attribute_cells'],4096))+bytes(m.uc.mem_read(m.symbols['erase_attribute_values'],4096))
   assert after==baseline,state
   assert [m.get(n)for n in names]==state
   cases+=1;accepted+=actual
 report=dict(passed=True,cases=cases,accepted=accepted,binary_sha256=sha(binary),checker_sha256=sha(Path(__file__)),sources=manifest['sources'],original_inputs=[],scope=__doc__)
 (binary.parent/'aspect-viewport-ownership-checks.json').write_text(json.dumps(report,indent=2)+'\n')
 print('PASS ASPECT pane ownership:',cases,'read-only cases,',accepted,'accepted scoped state')
if __name__=='__main__':main()
