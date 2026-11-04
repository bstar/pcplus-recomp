#!/usr/bin/env python3
"""Linked flow silence during DCD grace, without changing disconnect debounce.
Actual controller, foreground flow and shutdown routines execute; only DOS,
BIOS, UART registers and clock boundaries use the existing hardware model.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
from check_call_timer_live import Clock,configure
ROOT=Path(__file__).resolve().parents[1];DAY=0x1800b0
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def ready(m,flags=0x202):
 seg,off=m.entries['terminal_connection_flow_ready'];u=m.uc;sp=m.offset('terminal_stack_top')-4
 kept=dict(BX=0x2345,CX=0x3456,DX=0x4567,SI=0x5678,DI=0x6789,BP=0xbabe,ES=0x1357)
 for name,value in dict(CS=m.base_segment+seg,DS=m.ds,SS=m.ds,SP=sp,EFLAGS=flags,**kept).items():u.reg_write(globals()['UC_X86_REG_'+name],value)
 u.mem_write(m.data_base+sp,struct.pack('<2H',m.return_offset,m.code_segment));m.returned=False
 u.emu_start(m.symbols['terminal_connection_flow_ready'],0,count=200000)
 assert m.returned and u.reg_read(UC_X86_REG_SP)==sp+4
 assert u.reg_read(UC_X86_REG_DS)==u.reg_read(UC_X86_REG_SS)==m.ds and u.reg_read(UC_X86_REG_EFLAGS)&0x600==flags&0x600
 for name,value in kept.items():assert u.reg_read(globals()['UC_X86_REG_'+name])==value,name
 return u.reg_read(UC_X86_REG_AX)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 binary=a.terminal.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 manifest=json.loads((binary.parent/'manifest.json').read_text());assert sha(binary)==manifest['binary_sha256'];configure(binary)
 for name,h in manifest['sources'].items():assert sha(ROOT/name)==h,name
 cases=[]
 for start in [100,65534,DAY-2]:
  for duration in range(4):
   for pending in [17,19]:
    for hard in [0,1]:
     m=Clock();m.connect();m.put('uart_software_flow',1);m.put('uart_hardware_flow',hard);m.put('uart_flow_pending',pending,1)
     for value in [0,255,65]:m.call('csi_transmit_byte',[value],cleanup=2)
     m.tick=start;m.carrier=False;before=bytes(m.tx)
     for delta in range(duration+1):
      m.tick=(start+delta)%DAY
      assert ready(m,0x602 if delta%2 else 0x202)==0
      assert m.far('terminal_connection_flow_alive')==1
      m.call('terminal_poll_serial');assert m.state()==6 and m.get('connection_status')==1
      assert bytes(m.tx)==before and m.get('uart_flow_pending',1)==pending and m.get('terminal_tx_count')==3,(start,duration,pending,hard,delta,bytes(m.tx)[len(before):].hex(),m.get('terminal_tx_count'))
     m.carrier=True;m.tick=(start+duration+1)%DAY;m.call('terminal_poll_serial')
     m.call('terminal_poll_serial');m.call('terminal_poll_serial')
     assert bytes(m.tx)[len(before):]==bytes([pending,0,255,65]) and m.state()==6 and m.get('uart_flow_pending',1)==m.get('terminal_tx_count')==0
     cases.append(dict(kind='transient-retains-and-resumes',start=start,ticks=duration,pending=pending,hard=hard,passed=True))
  for entry in ['terminal_poll_serial','terminal_release_flow']:
   m=Clock();m.connect();m.put('uart_software_flow',1);m.put('uart_tx_paused',1);m.put('uart_flow_pending',17,1);m.put('uart_xoff_sent',1,1)
   m.tick=start;m.carrier=False;before=bytes(m.tx)
   if entry=='terminal_poll_serial':
    m.call('csi_transmit_byte',[65],cleanup=2)
    for delta in range(5):m.tick=(start+delta)%DAY;m.call(entry)
    assert m.state()==0 and m.get('connection_status')==6 and m.get('terminal_tx_count')==0
   else:
    m.advance_ticks=True;m.call(entry,limit=1000000)
    assert m.get('terminal_cleanup_flow_failed')==0 and m.get('terminal_exit_code')==0
   assert bytes(m.tx)==before and m.get('uart_flow_pending',1)==m.get('uart_xoff_sent',1)==m.get('uart_tx_paused')==0
   cases.append(dict(kind='sustained-retires-without-command-bytes',start=start,entry=entry,passed=True))
 for field,value,width in [('connection_enabled',0,1),('terminal_directory_mode',1,2),('connection_carrier_seen',0,1)]:
  m=Clock();m.connect();m.carrier=False;m.put(field,value,width);assert ready(m)==1
  m.put('uart_software_flow',1);m.put('uart_flow_pending',17,1);before=bytes(m.tx);m.call('terminal_poll_serial')
  if field!='terminal_directory_mode':assert bytes(m.tx)[len(before):]==b'\x11'
  cases.append(dict(kind='existing-untracked-direct-policy',field=field,passed=True))
 m=Clock();m.connect();m.put('uart_software_flow',1);m.put('uart_xoff_sent',1,1);m.tick=100;m.carrier=False;m.advance_ticks=True;before=bytes(m.tx)
 def recover(u,at,size,d):
  if at==m.symbols['terminal_clock_ticks'] and m.tick>=102:m.carrier=True
 m.uc.hook_add(UC_HOOK_CODE,recover);m.call('terminal_release_flow',limit=1000000)
 assert bytes(m.tx)[len(before):]==b'\x11' and not m.get('terminal_cleanup_flow_failed')
 cases.append(dict(kind='shutdown-waits-for-transient-carrier-then-resumes',passed=True))
 report=dict(passed=True,cases=cases,inputs=len(cases),terminal_sha256=sha(binary),manifest_sha256=sha(binary.parent/'manifest.json'),sources={n:sha(ROOT/n) for n in ['standalone/check_carrier_flow_ready.py','standalone/check_call_timer_live.py','standalone/check_transport.py']},scope=__doc__)
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS carrier flow readiness',len(cases),'inputs')
if __name__=='__main__':main()
