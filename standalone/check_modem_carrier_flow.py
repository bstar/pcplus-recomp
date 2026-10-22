#!/usr/bin/env python3
"""Execute modem carrier policy, child control suppression and parent retirement."""
import argparse,itertools,json,shutil,struct
from pathlib import Path
from check_aspect_flow_handoff import Flow,q,ROOT,sha
from check_parent_flow_handoff import prepare
from check_connection import Connection
from unicorn.x86_const import *


def parent_flow_alive(m):
    memory=json.loads((ROOT/'build/terminal/manifest.json').read_text())['memory_layout']
    segment=m.base_segment+next(s['relative_segment'] for s in memory['code_segments'] if s['name']=='MODEM_CODE')
    sp=m.offset('terminal_stack_top')-4;u=m.uc
    kept=dict(BX=0x2345,CX=0x3456,SI=0x4567,DI=0x5678,BP=0x6789,DX=0x789a,ES=0x1357)
    for name,value in dict(CS=segment,DS=m.ds,SS=m.ds,SP=sp,EFLAGS=0x602,**kept).items():
        u.reg_write(globals()['UC_X86_REG_'+name],value)
    u.mem_write(m.data_base+sp,struct.pack('<HH',m.return_offset,m.base_segment));m.returned=False
    u.emu_start(m.symbols['terminal_connection_flow_alive'],0,count=200000);assert m.returned
    assert u.reg_read(UC_X86_REG_SP)==sp+4 and u.reg_read(UC_X86_REG_DS)==u.reg_read(UC_X86_REG_SS)==m.ds
    for name,value in kept.items():assert u.reg_read(globals()['UC_X86_REG_'+name])==value,name
    assert u.reg_read(UC_X86_REG_EFLAGS)&0x600==0x600
    return u.reg_read(UC_X86_REG_AX)


class Modem(Flow):
    def __init__(self,flags=2):
        super().__init__(flags);self.words[1]=6;self.publish();self.registers[0x3fe]=0x90


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True);cases=[]
    for enabled,direct,seen,paused in itertools.product((0,1),(0,1),(0,128),(0,1)):
        m,result=prepare(1,1,paused,enabled,direct,seen);assert result==0
        flags=struct.unpack('<H',m.uc.mem_read(m.symbols['_script_handoff']+48,2))[0]
        assert flags==paused|(2 if enabled and not direct and seen else 0)
        cases.append(dict(case='parent-input-%d%d%d%d'%(enabled,direct,bool(seen),paused),passed=True))
    for mode in (b'N',b'S',b'H',b'B'):
        m=Modem();m.mode(mode);assert m.open()==0 and m.get('serial_carrier_policy')==2
        if mode in (b'S',b'B'):
            m.put('uart_flow_pending',19,1);assert m.call('_aspect_serial_poll')==0 and bytes(m.tx).endswith(b'\x13')
        m.registers[0x3fe]=0x10;m.put('uart_flow_pending',17,1);m.put('uart_xoff_sent',1,1)
        before=bytes(m.tx);assert m.call('_aspect_serial_poll')==0
        assert bytes(m.tx)==before and m.get('uart_flow_pending',1)==m.get('uart_xoff_sent',1)==0
        assert m.call('_aspect_serial_close')==0 and bytes(m.tx)==before
        words=struct.unpack('<I23H',m.uc.mem_read(m.desc,50));assert words[10]==1 and words[23]==2
        cases.append(dict(case='child-DCD-loss-no-control-'+mode.decode(),passed=True))
    for version in (5,6):
        m=Flow();m.words[1]=version;m.publish();m.mode(b'S');m.registers[0x3fe]=0x10
        assert m.open()==0 and m.get('serial_carrier_policy')==0
        m.put('uart_flow_pending',17,1);assert m.call('_aspect_serial_poll')==0 and bytes(m.tx).endswith(b'\x11')
        assert m.call('_aspect_serial_close')==0 and bytes(m.tx).endswith(b'\x13')
        cases.append(dict(case='untracked-low-DCD-policy-unchanged-v'+str(version),passed=True))
    for flags in (4,65535):
        m=Modem(flags);m.mode(b'S');assert m.open()==1 and not m.writes
        cases.append(dict(case='unknown-v6-flags'+str(flags),passed=True))
    for direct in (0,1):
        m=Connection();m.put('uart_software_flow',1);m.put('terminal_directory_mode',direct)
        if direct:m.start()
        else:m.connect()
        assert m.state()==6;m.receive_irq(b'\x13');assert m.get('uart_tx_paused')==1
        m.poll();assert m.get('uart_tx_paused')==1 and m.state()==6
        m.enqueue(b'OLD');m.carrier=False;m.poll()
        assert m.state()==0 and m.get('connection_status')==6 and m.get('uart_tx_paused')==0
        assert m.get('terminal_tx_count')==0 and b'OLD' not in bytes(m.tx)
        if not direct:
            before=bytes(m.tx);m.start();m.waiting();assert bytes(m.tx)[len(before):]==b'ATZ\rATDLocal.Example:2323\r'
        cases.append(dict(case='known-DCD-loss-retires-old-flow-direct'+str(direct),passed=True))
    for enabled,direct,seen,carrier in itertools.product((0,1),(0,1),(0,128),(False,True)):
        m=Connection();m.put('connection_enabled',enabled,1);m.put('terminal_directory_mode',direct);m.put('connection_carrier_seen',seen,1);m.carrier=carrier
        m.put('uart_tx_paused',1);m.put('uart_flow_pending',17,1);m.put('uart_xoff_sent',1,1);m.put('uart_rts_lowered',1,1);m.mcr=9
        answer=parent_flow_alive(m)
        lost=enabled and not direct and seen and not carrier
        assert answer==int(not lost)
        assert (m.get('uart_tx_paused'),m.get('uart_flow_pending',1),m.get('uart_xoff_sent',1),m.get('uart_rts_lowered',1))==((0,0,0,0) if lost else (1,17,1,1))
        assert m.mcr==(11 if lost else 9)
        cases.append(dict(case='parent-return-policy-%d%d%d%d'%(enabled,direct,bool(seen),carrier),passed=True))
    inputs={}
    for directory,leaf in [('terminal','TERMINAL.EXE'),('aspect-runner','ASPECT.EXE')]:
        base=ROOT/'build'/directory;manifest=json.loads((base/'manifest.json').read_text());assert sha(base/leaf)==manifest['binary_sha256'];inputs.update(manifest['sources'])
        for f in (base/leaf,base/'manifest.json',*base.glob('*.map')):inputs[str(f.relative_to(ROOT))]=sha(f)
    for f in [Path(__file__),ROOT/'standalone/check_aspect_flow_handoff.py',ROOT/'standalone/check_parent_flow_handoff.py',ROOT/'standalone/check_script_launch_live.py',ROOT/'standalone/check_aspect_render_client.py',ROOT/'standalone/check_connection.py',ROOT/'standalone/check_transport.py',ROOT/'standalone/check_uart.py']:
        inputs[str(f.relative_to(ROOT))]=sha(f)
    for name,digest in inputs.items():
        assert sha(ROOT/name)==digest;target=out/'inputs'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,target)
    result=dict(passed=True,cases=cases,inputs=inputs,parent_sha256=sha(ROOT/'build/terminal/TERMINAL.EXE'),runner_sha256=sha(ROOT/'build/aspect-runner/ASPECT.EXE'),scope=__doc__+' Actual DS=SS near/far instructions, guarded v6 policy, native UART ISR and ports execute. Hardware/kernel boundaries are modeled; no actual DOS/physical claim.')
    (out/'checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,cases=len(cases))))


if __name__=='__main__':main()
