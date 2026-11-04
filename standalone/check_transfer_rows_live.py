#!/usr/bin/env python3
"""Linked transfer UI row leases, complete video and canonical-state retention.
BIOS/UART/DOS boundaries use the shared declared model; product routines execute.
"""
import argparse,hashlib,json
from pathlib import Path
from unicorn.x86_const import *
import check_transport as transport
from program_display_model import Program
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def call(m,name,flags=0x202):
 kept={UC_X86_REG_BX:0x9876,UC_X86_REG_SI:0x1234,UC_X86_REG_DI:0x5678,UC_X86_REG_ES:0x1357}
 for r,v in kept.items():m.uc.reg_write(r,v)
 result=m.far_entry('terminal_transfer_ui_'+name+'_impl',flags)
 for r,v in kept.items():assert m.uc.reg_read(r)==v,(name,r)
 return result
def ready(rows,hidden=0):
 m=Program();m.setup(rows,hidden);m.put('terminal_transfer_active',1)
 # Declared leaf-call fixture: the private phase word follows the exported
 # protocol word in transfer_actions.asm. The real owner sets phase1 before UI.
 m.uc.mem_write(m.symbols['terminal_transfer_protocol']+2,b'\x01\x00');return m
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 binary=a.terminal.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 manifest=json.loads((binary.parent/'manifest.json').read_text());assert manifest['experimental_row_geometry_owner'] and sha(binary)==manifest['binary_sha256']
 for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 transport.BINARY=binary;transport.MAP=binary.parent/'terminal.map';cases=[]
 for rows in [25,28,43,50]:
  for hidden in [0,1]:
   for profile in [4,6]:
    for protocol in [0,1,2]:
     for direction in [0,1]:
      for automatic in [0,1]:
       m=ready(rows,hidden)
       for name,value in [('csi_terminal_id',profile),('terminal_transfer_protocol',protocol),('terminal_transfer_direction',direction),('terminal_transfer_automatic',automatic)]:m.put(name,value)
       if not automatic:m.keys.extend([ord(c) for c in 'TEST.BIN']+[0x1c0d])
       before=m.full();cursor,shape=m.cursor,m.shape;base=(rows-2)*160
       assert call(m,'open')==1 and m.get('_terminal_transfer_ui_visible',1)==1
       video=bytes(m.uc.mem_read(0xb8000,8000));assert video[:base]==before['video'][:base] and video[base+320:]==before['video'][base+320:]
       assert video[base+1:base+320:2]==bytes([31])*160
       assert ('ZMODEM' if protocol==2 else 'YMODEM' if protocol else 'XMODEM').encode() in video[base:base+160:2]
       if not automatic:assert video[base+160:base+176:2]==b'TEST.BIN' and m.cursor>>8==rows-1
       for name in ['words','bytes','defaults','planes','ui']:assert m.full()[name]==before[name],name
       call(m,'receiving');m.put('session_blocks_accepted',12345);m.put('terminal_upload_blocks_accepted',12345)
       # YMODEM's fixed C word block counter is at +6.
       m.uc.mem_write(m.symbols['_ymodem_current']+6,(12345).to_bytes(2,'little'));m.put('_terminal_zmodem_kbytes',12345)
       call(m,'progress');video=bytes(m.uc.mem_read(0xb8000,8000));assert video[base+132:base+142:2]==b'12345'
       assert video[:base]==before['video'][:base] and video[base+320:]==before['video'][base+320:]
       call(m,'restore');assert m.get('_terminal_transfer_ui_visible',1)==0
       assert bytes(m.uc.mem_read(0xb8000,8000))==before['video'] and (m.cursor,m.shape)==(cursor,shape)
       assert not m.get('terminal_quit') and not m.get('terminal_transfer_fault')
       cases.append(dict(kind='complete-acquire-progress-restore',rows=rows,hidden=hidden,profile=profile,protocol=protocol,direction=direction,automatic=automatic,passed=True))
  for hidden in [0,1]:
   m=ready(rows,hidden);before=m.full();m.keys.extend([0x3c00,ord('X'),0x011b]);assert call(m,'open')==0
   assert m.get('terminal_transfer_fault')==2 and m.get('terminal_transfer_protocol')==1
   call(m,'restore');assert bytes(m.uc.mem_read(0xb8000,8000))==before['video']
   cases.append(dict(kind='F2-Escape-restores',rows=rows,hidden=hidden,passed=True))
  m=ready(rows);m.put('terminal_transfer_automatic',1);before=m.full();assert call(m,'open')==1
  open_video=bytes(m.uc.mem_read(0xb8000,8000));assert call(m,'open')==0 and m.get('terminal_transfer_fault')==8
  assert bytes(m.uc.mem_read(0xb8000,8000))==open_video
  call(m,'restore');assert bytes(m.uc.mem_read(0xb8000,8000))==before['video']
  cases.append(dict(kind='double-acquire-keeps-first-lease',rows=rows,passed=True))
 for rows in [25,28,43,50]:
  faults=[('mode',13),('columns',40),('page',1),('BDA',24 if rows!=25 else 27),('ui_window_rows',26),('csi_column_count',132),('screen_attribute_row_bytes',132),('screen_video_row_bytes',158),('flags',0x602),('flags',2)]
  for name,value in faults:
   m=ready(rows);m.put('terminal_transfer_automatic',1)
   if name in ('mode','columns','page'):setattr(m,name,value)
   elif name=='BDA':m.uc.mem_write(0x484,bytes([value]))
   elif name!='flags':m.put(name,value)
   before=bytes(m.uc.mem_read(0xb8000,8000));assert call(m,'open',value if name=='flags' else 0x202)==0
   assert m.get('terminal_transfer_fault')==8 and m.get('_terminal_transfer_ui_visible',1)==0
   assert bytes(m.uc.mem_read(0xb8000,8000))==before
   cases.append(dict(kind='refused-before-video',rows=rows,fault=name,value=value,passed=True))
  for prior in [0,4]:
   m=ready(rows);m.put('terminal_transfer_automatic',1);assert call(m,'open')==1
   m.put('terminal_transfer_fault',prior);m.uc.mem_write(0x484,bytes([24 if rows!=25 else 27]));foreign=b'!\x4f'*4000;m.uc.mem_write(0xb8000,foreign)
   call(m,'restore');assert bytes(m.uc.mem_read(0xb8000,8000))==foreign
   assert m.get('terminal_quit')==1 and m.get('terminal_exit_code')==7 and m.get('terminal_transfer_fault')==(prior or 8) and m.get('_terminal_transfer_ui_visible',1)==0
   cases.append(dict(kind='stale-restore-refuses-and-requests-shutdown',rows=rows,prior_fault=prior,passed=True))
  m=ready(rows);m.put('terminal_transfer_automatic',1);assert call(m,'open')==1
  # Model a foreign owner violating the transfer lease, using the real row
  # transaction to establish a fully coherent different height. This reaches
  # the captured-base check, beyond simple malformed-BDA admission refusal.
  m.put('terminal_transfer_active',0);assert m.set_rows(50 if rows==25 else 25)==0;m.put('terminal_transfer_active',1)
  foreign=b'?\x2e'*4000;m.uc.mem_write(0xb8000,foreign);call(m,'restore')
  assert bytes(m.uc.mem_read(0xb8000,8000))==foreign and m.get('terminal_quit')==1 and m.get('terminal_exit_code')==7
  cases.append(dict(kind='coherent-foreign-height-cannot-replay-old-lease',rows=rows,passed=True))
 m=ready(25);m.put('terminal_transfer_automatic',1);m.uc.mem_write(0x484,b'\0');before=m.full();assert call(m,'open')==1;call(m,'restore');assert bytes(m.uc.mem_read(0xb8000,8000))==before['video']
 cases.append(dict(kind='legacy-unreported-BDA-height25',passed=True))
 result=dict(passed=True,cases=cases,inputs=len(cases),terminal_sha256=sha(binary),manifest_sha256=sha(binary.parent/'manifest.json'),sources={n:sha(ROOT/n) for n in ['standalone/check_transfer_rows_live.py','standalone/program_display_model.py','standalone/check_row_geometry_live.py']},scope=__doc__+' Complete8000-byte video/canaries, row/status defaults and far planes/history are checked; no actual remote protocol or physical acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS transfer row leases',len(cases),'inputs')
if __name__=='__main__':main()
