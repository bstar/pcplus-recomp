#!/usr/bin/env python3
"""Real linked far entries, resident services, IRQ return and MZ rejection guards."""
import hashlib,json,re,struct,tempfile
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
from check_terminal_print_controller_live import Controller
from check_meta_actions_live import ROOT,BINARY
from terminal_memory import inspect_terminal_memory

def main():
 listing=(ROOT/'build/terminal/terminal.map').read_text()
 image=BINARY.read_bytes();header=struct.unpack_from('<14H',image);start=header[4]*16
 symbols={name:(int(seg,16),int(off,16)) for seg,off,name in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',listing,re.M|re.I)}
 def at(name):seg,off=symbols[name];return start+seg*16+off
 cases=[]
 def check(name,fn):
  detail=fn();cases.append(dict(case=name,passed=True,detail=detail));print(name,'PASS',flush=True)
 def layout():
  good=inspect_terminal_memory(BINARY,ROOT/'build/terminal/terminal.map')
  assert good['far_code_bridge_pairs_verified']==66 and good['controller_bridge_pairs_verified']==22 and good['modem_bridge_pairs_verified']==22 and good['configuration_bridge_pairs_verified']==22
  assert good['resident_code_bytes']<65536
  mutations=[]
  for name,delta,value in [('terminal_controller_start',3,0),('terminal_controller_start_far',3,0xc3),('terminal_printer_put_raw_resident',0,0x90)]:
   data=bytearray(image);data[at(name)+delta]=value if data[at(name)+delta]!=value else value^1;mutations.append((name,data,listing))
  data=bytearray(image)
  wanted=at('terminal_controller_start')-start+3
  for i in range(header[3]):
   off,seg=struct.unpack_from('<HH',data,header[12]+i*4)
   if seg*16+off==wanted:struct.pack_into('<HH',data,header[12]+i*4,0,0);break
  else:raise AssertionError('Required relocation not found')
  mutations.append(('missing-MZ-far-call-relocation',data,listing))
  # The checker must reject executable code whose reported segment exceeds64K.
  bad_map=re.sub(r'(?m)^(PRINT_CODE\s+FARCODE\s+\S+\s+\S+\s+)\w+',r'\g<1>00010001',listing)
  assert bad_map!=listing;mutations.append(('oversized-code-segment',image,bad_map))
  merged=re.sub(r'(?m)^(PRINT_CODE\s+FARCODE\s+\S+\s+)\S+',r'\g<1>0000:f48c',listing)
  assert merged!=listing;mutations.append(('far-code-merged-into-resident-CS',image,merged))
  with tempfile.TemporaryDirectory() as folder:
   exe=Path(folder)/'BAD.EXE';mp=Path(folder)/'bad.map'
   for label,data,mptext in mutations:
    exe.write_bytes(data);mp.write_text(mptext)
    try:inspect_terminal_memory(exe,mp)
    except AssertionError:pass
    else:raise AssertionError(('Invalid executable accepted',label))
  return dict(layout=good,rejected_mutations=[m[0] for m in mutations])
 check('MZ-relocations-66-bridge-pairs-and-six-invalid-images-rejected',layout)
 def runtime():
  m=Controller();seen=set();low=[m.offset('terminal_stack_top')]
  code_seg=m.symbols['terminal_controller_code_start']//16
  # Code starts on a paragraph, and DS=SS must survive every actual bridge.
  def observe(u,address,size,_):
   cs=u.reg_read(UC_X86_REG_CS);ip=u.reg_read(UC_X86_REG_IP)
   if cs*16+ip!=address:return # hardware hook has just delivered an IRQ
   if cs in (m.base_segment,code_seg):low[0]=min(low[0],u.reg_read(UC_X86_REG_SP))
   if cs==code_seg:assert u.reg_read(UC_X86_REG_SS)==u.reg_read(UC_X86_REG_DS)==m.ds
   if cs==code_seg:seen.add('far')
   for name in ('terminal_controller_start_far','terminal_controller_run_far','terminal_controller_poll_far','terminal_controller_receive_hold_far','terminal_controller_filter_far','terminal_controller_key_far','terminal_controller_shutdown_far'):
    if address==m.symbols[name]:seen.add(name)
  m.uc.hook_add(UC_HOOK_CODE,observe)
  assert m.begin()==0;m.log(b'BEFORE');m.call('_capture_session_flush')
  m.start_controller();assert m.call('terminal_controller_receive_hold')==0
  assert m.controller_key(ord('k'));m.drain();assert bytes(m.tx)==b'k'
  m.feed_controller(b'AX\x1b[4i');m.finish_controller()
  m.csi(b'\x1b[5iBX\x1b[4i')
  m.start_controller();m.feed_controller(b'CX');m.call('terminal_controller_shutdown')
  assert m.device_bytes==b'AXBXCX' and not m.device_live
  assert seen=={'far',*(n+'_far' for n in ('terminal_controller_start','terminal_controller_run','terminal_controller_poll','terminal_controller_receive_hold','terminal_controller_filter','terminal_controller_key','terminal_controller_shutdown'))},seen
  assert m.contents()==b'BEFORE'
  assert m.uc.reg_read(UC_X86_REG_CS)==m.base_segment
  return dict(visited=sorted(seen),observed_stack_bytes=m.offset('terminal_stack_top')-low[0])
 check('all-seven-far-entry-paths-real-PRN-stack-adapter-and-DS-equals-SS',runtime)
 def irq():
  m=Controller();m.start_controller();injected=[False];frames=[]
  far_cs=m.symbols['terminal_controller_code_start']//16
  def observe(u,address,size,_):
   if address==m.symbols['terminal_controller_filter_impl'] and not injected[0]:
    injected[0]=True;m.rx.append(ord('R'))
   if address==m.symbols['uart_receive_interrupt']:
    ss=u.reg_read(UC_X86_REG_SS);sp=u.reg_read(UC_X86_REG_SP)
    frame=struct.unpack('<3H',u.mem_read(ss*16+sp,6));frames.append(frame)
  m.uc.hook_add(UC_HOOK_CODE,observe)
  assert m.consume(ord('A'))
  assert any(cs==far_cs for ip,cs,flags in frames),frames
  assert m.call('uart_receive_byte')==ord('R');assert m.consume(ord('R'))
  m.feed_controller(b'\x1b[4i');m.finish_controller()
  assert m.device_bytes==b'AR' and m.uc.reg_read(UC_X86_REG_CS)==m.base_segment
  return dict(actual_IRQ_frames=[list(f) for f in frames],far_CS=far_cs,printed_hex=m.device_bytes.hex())
 check('actual-UART-ISR-and-IRET-return-to-interrupted-far-code',irq)
 result=dict(passed=True,binary_sha256=hashlib.sha256(image).hexdigest(),cases=cases,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['standalone/check_far_code_live.py','standalone/terminal_memory.py','standalone/dos_image.py','standalone/check_transport.py','standalone/check_terminal_capture_live.py']},scope='Actual linked near/far bridges, controller, PRN queue and UART ISR; kernel/hardware modeled. MZ pointer/return/relocation and segment bounds checked independently, including rejection mutations. DOS child memory retention is a separate actual DOS test. Not arbitrary C stack-argument bridging or full application segmentation.')
 (ROOT/'build/terminal/far-code-live-checks.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
