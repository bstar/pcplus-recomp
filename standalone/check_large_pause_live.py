#!/usr/bin/env python3
"""Linked Screen Pause row leases and carrier-aware flow; BIOS/UART/DOS modeled.
Actual foreground, parser, row, notice and control instructions execute.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
import check_transport as transport
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 binary=a.terminal.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 manifest=json.loads((binary.parent/'manifest.json').read_text());assert sha(binary)==manifest['binary_sha256']
 for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 transport.BINARY=binary;transport.MAP=binary.parent/'terminal.map'
 from program_display_model import Program
 class Pause(Program):
  def enter(self,flags=0x202):
   u=self.uc;seg,_=self.entries['terminal_local_control_key'];sp=self.offset('terminal_stack_top')-4
   kept={UC_X86_REG_AX:0x3100,UC_X86_REG_BX:0x2345,UC_X86_REG_CX:0x3456,UC_X86_REG_DX:0x4567,UC_X86_REG_SI:0x5678,UC_X86_REG_DI:0x6789,UC_X86_REG_BP:0xbabe,UC_X86_REG_ES:0x1357}
   u.mem_write(self.data_base+sp,struct.pack('<2H',self.return_offset,self.code_segment));u.mem_write(self.data_base+sp-1800,b'GUARD!')
   for r,v in {**kept,UC_X86_REG_CS:self.base_segment+seg,UC_X86_REG_DS:self.ds,UC_X86_REG_SS:self.ds,UC_X86_REG_SP:sp,UC_X86_REG_EFLAGS:flags}.items():u.reg_write(r,v)
   self.returned=False;u.emu_start(self.symbols['terminal_local_control_key'],0,count=2000000)
   assert self.returned and u.reg_read(UC_X86_REG_SP)==sp+4
   for r,v in kept.items():assert u.reg_read(r)==v,r
   assert u.reg_read(UC_X86_REG_DS)==u.reg_read(UC_X86_REG_SS)==self.ds and u.reg_read(UC_X86_REG_EFLAGS)&0x600==flags&0x600
   assert bytes(u.mem_read(self.data_base+sp-1800,6))==b'GUARD!'
 def fresh(rows,profile=6,hidden=0):
  m=Pause();m.put('csi_terminal_id',profile);m.setup(rows,hidden);m.tx.clear();return m
 cases=[]
 def done(name,n):cases.append(dict(case=name,inputs=n,passed=True));print(name,n,'PASS',flush=True)
 n=0
 for rows in (25,28,43,50):
  for profile in (4,6):
   for key,pressure in [(ord('x'),'none'),(27,'THRE'),(0x2d00,'CTS'),(0x4800,'peer-XOFF')]:
    m=fresh(rows,profile);before=m.full();m.shape=0x260f if key==0x4800 else 0x607;shape=m.shape;polls=[]
    if pressure=='THRE':m.thre=False
    if pressure=='CTS':m.cts=False;m.put('uart_hardware_flow',1)
    if pressure=='peer-XOFF':m.put('uart_tx_paused',1)
    def watch(u,at,size,d):
     if at!=m.symbols['terminal_pause_poll_far']:return
     polls.append(at);video=bytes(u.mem_read(0xb8000,8000));base=(rows-1)*160
     assert video[:base]==before['video'][:base] and video[base+160:]==before['video'][base+160:]
     assert b'Screen paused.' in video[base:base+160:2] and m.shape==shape|0x2000
     if len(polls)==4:m.keys.append(key)
    hook=m.uc.hook_add(UC_HOOK_CODE,watch);m.enter();m.uc.hook_del(hook)
    after=m.full()
    for part in ('words','bytes','defaults','planes','ui','video'):assert before[part]==after[part],(rows,profile,pressure,part)
    assert len(polls)==4 and not m.keys and m.shape==shape and m.cursor==before['hardware'][4]
    assert not m.get('terminal_screen_pause_active') and not m.get('terminal_quit') and not m.get('terminal_local_control_status')
    assert bytes(m.tx)==(b'' if pressure=='THRE' else b'\x13\x11')
    if pressure=='THRE':
     assert m.get('uart_flow_pending',1)==17;m.thre=True;m.call('terminal_poll_serial');assert bytes(m.tx)==b'\x11'
    n+=1
 done('all-heights-profiles-resume-keys-pressure-full-planes-history-stack-ABI',n)
 n=0
 for rows in (25,28,43,50):
  for name,value in [('ui_flow_suppressed',1),('ui_flow_region_cells',79),('ui_flow_video_base',0xffff),('ui_flow_coordinate_base',0),('csi_row_count',0),('csi_last_row',0xffff),('csi_column_count',132),('screen_attribute_row_bytes',132),('screen_viewport_enabled',1)]:
   m=fresh(rows);m.put(name,value);before=m.full();m.enter();assert m.full()['video']==before['video'] and not m.tx
   assert m.get('terminal_local_control_status')==3 and not m.get('terminal_screen_pause_active');n+=1
  for kind in ('height','mode','page','columns','IF0','DF1'):
   m=fresh(rows)
   if kind=='height':m.uc.mem_write(0x484,b'\x19')
   if kind=='mode':m.mode=7
   if kind=='page':m.page=1
   if kind=='columns':m.columns=40
   before=m.full();m.enter(0x2 if kind=='IF0' else 0x602 if kind=='DF1' else 0x202)
   assert m.full()['video']==before['video'] and not m.tx and m.get('terminal_local_control_status')==3;n+=1
  m=fresh(rows,hidden=1);before=m.full();m.enter();assert m.full()['video']==before['video'] and not m.tx and m.get('terminal_local_control_status')==3;n+=1
 done('hidden-inconsistent-canonical-BIOS-flags-refused-before-control-or-video',n)
 n=0
 for old,new in ((25,28),(28,43),(43,50),(50,25)):
  for kind in ('offset','BIOS','coherent-new-height'):
   m=fresh(old);polls=[];last=[]
   def mutate(u,at,size,d):
    if at!=m.symbols['terminal_pause_poll_far']:return
    polls.append(at)
    if kind=='offset':m.put('ui_flow_video_base',0xffff)
    elif kind=='BIOS':u.mem_write(0x484,b'\x19')
    else:
     m.vrows=new;u.mem_write(0x484,bytes([new-1]))
     for name,value in {'ui_window_rows':new,'ui_flow_video_base':(new-1)*160,'ui_flow_coordinate_base':(new-1)*256,'csi_row_count':new-1,'csi_last_row':new-2}.items():m.put(name,value)
    u.mem_write(0xb8000,b'Z\x17'*4000);m.shape=0x1234;last.append(bytes(u.mem_read(0xb8000,8000)));m.keys.append(27)
   hook=m.uc.hook_add(UC_HOOK_CODE,mutate);m.enter();m.uc.hook_del(hook)
   assert len(polls)==1 and bytes(m.uc.mem_read(0xb8000,8000))==last[0] and m.shape==0x1234
   assert m.get('terminal_quit')==1 and m.get('terminal_exit_code')==7 and m.get('terminal_local_control_status')==3
   assert not m.get('terminal_screen_pause_active') and bytes(m.tx)==b'\x13';n+=1
 done('stale-and-coherently-different-leases-release-without-video-or-shape-replay',n)
 n=0
 for rows in (25,28,43,50):
  for transient in (False,True):
   m=fresh(rows);m.advance_ticks=False;m.put('connection_enabled',1,1);m.put('connection_carrier_seen',1,1);m.put('connection_state',6);m.put('connection_status',1);m.carrier=True;m.tick=100;polls=[];before=m.full()['video']
   def drop(u,at,size,d):
    if at!=m.symbols['terminal_pause_poll_far']:return
    polls.append(at);m.carrier=False;m.tick+=1
    if len(polls)==(2 if transient else 12):m.keys.append(ord('x'))
   hook=m.uc.hook_add(UC_HOOK_CODE,drop);m.enter();m.uc.hook_del(hook)
   assert bytes(m.tx)==b'\x13' and not m.get('terminal_screen_pause_active')
   if transient:
    assert m.get('connection_state')==6 and m.get('uart_flow_pending',1)==17
    m.carrier=True;m.call('terminal_poll_serial');assert bytes(m.tx)==b'\x13\x11' and m.get('uart_flow_pending',1)==0
   else:
    assert m.get('connection_state')==0 and m.get('connection_status')==6 and m.get('uart_flow_pending',1)==0
    m.call('terminal_connection_notice_restore');assert bytes(m.uc.mem_read(0xb8000,8000))==before
   n+=1
 done('carrier-grace-retains-resume-sustained-loss-retires-without-command-output',n)
 m=fresh(25);m.uc.mem_write(0x484,b'\0');m.keys.append(ord('x'));m.enter();assert not m.get('terminal_local_control_status');done('legacy-BDA-height-zero-means25',1)
 for name,h in manifest['sources'].items():assert sha(ROOT/name)==h,name
 report=dict(passed=True,terminal_sha256=sha(binary),manifest_sha256=sha(binary.parent/'manifest.json'),cases=cases,inputs=sum(c['inputs'] for c in cases),sources={n:sha(ROOT/n) for n in ['standalone/check_large_pause_live.py','standalone/program_display_model.py','standalone/check_row_geometry_live.py']},scope=__doc__+' Modeled carrier timing and display faults; no physical/SIP/BBS acceptance.')
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
