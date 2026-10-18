#!/usr/bin/env python3
"""Exercise linked escape instructions; external callbacks are explicit fixtures."""
import hashlib,json,struct
from pathlib import Path
from unicorn.x86_const import UC_X86_REG_BP,UC_X86_REG_SI
from dos_image import DosImage
ROOT=Path(__file__).resolve().parents[1]
class Escape(DosImage):
 def __init__(self,data,tokens=()):
  super().__init__(ROOT/'build/escape/ESCAPE.EXE',ROOT/'build/escape/escape.map')
  assert len(data)<=2048 and len(tokens)<=64
  self.uc.mem_write(self.symbols['escape_input_buffer'],data or b'\0')
  self.put('escape_input_length',len(data))
  if tokens:self.uc.mem_write(self.symbols['escape_tokens'],struct.pack('<'+'H'*len(tokens),*[ord(v) for v in tokens]))
 def run(self):
  self.call('ansi_escape_entry')
  assert self.uc.reg_read(UC_X86_REG_BP)==0xbabe and self.uc.reg_read(UC_X86_REG_SI)==0x1234
  return self

def main():
 cases=[]
 def check(name,fn):fn();cases.append({'case':name,'passed':True});print(name,'passed')
 def routes():
  for sequence,target,arg in [(b'#',0xe0f8,None),(b'7',0xdd74,0),(b'8',0xddbc,0),(b'D',0xda46,None),(b'E',0x12c8,None),(b'H',0xdac6,None),(b'M',0xda84,None),(b'P',0xec94,None),(b'Z',0xdd58,None),(b'c',0x20a4,1),(b'\x84',0xda46,None),(b'\x85',0x12c8,None),(b'\x88',0xdac6,None),(b'\x8d',0xda84,None),(b'\x90',0xec94,None)]:
   e=Escape(sequence).run();assert e.get('escape_last_service')==target and e.get('escape_service_calls')==1,sequence
   if arg is not None:assert e.get('escape_service_argument')==arg,sequence
 check('single-character-and-eight-bit-service-routing',routes)
 def ignore():
  for sequence in [b'Q',b'>',b'F',b'\0\x1b\x7fQ',b'',b' F',b' G']:
   e=Escape(sequence).run();assert e.get('escape_service_calls')==0 and e.get('escape_unread_calls')==0,sequence
  e=Escape(b' Q').run();assert e.get('escape_unread_calls')==1 and e.get('escape_input_position')==1
 check('ignored-bytes-unknown-command-and-space-putback',ignore)
 def charsets():
  for selector,group in [(b'(',0),(b')',1)]:
   for choice,a,g in [(b'A',1,0),(b'0',0,1),(b'2',0,1),(b'B',0,0),(b'Q',0,0)]:
    e=Escape(selector+b'\0'+choice).run()
    assert e.get(f'ansi_charset_g{group}_flag_a')==a and e.get(f'ansi_charset_g{group}_flag_graphics')==g
    assert e.get(f'ansi_charset_g{1-group}_flag_a')==0x5555 and e.get(f'ansi_charset_g{1-group}_flag_graphics')==0x5555
 check('G0-G1-charset-flags-and-zero-byte-skip',charsets)
 def state_machine():
  for prefix in (b'[',b'\x9b',b'*x',b'+x'):
   e=Escape(prefix,['S','D','S','L','A']).run()
   assert e.get('escape_parameter_calls')==2 and e.get('escape_transition_calls')==2 and e.get('escape_dispatch_calls')==1,prefix
   assert e.get('escape_token_position')==5
   for state in ('ansi_parameter_count','ansi_parameters','ansi_private','ansi_secondary'):assert e.get(state)==0,state
  e=Escape(b'[',['D','A']).run();assert e.get('escape_parameter_calls')==2 and e.get('escape_dispatch_calls')==0
 check('CSI-token-loop-reset-and-G2-G3-legacy-entry',state_machine)
 result={'passed':True,'binary_sha256':hashlib.sha256((ROOT/'build/escape/ESCAPE.EXE').read_bytes()).hexdigest(),'scope':'Linked recovered escape routine with recording callbacks and controlled parser tokens; no rendered terminal behavior is claimed.','cases':cases}
 (ROOT/'build/escape/cpu-results.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
