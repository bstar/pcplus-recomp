#!/usr/bin/env python3
"""Native dedicated-print diagnostic with opt-in original instruction replay."""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
from dos_image import DosImage
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/print_controller'
PROOF=json.loads((ROOT/'reconstruction/print_controller/provenance.json').read_text())
COUNTERS=['save','restore','hide','status','shape','break','next','open','close','putc','flush']
FIELDS=['fixture_'+n+'_calls' for n in COUNTERS]+['fixture_key_index','fixture_sent_count','fixture_rx_index','fixture_wire_count','fixture_last_handle','controller_rx_count','printer_stream']
def image(original):
 m=DosImage(OUT/'PRINTCTL.EXE',OUT/'print_controller.map')
 if not original:return m
 old=m.data_base;data=bytes(m.uc.mem_read(old,65536));m.ds=0x4000;m.data_base=0x40000;m.uc.mem_write(m.data_base,data)
 for name,at in list(m.symbols.items()):
  if old<=at<old+65536:m.symbols[name]=m.data_base+at-old
 b=(ROOT/'analysis/pcplus-originals/PCPLUS-main-2.01.EXE').read_bytes();assert hashlib.sha256(b).hexdigest()==PROOF['source_sha256'];m.uc.mem_write(m.base,b[0x1200:0xe2d0])
 for unit in PROOF['units']:
  st=int(unit['start'],16);off=unit['source_file_offset'];m.uc.mem_write(m.base+st,b[off:off+unit['bytes']])
 for at,name in PROOF['state'].items():m.symbols[name]=m.data_base+int(at,16)
 for at,name in PROOF['boundaries'].items():m.symbols[name]=m.base+int(at,16)
 for n,data in [('printer_device',b'PRN\0'),('controller_open_mode',b'wb\0')]:m.uc.mem_write(m.symbols[n],data)
 targets={int(a,16):n for a,n in PROOF['boundaries'].items() if n not in ['print_controller_original','printer_byte_original']}
 targets.update({0x8436:'printer_putc',0x8c54:'printer_flush'})
 def boundary(u,at,size,_):
  name=targets.get(at-m.base)
  if not name:return
  sp=u.reg_read(UC_X86_REG_SP);w=struct.unpack('<4H',u.mem_read(m.data_base+sp,8));cleanup=0;ax=None
  kind=name.replace('controller_','').replace('printer_','');kind={'cursor_shape':'shape','hide_cursor':'hide','next_byte':'next','key_available':'poll','read_key':'key','send_key':'send'}.get(kind,kind)
  if kind in COUNTERS:m.put('fixture_'+kind+'_calls',m.get('fixture_'+kind+'_calls')+1)
  if kind in ['save','restore']:cleanup=6
  elif kind=='poll':ax=int((not m.get('fixture_keys_after_rx') or not m.get('controller_rx_count')) and m.get('fixture_key_index')<m.get('fixture_key_count'))
  elif kind=='key':
   index=m.get('fixture_key_index');ax=struct.unpack('<H',u.mem_read(m.symbols['fixture_keys']+index*2,2))[0];m.put('fixture_key_index',index+1)
  elif kind=='send':
   index=m.get('fixture_sent_count');u.mem_write(m.symbols['fixture_sent']+index*2,struct.pack('<H',w[1]));m.put('fixture_sent_count',index+1);cleanup=2
  elif kind in ['dequeue','next']:
   ax=65535
   if m.get('controller_rx_count'):
    index=m.get('fixture_rx_index');ax=u.mem_read(m.symbols['fixture_rx']+index,1)[0];m.put('fixture_rx_index',index+1);m.put('controller_rx_count',m.get('controller_rx_count')-1)
  elif kind in ['open','close','flush','putc']:
   ax=m.get('fixture_'+kind+'_result')
   if kind=='putc':
    index=m.get('fixture_wire_count');assert index<4096;u.mem_write(m.symbols['fixture_wire']+index,bytes([w[1]&255]));m.put('fixture_wire_count',index+1);m.put('fixture_last_handle',w[2])
  if ax is not None:u.reg_write(UC_X86_REG_AX,ax)
  u.reg_write(UC_X86_REG_SP,sp+2+cleanup);u.reg_write(UC_X86_REG_IP,w[0])
 m.uc.hook_add(UC_HOOK_CODE,boundary);return m

def run(original=False):
 cases=[]
 def add(label,rx,expected,**kw):cases.append(dict(label=label,rx=rx,expected=expected,**kw))
 add('all256 dequeued values',bytes(range(256))+b'\x1b[4i',bytes(v for x in range(256) if x not in (0,127) for v in ([20,20] if x==20 else [x])))
 add('binary controls and double DC4',bytes([0,127,65,10,13,26,255,20,66])+b'\x1b[4i',bytes([65,10,13,26,255,20,20,66]))
 add('ANSI terminator retains following',b'A\x1b[4iTAIL',b'A',remaining=4)
 add('enable sequence discarded',b'\x1b[5iA\x1b[4i',b'A')
 add('zero sequence discarded',b'\x1b[0iA\x1b[4i',b'A')
 add('unknown escape replay',b'\x1bZA\x1b[4i',b'\x1bZA')
 add('ignored NUL DEL in escape',b'\x1b\0[\x7f4i',b'')
 add('digits without CSI introducer replay',b'\x1b4iX\x1b[4i',b'\x1b4iX\x1b[4i',sent=[27])
 add('numeric substring4 accepted',b'\x1b[14iTAIL',b'',remaining=4)
 add('mixed4and5 accepted',b'\x1b[4;5iTAIL',b'',remaining=4)
 add('semicolon ignored while parsing',b'\x1b[1;4i',b'')
 add('profile31 DC4 exits',b'A\x14TAIL',b'A',terminal=31,remaining=4)
 add('profile1 ESCX exits',b'A\x1bXTAIL',b'A',terminal=1,remaining=4)
 add('other profile ESCa exits',b'A\x1baTAIL',b'A',dec=0,other=1,remaining=4)
 add('a waits with family disabled',b'\x1baZ\x1b[4i',b'\x1baZ')
 add('X waits with non1 profile',b'\x1bXY\x1b[4i',b'\x1bXY')
 add('nonDEC i waits then replay',b'\x1b[iX',b'\x1b[iX\xff',dec=0,sent=[27])
 add('native timeout sentinel forwarded',b'\x1b',b'\x1b\xff',sent=[27])
 add('early keyboard cancel retains RX',b'AB',b'A',keys=[27,27],sent=[27],remaining=1,keys_after_rx=0)
 add('ordinary keys and consecutive ESC',b'A',b'A',keys=[0x1e61,0x001b,0x001b],sent=[0x1e61,0x001b])
 add('break forwarded',b'',b'',keys=[0x3000,27,27],sent=[0x3000,27],breaks=1)
 add('highword ESC not cancellation',b'',b'',keys=[0x011b,27,27],sent=[0x011b,27])
 add('separated escapes do not exit',b'',b'',keys=[27,65,27,27],sent=[27,65,27])
 for opened in [0,0x1111]:
  for errors in [0,65535]:add('ignored CRT errors',b'A\x1b[4i',b'A',opened=opened,errors=errors)
 results=[]
 for case in cases:
  m=image(original);rx=case['rx'];keys=case.get('keys',[27,27]);trace=[]
  points={0xd1a3:'saw4',0xd208:'saw[',0xd1db:'reset_flags',0xd1c1:'replay_buffer',0xd246:'exit'}
  locations={(m.base+at if original else m.symbols['print_at_'+format(at,'04x')]):name for at,name in points.items()}
  def trace_hook(u,at,size,_):
   if at in locations:trace.append(locations[at])
  m.uc.hook_add(UC_HOOK_CODE,trace_hook)
  for n,v in {'controller_rx_count':len(rx),'controller_terminal_id':case.get('terminal',6),'controller_dec_family':case.get('dec',1),'controller_other_family':case.get('other',0),'fixture_key_count':len(keys),'fixture_keys_after_rx':case.get('keys_after_rx',1),'fixture_open_result':case.get('opened',0x1111),'fixture_putc_result':case.get('errors',0),'fixture_flush_result':case.get('errors',0),'fixture_close_result':case.get('errors',0)}.items():m.put(n,v)
  m.uc.mem_write(m.symbols['fixture_rx'],rx);m.uc.mem_write(m.symbols['fixture_keys'],struct.pack('<'+'H'*len(keys),*keys));m.call('print_controller_original',limit=100000)
  for reg,value in [(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678),(UC_X86_REG_DS,m.ds),(UC_X86_REG_SS,m.ds)]:assert m.uc.reg_read(reg)==value,(case['label'],reg)
  wire=bytes(m.uc.mem_read(m.symbols['fixture_wire'],m.get('fixture_wire_count')));assert wire==case['expected'],(case['label'],wire,case['expected'])
  sent=list(struct.unpack('<'+'H'*m.get('fixture_sent_count'),m.uc.mem_read(m.symbols['fixture_sent'],m.get('fixture_sent_count')*2)))
  assert sent==case.get('sent',[]),(case['label'],sent)
  for n in ['save','restore','hide','status','shape','open','close']:assert m.get('fixture_'+n+'_calls')==1,(case['label'],n)
  assert m.get('fixture_flush_calls')==len(wire) and m.get('fixture_putc_calls')==len(wire)
  assert m.get('fixture_break_calls')==case.get('breaks',0)
  assert m.get('controller_rx_count')==case.get('remaining',0)
  results.append({'case':case['label'],'wire_hex':wire.hex(),'sent':sent,'branch_trace':trace,'state':{n:m.get(n) for n in FIELDS}})
 # No idle timeout/carrier/quit callback exists in this native loop. Characterize
 # its actual nonreturn with no input instead of inventing an EOF success.
 m=image(original);m.put('controller_rx_count',0);m.put('fixture_key_count',0)
 try:m.call('print_controller_original',limit=10000)
 except AssertionError:
  assert not m.returned
 else:raise AssertionError('Empty native controller unexpectedly returned')
 assert m.get('fixture_open_calls')==1 and m.get('fixture_close_calls')==0 and m.get('fixture_restore_calls')==0
 results.append({'case':'noinput has no bounded termination','instruction_budget':10000,'state':{n:m.get(n) for n in ['fixture_open_calls','fixture_close_calls','fixture_restore_calls','controller_rx_count']}})
 return results
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--original',action='store_true');a=p.parse_args();linked=run();original=run(True) if a.original else None
 if original is not None:assert linked==original,'Original/source discrepancy'
 result={'passed':True,'binary_sha256':hashlib.sha256((OUT/'PRINTCTL.EXE').read_bytes()).hexdigest(),'linked_cases':len(linked),'original_cases':len(original) if original else 0,'cases':linked,'scope':'Exact native controller and byte wrapper; memory UART/keyboard/CRT/UI boundaries, no real printer or original app execution.'};(OUT/'checks.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS',len(linked),'linked,',len(original) if original else 0,'original comparisons')
