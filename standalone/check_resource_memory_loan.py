#!/usr/bin/env python3
"""Execute real initialized parent/traps/EXEC/loan with declared DOS failures."""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn import UC_HOOK_INSN
from unicorn.x86_const import *
import check_terminal_traps as traps
from check_process import Kernel
ROOT=Path(__file__).resolve().parents[1]
class Memory(traps.Machine):
 def __init__(self,*,resize_failure=0,exec_error=0):
  super().__init__()
  self.ds=self.image.ds;self.data_base=self.image.data_base;self.offset=self.image.offset
  self.sizes=[];self.children=[];self.resize_failure=resize_failure;self.exec_error=exec_error;self.child_status=37;self.clobber=True
  self.pic=0;self.lcr=3;self.mcr=0xb;self.ier=1;self.quiet_checks=0
  self.u.hook_add(UC_HOOK_INSN,self.input_port,None,1,0,UC_X86_INS_IN)
  self.u.hook_add(UC_HOOK_INSN,self.output_port,None,1,0,UC_X86_INS_OUT)
  self.image.put('uart_previous_irq_offset',0x1234);self.image.put('uart_previous_irq_segment',0xf000)
  self.u.reg_write(UC_X86_REG_AX,self.psp)
  assert self.image.call('terminal_program_initialize')==self.psp
  self.full=self.image.get('process_keep_paragraphs');self.floor=self.image.get('terminal_program_critical_paragraphs');self.actual=self.full
  self.pic=1<<(self.image.get('terminal_irq_vector')-8);self.ier=0;self.mcr=9
  assert self.floor<self.full
  self.far('terminal_trap_open')
  self.image.put('terminal_program_active',1);self.image.put('terminal_program_kind',4)
  self.live=self.image.symbols['terminal_history_buffer'];self.frozen=self.image.symbols['redisplay_snapshot'];self.end=self.image.symbols['_redisplay_row_index_end']
  self.ring=bytes((i*17+23)&255 for i in range(63000));self.u.mem_write(self.live,self.ring);self.u.mem_write(self.frozen,b'\xcc'*(self.end-self.frozen))
  self.calls.clear()
 def input_port(self,u,port,size,data):
  if port==0x21:return self.pic
  if port==self.image.get('uart_port_lcr'):return self.lcr
  if port==self.image.get('uart_port_mcr'):return self.mcr
  if port==self.image.get('uart_port_ier'):return self.ier
  raise AssertionError(('Unexpected UART read',port))
 def output_port(self,u,port,size,value,data):
  if port==0x21:self.pic=value&255;return
  if port==self.image.get('uart_port_lcr'):self.lcr=value&255;return
  if port==self.image.get('uart_port_mcr'):self.mcr=value&255;return
  if port==self.image.get('uart_port_ier'):self.ier=value&255;return
  raise AssertionError(('Unexpected UART write',port))
 def code(self,u,address,size,data):
  if address==0xf0005:self.done='returned';u.emu_stop()
  elif address==self.image.symbols['terminal_trap_hold']:raise AssertionError('Unexpected trap quarantine')
 def far(self,name):
  self.registers();seg,off=self.map[name];stub=0xf0000
  self.u.mem_write(stub,b'\x9a'+struct.pack('<HH',off,seg)+b'\xf4');self.u.ctl_remove_cache(stub,stub+6)
  sp=self.image.offset('terminal_stack_top')-16;self.u.reg_write(UC_X86_REG_CS,0xf000);self.u.reg_write(UC_X86_REG_SP,sp)
  self.done=None;self.u.emu_start(stub,0,count=100000);assert self.done=='returned' and self.u.reg_read(UC_X86_REG_SP)==sp
  assert self.u.reg_read(UC_X86_REG_AX)==0
 def set_carry(self,value):
  flags=self.u.reg_read(UC_X86_REG_EFLAGS);self.u.reg_write(UC_X86_REG_EFLAGS,flags|1 if value else flags&~1)
 def interrupt(self,u,n,data):
  ax=u.reg_read(UC_X86_REG_AX);ah=ax>>8
  if n==0x21 and ah==0x25:
   irq=self.image.get('terminal_irq_vector');assert ax&255==irq
   assert self.pic&(1<<(irq-8)) and self.ier==0 and not self.mcr&2 and not self.lcr&0x80
   self.u.mem_write(irq*4,struct.pack('<HH',u.reg_read(UC_X86_REG_DX),u.reg_read(UC_X86_REG_DS)))
   return
  if n==0x21 and ah==0x4a:
   size=u.reg_read(UC_X86_REG_BX);assert u.reg_read(UC_X86_REG_ES)==self.psp
   self.sizes.append(size);error=8 if len(self.sizes)==self.resize_failure else 0
   if len(self.sizes)==2 and self.children:
    irq=self.image.get('terminal_irq_vector');assert self.pic&(1<<(irq-8)) and self.ier==0 and not self.mcr&2
    assert struct.unpack('<HH',self.u.mem_read(irq*4,4))==(0x1234,0xf000)
    self.quiet_checks+=1
   if not error:self.actual=size
   u.reg_write(UC_X86_REG_AX,error);self.set_carry(bool(error));return
  if n==0x21 and ah in (0x29,0x4b,0x4d):
   if ah==0x4b and self.image.get('process_loan_active'):
    assert self.actual==self.floor and self.image.get('process_keep_paragraphs')==self.floor
    # A child may use the complete relinquished region. This is a DOS memory
    # boundary fixture, not a substituted parent callback or completion.
    self.u.mem_write(self.frozen,b'\xed'*(self.end-self.frozen))
   result=Kernel.interrupt(self,u,n,data)
   if ah==0x4b:
    self.pic=0;self.ier=255;self.lcr=0x83;self.mcr=0xb
    self.u.mem_write(self.image.get('terminal_irq_vector')*4,struct.pack('<HH',0xabcd,0x4567))
   return result
  return super().interrupt(u,n,data)
 def run(self):
  pointer=self.image.stage_near(b'CHILD.COM\0'+bytes(22)+b'\xa5'*8)
  self.u.reg_write(UC_X86_REG_ES,0xb800)
  status=self.image.call('process_run',[pointer,0,pointer+32],limit=1000000)
  assert self.u.reg_read(UC_X86_REG_DS)==self.u.reg_read(UC_X86_REG_SS)==self.image.ds and self.u.reg_read(UC_X86_REG_ES)==0xb800
  assert self.u.reg_read(UC_X86_REG_BP)==0xbabe and self.u.reg_read(UC_X86_REG_SI)==0x1234 and self.u.reg_read(UC_X86_REG_DI)==0x5678
  assert bytes(self.u.mem_read(self.live,63000))==self.ring
  return status,struct.unpack('<4H',self.u.mem_read(self.image.data_base+pointer+32,8))
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
 binary=args.terminal.resolve();manifest=json.loads((binary.parent/'manifest.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 assert manifest['experimental_directory_resource_owner'] and sha(binary)==manifest['binary_sha256']
 for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 traps.OUT=binary.parent
 out=args.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True);cases=[]
 for options,expected in [({},0),({'exec_error':2},3),({'exec_error':8},3),({'resize_failure':1},2),({'resize_failure':2},8),({'resize_failure':2,'exec_error':2},8)]:
  m=Memory(**options);status,result=m.run();assert status==expected and result[0]==status
  assert m.sizes==[m.floor,m.full] and not m.image.get('process_loan_active')
  if expected==8:
   assert m.actual==m.floor and result[3]==m.floor and m.image.get('process_loan_restore_error')==8
   assert m.image.get('terminal_quit')==1 and m.image.get('terminal_exit_code')==7
   assert result[1]==(2 if options.get('exec_error')==2 else 8)
   before=(len(m.calls),len(m.sizes));status,result=m.run();assert status==4 and result==(0xa5a5,)*4 and before==(len(m.calls),len(m.sizes))
  else:
   assert m.actual==m.full and result[3]==m.full and m.image.get('process_keep_paragraphs')==m.image.get('process_minimum_paragraphs')==m.full
   assert not m.image.get('process_loan_restore_error') and not m.image.get('terminal_quit')
  assert m.quiet_checks==bool(m.children)
  cases.append(dict(case='EXEC-and-restoration',options=options,status=expected,requested_sizes=m.sizes,passed=True))
 for name,value in [('terminal_program_active',0),('terminal_program_pending',1),('_redisplay_active',1),('_command_menu_active',1),('_redisplay_live_ready',1),('terminal_snapshot_active',1),('terminal_program_kind',6),('terminal_program_kind',2)]:
  m=Memory();m.image.put(name,value);status,result=m.run();assert status==0 and m.sizes==[m.full] and m.actual==m.full
  assert bytes(m.u.mem_read(m.frozen,m.end-m.frozen))==b'\xcc'*(m.end-m.frozen)
  cases.append(dict(case='refuse-loan-while-owned',field=name,value=value,passed=True))
 result=dict(passed=True,binary_sha256=sha(binary),cases=cases,inputs=len(cases),original_inputs=[],
  full_paragraphs=m.full,critical_paragraphs=m.floor,loan_bytes=(m.full-m.floor)*16,live_ring_bytes_preserved=63000,
  sources={n:sha(ROOT/n) for n in ['standalone/check_resource_memory_loan.py','standalone/check_terminal_traps.py','standalone/check_process.py','standalone/dos_image.py','src/process/dos_exec.asm','src/terminal/program_actions.asm','src/terminal/redisplay.asm']},
  scope='Actual linked initialization, traps, argument/ownership/loan/EXEC/restoration and quieting instructions; DOS boundaries and UART registers modeled, including a child leaving enabled IRQ/IER/DLAB and a stale vector. Native package compilation/viewers remain separate evidence.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS',len(cases),'memory loan/admission/failure inputs')
if __name__=='__main__':main()
