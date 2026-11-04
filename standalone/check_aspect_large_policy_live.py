#!/usr/bin/env python3
"""Execute linked larger-row ASPECT admission/preflight over canonical row owners.
BIOS/UART/DOS setup boundaries modeled; no child execution or BBS acceptance.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_WRITE
from unicorn.x86_const import *
import check_transport as transport
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 binary=a.terminal.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 manifest=json.loads((binary.parent/'manifest.json').read_text());assert sha(binary)==manifest['binary_sha256'] and manifest['experimental_program_display_owner']
 for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 transport.BINARY=binary;transport.MAP=binary.parent/'terminal.map'
 from program_display_model import Program
 class Render(Program):
  def __init__(self):
   super().__init__();self.checking=False;self.outside=[];self.sentinel=None
   self.uc.hook_add(UC_HOOK_CODE,self.stop_policy);self.uc.hook_add(UC_HOOK_MEM_WRITE,self.write_policy)
  def stop_policy(self,u,address,size,d):
   if self.checking and address==self.sentinel:self.returned=True;u.emu_stop()
  def write_policy(self,u,access,address,size,value,d):
   if self.checking and not self.data_base+self.offset('terminal_stack_top')-3000<=address<=self.data_base+self.offset('terminal_stack_top')-size:self.outside.append((address,size,value))
  def policy(self,name='_aspect_render_admit',arguments=()):
   u=self.uc;seg,off=self.entries[name];cs=self.base_segment+seg
   extent=next(s for s in manifest['memory_layout']['code_segments'] if s['relative_segment']==seg)
   # Stop only in unused code space, without replacing any product instruction.
   assert extent['bytes']<0xfff0
   self.sentinel=cs*16+0xfff0;sp=self.offset('terminal_stack_top')-2*(1+len(arguments))
   u.mem_write(self.data_base+sp,struct.pack('<'+'H'*(1+len(arguments)),0xfff0,*arguments))
   for r,v in [(UC_X86_REG_CS,cs),(UC_X86_REG_DS,self.ds),(UC_X86_REG_SS,self.ds),(UC_X86_REG_SP,sp),(UC_X86_REG_EFLAGS,0x202),(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678)]:u.reg_write(r,v)
   self.returned=False;self.checking=True
   try:u.emu_start(self.symbols[name],0,count=1000000)
   finally:self.checking=False
   assert self.returned and u.reg_read(UC_X86_REG_SP)==sp+2 and not self.outside,(name,self.outside)
   for r,v in [(UC_X86_REG_DS,self.ds),(UC_X86_REG_SS,self.ds),(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678)]:assert u.reg_read(r)==v,name
   return u.reg_read(UC_X86_REG_AX)
  def ready(self,rows,hidden):
   self.setup(rows,hidden);self.put('terminal_program_active',1);self.put('terminal_program_kind',4)
   return self
 cases=[]
 def done(name,count):cases.append(dict(case=name,inputs=count,passed=True));print(name,count,'PASS',flush=True)
 n=0
 enabled=manifest.get('experimental_aspect_row_owner',False)
 for rows in [25,28,43,50]:
  for hidden in [0,1]:
   for profile in [4,6]:
    for connection in [0,6]:
     m=Render().ready(rows,hidden);m.put('csi_terminal_id',profile);m.put('connection_state',connection)
     expected=0 if enabled or rows==25 else 3
     assert m.policy()==expected,(rows,hidden,profile,connection)
     for depth in [1,16]:
      m.put('terminal_aspect_active',1);m.put('terminal_parser_active',depth)
      for name,args in [('_aspect_render_preflight_control',[65]),('_aspect_render_preflight_command',[])]:assert m.policy(name,args)==expected,(rows,hidden,name)
      n+=2
     n+=1
 done('coherent-heights-status-states-profiles-offline-online-admit-and-scoped-preflight-depths',n)
 n=0
 if enabled:
  for rows in [28,43,50]:
   for name,value in [('ui_window_rows',25),('csi_row_count',24),('ui_flow_suppressed',2),('ui_flow_video_base',3840),('ui_flow_coordinate_base',0x1800),('ui_flow_region_cells',79),('screen_attribute_row_bytes',132),('erase_cell_count',4097),('csi_last_row',rows),('screen_cursor_row',rows),('screen_cursor_column',80),('screen_attribute_offset',4000),('screen_video_offset',8000)]:
    m=Render().ready(rows,0);m.put(name,value);assert m.policy()==3,(rows,name,value);n+=1
   for physical in [26,27,29,42,44,49,51,255]:
    m=Render().ready(rows,0);m.uc.mem_write(0x484,bytes([physical-1]));assert m.policy()==3,(rows,physical);n+=1
  done('incoherent-height-status-stride-cell-capacity-offset-and-BIOS-refusals',n)
 if enabled:
  n=0
  for rows in [25,28,43,50]:
   for hidden in [0,1]:
    for profile in [4,6]:
     for setting,mode in [(1,3),(0,3),(1,12)]:
      m=Render().ready(rows,hidden)
      for name,value in {'csi_terminal_id':profile,'terminal_aspect_active':1,'terminal_parser_active':1,'terminal_peer_width_available':1,'ansi_private':1,'ansi_parameter_count':2}.items():m.put(name,value)
      m.put('render_attached',1);m.put('resident_bridge_busy',1)
      m.uc.mem_write(m.symbols['ansi_parameters'],struct.pack('<2H',6,mode));before=m.full()
      expected=0 if rows==25 and mode==3 else 3
      assert m.policy('_aspect_render_preflight_modes',[setting])==expected,(rows,hidden,profile,setting,mode)
      after=m.full()
      for key in ['words','bytes','defaults','planes','video','ui']:assert after[key]==before[key],key
      n+=1
  done('whole-mode-list-preflight-preserves-state-and-retains-supported25-row-width-requests',n)
 for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 sources=['standalone/check_aspect_large_policy_live.py','standalone/program_display_model.py','standalone/check_row_geometry_live.py']
 report=dict(passed=True,terminal_sha256=sha(binary),manifest_sha256=sha(binary.parent/'manifest.json'),enabled=enabled,inputs=sum(c['inputs'] for c in cases),cases=cases,no_nonstack_policy_writes=True,sources={n:sha(ROOT/n) for n in sources},scope=__doc__)
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
