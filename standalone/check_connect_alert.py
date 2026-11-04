#!/usr/bin/env python3
"""Execute the linked connection controller, paired speaker owner and keyboard."""
import argparse,json,struct,hashlib
from pathlib import Path
from unicorn.x86_const import *
import check_transport as transport
from check_connection import Connection

ROOT=Path(__file__).resolve().parents[1]
DAY=0x1800b0

class Alert(Connection):
    def interrupt(self,u,number,data):
        # Full candidates also bind the recovered call clock at CONNECT.
        # Model its DOS date/time boundary; speaker/controller code still executes.
        ah=u.reg_read(UC_X86_REG_AX)>>8
        if number==0x21 and ah==0x2c:
            seconds=(self.tick*65536//1193182)%86400
            u.reg_write(UC_X86_REG_CX,(seconds//3600)<<8|seconds//60%60)
            u.reg_write(UC_X86_REG_DX,(seconds%60)<<8);return
        if number==0x21 and ah==0x2a:
            u.reg_write(UC_X86_REG_CX,2026);u.reg_write(UC_X86_REG_DX,0x0b03)
            u.reg_write(UC_X86_REG_AX,0x2a02);return
        super().interrupt(u,number,data)
    def __init__(self,seconds=5,enabled=1,port=0xa0,**kw):
        self.speaker=port;self.sounds=[]
        super().__init__(**kw)
        self.far('initialize')
        self.put('_terminal_sound_enabled',enabled)
        self.put('_terminal_connect_alert_seconds',seconds)
    def tick_hook(self,u,address,size,data):
        super().tick_hook(u,address,size,data)
        if address==self.symbols['_speaker_ticks']:u.mem_write(0x46c,struct.pack('<I',self.tick))
    def input_port(self,u,port,size,data):
        if port==0x61:return self.speaker
        return super().input_port(u,port,size,data)
    def output_port(self,u,port,size,value,data):
        if port in (0x61,0x42,0x43):
            self.sounds.append((self.tick,port,value))
            if port==0x61:self.speaker=value
            return
        return super().output_port(u,port,size,value,data)
    def far(self,name,flags=0x202):
        m=json.loads((transport.BINARY.parent/'manifest.json').read_text())
        segment=self.base_segment+next(s['relative_segment'] for s in m['memory_layout']['code_segments'] if s['name']=='CONFIG_CODE')
        sp=self.offset('terminal_stack_top')-4;u=self.uc
        kept=dict(AX=0x1234,BX=0x2345,CX=0x3456,DX=0x4567,SI=0x5678,DI=0x6789,BP=0xbabe,ES=0x1357)
        for name_,value in dict(CS=segment,DS=self.ds,SS=self.ds,SP=sp,EFLAGS=flags,**kept).items():u.reg_write(globals()['UC_X86_REG_'+name_],value)
        u.mem_write(self.data_base+sp,struct.pack('<HH',self.return_offset,self.base_segment));self.returned=False
        u.emu_start(self.symbols['terminal_connect_alert_'+name],0,count=200000)
        assert self.returned and u.reg_read(UC_X86_REG_SP)==sp+4
        assert u.reg_read(UC_X86_REG_DS)==u.reg_read(UC_X86_REG_SS)==self.ds
        assert u.reg_read(UC_X86_REG_EFLAGS)&0x600==flags&0x600
        for name_,value in kept.items():assert u.reg_read(globals()['UC_X86_REG_'+name_])==value,name_
    def gates(self):return [(t,v&3) for t,p,v in self.sounds if p==0x61]

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    transport.BINARY=a.terminal.resolve();transport.MAP=transport.BINARY.parent/'terminal.map'
    a.output.mkdir(parents=True,exist_ok=False);cases=[]
    def done(name):cases.append(dict(case=name,passed=True))
    for start in (100,65534,DAY-2):
        m=Alert();m.tick=start;m.connect();origin=m.tick
        assert m.sounds==[(origin,0x43,0xb6),(origin,0x42,0x4b),(origin,0x42,5),(origin,0x61,0xa3)]
        for delta in range(110):
            m.tick=(origin+delta)%DAY;m.call('terminal_connection_poll')
            assert m.state()==6 and m.get('connection_status')==1
        expected=[(delta,3 if delta%15 in (0,5) else 0) for delta in range(99) if delta%15 in (0,3,5,8)]
        assert [((t-origin)%DAY,v) for t,v in m.gates()]==expected
        assert m.speaker==0xa0 and m.get('_speaker_owned')==0
        done('paired880-timing-clean-expiry-wrap-'+str(start))
    for enabled,seconds in ((0,5),(1,0),(0,0)):
        m=Alert(seconds,enabled);m.connect();m.poll(10);assert not m.sounds
        done('quiet-policy-%d-%d'%(enabled,seconds))
    m=Alert(enabled=65535);m.connect();assert m.speaker==0xa3;m.far('stop');assert m.speaker==0xa0
    done('any-nonzero-sound-flag-enables')
    m=Alert(port=0xa3);m.connect();m.poll(10);assert not m.sounds and m.speaker==0xa3
    done('foreign-active-speaker-never-stolen-or-silenced')
    for response in (b'BUSY',b'NO CARRIER',b'VOICE',b'TIMEOUT'):
        m=Alert();m.start();m.waiting();m.receive(response);m.poll(25);assert not m.sounds
        done('no-alert-on-'+response.decode())
    m=Alert();m.connect();at=len(m.tx);m.keys.append(ord('q'));m.call('terminal_poll_io');m.drain()
    assert bytes(m.tx[at:])==b'q' and m.speaker==0xa0
    done('keypress-stops-alert-and-is-transmitted-once')
    for field in ('terminal_program_pending','terminal_program_active','terminal_transfer_pending','terminal_transfer_active','terminal_quit'):
        m=Alert();m.connect();m.put(field,1);m.far('poll');assert m.speaker==0xa0
        done('cleanup-'+field)
    m=Alert();m.connect();m.carrier=False;m.poll(6);assert m.state()==0 and m.speaker==0xa0
    done('confirmed-carrier-loss-silences')
    for function in ('terminal_connection_cancel','terminal_connection_exit'):
        m=Alert();m.connect();m.call(function,ax=1);assert m.speaker==0xa0
        done('cleanup-'+function)
    m=Alert();m.connect();before=list(m.sounds);m.far('stop',flags=2)
    assert m.sounds==before and m.get('_speaker_owned')==1
    m.far('stop');assert m.speaker==0xa0 and m.get('_speaker_owned')==0
    done('invalid-IF-stop-retains-owner-for-repaired-cleanup')
    m=Alert();m.connect();m.tick=DAY;m.far('poll');assert m.speaker==0xa0
    done('invalid-clock-silences')
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    result=dict(passed=True,cases=cases,binary_sha256=sha(a.terminal),
        sources={n:sha(ROOT/n) for n in ('standalone/check_connect_alert.py','src/ui/connect_alert.c','src/ui/speaker.c','src/ui/speaker_native.asm','src/terminal/connect_alert_bridge.asm')},
        scope=__doc__+' Actual linked PIT/speaker and UART instructions with hardware/BIOS-clock model. No acoustic or physical modem acceptance.')
    (a.output/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS',len(cases),'connect alert/timing/ownership cases')

if __name__=='__main__':main()
