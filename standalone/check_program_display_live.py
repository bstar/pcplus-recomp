#!/usr/bin/env python3
"""Execute actual PROGRAM/EXEC and full-height display owner with fault boundaries.
BIOS, UART and DOS kernel effects modeled; no BBS/SIP/physical acceptance.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
import check_transport as transport
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 binary=a.terminal.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 manifest=json.loads((binary.parent/'manifest.json').read_text());assert manifest['experimental_program_display_owner'] and sha(binary)==manifest['binary_sha256']
 for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 transport.BINARY=binary;transport.MAP=binary.parent/'terminal.map'
 from program_display_model import Program
 cases=[]
 def done(name,n):cases.append(dict(case=name,inputs=n,passed=True));print(name,n,'PASS',flush=True)
 count=0;pending=0
 for rows in [25,28,43,50]:
  for hidden in [0,1]:
   for fault in ['success','exec','resize','bad-environment']:
    m=Program();m.setup(rows,hidden)
    if fault=='exec':m.exec_error=2
    if fault=='resize':m.resize_error=8
    if fault=='bad-environment':m.uc.mem_write((0x7000-1)*16,b'X')
    assert m.queue()==0
    try:m.safe()
    except AssertionError:
     print('FAILED',rows,hidden,fault,'keys',list(m.keys),'trap',m.get('terminal_trap_phase'),'quit',m.get('terminal_quit'),'IP',hex(m.uc.reg_read(UC_X86_REG_CS)*16+m.uc.reg_read(UC_X86_REG_IP)),flush=True);raise
    assert m.get('terminal_program_status')==(4 if fault=='success' else 5),(rows,hidden,fault,m.get('terminal_program_status'),m.get('terminal_exit_code'))
    m.verify(rows)
    assert len(m.children)==1 if fault=='success' else len(m.children)>=1 if fault=='exec' else not m.children
    if fault=='success':
     assert m.get('uart_rx_count')==1 and not m.rx and not m.get('uart_rx_dropped')
     value=m.call('uart_receive_byte');assert value==ord('R')
     m.call('terminal_receive_input',ax=value,limit=1000000)
     assert bytes(m.uc.mem_read(0xb8000,1))==b'R' and not m.get('terminal_quit')
     pending+=1
    count+=1
 done('all-heights-status-states-actual-PROGRAM-EXEC-success-and-kernel-failures',count)
 done('pending-return-UART-byte-parses-after-full-frame-restore',pending)
 count=0
 for rows in [25,28,43,50]:
  for hidden in [0,1]:
   m=Program();m.setup(rows,hidden);m.put('connection_state',6)
   assert m.queue()==0;m.safe();m.verify(rows)
   assert m.get('connection_state')==6 and m.get('uart_rx_count')==1 and not m.get('uart_rx_dropped')
   count+=1
 done('tracked-online-PROGRAM-retains-connection-full-frame-and-pending-UART-data',count)
 # A refused restoration must not replay an old frame over a fallback25 view.
 for fault in ['font-refused','mode-refused','canonical-changed']:
  m=Program();m.setup(43);assert m.queue()==0;triggered=[]
  def boundary(u,address,size,data):
   if address==m.symbols['_program_display_restore'] and not triggered:
    triggered.append(True)
    if fault=='font-refused':m.font_refusals=2
    elif fault=='mode-refused':m.mode_refusals=1
    else:m.put('ui_window_rows',25)
  hook=m.uc.hook_add(UC_HOOK_CODE,boundary)
  try:m.safe()
  finally:m.uc.hook_del(hook)
  assert triggered and m.get('terminal_quit') and m.get('terminal_exit_code')==2 and m.get('csi_unimplemented_service')==0x6ef7
  assert not m.get('_program_display_ready') and not m.get('terminal_program_active')
  assert bytes(m.uc.mem_read(0xb8000,43*160))!=m.expected
 done('unverified-geometry-and-canonical-mutation-request-fatal-without-stale-replay',3)
 m=Program();m.setup(50);assert m.far_entry('_program_display_save')==0;image=bytes(m.uc.mem_read(m.symbols['program_screen'],8000))
 assert m.far_entry('_program_display_save')==2 and bytes(m.uc.mem_read(m.symbols['program_screen'],8000))==image
 assert m.far_entry('_program_display_restore')==0 and bytes(m.uc.mem_read(0xb8000,8000))==m.expected
 done('exclusive-save-lease-and-direct-verified-restore-ABI',3)
 m=Program();m.setup(43);m.child_direction_flag=True;assert m.queue()==0;m.safe();m.verify(43)
 assert not m.uc.reg_read(UC_X86_REG_EFLAGS)&0x400
 done('child-direction-flag-does-not-leak-through-restored-parent',1)
 m=Program();m.setup(50);m.shape=m.parent_shape=0x2000;m.cursor_bp_fault=True;m.cursor_bp_events=0
 assert m.queue()==0;m.safe();m.verify(50);assert m.cursor_bp_events==1
 done('BIOS-cursor-shape-BP-clobber-preserves-parent-C-frame-and-return-cursor',1)
 m=Program();m.put('_program_display_ready',0xffff);m.call('terminal_program_initialize',ax=0xff0);assert not m.get('_program_display_ready')
 done('actual-PROGRAM-initializer-clears-readiness-independent-of-BSS',1)
 for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 report=dict(passed=True,terminal_sha256=sha(binary),manifest_sha256=sha(binary.parent/'manifest.json'),inputs=sum(c['inputs'] for c in cases),cases=cases,checker_sha256=sha(Path(__file__)),boundary_model_sha256=sha(ROOT/'standalone/program_display_model.py'),scope=__doc__+' Actual trap open/suspend/resume and context-restoring DOS backend execute; injected faults alter only declared boundary outcomes/canonical input.')
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
