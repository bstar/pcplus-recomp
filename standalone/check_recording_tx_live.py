#!/usr/bin/env python3
"""Actual linked TX provenance and recorder; DOS/hardware boundaries are models."""
import hashlib
import json
import re
import struct
from pathlib import Path
from unicorn.x86_const import *
from check_recording_foreground_live import Recorder, ROOT, BINARY


def ready():
    m = Recorder();m.initialize();assert m.begin_recording() == 0
    return m


def queued(m, data, user):
    for value in data:
        assert m.call('terminal_enqueue_user_al' if user else 'terminal_enqueue_al', ax=value) == value


def recorded(m):
    assert m.far('stop') == 0
    source = bytes(m.files['PCPLUS.ASP'])
    return b''.join(bytes.fromhex(x.decode()) for x in re.findall(rb'^transmitraw "([0-9A-F]*)"\r?$', source, re.M))


def main():
    cases = []
    def check(name, function):
        function();cases.append(dict(case=name, passed=True));print(name, 'PASS', flush=True)

    def mixed():
        m = ready()
        for value in range(256):
            queued(m, bytes([value]), True);queued(m, bytes([255-value]), False)
        assert m.state()[38+86:38+90] == bytes(4) # No successfully emitted bytes yet.
        m.drain()
        assert bytes(m.tx) == b''.join(bytes([v, 255-v]) for v in range(256))
        assert recorded(m) == bytes(range(256))
        assert bytes(m.uc.mem_read(m.symbols['terminal_tx_origin_bits'], 128)) == bytes(128)
    check('all-octets-interleaved-with-report-bytes-record-only-user-wire', mixed)

    def stalls():
        m = ready();queued(m, b'U', True);queued(m, b'R', False)
        before = m.state();tags = bytes(m.uc.mem_read(m.symbols['terminal_tx_origin_bits'], 128))
        m.thre = False
        for i in range(5):m.call('terminal_poll_io')
        m.thre = True;m.cts = False;m.put('uart_hardware_flow', 1)
        for i in range(5):m.call('terminal_poll_io')
        assert not m.tx and m.state() == before and m.get('terminal_tx_count') == 2
        assert bytes(m.uc.mem_read(m.symbols['terminal_tx_origin_bits'], 128)) == tags
        m.cts = True;m.drain()
        assert bytes(m.tx) == b'UR' and recorded(m) == b'U'
    check('THRE-and-CTS-stalls-do-not-consume-origin-or-record-unsent-byte', stalls)

    def wrap():
        m = ready();m.put('terminal_tx_head', 1020);m.put('terminal_tx_tail', 1020)
        m.uc.mem_write(m.symbols['terminal_tx_origin_bits'], b'\xff'*128)
        expected = bytearray();wire = bytearray()
        for i in range(1024):
            value = i & 255;user = i % 3 == 0
            queued(m, bytes([value]), user);wire.append(value)
            if user:expected.append(value)
        assert m.get('terminal_tx_count') == 1024 and not m.get('terminal_quit')
        m.drain();assert bytes(m.tx) == wire and recorded(m) == expected
        assert bytes(m.uc.mem_read(m.symbols['terminal_tx_origin_bits'], 128)) == bytes(128)
    check('full-capacity-1024-slot-wrap-overwrites-dirty-origins', wrap)

    def reset():
        m = ready();queued(m, b'OLD', True)
        for name in ('terminal_tx_count', 'terminal_tx_head', 'terminal_tx_tail'):m.put(name, 0)
        queued(m, b'NEW', False);m.drain()
        assert bytes(m.tx) == b'NEW' and recorded(m) == b''
    check('discarded-queue-reuse-cannot-record-stale-user-origin', reset)

    def clipboard():
        m = ready();pointer = m.stage_near(b'PASTE!')
        assert m.call('_clipboard_transport', [0, pointer, 6]) == 0
        queued(m, b'REPLY', False)
        for i in range(3):m.call('terminal_poll_io')
        assert m.call('_clipboard_transport', [2, 0, 0]) == 0
        m.drain()
        assert bytes(m.tx) == b'PASREPLY' and recorded(m) == b'PAS'
    check('clipboard-prefix-cancel-preserves-later-unrecorded-replies', clipboard)

    def binding():
        m = ready();m.uc.mem_write(m.symbols['terminal_keymap']+5*12, b'A\xffB'+bytes(9))
        assert m.call('terminal_enqueue_key_slot', ax=5) == 0
        m.drain();assert bytes(m.tx) == b'A\0B' and recorded(m) == b'A\0B'
    check('expanded-key-binding-records-actual-FF-to-NUL-output', binding)

    def macro():
        m = ready();m.record(0, b'X\xffY~Z');assert m.start(0) == 0
        for tick in range(30):
            m.poll(tick)
            if not m.get('terminal_macro_active'):break
        assert not m.get('terminal_macro_active') and bytes(m.tx) == b'X\0YZ'
        assert recorded(m) == b'X\0YZ'
    check('direct-TEXT-binding-records-wire-bytes-and-excludes-pause-marker', macro)

    def transfer_drain():
        m = ready();queued(m, b'BEFORE', True);queued(m, b'R', False)
        m.peer_enabled = True;m.waiting_ui = True;m.filename = b'D:\\RECV.BIN';m.advance_ticks = True
        m.call('terminal_transfer_start')
        m.call('terminal_transfer_poll', limit=10000000)
        assert not m.get('terminal_transfer_fault') and not m.get('terminal_transfer_active')
        assert bytes(m.files['D:\\RECV.BIN']) == bytes(range(128))
        assert bytes(m.tx).startswith(b'BEFORER') and recorded(m) == b'BEFORE'
    check('transfer-drain-records-queued-user-prefix-and-excludes-protocol', transfer_drain)

    def write_error():
        m = ready();m.capture_fault = 'write'
        queued(m, bytes(range(100)), True);m.drain()
        assert bytes(m.tx) == bytes(range(100)) and m.field('status') == 8
        assert not m.files and not m.handles and m.far('stop') == 8
        assert bytes(m.uc.mem_read(m.symbols['terminal_tx_origin_bits'], 128)) == bytes(128)
    check('recorder-write-failure-preserves-already-accepted-serial-stream', write_error)

    def helper_abi():
        m = ready();assert m.far('receive', [ord('?')]) == 0
        for name in ('terminal_tx_origin_set_far', 'terminal_tx_origin_delivered_far', 'terminal_record_user_delivered_far'):
            for slot in (0, 7, 8, 15, 255, 511, 1023):
                segment, offset = m.entries[name]
                sp = m.offset('terminal_stack_top')-4
                m.uc.mem_write(m.data_base+sp, struct.pack('<HH', m.return_offset, m.code_segment))
                expected = {UC_X86_REG_AX:0x12ff,UC_X86_REG_BX:slot,UC_X86_REG_CX:0x5678,
                    UC_X86_REG_DX:1,UC_X86_REG_SI:0x2345,UC_X86_REG_DI:0x3456,UC_X86_REG_BP:0xbabe,
                    UC_X86_REG_ES:0x7200,UC_X86_REG_DS:m.ds,UC_X86_REG_SS:m.ds,UC_X86_REG_EFLAGS:0x247}
                for register,value in expected.items():m.uc.reg_write(register,value)
                m.uc.reg_write(UC_X86_REG_CS,m.base_segment+segment);m.uc.reg_write(UC_X86_REG_SP,sp)
                m.returned = False;m.uc.emu_start(m.symbols[name],0,count=10000)
                assert m.returned and m.uc.reg_read(UC_X86_REG_SP)==sp+4
                assert all(m.uc.reg_read(register)==value for register,value in expected.items()),(name,slot)
        assert recorded(m) == b'\xff'*14
    check('all-three-far-helpers-preserve-registers-flags-and-stack-at-bit-boundaries', helper_abi)

    result = dict(passed=True, binary_sha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(), cases=cases,
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        scope=__doc__+' No Record UI, RX taps, complete owner exclusions, actual DOS/BBS or physical acceptance.')
    (ROOT/'build/terminal/recording-tx-checks.json').write_text(json.dumps(result, indent=2)+'\n')


if __name__ == '__main__':main()
