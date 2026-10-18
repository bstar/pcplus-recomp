#!/usr/bin/env python3
"""Exercise continuous stream through actual input/ANSI/control/render/history code."""
from pathlib import Path
import hashlib,json
from unicorn import UC_HOOK_INTR
from check_render import Render
from dos_image import DosImage
ROOT=Path(__file__).resolve().parents[1]
BINARY=ROOT/'build/input_dispatch/INPUT.EXE'
class MissingInputService(Exception):pass
class Input(Render):
 def __init__(self):
  DosImage.__init__(self,BINARY,ROOT/'build/input_dispatch/input_dispatch.map')
  self.positions=[];self.calls=[];self.video=0xb8000
  self.uc.mem_write(self.video,b'\xa5'*4000);self.uc.hook_add(UC_HOOK_INTR,self.interrupt)
  self.call('csi_clear_tabs',(1,))
 def interrupt(self,uc,number,data):
  if number==3:raise MissingInputService(self.get('csi_unimplemented_service'))
  Render.interrupt(self,uc,number,data)
 def feed(self,data):
  assert len(data)<=2048
  self.uc.mem_write(self.symbols['ansi_input_buffer'],data or b'\0')
  self.put('ansi_input_pointer',self.offset('ansi_input_buffer'));self.put('ansi_input_length',len(data))
  self.call('ansi_reset');self.call('terminal_process_stream',limit=1000000)
  assert self.get('ansi_input_position')==len(data) and self.get('ansi_parameter_canary')==0xa55a
 def history(self):
  start=self.get('terminal_history_start');end=self.get('terminal_history_pointer')
  assert end>=start
  return bytes(self.uc.mem_read(self.data_base+start,end-start))

def main():
 cases=[]
 def check(name,fn):fn();cases.append({'case':name,'passed':True});print(name,'passed',flush=True)
 def continuous():
  c=Input();c.feed(b'AB\tC\r\n\x1b[31mD\x08E')
  assert c.cell(0,0)==b'A\x07' and c.cell(0,1)==b'B\x07' and c.cell(0,8)==b'C\x07'
  assert c.cell(1,0)==b'E\x04' and (c.get('screen_cursor_row'),c.get('screen_cursor_column'))==(1,1)
  assert c.history()==b'ABC\rDE'
 check('continuous-print-tab-cr-lf-sgr-backspace-and-real-history',continuous)
 def tables():
  for profile in range(2,12):
   c=Input();c.put('csi_terminal_id',profile);c.feed(b'A\x1b[2;4HZ')
   assert c.cell(1,3)==b'Z\x07' and c.get('screen_cursor_column')==4
  c=Input();c.feed(b'A\x00B\x7fC');assert c.history()==b'ABC' and c.get('screen_cursor_column')==3
 check('actual-startup-escape-and-control-function-pointer-tables',tables)
 def crlf():
  c=Input();c.feed(b'ABC\rZ');assert c.cell(0,0)==b'Z\x07' and c.get('screen_cursor_column')==1
  c=Input();c.put('terminal_cr_adds_lf',1);c.feed(b'A\rB');assert c.cell(1,0)==b'B\x07'
  c=Input();c.put('terminal_newline_mode_9020',1);c.feed(b'AB\nC');assert c.cell(1,0)==b'C\x07'
  c=Input();c.feed(b'AB\nC');assert c.cell(1,2)==b'C\x07'
 check('original-cr-lf-mode-dependent-column-and-row-behavior',crlf)
 def wrapping():
  c=Input();c.feed(b'A'*80+b'B');assert c.cell(0,79)==b'A\x07' and c.cell(1,0)==b'B\x07'
  c=Input();c.feed(b'\x1b[25;80HAB');assert c.cell(23,79)==b'A\x07' and c.cell(24,0)==b'B\x07' and len(c.calls)==1
 check('continuous-stream-wrap-and-real-bottom-scroll',wrapping)
 def control_inside_escape():
  c=Input();c.feed(b'AB\x1b[1\x08;2HZ')
  assert c.cell(0,1)==b'Z\x07' and c.get('screen_cursor_column')==2
 check('embedded-parser-control-reenters-actual-control-dispatcher',control_inside_escape)
 def history():
  c=Input();c.feed(b'AB\rC\r\nD');assert c.history()==b'AB\rC\rD'
  # Force a small ring to exercise actual pointer wrap and full latch.
  c=Input();start=c.get('terminal_history_start');c.put('terminal_history_end',start+4);c.feed(b'ABCDE')
  assert c.get('terminal_history_wrapped')==1 and c.get('terminal_history_pointer')==start+1
  assert bytes(c.uc.mem_read(c.data_base+start,4))==b'EBCD'
 check('real-history-cr-state-and-buffer-wrap',history)
 def unavailable():
  for state,data,want in [(None,b'\x01',0xe62),('terminal_sink_3988_enabled',b'A',0x36fc),('terminal_sink_398a_enabled',b'A',0x8436)]:
   c=Input()
   if state:c.put(state,1)
   try:c.feed(data)
   except MissingInputService as error:assert error.args==(want,),(state,error.args,want)
   else:raise AssertionError('unrecovered input feature silently succeeded')
 check('unrecovered-control-and-enabled-sink-boundaries-fail-fast',unavailable)
 def byte_abi():
  for argument,want in [(0xffb1,0xb1),(0xffff,0xff),(0x01b1,0xb1)]:
   c=Input();c.call('terminal_receive_character',(argument,))
   assert c.cell(0,0)==bytes([want,7]) and c.get('screen_cursor_column')==1
  # These real dispatcher command entries produce the legacy signed token.
  # Feed the dispatcher directly: full parser CAN/SUB control-family semantics
  # are separate unresolved work, not silently treated as cancellation here.
  for command in (0x18,0x1a):
   c=Input();c.put('ansi_command',command);c.call('ansi_dispatch_command')
   assert c.cell(0,0)==b'\xb1\x07'
 check('maintained-byte-abi-and-real-dispatcher-negative-token-producer',byte_abi)

 result={'passed':True,'binary_sha256':hashlib.sha256(BINARY.read_bytes()).hexdigest(),'cases':cases,'scope':'Actual recovered input/escape/parameter/CSI/control/render/video/cursor/scroll/history/guarded-log instructions; memory serial provider and explicit BIOS model. Unsupported control profiles and enabled sink services trap.'}
 (ROOT/'build/input_dispatch/checks.json').write_text(json.dumps(result,indent=2)+'\n');return result
if __name__=='__main__':main()
