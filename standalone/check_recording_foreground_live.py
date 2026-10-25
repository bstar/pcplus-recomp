#!/usr/bin/env python3
"""Execute the actual terminal's stable recorder owner; kernel/hardware modeled.

This invokes the compiled far APIs and resident DOS backend, without patching
product code. It does not accept Record UI, automatic taps or physical hardware.
"""
import hashlib
import json
import re
import struct
from unicorn.x86_const import *
from check_terminal_capture_live import Capture
from check_meta_actions_live import ROOT, BINARY
import check_transport as transport


class Recorder(Capture):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        listing = transport.MAP.read_text()
        self.entries = {n: (int(s, 16), int(o, 16)) for s, o, n in re.findall(
            r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$', listing, re.M | re.I)}

    def far(self, suffix, arguments=()):
        name = '_recording_terminal_' + suffix
        segment, offset = self.entries[name]
        words = [self.return_offset, self.code_segment, *arguments]
        sp = self.offset('terminal_stack_top') - 2 * len(words)
        self.uc.mem_write(self.data_base + sp, struct.pack('<' + 'H' * len(words), *words))
        for register, value in ((UC_X86_REG_CS, self.base_segment + segment),
                (UC_X86_REG_DS, self.ds), (UC_X86_REG_SS, self.ds),
                (UC_X86_REG_SP, sp), (UC_X86_REG_BP, 0xbabe), (UC_X86_REG_EFLAGS, 0x202)):
            self.uc.reg_write(register, value)
        self.returned = False
        self.uc.emu_start(self.symbols[name], 0, count=300000)
        assert self.returned and self.uc.reg_read(UC_X86_REG_SP) == sp + 4, name
        assert self.uc.reg_read(UC_X86_REG_DS) == self.uc.reg_read(UC_X86_REG_SS) == self.ds
        assert self.uc.reg_read(UC_X86_REG_BP) == 0xbabe
        return self.uc.reg_read(UC_X86_REG_AX)

    def state(self):
        return bytes(self.uc.mem_read(self.symbols['_recording_terminal_owner'], 326))

    def field(self, name):
        fields = ('state', 'status', 'dos_error', 'close_error', 'cleanup_error', 'publish_error',
                  'restore_error', 'reservation_error', 'mode', 'busy', 'claimed', 'stage_owned',
                  'backup_owned', 'published', 'handle_state', 'sequence', 'directory_length')
        return struct.unpack_from('<H', self.state(), 136 + 2 * fields.index(name))[0]

    def initialize(self):
        self.uc.mem_write(self.symbols['_recording_terminal_owner'], b'\xa5' * 326)
        self.uc.mem_write(self.symbols['_recording_terminal_path'], b'\xa5' * 64)
        assert self.far('inspect') == 0
        assert self.far('initialize') == 0 and self.state() == bytes(326)
        assert self.far('inspect') == self.offset('_recording_terminal_owner')
        path = bytes(self.uc.mem_read(self.symbols['_recording_terminal_path'], 64))
        assert path == b'PCPLUS.ASP\0' + bytes(53)

    def begin_recording(self, mode=1):
        return self.far('begin', [mode, 1])


def main():
    cases = []
    def check(name, function):
        function()
        cases.append(dict(case=name, passed=True))
        print(name, 'PASS', flush=True)

    def dirty_and_exact():
        m = Recorder()
        m.initialize()
        assert m.begin_recording() == 0
        before = m.state()
        assert m.far('initialize') == m.begin_recording() == 2 and m.state() == before
        for byte in b'READY>':
            assert m.far('transmit', [byte]) == 0
        for byte in b'Name? ':
            assert m.far('receive', [byte]) == 0
        for byte in range(256):
            assert m.far('transmit', [byte]) == 0
        assert m.far('stop') == 0 and m.field('published') == 1 and not m.handles
        header = b'; LoC ASPECT recording - maintained runtime required\r\nstring loc_prompt\r\nproc main\r\n'
        expected = header + b'transmitraw "52454144593E"\r\nstrcpy loc_prompt "Name? "\r\nwaitfor loc_prompt 1\r\nif waitfor == 0\r\nexit\r\nendif\r\n'
        payload = bytes(range(256))
        expected += b''.join(b'transmitraw "' + payload[i:i+40].hex().upper().encode() + b'"\r\n' for i in range(0, 256, 40))
        expected += b'endproc\r\n'
        assert bytes(m.files['PCPLUS.ASP']) == expected
        calls = len(m.capture_calls) + len(m.fs_calls)
        assert m.far('stop') == m.far('shutdown') == 0
        assert len(m.capture_calls) + len(m.fs_calls) == calls
    check('dirty-state-initialization-stable-owner-and-exact-source', dirty_and_exact)

    def shutdown():
        m = Recorder();m.initialize();m.files['PCPLUS.ASP'] = bytearray(b'ORIGINAL')
        assert m.begin_recording(2) == 0 and m.far('transmit', [65]) == 0
        assert m.far('shutdown') == 0 and m.field('status') == 14 and not m.handles
        assert m.files == {'PCPLUS.ASP': bytearray(b'ORIGINAL')}
        before = m.state();calls = len(m.capture_calls) + len(m.fs_calls)
        assert m.far('shutdown') == 0 and m.state() == before
        assert len(m.capture_calls) + len(m.fs_calls) == calls
    check('shutdown-cancels-unpublished-replacement-preserving-original', shutdown)

    def uncertain():
        m = Recorder(fault='close');m.initialize()
        assert m.begin_recording() == 0 and m.far('stop') == 9
        assert m.field('handle_state') == 2 and m.field('claimed') == 1
        before = m.state();calls = len(m.capture_calls) + len(m.fs_calls)
        assert m.far('initialize') == m.begin_recording() == m.far('shutdown') == 13
        assert m.state() == before and len(m.capture_calls) + len(m.fs_calls) == calls
        assert m.handles and len(m.files) == 1 and 'PCPLUS.ASP' not in m.files
    check('ambiguous-close-retains-stage-handle-and-owner-without-retry', uncertain)

    def denied():
        m = Recorder();m.initialize()
        assert m.begin(b'PCPLUS.ASP') == 0
        assert m.begin_recording() == 2 and m.field('reservation_error') == 2
        m.log(b'CAPTURE');assert m.call('_capture_session_stop') == 0
        assert bytes(m.files['PCPLUS.ASP']) == b'CAPTURE' and m.far('shutdown') == 0
        assert not m.handles and not any(n.endswith('.TMP') for n in m.files)
    check('existing-capture-denies-recorder-and-keeps-writing', denied)

    def independent():
        m = Recorder();m.initialize();assert m.begin() == 0 and m.begin_recording() == 0
        m.log(b'LOG');assert m.far('transmit', [0xff]) == 0 and m.far('stop') == 0
        assert m.call('_capture_session_stop') == 0
        assert bytes(m.files['LOG.TXT']) == b'LOG' and b'transmitraw "FF"' in m.files['PCPLUS.ASP']
    check('independent-capture-and-recorder-coexist', independent)

    def failed_write():
        m = Recorder(fault='write');m.initialize()
        assert m.begin_recording() == 8 and not m.handles and not m.files
        assert m.far('shutdown') == 8
    check('failed-header-write-removes-only-owned-stage-and-retains-error', failed_write)

    result = dict(passed=True, binary_sha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(), cases=cases,
        source_sha256=hashlib.sha256(__import__('pathlib').Path(__file__).read_bytes()).hexdigest(),
        scope=__doc__)
    (ROOT / 'build/terminal/recording-foreground-checks.json').write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    main()
