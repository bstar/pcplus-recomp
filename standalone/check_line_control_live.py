#!/usr/bin/env python3
"""Actual linked original line shortcut/menu cycles with guarded display ownership.
BIOS/UART/DOS and fault timings modeled; no online NAWS/physical acceptance.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn.x86_const import *
import check_transport as transport
ROOT=Path(__file__).resolve().parents[1];sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 binary=a.terminal.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 manifest=json.loads((binary.parent/'manifest.json').read_text());assert manifest['experimental_line_control'] and sha(binary)==manifest['binary_sha256']
 for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 transport.BINARY=binary;transport.MAP=binary.parent/'terminal.map'
 from check_display_transaction_live import Transaction
 from check_recording_rx_live import ordinary
 def fresh(rows=50,mode=0,hidden=0):
  m=Transaction();m.saved(hidden,1,rows,mode);assert m.invoke(entry='_terminal_display_startup')==0;return m
 def entry(m,key):
  u=m.uc;seg,_=m.entries['terminal_local_control_key'];sp=m.offset('terminal_stack_top')-4
  u.mem_write(m.data_base+sp,struct.pack('<2H',m.return_offset,m.code_segment))
  for r,v in [(UC_X86_REG_CS,m.base_segment+seg),(UC_X86_REG_DS,m.ds),(UC_X86_REG_SS,m.ds),(UC_X86_REG_SP,sp),(UC_X86_REG_AX,key),(UC_X86_REG_BP,0xbabe),(UC_X86_REG_EFLAGS,0x202)]:u.reg_write(r,v)
  m.returned=False;u.emu_start(m.symbols['terminal_local_control_key'],0,count=1000000);assert m.returned and u.reg_read(UC_X86_REG_SP)==sp+4 and u.reg_read(UC_X86_REG_BP)==0xbabe and u.reg_read(UC_X86_REG_AX)==key and u.reg_read(UC_X86_REG_EFLAGS)&1
 cases=[]
 def done(name,n):cases.append(dict(case=name,inputs=n,passed=True));print(name,n,'PASS',flush=True)
 n=0
 for rows in (25,28,43,50):
  for mode in (0,3):
   for hidden in (0,1):
    for key in (0x0c1f,0x001f,0xe01f):
     m=fresh(rows,mode,hidden);saved=bytes(m.uc.mem_read(m.symbols['_terminal_display_preferences'],8));history=bytes((i*17+3)&255 for i in range(63000));m.uc.mem_write(m.symbols['terminal_history_buffer'],history)
     for selector in ([2,1] if not mode else [2,3,4,1]):
      m.key(key);physical=rows if selector in (2,4) else 25;m.verify(physical,hidden)
      assert m.meta()==(selector,1,0,0) and not m.get('terminal_local_control_status') and not m.tx
      assert bytes(m.uc.mem_read(m.symbols['_terminal_display_preferences'],8))==saved and bytes(m.uc.mem_read(m.symbols['terminal_history_buffer'],63000))==history;n+=1
 done('all-heights-normalized-keys-two-four-cycles-visibility-prefs-history-and-full-shadow',n)
 n=0
 for mode in (0,3):
  for rows in (28,43,50):
   for browser in (False,True):
    m=fresh(rows,mode);m.key(0x2c00)
    if browser:
     m.key(ord('`'));m.key(ord('/'))
     for value in b'Toggle Lines':m.key(value)
     m.key(13);m.key(27);m.key(13)
    else:m.key(0x0c1f)
    m.verify(rows);assert m.meta()==(2,1,0,0) and not m.get('_command_menu_active') and not m.get('_redisplay_active') and not m.tx
    ordinary(m,b'\x1bc\x1b[18t\x1b[99;80H\x1b[6n');m.drain();assert bytes(m.tx)==b'\x1b'+f'[8;{rows-1};80t'.encode()+b'\x1b'+f'[{rows-1};80R'.encode();n+=1
 done('reference-and-browser-release-full-frame-before-cycle-and-RIS-parser-queries',n)
 n=0
 for hidden in (0,1):
  m=fresh(50,0,hidden);saved=bytes(m.uc.mem_read(m.symbols['_terminal_display_preferences'],8));m.key(0x1b1d);m.key(0x0c1f);m.verify(50,1-hidden)
  assert bytes(m.uc.mem_read(m.symbols['_terminal_display_preferences'],8))==saved
  m.key(0x1b1d);m.key(0x0c1f);m.verify(25,hidden);assert not m.tx;n+=1
 done('line-cycles-preserve-live-status-choice-without-reapplying-saved-hidden-word',n)
 n=0
 for mode in (0x8000,0xffff,0x12):
  m=fresh(43,mode)
  for selector,physical,result in [(2,43,0),(1,25,3 if mode==0x12 else 0),(2,43,0)]:
   m.key(0x0c1f);m.verify(physical);assert m.meta()==(selector,1,int(selector==1),result) and not m.tx;n+=1
 done('nonzero-mode-cycle-uses-accepted-fallback-selector-for-next-key',n)
 n=0
 for field in ('terminal_parser_active','terminal_macro_active','terminal_program_pending','terminal_transfer_active','terminal_aspect_active','terminal_ansi_wait_active','uart_break_hold'):
  m=fresh();m.put(field,1);before=m.all();entry(m,0x0c1f);assert m.get('terminal_deferred_count')==1 and m.get('terminal_local_control_status')==1 and m.all()==before
  m.put(field,0);m.call('terminal_poll_io',limit=2000000);m.verify(50);assert m.meta()==(2,1,0,0) and not m.get('terminal_deferred_count') and not m.tx;n+=1
 done('exclusive-owner-deferral-preserves-key-and-cycles-once-after-release',n)
 n=0
 for field,value in [('connection_state',6),('ui_flow_video_base',0xffff),('reset_ready',0)]:
  m=fresh();m.put(field,value);before=m.all();entry(m,0x0c1f);assert m.get('terminal_local_control_status')==(2 if field=='reset_ready' else 3) and m.all()==before and not m.tx;n+=1
 m=Transaction();before=m.all();m.key(0x0c1f);assert m.get('terminal_local_control_status')==7 and m.all()==before and not m.tx;n+=1
 m=fresh();m.put('_terminal_display_selector',65535);before=m.all();m.key(0x0c1f);assert m.get('terminal_local_control_status')==1 and m.all()==before and not m.tx;n+=1
 done('tracked-online-invalid-geometry-baseline-selector-and-missing-preferences-refuse',n)
 for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 sources=['standalone/check_line_control_live.py','standalone/check_display_transaction_live.py','standalone/check_row_geometry_live.py']
 r=dict(passed=True,terminal_sha256=sha(binary),manifest_sha256=sha(binary.parent/'manifest.json'),inputs=sum(c['inputs'] for c in cases),cases=cases,sources={n:sha(ROOT/n) for n in sources},scope=__doc__+' Actual keyboard/reference/browser/local owner/selector/RIS paths. Source data and BIOS effects declared; not actual DOS/BBS/physical acceptance.')
 (out/'result.json').write_text(json.dumps(r,indent=2)+'\n')
if __name__=='__main__':main()
