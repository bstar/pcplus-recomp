#!/usr/bin/env python3
"""Current parent bridge -> allocation validator -> EMULATE owner; kernel/hardware modeled."""
import argparse,json,struct,sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
import check_transport as transport
ROOT=transport.ROOT
sha=lambda p:__import__('hashlib').sha256(p.read_bytes()).hexdigest()

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--product',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 product=a.product.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(exist_ok=False)
 transport.BINARY=product/'TERMINAL.EXE';transport.MAP=product/'terminal.map'
 from check_live_setup_profile import Profile
 manifest=json.loads((product/'manifest.json').read_text());assert manifest['experimental_aspect_emulate_policy'] and sha(transport.BINARY)==manifest['binary_sha256']
 for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 class Parent(Profile):
  child_psp=0x9000;child_ds=0x9100;client_offset=0x1000
  def __init__(self):
   self.current_psp=self.child_psp;self.callback_calls=0;self.unsafe=[];self.min_parent_sp=65535;self.monitor=False
   super().__init__()
   self.uc.hook_add(UC_HOOK_CODE,self.observe)
   self.uc.mem_write(0x449,b'\x03\x50\x00');self.uc.mem_write(0x462,b'\0');self.uc.mem_write(0x484,b'\x18')
   self.put('terminal_program_active',1);self.put('terminal_program_kind',4);self.put('terminal_program_pending',0);self.put('connection_state',6)
   self.uc.mem_write((self.child_psp-1)*16,b'M'+struct.pack('<HH',self.child_psp,0x1000)+b'\0'*11)
   # Explicit authored child callback boundary. EMULATE must not call it.
   self.uc.mem_write(0x90100,b'\x31\xc0\xcb')
  def interrupt(self,u,n,data):
   if n==0x21 and u.reg_read(UC_X86_REG_AX)>>8==0x62:u.reg_write(UC_X86_REG_BX,self.current_psp);return
   return super().interrupt(u,n,data)
  def observe(self,u,at,size,data):
   if at==0x90100:self.callback_calls+=1
   if self.monitor and u.reg_read(UC_X86_REG_EFLAGS)&0x200 and u.reg_read(UC_X86_REG_DS)!=u.reg_read(UC_X86_REG_SS):self.unsafe.append(at)
   if self.monitor and u.reg_read(UC_X86_REG_SS)==u.reg_read(UC_X86_REG_DS)==self.ds:self.min_parent_sp=min(self.min_parent_sp,u.reg_read(UC_X86_REG_SP))
  def far(self,name,operation=0,value=0,child=False,flags=0x202,caller_ds=None):
   u=self.uc;target=self.symbols[name]
   segment=self.base_segment+next(s['relative_segment'] for s in manifest['memory_layout']['code_segments'] if self.base+s['relative_segment']*16<=target<self.base+s['relative_segment']*16+s['bytes'])
   ss=self.child_ds if child else self.ds;ds=ss if caller_ds is None else caller_ds;sp=0xe000 if child else self.offset('terminal_stack_top')-4
   keep=[(UC_X86_REG_BX,value),(UC_X86_REG_CX,0x1234),(UC_X86_REG_DX,0x2345),(UC_X86_REG_SI,0x3456),(UC_X86_REG_DI,0x4567),(UC_X86_REG_BP,0xbabe),(UC_X86_REG_ES,0x7000),(UC_X86_REG_DS,ds),(UC_X86_REG_SS,ss)]
   for r,v in [(UC_X86_REG_CS,segment),(UC_X86_REG_SP,sp),(UC_X86_REG_AX,operation),(UC_X86_REG_EFLAGS,flags)]+keep:u.reg_write(r,v)
   u.mem_write(ss*16+sp,struct.pack('<HH',self.return_offset,self.code_segment));self.returned=False
   # DS!=SS is an explicitly invalid caller, not a transition safety claim.
   self.monitor=ds==ss;self.min_parent_sp=65535
   u.emu_start(target,0,count=4000000);self.monitor=False;assert self.returned,name
   assert u.reg_read(UC_X86_REG_SP)==sp+4,(name,'SP')
   for r,v in keep:assert u.reg_read(r)==v,(name,r,u.reg_read(r),v)
   if child:assert u.reg_read(UC_X86_REG_EFLAGS)&0xffff==flags and not self.unsafe,(flags,self.unsafe)
   assert self.callback_calls==0
   return u.reg_read(UC_X86_REG_AX)
  def prepare(self):
   assert self.far('terminal_render_prepare')==0
   assert self.get('_script_render_version')==20
   self.record=[0x5243,20,self.get('_script_render_token'),0x100,0x9000];self.publish();return self
  def publish(self):self.uc.mem_write(self.child_ds*16+self.client_offset,struct.pack('<5H',*self.record))
  def rpc(self,op,value=0,**kw):
   before=(self.dll,self.dlm,self.lcr,self.mcr,self.ier,self.pic,self.vector_value(),bytes(self.rx),bytes(self.tx),self.data_reads,list(self.port_writes))
   result=self.far('resident_bridge_entry',op,value,child=True,**kw)
   if op==20:assert before==(self.dll,self.dlm,self.lcr,self.mcr,self.ier,self.pic,self.vector_value(),bytes(self.rx),bytes(self.tx),self.data_reads,list(self.port_writes))
   return result
  def begin(self):assert self.rpc(0,self.client_offset)==0 and self.get('render_attached')==1;return self
  def view(self):return bytes(self.uc.mem_read(0xb8000,4000)),self.keymap(),self.get('csi_terminal_id'),bytes(self.uc.mem_read(self.symbols['terminal_configuration_values'],44))
 cases=[]
 def done(name,**kw):cases.append(dict(case=name,passed=True,**kw))
 m=Parent();assert m.rpc(20,6)==0xfffd;done('inactive-bridge')
 for index,value in [(0,0),(1,19),(1,21),(2,0),(3,0),(4,0xffff)]:
  m=Parent().prepare();original=list(m.record);m.record[index]=value;m.publish();before=m.view()
  assert m.rpc(0,m.client_offset)==10 and m.get('render_attached')==0 and m.view()==before and m.get('resident_bridge_busy')==0
  m.record=original;m.publish();m.begin();assert m.rpc(20,6)==0
  done('invalid-client-and-repaired-BEGIN',word=index,value=value)
 for index,value in [(0,ord('Q')),(2,0),(4,0)]:
  m=Parent().prepare();at=(m.child_psp-1)*16+index;before=bytes(m.uc.mem_read(at,1));m.uc.mem_write(at,bytes([value]))
  assert m.rpc(0,m.client_offset)==10 and m.get('render_attached')==0
  m.uc.mem_write(at,before);m.begin();assert m.rpc(20,4)==0
  done('invalid-MCB-and-repaired-BEGIN',byte=index)
 for where in ('low-first','low-last','high-first','high-last'):
  m=Parent().prepare();bottom=m.offset('terminal_stack_top')-8192
  off=bottom+(0 if where=='low-first' else 15 if where=='low-last' else 4112 if where=='high-first' else 4127)
  at=m.data_base+off;before=bytes(m.uc.mem_read(at,1));m.uc.mem_write(at,b'\0')
  assert m.rpc(0,m.client_offset)==0xfffb and m.get('render_attached')==0 and m.get('resident_bridge_busy')==0
  m.uc.mem_write(at,before);m.begin();assert m.rpc(20,6)==0
  done('actual-parent-redzone-and-repaired-retry',where=where)
 m=Parent().prepare();assert m.rpc(0,m.client_offset,caller_ds=m.child_ds+1)==0xfffc and m.get('render_attached')==0
 m.begin();done('DS-SS-mismatch-refused-before-BEGIN')
 m=Parent().prepare();m.put('resident_bridge_busy',1);assert m.rpc(0,m.client_offset)==0xfffe
 m.put('resident_bridge_busy',0);m.begin();done('busy-bridge-refused-and-retried')
 for field,value,error,width in [('terminal_program_active',0,10,2),('terminal_program_kind',3,10,2),('render_attached',0,10,2),('render_program_owned',1,10,2),('terminal_program_pending',1,3,2),('terminal_parser_active',1,3,2),('terminal_ansi_wait_active',1,3,2),('terminal_setup_profile_ready',1,10,2),('terminal_script_window_active',1,10,2),('terminal_script_confirm_active',1,10,2),('terminal_editor_screen_owned',1,10,1),('terminal_browser_screen_owned',1,10,1)]:
  m=Parent().prepare().begin();old=m.get(field,width);m.put(field,value,width);before=m.view();assert m.rpc(20,6)==error and m.view()==before and m.get('resident_bridge_busy')==0,field
  m.put(field,old,width);assert m.rpc(20,6)==0
  done('actual-RPC-owner-guard-and-retry',field=field,result=error)
 m=Parent().prepare().begin();m.current_psp+=1;assert m.rpc(20,6)==10;m.current_psp-=1;assert m.rpc(20,6)==0;done('changed-DOS-current-PSP')
 m=Parent().prepare().begin();m.child_ds+=1;assert m.rpc(20,6)==10;m.child_ds-=1;assert m.rpc(20,6)==0;done('changed-caller-DS-SS')
 m=Parent().prepare().begin();at=m.symbols['_script_handoff']+22;m.uc.mem_write(at,b'\x01\0');assert m.rpc(20,6)==14;m.uc.mem_write(at,b'\0\0');assert m.rpc(20,6)==0;done('serial-handoff-returned-refused-and-retried')
 for flags in (2,3,0x202,0x203,0x402,0x403,0x602,0x603):
  m=Parent().prepare().begin()
  for selector in (0,32,256,65535,4,6):
   before=m.view();expected=3 if selector in (0,32) else 7 if selector>255 else 0
   assert m.rpc(20,selector,flags=flags)==expected
   assert m.get('resident_bridge_busy')==0
   if expected:assert m.view()==before
   else:assert m.get('csi_terminal_id')==selector
   done('RPC-selector-ABI',flags=flags,selector=selector,result=expected,parent_stack_bytes=0 if m.min_parent_sp==65535 else m.offset('terminal_stack_top')-8192+4112-m.min_parent_sp)
 m=Parent().prepare().begin();assert m.rpc(2)==0 and m.rpc(20,6)==10;m.begin();assert m.rpc(20,4)==0;done('END-retires-and-new-BEGIN-restores-service')
 m=Parent().prepare().begin();old=list(m.record);m.far('terminal_render_revoke');assert m.get('render_attached')==0
 assert m.rpc(20,6)==0xfffd;m.prepare();current=list(m.record);assert old[2]!=current[2]
 m.record=old;m.publish();assert m.rpc(0,m.client_offset)==10;m.record=current;m.publish();m.begin();assert m.rpc(20,6)==0;done('revoke-inactive-and-stale-token-after-reprepare')
 sources=dict(manifest['sources'])
 for module in tuple(sys.modules.values()):
  file=getattr(module,'__file__',None)
  if file:
   path=Path(file).resolve()
   if path.is_relative_to(ROOT/'standalone'):sources[str(path.relative_to(ROOT))]=sha(path)
 report=dict(passed=True,cases=cases,parent_sha256=sha(transport.BINARY),sources=sources,original_inputs=[],fixture_history=['Initial MCB negative fixture wrote unchanged low bytes1/3. Correct high-byte mutations2/4 reject, then repaired BEGIN succeeds. No product changes.','Stack sampling excludes the CLI-protected intermediate SS/SP transition until parent DS=SS is installed; it is not body stack use.'],limitations=['Actual relocated production parent bridge, BEGIN allocation validator, RPC20 dispatcher, guards, keyboard staging and reset instructions execute. DOS current PSP, MCB/client bytes, BIOS/UART/filesystem boundaries are modeled.','Authored child caller frames and unused callback stub are not a real ASPECT interpreter. No DOS EXEC, child callback execution, IRQ timing/latency or physical acceptance claim.','Redzone and reentry values are deliberately faulted/restored in fixtures; product instructions are not patched, substituted or skipped. This does not prove arbitrary stack-overflow recovery or modal/WHEN/fatal-reset composition.'],scope=__doc__)
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS current parent EMULATE bridge',len(cases),'cases')
if __name__=='__main__':main()
