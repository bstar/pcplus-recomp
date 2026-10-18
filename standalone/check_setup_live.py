#!/usr/bin/env python3
"""Direct settings child through the actual keyboard/UART/video/EXEC owner."""
import hashlib,json,struct
from unicorn.x86_const import UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI,UC_X86_REG_ES,UC_X86_REG_AX
from check_program_actions_live import LiveProgram,ROOT,BINARY

class SetupProgram(LiveProgram):
 def __init__(self,**kw):
  self.local_text=bytearray();super().__init__(**kw)
 def interrupt(self,uc,number,data):
  ax=uc.reg_read(UC_X86_REG_AX)
  if number==0x10 and ax>>8==14:self.local_text.append(ax&255)
  return super().interrupt(uc,number,data)

def model(path=b'TEST.PRM',**kw):
 m=SetupProgram(child_status=0,**kw)
 m.put('terminal_option_mask',16)
 m.uc.mem_write(m.symbols['terminal_config_path'],path.ljust(64,b'\0'))
 return m
def main():
 cases=[]
 def done(name,count):cases.append(dict(case=name,inputs=count,passed=True));print(name,count,flush=True)
 for path in [b'A',b'test.prm',b'12345678.PRM',b'A_B-1.PRM']:
  m=model(path);m.keys.append(0x7100);m.poll()
  assert m.get('terminal_program_pending')==m.get('terminal_program_kind')==1
  assert not m.children and not m.tx and not m.get('terminal_quit')
  m.safe()
  assert m.children==[dict(path=b'PRMEDIT.EXE',tail=b' '+path)]
  assert struct.unpack('<4H',m.uc.mem_read(m.symbols['terminal_program_result'],8))[:3]==(0,0,0)
  assert m.get('terminal_program_status')==4
  assert b'Setup closed.' in m.local_text and b'could not run' not in m.local_text
  m.restored();assert m.data_reads==0 and bytes(m.rx)==b'R'
 done('AltF10-queues-direct-local-child-exact-tail-and-restores-full-parent',4)
 bad=[b'',b'.PRM',b'A.',b'A..PRM',b'123456789.PRM',b'A.PRMX',b'D:\\TEST.PRM',b'..\\TEST.PRM',b'A B.PRM',b'A|B.PRM',b'A&B.PRM',b'A$B.PRM',b'X'*64]
 for path in bad:
  m=model(path);assert m.call('terminal_setup_start')==1
  assert not m.get('terminal_program_pending') and not m.children and not m.tx
 m=model();m.put('terminal_option_mask',0);assert m.call('terminal_setup_start')==1
 done('absent-explicit-config-and-invalid-or-shell-like-paths-never-queue',len(bad)+1)
 for field,value in [('terminal_macro_active',1),('terminal_program_pending',1),('terminal_program_active',1),('terminal_controller_active',1),('terminal_monitor_active',1),('uart_break_hold',1),('connection_state',2)]:
  m=model();m.put(field,value);before=m.get('terminal_program_pending')
  assert m.call('terminal_setup_start')==2 and m.get('terminal_program_pending')==before and not m.children
 done('existing-local-owners-and-connection-negotiation-reject-reentrant-setup',7)
 for key in [0x011b,0x2d00]:
  m=model();assert m.call('terminal_setup_start')==0
  m.keys.append(key);m.poll()
  assert not m.get('terminal_program_pending') and not m.get('terminal_program_kind') and not m.children
 done('Escape-and-AltX-cancel-pending-setup-without-EXEC',2)
 for exec_error in [2,5,8]:
  m=model(exec_error=exec_error);assert m.call('terminal_setup_start')==0;m.safe()
  assert m.get('terminal_program_status')==5 and not m.get('terminal_program_active')
  assert b'Program could not run.' in m.local_text
  m.restored()
 done('direct-EXEC-failure-restores-connection-video-and-startup-hardware-baseline',3)
 m=model();m.child_status=9;assert m.call('terminal_setup_start')==0;m.safe();assert m.get('terminal_program_status')==5;m.restored()
 assert b'Program could not run.' in m.local_text
 done('failed-editor-exit-is-reported-without-exiting-terminal',1)
 m=model();m.put('uart_software_flow',1);assert m.call('terminal_setup_start')==0;m.safe()
 assert bytes(m.tx)==b'\x13' and not m.children
 m.temt=False;m.safe();assert not m.children
 m.temt=True;m.safe();assert len(m.children)==1 and m.get('uart_flow_pending',1)==0x11
 m.poll();assert bytes(m.tx)==b'\x13\x11';m.restored()
 done('software-peer-pause-waits-for-physical-TEMT-and-resumes-once',1)
 for reg,value in [(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678),(UC_X86_REG_ES,0xb800)]:assert m.uc.reg_read(reg)==value
 result=dict(passed=True,inputs=sum(c['inputs'] for c in cases),cases=cases,binary_sha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),scope='Actual linked AltF10 scheduler, direct process_run, child handoff, flow, UART IRQ/vector/format and video restoration. Kernel/BIOS/UART modeled. Editor saves are adopted on next startup; live candidate commit remains separate unfinished work.')
 (ROOT/'build/terminal/setup-live-checks.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
