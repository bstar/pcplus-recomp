#!/usr/bin/env python3
"""Execute capability21 parent bridge, allocation policy and field controller."""
import argparse,hashlib,json,struct,sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
import check_transport as transport
ROOT=transport.ROOT
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('product','output'):p.add_argument('--'+name,type=Path,required=True)
 a=p.parse_args();product=a.product.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir()
 transport.BINARY=product/'TERMINAL.EXE';transport.MAP=product/'terminal.map'
 from check_live_setup_profile import Profile
 manifest=json.loads((product/'manifest.json').read_text());assert manifest['experimental_aspect_get_display'] and sha(transport.BINARY)==manifest['binary_sha256']
 for name,digest in manifest['sources'].items():assert sha(ROOT/name)==digest,name
 class Parent(Profile):
  child_psp=0x9000;child_ds=0x9100;client_offset=0x1000
  def __init__(self):
   self.current_psp=self.child_psp;self.callback_calls=0;self.monitor=False;self.unsafe=[]
   super().__init__();self.uc.hook_add(UC_HOOK_CODE,self.observe)
   self.uc.mem_write(0x449,b'\x03\x50\0');self.uc.mem_write(0x462,b'\0');self.uc.mem_write(0x484,b'\x18')
   self.put('terminal_program_active',1);self.put('terminal_program_kind',4);self.put('terminal_program_pending',0);self.put('connection_state',6)
   self.uc.mem_write((self.child_psp-1)*16,b'M'+struct.pack('<HH',self.child_psp,0x1000)+b'\0'*11)
   self.uc.mem_write(0x90100,b'\x31\xc0\xcb')
  def observe(self,u,at,size,data):
   if at==0x90100:self.callback_calls+=1
   if self.monitor and u.reg_read(UC_X86_REG_EFLAGS)&0x200 and u.reg_read(UC_X86_REG_DS)!=u.reg_read(UC_X86_REG_SS):self.unsafe.append(at)
  def interrupt(self,u,n,data):
   if n==0x21 and u.reg_read(UC_X86_REG_AX)>>8==0x62:u.reg_write(UC_X86_REG_BX,self.current_psp);return
   return super().interrupt(u,n,data)
  def far(self,name,op=0,value=0,child=False,flags=0x202,caller_ds=None):
   u=self.uc;target=self.symbols[name]
   segment=self.base_segment+next(s['relative_segment'] for s in manifest['memory_layout']['code_segments'] if self.base+s['relative_segment']*16<=target<self.base+s['relative_segment']*16+s['bytes'])
   ss=self.child_ds if child else self.ds;ds=ss if caller_ds is None else caller_ds;sp=0xe000 if child else self.offset('terminal_stack_top')-4
   keep=[(UC_X86_REG_BX,value),(UC_X86_REG_CX,0x1234),(UC_X86_REG_DX,0x2345),(UC_X86_REG_SI,0x3456),(UC_X86_REG_DI,0x4567),(UC_X86_REG_BP,0xbabe),(UC_X86_REG_ES,0x7000),(UC_X86_REG_DS,ds),(UC_X86_REG_SS,ss)]
   for r,v in [(UC_X86_REG_CS,segment),(UC_X86_REG_SP,sp),(UC_X86_REG_AX,op),(UC_X86_REG_EFLAGS,flags)]+keep:u.reg_write(r,v)
   u.mem_write(ss*16+sp,struct.pack('<HH',self.return_offset,self.code_segment));self.returned=False;self.monitor=ds==ss;self.unsafe=[]
   u.emu_start(target,0,count=4000000);self.monitor=False;assert self.returned,name
   assert u.reg_read(UC_X86_REG_SP)==sp+4
   for r,v in keep:assert u.reg_read(r)==v,(name,r,u.reg_read(r),v)
   # Existing BREAK's recovered packed-cell snapshot reader intentionally
   # borrows video DS for four instructions; it does not access stack/callbacks
   # there (see ui_screen_far.asm). New field operations allow no such span.
   unexpected=[at for at in self.unsafe if not(op==5 and self.symbols['ui_read_byte']+0x11<=at<=self.symbols['ui_read_byte']+0x17)]
   if child:assert u.reg_read(UC_X86_REG_EFLAGS)&0xffff==flags and not unexpected,(op,flags,u.reg_read(UC_X86_REG_EFLAGS)&0xffff,unexpected[:8])
   assert self.callback_calls==0
   return u.reg_read(UC_X86_REG_AX)
  def prepare(self):
   assert self.far('terminal_render_prepare')==0 and self.get('_script_render_version')==21
   self.record=[0x5243,21,self.get('_script_render_token'),0x100,0x9000];self.publish();return self
  def publish(self):self.uc.mem_write(self.child_ds*16+self.client_offset,struct.pack('<5H',*self.record))
  def rpc(self,op,value=0,**kw):
   before=(self.dll,self.dlm,self.lcr,self.mcr,self.ier,self.pic,self.vector_value(),bytes(self.rx),bytes(self.tx),self.data_reads,list(self.port_writes))
   result=self.far('resident_bridge_entry',op,value,child=True,**kw)
   assert before==(self.dll,self.dlm,self.lcr,self.mcr,self.ier,self.pic,self.vector_value(),bytes(self.rx),bytes(self.tx),self.data_reads,list(self.port_writes))
   return result
  def begin(self):assert self.rpc(0,self.client_offset)==0;return self
  def view(self):return bytes(self.uc.mem_read(0xb8000,4000)),self.cursor,self.shape,self.get('screen_cursor_row'),self.get('screen_cursor_column')
  def field(self,width=5,text=b'LoC!?'):
   assert self.rpc(21,0xffff)==0 and self.rpc(22,0x1f00|width)==0
   for i,byte in enumerate(text):assert self.rpc(23,i*256+byte)==0
   return self
 cases=[]
 def done(name,**kw):cases.append(dict(case=name,passed=True,**kw))
 m=Parent();assert m.rpc(21,0xffff)==0xfffd;done('inactive-bridge')
 m=Parent().prepare().begin();before=m.view();oldshape=m.shape;row=m.get('screen_cursor_row');col=m.get('screen_visible_column');m.field()
 assert m.view()==before and m.rpc(24,0x104)==0
 frame=bytearray(before[0]);start=(row*80+col)*2
 for i,byte in enumerate(b'LoC!?'):frame[start+i*2:start+i*2+2]=bytes([byte,31])
 assert m.view()[0]==bytes(frame) and m.get('screen_cursor_column')==before[4]
 assert m.rpc(25,9)==0xf000|((col+4)%80)
 assert m.rpc(26,0)==0 and m.shape==oldshape and m.get('screen_cursor_column')==col+4
 assert m.view()[0]==bytes(frame) and m.rpc(2)==0xe000 and not m.get('render_attached');done('actual-bridge-staging-pixels-native-adoption-and-END')
 for op,value in [(5,0),(8,0x2c00),(9,0),(11,1),(12,0),(20,6)]:
  m=Parent().prepare().begin().field();before=m.view();assert m.rpc(op,value)==10 and m.view()==before and m.get('terminal_script_field_active')==1
  assert m.rpc(26,1)==0xe000;done('competing-operation',operation=op)
 m=Parent().prepare().begin();assert m.rpc(5,0)==0;before=m.view()
 assert m.rpc(21,0xffff)==10 and m.view()==before and not m.get('terminal_script_field_active')
 assert m.rpc(5,1)==0;m.field();assert m.rpc(26,1)==0xe000;done('BREAK-bracket-excludes-field-and-repaired-retry')
 m=Parent().prepare().begin().field();assert m.rpc(24,0)==0
 assert m.rpc(1,ord('Z'))==0;assert m.rpc(24,0)==0;assert m.rpc(26,0)==0;done('real-parent-parser-emits-while-field-owned-and-repaint')
 for where in ('client','version','mcb','descriptor','callback'):
  m=Parent().prepare().begin().field();before=m.view()
  if where=='client':at=m.child_ds*16+m.client_offset+4
  elif where=='version':at=m.child_ds*16+m.client_offset+2
  elif where=='mcb':at=(m.child_psp-1)*16+3
  elif where=='descriptor':at=m.symbols['_script_render_token']
  else:at=m.child_ds*16+m.client_offset+6
  saved=bytes(m.uc.mem_read(at,2));m.uc.mem_write(at,struct.pack('<H',0x200 if where=='callback' else 20 if where=='version' else 0))
  assert m.rpc(24,0)==10 and m.rpc(26,1)==10 and m.view()==before and m.get('terminal_script_field_active')==1
  m.uc.mem_write(at,saved);assert m.rpc(26,1)==0xe000;done('per-request-authentication-and-retry',changed=where)
 for version in (0,20,22):
  m=Parent().prepare();m.record[1]=version;m.publish();assert m.rpc(0,m.client_offset)==10 and not m.get('render_attached');done('wrong-version-BEGIN',version=version)
 for changed in ('psp','ds'):
  m=Parent().prepare().begin().field();before=m.view()
  if changed=='psp':m.current_psp+=1
  else:m.child_ds+=1
  assert m.rpc(24,0)==10 and m.view()==before
  if changed=='psp':m.current_psp-=1
  else:m.child_ds-=1
  assert m.rpc(26,1)==0xe000;done('wrong-caller',changed=changed)
 m=Parent().prepare().begin().field();m.uc.mem_write(m.symbols['_script_handoff']+22,b'\1\0')
 assert m.rpc(24,0)==14 and m.rpc(26,0)==14 and m.rpc(26,1)==0xe000;done('returned-UART-allows-only-explicit-error-retirement')
 m=Parent().prepare().begin().field();before=m.view();assert m.rpc(24,0,caller_ds=m.child_ds+1)==0xfffc and m.view()==before
 assert m.rpc(26,1)==0xe000;done('bridge-DS-SS-refusal-preserves-field')
 m=Parent().prepare().begin().field();before=m.view();m.put('resident_bridge_busy',1);assert m.rpc(26,1)==0xfffe and m.view()==before and m.get('terminal_script_field_active')==1
 m.put('resident_bridge_busy',0);assert m.rpc(26,1)==0xe000;done('busy-bridge-cannot-falsely-acknowledge-retirement')
 for end in (26,2):
  m=Parent().prepare().begin().field();m.put('terminal_script_window_active',1);before=m.view()
  assert m.rpc(end,1 if end==26 else 0)==0xe00a and not m.get('terminal_script_field_active') and m.view()==before
  assert m.get('render_attached')==(end==26);done('tagged-retirement-despite-foreign-window',operation=end)
 m=Parent().prepare().begin().field();m.put('script_break_ui_active',1);before=m.view()
 assert m.rpc(26,1)==0xe00a and m.view()==before and not m.get('terminal_script_field_active');done('foreign-BREAK-error-retirement-preserves-cursor')
 for flags in (2,3,0x202,0x203,0x402,0x403,0x602,0x603):
  m=Parent().prepare().begin();before=m.view();result=m.rpc(21,0xffff,flags=flags)
  if not flags&0x200:
   assert result==10 and m.view()==before and not m.get('terminal_script_field_active');done('disabled-IF-refused-with-caller-ABI',flags=flags);continue
  assert result==0
  assert m.rpc(22,0x0701,flags=flags)==0 and m.rpc(23,0xff,flags=flags)==0 and m.rpc(24,0,flags=flags)==0 and m.rpc(26,0,flags=flags)==0
  done('actual-request-ABI',flags=flags)
 m=Parent().prepare().begin().field();m.far('terminal_render_revoke');assert not m.get('terminal_script_field_active') and not m.get('render_attached') and m.rpc(21,0xffff)==0xfffd;done('revoke-retires-field-and-old-bridge')
 sources=dict(manifest['sources'])
 for module in list(sys.modules.values()):
  name=getattr(module,'__file__',None)
  if not name:continue
  path=Path(name).resolve()
  if path.suffix=='.py' and path.is_relative_to(ROOT) and path.relative_to(ROOT).parts[0] in ('standalone','src'):sources[str(path.relative_to(ROOT))]=sha(path)
 report=dict(passed=True,parent_sha256=manifest['binary_sha256'],cases=cases,sources=sources,original_inputs=[],scope=__doc__+' Actual linked full parent renderer/bridge/allocation validator/field/adapters/native cursor/parser. Authored child callback never executes. BIOS, DOS PSP, UART hardware modeled; no actual child EXE/interpreter, live serial/BBS, whole package or physical acceptance.')
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS GET display bridge:',len(cases),'cases')

if __name__=='__main__':main()
