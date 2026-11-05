#!/usr/bin/env python3
"""Linked Gateway scheduler/guards/frame return with modeled DOS/BIOS/UART."""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn.x86_const import *
from unicorn import UC_HOOK_CODE
import check_transport as transport
from check_process import Kernel
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
 binary=a.terminal.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();manifest=json.loads(binary.with_name('manifest.json').read_text())
 assert manifest['experimental_gateway_frontend'] and sha(binary)==manifest['binary_sha256']
 for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 transport.BINARY=binary;transport.MAP=binary.with_name('terminal.map')
 from program_display_model import Program
 class Front(Program):
  def __init__(self,rows=25):
   super().__init__();self.setup(rows);self.pic&=~1;self.put('hardware_active',1,1);self.put('vector_active',1,1)
   self.environment(b'COMSPEC=Z:\\COMMAND.COM\0PATH=Z:\\\0\0',segment=0x9000)
   self.child_fault='';self.exited=None;self.retained=False
  def interrupt(self,u,n,d):
   if n==0x21 and u.reg_read(UC_X86_REG_AX)>>8==0x51:u.reg_write(UC_X86_REG_BX,self.dos_psp);return
   if n==0x21 and u.reg_read(UC_X86_REG_AX)>>8==0x31:self.retained=True;self.exited=u.reg_read(UC_X86_REG_AX)&255;u.emu_stop();return
   if n==0x21 and u.reg_read(UC_X86_REG_AX)>>8==0x4c:self.exited=u.reg_read(UC_X86_REG_AX)&255;u.emu_stop();return
   if n==0x21 and u.reg_read(UC_X86_REG_AX)==0x4b00:
    assert self.ier==9 and not self.pic&self.irq_mask and self.get('terminal_program_kind')==9
    Kernel.interrupt(self,u,n,d)
    if not self.exec_error:
     self.mode=0x13;self.page=2;self.cursor=0x1401;self.shape=0x2020;u.mem_write(0xb8000,b'\xff'*8000)
     if self.child_fault=='files':u.mem_write(self.symbols['_gateway_files_storage']+4,b'\1\0')
     if self.child_fault=='serial':self.lcr=0x9e;self.ier=0;self.mcr=3
     if self.child_fault=='overflow':self.overrun=True
     if self.child_fault=='display':self.font_refusals=2
     if self.child_fault=='mouse':self.mouse_boundary.present=False
     if self.child_fault=='carrier':self.carrier=False
    return
   return super().interrupt(u,n,d)
  def front(self,name):return self.far_entry('_gateway_'+name)
  def state(self):return struct.unpack('<8HI',self.uc.mem_read(self.symbols['_gateway_front_storage'],20))
  def ticks(self,value):self.uc.mem_write(0x46c,struct.pack('<I',value))
  def shutdown(self):
   u=self.uc
   for r,v in [(UC_X86_REG_CS,self.code_segment),(UC_X86_REG_DS,self.ds),(UC_X86_REG_SS,self.ds),(UC_X86_REG_SP,self.offset('terminal_stack_top')-4),(UC_X86_REG_EFLAGS,0x202)]:u.reg_write(r,v)
   u.emu_start(self.symbols['terminal_shutdown'],0,count=5000000)
   at=u.reg_read(UC_X86_REG_CS)*16+u.reg_read(UC_X86_REG_IP)
   assert self.exited is not None,dict(at=hex(at),near=sorted(((abs(a-at),n,hex(a)) for n,a in self.symbols.items()))[:6],registers={str(r):u.reg_read(r) for r in (UC_X86_REG_CS,UC_X86_REG_IP,UC_X86_REG_SP,UC_X86_REG_AX)})
 out.mkdir(parents=True);cases=[]
 def record(name,**details):cases.append(dict(case=name,passed=True,**details))
 for rows in (25,28,43,50):
  m=Front(rows);assert m.front('start')==0 and m.get('terminal_program_pending')==1 and m.get('terminal_program_kind')==9
  m.front('poll');assert not m.get('terminal_quit') and m.get('terminal_program_status')==4,(rows,m.state(),m.children,m.get('terminal_exit_code'))
  m.verify(rows);assert len(m.children)==1 and m.children[0]=={'path':b'Z:\\COMMAND.COM','tail':b''} and not m.keys
  assert m.front('quarantined')==0
  record('actual-scheduler-graphics-child-'+str(rows))
 m=Front(43)
 for _ in range(3):
  assert m.front('start')==0;m.front('poll');m.verify(43)
 assert len(m.children)==3;record('same-process-three-Gateway-roundtrips')
 for lost in (False,True):
  m=Front();m.put('connection_state',6);m.put('connection_carrier_seen',1,1);m.put('terminal_directory_mode',0)
  if lost:m.child_fault='carrier'
  assert m.front('start')==0;m.front('poll');assert not m.get('terminal_quit') and m.get('connection_state')==6
  if lost:
   m.tick=4;m.call('terminal_connection_poll');assert m.get('connection_state')==0 and m.get('connection_status')==6 and not m.get('terminal_quit')
  else:m.verify(25)
  record('connected-return-'+('qualified-DCD-loss' if lost else 'live-carrier'))
 for fault in ('exec','resize','environment'):
  m=Front();
  if fault=='exec':m.exec_error=2
  elif fault=='resize':m.resize_error=8
  else:m.environment(b'PATH=Z:\\\0\0',segment=0x9000)
  assert m.front('start')==0;m.front('poll')
  assert not m.get('terminal_quit') and not m.get('terminal_program_active') and not m.get('terminal_program_pending') and m.get('terminal_program_status')==5 and m.front('quarantined')==0
  assert m.mode==3 and m.vrows==25 and m.vector_value()==m.parent_vector and m.ier==1 and not m.pic&m.irq_mask
  record('failed-'+fault+'-restores-live-terminal')
 guards=['terminal_program_pending','terminal_program_active','terminal_aspect_active','terminal_parser_active','terminal_macro_active','terminal_ansi_wait_active','terminal_monitor_active','terminal_snapshot_active','terminal_screen_print_active','terminal_controller_active','terminal_transfer_active','terminal_transfer_pending','uart_break_hold','_redisplay_active','_redisplay_live_ready','_redisplay_export_pending','_redisplay_search_pending','_command_menu_active','_terminal_elapsed_view_active','terminal_screen_pause_active','terminal_manual_init_active','_clipboard_ui_active','_clipboard_ui_visible','_clipboard_paste_pending','terminal_menu_pending','_terminal_status_toggle_active','_terminal_row_geometry_active','_program_display_ready','reset_bank_busy','terminal_auto_answer_notice_active','terminal_script_overlay_visible']
 for field in guards:
  m=Front();m.put(field,1);video=bytes(m.uc.mem_read(0xb8000,4000));assert m.front('start')==2 and not m.children and bytes(m.uc.mem_read(0xb8000,4000))==video,field
  record('guard-'+field)
 for field in ('terminal_browser_screen_owned','terminal_editor_screen_owned','hardware_active','vector_active'):
  m=Front();m.put(field,0 if field in ('hardware_active','vector_active') else 1,1);assert m.front('start')==2 and not m.children;record('guard-'+field)
 for kind,value in [('mode',0x13),('columns',40),('page',1)]:
  m=Front();setattr(m,kind,value);assert m.front('start')==2 and not m.children;record('guard-BIOS-'+kind)
 for state in (1,2,3,4,5):
  m=Front();m.put('connection_state',state);assert m.front('start')==2 and not m.children;record('guard-connection-'+str(state))
 m=Front();m.pic|=1;assert m.front('start')==2 and not m.children;record('guard-masked-timer')
 m=Front();assert m.front('start')==0;m.put('terminal_parser_active',1);m.front('poll');assert not m.get('terminal_program_pending') and not m.children and not m.get('terminal_quit');record('launch-revalidates-parser')
 m=Front();m.put('terminal_tx_count',1);assert m.front('start')==0;progress=m.state()[-1]
 m.ticks(20);assert m.front('start')==0 and m.state()[-1]==progress
 m.ticks(35);m.front('poll');assert m.get('terminal_program_pending') and not m.children
 m.ticks(36);m.front('poll');assert not m.get('terminal_program_pending') and m.get('terminal_tx_count')==1 and m.get('terminal_program_status')==8 and not m.children
 record('idempotent-request-bounded-TX-wait-without-dropping-output')
 m=Front();m.put('terminal_tx_count',1);assert m.front('start')==0;m.ticks(35);m.put('terminal_macro_tx_epoch',1);m.front('poll');assert m.state()[-1]==35
 m.ticks(70);m.front('poll');assert m.get('terminal_program_pending');m.ticks(71);m.front('poll');assert not m.get('terminal_program_pending');record('TX-progress-rearms-deadline')
 m=Front();m.put('terminal_printer_count',3);assert m.front('start')==0;m.ticks(35);m.put('terminal_printer_count',2);m.front('poll');assert m.state()[-1]==35 and not m.children
 m.put('terminal_printer_fault_epoch',1);m.front('poll');assert not m.get('terminal_program_pending') and not m.children;record('printer-progress-and-new-drain-failure')
 m=Front();m.put('terminal_tx_count',1);m.ticks(0x1800b0-10);assert m.front('start')==0;m.ticks(9);m.front('poll');assert m.get('terminal_program_pending');m.ticks(26);m.front('poll');assert not m.get('terminal_program_pending');record('BIOS-midnight-deadline')
 m=Front();assert m.front('start')==0;m.call('terminal_program_cancel');m.front('poll');assert not m.children and m.front('start')==0;record('cancel-and-requeue')
 m=Front();m.put('terminal_tx_count',2);assert m.front('start')==0;m.keys.append(ord('q'));m.call('terminal_poll_io');assert list(m.keys)==[ord('q')] and ord('q') not in m.tx
 m.call('terminal_program_poll');assert m.get('terminal_program_pending') and not m.children;record('pending-typeahead-and-separate-PROGRAM-policy')
 for fault,code in [('files',18),('serial',19),('overflow',6),('display',2),('mouse',14)]:
  m=Front(43);m.child_fault=fault
  if fault=='mouse':
   m.start_mouse();m.environment(b'COMSPEC=Z:\\COMMAND.COM\0PATH=Z:\\\0\0',segment=0x9800)
  if fault=='files':
   # Model the pre-application IRQ target in ROM, outside the owned MCB.
   m.old_vector=(0x5678,0xf000);m.put('uart_previous_irq_segment',0xf000)
   m.uc.mem_write(m.dos_psp*16,b'\xcd\x20');m.uc.mem_write((m.dos_psp-1)*16,struct.pack('<BHH',ord('M'),m.dos_psp,0x8000));m.far_entry('terminal_exit_guard_begin');assert m.get('terminal_exit_guard_valid')==1
  assert m.front('start')==0;m.front('poll');assert m.get('terminal_quit') and m.get('terminal_exit_code')==code,(fault,m.state(),m.get('terminal_exit_code'))
  assert bool(m.front('quarantined'))==(fault=='files'),fault
  if fault=='files':
   events=[];names=['_terminal_autostart_flush','terminal_redisplay_stop','terminal_printer_shutdown','_terminal_phone_log_events_shutdown_far','terminal_transfer_shutdown','terminal_monitor_shutdown','_capture_session_shutdown','_recording_terminal_shutdown','terminal_directory_flush_accounting']
   targets={m.symbols[n]:n for n in names if n in m.symbols}
   def trace(u,address,size,data):
    if address in targets:events.append(targets[address])
   hook=m.uc.hook_add(UC_HOOK_CODE,trace)
   try:m.shutdown()
   finally:m.uc.hook_del(hook)
   assert not events and m.exited==15 and m.retained and m.get('terminal_exit_code')==18 and m.get('terminal_exit_guard_reason')==2 and m.vector_value()==m.old_vector and not m.get('hardware_active',1),dict(events=events,exited=m.exited,retained=m.retained,code=m.get('terminal_exit_code'),reason=m.get('terminal_exit_guard_reason'),vector=m.vector_value(),old_vector=m.old_vector,hw=m.get('hardware_active',1))
  record('fault-'+fault,exit_code=code)
 result=dict(passed=True,binary_sha256=sha(binary),cases=cases,original_inputs=[],scope=__doc__,sources={n:sha(ROOT/n) for n in ['standalone/check_gateway_front.py','standalone/program_display_model.py','standalone/check_row_geometry_live.py','standalone/check_program_actions_live.py','standalone/check_transport.py','standalone/check_process.py']})
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS',len(cases),'Gateway frontend cases')
if __name__=='__main__':main()
