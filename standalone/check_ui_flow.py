#!/usr/bin/env python3
"""Execute the recovered flow message, text writer, delay and CGA dependencies."""
import hashlib,json
from unicorn import UC_HOOK_MEM_READ,UC_HOOK_INSN
from unicorn.x86_const import UC_X86_INS_OUT
from check_ui_windows import Windows,ROOT,BINARY

class Flow(Windows):
 def __init__(self):
  super().__init__();self.tick_reads=0;self.outputs=[]
  self.uc.hook_add(UC_HOOK_MEM_READ,self.clock,None,0x46c,0x46d)
  self.uc.hook_add(UC_HOOK_INSN,self.output,None,1,0,UC_X86_INS_OUT)
 def status(self,uc,port,size,_):
  assert (port,size)==(0x3da,1)
  value=9 if self.reads%2 else 0;self.reads+=1;return value
 def output(self,uc,port,size,value,_):
  assert (port,size)==(0x3d8,1);self.outputs.append(value)
 def clock(self,uc,access,address,size,value,_):
  assert address==0x46c and size==2
  uc.mem_write(0x46c,((0xfffe+self.tick_reads//3)&65535).to_bytes(2,'little'));self.tick_reads+=1
 def message(self,duration=0,message=b'FLOW'):
  at=self.offset('window_buffer')+3000;self.uc.mem_write(self.data_base+at,message+b'\0')
  return self.invoke('pcplus_flow_message',[at,duration],callee_cleanup=False)

def run():
 cases=[]
 def check(name,fn):fn();cases.append({'case':name,'passed':True});print(name,'passed',flush=True)
 def painted():
  for cga in (False,True):
   a=Flow();a.put('text_cga_status_port',0x3da if cga else 0);a.uc.mem_write(a.video,b'A\x07'*2000)
   a.message(0)
   assert a.memory()[:30]==b' \x1eF\x1eL\x1eO\x1eW\x1e'+b' \x1e'*10
   assert a.memory()[30:]==b'A\x07'*(2000-15) and a.tick_reads==0
   assert a.outputs==([0x25,0x2d] if cga else [])
 check('zero-duration-leaves-real-string-overlay-with-CGA-blanking',painted)
 def restored():
  for duration in (1,3,65535):
   a=Flow();pattern=bytes(i%256 for i in range(4000));a.uc.mem_write(a.video,pattern)
   a.message(duration,b'TIMED');assert a.memory()==pattern
   edges=duration+1 if duration!=65535 else 1
   assert a.tick_reads==edges*3+1,(duration,a.tick_reads)
 check('timed-message-restores-original-cells-and-wraps-BDA-lowword',restored)
 def suppressed():
  a=Flow();a.put('ui_flow_suppressed',1);a.uc.mem_write(a.video,b'\xa5'*4000)
  a.message(3);assert a.memory()==b'\xa5'*4000 and not a.tick_reads and not a.reads
 check('suppressed-original-branch-performs-no-video-or-delay-I-O',suppressed)
 def bottom():
  a=Flow();a.uc.mem_write(a.video,b'A\x07'*2000);a.put('ui_flow_video_base',3840);a.put('ui_flow_coordinate_base',0x1800)
  a.message(0,b'123456789ABCDE')
  assert a.memory()[:3840]==b'A\x07'*1920
  assert a.memory()[3840:3870]==b' \x1e'+b''.join(bytes([v,0x1e]) for v in b'123456789ABCDE')
  assert a.memory()[3870:]==b'A\x07'*65
 check('configured-bottom-row-and-maximum-fitting-message',bottom)
 def delay():
  for duration,edges in [(0,1),(1,2),(3,4),(65535,1)]:
   a=Flow();a.invoke('ui_tick_delay',[duration]);assert a.tick_reads==edges*3+1
 check('actual-delay-input-zero-and-duration-plus-one-legacy-semantics',delay)
 result={'passed':True,'binary_sha256':hashlib.sha256(BINARY.read_bytes()).hexdigest(),'cases':cases,'fixtures':['BDA tick lowword advances every three reads and crosses ffff->0.','CGA status alternates0/9; actual IN/OUT and blank/unblank code executes.'],'scope':'Actual recovered original flow-message and complete dependencies; no menu fixtures/no-op rendering.'}
 (ROOT/'build/ui-windows/flow-checks.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':run()
