#!/usr/bin/env python3
"""Exercise linked live KEY/TEXT code, real transport, IRQ, keyboard and UART.

Only BIOS keyboard/tick memory and UART registers are modeled by Transport.
No application/runtime function is replaced, skipped, patched or mocked.
"""
import hashlib,json,struct
from unicorn.x86_const import (UC_X86_REG_AX,UC_X86_REG_BP,UC_X86_REG_SI,
 UC_X86_REG_DI,UC_X86_REG_ES,UC_X86_REG_EFLAGS)
from check_transport import Transport,ROOT,BINARY
DAY=0x1800b0
class Meta(Transport):
 def __init__(self,keys=()):
  super().__init__(keys);self.advance_ticks=False;self.carrier=True
  self.put('terminal_macro_pause_character',ord('~'),1)
  self.put('terminal_macro_character_delay_units',0)
 def tick_hook(self,uc,address,size,_):
  if address in (self.symbols['terminal_tick_low'],self.symbols['terminal_clock_ticks']):
   self.tick_reads+=1
   if self.advance_ticks:self.tick=(self.tick+1)%DAY
   uc.mem_write(0x46c,struct.pack('<I',self.tick))
 def input_port(self,uc,port,size,data):
  if port==self.get('uart_port_msr'):return (0x80 if self.carrier else 0)|(0x10 if self.cts else 0)
  return super().input_port(uc,port,size,data)
 def record(self,index,text,kind=3,terminated=True):
  assert 0<=index<10 and len(text)<=(51 if terminated else 52)
  data=struct.pack('<H',kind)+text+(b'\0' if terminated else b'')
  self.uc.mem_write(self.symbols['terminal_action_definitions']+54*index,data.ljust(54,b'Q'))
 def start(self,index=0):
  result=self.call('terminal_macro_start',ax=index)
  for reg,value in [(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678),(UC_X86_REG_ES,0xb800)]:assert self.uc.reg_read(reg)==value
  return result
 def poll(self,tick=None):
  if tick is not None:self.tick=tick%DAY
  before=len(self.tx);self.call('terminal_poll_io');return bytes(self.tx[before:])
 def finish(self,max_polls=100):
  for _ in range(max_polls):
   if not self.get('terminal_macro_active') and not self.get('terminal_tx_count'):return
   self.poll()
  raise AssertionError(('Live macro did not finish',self.get('terminal_macro_status'),bytes(self.tx)))

def main():
 digest=hashlib.sha256(BINARY.read_bytes()).hexdigest();cases=[]
 def check(name,fn):
  count=fn();cases.append({'case':name,'inputs':count,'passed':True});print(name,'passed',count,flush=True)
 def grammar():
  recipes=[(b'plain',b'plain'),(b'^M^J',b'\r\n'),(b'^@A',b'\0A'),(b'^^',b'\x1e'),(b'^^^',b'^'),(b'^`LOST',b''),(b'AB^ LOST',b'AB'),(b'X'*51,b'X'*51)]
  for text,want in recipes:
   m=Meta();m.record(0,text);assert m.start()==0;m.finish();assert bytes(m.tx)==want,(text,bytes(m.tx),want)
   assert not m.get('terminal_quit') and m.get('terminal_macro_status')==2
  for operand in range(1,256):
   if operand==94:continue # literal^^^ differs from double^^; both above.
   m=Meta();m.put('terminal_macro_pause_character',0,1);m.record(0,b'^'+bytes([operand]));assert m.start()==0;m.finish()
   value=0 if operand==64 else operand&31;want=bytes([value]) if operand==64 or value else b''
   assert bytes(m.tx)==want,(operand,bytes(m.tx),want)
  return len(recipes)+254
 check('actual-caret-operands-FF-to-wire-NUL-embedded-NUL-stop-and-51-byte-bound',grammar)
 def invalid():
  for text,terminated in [(b'broken^',True),(b'^^^^',True),(b'Q'*52,False)]:
   m=Meta();m.record(0,text,terminated=terminated);assert m.start()==3
   assert not m.get('terminal_macro_active') and not m.tx and not m.get('terminal_tx_count')
  for index in (10,11,255,0xffff):
   m=Meta();assert m.start(index)==1 and not m.tx
  for index in range(10):
   m=Meta();m.record(index,bytes([65+index]));assert m.start(index)==0;m.finish();assert bytes(m.tx)==bytes([65+index])
  for kind in (0,1,2,4,0xffff):
   for text in (b'',b'not-TEXT'):
    m=Meta();m.record(0,text,kind);assert m.start()==2,(kind,text)
    assert not m.get('terminal_macro_active') and not m.tx and not m.get('terminal_tx_count')
  for index in range(10):
   m=Meta([(0x78+index)<<8]);m.record(index,bytes([65+index]));m.poll();m.finish()
   assert bytes(m.tx)==bytes([65+index]) and not m.keys and not m.get('terminal_quit')
  for kind in (0,1,2):
   for text in (b'',b'unsupported'):
    m=Meta([0x7800]);m.record(0,text,kind);m.poll()
    assert (m.get('terminal_exit_code'),m.get('terminal_quit'))==(4,1) and not m.tx and not m.get('terminal_macro_active')
  m=Meta();m.record(0,b'');assert m.start()==0 and not m.get('terminal_macro_active')
  m.record(0,b'A');assert m.start()==0 and m.start()==4;m.finish();assert bytes(m.tx)==b'A'
  return 3+4+10+10+2+10+6
 check('unsafe-text-invalid-index-kind-first-empty-and-busy-atomicity',invalid)
 def pauses():
  for initial in (0,0xfffb,DAY-5):
   m=Meta();m.tick=initial;m.record(0,b'A~B');assert m.start()==0
   assert m.poll(initial)==b'A';assert m.poll(initial)==b''
   assert m.poll(initial+9)==b'' and m.get('terminal_macro_active')
   assert m.poll(initial+10)==b'B';m.finish();assert bytes(m.tx)==b'AB' and not m.get('terminal_quit')
  m=Meta();m.put('terminal_macro_pause_character',0xff,1);m.record(0,b'^@Z');assert m.start()==0
  assert m.poll(0)==b'' and m.poll(9)==b'' and m.poll(10)==b'Z';m.finish();assert bytes(m.tx)==b'Z'
  m=Meta();m.record(0,b'~~X');assert m.start()==0
  for tick in (0,9,10,19):assert m.poll(tick)==b''
  assert m.poll(20)==b'X';m.finish()
  return 5
 check('ten-full-BIOS-tick-pauses-lowword-wrap-midnight-and-FF-precedence',pauses)
 def stalls():
  total=0
  for initial in (0,0xfff0,DAY-20):
   for reason in ('cts','thre','xoff'):
    m=Meta();m.tick=initial;m.record(0,b'AB');assert m.start()==0
    if reason=='cts':m.put('uart_hardware_flow',1);m.cts=False
    elif reason=='thre':m.thre=False
    else:m.put('uart_software_flow',1);m.receive_irq(b'\x13')
    assert m.poll(initial+35)==b'' and m.get('terminal_macro_active')
    m.poll(initial+36)
    assert not m.tx and not m.get('terminal_macro_active')
    assert (m.get('terminal_macro_status'),m.get('terminal_exit_code'),m.get('terminal_quit'))==(6,10,1),reason
    total+=1
  m=Meta();m.record(0,b'AB');assert m.start()==0;m.put('uart_software_flow',1);m.receive_irq(b'\x13')
  assert m.poll(35)==b'';m.receive_irq(b'\x11');assert m.poll(35)==b'A'
  assert m.poll(70)==b'B';m.finish();assert not m.get('terminal_quit');total+=1
  return total
 check('actual-CTS-THRE-XOFF-no-progress-timeout-and-XON-recovery',stalls)
 def priorities():
  m=Meta();m.record(0,b'M');assert m.start()==0;m.enqueue(b'R'*80)
  for tick in range(1,81):assert m.poll(tick)==b'R' and m.get('terminal_macro_active')
  assert m.poll(81)==b'M';m.finish();assert bytes(m.tx)==b'R'*80+b'M' and not m.get('terminal_quit')
  # Flowcontrol bypasses ordinary XOFF/CTS restrictions and precedes macrodata.
  m=Meta();m.record(0,b'M');assert m.start()==0;m.put('uart_flow_pending',0x11,1);m.put('uart_hardware_flow',1);m.cts=False
  assert m.poll(0)==b'\x11';m.cts=True;assert m.poll(1)==b'M';m.finish()
  m=Meta();m.record(0,b'M');assert m.start()==0;m.receive_irq(b'\0\x80\xff')
  assert [m.call('uart_receive_byte') for _ in range(3)]==[0,128,255]
  m.finish();assert bytes(m.tx)==b'M'
  return 3
 check('normal-reply-ring-and-flowcontrol-priority-progress-epoch-and-binary-RX',priorities)
 def fifo():
  m=Meta([0x1e61,0x3062,0x2e63]);m.record(0,b'XY');assert m.start()==0
  for _ in range(10):m.poll()
  assert bytes(m.tx)==b'XYabc' and not m.keys and not m.get('terminal_quit')
  # Direct deferred FIFO wrap exercise executes the actual32-word ring API.
  m=Meta()
  for round_ in range(3):
   for n in range(32):m.call('terminal_defer_key',ax=0x100+round_*32+n)
   for n in range(32):assert m.call('terminal_take_deferred_key')==0x100+round_*32+n and not(m.uc.reg_read(UC_X86_REG_EFLAGS)&1)
   m.call('terminal_take_deferred_key');assert m.uc.reg_read(UC_X86_REG_EFLAGS)&1
  m=Meta();m.record(0,b'LONG');assert m.start()==0;m.thre=False
  m.keys.extend([0x1e61]*33)
  for _ in range(33):m.poll()
  assert (m.get('terminal_macro_active'),m.get('terminal_macro_status'),m.get('terminal_exit_code'),m.get('terminal_quit'))==(0,7,3,1)
  assert not m.tx;m.call('terminal_take_deferred_key');assert m.uc.reg_read(UC_X86_REG_EFLAGS)&1
  return 5
 check('macro-before-keystrokes-FIFO-wrap-full-explicit-exit-without-drop',fifo)
 def cancel():
  for key in (0x011b,0x2d00,0x2300,0x2000):
   m=Meta();m.record(0,b'UNSENT');assert m.start()==0;m.thre=False
   m.call('terminal_defer_key',ax=ord('q'));m.keys.append(key);m.poll()
   assert not m.get('terminal_macro_active') and not m.tx
   m.thre=True
   for _ in range(5):m.poll()
   assert not m.tx and m.get('terminal_macro_status')==3
   m.call('terminal_take_deferred_key');assert m.uc.reg_read(UC_X86_REG_EFLAGS)&1
  for state in (1,5,7,8,9):
   m=Meta();m.record(0,b'A');assert m.start()==0;m.put('connection_state',state);m.put('terminal_macro_tx_allowed',1)
   m.call('terminal_macro_poll');assert not m.get('terminal_macro_active') and not m.tx
  m=Meta();m.record(0,b'A');assert m.start()==0;m.put('terminal_quit',1);m.call('terminal_macro_poll')
  assert not m.get('terminal_macro_active') and not m.tx
  return 10
 check('Escape-AltX-AltH-AltD-cancel-clear-FIFO-and-modem-ownership',cancel)
 def carrier_and_configuration():
  # Establish carrier_seen through the actual MSR polling path, never by
  # modifying private application state; then drop both actual DCD and CTS.
  m=Meta();m.put('connection_enabled',1,1);m.put('connection_state',6)
  m.call('terminal_connection_poll');m.record(0,b'UNSENT');assert m.start()==0
  m.call('terminal_defer_key',ax=ord('q'));m.enqueue(b'REPLY')
  m.carrier=False;m.cts=False;m.put('uart_hardware_flow',1);m.poll()
  assert (m.get('connection_state'),m.get('connection_status'))==(0,6)
  assert not m.get('terminal_macro_active') and m.get('terminal_macro_status')==3
  assert not m.tx and not m.get('terminal_tx_count') and not m.get('terminal_quit')
  m.call('terminal_take_deferred_key');assert m.uc.reg_read(UC_X86_REG_EFLAGS)&1
  m.cts=True
  for _ in range(3):m.poll()
  assert not m.tx
  # Real maintained configuration decoder/prepare and original response/send
  # integration; only hardware remains modeled by existing Connection oracle.
  from check_connection import Connection
  c=Connection();Meta.record(c,0,b'OLD');assert c.call('terminal_macro_start',ax=0)==0
  c.call('terminal_defer_key',ax=ord('q'))
  c.call('terminal_connection_start',ax=0xa55a)
  assert c.get('connection_state') in (1,2) and not c.get('terminal_macro_active') and not c.tx
  c.call('terminal_take_deferred_key');assert c.uc.reg_read(UC_X86_REG_EFLAGS)&1
  # Cancellation's argument must survive terminal_macro_cancel before the
  # controller decides between online hangup(AX1) and attemptcancel(AX0).
  for argument,want_state in ((0,7),(1,9)):
   c=Connection();c.connect();c.tx.clear();Meta.record(c,0,b'OLD')
   assert c.call('terminal_macro_start',ax=0)==0
   c.call('terminal_connection_cancel',ax=argument)
   assert c.get('connection_state')==want_state and not c.get('terminal_macro_active') and not c.tx
   assert c.get('terminal_macro_status')==3
  for argument in (0,1,0xcafe):
   m=Meta();m.record(0,b'A');assert m.start()==0
   assert m.call('terminal_macro_cancel',ax=argument)==argument
   assert not m.get('terminal_macro_active') and m.get('terminal_macro_status')==3
  return 7
 check('actual-carrier-loss-and-configured-start-cancel-clear-macro-preserve-AX',carrier_and_configuration)
 assert hashlib.sha256(BINARY.read_bytes()).hexdigest()==digest,'Live binary changed during tests'
 proof={'passed':True,'binary_sha256':digest,'inputs':sum(x['inputs'] for x in cases),'cases':cases,'scope':'Actual linked live macro/start/poll/cancel/deferredFIFO, recovered caret expander, transport, BIOS keyboard reader, UART IRQ/flow and physical-write instructions. Only hardware registers, BIOSkeys and BIOSdayticks modeled. No runtime callback substituted.','limitations':['No DOSfilesystem/KEYreader or physical UART/modem/BBS validation in this CPUtest.','Cancellation cannot retract physically accepted bytes from earlier foreground polls.','Original calibrated character-delay units are retained metadata; live TEXT uses the maintained fast pacing policy. No calibrated live timing claim.']}
 (ROOT/'build/terminal/meta-actions-live-checks.json').write_text(json.dumps(proof,indent=2)+'\n')
 print('Live Meta/TEXT:',len(cases),'groups,',proof['inputs'],'inputs passed')
if __name__=='__main__':main()
