#!/usr/bin/env python3
"""Source-linked Script menu, direct EXEC, and UART/video child restoration.
Only DOS kernel/BIOS/UART hardware is modeled; the ASPECT child interpreter is
verified separately by actual DOS tests, not by this EXEC boundary model.
"""
import hashlib,json
from pathlib import Path
from check_translation_edit_live import Editor,ROOT
from check_program_actions_live import BINARY
from unicorn.x86_const import *
from unicorn import UC_HOOK_CODE
from check_transport import Transport
import struct
class Script(Editor):
 def __init__(self):
  super().__init__()
  # Actual startup snapshot and physical BDA contract required for renderer
  # admission. No product policy or capture callback is replaced here.
  self.uc.mem_write(0x449,b'\x03'+struct.pack('<H',80))
  self.uc.mem_write(0x462,b'\0');self.uc.mem_write(0x484,b'\x18')
  for initializer in ['_capture_file_initialize','_snapshot_file_initialize',
                      '_monitor_file_initialize','_capture_session_initialize','_printer_device_initialize']:
   assert self.call(initializer)==0
  assert self.call('terminal_reset_capture')==0
  self.handback=b'';self.handback_status=0;self.live_prompt_calls=0;self.handoff_tamper=None
 def restored(self):
  assert bytes(self.uc.mem_read(0xb8000,4000))==self.original_screen
  assert (self.mode,self.columns,self.page,self.cursor,self.shape)==(3,80,0,0x0611,0x060f)
  assert {name:self.get(name) for name in self.logical_names}==self.logical_before
  assert self.vector_value()==self.parent_vector
  expected_mcr=9 if self.get('uart_rts_lowered',1) else 11
  assert (self.lcr,self.mcr,self.ier,self.dll,self.dlm)==(3,expected_mcr,1,3,0)
  assert not self.pic&self.irq_mask
  assert {name:self.get(name,1 if name.startswith('uart_saved_') else 2) for name in self.baseline}==self.baseline
 def interrupt(self,u,n,d):
  ax=u.reg_read(UC_X86_REG_AX)
  if (n==0x16 or (n==0x10 and ax>>8==14)) and self.get('terminal_program_active') and self.get('terminal_program_kind')==4:
   assert self.ier==1 and not self.pic&self.irq_mask and self.vector_value()==self.parent_vector,'Script prompt stranded the parent UART'
   self.live_prompt_calls+=1
   if n==0x16:return Transport.interrupt(self,u,n,d)
   if ax>>8==14:
    row,col=self.cursor>>8,self.cursor&255
    if ax&255==13:col=0
    elif ax&255==10:row+=1
    else:
     if row<25 and col<80:u.mem_write(0xb8000+(row*80+col)*2,bytes([ax&255,7]))
     col+=1
    if col>=80:col=0;row+=1
    self.cursor=(min(row,24)<<8)|col;return
  result=super().interrupt(u,n,d)
  if n==0x21 and ax==0x4b00 and not self.exec_error:
   # Child process is a DOSkernel boundary; exact ASIO child publication is
   # independently executed by check_aspect_serial.py.
   at=self.symbols['_script_handoff'];ring=self.symbols['uart_rx_buffer']
   u.mem_write(ring,self.handback);u.mem_write(at+16,struct.pack('<2H',len(self.handback),self.handback_status));u.mem_write(at+22,b'\x01\x00')
   if self.handoff_tamper:
    offset,value=self.handoff_tamper;u.mem_write(at+offset,struct.pack('<H',value))
  return result

def main():
 cases=[]
 def done(name,n):cases.append(dict(case=name,inputs=n,passed=True));print(name,n,flush=True)
 def model(**kw):
  m=Script()
  m.install_program_name();m.child_status=0;return m
 def path(m,p):m.uc.mem_write(m.symbols['_command_menu_script'],p+b'\0')
 def prepare_phase(m):
  # Direct unit call represents PROGRAM's actual quiet pre-EXEC phase.
  # The normal safe-point cases below reach this phase through product code.
  assert m.get('terminal_program_pending') and m.get('terminal_program_kind')==4
  m.put('terminal_program_pending',0);m.put('terminal_program_active',1)
  return m.call('terminal_script_prepare')
 def descriptor(m):return struct.unpack('<I22H',m.uc.mem_read(m.symbols['_script_handoff'],48))
 def guard(d):
  g=d[3]^d[4]^d[5]^0xa510
  for value in [*d[7:9],*d[11:]]:g^=value
  return g
 def capability(d):
  assert d[1:3]==(4,48) and d[19] and d[20] and d[21] and d[22]==1,d
  assert d[9]==guard(d),d

 for p in [b'TEST.ASX',b'D:\\TEST.ASX',b'D:\\SCRIPTS\\TEST.ASX',b'D:TEST.ASX',b'\\TEST.ASX']:
  m=model();path(m,p);assert m.call('terminal_script_start')==0
  assert m.get('terminal_program_pending') and m.get('terminal_program_kind')==4 and not m.children
  m.keys.append(32);m.safe();assert len(m.children)==1 and m.children[0]['path']==b'D:\\APP\\ASPECT.EXE' and m.children[0]['tail'].startswith(b' '+p+b' /S1:0003:03:H:')
  assert m.get('terminal_program_status')==4 and not m.get('terminal_program_active');m.restored()
 done('relative-drive-rooted-direct-sibling-child-and-real-foreground-restore',5)
 # Native terminal slot0 is a live IRQ-table slot, not a COM identifier.
 # Execute prepare independently of the modeled COM1 hardware boundary.
 for port,base,vector in [(1,0x3f8,12),(2,0x2f8,11),(3,0x3e8,12),(4,0x2e8,11)]:
  m=model();path(m,b'TEST.ASX');m.put('terminal_port_number',port)
  m.put('uart_port_index',0);m.put('terminal_irq_vector',vector)
  for name,offset in [('rbr',0),('thr',0),('ier',1),('lcr',3),('mcr',4),('lsr',5),('msr',6)]:
   m.put('uart_port_'+name,base+offset)
  assert m.call('terminal_script_start')==0
  assert prepare_phase(m)==0
  tail=bytes(m.uc.mem_read(m.symbols['terminal_translation_edit_tail'],96)).split(b'\0',1)[0]
  assert b' /S'+str(port).encode()+b':0003:03:H:' in tail,tail
 done('selected-COM1-through4-independent-of-native-active-slot-zero',4)
 for port,base,vector in [(0,0x3f8,12),(5,0x3f8,12),(2,0x3f8,11),(2,0x2f8,12)]:
  m=model();path(m,b'TEST.ASX');m.put('terminal_port_number',port)
  m.put('uart_port_thr',base);m.put('terminal_irq_vector',vector)
  assert m.call('terminal_script_start')==0
  assert prepare_phase(m)==1 and not m.children
 done('invalid-COM-base-and-child-unsupported-custom-IRQ-refused-before-EXEC',4)
 for status in [0,7]:
  m=model();path(m,b'TEST.ASX');m.put('connection_state',6);m.child_status=status
  if status:m.keys.append(32)
  assert m.call('terminal_script_start')==0;m.safe();m.restored()
  assert len(m.children)==1 and m.get('terminal_program_status')==(5 if status else 4)
  assert (m.live_prompt_calls>0)==bool(status)
 done('connected-success-resumes-without-key-and-error-retains-serviced-prompt',2)
 for p in [b'',b'..\\T.ASX',b'.\\T.ASX',b'LONGNAME9.ASX',b'T.LONG',b'T A.ASX',b'T.ASX /c',b'CON.ASX',b'D:\\COM1\\T.ASX',b'T;X',b'T".ASX',b'T*',b'D:\\',b'T/ABC']:
  m=model();path(m,p);assert m.call('terminal_script_start')==0;m.keys.append(32);m.safe()
  assert not m.children and m.get('terminal_program_status')==5;m.restored()
 done('invalid-traversal-devices-shellsyntax-and-unbounded-components-denied-before-EXEC',14)
 for fault in ['missing','child-error','trailer','memory']:
  m=model();path(m,b'TEST.ASX')
  if fault=='missing':m.exec_error=2
  if fault=='child-error':m.child_status=7
  if fault=='trailer':m.environment(b'PCPLUS=D:\\WRONG\0\0')
  if fault=='memory':m.resize_error=8
  assert m.call('terminal_script_start')==0;m.keys.append(32);m.safe()
  assert m.get('terminal_program_status')==5 and not m.get('terminal_quit');m.restored()
  if fault=='trailer':assert not m.children and 0x4a not in m.calls
 done('missing-helper-child-error-malformed-trailer-allocation-failure-resume',4)
 m=model();m.keys.extend([0x2c00,ord('a')]);m.poll();m.poll()
 assert m.get('_command_menu_active') and not m.get('terminal_program_pending')
 m.keys.extend(map(ord,'TEST.ASX'));m.keys.append(13)
 for _ in range(9):m.poll()
 assert not m.get('_command_menu_active') and m.get('terminal_program_pending')
 m.keys.append(32);m.safe();assert len(m.children)==1 and m.children[0]['path']==b'D:\\APP\\ASPECT.EXE' and m.children[0]['tail'].startswith(b' TEST.ASX /S1:0003:03:H:');m.restored()
 done('File-menu-Script-prompt-produces-complete-argument-only-after-view-restoration',1)
 m=model();m.keys.extend([0x2c00,ord('a'),ord('T'),27,27])
 for _ in range(5):m.poll()
 assert not m.get('_command_menu_active') and not m.get('terminal_program_pending') and not m.children
 done('Script-filename-Escape-and-menu-Escape-no-child',1)
 for marker in ['terminal_program_pending','terminal_macro_active','terminal_monitor_active','terminal_controller_active','uart_break_hold']:
  m=model();path(m,b'TEST.ASX');m.put(marker,1)
  # Macro owner is guarded in the real transport before Script dispatch.
  if marker=='terminal_macro_active':
   m.keys.append(0xfe00);m.poll();assert not m.get('terminal_program_pending')
  else:assert m.call('terminal_script_start')!=0
  assert not m.children
 done('existing-foreground-owner-admission-refuses-nesting',5)
 m=model();path(m,b'TEST.ASX');m.handback=b'\x1b[2;1HREMAINDER'
 assert m.call('terminal_script_start')==0;m.keys.append(32);m.safe();m.restored()
 assert m.get('uart_rx_count')==len(m.handback)
 while m.get('uart_rx_count'):
  value=m.call('ansi_next_byte');assert value!=0xffff
  m.call('terminal_receive_character',[value],limit=1000000)
 assert bytes(m.uc.mem_read(0xb8000+160,18))[::2]==b'REMAINDER'
 assert m.get('uart_rx_count')==0
 done('child-unread-ASIO-publication-reenters-real-parent-parser-with-exact-bytes',1)
 for state in ['uart_rx_dropped','terminal_parser_active','terminal_ansi_wait_active']:
  m=model();path(m,b'TEST.ASX');m.put(state,1)
  assert m.call('terminal_script_start')==1 and not m.children and not m.get('terminal_program_pending')
 done('parent-RX-loss-parser-wait-state-admission-before-process-owner',3)
 for count,start,entry in [(0,0,0),(17,4090,7),(4096,2047,200)]:
  m=model();path(m,b'TEST.ASX');m.put('uart_rx_count',count)
  m.put('uart_rx_read',m.symbols['uart_rx_buffer']-m.data_base+start)
  if entry:
   m.put('terminal_directory_context_valid',1)
   m.uc.mem_write(m.symbols['terminal_directory_context'],struct.pack('<H',entry))
  assert m.call('terminal_script_start')==0 and prepare_phase(m)==0
  d=descriptor(m)
  capability(d)
  assert d[7:9]==(count,start if count else 0)
  pointer=m.symbols['terminal_directory_context']-m.data_base+252 if entry else 0
  assert d[13:19]==(entry,pointer,0,0,0,0)
  assert d[9]==guard(d)
 done('ASIOv4-retains-wrapped-full-raw-preload-and-selected-directory-in-quiet-parent',3)
 for selected,pending,delta in [(True,True,1),(True,True,0),(True,False,7),(False,True,1)]:
  m=model();path(m,b'TEST.ASX')
  if selected:
   m.put('terminal_directory_context_valid',1)
   m.uc.mem_write(m.symbols['terminal_directory_context'],struct.pack('<H',7))
  m.uc.mem_write(m.symbols['directory_pending'],bytes([int(pending)]))
  for name,value in [('year',2024),('month',2),('day',29),('count',delta)]:
   m.put('directory_pending_'+name,value)
  context=bytes(m.uc.mem_read(m.symbols['terminal_directory_context'],366))
  assert m.call('terminal_script_start')==0 and prepare_phase(m)==0
  d=descriptor(m)
  expected=(2024,2,29,delta) if selected and pending else (0,0,0,0)
  capability(d)
  assert d[15:19]==expected,d
  assert d[9]==guard(d)
  assert bytes(m.uc.mem_read(m.symbols['terminal_directory_context'],366))==context
 done('pending-accounting-projection-guard-preserves-parent-context-including-counter-wrap',4)
 m=model();path(m,b'TEST.ASX');m.put('uart_software_flow',1);m.put('uart_hardware_flow',1)
 assert m.call('terminal_script_start')==0
 # Existing PROGRAM owner first announces XOFF, then waits for physical TEMT.
 m.safe();m.keys.append(32);m.safe()
 assert len(m.children)==1 and b' /S1:0003:03:B:' in m.children[0]['tail']
 assert m.get('uart_software_flow')==m.get('uart_hardware_flow')==1;m.restored()
 done('dual-flow-PRM-state-preserved-by-compact-B-child-lease',1)
 for payload,soft in [(b'PROMPT RX',False),(b'X'*3073,True),(b'X'*4097,False)]:
  m=model();m.mutate_child=False;path(m,b'TEST.ASX');m.put('uart_software_flow',int(soft));injected=[False]
  def irq(u,address,size,unused):
   if address!=m.symbols['terminal_script_return_key'] or injected[0]:return
   injected[0]=True;m.rx.extend(payload);m.keys.append(32)
   ss=u.reg_read(UC_X86_REG_SS);sp=u.reg_read(UC_X86_REG_SP)-6
   cs=u.reg_read(UC_X86_REG_CS);ip=u.reg_read(UC_X86_REG_IP);flags=u.reg_read(UC_X86_REG_EFLAGS)
   u.mem_write(ss*16+sp,struct.pack('<3H',ip,cs,flags&65535));u.reg_write(UC_X86_REG_SP,sp)
   off,seg=m.parent_vector;u.reg_write(UC_X86_REG_CS,seg);u.reg_write(UC_X86_REG_IP,off);u.reg_write(UC_X86_REG_EFLAGS,flags&~0x300)
  m.uc.hook_add(UC_HOOK_CODE,irq)
  assert m.call('terminal_script_start')==0
  if soft:m.safe()
  m.safe();assert injected[0] and m.live_prompt_calls>0
  assert m.get('uart_rx_count')==min(len(payload),4096)
  assert bytes(m.uc.mem_read(m.symbols['uart_rx_buffer'],min(len(payload),4096)))==payload[:4096]
  if len(payload)>4096:assert m.get('terminal_quit')==1 and m.get('terminal_exit_code')==6
  else:assert not m.get('terminal_quit')
  if soft:assert m.get('uart_xoff_sent',1)==1 and bytes(m.tx).endswith(b'\x13')
  m.restored()
 done('actual-IRQ-during-visible-Script-prompt-buffers-bytes-polls-SOFThighwater-reports-overflow',3)
 for key in [0x2d00,0x2300]:
  m=model();path(m,b'TEST.ASX');assert m.call('terminal_script_start')==0;m.keys.append(key);m.safe();m.restored()
  if key==0x2d00:assert m.get('terminal_quit')==1
  else:assert m.get('terminal_deferred_count')==1
 done('serviced-Script-prompt-AltX-quits-and-AltH-defers-until-live-screen-restored',2)
 for mode in [0,1,2]:
  m=model();path(m,b'TEST.ASX');m.put('terminal_translation_mode',mode)
  m.put('terminal_translation_enabled',int(mode==1));m.put('uart_rx_mask',127 if mode==2 else 255)
  m.uc.mem_write(m.symbols['terminal_translation_table'],bytes(i^85 for i in range(256)))
  assert m.call('terminal_script_start')==0;m.keys.append(32);m.safe()
  assert len(m.children)==1 and m.get('terminal_program_status')==4;m.restored()
  d=descriptor(m)
  pointer=m.symbols['terminal_translation_table']-m.data_base if mode==1 else 0
  capability(d)
  assert d[11:19]==(pointer,mode,0,0,0,0,0,0),d
  assert d[9]==guard(d)
 done('ASIOv4-parent-policy-mode-enabled-dequeuemask-and-existing-table-pointer-guard',3)
 for mode,enabled,mask in [(3,0,255),(0,1,255),(1,0,255),(1,1,127),(2,1,127),(2,0,255),(0,0,127)]:
  m=model();path(m,b'TEST.ASX');m.put('terminal_translation_mode',mode)
  m.put('terminal_translation_enabled',enabled);m.put('uart_rx_mask',mask)
  assert m.call('terminal_script_start')==0;m.keys.append(32);m.safe()
  assert not m.children and m.get('terminal_program_status')==5;m.restored()
 done('ASIOv4-inconsistent-mode-enabled-and-UARTmask-denied-before-child',7)
 for offset,value in [(4,2),(20,0),(24,1),(26,1),(28,1),(30,1),(32,2026),(34,10),(36,19),(38,1),(40,1),(42,1),(44,0),(46,2)]:
  m=model();path(m,b'TEST.ASX');m.handoff_tamper=(offset,value)
  assert m.call('terminal_script_start')==0;m.keys.append(32);m.safe()
  assert len(m.children)==1 and m.get('terminal_program_status')==5;m.restored()
 done('ASIOv4-parent-completion-rejects-version-guard-table-mode-and-directory-and-projection-and-capability-mutation',14)
 for stored,want in [(b'LOGON',b'LOGON.ASX'),(b'go.asx',b'GO.ASX'),(b'D:go',b'D:GO.ASX')]:
  m=model();m.put('terminal_directory_context_valid',1);m.put('connection_state',6)
  m.uc.mem_write(m.symbols['terminal_directory_context'],struct.pack('<H',7))
  m.uc.mem_write(m.symbols['terminal_directory_context']+252+52,stored+b'\0')
  m.call('terminal_directory_script_connected')
  assert m.get('terminal_program_pending') and m.get('terminal_program_kind')==4
  tail=bytes(m.uc.mem_read(m.symbols['terminal_translation_edit_tail'],96)).split(b'\0',1)[0]
  assert tail==b' '+want,tail
  m.safe();assert len(m.children)==1 and m.get('terminal_program_status')==4 and not m.live_prompt_calls
  m.restored()
 done('directory-connected-queues-normalized-compiled-script-through-real-foreground-owner',3)
 # Whole owner and complex-glyph admission runs in the real checked quiet
 # PROGRAM phase, with no EXEC/callback substitution or renderer BEGIN.
 for symbol in ['_capture_file_result','_snapshot_file_result','_monitor_file_result','_history_file_result','_printer_device_result']:
  for offset in [10,12]:
   m=model();path(m,b'TEST.ASX');assert m.call('terminal_script_start')==0
   m.uc.mem_write(m.symbols[symbol]+offset,b'\x01\0')
   before=bytes(m.uc.mem_read(m.symbols[symbol],32))
   assert prepare_phase(m)==1 and not m.children
   assert bytes(m.uc.mem_read(m.symbols[symbol],32))==before
 done('checked-quiet-admission-refuses-open-and-uncertain-capture-snapshot-monitor-history-PRN',10)
 for kind in ['attribute-plane','line-flags','unterminated-keyslot','CGA','viewport','complex-mode','BDA-mode','BDA-width','BDA-page','BDA-rows']:
  m=model();path(m,b'TEST.ASX');assert m.call('terminal_script_start')==0
  if kind=='attribute-plane':m.uc.mem_write(m.symbols['screen_attribute_cells']+19,b'\x80')
  if kind=='line-flags':m.uc.mem_write(m.symbols['screen_line_flags']+3,b'\x40')
  if kind=='unterminated-keyslot':m.uc.mem_write(m.symbols['terminal_keymap']+12,b'X'*12)
  if kind=='CGA':m.put('text_cga_status_port',0x3da)
  if kind=='viewport':m.put('screen_viewport_active',1)
  if kind=='complex-mode':m.put('terminal_mode_372c',1)
  if kind=='BDA-mode':m.uc.mem_write(0x449,b'\x07')
  if kind=='BDA-width':m.uc.mem_write(0x44a,struct.pack('<H',40))
  if kind=='BDA-page':m.uc.mem_write(0x462,b'\x01')
  if kind=='BDA-rows':m.uc.mem_write(0x484,b'\x31')
  screen=bytes(m.uc.mem_read(0xb8000,4000))
  assert prepare_phase(m)==1 and not m.children,kind
  assert bytes(m.uc.mem_read(0xb8000,4000))==screen
 done('real-renderer-admission-refuses-complex-glyph-keymap-CGA-viewport-and-BDA-geometry-before-view-mutation',10)
 result=dict(passed=True,binary_sha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),cases=cases,
  inputs=sum(x['inputs'] for x in cases),checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),manifest_sha256=hashlib.sha256((ROOT/'build/terminal/manifest.json').read_bytes()).hexdigest(),sources={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['src/terminal/script_launch.asm','src/terminal/script_launch.c','src/redisplay/command_menu.c','src/terminal/program_actions.asm','src/terminal/config_abi.inc','src/aspect/serial_handoff.h','src/aspect/renderer_policy.c','src/terminal/aspect_renderer.asm','src/terminal/terminal_reset.asm','src/uart/api.asm',__file__.split(str(ROOT)+'/')[-1]]},
  limitations=['DOS EXEC boundary modeled; interpreter semantics and actual child launch require separate DOS test.','The modeled child only publishes unread bytes, never calls BEGIN; no renderer adoption is fabricated. Full child/parent shared renderer execution has separate actual DOS coverage. Capture closes before child; ordinary PROGRAM fallback restores the unadopted old view.'])
 (ROOT/'build/terminal/script-launch-live-checks.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
