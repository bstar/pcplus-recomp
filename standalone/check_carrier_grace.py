#!/usr/bin/env python3
"""Replay transient/sustained physical-modem DCD through linked controller code."""
import argparse,json,struct,hashlib
from pathlib import Path
from unicorn.x86_const import *
import check_transport as transport
from check_connection import Connection

ROOT=Path(__file__).resolve().parents[1]
DAY=0x1800b0
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def select(path):
    transport.BINARY=path;transport.MAP=path.parent/'terminal.map'

def flow_alive(m):
    manifest=json.loads((transport.BINARY.parent/'manifest.json').read_text())
    segment=m.base_segment+next(s['relative_segment'] for s in manifest['memory_layout']['code_segments'] if s['name']=='MODEM_CODE')
    sp=m.offset('terminal_stack_top')-4;u=m.uc
    kept=dict(BX=0x2345,CX=0x3456,DX=0x4567,SI=0x5678,DI=0x6789,BP=0xbabe,ES=0x1357)
    for name,value in dict(CS=segment,DS=m.ds,SS=m.ds,SP=sp,EFLAGS=0x602,**kept).items():u.reg_write(globals()['UC_X86_REG_'+name],value)
    u.mem_write(m.data_base+sp,struct.pack('<HH',m.return_offset,m.base_segment));m.returned=False
    u.emu_start(m.symbols['terminal_connection_flow_alive'],0,count=200000)
    assert m.returned and u.reg_read(UC_X86_REG_SP)==sp+4
    assert u.reg_read(UC_X86_REG_DS)==u.reg_read(UC_X86_REG_SS)==m.ds
    assert u.reg_read(UC_X86_REG_EFLAGS)&0x600==0x600
    for name,value in kept.items():assert u.reg_read(globals()['UC_X86_REG_'+name])==value,name
    return u.reg_read(UC_X86_REG_AX)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--terminal',type=Path,required=True);p.add_argument('--baseline',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    select(a.baseline.resolve());m=Connection();m.connect();m.carrier=False;m.poll();m.carrier=True;m.poll()
    assert (m.state(),m.get('connection_status'))==(0,6)
    select(a.terminal.resolve());cases=[]
    for start in (100,65534,DAY-2):
        for duration in range(4):
            m=Connection();m.connect();m.tick=start;m.carrier=False;m.call('terminal_connection_poll')
            for delta in range(duration+1):
                m.tick=(start+delta)%DAY;m.call('terminal_connection_poll')
                assert (m.state(),m.get('connection_status'))==(6,1)
                assert flow_alive(m)==1
            m.carrier=True;m.call('terminal_connection_poll')
            assert (m.state(),m.get('connection_status'))==(6,1)
            # A later low interval must receive its own full bound.
            m.tick=(start+50)%DAY;m.carrier=False;m.call('terminal_connection_poll')
            assert (m.state(),m.get('connection_status'))==(6,1)
            cases.append(dict(kind='transient',start=start,ticks=duration,passed=True))
        for first_owner in ('poll','flow'):
            m=Connection();m.connect();m.tick=start;m.carrier=False
            if first_owner=='poll':m.call('terminal_connection_poll')
            else:assert flow_alive(m)==1
            for delta in (0,1,2,3):
                m.tick=(start+delta)%DAY;assert flow_alive(m)==1
            m.tick=(start+4)%DAY;assert flow_alive(m)==0
            m.call('terminal_connection_poll');assert (m.state(),m.get('connection_status'))==(0,6)
            # Sustained loss stays a real disconnect, not automatic fake reconnection.
            m.carrier=True;m.call('terminal_connection_poll');assert m.state()==0
            cases.append(dict(kind='sustained',start=start,first_owner=first_owner,passed=True))
    m=Connection();m.carrier=False;m.connect();m.poll(10)
    assert (m.state(),m.get('connection_status'))==(6,1)
    m.carrier=True;m.poll();m.carrier=False;m.poll();assert m.state()==6
    cases.append(dict(kind='initially-unasserted-DCD',passed=True))
    m=Connection();m.put('terminal_directory_mode',1);m.start();m.carrier=False;m.poll()
    assert (m.state(),m.get('connection_status'))==(0,6)
    cases.append(dict(kind='direct-link-policy-unchanged',passed=True))
    result=dict(passed=True,cases=cases,terminal_sha256=sha(a.terminal),baseline_sha256=sha(a.baseline),
        sources={n:sha(ROOT/n) for n in ('standalone/check_carrier_grace.py','src/terminal/connection.asm')},
        scope=__doc__+' Actual linked controller, flow-return and notice code. Modeled UART/BIOS ticks, including midnight and low-word wrap. No claim about physical DCD cause or child-owned serial sampling.')
    (a.output/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS:',len(cases),'carrier timing/ownership cases; old transient control fails as expected')

if __name__=='__main__':main()
