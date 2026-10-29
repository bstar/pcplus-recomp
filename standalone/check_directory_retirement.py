#!/usr/bin/env python3
"""Execute retirement admission/cancel and pure setup-context/namespace APIs."""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn.x86_const import *
from check_directory_identity import Identity
from check_setup_model import image
from check_directory_live import serial_expected
from directory_fixtures import directory
from terminal_memory import inspect_terminal_memory
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
class Retirement(Identity):
 def __init__(self,binary):
  super().__init__(binary,reply=b'D:\\BASE\\TEST.PRM');self.bios=[];self.calendar=[]
 def interrupt(self,u,n,data):
  ax=u.reg_read(UC_X86_REG_AX)
  if n==0x1a and ax>>8==0:
   self.bios.append(ax);u.reg_write(UC_X86_REG_CX,0);u.reg_write(UC_X86_REG_DX,100);return
  if n==0x21 and ax>>8==0x2a:
   self.calendar.append(ax);u.reg_write(UC_X86_REG_CX,2026);u.reg_write(UC_X86_REG_DX,10<<8|29);return
  return super().interrupt(u,n,data)
 def fixture(self):
  self.configured();raw=directory();context=struct.pack('<H',1)+raw[:250]+raw[250:364]+bytes(2)+b'TEST.PRM\0'+bytes(55)+b'D:\\TEST.DIR\0'+bytes(52)
  assert len(context)==496;self.uc.mem_write(self.symbols['terminal_directory_context'],context)
  serial=serial_expected(image(),raw[250:364]);self.uc.mem_write(self.symbols['terminal_configuration_values'],serial)
  self.put('terminal_option_mask',16|64)
  self.put('process_psp',0xff0);self.uc.mem_write(0xff00+0x2c,struct.pack('<H',0x800))
  self.uc.mem_write(0x7ff0,b'M'+bytes(2)+struct.pack('<H',32)+bytes(11))
  self.uc.mem_write(0x8000,b'TEST=X\0\0\1\0C:\\APP\\TERMINAL.EXE\0')
  return context
 def bind(self):
  return self.call('_live_setup_bind',[self.offset('terminal_config_path'),self.offset('terminal_directory_context'),self.offset('terminal_configuration_values')])
 def reconcile(self,pointer,action):return self.bank('_live_setup_reconcile_accounting',[pointer,action])
 def begin(self,context,active,target):
  return self.call('_live_setup_begin',[self.offset('terminal_config_path'),context,active,16|64,target])
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
 binary=a.terminal.resolve();manifest=json.loads((binary.parent/'manifest.json').read_text());assert manifest['experimental_directory_retirement'] and sha(binary)==manifest['binary_sha256']
 for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True);cases=[]
 def done(name,**values):cases.append(dict(case=name,passed=True,**values))
 blocked=[('connection_state',6),('terminal_parser_active',1),('terminal_transfer_pending',1),('terminal_transfer_active',1),('terminal_controller_active',1),('terminal_monitor_active',1),('process_busy',1),('_redisplay_active',1),('_command_menu_active',1),('uart_rx_count',1),('uart_rx_dropped',1),('terminal_tx_count',1),('terminal_program_pending',1),('terminal_program_active',1),('terminal_directory_context_valid',0),('directory_pending',0),('_directory_retire_armed',0),('terminal_quit',1)]
 for name,value in blocked:
  m=Retirement(binary);m.fixture();m.put('directory_pending',1,1);m.put('directory_pending_count',3);m.put('_directory_retire_armed',1)
  m.put(name,value,1 if name=='directory_pending' else 2);old=m.get('terminal_program_pending')
  m.bank('_terminal_directory_retire_poll',far=True)
  assert m.get('terminal_program_pending')==old and not m.get('_terminal_directory_retirement') and not m.calls and not m.bios,(name,value)
  assert m.get('directory_pending_count')==3
  done('poll-refuses-'+name)
 m=Retirement(binary);m.fixture();m.put('connection_state',6);m.call('terminal_directory_note_connected')
 assert m.get('_directory_retire_armed')==1 and m.get('directory_pending',1)==1 and m.get('directory_pending_count')==1 and len(m.calendar)==1
 m.bank('_terminal_directory_retire_poll',far=True);assert m.get('_directory_retire_armed')==1 and not m.get('terminal_program_pending')
 done('connected-event-survives-once-only-initialization')
 m=Retirement(binary);m.fixture();m.put('directory_pending',1,1);m.put('directory_pending_count',3);m.put('_directory_retire_armed',1)
 m.uc.mem_write(m.symbols['_terminal_directory_retirement'],b'\xa5'*10);m.bank('_terminal_directory_retire_poll',far=True)
 assert m.get('terminal_program_pending')==1 and m.get('terminal_program_kind')==7 and m.get('_directory_retire_armed')==0
 assert struct.unpack('<5H',m.uc.mem_read(m.symbols['_terminal_directory_retirement'],10))==(1,0,0,0,0)
 assert m.bank('_terminal_directory_retire_run',far=True)==1 and m.get('_terminal_directory_retirement')==1 and not m.calls
 m.call('terminal_program_cancel');assert not m.get('terminal_program_pending') and m.get('directory_pending_count')==3 and m.get('directory_pending',1)==1
 assert struct.unpack('<5H',m.uc.mem_read(m.symbols['_terminal_directory_retirement'],10))==(0,5,0,0,0)
 old=len(m.bios);m.bank('_terminal_directory_retire_poll',far=True);assert not m.get('terminal_program_pending') and len(m.bios)==old
 m.put('_directory_retire_armed',1);m.bank('_terminal_directory_retire_poll',far=True);assert m.get('terminal_program_pending')==1
 done('queue-kind7-refuse-run-before-handoff-cancel-and-rearm')
 m=Retirement(binary);original=m.fixture();assert m.bind()==0
 changed=bytearray(original);changed[252+61:252+70]=b'10/29/26\0';struct.pack_into('<H',changed,252+70,3)
 blob=bytes(changed)+bytes(628)+b'Example:23\0'+bytes(53)+b'\xa5'*68;pointer=m.stage_near(blob);active=pointer+496;target=active+628;tail=target+64
 m.uc.mem_write(m.data_base+active,bytes(m.uc.mem_read(m.symbols['terminal_configuration_values'],44)))
 assert m.reconcile(pointer,0)==0 and m.context()==original
 assert m.begin(m.offset('terminal_directory_context'),active,target)==0
 assert m.reconcile(pointer,1)==7;m.call('_live_setup_abort',[0])
 assert m.reconcile(pointer,1)==0 and m.context()==original
 assert m.begin(m.offset('terminal_directory_context'),active,target)==3
 old=len(m.calls);m.error=5
 assert m.begin(pointer,active,target)==0 and len(m.calls)==old
 m.call('_live_setup_abort',[0]);assert m.reconcile(pointer,0)==0
 assert m.bank('_live_setup_frozen_command',[tail])==0
 assert bytes(m.uc.mem_read(m.data_base+tail,68))==b' D:\\BASE\\TEST.PRM\0'+bytes(50)
 done('only-accounting-context-publishes-pending-refusal-and-frozen-PRM-identity')
 for offset in [0,2,252,366,368,432]:
  m=Retirement(binary);original=m.fixture();assert m.bind()==0;bad=bytearray(original);bad[offset]^=1;pointer=m.stage_near(bytes(bad))
  assert m.reconcile(pointer,1)==3 and bytes(m.uc.mem_read(m.data_base+pointer,496))==bad and m.context()==original
  assert m.reconcile(m.offset('terminal_directory_context'),0)==0
  done('reject-nonstat-context-byte-'+str(offset))
 for pointer,action in [(0,0),(65535,0),(1,2)]:
  m=Retirement(binary);m.fixture();assert m.bank('_live_setup_reconcile_accounting',[pointer,action])==1 and not m.calls
  done('invalid-reconcile-extent-or-action',pointer=pointer,action=action)
 for failure in ('none','macro','pending','bad-environment','unbound'):
  m=Retirement(binary);m.fixture();assert m.bind()==0
  m.uc.mem_write(m.symbols['terminal_setup_tail'],b'\xa5'*68);m.uc.mem_write(m.symbols['program_setup_executable'],b'\xa5'*64)
  if failure=='macro':m.put('terminal_macro_active',1)
  elif failure=='pending':m.put('terminal_program_pending',1)
  elif failure=='bad-environment':m.uc.mem_write(0x7ff0,b'X')
  elif failure=='unbound':m.error=5;assert m.bind()!=0
  old=len(m.calls);status=m.bank('_terminal_setup_frozen_start',far=True);assert len(m.calls)==old
  if failure=='none':
   assert status==0 and m.get('terminal_program_pending')==1 and m.get('terminal_program_kind')==1
   assert bytes(m.uc.mem_read(m.symbols['terminal_setup_tail'],68))==b' D:\\BASE\\TEST.PRM\0'+bytes(50)
   assert bytes(m.uc.mem_read(m.symbols['program_setup_executable'],64))==b'C:\\APP\\PRMEDIT.EXE\0'+bytes(45)
  else:
   assert status==(2 if failure in ('macro','pending') else 1)
   assert bytes(m.uc.mem_read(m.symbols['terminal_setup_tail'],68))==b'\xa5'*68 and bytes(m.uc.mem_read(m.symbols['program_setup_executable'],64))==b'\xa5'*64
  done('settings-schedule-'+failure)
 memory=inspect_terminal_memory(binary,binary.parent/'terminal.map');loaded=Retirement(binary);data=binary.read_bytes();header=struct.unpack_from('<14H',data);start=header[4]*16;damaged=[]
 for name,symbol,delta,value in [('wrong-retirement-kind','_directory_retire_queue',14,6),('wrong-setup-kind','_directory_setup_queue',14,7),('wrong-flush-target','_directory_retire_flush',1,None),('wrong-poll-target','terminal_directory_retire_poll_site',1,None),('wrong-frozen-setup-target','terminal_setup_start',2,None)]:
  at=start+loaded.symbols[symbol]-loaded.base+delta;bad=bytearray(data);value=bad[at]^1 if value is None else value;assert bad[at]!=value;bad[at]=value;target=out/(name+'.analysis.exe');target.write_bytes(bad)
  try:inspect_terminal_memory(target,binary.parent/'terminal.map')
  except AssertionError:damaged.append(dict(case=name,rejected=True))
  else:raise AssertionError(name)
 site=loaded.symbols['terminal_directory_retire_poll_site']-loaded.base+3
 relocation=next(header[12]+4*i for i in range(header[3]) if (lambda p:p[0]+16*p[1])(struct.unpack_from('<HH',data,header[12]+4*i))==site)
 bad=bytearray(data);struct.pack_into('<HH',bad,relocation,0,0);target=out/'missing-poll-relocation.analysis.exe';target.write_bytes(bad)
 try:inspect_terminal_memory(target,binary.parent/'terminal.map')
 except AssertionError:damaged.append(dict(case='missing-poll-relocation',rejected=True))
 else:raise AssertionError('Missing poll relocation accepted')
 result=dict(passed=True,binary_sha256=sha(binary),inputs=len(cases),cases=cases,original_inputs=[],damaged_controls=damaged,memory=memory,
  sources={n:sha(ROOT/n) for n in ['standalone/check_directory_retirement.py','standalone/check_directory_identity.py','standalone/dos_image.py','standalone/terminal_memory.py','standalone/directory_fixtures.py','standalone/check_setup_model.py','standalone/check_directory_live.py','src/config/live_setup_owner.c','src/config/live_setup_owner.h','src/terminal/directory_retirement.c','src/terminal/directory_retirement.h','src/terminal/setup_live.asm']},
  scope=__doc__+' Actual linked poll/queue/cancel, connected-event and setup APIs. BIOS time/calendar and DOS canonicalization modeled; PSP/environment is an explicit memory fixture. No product instruction is patched or completed. Actual UART quiescence, installed/failed writes and logical refresh are tested separately in DOS.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS',len(cases),'retirement/setup inputs')
if __name__=='__main__':main()
