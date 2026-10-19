#!/usr/bin/env python3
"""Actual far keyboard/native field navigation; only hardware is modeled."""
import hashlib,itertools,json,struct
from pathlib import Path
from unicorn.x86_const import *
from check_line_edit_live import Live
from check_terminal_key_output import Machine
from check_keyboard_mapping_raw import KEYS
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/terminal-key-output'
class Reverse(Live):
 def __init__(self):
  self.bells=0;self.clobber_bell=False;super().__init__()
  manifest=json.loads((ROOT/'build/terminal/manifest.json').read_text())
  self.segment=self.base_segment+next(s['relative_segment'] for s in manifest['memory_layout']['code_segments'] if s['name']=='ASPECT_CODE')
  self.uc.mem_write(self.symbols['terminal_keymap']+7*12,b'R\0'+bytes(10))
  self.tabs([0,8,16,24,32,40,48,56,64,72])
 def interrupt(self,u,n,_):
  if n==0x10 and u.reg_read(UC_X86_REG_AX)==0x0e07:
   self.bells+=1
   if self.clobber_bell:
    for r in (UC_X86_REG_AX,UC_X86_REG_BX,UC_X86_REG_CX,UC_X86_REG_DX,UC_X86_REG_SI,UC_X86_REG_DI,UC_X86_REG_BP,UC_X86_REG_DS,UC_X86_REG_ES):u.reg_write(r,0x7000)
   return
  return super().interrupt(u,n,_)
 def tabs(self,values):
  self.uc.mem_write(self.symbols['terminal_tab_stops'],bytes(values)+b'\xfe'*(30-len(values)))
 def key(self,half=1):return Machine.run(self,KEYS[7],half)
 def wire(self):return Machine.wire(self)
 def snapshot(self):
  return (self.cells(),bytes(self.uc.mem_read(self.symbols['screen_attribute_cells'],2000)),bytes(self.uc.mem_read(self.symbols['ansi_parameters'],16)))

def field_reference(height,row,col,flags,width,blocked=False,first=0,last=None,scroll=True,suppressed=False):
 last=height-1 if last is None else last;n=height*80;notices=0
 def adjust(p,step):
  nonlocal notices
  if not flags[p]&0x81:return p
  for j in range(1,n+1):
   q=(p+step*j)%n
   if not flags[q]&0x81:return q
  notices+=1;return 0
 if col:
  if width==2 and col==1:return None
  p=row*80+col-width
  p=adjust(p,-1)
 elif row==first and blocked:p=row*80
 else:
  if row==first:p=last*80+79
  elif row:p=row*80-1
  else:return None
  p=adjust(p,-1)
 if p==0 and blocked:return (0,0,notices)
 p=adjust(p,-1)
 while p and not flags[p]&0x81:p-=1
 if not p:
  q=adjust(0,1);return (*divmod(q,80),notices)
 r,c=divmod(p,80)
 if c<79:
  if width==1:c+=1
  elif c<78:c+=2
 else:
  if suppressed or (r==last and scroll):return None
  c=0
  r=0 if r==last else min(r+1,height-1)
 p=adjust(r*80+c,1)
 return (*divmod(p,80),notices)

def main():
 OUT.mkdir(exist_ok=True);cases=0
 parameters=struct.pack('<8H',*range(0x1234,0x123c))
 def stage(t,row,col,flags=None,width=1,height=25):
  t.put('csi_last_row',height-1);t.put('screen_last_row',height-1);t.put('erase_cell_count',height*80)
  if width==2:t.uc.mem_write(t.symbols['screen_line_flags'],b'\x40'*25)
  t.position(row,col)
  if flags is not None:t.uc.mem_write(t.symbols['screen_attribute_cells'],bytes(flags))
  t.uc.mem_write(t.symbols['ansi_parameters'],parameters)
 for stops,col,wrap,tab_wrap,skip,blocked in itertools.product([[],[0],[3,12,30],[0,8,16,24,32,40,48,56,64,72]],(0,1,8,25,79),(0,1),(0,1),(0,1),(0,1)):
  t=Reverse();stage(t,0,col);t.tabs(stops)
  for field,value in [('screen_cursor_wrap',wrap),('terminal_tab_wrap',tab_wrap),('scroll_skip_attribute_scan',skip),('screen_reverse_wrap_blocked',blocked)]:t.put(field,value)
  unsafe=bool(stops) and col==0 and bool(tab_wrap or skip) and (not wrap or blocked)
  before=t.snapshot();value=t.key()
  if unsafe:
   assert value==3 and t.wire()==b'' and t.snapshot()==before
   assert (t.get('screen_cursor_row'),t.get('screen_cursor_column'))==(0,col)
  else:
   previous=next((v for v in reversed(stops) if v<col),0)
   expected=(0,col if not stops and (tab_wrap or skip) else previous)
   if stops and col==0 and (tab_wrap or skip):expected=(24,next((v for v in reversed(stops) if v<79),0))
   assert value==0 and t.wire()==b'R'
   assert (t.get('screen_cursor_row'),t.get('screen_cursor_column'))==expected,(stops,col,wrap,tab_wrap,skip,blocked,expected)
  assert bytes(t.uc.mem_read(t.symbols['ansi_parameters'],16))==parameters
  cases+=1
 for height,width,pattern,col,blocked in itertools.product((1,5,25),(1,2),range(4),(0,1,2,17,78,79),(0,1)):
  n=height*80;row=min(2,height-1)
  flags=bytes(0 if pattern==0 else 0x81 if pattern==1 else (0x80 if i%13==0 else 0) if pattern==2 else (1 if i%5 else 2) for i in range(n))
  t=Reverse();stage(t,row,col,flags,width,height);t.put('screen_cursor_wrap',1);t.put('screen_attribute_checks',1);t.put('screen_reverse_wrap_blocked',blocked)
  # Protected navigation never reads tab stops; corrupt stops must not mask it.
  t.uc.mem_write(t.symbols['terminal_tab_stops'],b'\xff'*30)
  t.clobber_bell=True;before=t.snapshot();expected=field_reference(height,row,col,flags,width,blocked)
  value=t.key()
  if expected is None:
   assert value==3 and t.wire()==b'' and t.snapshot()==before,(height,width,pattern,col,blocked)
   assert (t.get('screen_cursor_row'),t.get('screen_cursor_column'))==(row,col)
  else:
   assert value==0 and t.wire()==b'R'
   assert (t.get('screen_cursor_row'),t.get('screen_cursor_column'),t.bells)==expected,(height,width,pattern,col,blocked,expected,t.get('screen_cursor_row'),t.get('screen_cursor_column'),t.bells)
   assert t.snapshot()==before,'Cursor-only navigation changed video, metadata or parser parameters'
  cases+=1
 for values in ([0]*30,[16,8]+[254]*28,[8,8]+[254]*28,[80]+[254]*29):
  t=Reverse();stage(t,5,25);t.uc.mem_write(t.symbols['terminal_tab_stops'],bytes(values));before=t.snapshot()
  assert t.key()==3 and not t.wire() and t.snapshot()==before;cases+=1
  assert (t.get('screen_cursor_row'),t.get('screen_cursor_column'))==(5,25)
 for field,value in [('screen_columns',0),('screen_attribute_row_bytes',0),('screen_video_row_bytes',0),('text_video_segment',0),('screen_viewport_enabled',1),('screen_viewport_active',1),('screen_viewport_offset',1),('erase_cell_count',1999),('screen_attributes_base',0xff00),('screen_first_row',25),('screen_last_row',25),('screen_attribute_offset',1),('screen_video_offset',1)]:
  t=Reverse();stage(t,5,25);t.put(field,value);before=t.snapshot()
  assert t.key()==3 and not t.wire() and t.snapshot()==before,(field,value);cases+=1
  assert (t.get('screen_cursor_row'),t.get('screen_cursor_column'))==(5,25)
 for suppressed in (0,1):
  t=Reverse();stage(t,11,10);t.put('screen_first_row',5);t.put('screen_last_row',10);t.put('screen_cursor_wrap',1);t.put('screen_attribute_checks',1);t.put('scroll_suppress_next_linefeed',suppressed)
  t.uc.mem_write(t.symbols['screen_attribute_cells']+10*80+79,b'\x80');before=t.snapshot()
  assert t.key()==3 and not t.wire() and t.snapshot()==before;cases+=1
  assert (t.get('screen_cursor_row'),t.get('screen_cursor_column'))==(11,10)
 for last in (24,2):
  t=Reverse();stage(t,3,10);t.put('screen_cursor_wrap',1);t.put('screen_attribute_checks',1);t.put('screen_last_row',last);t.put('scroll_enabled',0 if last==2 else 1)
  t.uc.mem_write(t.symbols['screen_attribute_cells']+2*80+79,b'\x80');before=t.snapshot()
  assert t.key()==0 and t.wire()==b'R' and t.snapshot()==before
  assert (t.get('screen_cursor_row'),t.get('screen_cursor_column'))==((0,0) if last==2 else (3,0))
  cases+=1
 # Full duplex must continue sending profile bytes without a local-echo plane.
 t=Reverse();t.put('screen_columns',0);assert t.key(0)==0 and t.wire()==b'R';cases+=1
 report=dict(passed=True,cases=cases,binary_sha256=hashlib.sha256((ROOT/'build/terminal/TERMINAL.EXE').read_bytes()).hexdigest(),checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),original_inputs=[],scope='Actual shared key core, checked far admission, recovered reverse Tab, boundary/coordinate/division/protected-home and real resident cursor helpers. Hardware-only BIOS/CRT models include adversarial notice-register clobbering. Table/mode matrix, protected/circular fields,1..25-row planes, doublewidth and pre-wire malformed/unsafe-state rejection; video/metadata/parser parameters unchanged. No physical BIOS/modem or full application/viewport claim.')
 (OUT/'reverse-tab-checks.json').write_text(json.dumps(report,indent=2)+'\n');print('Live reverse Tab',cases,'cases PASS')
if __name__=='__main__':main()
