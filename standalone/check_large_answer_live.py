#!/usr/bin/env python3
"""Linked accepted-row Auto Answer, command/notice/tone ownership and admission.
Actual product instructions execute; DOS/BIOS/UART/PIT and fault timings modeled.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn.x86_const import *
from check_call_timer_live import configure,ROOT
from check_auto_answer_live import Answer
from check_row_geometry_live import Geometry
from program_display_model import Program
from check_manual_init_dispatch_live import ordinary
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
class Large(Geometry,Answer):
 setup=Program.setup
 def admit(self,flags=0x202,ss_delta=0):
  seg,_=self.entries['terminal_auto_answer_admit_far'];u=self.uc;ss=self.ds+ss_delta;sp=self.offset('terminal_stack_top')-4
  kept={UC_X86_REG_BX:0x2345,UC_X86_REG_CX:0x3456,UC_X86_REG_DX:0x4567,UC_X86_REG_SI:0x5678,UC_X86_REG_DI:0x6789,UC_X86_REG_BP:0xbabe,UC_X86_REG_ES:0x1357}
  for r,v in {**kept,UC_X86_REG_CS:self.base_segment+seg,UC_X86_REG_DS:self.ds,UC_X86_REG_SS:ss,UC_X86_REG_SP:sp,UC_X86_REG_EFLAGS:flags}.items():u.reg_write(r,v)
  u.mem_write(ss*16+sp,struct.pack('<2H',self.return_offset,self.code_segment));u.mem_write(ss*16+sp-200,b'GUARD!');self.returned=False
  u.emu_start(self.symbols['terminal_auto_answer_admit_far'],0,count=100000)
  assert self.returned and u.reg_read(UC_X86_REG_SP)==sp+4 and u.reg_read(UC_X86_REG_DS)==self.ds and u.reg_read(UC_X86_REG_SS)==ss
  for r,v in kept.items():assert u.reg_read(r)==v,r
  assert u.reg_read(UC_X86_REG_EFLAGS)&0x600==flags&0x600 and bytes(u.mem_read(ss*16+sp-200,6))==b'GUARD!'
  return u.reg_read(UC_X86_REG_AX)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 binary=a.terminal.resolve();configure(binary);out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 manifest=json.loads((binary.parent/'manifest.json').read_text());assert sha(binary)==manifest['binary_sha256']
 for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 def fresh(rows,profile=6,enabled=0):
  m=Large();m.put('csi_terminal_id',profile);m.setup(rows);m.put('_terminal_sound_enabled',enabled);m.tx.clear();return m
 cases=[]
 def done(name,n):cases.append(dict(case=name,inputs=n,passed=True));print(name,n,'PASS',flush=True)
 n=0
 for rows in (25,28,43,50):
  for profile in (4,6):
   for enabled in (0,1):
    m=fresh(rows,profile,enabled);before=m.full();assert m.admit()==0;m.key(0x1500)
    assert m.active() and m.notice() and b'AUTO ANSWER...' in bytes(m.uc.mem_read(0xb8000+(rows-1)*160,160))[::2]
    assert bytes(m.uc.mem_read(0xb8000,(rows-1)*160))==before['video'][:(rows-1)*160] and not m.tx
    m.finish();assert bytes(m.tx)==b'ATS0=1\r' and not m.notice() and not m.active() and not m.get('_speaker_owned')
    after=m.full()
    for part in ('words','bytes','defaults','planes','ui'):assert before[part]==after[part],(rows,profile,enabled,part)
    assert after['video'][:(rows-1)*160]==before['video'][:(rows-1)*160]
    assert b'AUTO ANSWER...' not in after['video'][::2] and bool(m.sounds)==bool(enabled);n+=1
 done('all-heights-profiles-quiet-sound-command-and-full-body-history-ownership',n)
 n=0
 for rows in (25,28,43,50):
  for browser in (False,True):
   m=fresh(rows);before=m.full()['video'][:(rows-1)*160]
   if browser:
    m.key(ord('`'));m.key(ord('/'))
    for value in b'Auto Answer':m.key(value)
    m.key(13);m.key(27);m.key(13)
   else:m.key(0x2c00);m.key(0x1500)
   assert m.active() and m.notice() and not m.get('_command_menu_active') and bytes(m.uc.mem_read(0xb8000,(rows-1)*160))==before
   m.finish();assert bytes(m.tx)==b'ATS0=1\r';n+=1
 done('reference-and-browser-restore-all-physical-body-rows-before-notice',n)
 n=0
 for rows in (25,28,43,50):
  m=fresh(rows);m.connect(b'CONNECT\r\n');m.tx.clear();m.put('screen_first_row',2);m.put('screen_last_row',rows-3)
  assert m.admit()==0;m.key(0x1500);m.key(ord('x'));ordinary(m,b'\x1b'+f'[{rows-1};1HLATEST'.encode()+b'\x1b[6n')
  m.finish();m.drain();assert bytes(m.tx)==b'ATS0=1\r'+b'\x1b'+f'[{rows-1};7R'.encode()+b'x'
  assert b'LATEST' in bytes(m.uc.mem_read(0xb8000,(rows-1)*160))[::2] and not m.notice();n+=1
 done('custom-scroll-bounds-normal-lower-RX-CPR-and-typeahead',n)
 n=0
 for rows in (25,28,43,50):
  for key,reason in ((27,3),(0x2300,3),(0x2d00,8)):
   m=fresh(rows,enabled=1);m.connect(b'CONNECT\r\n');m.tx.clear();before=m.full()['video'][:(rows-1)*160];m.key(0x1500);m.key(key)
   assert not m.active() and not m.notice() and m.get('terminal_manual_init_status')==reason and m.speaker==0xa0
   assert bytes(m.tx)==b'A' and bytes(m.uc.mem_read(0xb8000,(rows-1)*160))==before;n+=1
  m=fresh(rows,enabled=1);m.connect(b'CONNECT\r\n');m.tx.clear();m.key(0x1500);m.poll();m.thre=False;m.carrier=False;m.poll(8)
  assert m.state()==0 and not m.active() and not m.notice() and m.get('terminal_manual_init_status')==7 and m.speaker==0xa0
  assert b'Carrier lost' in bytes(m.uc.mem_read(0xb8000+(rows-1)*160,160))[::2]
  m.carrier=True;m.thre=True;m.tx.clear();m.connect(b'CONNECT\r\n');assert bytes(m.tx)==b'\rATZ\rATDLocal.Example:2323\r';n+=1
 done('cancel-hangup-exit-and-qualified-carrier-loss-redial-at-each-height',n)
 n=0
 fields=[('ui_flow_suppressed',1),('ui_flow_video_base',0xffff),('ui_flow_coordinate_base',0),('ui_flow_region_cells',79),('csi_row_count',0),('csi_last_row',0xffff),('csi_column_count',132),('screen_attribute_row_bytes',132),('screen_viewport_enabled',1),('screen_last_row',50),('screen_first_row',50)]
 for rows in (25,28,43,50):
  for name,value in fields:
   m=fresh(rows,enabled=1);m.put(name,value);before=m.full();assert m.admit()==1;m.key(0x1500)
   assert not m.tx and not m.sounds and not m.active() and not m.notice() and m.full()['video']==before['video'];n+=1
  for kind in ('mode','columns','page','height'):
   m=fresh(rows,enabled=1)
   if kind=='height':m.uc.mem_write(0x484,b'\x19')
   else:setattr(m,kind,7 if kind=='mode' else 40 if kind=='columns' else 1)
   before=m.full()['video'];assert m.admit()==1;m.key(0x1500);assert not m.tx and not m.sounds and not m.active() and not m.notice() and m.full()['video']==before;n+=1
  for flags,delta in ((0x2,0),(0x602,0),(0x202,1)):
   m=fresh(rows,enabled=1);before=m.full();assert m.admit(flags,delta)==1 and m.full()==before;n+=1
 done('canonical-BIOS-ABI-flag-and-reserved-row-refusals-have-no-effects',n)
 m=fresh(25);m.uc.mem_write(0x484,b'\0');assert m.admit()==0;done('legacy-BDA-zero-height-admitted-as25',1)
 for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 sources=['standalone/check_large_answer_live.py','standalone/check_auto_answer_live.py','standalone/check_call_timer_live.py','standalone/check_row_geometry_live.py','standalone/program_display_model.py']
 report=dict(passed=True,terminal_sha256=sha(binary),manifest_sha256=sha(binary.parent/'manifest.json'),inputs=sum(c['inputs'] for c in cases),cases=cases,sources={n:sha(ROOT/n) for n in sources},scope=__doc__+' Model-only fault/tone/ABI timing. Not physical/SIP/BBS acceptance.')
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
