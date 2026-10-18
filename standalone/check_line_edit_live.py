#!/usr/bin/env python3
"""Independent actual-linked line-policy regression; only hardware is modeled."""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_AX,UC_X86_REG_DX,UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI,UC_X86_REG_ES
from check_transport import Transport
from check_scroll import Scroll
ROOT=Path(__file__).resolve().parents[1]
class Abort(Exception):pass
class Live(Transport):
 def __init__(self,keys=()):
  self.calls=[];super().__init__(keys)
  self.original=[((row%7+1)<<8)|(33+col) for row in range(25) for col in range(80)]
  self.uc.mem_write(0xb8000,struct.pack('<2000H',*self.original));self.uc.hook_add(UC_HOOK_CODE,self.observe)
 def interrupt(self,u,n,unused):
  if n==0x10:return Scroll.interrupt(self,u,n,unused)
  return super().interrupt(u,n,unused)
 def observe(self,u,address,size,unused):
  if address==self.symbols['terminal_abort']:raise Abort(u.reg_read(UC_X86_REG_AX))
 def cells(self):return list(struct.unpack('<2000H',self.uc.mem_read(0xb8000,4000)))
 def position(self,row,col):
  self.uc.reg_write(UC_X86_REG_DX,col);self.call('screen_set_cursor',ax=row)
 def feed(self,data):
  pending=memoryview(data);self.consumed=0
  while pending or self.get('uart_rx_count'):
   if pending and self.get('uart_rx_count')<128:
    block=bytes(pending[:512]);pending=pending[len(block):];self.receive_irq(block)
   before=self.get('uart_rx_count');value=self.call('ansi_next_byte');assert value!=0xffff
   self.call('terminal_receive_character',[value],limit=1000000)
   self.consumed+=before-self.get('uart_rx_count')
  assert not self.get('csi_unimplemented_service')
 def expected(self,row,bottom,count,insert):
  out=self.original[:]
  for y in range(row,bottom+1):
   source=y-count if insert else y+count
   out[y*80:y*80+80]=self.original[source*80:source*80+80] if row<=source<=bottom else [0x0720]*80
  return out

def run(wire=None):
 cases=[]
 def check(name,fn):fn();cases.append({'case':name,'passed':True});print(name,'passed',flush=True)
 def edit_cases():
  for command,insert in [(b'L',True),(b'M',False)]:
   for mono in (0,1):
    for top,bottom,row,col,count in [(0,24,5,17,1),(3,10,5,79,3),(3,10,10,0,8),(0,24,0,7,32767)]:
     t=Live();t.put('attributes_monochrome',mono);t.put('screen_first_row',top);t.put('screen_last_row',bottom);t.position(row,col)
     t.feed(b'\x1b['+str(count).encode()+command)
     assert t.cells()==t.expected(row,bottom,min(count,bottom-row+1),insert),(command,mono,top,bottom,row,col,count)
     assert (t.get('screen_cursor_row'),t.get('screen_cursor_column'))==(row,col)
     assert all(c['rectangle']==[row,0,bottom,79] for c in t.calls)
 check('network-L-M-both-profile-gates-margins-count-clipping-column-preservation',edit_cases)
 def defaults():
  for raw in (b'\x1b[M',b'\x1b[0M',b'\x1b[1M'):
   t=Live();t.position(6,23);t.feed(raw);assert t.cells()==t.expected(6,24,1,False)
 check('network-delete-line-omitted-zero-one-counts',defaults)
 def huge_counts():
  for command in (b'L',b'M'):
   for count in (32768,65535):
    t=Live();t.put('screen_first_row',3);t.put('screen_last_row',10);t.position(5,17)
    t.feed(b'\x1b['+str(count).encode()+command)
    assert 1<=len(t.calls)<=6 and t.get('screen_cursor_column')==17
    assert t.cells()[:5*80]==t.original[:5*80] and t.cells()[11*80:]==t.original[11*80:]
 check('high-bit-counts-remain-bounded-and-preserve-outside-region',huge_counts)
 def invalid_regions():
  for top,bottom,row,protected,wrap in [(3,10,2,0,0),(3,10,11,0,0),(0,25,5,0,0),(3,10,5,1,1)]:
   for service in ('csi_service_d668','csi_service_d73c','csi_service_daf2'):
    t=Live();t.put('screen_first_row',top);t.put('screen_last_row',bottom);t.put('screen_cursor_row',row);t.put('screen_cursor_column',13);t.put('screen_attribute_checks',protected);t.put('screen_cursor_wrap',wrap);t.put('ansi_parameters',32767)
    t.call(service);assert t.cells()==t.original and not t.calls
    assert (t.get('screen_cursor_row'),t.get('screen_cursor_column'))==(row,13)
 check('outside-margins-invalid-bottom-and-protected-state-are-no-op',invalid_regions)
 def attributes():
  t=Live();t.position(5,17);t.put('screen_cursor_wrap',1)
  try:t.feed(b'\x1b[M')
  except Abort as e:assert e.args==(0x2d98,)
  else:raise AssertionError('Unrecovered attribute repair silently skipped')
  assert t.cells()==t.original
 check('unsupported-attribute-plane-remains-explicit-before-mutation',attributes)
 def original_lines():
  for service,insert in [('csi_service_d668',True),('csi_service_d73c',False)]:
   t=Live();t.position(5,17);t.put('terminal_ansi_m_policy',1);t.call(service)
   assert t.cells()==t.expected(5,24,1,insert) and t.get('screen_cursor_column')==0
 check('original-policy-recovered-per-line-column-home-semantics',original_lines)
 def waits():
  for initial in (0,0xfff0):
   t=Live();t.put('terminal_ansi_m_policy',1);t.tick=initial;t.call('csi_service_daf2')
   assert t.get('terminal_ansi_wait_timed_out')==1 and t.tick_reads==37 and not t.get('terminal_ansi_wait_active') and t.cells()==t.original
  for data in (b'\x0e',b'garbage\x0e'):
   t=Live();t.put('terminal_ansi_m_policy',1);t.receive_irq(data);t.call('csi_service_daf2')
   assert not t.get('uart_rx_count') and not t.get('terminal_ansi_wait_timed_out') and not t.get('terminal_ansi_wait_active')
  for key,want_quit in [(0x011b,0),(0x2d00,1)]:
   t=Live([key]);t.put('terminal_ansi_m_policy',1);t.call('csi_service_daf2')
   assert t.get('terminal_quit')==want_quit and not t.get('terminal_ansi_wait_active') and not t.get('terminal_ansi_wait_timed_out')
  t=Live();t.put('terminal_ansi_m_policy',1);t.put('connection_state',2);t.call('csi_service_daf2')
  assert t.tick_reads==1 and not t.get('terminal_ansi_wait_active') and not t.get('terminal_ansi_wait_timed_out')
 check('original-alternate-wait-CtrlN-discard-Escape-AltX-timeout-wrap-modem-yield',waits)
 def abi():
  for service in ('csi_service_d668','csi_service_d73c','csi_service_daf2'):
   t=Live();t.position(5,17);t.put('ansi_parameters',3);t.call(service)
   for reg,value in [(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678),(UC_X86_REG_ES,0xb800)]:assert t.uc.reg_read(reg)==value,(service,reg)
 check('network-wrapper-near-stack-BP-SI-DI-ES-preservation',abi)
 if wire:
  def captured():
   t=Live();t.feed(wire.read_bytes());assert not t.get('csi_unimplemented_service')
  check('explicit-actual-captured-stream-through-real-UART-input-and-video',captured)
 result={'passed':True,'binary_sha256':hashlib.sha256((ROOT/'build/terminal/TERMINAL.EXE').read_bytes()).hexdigest(),'cases':cases,'wire':str(wire) if wire else None,'scope':'Actual linked live line policy, recovered line/erase/cursor and UART/keyboard instructions. Hardware-only video/UART/BIOS keyboard/tick oracle; no product service stub. NETWORK is intentional maintained compatibility policy; ORIGINAL alternate wait bounded36ticks. No physical modem or complete terminal claim.'}
 out=ROOT/'build/terminal/line-edit-live-checks.json';out.write_text(json.dumps(result,indent=2)+'\n');print('Live line policy:',len(cases),'groups passed')
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--wire',type=Path);a=p.parse_args();run(a.wire)
