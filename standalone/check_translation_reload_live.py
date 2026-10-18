#!/usr/bin/env python3
"""Actual startup selection and same-table foreground reload; model only hardware/DOS."""
import hashlib,json,re,struct
from pathlib import Path
from unicorn.x86_const import UC_X86_REG_AX
from check_live_translation import Translation,IDENTITY,CURRENT
ROOT=Path(__file__).resolve().parents[1]

class Reload(Translation):
 def __init__(self):
  self.on_answer=None
  super().__init__()
 def interrupt(self,u,n,d):
  if n==0x16 and u.reg_read(UC_X86_REG_AX)>>8 in (0,0x10) and self.get('terminal_program_active') and self.on_answer:
   change=self.on_answer;self.on_answer=None;change(self)
  return super().interrupt(u,n,d)
 def bind(self,source=CURRENT,*,fallback=False,explicit=False):
  self.active(1)
  if fallback:self.environment(b'PCPLUS=D:\\ENV\0\0')
  if explicit:
   self.put('terminal_option_mask',self.get('terminal_option_mask')|16384)
   self.uc.mem_write(self.symbols['terminal_translation_path'],b'CUSTOM.XLT\0')
  self.xlt_files[source]=IDENTITY
  assert self.call('terminal_load_translation')==0 and self.table()==IDENTITY
  self.xlt_calls.clear();self.local_text.clear();return self
 def run_reload(self,answer=ord('Y'),*,menu=False,ack=False):
  state=self.get('connection_state')
  if menu:
   self.keys.extend([0x2c00,0x4d00,0x4d00,0x4d00,ord('r')])
   for _ in range(5):self.poll()
  else:self.keys.append(0x7000);self.poll()
  assert self.get('terminal_program_pending') and self.get('terminal_program_kind')==2
  self.keys.append(answer)
  if ack:self.keys.append(32)
  self.safe()
  assert not self.children and 0x4a not in self.calls and 0x4b not in self.calls
  assert not self.get('terminal_program_pending') and not self.get('terminal_program_active')
  self.restored();assert not self.get('terminal_quit') and self.get('connection_state')==state
  assert not self.keys
 def reload_event(self,event,table=0,result=None):
  result=self.offset('terminal_translation_reload_io') if result is None else result
  return self.call('_xlt_live_reload',[event,table,result])

def main():
 groups=[]
 def done(name,n):groups.append(dict(case=name,inputs=n,passed=True));print(name,n,flush=True)
 changed=bytes(reversed(IDENTITY))
 for kind,source in [('default',CURRENT),('fallback',b'D:\\ENV\\PCPLUS.XLT'),('explicit',b'D:\\WORK\\CUSTOM.XLT')]:
  m=Reload().bind(source,fallback=kind=='fallback',explicit=kind=='explicit')
  m.cwd=b'D:\\OTHER';m.environment(b'PCPLUS=D:\\WRONG\0\0')
  m.uc.mem_write(m.symbols['terminal_translation_path'],b'WRONG.XLT\0')
  m.xlt_files[CURRENT]=b'bad';m.xlt_files[b'D:\\OTHER\\PCPLUS.XLT']=b'bad';m.xlt_files[b'D:\\WRONG\\PCPLUS.XLT']=b'bad'
  m.xlt_files[source]=changed;m.run_reload(menu=kind=='default')
  assert m.table()==changed and m.get('terminal_translation_reload_status')==2
  assert [c[1] for c in m.xlt_calls if c[0]==0x3d]==[source]
  assert m.get('terminal_translation_mode')==m.get('terminal_translation_enabled')==1 and m.get('uart_rx_mask')==255
 done('actual-default-fallback-explicit-source-frozen-across-CWD-env-CLI-changes-menu-and-AltF9',3)
 for key in (ord('N'),27,32,13):
  m=Reload().bind();m.xlt_files[CURRENT]=changed;m.run_reload(key)
  assert m.table()==IDENTITY and m.get('terminal_translation_reload_status')==3
  assert m.reload_event(1,m.offset('terminal_translation_table'))==7
 done('four-declines-discard-reload-stage-without-changing-active-table',4)
 m=Reload().bind();m.xlt_files[CURRENT]=changed
 m.on_answer=lambda model:model.xlt_files.__setitem__(CURRENT,bytes(256))
 m.run_reload();assert m.table()==changed and len([c for c in m.xlt_calls if c[0]==0x3d])==1
 done('confirmation-accepts-checked-snapshot-without-second-read-after-disk-change',1)
 for fault in ('missing','empty','short','suffix','read','probe','close','access'):
  m=Reload().bind();m.xlt_files[CURRENT]={'empty':b'','short':bytes(255),'suffix':bytes(257)}.get(fault,changed)
  if fault=='missing':
   del m.xlt_files[CURRENT];m.environment(b'PCPLUS=D:\\ENV\0\0');m.xlt_files[b'D:\\ENV\\PCPLUS.XLT']=changed
  if fault in ('read','probe','close'):m.xlt_fault=fault
  if fault=='access':m.xlt_open_error=5
  m.run_reload(32);assert m.table()==IDENTITY and m.get('terminal_translation_reload_status')==5
  assert b'old table retained' in m.local_text
  assert m.reload_event(1,m.offset('terminal_translation_table'))==7
 done('missing-empty-short-suffix-read-probe-close-access-failures-retain-active-table',8)
 m=Reload().bind();del m.xlt_files[CURRENT];m.run_reload(32)
 m.xlt_files[CURRENT]=changed;m.run_reload();assert m.table()==changed
 done('failed-reload-retains-selected-source-for-later-successful-retry',1)
 flags=['terminal_parser_active','terminal_macro_active','terminal_transfer_pending','terminal_transfer_active',
  'terminal_monitor_active','terminal_controller_active','terminal_snapshot_active','terminal_ansi_wait_active','_redisplay_active']
 for marker in flags:
  m=Reload().bind();m.put(marker,1)
  assert m.call('terminal_translation_reload_start')==1
  assert not m.get('terminal_program_pending') and m.table()==IDENTITY and not m.xlt_calls
 for mode in (0,2):
  m=Reload().bind();m.put('terminal_translation_mode',mode)
  assert m.call('terminal_translation_reload_start')==1 and not m.get('terminal_program_pending') and not m.xlt_calls
 done('all-local-owners-and-nontable-modes-refuse-before-DOS-or-program-scheduling',len(flags)+2)
 for marker in flags:
  m=Reload().bind();m.xlt_files[CURRENT]=changed
  m.on_answer=lambda model,name=marker:model.put(name,1)
  m.run_reload(ack=True);assert m.table()==IDENTITY and m.get('terminal_translation_reload_status')==6
  assert m.reload_event(1,m.offset('terminal_translation_table'))==7
 done('late-owner-change-at-real-BIOS-answer-cancels-stage-before-commit',len(flags))
 m=Reload().bind();m.xlt_files[CURRENT]=changed
 assert m.reload_event(0)==0
 for event,table,result in [(3,0,None),(0,1,None),(2,1,None),(1,0,None),(1,0xff01,None),(0,0,0),(0,0,0xfffc),(1,m.offset('terminal_translation_table'),m.offset('terminal_translation_table'))]:
  assert m.reload_event(event,table,result)==1 and m.table()==IDENTITY
 assert m.reload_event(1,m.offset('terminal_translation_table'))==0 and m.table()==changed
 assert m.reload_event(1,m.offset('terminal_translation_table'))==7
 done('eight-invalid-API-frames-preserve-valid-stage-and-accept-consumes-once',9)
 m=Reload().bind();io=m.offset('terminal_translation_reload_io');table=m.offset('terminal_translation_table')
 m.xlt_files[CURRENT]=changed
 assert m.call('_xlt_live_bind',[m.get('process_psp')])==0
 assert m.call('_xlt_live_stage',[1,io])==0 and m.reload_event(2)==0
 assert m.call('_xlt_live_commit',[1,table])==0 and m.table()==changed
 done('reload-cancel-does-not-discard-an-unrelated-settings-stage',1)
 m=Reload().bind();m.xlt_files[CURRENT]=changed;m.put('connection_state',6)
 m.receive_irq(b'L');reads=m.data_reads;m.run_reload()
 assert m.get('connection_state')==6 and m.get('uart_rx_count')==1 and m.data_reads==reads
 assert m.call('uart_receive_byte')==ord('L') and m.call('terminal_translate_input',ax=ord('L'))==255-ord('L')
 done('established-connection-and-queued-raw-input-retained-until-new-table-is-accepted',1)
 m=Reload().bind();m.xlt_files[CURRENT]=changed;m.put('uart_software_flow',1);m.put('uart_hardware_flow',0)
 m.enqueue(b'REPLY');assert m.call('terminal_translation_reload_start')==0
 m.safe();assert m.get('terminal_program_pending') and not m.xlt_calls
 while m.get('terminal_tx_count'):m.poll()
 m.safe();assert bytes(m.tx)==b'REPLY\x13' and not m.xlt_calls
 m.temt=False;m.safe();assert m.get('terminal_program_pending') and not m.xlt_calls
 m.temt=True;m.keys.append(ord('Y'));m.safe();m.poll();m.restored()
 assert bytes(m.tx)==b'REPLY\x13\x11' and m.table()==changed and not m.keys
 done('queued-TX-and-physical-XOFF-TEMT-drain-before-DOS-and-owned-XON-after-return',1)
 for kind in ('cancel','timeout'):
  m=Reload().bind();assert m.call('terminal_translation_reload_start')==0
  if kind=='cancel':m.call('terminal_program_cancel')
  else:m.temt=False;m.safe(m.tick+36)
  assert not m.get('terminal_program_pending') and m.get('terminal_translation_reload_status')==4
  assert not m.xlt_calls and m.table()==IDENTITY
 done('canceled-or-timed-out-foreground-request-does-not-stage-or-replace-table',2)
 for name,value in [('terminal_translation_enabled',0),('uart_rx_mask',127)]:
  m=Reload().bind();m.put(name,value)
  assert m.call('terminal_translation_reload_start')==1 and not m.get('terminal_program_pending') and not m.xlt_calls
 done('inconsistent-enabled-or-driver-mask-refuses-before-foreground-handoff',2)
 for bad in range(8):
  m=Reload().bind();table=m.offset('terminal_translation_table');io=m.offset('terminal_translation_reload_io')
  args=[m.get('process_psp'),1,0,table,io]
  if bad==0:args[1]=3
  if bad==1:args[1]=65535
  if bad==2:args[3]=0
  if bad==3:args[3]=0xff01
  if bad==4:args[4]=0
  if bad==5:args[4]=0xfffc
  if bad==6:args[4]=table
  if bad==7:args[1]=2;args[2]=m.offset('terminal_translation_path')
  assert m.call('_xlt_live_initialize',args)==1 and m.table()==IDENTITY and not m.xlt_calls
  m.xlt_files[CURRENT]=changed;assert m.reload_event(0)==0
  assert m.reload_event(1,table)==0 and m.table()==changed
 done('eight-invalid-startup-initializer-frames-preserve-active-binding-and-table',8)
 m=Reload();listing=(ROOT/'build/terminal/terminal.map').read_text()
 segment,offset,size=re.search(r'^_BSS\s+BSS\s+DGROUP\s+([0-9a-f]+):([0-9a-f]+)\s+([0-9a-f]+)',listing,re.M|re.I).groups()
 m.uc.mem_write(m.base+int(segment,16)*16+int(offset,16),b'\xa5'*int(size,16));before=m.table()
 assert m.reload_event(0)==7 and m.reload_event(1,m.offset('terminal_translation_table'))==7
 assert m.table()==before and not m.xlt_calls
 done('serialized-active-source-guard-rejects-reload-with-poisoned-DOS-BSS',2)
 m=Reload().bind();m.xlt_files[CURRENT]=changed;m.enqueue(b'REPLY')
 m.keys.append(0x7000);m.poll();assert m.get('terminal_program_pending')
 for key in (ord('Y'),ord('Z')):m.keys.append(key);m.poll()
 assert m.get('terminal_deferred_count')==2 and not m.keys
 while m.get('terminal_tx_count'):m.poll()
 m.safe();m.restored();assert m.table()==changed and m.get('terminal_deferred_count')==1
 m.poll();m.poll();assert bytes(m.tx)==b'REPLYZ' and not m.get('terminal_deferred_count')
 m.call('terminal_program_cancel');assert m.get('terminal_translation_reload_status')==2
 done('early-confirmation-is-consumed-from-drain-typeahead-and-following-key-keeps-order',1)
 for key,fault,want in [(0,None,3),(32,'missing',5)]:
  m=Reload().bind()
  if fault:del m.xlt_files[CURRENT]
  assert m.call('terminal_translation_reload_start')==0
  m.call('terminal_defer_key',ax=key);m.safe();m.restored()
  assert m.table()==IDENTITY and m.get('terminal_translation_reload_status')==want
  assert not m.keys and not m.get('terminal_deferred_count') and not m.get('terminal_program_active')
 done('zero-valued-typeahead-and-buffered-failure-acknowledgement-do-not-block-BIOS',2)
 result=dict(passed=True,binary_sha256=hashlib.sha256((ROOT/'build/terminal/TERMINAL.EXE').read_bytes()).hexdigest(),
  inputs=sum(c['inputs'] for c in groups),cases=groups,sources={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in
  ['standalone/check_translation_reload_live.py','standalone/check_live_translation.py','standalone/live_setup_kernel.py','standalone/check_program_actions_live.py',
   'src/translation/xlt_live.c','src/translation/xlt_live.h','src/terminal/translation.asm','src/terminal/meta_actions.asm','src/terminal/translation_reload.asm','src/terminal/program_actions.asm','src/terminal/transport.asm','src/redisplay/command_menu.c']},
  scope='Actual linked startup canonical selection and explicit reload, C staging, configuration far frames, menu/keyboard dispatch, PROGRAM UART/IRQ/video handoff and real BIOS answers. Only hardware/DOS boundaries modeled. Late state/disk changes occur at the BIOS boundary; no product function replaced. Actual DOS workflow remains separate.')
 (ROOT/'build/terminal/translation-reload-checks.json').write_text(json.dumps(result,indent=2)+'\n')
 print('Translation reload passed',result['inputs'])
if __name__=='__main__':main()
