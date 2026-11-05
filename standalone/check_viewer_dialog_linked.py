#!/usr/bin/env python3
"""Execute terminal viewer editor and borrowed-frame lifecycle with modeled DOS errors."""
import argparse,json,struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
from check_directory_identity import Identity,ROOT,sha
from check_viewer_file_linked import Owner

class Dialog(Identity):
 def __init__(self,binary,fault='',rows=25):
  super().__init__(binary);self.fault=fault;self.calls=[];self.position=0;self.opened=False
  self.ready=1
  self.returns={self.symbols[n]:v for n,v in [('_recording_ui_ready',1),('_path_session_quarantined',0),('_recording_terminal_inspect',0),('_capture_file_child_handle',0xffff),('_printer_device_child_handle',0xffff)]}
  self.uc.hook_add(UC_HOOK_CODE,self.boundary)
  self.put('csi_column_count',80);self.put('ui_window_rows',rows)
  self.state=self.symbols['_terminal_viewer_dialog_state'];self.rows=rows
  # A real near control-word address is the token; do not require startup to
  # have changed redisplay_active from its initialized zero value.
  seg,off=self.entries['redisplay_snapshot'];self.loan=[off,seg]
  assert self.bank('_viewer_dialog_bind',self.loan,far=True)==0
  self.near_size=self.offset('terminal_stack_top')-self.stack_bytes
 def boundary(self,u,address,size,data):
  if address not in self.returns:return
  value=self.ready if address==self.symbols['_recording_ui_ready'] else self.returns[address]
  sp=u.reg_read(UC_X86_REG_SP);ss=u.reg_read(UC_X86_REG_SS);ip,cs=struct.unpack('<HH',u.mem_read(ss*16+sp,4))
  u.reg_write(UC_X86_REG_AX,value);u.reg_write(UC_X86_REG_SP,sp+4);u.reg_write(UC_X86_REG_CS,cs);u.reg_write(UC_X86_REG_IP,ip)
 def interrupt(self,u,number,data):return Owner.interrupt(self,u,number,data)
 def carry(self,error):return Owner.carry(self,error)
 def event(self,event,key=0):return self.bank('_viewer_dialog_event',[event,key,0,0xb800],far=True)
 def head(self):return struct.unpack('<10H',self.uc.mem_read(self.state,20))
 def open(self):
  assert self.event(0)==1
  for c in b'data.bin':assert self.event(1,c)==1
  assert self.event(1,13)==1
 def load(self):
  for _ in range(200):
   if self.head()[2] not in [2,5]:return
   before=len(self.calls);self.event(3);assert len(self.calls)-before<=1
  raise AssertionError('unbounded viewer')

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ['terminal','output']:p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();binary=a.terminal.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 manifest=json.loads(binary.with_name('manifest.json').read_text());assert manifest['experimental_file_viewer'] and sha(binary)==manifest['binary_sha256']
 m=Identity(binary);state=m.symbols['_terminal_viewer_dialog_state'];field=bytes(range(33,76));edits=0
 near_size=m.offset('terminal_stack_top')-m.stack_bytes;near=bytes(m.uc.mem_read(m.data_base,near_size))
 for position,full in [(i,0) for i in range(43)]+[(42,1)]:
  for insert in [0,1]:
   for key in [0x0e08,0x5300,0x4b00,0x4d00,0x4700,0x4f00,0x7500,0x5200,ord('Z')]:
    data=struct.pack('<10H',0x5644,1,1,position,insert,full,0,1,25,0)+field+b'\0'+bytes(4)
    m.uc.mem_write(state,data);want=field;cur=position;latch=full;ins=insert
    if key==0x0e08:
     latch=0
     if cur:cur-=1;want=field[:cur]+field[cur+1:]+b' '
    elif key==0x5300:latch=0;want=field[:cur]+field[cur+1:]+b' '
    elif key==0x4b00:latch=0;cur=max(0,cur-1)
    elif key==0x4d00:cur=min(42,cur+1)
    elif key==0x4700:latch=0;cur=0
    elif key==0x4f00:latch=0;cur=42
    elif key==0x7500:latch=0;want=field[:cur]+b' '*(43-cur)
    elif key==0x5200:ins=1-insert
    elif not full:
     want=field[:cur]+b'Z'+field[cur:42] if insert else field[:cur]+b'Z'+field[cur+1:]
     if cur==42:latch=1
     else:cur+=1
    assert m.bank('_viewer_dialog_event',[1,key,0,0xb800],far=True)==1
    actual=bytes(m.uc.mem_read(state,68));head=struct.unpack_from('<10H',actual)
    assert head[:6]==(0x5644,1,1,cur,ins,latch) and actual[20:63]==want,(position,full,insert,key,head)
    assert m.bank('_viewer_dialog_cursor',far=True)==0x0c00+30+cur
    assert bytes(m.uc.mem_read(m.data_base,near_size))==near
    edits+=1
 cases=[]
 for rows in [25,28,43,50]:
  d=Dialog(binary,rows=rows);d.open();d.load();assert d.head()[2]==3
  frame=bytes(d.uc.mem_read(0xb8000,rows*160));assert frame[-160:-148:2]==b' Home:' and set(frame[-159::2])=={0x71}
  assert d.bank('_viewer_dialog_pending',far=True)==0 and d.bank('_viewer_dialog_fullscreen',far=True)==1
  assert d.event(1,27)==0 and d.bank('_viewer_dialog_owned',far=True)==0 and d.calls.count('close')==1
  cases.append(dict(case='geometry',rows=rows,passed=True))
 for fault in ['read-error','seek-error','close-error','read-close-error','release-error']:
  d=Dialog(binary,fault);d.open()
  if fault=='seek-error':
   d.load();assert d.event(1,0x4700)==1;d.load()
  elif fault in ['read-error','read-close-error']:d.load()
  elif fault=='release-error':d.uc.mem_write(d.symbols['_capture_reservation']+6,b'\1\0');d.event(1,27)
  else:d.event(1,27)
  uncertain=fault in ['close-error','read-close-error','release-error']
  if uncertain:
   assert d.bank('_viewer_dialog_unsafe',far=True)==1 and d.bank('_viewer_dialog_owned',far=True)==1
   assert d.get('terminal_quit')==1 and d.get('terminal_exit_code')==20
   calls=d.calls[:];assert d.bank('_viewer_dialog_shutdown',far=True)==1 and d.calls==calls
  else:
   assert d.head()[2]==4 and d.calls.count('close')==1
   assert d.event(1,32)==1 and d.head()[2]==1 and d.event(1,27)==0
   assert not d.get('terminal_quit') and d.bank('_viewer_dialog_owned',far=True)==0
  cases.append(dict(case=fault,quarantined=uncertain,DOS_calls=d.calls,passed=True))
 d=Dialog(binary);d.ready=0;d.event(0);assert d.head()[2]==6 and not d.calls and d.event(1,27)==0
 cases.append(dict(case='readiness-refused',passed=True))
 names=['standalone/check_viewer_dialog_linked.py','standalone/check_viewer_file_linked.py','standalone/check_directory_identity.py','standalone/dos_image.py']
 result=dict(passed=True,binary_sha256=sha(binary),editor_cases=edits,cases=cases,sources={n:sha(ROOT/n) for n in names},original_inputs=[],
  scope=__doc__+' Actual banked frontend/session/decoder/owner/claim/kernel with modeled DOS and readiness boundaries.792editor cases preserve all non-stack DGROUP, cursor and bytes; four full-height geometries, cleanup/read/seek/close/release faults, quarantine/quit and no repeated close. No physical/BIOS geometry or live BBS pressure acceptance.')
 out.mkdir(parents=True);(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS',edits,'editor cases and',len(cases),'frontend lifecycle cases')
if __name__=='__main__':main()
