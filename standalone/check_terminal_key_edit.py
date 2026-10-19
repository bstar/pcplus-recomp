#!/usr/bin/env python3
"""Actual shared key core and native ICH/DCH echo, with hardware-only models."""
import hashlib,json,struct
from pathlib import Path
from check_line_edit_live import Live
from check_terminal_key_output import Machine
from check_keyboard_mapping_raw import KEYS
ROOT=Path(__file__).resolve().parents[1]
class Edit(Live):
 def __init__(self):
  super().__init__()
  manifest=json.loads((ROOT/'build/terminal/manifest.json').read_text())
  self.segment=self.base_segment+next(s['relative_segment'] for s in manifest['memory_layout']['code_segments'] if s['name']=='ASPECT_CODE')
 def key(self,key,half=1):return Machine.run(self,key,half)
 def wire(self):return Machine.wire(self)
def main():
 (ROOT/'build/terminal-key-output').mkdir(parents=True,exist_ok=True)
 cases=0
 for profile in (4,6):
  for width in (1,2):
   for slot in (8,9,54,55):
    t=Edit();t.put('csi_terminal_id',profile);col=17 if width==1 else 16;t.position(5,col)
    if width==2:t.uc.mem_write(t.symbols['screen_line_flags']+5,b'\x40')
    parameters=struct.pack('<8H',*range(0x1234,0x123c));t.uc.mem_write(t.symbols['ansi_parameters'],parameters)
    t.uc.mem_write(t.symbols['terminal_keymap']+slot*12,b'K\0'+b'\0'*10)
    assert t.key(KEYS[slot])==0 and t.wire()==b'K'
    start=5*80+col;end=6*80;want=t.original[:]
    insert=slot in (8,54)
    if insert:want[start:end]=[0x0620]*width+t.original[start:end-width]
    else:want[start:end]=t.original[start+width:end]+[0x0720]*width
    assert t.cells()==want,(profile,width,slot)
    assert (t.get('screen_cursor_row'),t.get('screen_cursor_column'))==(5,col)
    assert bytes(t.uc.mem_read(t.symbols['ansi_parameters'],len(parameters)))==parameters
    cases+=1
 mutations=[('screen_columns',0),('screen_attribute_row_bytes',0),('screen_video_row_bytes',0),('screen_video_offset',1),('screen_attribute_offset',1),('screen_viewport_active',1),('screen_viewport_offset',1),('text_video_segment',0),('csi_last_row',25)]
 for slot in (8,9,54,55):
  for field,value in mutations:
   t=Edit();t.position(5,17);t.put('ansi_parameters',32767);t.put(field,value)
   assert t.key(KEYS[slot])==3 and not t.wire() and t.cells()==t.original,(slot,field)
   assert t.get('ansi_parameters')==32767;cases+=1
 for offset in (5*80+17,5*80+19,5*80+79):
  t=Edit();t.position(5,17);t.put('screen_cursor_wrap',1);t.put('ansi_parameters',32767)
  t.uc.mem_write(t.symbols['screen_attribute_cells']+offset,b'\x80')
  assert t.key(KEYS[9])==3 and not t.wire() and t.cells()==t.original
  assert t.get('ansi_parameters')==32767;cases+=1
 report=dict(passed=True,cases=cases,binary_sha256=hashlib.sha256((ROOT/'build/terminal/TERMINAL.EXE').read_bytes()).hexdigest(),checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='Actual shared key core, checked admission, native ICH/DCH and video/memory helpers. Hardware boundaries only are modeled. Both profiles, four standard/enhanced key identities, single/doublewidth edits, unchanged cursor/parser parameters and invalid/repair admission before any wire or video mutation. No physical keyboard/modem claim.',original_inputs=[])
 (ROOT/'build/terminal-key-output/edit-checks.json').write_text(json.dumps(report,indent=2)+'\n');print('Shared key native editing',cases,'cases PASS')
if __name__=='__main__':main()
