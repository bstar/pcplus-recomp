#!/usr/bin/env python3
"""Linked Alt-Y/reference/browser, configured answer-on, serviced notice and sound.
Actual dispatch/owner/parser/speaker instructions; DOS/BIOS/UART/PIT boundaries modeled.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from check_call_timer_live import Clock,configure,ROOT
from check_manual_init_dispatch_live import stable,ordinary
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

class Answer(Clock):
    def __init__(self,*,online=False,enabled=0,duplex=0,port=0xa0):
        self.speaker=port;self.sounds=[]
        super().__init__()
        if online:self.now=100;self.connect(b'CONNECT\r\n')
        self.tx.clear();self.put('_terminal_sound_enabled',enabled);self.put('modes_value_1d1a',duplex)
        self.uc.mem_write(self.symbols['terminal_modem_settings']+140,b'ATS0=1^M\0'+bytes(16))
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
    def notice(self):return self.get('terminal_auto_answer_notice_active')
    def near(self,name,args=()):
        # Actual CONFIG_CODE near-cdecl API; no product callback is replaced.
        seg,offset=self.entries[name];cs=self.base_segment+seg;sentinel=0xfffe
        sp=self.offset('terminal_stack_top')-2*(len(args)+1)
        self.uc.mem_write(self.data_base+sp,struct.pack('<'+'H'*(len(args)+1),sentinel,*args))
        for r,v in ((UC_X86_REG_CS,cs),(UC_X86_REG_DS,self.ds),(UC_X86_REG_SS,self.ds),
                    (UC_X86_REG_SP,sp),(UC_X86_REG_EFLAGS,0x202),(UC_X86_REG_BP,0xbabe)):
            self.uc.reg_write(r,v)
        returned=[]
        def stop(u,address,size,_):
            if address==cs*16+sentinel:
                returned.append(True);u.emu_stop()
        hook=self.uc.hook_add(UC_HOOK_CODE,stop)
        try:self.uc.emu_start(self.symbols[name],0,count=1000000)
        finally:self.uc.hook_del(hook)
        assert returned and self.uc.reg_read(UC_X86_REG_SP)==sp+2 and self.uc.reg_read(UC_X86_REG_BP)==0xbabe
        assert self.uc.reg_read(UC_X86_REG_DS)==self.uc.reg_read(UC_X86_REG_SS)==self.ds
        return self.uc.reg_read(UC_X86_REG_AX)
    def active(self):return self.get('terminal_manual_init_active')
    def finish(self):
        for _ in range(600):
            if not self.active() and not self.notice() and not self.get('_speaker_owned'):return
            self.poll()
        raise AssertionError('answer/notice/tone not retired')

def direct(online=False,enabled=0,duplex=0):
    m=Answer(online=online,enabled=enabled,duplex=duplex);before=stable(m)
    m.key(0x1500)
    assert m.active() and m.notice() and b'AUTO ANSWER...' in m.text()[1920:]
    assert not m.tx and m.get('terminal_manual_command_kind')==1
    m.finish();assert bytes(m.tx)==b'ATS0=1\r' and stable(m)==before
    assert b'AUTO ANSWER...' not in m.text() and not m.notice()
    if enabled:
        assert [(p,v) for _,p,v in m.sounds]==[(0x43,0xb6),(0x42,0x97),(0x42,0x0a),(0x61,0xa3),(0x61,0xa0)]
    else:assert not m.sounds
    if duplex:assert m.text().startswith(b'ATS0=1')
    return 1

def menus():
    for browser in (False,True):
        m=Answer()
        if browser:
            m.key(ord('`'));m.key(ord('/'))
            for value in b'Auto Answer':m.key(value)
            m.key(13);m.key(27);m.key(13)
        else:m.key(0x2c00);m.key(0x1500)
        assert m.active() and m.notice() and not m.get('_command_menu_active') and not m.get('_redisplay_active')
        assert b'COMMUNICATIONS' not in m.text()
        m.finish();assert bytes(m.tx)==b'ATS0=1\r'
    return 2

def rx_and_typeahead():
    m=Answer(online=True);before=stable(m);m.key(0x1500)
    m.key(ord('x'));m.key(0x1500);m.key(0x2400)
    assert m.get('terminal_deferred_count')==1
    ordinary(m,b'\x1b[24;1HLATEST\x1b[6nOK\r\n')
    assert m.notice() and b'LATEST' in m.text() and m.get('terminal_tx_count')>0
    m.finish();m.drain()
    assert bytes(m.tx).startswith(b'ATS0=1\r\x1b[24;7R') and bytes(m.tx).endswith(b'x')
    assert b'LATEST' in m.text() and b'AUTO ANSWER...' not in m.text()
    assert stable(m)==before
    return 1

def lifecycle():
    count=0
    for key,reason in ((27,3),(0x2300,3),(0x2d00,8)):
        m=Answer(online=True,enabled=1);m.key(0x1500);m.key(key)
        assert not m.active() and not m.notice() and m.get('terminal_manual_init_status')==reason
        assert m.speaker==0xa0 and not m.get('_speaker_owned') and bytes(m.tx)==b'A'
        assert b'AUTO ANSWER...' not in m.text() and m.get('connection_resync',1)==1
        count+=1
    m=Answer(online=True,enabled=1);m.key(0x1500);m.poll();m.thre=False;m.carrier=False;m.now=107;m.poll(8)
    assert not m.active() and not m.notice() and m.get('terminal_manual_init_status')==7
    assert m.state()==0 and m.duration()=='00:00:07' and m.speaker==0xa0
    assert b'Carrier lost' in m.text()[1920:] and b'AUTO ANSWER...' not in m.text()
    m.carrier=True;m.thre=True;m.tx.clear();m.now=110;m.connect(b'CONNECT\r\n')
    assert bytes(m.tx)==b'\rATZ\rATDLocal.Example:2323\r'
    return count+1

def stalls():
    count=0
    for kind in ('thre','cts','xoff'):
        m=Answer(online=True,enabled=1);m.key(0x1500)
        if kind=='thre':m.thre=False
        if kind=='cts':m.cts=False
        if kind=='xoff':m.put('uart_software_flow',1);m.put('uart_tx_paused',1)
        m.poll(38)
        assert not m.active() and not m.notice() and m.get('terminal_manual_init_status')==4
        assert not m.tx and m.speaker==0xa0 and m.state()==6 and m.get('terminal_call_timer_running')
        count+=1
    return count

def empty_and_invalid():
    m=Answer(enabled=1);m.uc.mem_write(m.symbols['terminal_modem_settings']+140,bytes(25))
    m.key(0x1500);assert not m.active() and m.notice() and m.speaker==0xa3
    m.finish();assert not m.tx and not m.notice() and m.speaker==0xa0
    m=Answer(enabled=1);m.uc.mem_write(m.symbols['terminal_modem_settings']+140,b'X'*25)
    before=m.text();m.key(0x1500)
    assert not m.active() and not m.notice() and not m.tx and not m.sounds and m.text()==before
    return 2

def foreign_sound():
    m=Answer(enabled=1,port=0xa3);m.key(0x1500)
    assert not m.sounds and m.speaker==0xa3
    # The command completes normally even if hardware is already sounding.
    for _ in range(30):m.poll()
    assert bytes(m.tx)==b'ATS0=1\r' and not m.notice() and m.speaker==0xa3 and not m.sounds
    m=Answer(enabled=1);m.key(0x1500)
    assert m.near('_speaker_stop')==0
    assert m.near('_speaker_start',[220,10,0x4240,15])==1
    generation=m.get('_speaker_generation_word');at=len(m.sounds)
    m.far('terminal_auto_answer_ui_stop_far')
    assert m.get('_speaker_generation_word')==generation and m.speaker==0xa3 and len(m.sounds)==at
    assert not m.notice();assert m.near('_speaker_stop')==0
    return 2

def mute_during_tone():
    m=Answer(enabled=1);m.key(0x1500);assert m.speaker==0xa3 and m.notice()
    m.put('_terminal_sound_enabled',0);m.poll()
    assert m.speaker==0xa0 and not m.get('_speaker_owned') and m.notice() and m.active()
    m.finish();assert bytes(m.tx)==b'ATS0=1\r'
    return 1

def admission():
    count=0
    for field in ('terminal_parser_active','terminal_program_pending','terminal_transfer_pending','uart_break_hold'):
        m=Answer();m.put(field,1);m.key(0x1500)
        assert not m.active() and not m.notice() and not m.sounds
        assert m.get('terminal_deferred_count')==1
        m.put(field,0);m.call('terminal_poll_io');assert m.active() and m.notice()
        m.finish();count+=1
    for kind in ('mode','columns','page','height','terminal_rows'):
        m=Answer(enabled=1)
        if kind=='height':m.uc.mem_write(0x484,b'\x31')
        elif kind=='terminal_rows':m.put('screen_last_row',24)
        else:setattr(m,kind,7 if kind=='mode' else 40 if kind=='columns' else 1)
        before=m.text();m.key(0x1500)
        assert not m.active() and not m.notice() and not m.tx and not m.sounds and m.text()==before
        count+=1
    return count

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    configure(a.terminal);assert json.loads((a.terminal.parent/'manifest.json').read_text())['experimental_auto_answer']
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False);cases=[]
    for name,fn in [('idle-quiet-no-echo',direct),('online-nonzero-sound-and-local-echo',lambda:direct(True,65535,1)),
                    ('reference-and-browser-restoration',menus),('normal-RX-CPR-typeahead-and-underlay',rx_and_typeahead),
                    ('cancel-hangup-exit-qualified-loss-and-redial',lifecycle),('flow-stall-timeout-cleanup',stalls),
                    ('empty-and-invalid-configured-answer',empty_and_invalid),('foreign-speaker-and-generation-ownership',foreign_sound),
                    ('mute-stops-only-owned-tone-while-notice-remains',mute_during_tone),
                    ('deferred-owners-and-unsupported-video',admission)]:
        count=fn();cases.append(dict(case=name,inputs=count,passed=True));print(name,count,'PASS',flush=True)
    paths=[Path(__file__).resolve(),ROOT/'src/terminal/modem_answer_ui.asm',ROOT/'src/terminal/manual_init_dispatch.asm',ROOT/'src/terminal/local_controls.asm',ROOT/'src/terminal/transport.asm']
    report=dict(passed=True,terminal_sha256=hashlib.sha256(a.terminal.read_bytes()).hexdigest(),cases=cases,
                sources={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
                scope=__doc__+' Maintained440Hz/four-BIOS-tick tone and status-row notice; no exact original pixels/calibrated timing, actual DOS/BBS/SIP/physical acceptance or deployment.')
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS live Auto Answer:',sum(c['inputs'] for c in cases),'inputs')

if __name__=='__main__':main()
