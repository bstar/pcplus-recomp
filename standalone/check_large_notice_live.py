#!/usr/bin/env python3
"""Execute linked dynamic connection notices; BIOS/UART/DOS setup boundaries modeled.
Checks frame/lease/ABI behavior, not actual BBS/SIP or physical acceptance.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn.x86_const import *
import check_transport as transport
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 binary=a.terminal.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 manifest=json.loads((binary.parent/'manifest.json').read_text());assert sha(binary)==manifest['binary_sha256'] and manifest['experimental_row_notices']
 for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 transport.BINARY=binary;transport.MAP=binary.parent/'terminal.map'
 from program_display_model import Program
 class Notice(Program):
  def entry(self,name,si=0,far=False):
   u=self.uc;words=[self.return_offset,self.code_segment] if far else [self.return_offset];sp=self.offset('terminal_stack_top')-2*len(words)
   kept={UC_X86_REG_AX:0x1234,UC_X86_REG_BX:0x2345,UC_X86_REG_CX:0x3456,UC_X86_REG_DX:0x4567,UC_X86_REG_SI:si,UC_X86_REG_DI:0x6789,UC_X86_REG_BP:0xbabe,UC_X86_REG_ES:0x1357}
   for r,v in {**kept,UC_X86_REG_CS:self.code_segment,UC_X86_REG_DS:self.ds,UC_X86_REG_SS:self.ds,UC_X86_REG_SP:sp,UC_X86_REG_EFLAGS:0x202}.items():u.reg_write(r,v)
   u.mem_write(self.data_base+sp,struct.pack('<'+'H'*len(words),*words));self.returned=False;u.emu_start(self.symbols[name],0,count=1000000)
   assert self.returned and u.reg_read(UC_X86_REG_SP)==sp+2*len(words)
   assert u.reg_read(UC_X86_REG_DS)==u.reg_read(UC_X86_REG_SS)==self.ds and u.reg_read(UC_X86_REG_EFLAGS)&0x600==0x200
   if name!='terminal_pause_notice_flush_far':
    for r,v in kept.items():
     if r!=UC_X86_REG_AX or name!='terminal_status_notice_refresh':assert u.reg_read(r)==v,(name,r)
   return u.reg_read(UC_X86_REG_AX),u.reg_read(UC_X86_REG_EFLAGS)&1
  def show(self,text=b'Carrier lost'):
   ptr=self.offset('_command_menu_script');self.uc.mem_write(self.data_base+ptr,text+b'\0');self.entry('terminal_connection_notice',ptr)
  def frame(self,rows):return bytes(self.uc.mem_read(0xb8000,rows*160))
  def replace_geometry(self,rows):
   # Fault boundary: another owner missed notice retirement. Supply a coherent
   # new row tuple and newer frame directly; the real transaction would refuse.
   self.vrows=rows;self.uc.mem_write(0x484,bytes([rows-1]))
   for n,v in {'ui_window_rows':rows,'ui_flow_video_base':(rows-1)*160,'ui_flow_coordinate_base':(rows-1)*256,'csi_row_count':rows-1,'csi_last_row':rows-2}.items():self.put(n,v)
   self.uc.mem_write(0xb8000,b'Z\x07'*(rows*80))
 cases=[]
 def done(name,n):cases.append(dict(case=name,inputs=n,passed=True));print(name,n,'PASS',flush=True)
 n=0
 for rows in (25,28,43,50):
  for hidden in (0,1):
   m=Notice();m.setup(rows,hidden);before=m.frame(rows);state=m.full();m.show();shown=m.frame(rows)
   if hidden:assert shown==before
   else:assert shown[:(rows-1)*160]==before[:(rows-1)*160] and b'Carrier lost' in shown[(rows-1)*160::2]
   _,cf=m.entry('terminal_status_row_admit_far',far=True);assert cf==int(rows!=25 or hidden)
   m.show(b'Second notice');m.entry('terminal_connection_notice_restore');assert m.frame(rows)==before
   after=m.full()
   for key in ('words','bytes','defaults','planes','ui'):assert after[key]==state[key],(rows,hidden,key)
   assert not m.tx;n+=1
 done('all-heights-hidden-visible-notice-replacement-restore-ABI-and-fixed-shared-gate',n)
 n=0
 for rows in (25,28,43,50):
  m=Notice();m.setup(rows);logical=m.frame(rows)[:(rows-1)*160];m.show();notice=m.frame(rows)[(rows-1)*160:(rows-1)*160+30]
  assert m.entry('terminal_status_notice_refresh',far=True)[0]==0
  assert m.frame(rows)[:(rows-1)*160]==logical and m.frame(rows)[(rows-1)*160:(rows-1)*160+30]==notice
  m.entry('terminal_connection_notice_restore');assert b'Alt-Z FOR HELP' in m.frame(rows)[(rows-1)*160::2]
  for owner in ('terminal_screen_pause_active','_terminal_elapsed_view_active'):
   m=Notice();m.setup(rows);before=m.frame(rows);m.put(owner,1);m.show();assert m.frame(rows)==before
   m.put(owner,0);m.entry('terminal_pause_notice_flush_far',far=True);assert b'Carrier lost' in m.frame(rows)[(rows-1)*160::2]
   m.entry('terminal_connection_notice_restore');assert m.frame(rows)==before;n+=1
  n+=1
 done('active-status-repaint-retains-notice-and-deferred-modal-flush-uses-current-row',n)
 n=0
 for old,new in ((25,28),(28,43),(43,50),(50,25)):
  for action in ('restore','show','refresh'):
   m=Notice();m.setup(old);m.show();m.replace_geometry(new);fresh=m.frame(new)
   if action=='restore':m.entry('terminal_connection_notice_restore');assert m.frame(new)==fresh
   elif action=='show':m.show(b'New notice');m.entry('terminal_connection_notice_restore');assert m.frame(new)==fresh
   else:
    assert m.entry('terminal_status_notice_refresh',far=True)[0]==0
    assert m.frame(new)[:(new-1)*160]==fresh[:(new-1)*160]
    assert b'Carrier lost' not in m.frame(new)[(new-1)*160::2]
    fresh=m.frame(new);m.entry('terminal_connection_notice_restore');assert m.frame(new)==fresh
   n+=1
 done('missed-retirement-cannot-replay-an-old-row-lease-into-new-geometry',n)
 n=0
 for rows in (25,28,43,50):
  for name,value in [('ui_flow_suppressed',2),('ui_flow_video_base',0xffff),('ui_flow_coordinate_base',0),('ui_flow_region_cells',79),('screen_columns',40),('screen_video_row_bytes',80),('text_video_segment',0xb000),('ui_window_rows',26),('csi_row_count',0),('csi_last_row',0xffff)]:
   m=Notice();m.setup(rows);m.put(name,value);before=m.frame(rows);m.put('_redisplay_active',1);m.put('_command_menu_active',1);m.show()
   assert m.frame(rows)==before and m.get('_redisplay_active')==m.get('_command_menu_active')==1
   m.put('_redisplay_active',0);m.put('_command_menu_active',0);m.entry('terminal_connection_notice_restore');assert m.frame(rows)==before;n+=1
 done('incoherent-layout-refuses-before-viewer-close-or-video-write',n)
 for name,h in manifest['sources'].items():assert sha(ROOT/name)==h,name
 sources=['standalone/check_large_notice_live.py','standalone/program_display_model.py','standalone/check_row_geometry_live.py']
 report=dict(passed=True,terminal_sha256=sha(binary),manifest_sha256=sha(binary.parent/'manifest.json'),inputs=sum(c['inputs'] for c in cases),cases=cases,sources={n:sha(ROOT/n) for n in sources},scope=__doc__)
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
