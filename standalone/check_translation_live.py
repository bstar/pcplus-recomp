#!/usr/bin/env python3
"""Actual linked XLT loader/far ABI, UART, parser, capture and raw monitor.

Only DOS/BIOS/UART boundaries are modeled; no product callback is skipped.
"""
import hashlib
import json
import struct
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
from check_terminal_monitor_live import Monitor
from check_meta_actions_live import ROOT, BINARY


class Translation(Monitor):
    def __init__(self, fault=None):
        super().__init__()
        self.xlt_fault = fault
        self.xlt_calls = []
        self.xlt_handles = set()
        self.far_seen = False
        self.max_stack = 0
        self.uc.hook_add(UC_HOOK_CODE, self.observe_translation)
        self.put('attributes_monochrome', 1)
        self.put('csi_terminal_id', 6)
        self.call('csi_clear_tabs', [1])
        self.call('terminal_clear_home')
        assert self.call('terminal_reset_capture') == 0

    def observe_translation(self, u, address, size, _):
        if self.symbols['terminal_config_code_start'] <= address < self.symbols['terminal_config_code_end']:
            self.far_seen = True
            assert u.reg_read(UC_X86_REG_DS) == u.reg_read(UC_X86_REG_SS) == self.ds
            self.max_stack = max(self.max_stack, self.offset('terminal_stack_top') - u.reg_read(UC_X86_REG_SP))

    def interrupt(self, u, number, data):
        ax = u.reg_read(UC_X86_REG_AX)
        ah = ax >> 8
        handle = u.reg_read(UC_X86_REG_BX)
        if number != 0x21 or not (ax == 0x3d00 or ah in (0x3f, 0x3e) and handle in self.xlt_handles):
            return super().interrupt(u, number, data)
        error = answer = 0
        if ah == 0x3d:
            name = self.path(u.reg_read(UC_X86_REG_DS), u.reg_read(UC_X86_REG_DX))
            if name not in self.files or self.xlt_fault == 'open':
                error = 2
            else:
                answer = next(h for h in range(5, 64) if h not in self.handles)
                self.handles[answer] = name
                self.positions[answer] = 0
                self.xlt_handles.add(answer)
        else:
            name = self.handles[handle]
            if ah == 0x3f:
                if self.xlt_fault == 'read' or self.xlt_fault == 'probe' and self.positions[handle] == 256:
                    error = 5
                else:
                    count = u.reg_read(UC_X86_REG_CX)
                    if self.xlt_fault == 'fragment':
                        count = min(count, 13)
                    at = self.positions[handle]
                    blob = bytes(self.files[name][at:at + count])
                    answer = len(blob)
                    if blob:
                        u.mem_write(u.reg_read(UC_X86_REG_DS) * 16 + u.reg_read(UC_X86_REG_DX), blob)
                    self.positions[handle] += answer
            elif ah == 0x3e:
                if self.xlt_fault == 'close':
                    error = 6
                else:
                    self.xlt_handles.remove(handle)
                    del self.handles[handle]
                    del self.positions[handle]
        self.xlt_calls.append((ah, name, error, answer))
        u.reg_write(UC_X86_REG_AX, error or answer)
        self.set_carry(bool(error))

    def load(self, blob, selected=True):
        if blob is not None:
            self.files['TEST.XLT'] = bytearray(blob)
        self.uc.mem_write(self.symbols['terminal_translation_path'], b'TEST.XLT\0')
        self.put('terminal_option_mask', 16384 if selected else 0)
        result = self.call('terminal_load_translation')
        for reg, want in [(UC_X86_REG_BP, 0xbabe), (UC_X86_REG_SI, 0x1234),
                          (UC_X86_REG_DI, 0x5678), (UC_X86_REG_ES, 0xb800)]:
            assert self.uc.reg_read(reg) == want
        return result

    def feed_normal(self, blob):
        self.receive_irq(blob)
        while self.get('uart_rx_count'):
            value = self.call('uart_receive_byte')
            self.call('terminal_receive_input', ax=value, limit=1000000)
            assert not self.get('terminal_parser_active')


def main():
    groups = []

    def check(name, fn):
        count = fn()
        groups.append(dict(case=name, inputs=count, passed=True))
        print(name, 'PASS', count, flush=True)

    def loading():
        mapping = bytes((i * 73 + 19) & 255 for i in range(256))
        for fault in (None, 'fragment'):
            m = Translation(fault)
            assert m.load(mapping) == 0 and m.get('terminal_translation_enabled') == 1
            assert bytes(m.uc.mem_read(m.symbols['terminal_translation_table'], 256)) == mapping
            assert m.far_seen and not m.handles and m.max_stack < 1024
            for value in range(256):
                assert m.call('terminal_translate_input', ax=value) == mapping[value]
            assert bytes(m.files['TEST.XLT']) == mapping
        m = Translation()
        assert m.load(None, selected=False) == 0 and not m.xlt_calls
        assert not m.get('terminal_translation_enabled')
        return 513
    check('checked-loader-far-C-register-services-all256-mappings-and-disabled-no-IO', loading)

    def errors():
        for size in (0, 1, 255, 257, 512):
            m = Translation()
            m.uc.mem_write(m.symbols['terminal_translation_table'], b'\x97' * 256)
            assert m.load(bytes(size)) == 12 and not m.get('terminal_translation_enabled')
            assert m.get('terminal_translation_status') == 4 and not m.handles
            assert bytes(m.uc.mem_read(m.symbols['terminal_translation_table'], 256)) == b'\x97' * 256
        for fault, status in [('open', 2), ('read', 3), ('probe', 3), ('close', 5)]:
            m = Translation(fault)
            m.uc.mem_write(m.symbols['terminal_translation_table'], b'\x97' * 256)
            assert m.load(bytes(range(256))) == 12
            assert m.get('terminal_translation_status') == status
            assert not m.get('terminal_translation_enabled')
            assert bytes(m.uc.mem_read(m.symbols['terminal_translation_table'], 256)) == b'\x97' * 256
            assert sum(c[0] == 0x3e for c in m.xlt_calls) == (fault != 'open')
        return 9
    check('failed-load-keeps-table-disabled-preserves-bytes-and-closes-once', errors)

    def parser():
        mapping = bytearray(range(256))
        mapping[ord('Q')] = 27
        mapping[ord('x')] = ord('y')
        mapping[ord('[')] = ord('!')
        m = Translation()
        assert m.load(mapping) == 0
        assert m.begin() == 0
        m.feed_normal(b'Q[HxQ[6n')
        m.call('_capture_session_flush')
        assert bytes(m.uc.mem_read(0xb8000, 2)) == b'y\x07'
        assert bytes(m.uc.mem_read(m.symbols['terminal_history_buffer'], 1)) == b'y'
        assert bytes(m.files['LOG.TXT']) == b'y'
        m.drain()
        assert bytes(m.tx) == b'\x1b[1;2R'
        assert not m.get('uart_rx_count')
        before = bytes(m.uc.mem_read(m.symbols['terminal_translation_table'], 256))
        m.feed_normal(b'Qc')
        assert m.get('terminal_translation_enabled') == 1
        assert bytes(m.uc.mem_read(m.symbols['terminal_translation_table'], 256)) == before
        m.feed_normal(b'x')
        assert bytes(m.uc.mem_read(0xb8000, 2)) == b'y\x07'
        m.key(ord('x'));m.drain()
        assert bytes(m.tx).endswith(b'x')
        assert bytes(m.files['TEST.XLT']) == mapping
        return 5
    check('mapped-ESC-render-and-capture-raw-parser-continuation-raw-replies-TX-and-RIS', parser)

    def monitor():
        m = Translation()
        assert m.load(bytes([ord('Z')]) * 256) == 0
        m.enter()
        blob = bytes(range(256))
        assert m.feed(blob) == blob
        m.stop()
        assert m.dump() == blob and not m.handles
        return 256
    check('active-XLT-does-not-change-raw-monitor-DOS-dump', monitor)
    result = dict(passed=True, binary_sha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),
                  cases=groups, inputs=sum(g['inputs'] for g in groups),
                  scope='Actual linked loader/far ABI, UART, normal receive owner, parser, capture, raw monitor and RIS; hardware/DOS API boundaries modeled. Full main-loop ordering and pre-UART rejection also need actual DOS tests.')
    (ROOT / 'build/terminal/translation-live-checks.json').write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    main()
