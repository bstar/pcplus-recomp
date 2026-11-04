#!/usr/bin/env python3
"""Execute ordinary CSI18t through actual parser and whole-packet UART queue.
BIOS/UART effects modeled; no bridge proxy or physical acceptance.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn.x86_const import *
import check_transport as transport
from check_display_transaction_live import Transaction
from check_recording_rx_live import ordinary,inject
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
QUERY=b'\x1b[18t'
FIELDS=('screen_cursor_row','screen_cursor_column','screen_visible_column','screen_previous_row','screen_previous_column',
 'screen_video_offset','screen_attribute_offset','csi_wrap_pending','csi_saved_row','csi_saved_column',
 'cursor_state_saved_3342','cursor_state_saved_cdf0','cursor_state_saved_cdec','cursor_state_saved_cdfc','cursor_state_saved_ce04',
 'cursor_state_saved_1f70','cursor_state_saved_1d20','cursor_state_saved_cdd2','csi_origin_mode','csi_origin_row','csi_origin_bottom',
 'screen_first_row','screen_last_row','screen_top_margin','screen_bottom_margin','screen_viewport_enabled','screen_viewport_active',
 'screen_viewport_offset','screen_viewport_left','attributes_current','attributes_normal_value','attributes_bold_active','attributes_blink_active',
 'ansi_charset_g0_flag_graphics','ansi_charset_g1_flag_graphics','csi_row_count','csi_last_row','csi_column_count','erase_cell_count')
def state(m):
 planes=m.full()['planes'];planes.pop('ansi_parameters')
 return dict(fields={n:m.get(n) for n in FIELDS if n in m.symbols},planes=planes,
  video=bytes(m.uc.mem_read(0xb8000,8000)),meta=m.meta())
def packet(m):
 head=m.get('terminal_tx_head');count=m.get('terminal_tx_count');buf=m.symbols['terminal_tx_buffer']
 return bytes(m.uc.mem_read(buf+(head+i)%1024,1)[0] for i in range(min(count,1024)))
def seed_ring(m,count,head=0):
 m.put('terminal_tx_head',head);m.put('terminal_tx_tail',(head+count)%1024);m.put('terminal_tx_count',count)
 for i in range(min(count,1024)):m.uc.mem_write(m.symbols['terminal_tx_buffer']+(head+i)%1024,b'P')
 m.uc.mem_write(m.symbols['terminal_tx_origin_bits'],b'\xff'*128);m.thre=False

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 binary=a.terminal.resolve();manifest=json.loads((binary.parent/'manifest.json').read_text());assert manifest['experimental_window_size_report'] and sha(binary)==manifest['binary_sha256']
 for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 transport.BINARY=binary;transport.MAP=binary.parent/'terminal.map';out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False);cases=[]
 def done(name,n=1):cases.append(dict(case=name,inputs=n,passed=True));print('PASS',name,n,flush=True)
 count=0
 for profile in (4,6):
  for hidden in (0,1):
   for physical in (25,28,43,50):
    m=Transaction();m.put('csi_terminal_id',profile);m.set_baseline('csi_terminal_id',profile);m.saved(hidden=hidden,selector=2,rows=physical,mode=0)
    assert m.invoke(entry='_terminal_display_apply_saved')==0 and m.get('csi_terminal_id')==profile
    ordinary(m,b'\x1b[4;5H\x1b7\x1b[31m\x1b[3;12r\x1b[?6h\x1b[4;5H');before=state(m)
    ordinary(m,QUERY);m.drain();effective=physical if hidden else physical-1
    assert bytes(m.tx)==f'\x1b[8;{effective};80t'.encode() and state(m)==before,(profile,hidden,physical,bytes(m.tx));count+=1
 done('actual-parser-accepted-height-status-profile-margin-attribute-and-saved-cursor-preservation',count)
 m=Transaction();ordinary(m,b'\x1b[5;80HA');assert m.get('csi_wrap_pending')==1;before=state(m)
 ordinary(m,QUERY);m.drain();assert state(m)==before and bytes(m.tx)==b'\x1b[8;24;80t'
 ordinary(m,b'Z');assert bytes(m.uc.mem_read(0xb8000+5*160,1))==b'Z'
 done('query-preserves-deferred-wrap-and-next-character-behavior')
 m=Transaction();m.uc.mem_write(0x449,b'\x03\x50\x00');m.uc.mem_write(0x462,b'\0')
 assert m.call('terminal_native_width',ax=1,limit=4000000)==0
 ordinary(m,b'\x1b[2;120H');before=state(m);ordinary(m,QUERY);m.drain()
 assert bytes(m.tx)==b'\x1b[8;24;132t' and state(m)==before
 done('logical-wide-text-area-query-preserves-existing-viewport')
 m=Transaction();inject(m,QUERY+b'X');first=m.call('uart_receive_byte');assert first==27
 m.call('terminal_receive_input',ax=first,limit=1000000)
 assert m.get('uart_rx_count')==1
 ordinary(m,b'');m.drain();assert bytes(m.tx)==b'\x1b[8;24;80t' and bytes(m.uc.mem_read(0xb8000,1))==b'X'
 done('real-continuation-reader-consumes-one-query-and-retains-next-data-byte')
 count=0
 for query in (b'\x1b[t',b'\x1b[17t',b'\x1b[19t',b'\x1b[8;43;80t',b'\x1b[18;1t',b'\x1b[?18t',b'\x1b[>18t'):
  m=Transaction();before=state(m);ordinary(m,query);m.drain();assert not m.tx and state(m)==before;count+=1
 done('other-window-operations-private-and-extra-parameter-forms-remain-inert',count)
 for prior in (b'\x1b[?18t',b'\x1b[>18t',b'\x1b[18;1t',b'\x1b[8;43;80t'):
  m=Transaction();ordinary(m,prior+QUERY);m.drain();assert bytes(m.tx)==b'\x1b[8;24;80t'
 done('following-normal-query-clears-private-and-parameter-history',4)
 expected=b'\x1b[8;24;80t';count=0
 for head in (0,1019):
  for available in (0,len(expected)-1,len(expected),len(expected)+1,1024):
   m=Transaction();initial=1024-available;seed_ring(m,initial,head);before=packet(m)
   ordinary(m,QUERY);want=before+(expected if available>=len(expected) else b'')
   assert packet(m)==want and not m.get('terminal_quit') and not m.get('terminal_exit_code')
   if available>=len(expected):
    bits=bytes(m.uc.mem_read(m.symbols['terminal_tx_origin_bits'],128))
    for i in range(len(expected)):
     slot=(head+initial+i)%1024;assert not bits[slot//8]&(1<<(slot%8))
   m.thre=True;m.drain();assert bytes(m.tx)==want;count+=1
 done('atomic-capacity-wrap-and-nonuser-origin-before-real-UART-delivery',count)
 count=0
 for field,value in [('terminal_tx_count',1025),('terminal_tx_head',1024),('terminal_tx_tail',1024),('terminal_tx_tail',1)]:
  m=Transaction();seed_ring(m,0);m.put(field,value)
  before=(m.get('terminal_tx_head'),m.get('terminal_tx_tail'),m.get('terminal_tx_count'),bytes(m.uc.mem_read(m.symbols['terminal_tx_buffer'],1024)))
  ordinary(m,QUERY)
  after=(m.get('terminal_tx_head'),m.get('terminal_tx_tail'),m.get('terminal_tx_count'),bytes(m.uc.mem_read(m.symbols['terminal_tx_buffer'],1024)))
  assert before==after and not m.tx and not m.get('terminal_quit');count+=1
 done('corrupted-queue-refuses-complete-response-without-queue-writes',count)
 for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 result=dict(passed=True,terminal_sha256=sha(binary),manifest_sha256=sha(binary.parent/'manifest.json'),cases=cases,checker_sha256=sha(Path(__file__)),scope=__doc__+' Actual parser/report/queue/origin/UART instructions execute. CSI temporary parsing fields can change; cursor/modes/attributes/save bank/history/video/shadow/selection remain unchanged. No staged SynthModem probe, live BBS/transfer/analog/physical or deployment acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
