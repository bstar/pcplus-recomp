#!/usr/bin/env python3
"""Execute full-height shared views with real selector, key, IRQ and parser code.
BIOS/UART/DOS boundaries modeled; not physical timing or complete modal parity.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn.x86_const import *
from unicorn import UC_HOOK_CODE
import check_transport as transport
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 binary=a.terminal.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 manifest=json.loads((binary.parent/'manifest.json').read_text());assert manifest['experimental_large_view_frames'];assert sha(binary)==manifest['binary_sha256']
 for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 transport.BINARY=binary;transport.MAP=binary.parent/'terminal.map'
 from check_display_transaction_live import Transaction
 from check_recording_rx_live import ordinary
 class View(Transaction):
  def interrupt(self,u,n,d):
   if n==0x21 and u.reg_read(UC_X86_REG_AX)==0x2a00:
    u.reg_write(UC_X86_REG_CX,1993);u.reg_write(UC_X86_REG_DX,0x0307);u.reg_write(UC_X86_REG_AX,0);return
   if n==0x21 and u.reg_read(UC_X86_REG_AX)==0x2c00:
    u.reg_write(UC_X86_REG_CX,0x0c00);u.reg_write(UC_X86_REG_DX,0);return
   return super().interrupt(u,n,d)
  def setup(self,rows,hidden=0):
   self.saved(hidden,2,rows,0);assert self.invoke(entry='_terminal_display_apply_saved')==0
   ordinary(self,b''.join(f'\x1b[{r};1HROW{r:02d}'.encode() for r in range(1,rows-(0 if hidden else 1)+1)))
   self.uc.mem_write(0xb8000+rows*160,b'\x5a'*(8000-rows*160+16))
   self.uc.mem_write(self.symbols['redisplay_live'],b'\x56'*8000)
   self.uc.mem_write(self.symbols['redisplay_view'],b'\x7a'*8000)
  def video(self):return bytes(self.uc.mem_read(0xb8000,8000))
  def assert_unused(self,rows):
   used=rows*160
   for name,value in [('redisplay_live',0x56),('redisplay_view',0x7a)]:
    assert bytes(self.uc.mem_read(self.symbols[name]+used,8000-used))==bytes([value])*(8000-used),name
   assert bytes(self.uc.mem_read(0xb8000+used,8000-used+16))==b'\x5a'*(8000-used+16)
 cases=[]
 def done(name,n):cases.append(dict(case=name,inputs=n,passed=True));print(name,n,'PASS',flush=True)
 count=0
 for rows in [25,28,43,50]:
  for hidden in [0,1]:
   for key in [0x2c00,0x8400,0x8300,0x1400]:
    m=View();m.setup(rows,hidden);before=m.video();m.key(key);assert m.get('_redisplay_active'),(rows,hidden,key)
    if key!=0x8400:assert m.video()[4000:rows*160]==before[4000:rows*160]
    else:
     footer=m.video()[(rows-1)*160:rows*160:2]
     assert b'Frozen history;' in footer,(rows,hidden,footer)
     if rows>25:assert m.video()[4000:rows*160]!=before[4000:rows*160]
    frozen=bytes(m.uc.mem_read(m.symbols['redisplay_snapshot'],63000))
    m.call('terminal_redisplay_before',limit=1000000);assert m.video()==before
    payload=f'\x1b[{rows-(0 if hidden else 1)};1HLATEST\x1b[6n'.encode()
    ordinary(m,payload);expected=m.video();cursor=m.cursor
    assert expected[(rows-(0 if hidden else 1)-1)*160:(rows-(0 if hidden else 1)-1)*160+12:2]==b'LATEST'
    m.call('terminal_redisplay_idle',limit=1000000);m.drain()
    assert bytes(m.tx)==f'\x1b[{rows-(0 if hidden else 1)};7R'.encode()
    if key!=0x8400:assert m.video()[4000:rows*160]==expected[4000:rows*160]
    m.key(27);assert m.video()==expected and m.cursor==cursor,(rows,hidden,key)
    assert not m.get('_redisplay_active') and not m.get('_clipboard_ui_visible') and not m.get('terminal_quit')
    assert bytes(m.uc.mem_read(m.symbols['redisplay_snapshot'],63000))==frozen
    m.assert_unused(rows);count+=1
 done('all-heights-status-states-and-four-views-preserve-full-updated-underlay-and-guards',count)
 # Repeat receive/repaint with actual IRQ delivery and partial query parsing.
 m=View();m.setup(50);m.key(0x2c00)
 for i in range(64):
  delivered=[]
  def continuation(u,address,size,data):
   if address==m.symbols['uart_receive_byte'] and m.get('terminal_parser_active') and not m.get('uart_rx_count') and not delivered:
    delivered.append(True);m.rx.extend(b'6n') # Real pending IRQ delivery, not a parser replacement.
  hook=m.uc.hook_add(UC_HOOK_CODE,continuation)
  try:
   m.call('terminal_redisplay_before',limit=1000000);ordinary(m,f'\x1b[49;1H{i:04d}\x1b['.encode())
   assert delivered and not m.get('terminal_parser_active')
  finally:m.uc.hook_del(hook)
  expected=m.video();m.call('terminal_redisplay_idle',limit=1000000)
 m.drain();assert bytes(m.tx)==b'\x1b[49;5R'*64 and not m.get('uart_rx_dropped')
 m.key(27);assert m.video()==expected and b'0063' in m.video()[48*160:49*160:2]
 done('64-sustained-full-height-menu-receive-repaint-query-cycles',64)
 count=0
 for mismatch in ['bad-height','BDA-absent-at50','wrong-canonical-height','wrong-effective-rows','wrong-live-segment','wrong-view-segment','wrong-live-offset','wrong-view-offset']:
  m=View();m.setup(50);before=m.video();frames={n:bytes(m.uc.mem_read(m.symbols[n],8000)) for n in ['redisplay_live','redisplay_view']}
  if mismatch=='bad-height':m.uc.mem_write(0x484,b'\x1d')
  elif mismatch=='BDA-absent-at50':m.uc.mem_write(0x484,b'\0')
  elif mismatch=='wrong-canonical-height':m.put('ui_window_rows',43)
  elif mismatch=='wrong-effective-rows':m.put('csi_row_count',24)
  else:
   part='redisplay_live_segment' if 'live' in mismatch else 'redisplay_view_segment'
   address=m.symbols[part]-(2 if mismatch.endswith('offset') else 0)
   value=int.from_bytes(m.uc.mem_read(address,2),'little');m.uc.mem_write(address,struct.pack('<H',(value+1)&65535))
  m.key(0x2c00);assert not m.get('_redisplay_active') and m.video()==before and not m.tx,mismatch
  m.assert_unused(50)
  assert all(bytes(m.uc.mem_read(m.symbols[n],8000))==data for n,data in frames.items())
  count+=1
 done('incoherent-height-canonical-and-frame-identity-refusals-before-write',count)
 # Full history remains63K; pagination uses the accepted content height.
 m=View();m.setup(50)
 m.put('terminal_history_pointer',m.get('terminal_history_start'));m.put('terminal_history_wrapped',0)
 ordinary(m,b''.join(f'L{i:04d}\r\n'.encode() for i in range(300)))
 m.key(0x8400);bottom=m.video();m.key(0x4700);top=m.video();assert top!=bottom and b'L0000' in top[::2]
 m.key(0x5100);page=m.video();assert b'L0048' in page[160:320:2],page[160:320:2]
 m.key(0x4900);assert m.video()==top;m.key(0x4f00);assert m.video()==bottom;m.key(27)
 done('full-height-history-home-page-down-up-and-end',4)
 for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 report=dict(passed=True,inputs=sum(c['inputs'] for c in cases),cases=cases,terminal_sha256=sha(binary),manifest_sha256=sha(binary.parent/'manifest.json'),checker_sha256=sha(Path(__file__)),scope=__doc__)
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
