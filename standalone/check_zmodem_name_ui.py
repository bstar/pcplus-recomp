#!/usr/bin/env python3
"""Actual linked transfer-owner display, storage, wire and screen restoration."""
from collections import deque
import hashlib,json,zlib
from pathlib import Path
from check_terminal_zmodem_live import LiveZmodem,ROOT,BINARY,h,offer

def local_name(wire):
 if wire in ('ONE.BIN','A.ZIP','12345678.ZIP'):return wire
 return f'{zlib.crc32(wire.upper().encode()):08X}.ZIP'
def expected(wire,local,skip):
 shown=wire if len(wire)<=46 else wire[:45]+'~'
 return ('Remote: '+shown.ljust(46)+('  Skip: ' if skip else '  Save: ')+local.ljust(12)).ljust(80).encode('ascii')
class DisplayPeer(LiveZmodem):
 def __init__(self,wire,skip=False):
  self.recording=False;self.labels=set();super().__init__();self.local=local_name(wire)
  self.recording=True
  self.strict=False # Existing peer asserts ONE.BIN; this test checks its own path.
  self.script[0]=(h(1,0x23000000),offer(wire,len(self.source)+123,67))
  if skip:
   self.files['D:\\RECV\\'+self.local]=bytearray(b'EXISTING')
   self.script=deque([self.script[0],(h(5),h(8)),(h(8),b'OOAPP')])
 def output_port(self,u,port,size,value,data):
  super().output_port(u,port,size,value,data)
  if not self.recording:return
  assert self.script_enabled,'Independent peer script diverged'
  line=bytes(u.mem_read(0xb8000+3840,160))
  if line[::2].startswith(b'Remote: '):self.labels.add(line)

def main():
 cases=[];digest=hashlib.sha256(BINARY.read_bytes()).hexdigest()
 names=['ONE.BIN','A.ZIP','12345678.ZIP','PCPLUS PROBE 01 (1991).ZIP']+[('A'*(n-4)+'.ZIP') for n in (45,46,47,255)]
 for wire in names:
  for skip in (False,True):
   m=DisplayPeer(wire,skip);original=bytes((i*37+11)&255 for i in range(4000));m.uc.mem_write(0xb8000,original)
   assert m.run(owner=True)==0 and not m.script and not m.pending and not m.handles
   wanted=expected(wire,m.local,skip);assert m.labels,wire
   assert all(line[::2]==wanted and line[1::2]==b'\x1f'*80 for line in m.labels),(wire,m.labels,wanted)
   assert bytes(m.files['D:\\RECV\\'+m.local])==(b'EXISTING' if skip else m.source)
   # The completion notice owns the footer after transfer UI restoration.
   m.call('terminal_connection_notice_restore')
   assert bytes(m.uc.mem_read(0xb8000+3840,160))==original[3840:4000]
   assert bytes(m.uc.mem_read(0xb8000,3680))==original[:3680]
   assert m.get('_terminal_transfer_ui_visible',1)==0
   assert bytes(m.call('uart_receive_byte') for _ in range(3))==b'APP'
   cases.append(dict(wire=wire,local=m.local,skipped=skip,visible=True,restored=True))
 # Direct engine entry does not own the filename row. Existing progress
 # reporting independently uses the counter cells in row23.
 m=DisplayPeer('PCPLUS PROBE 01 (1991).ZIP');original=bytes((i*29+7)&255 for i in range(4000));m.uc.mem_write(0xb8000,original)
 assert m.run()==0 and not m.script and not m.handles and not m.labels
 assert bytes(m.uc.mem_read(0xb8000,3680))==original[:3680]
 assert bytes(m.uc.mem_read(0xb8000+3840,160))==original[3840:4000]
 cases.append(dict(case='no-UI-owner-no-filename-write',passed=True))
 result=dict(passed=True,binary_sha256=digest,cases=cases,inputs=len(cases),checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
  scope='Actual linked CONFIG_CODE ZMODEM callbacks, transfer UI save/restore, checked storage and UART ISR. Independent exact peer script, alias/80-column display expectations; modeled BIOS/kernel/hardware. No actual DOS/BBS/physical claim.')
 (ROOT/'build/terminal/zmodem-name-ui-checks.json').write_text(json.dumps(result,indent=2)+'\n');print('ZMODEM name UI:',len(cases),'linked cases PASS')
if __name__=='__main__':main()
