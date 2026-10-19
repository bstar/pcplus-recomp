#!/usr/bin/env python3
"""Execute direct editor scheduling, DOS EXEC and checked post-child adoption."""
import hashlib,json,struct
from pathlib import Path
from unicorn.x86_const import UC_X86_REG_AX
from check_translation_reload_live import Reload,IDENTITY,CURRENT,ROOT

class Editor(Reload):
 def __init__(self):
  self.edited=None;self.edited_source=CURRENT
  super().__init__()
 def install_program_name(self,program=b'D:\\APP\\TERMINAL.EXE',entries=b'PCPLUS=D:\\ENV\0'):
  self.environment(entries+(b'\0' if entries else b'\0\0')+b'\x01\0'+program+b'\0')
 def interrupt(self,u,n,d):
  ax=u.reg_read(UC_X86_REG_AX)
  answer=super().interrupt(u,n,d)
  if n==0x21 and ax==0x4b00 and not self.exec_error and self.edited is not None:
   self.xlt_files[self.edited_source]=self.edited
  return answer
 def launch_editor(self,answer=ord('Y'),menu=False,ack=False):
  if menu:
   self.keys.extend([0x2c00,0x4d00,0x4d00,0x4d00,ord('t')])
   for _ in range(5):self.poll()
  else:self.keys.append(0x6f00);self.poll()
  assert self.get('terminal_program_pending') and self.get('terminal_program_kind')==3
  self.keys.append(answer)
  if ack:self.keys.append(32)
  self.safe()
  assert not self.get('terminal_program_active') and not self.get('terminal_program_pending')
  self.restored();assert not self.keys and not self.get('terminal_quit')

def main():
 cases=[]
 def done(name,n):cases.append(dict(case=name,inputs=n,passed=True));print(name,n,flush=True)
 changed=bytes(reversed(IDENTITY))
 for kind,source in [('default',CURRENT),('fallback',b'D:\\ENV\\PCPLUS.XLT'),('explicit',b'D:\\WORK\\CUSTOM.XLT')]:
  for accept in [True,False]:
   m=Editor().bind(source,fallback=kind=='fallback',explicit=kind=='explicit');m.install_program_name()
   m.cwd=b'D:\\OTHER';m.edited_source=source;m.edited=changed
   m.launch_editor(ord('Y') if accept else ord('N'),menu=kind=='default')
   assert m.children==[dict(path=b'D:\\APP\\XLTEDIT.EXE',tail=b' "'+source+b'"')]
   assert m.table()==(changed if accept else IDENTITY)
   assert m.get('terminal_translation_edit_status')==(2 if accept else 3)
   assert m.get('terminal_translation_mode')==m.get('terminal_translation_enabled')==1 and m.get('uart_rx_mask')==255
   assert [c[1] for c in m.xlt_calls if c[0]==0x3d]==[source]
 done('exact-selected-default-fallback-explicit-path-direct-sibling-executable-menu-and-confirmation',6)
 for fault in ['missing-child','memory','child-exit','missing-table','short-table','close-table','trailer']:
  m=Editor().bind();m.install_program_name();m.edited=changed
  if fault=='missing-child':m.exec_error=2
  if fault=='memory':m.resize_error=8
  if fault=='child-exit':m.child_status=9
  if fault=='missing-table':m.edited=None;del m.xlt_files[CURRENT]
  if fault=='short-table':m.edited=bytes(255)
  if fault=='close-table':m.xlt_fault='close'
  if fault=='trailer':m.environment(b'PCPLUS=D:\\WRONG\0\0')
  m.launch_editor(32)
  assert m.table()==IDENTITY
  assert m.get('terminal_translation_edit_status')==(5 if fault in ('missing-table','short-table','close-table') else 7)
  if fault in ('missing-child','memory','child-exit','trailer'):assert not m.xlt_calls
  if fault=='trailer':assert not m.children and 0x4a not in m.calls
 done('EXEC-allocation-child-exit-malformed-environment-and-post-child-read-failures-retain-active-table',7)
 for marker in ['terminal_parser_active','terminal_macro_active','terminal_transfer_pending','terminal_transfer_active','terminal_monitor_active','terminal_controller_active','terminal_snapshot_active','terminal_ansi_wait_active','_redisplay_active']:
  m=Editor().bind();m.install_program_name();m.put(marker,1)
  assert m.call('terminal_translation_edit_start')==1 and not m.get('terminal_program_pending') and not m.children
 for mode in [0,2]:
  m=Editor().bind();m.put('terminal_translation_mode',mode)
  assert m.call('terminal_translation_edit_start')==1 and not m.get('terminal_program_pending')
 done('local-owner-and-nontable-modes-refuse-before-execution',11)
 m=Editor().bind();m.install_program_name();assert m.call('terminal_translation_edit_start')==0
 m.call('terminal_program_cancel');assert m.get('terminal_translation_edit_status')==4 and not m.children
 done('pending-editor-cancel-does-not-execute-or-read-table',1)
 m=Editor().bind();m.install_program_name();m.xlt_files[CURRENT]=changed
 assert m.call('_xlt_live_stage',[1,m.offset('terminal_translation_reload_io')])==0
 exe=m.offset('terminal_translation_edit_executable');tail=m.offset('terminal_translation_edit_tail')
 assert m.call('_xlt_live_editor',[m.get('process_psp'),exe,tail])==0
 assert m.call('_xlt_live_commit',[1,m.offset('terminal_translation_table')])==0 and m.table()==changed
 done('command-construction-preserves-unrelated-settings-stage',1)
 m=Editor().bind();m.install_program_name();m.edited=changed;m.put('connection_state',6)
 m.launch_editor();assert m.get('connection_state')==6 and m.table()==changed and not m.tx
 done('established-connection-remains-connected-through-direct-editor',1)
 m=Editor().bind();m.install_program_name();m.edited=changed
 m.on_answer=lambda model:model.put('terminal_parser_active',1)
 m.launch_editor(ack=True);assert m.table()==IDENTITY and m.get('terminal_translation_edit_status')==6
 done('late-owner-change-after-child-refuses-staged-table-adoption',1)
 # Strict DOS3 trailer bounds and helper-name construction, with no fallback.
 malformed=[b'A'*512,b'\0A'+b'X'*30,b'\0\0\0\0D:\\T.EXE\0',
  b'\0\0\x02\0D:\\T.EXE\0',b'\0\0\0\x01D:\\T.EXE\0',
  b'\0\0\x01\0TERMINAL.EXE\0',b'\0\0\x01\0D:T.EXE\0',
  b'\0\0\x01\0D:\\APP\\\0',b'\0\0\x01\0D:\\A?\\T.EXE\0',
  b'\0\0\x01\0D:\\A"\\T.EXE\0']
 for data in malformed:
  m=Editor().bind();m.environment(data);exe=m.offset('terminal_translation_edit_executable');tail=m.offset('terminal_translation_edit_tail')
  m.uc.mem_write(m.data_base+exe,b'\xa5'*132)
  assert m.call('_xlt_live_editor',[m.get('process_psp'),exe,tail])==6
  assert bytes(m.uc.mem_read(m.data_base+exe,132))==b'\xa5'*132 and not m.children and not m.xlt_calls
 done('malformed-truncated-and-unqualified-DOS-environment-trailers-preserve-outputs',len(malformed))
 for kind in ['PSP0','PSPFFFF','absent','signature','zero-size','physical-overflow']:
  m=Editor().bind();m.install_program_name();psp=m.get('process_psp');segment=0x7000
  if kind=='PSP0':psp=0
  if kind=='PSPFFFF':psp=65535
  if kind=='absent':m.uc.mem_write(psp*16+0x2c,b'\0\0')
  if kind=='signature':m.uc.mem_write((segment-1)*16,b'!')
  if kind=='zero-size':m.uc.mem_write((segment-1)*16+3,b'\0\0')
  if kind=='physical-overflow':m.uc.mem_write((segment-1)*16+3,b'\xff\xff')
  exe=m.offset('terminal_translation_edit_executable');tail=m.offset('terminal_translation_edit_tail');m.uc.mem_write(m.data_base+exe,b'\xa5'*132)
  assert m.call('_xlt_live_editor',[psp,exe,tail])==6
  assert bytes(m.uc.mem_read(m.data_base+exe,132))==b'\xa5'*132 and not m.xlt_calls
 done('invalid-PSP-environment-MCB-shape-size-and-physical-extent',6)
 for extra,want in [(b'ABC',0),(b'ABCD',6)]:
  m=Editor().bind();program=b'D:\\'+b'ABCDEFGH\\'*5+extra+b'\\T.EXE';m.install_program_name(program,entries=b'')
  exe=m.offset('terminal_translation_edit_executable');tail=m.offset('terminal_translation_edit_tail');m.uc.mem_write(m.data_base+exe,b'\xa5'*132)
  assert m.call('_xlt_live_editor',[m.get('process_psp'),exe,tail])==want
  if not want:assert len(bytes(m.uc.mem_read(m.data_base+exe,64)).split(b'\0')[0])==63
  else:assert bytes(m.uc.mem_read(m.data_base+exe,132))==b'\xa5'*132
 done('empty-environment-and-helper-path-63-byte-boundary',2)
 for source in [b'D:\\'+b'ABCDEFGH\\'*6+b'TT.XLT',b'D:\\WORK\\T\x82ST.XLT']:
  m=Editor();m.active(1);m.put('terminal_option_mask',m.get('terminal_option_mask')|16384)
  m.uc.mem_write(m.symbols['terminal_translation_path'],source+b'\0');m.xlt_files[source]=IDENTITY
  assert m.call('terminal_load_translation')==0;m.install_program_name(b'D:\\APP\x82\\TERMINAL.EXE')
  exe=m.offset('terminal_translation_edit_executable');tail=m.offset('terminal_translation_edit_tail')
  assert m.call('_xlt_live_editor',[m.get('process_psp'),exe,tail])==0
  assert bytes(m.uc.mem_read(m.data_base+tail,68)).split(b'\0')[0]==b' "'+source+b'"'
  assert bytes(m.uc.mem_read(m.data_base+exe,64)).split(b'\0')[0]==b'D:\\APP\x82\\XLTEDIT.EXE'
 done('maximum-selected-table-path-and-raw-CP437-table-and-program-directories',2)
 # The command builder is independent of any DOS call, and never consumes a
 # separate already-staged settings transaction.
 m=Editor().bind();m.install_program_name();exe=m.offset('terminal_translation_edit_executable');tail=m.offset('terminal_translation_edit_tail')
 assert m.call('_xlt_live_editor',[m.get('process_psp'),exe,tail])==0
 for a,b in [(0,tail),(0xffc1,tail),(exe,0xffbd),(exe,exe),(exe,exe+63),(tail,tail)]:
  before=bytes(m.uc.mem_read(m.data_base+exe,132));assert m.call('_xlt_live_editor',[m.get('process_psp'),a,b])==1
  assert bytes(m.uc.mem_read(m.data_base+exe,132))==before
 done('external-nonwrapping-disjoint-command-builder-outputs',7)
 result=dict(passed=True,binary_sha256=hashlib.sha256((ROOT/'build/terminal/TERMINAL.EXE').read_bytes()).hexdigest(),inputs=sum(c['inputs'] for c in cases),cases=cases,
  sources={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['standalone/check_translation_edit_live.py','src/terminal/translation_edit.asm','src/terminal/program_actions.asm','src/translation/xlt_live.c','src/config/resource_path.c','src/redisplay/command_menu.c']},
  scope='Actual linked command construction, direct near/far calls, scheduling, DOS EXEC backend, quiet UART and confirmation/reader paths. Only DOS kernel, BIOS, UART and child execution boundaries modeled. Actual production editor/DOS media workflows remain separate; no physical modem or whole-application claim.')
 (ROOT/'build/terminal/translation-edit-checks.json').write_text(json.dumps(result,indent=2)+'\n');print('Translation editor checks passed',result['inputs'])
if __name__=='__main__':main()
