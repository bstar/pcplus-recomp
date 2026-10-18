#!/usr/bin/env python3
"""Verify real UI services are linked with coherent live terminal UART state."""
import hashlib,json
from pathlib import Path
from dos_image import DosImage
from check_ui_windows import Windows
ROOT=Path(__file__).resolve().parents[1];BINARY=ROOT/'build/terminal/TERMINAL.EXE'
class TerminalUI(Windows):
 def __init__(self):
  DosImage.__init__(self,BINARY,ROOT/'build/terminal/terminal.map')
  self.video=0xb8000;self.reads=0

def main():
 a=TerminalUI();pattern=bytes(i%256 for i in range(4000));a.uc.mem_write(a.video,pattern)
 message=bytes(a.uc.mem_read(a.symbols['uart_flow_message'],32)).split(b'\0',1)[0]
 assert 1<=len(message)<=14,'UART message exceeds the original saved region'
 logical=['screen_cursor_row','screen_cursor_column','attributes_current','csi_saved_row','csi_saved_column']
 before={name:a.get(name) for name in logical}
 at=a.offset('uart_flow_screen_save')
 a.invoke('pcplus_screen_save',[15,3840,at])
 a.invoke('pcplus_flow_message',[a.offset('uart_flow_message'),0],callee_cleanup=False)
 video=a.memory();expected=b''.join(bytes([value,0x1e]) for value in message)
 assert video[:3840]==pattern[:3840] and video[3842:3842+len(expected)]==expected
 assert video[3870:]==pattern[3870:],'Flow message escaped saved UART region'
 assert {name:a.get(name) for name in logical}==before,'Flow UI changed terminal context'
 a.invoke('pcplus_screen_restore',[15,3840,at]);assert a.memory()==pattern
 assert {name:a.get(name) for name in logical}==before
 result={'passed':True,'binary_sha256':hashlib.sha256(BINARY.read_bytes()).hexdigest(),'scope':'Actual terminal-linked recovered screen snapshots and flow writer, real source-owned bottom-row geometry/message. Logical cursor/attributes/CSI saved state preserved; raw packed snapshot and full video restored.'}
 (ROOT/'build/terminal/ui-checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
