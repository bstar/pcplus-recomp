#!/usr/bin/env python3
"""Linked child capability/stack/ABI tests; the far endpoint is an explicit
lifecycle boundary, not a parser. UART/kernel/keyboard boundaries are modeled."""
import hashlib,json,struct
import check_uart as q
from unicorn.x86_const import *
q.BINARY=q.ROOT/'build/aspect-runner/ASPECT.EXE';q.MAP=q.ROOT/'build/aspect-runner/ASPECT.map'
OUT=q.ROOT/'build/aspect-render-client'
class Client(q.Machine):
 def __init__(self):
  super().__init__();self.requests=[];self.reenter=False;self.nested=0;self.monitor=False;self.bad_windows=[];self.inject_irq=False;self.irq_injected=False;self.tick=0;self.child_psp=0x9000;self.parent_psp=0x6000
  self.uc.mem_write(0x400,struct.pack('<4H',0x3f8,0x2f8,0x3e8,0x2e8))
  self.uc.mem_write(self.child_psp*16+0x16,struct.pack('<H',self.parent_psp))
  self.uc.mem_write((self.parent_psp-1)*16,b'M'+struct.pack('<HH',self.parent_psp,0x2000))
  self.put('__STACKLOW',0xc000);self.put('__STACKTOP',0xe000)
  self.uc.mem_write(0x61100,b'\xb8\0\0\xcb') # Explicit BEGIN/EMIT/END success boundary.
  self.uc.mem_write(self.data_base+0xb000,b'/S1:0003:03:N:6200:0100\0')
  self.desc=0x62100;self.words=[0x4f495341,4,48,0x6000,0x6200,0x1000,4096,0,0,0,0,0,0,0,0,0,0,0,0,0x100,0x6100,0x7123,12]
  self.publish()
 def publish(self):
  w=self.words;w[9]=w[3]^w[4]^w[5]^0xa510
  for i in [7,8,11,12,13,14,15,16,17,18,19,20,21,22]:w[9]^=w[i]
  self.uc.mem_write(self.desc,struct.pack('<I22H',*w))
 def _code(self,u,a,s,d):
  if a==self.base+0xf000:self.returned=True;u.emu_stop()
  if self.monitor and u.reg_read(UC_X86_REG_EFLAGS)&0x200 and u.reg_read(UC_X86_REG_DS)!=u.reg_read(UC_X86_REG_SS):
   self.bad_windows.append(dict(instruction=a,ds=u.reg_read(UC_X86_REG_DS),ss=u.reg_read(UC_X86_REG_SS)))
  if self.monitor and self.inject_irq and not self.irq_injected and a==self.symbols['_aspect_render_callback_dispatch'] and u.reg_read(UC_X86_REG_EFLAGS)&0x200:
   self.irq_injected=True;self.rx.extend(b'Q');sp=u.reg_read(UC_X86_REG_SP)-6;ss=u.reg_read(UC_X86_REG_SS);cs=u.reg_read(UC_X86_REG_CS);flags=u.reg_read(UC_X86_REG_EFLAGS)
   u.mem_write(ss*16+sp,struct.pack('<3H',a-cs*16,cs,flags&0xffff));u.reg_write(UC_X86_REG_SP,sp);u.reg_write(UC_X86_REG_EFLAGS,flags&~0x300)
   u.reg_write(UC_X86_REG_CS,self.base_segment);u.reg_write(UC_X86_REG_IP,self.symbols['uart_receive_interrupt']-self.base)
   return
  if a==0x61100:self.requests.append((u.reg_read(UC_X86_REG_AX),u.reg_read(UC_X86_REG_BX)))
  if self.reenter and a==self.symbols['_aspect_render_callback_dispatch']:
   if not self.nested:
    self.nested=1;sp=u.reg_read(UC_X86_REG_SP)-4
    u.mem_write(self.data_base+sp,struct.pack('<HH',a-self.base,self.base_segment));u.reg_write(UC_X86_REG_SP,sp)
    u.reg_write(UC_X86_REG_AX,3);u.reg_write(UC_X86_REG_BX,0);u.reg_write(UC_X86_REG_IP,self.callback_offset)
   elif self.nested==1:
    assert u.reg_read(UC_X86_REG_AX)==10;self.nested=2
  if a==self.symbols['_aspect_serial_ticks']:
   self.tick+=1;u.mem_write(0x46c,struct.pack('<I',self.tick%1573040))
 def _interrupt(self,u,n,d):
  if n==0x21 and u.reg_read(UC_X86_REG_AX)>>8==0x62:u.reg_write(UC_X86_REG_BX,self.child_psp);return
  if n==0x16:
   u.reg_write(UC_X86_REG_EFLAGS,u.reg_read(UC_X86_REG_EFLAGS)|0x40);return
  return super()._interrupt(u,n,d)
 def call(self,name,arguments=(),irq=False,limit=250000,**regs):
  u=self.uc;u.reg_write(UC_X86_REG_CS,self.base_segment);u.reg_write(UC_X86_REG_DS,self.ds);u.reg_write(UC_X86_REG_SS,self.ds);u.reg_write(UC_X86_REG_EFLAGS,0x202)
  for r,v in regs.items():u.reg_write(globals()['UC_X86_REG_'+r.upper()],v)
  words=([0xf000,self.base_segment,0x202] if irq else [0xf000])+list(arguments);sp=0xdfc0-len(words)*2
  u.mem_write(self.data_base+sp,struct.pack('<'+'H'*len(words),*words));u.reg_write(UC_X86_REG_SP,sp)
  self.returned=False;u.emu_start(self.symbols[name],self.base+0x10000,count=limit);assert self.returned,name
  return u.reg_read(UC_X86_REG_AX)
 def open(self):return self.call('_aspect_serial_open',[0xb000])
 def callback(self,operation,value=0,flags=0x202):
  offset=self.call('_aspect_render_callback_offset');self.callback_offset=offset;u=self.uc
  values={'bx':value,'cx':0x1234,'dx':0x2345,'si':0x3456,'di':0x4567,'bp':0x5678,'es':0x7200,'ds':0x6200,'ss':0x6200,'cs':self.base_segment,'sp':0xe000,'ax':operation}
  for name,v in values.items():u.reg_write(globals()['UC_X86_REG_'+name.upper()],v)
  u.reg_write(UC_X86_REG_EFLAGS,flags);u.mem_write(0x62000+0xe000,struct.pack('<HH',0xf000,self.base_segment))
  self.monitor=True;self.returned=False;u.emu_start(self.base+offset,self.base+0x10000,count=300000);assert self.returned
  self.monitor=False
  if self.bad_windows:
   OUT.mkdir(parents=True,exist_ok=True);(OUT/'transition-window-failure.json').write_text(json.dumps(dict(binary_sha256=sha(q.BINARY),visible_windows=self.bad_windows),indent=2)+'\n')
  assert not self.bad_windows,self.bad_windows
  for name,v in values.items():
   if name in ['ax','cs']:continue
   expect=v+4 if name=='sp' else v
   assert u.reg_read(globals()['UC_X86_REG_'+name.upper()])==expect,(name,hex(u.reg_read(globals()['UC_X86_REG_'+name.upper()])),hex(expect))
  assert u.reg_read(UC_X86_REG_EFLAGS)&0xfff==flags&0xfff
  return u.reg_read(UC_X86_REG_AX)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cases=[]
 def done(name,n):cases.append(dict(case=name,inputs=n,passed=True));print(name,n,flush=True)
 for i,v in [(22,10),(22,11),(6,4095),(20,0),(21,0),(22,3),(13,1),(15,2026),(7,4097),(8,4096)]:
  m=Client();m.words[i]=v;m.publish();assert m.open()==1 and not m.writes and not m.get('_aspect_serial_active')
 done('invalid-capability-preload-projection-before-UART',10)
 # Valid token + invalid far entry must fail even with a freshly valid guard.
 for seg,off in [(0x5000,0),(0x8000,0),(0x6200,0x100),(0x6200,0x1000)]:
  m=Client();m.words[19]=off;m.words[20]=seg;m.publish();assert m.open()==1 and not m.writes
 done('entry-outside-parent-or-overlapping-descriptor-ring',4)
 for low,top in [(0xc000,0xc800),(0xf000,0x1000),(0xd800,0xf800)]:
  m=Client();m.put('__STACKLOW',low);m.put('__STACKTOP',top);assert m.open()==1 and not m.writes
 done('callback-stack-extent-and-live-SP-admission-before-UART',3)
 m=Client();assert m.open()==0 and m.call('_aspect_render_active')==1
 assert m.symbols['_runtime_receive_suppress_echo']==m.symbols['_runtime_wait_gate']==m.symbols['aspect_flow_wait_gate']
 m.put('_runtime_wait_gate',3);m.call('_runtime_receive_reset');assert m.get('_runtime_wait_gate')==3 and m.get('_runtime_receive_display')==1
 assert m.call('_aspect_render_emit',[65])==0
 assert m.call('_aspect_serial_close')==0 and m.call('_aspect_render_active')==1
 assert m.call('_aspect_render_emit',[66])==0 and m.call('_aspect_render_finish')==0 and not m.call('_aspect_render_active')
 done('single-native-E382-alias-render-admission-and-post-UART-diagnostic-lifecycle',1)
 m=Client();assert m.call('_aspect_render_status',[65535])==10 and not m.requests
 assert m.open()==0;m.requests.clear()
 for value in (65535,0,1,255):
  assert m.call('_aspect_render_status',[value])==0 and m.requests[-1]==(3,value)
 before=len(m.requests)
 for value in (256,65534):assert m.call('_aspect_render_status',[value])==7
 assert len(m.requests)==before
 assert m.call('_aspect_render_finish')==0;m.requests.clear()
 assert m.call('_aspect_render_status',[65535])==10 and not m.requests
 done('v2-STATUS-scalar-bounds-and-lease-lifetime-before-parent-request',8)
 m=Client();assert m.open()==0;assert m.call('_aspect_serial_close')==0
 m.requests.clear();assert m.call('_aspect_render_status',[65535])==14 and not m.requests
 done('STATUS-after-UART-close-rejected-before-parent-hardware-request',1)
 for flags in [0x43,0x243,0x443,0x643]:
  m=Client();assert m.open()==0;m.receive_irq(b'\xff')
  assert m.callback(5,flags=flags)==255
  assert m.callback(1,flags=flags)==0
  assert m.callback(5,flags=flags)==255
  assert m.callback(3,flags=flags)==0
  assert m.callback(4,flags=flags)==0
 done('different-parent-DS-SS-child-stack-full-register-IF-DF-preservation',4)
 m=Client();m.words[12]=2;m.publish();assert m.open()==0;m.receive_irq(b'\xff')
 assert m.callback(5)==127 and m.callback(1)==0
 assert m.call('_aspect_serial_close')==0
 assert bytes(m.uc.mem_read(0x63000,1))==b'\xff'
 done('7bit-dequeue-unread-and-raw-ASIO-handback-through-callback',1)
 m=Client();assert m.open()==0;assert m.callback(1)==14 and m.get('_runtime_error')==14
 assert m.callback(4)==14
 done('invalid-unread-is-typed-fatal-not-ignored',1)
 m=Client();assert m.open()==0
 m.uc.mem_write(m.data_base+0xc000,b'\0\0');assert m.callback(3)==10
 assert m.call('_aspect_render_emit',[65])==10
 done('redzone-corruption-rejects-callback-and-next-request',1)
 # Receive mapping consumes one lead only; actual cdecl callback is invoked
 # by the unchanged native4C74 body. No parent parser is modeled in this unit.
 m=Client();assert m.open()==0;m.call('_runtime_receive_reset');m.receive_irq(b'A')
 assert m.call('_runtime_receive_character',[1,0])==65 and m.get('uart_rx_count')==0
 assert m.call('_aspect_render_finish')==0
 done('actual-native4C74-cdecl-emit-balanced-stack',1)
 m=Client();assert m.open()==0;m.call('_runtime_receive_reset');m.put('_runtime_wait_gate',1)
 m.receive_irq(b'ABCD');m.requests.clear()
 assert m.call('aspect_receive_read_control',[0])==65 and not m.requests
 m.call('aspect_flow_gate_decrement');assert m.get('_runtime_wait_gate')==0
 assert m.call('aspect_receive_read_control',[0])==66 and m.requests==[(1,66)]
 m.call('aspect_flow_gate_increment');assert m.get('_runtime_wait_gate')==1
 assert m.call('aspect_receive_read_control',[0])==67 and m.requests==[(1,66)]
 assert m.call('_runtime_receive_character',[1,0])==68 and m.requests==[(1,66),(1,68)]
 m.call('aspect_flow_gate_decrement');assert m.get('_runtime_wait_gate')==0
 done('actual-CF-D0-shared-E382-selector-display-and-independent-WAITFOR-display',1)
 m=Client();assert m.open()==0;m.reenter=True
 assert m.callback(3)==0 and m.nested==2
 assert m.callback(4)==0
 done('nested-callback-rejects-without-overwriting-active-parent-frame',1)
 m=Client();assert m.open()==0;m.receive_irq(b'A');assert m.callback(5)==65
 m.receive_irq(b'Z'*4096);before=bytes(m.uc.mem_read(m.symbols['uart_rx_buffer'],4096))
 assert m.callback(1)==14 and m.get('_aspect_serial_status')==5 and m.get('uart_rx_count')==4096
 assert bytes(m.uc.mem_read(m.symbols['uart_rx_buffer'],4096))==before and m.callback(4)==14
 assert m.call('_aspect_serial_close')==5
 assert m.call('_aspect_render_emit',[ord('E')])==0 and m.callback(4)==0
 assert m.call('_aspect_render_finish')==0
 done('real-ISR-fills-unread-slot-typed-overflow-and-postclose-error-render',1)
 for code in [1,3,10,13,14,0xfffb,0xfffc,0xfffd,0xfffe,0xffff]:
  m=Client();assert m.open()==0;m.uc.mem_write(0x61100,b'\xb8'+struct.pack('<H',code)+b'\xcb');m.uc.ctl_remove_cache(0x61100,0x61104)
  observed=m.call('_aspect_render_emit',[65]);assert observed==(code if code<=14 else 10),(code,observed)
 done('parent-result-is-typed-and-reserved-bridge-results-map-state',10)
 m=Client();assert m.open()==0;m.inject_irq=True
 assert m.callback(3,flags=0x643)==0 and m.irq_injected and m.get('uart_rx_count')==1
 assert m.call('_aspect_serial_read')==ord('Q')
 done('IF-obeying-actual-UART-ISR-during-child-callback-with-restored-parent-frame',1)
 report=dict(passed=True,binary_sha256=sha(q.BINARY),manifest_sha256=sha(q.ROOT/'build/aspect-runner/manifest.json'),checker_sha256=sha(__import__('pathlib').Path(__file__)),original_inputs=[],regression_history=[{'binary_sha256':'83dc70363614c919c50b375c30e80645f2d0ff21a244022cc05a5841b56499cb','failure':'IF-enabled childDS/parentSS transition','evidence':'build/aspect-render-client-history/pre-CLI-transition/transition-window-failure.json'}],cases=cases,inputs=sum(c['inputs'] for c in cases),limitations=['Far endpoint is an explicit lifecycle success boundary; actual parent input/parser/render engine is not modeled or claimed here.','DOS/UART/BIOS keyboard boundaries modeled; real callback-stack and register instructions execute.','CPU unit sets documented usable CRT stack bounds; independent actual8086DOS fixture corroborates real Watcom bounds.'])
 OUT.mkdir(parents=True,exist_ok=True);(OUT/'checks.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
