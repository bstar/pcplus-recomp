#!/usr/bin/env python3
"""Actual linked recorder RX/filter/parser paths; kernel/hardware modeled."""
import hashlib
import json
import struct
import re
from pathlib import Path
from check_recording_foreground_live import Recorder, ROOT, BINARY


def ready():
    m=Recorder();m.advance_ticks=True
    m.put('_recording_terminal_replay',0xdead);m.put('_recording_terminal_unread_pointer',0xbeef)
    m.initialize()
    assert m.get('_recording_terminal_replay')==m.get('_recording_terminal_unread_pointer')==0
    assert m.begin_recording()==0
    return m


def received(m):return struct.unpack_from('<I',m.state(),128)[0]
def tail(m):return m.state()[108:108+struct.unpack_from('<H',m.state(),64)[0]]
def inject(m,data):
    # Recorder's parent delivers pending hardware IRQs automatically. Do not
    # also call the ISR directly: that would manufacture an empty extra read.
    m.rx.extend(data);m.call('uart_poll_flow');assert not m.rx
def ordinary(m,data):
    inject(m,data)
    while m.get('uart_rx_count'):
        value=m.call('uart_receive_byte');assert value!=65535
        m.call('terminal_receive_input',ax=value,limit=1000000)


def main():
    cases=[]
    def check(name,function):
        function();cases.append(dict(case=name,passed=True));print(name,'PASS',flush=True)

    def raw_translation():
        m=ready();table=bytes((v+17)&255 for v in range(256))
        m.uc.mem_write(m.symbols['terminal_translation_table'],table);m.put('terminal_translation_enabled',1)
        ordinary(m,b'ABC> ')
        assert received(m)==5 and tail(m)==b'ABC> '
        assert m.far('transmit',[ord('!')])==0 and m.far('stop')==0
        assert b'strcpy loc_prompt "ABC> "' in m.files['PCPLUS.ASP']
    check('normal-RX-is-recorded-before-input-translation',raw_translation)

    def parser():
        m=ready();data=b'A\x1b[31mHELLO\x1b[0m> '
        ordinary(m,data)
        assert received(m)==len(data) and tail(m)==data[-16:]
        assert m.far('stop')==0
    check('native-ANSI-parser-continuations-retain-exact-sliding-raw-prompt',parser)

    def replay(wrap=False,normal=False):
        m=ready()
        if wrap:
            last=m.get('uart_rx_last');m.put('uart_rx_read',last);m.put('uart_rx_write',last)
        inject(m,b'AB')
        assert m.call('ansi_next_byte')==65
        m.call('ansi_unread_byte')
        assert m.get('_recording_terminal_replay')==1
        before=m.state()
        assert m.far('initialize')==2 and m.state()==before and m.get('_recording_terminal_replay')==1
        if normal:
            value=m.call('uart_receive_byte');assert value==65
            m.call('terminal_receive_input',ax=value)
        else:assert m.call('ansi_next_byte')==65
        assert m.call('ansi_next_byte')==66
        assert received(m)==2 and tail(m)==b'AB' and not m.get('_recording_terminal_replay')
        assert m.far('stop')==0 and b'strcpy loc_prompt "AB"' in m.files['PCPLUS.ASP']
    check('parser-unreceive-is-observed-once',replay)
    check('parser-unreceive-across-physical-ring-wrap',lambda:replay(wrap=True))
    check('parser-unreceive-returning-to-normal-owner-is-observed-once',lambda:replay(normal=True))

    def identical():
        m=ready();ordinary(m,b'AAAA')
        assert received(m)==4 and tail(m)==b'AAAA'
        assert m.far('cancel')==14
    check('distinct-identical-wire-bytes-are-not-deduplicated',identical)

    def timeout():
        m=ready();assert m.call('ansi_next_byte',limit=1000000)==65535
        assert not received(m) and not tail(m)
        assert m.far('stop')==0 and b'waitfor' not in m.files['PCPLUS.ASP']
    check('continuation-timeout-sentinel-is-not-recorded',timeout)

    def lifecycle():
        m=ready();inject(m,b'A');assert m.call('ansi_next_byte')==65
        m.call('ansi_unread_byte');assert m.get('_recording_terminal_replay')==1
        assert m.far('cancel')==14 and not m.get('_recording_terminal_replay')
        assert m.begin_recording()==0 and m.call('ansi_next_byte')==65
        assert received(m)==1 and tail(m)==b'A'
        assert m.far('stop')==0
    check('new-session-does-not-inherit-parser-replay-marker',lifecycle)

    def autostart():
        m=ready();m.put('_terminal_transfer_preferences',1)
        assert m.call('_terminal_auto_allowed')==0
        for value in b'Ordinary prompt> ':m.call('_terminal_autostart_input',[value])
        assert received(m)==17 and tail(m)==b'rdinary prompt> '
        assert not m.get('terminal_transfer_pending')
        assert m.far('cancel')==14 and m.call('_terminal_auto_allowed')==1
    check('active-recorder-disables-invitation-owner-and-delivers-ordinary-input',autostart)

    def query_and_user():
        m=ready();data=b'\x1b[6nName? '
        ordinary(m,data)
        assert received(m)==len(data) and tail(m)==data
        m.call('terminal_enqueue_user_al',ax=ord('U'));m.drain()
        assert bytes(m.tx).startswith(b'\x1b[') and bytes(m.tx).endswith(b'U')
        assert m.far('stop')==0
        source=bytes(m.files['PCPLUS.ASP'])
        recorded=b''.join(bytes.fromhex(x.decode()) for x in re.findall(rb'^transmitraw "([0-9A-F]*)"\r?$',source,re.M))
        assert recorded==b'U' and b'waitfor loc_prompt 1' in source
        assert source.index(b'waitfor loc_prompt')<source.index(b'transmitraw "55"')
    check('native-query-reply-excluded-while-prompt-precedes-accepted-user-TX',query_and_user)

    result=dict(passed=True,binary_sha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),cases=cases,
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        scope=__doc__+' No Record UI, full transition exclusions, actual DOS recording/BBS or physical acceptance.')
    (ROOT/'build/terminal/recording-rx-checks.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':main()
