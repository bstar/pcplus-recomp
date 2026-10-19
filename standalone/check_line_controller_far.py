#!/usr/bin/env python3
"""Paired baseline/current line state and actual register/FLAGS callback equivalence."""
import hashlib,itertools,json,struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
import check_transport as transport
from check_line_edit_live import Live,ROOT
BASE=ROOT/'build/line-controller-baseline'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def machine(baseline=False,keys=()):
 old_binary,old_map=transport.BINARY,transport.MAP
 if baseline:transport.BINARY=BASE/'TERMINAL.EXE';transport.MAP=BASE/'terminal.map'
 try:return Live(keys)
 finally:transport.BINARY,transport.MAP=old_binary,old_map

def snapshot(t):
 names=['screen_cursor_row','screen_cursor_column','screen_attribute_offset','screen_video_offset','screen_cursor_wrap','attributes_normal_value','erase_cell_count','ansi_parameters','terminal_quit','terminal_ansi_wait_active','terminal_ansi_wait_cancel','terminal_ansi_wait_timed_out','uart_rx_count']
 return dict(words={n:t.get(n) for n in names},planes=[bytes(t.uc.mem_read(t.symbols[n],4096)) for n in ('screen_attribute_cells','erase_attribute_values')],video=bytes(t.uc.mem_read(0xb8000,8000)),BIOS=t.calls,wire=bytes(t.tx),ticks=t.tick_reads,keys=list(t.keys))
def abi(t):
 return [t.uc.reg_read(r) for r in (UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI,UC_X86_REG_ES)]+[t.uc.reg_read(UC_X86_REG_DS)==t.ds,t.uc.reg_read(UC_X86_REG_SS)==t.ds,t.uc.reg_read(UC_X86_REG_EFLAGS)&0x600]
def direct(t,name,far,flags):
 u=t.uc
 for r,v in [(UC_X86_REG_CS,t.base_segment),(UC_X86_REG_DS,t.ds),(UC_X86_REG_SS,t.ds),(UC_X86_REG_ES,0xb800),(UC_X86_REG_EFLAGS,flags),(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678),(UC_X86_REG_AX,5),(UC_X86_REG_BX,0x5a5a),(UC_X86_REG_CX,0x7a7a),(UC_X86_REG_DX,17)]:u.reg_write(r,v)
 words=[t.return_offset]+([t.base_segment] if far else []);sp=t.offset('terminal_stack_top')-2*len(words)
 u.mem_write(t.data_base+sp,struct.pack('<'+'H'*len(words),*words));u.reg_write(UC_X86_REG_SP,sp);t.returned=False
 registers=(UC_X86_REG_AX,UC_X86_REG_BX,UC_X86_REG_CX,UC_X86_REG_DX,UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI,UC_X86_REG_ES,UC_X86_REG_DS,UC_X86_REG_SS,UC_X86_REG_EFLAGS)
 observed=[]
 def native_return(cpu,at,size,data):
  if at==t.symbols[name]+3:observed.append([cpu.reg_read(r) for r in registers])
 token=u.hook_add(UC_HOOK_CODE,native_return) if far else None
 try:u.emu_start(t.symbols[name],0,count=1000000)
 finally:
  if token is not None:u.hook_del(token)
 assert t.returned and u.reg_read(UC_X86_REG_SP)==t.offset('terminal_stack_top')
 result=[u.reg_read(r) for r in registers]
 if far:assert observed==[result],(name,'callback changed native register/FLAGS result')
 return result

def check_callbacks():
 callback_cases=0
 callbacks=[('line_native_insert_far','csi_insert_line'),('line_native_delete_far','csi_delete_line'),('line_poll_far','terminal_poll_io'),('line_tick_far','terminal_tick_low'),('line_receive_far','uart_receive_byte'),('attribute_screen_set_cursor_far','screen_set_cursor')]
 for (bridge,target),flags,rx in itertools.product(callbacks,(0x202,0x247),(b'',b'X')):
  runs=[]
  for far in (False,True):
   t=machine();t.position(5,17)
   if rx:t.receive_irq(rx)
   regs=direct(t,bridge if far else target,far,flags);runs.append((regs,snapshot(t)))
  assert runs[0][1]==runs[1][1],(bridge,hex(flags),rx,'state/BIOS')
  assert runs[0][0][4:7]==runs[1][0][4:7],(bridge,'callee registers')
  if bridge in ('line_tick_far','line_receive_far'):assert runs[0][0][0]==runs[1][0][0],(bridge,'scalar result')
  # Cursor output returns the low byte of a temporary stack pointer in BX.
  # BX is volatile; its numeric value varies with the real far-call frame.
  # The observation above requires exact preservation of that actual native
  # return, including BX and FLAGS, rather than inventing a stable BX ABI.
  callback_cases+=1
 return callback_cases

def main():
 current=sha(ROOT/'build/terminal/TERMINAL.EXE');baseline=sha(BASE/'TERMINAL.EXE')
 assert baseline=='d418fca35f3ed3e4adbe7f87eb236f10660ddcc813cb73acfbe5abeac05627cd'
 line_cases=0;wait_cases=0;callback_cases=0
 for (height,top,bottom,row),cmd,pattern,col,n,mono in itertools.product([(1,0,0,0),(5,1,3,2),(25,0,24,24),(25,3,10,5)],(b'L',b'M'),range(3),(0,79),(1,3),(0,1)):
  runs=[]
  for prior in (True,False):
   t=machine(prior);t.put('csi_last_row',height-1);t.put('erase_cell_count',height*80);t.put('screen_first_row',top);t.put('screen_last_row',bottom);t.put('attributes_monochrome',mono);t.position(row,col);t.put('screen_cursor_wrap',int(pattern>0))
   flags=bytes(0 if not pattern else (0x80 if i%79==0 else i%4) if pattern==1 else (0x81 if i%80==0 else i%4) for i in range(height*80));values=bytes((i*31+0x17)&255 for i in range(height*80))
   t.uc.mem_write(t.symbols['screen_attribute_cells'],flags+b'\x55'*(4096-len(flags)));t.uc.mem_write(t.symbols['erase_attribute_values'],values+b'\x66'*(4096-len(values)))
   t.feed(b'\x1b['+str(n).encode()+cmd);runs.append((snapshot(t),abi(t)))
  assert runs[0]==runs[1],(height,top,bottom,row,cmd,pattern,col,n,mono)
  line_cases+=1
 for entry,initial,rx,key,state in itertools.product(('csi_service_daf2','terminal_wait_control_n'),(0,0xfff0),(b'',b'garbage\x0eTAIL'),(None,0x011b,0x2d00,ord('x')),(0,6,2)):
  runs=[]
  for prior in (True,False):
   t=machine(prior,[] if key is None else [key]);t.put('terminal_ansi_m_policy',1);t.put('connection_state',state);t.tick=initial
   if rx:t.receive_irq(rx)
   t.call(entry);runs.append((snapshot(t),abi(t)))
  assert runs[0]==runs[1],(entry,initial,rx,key,state)
  wait_cases+=1
 callback_cases=check_callbacks()
 report=dict(passed=True,binary_sha256=current,baseline_sha256=baseline,line_cases=line_cases,wait_cases=wait_cases,callback_cases=callback_cases,
  checker_sha256=sha(Path(__file__)),baseline_map_sha256=sha(BASE/'terminal.map'),
  sources={p:sha(ROOT/p) for p in ('src/terminal/line_edit.asm','src/terminal/line_controller.asm','src/terminal/attribute_boundary.asm','standalone/check_line_edit_live.py','standalone/check_transport.py')},
  scope='Actual frozen baseline/current DOS MZ instructions and shared hardware-only model. Full planes/video, cursor/parser/owner state, wire, remaining keys, tick reads and callee ABI compare; both profiles and zero/complex metadata.96 wait cases cover CtrlN remaining input, Escape/AltX, ignored key, timeout low-word wrap and modem yield.24 same-image near-target/far-callback executions compare state/BIOS effects and declared scalar/callee results. Each callback must preserve every general register and FLAGS observed at its actual native return; volatile cursor BX may depend on frame position. No product instructions substituted; no actual DOS/BBS or physical claim.')
 (ROOT/'build/terminal/line-controller-far-checks.json').write_text(json.dumps(report,indent=2)+'\n');print('Far line controller:',line_cases,'paired line,',wait_cases,'paired wait,',callback_cases,'register/FLAGS callbacks PASS')
if __name__=='__main__':main()
