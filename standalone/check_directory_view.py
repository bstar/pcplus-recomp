#!/usr/bin/env python3
"""Execute linked serviced directory, reader, UART and screen owner instructions.

Only kernel filesystem/BIOS/UART boundaries are modeled. No product routine is
patched, skipped, manually completed or supplied a fake return frame.
"""
import argparse
import hashlib
import json
import re
import tempfile
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import (UC_X86_REG_AX, UC_X86_REG_BX, UC_X86_REG_CX, UC_X86_REG_CS, UC_X86_REG_IP,
    UC_X86_REG_DX, UC_X86_REG_DS, UC_X86_REG_SS, UC_X86_REG_SP)
import struct
import check_transport as transport
from directory_view_fixture import fixture
from terminal_memory import inspect_terminal_memory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--terminal', type=Path, required=True)
    args = parser.parse_args()
    binary = args.terminal.resolve()
    manifest = json.loads((binary.parent / 'manifest.json').read_text())
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    assert manifest['experimental_directory_view'] and sha(binary) == manifest['binary_sha256']
    for name, digest in manifest['sources'].items():
        assert sha(transport.ROOT / name) == digest, name
    transport.BINARY, transport.MAP = binary, binary.parent / 'terminal.map'
    from check_recording_ui_live import UI
    from check_recording_rx_live import ordinary
    UI.browser_key = 0x2960

    class Directory(UI):
        def __init__(self, *, data=fixture(), short=0, close_error=False):
            self.directory_io = []
            self.directory_handles = set()
            self.short = short
            self.close_error = close_error
            self.leases = []
            super().__init__()
            if data is not None:
                self.files['PCPLUS.DIR'] = bytearray(data)
            self.uc.hook_add(UC_HOOK_CODE, self.observe)

        def observe(self, uc, address, size, user):
            if address != self.symbols['_directory_reader_begin']:
                return
            assert uc.reg_read(UC_X86_REG_DS) == uc.reg_read(UC_X86_REG_SS) == self.ds
            at = self.data_base + uc.reg_read(UC_X86_REG_SP) + 4
            r, path, first, so, ss, po, ps, scratch = struct.unpack('<8H', uc.mem_read(at, 16))
            assert ss * 16 + so == self.symbols['redisplay_snapshot']
            assert ps * 16 + po == self.symbols['redisplay_snapshot'] + 1394
            assert self.data_base + scratch == self.symbols['_directory_view_scratch']
            assert self.get('_redisplay_active') and self.get('_command_menu_active')
            self.leases.append(first)

        def interrupt(self, uc, number, user):
            ax = uc.reg_read(UC_X86_REG_AX)
            ah = ax >> 8
            handle = uc.reg_read(UC_X86_REG_BX)
            if number != 0x21 or not (ax == 0x3d80 or handle in self.directory_handles and ah in (0x3f, 0x3e)):
                return super().interrupt(uc, number, user)
            count, error, value = 0, 0, 0
            if ax == 0x3d80:
                path = self.path(uc.reg_read(UC_X86_REG_DS), uc.reg_read(UC_X86_REG_DX))
                if path not in self.files:
                    error = 2
                else:
                    value = next(h for h in range(5, 64) if h not in self.handles)
                    self.handles[value] = path
                    self.positions[value] = 0
                    self.directory_handles.add(value)
            elif ah == 0x3f:
                count = uc.reg_read(UC_X86_REG_CX)
                assert 0 < count <= 512
                pointer = uc.reg_read(UC_X86_REG_DS) * 16 + uc.reg_read(UC_X86_REG_DX)
                assert pointer == self.symbols['_directory_view_scratch']
                if self.short:
                    count = min(count, self.short)
                start = self.positions[handle]
                data = self.files[self.handles[handle]][start:start + count]
                self.positions[handle] += len(data)
                uc.mem_write(pointer, bytes(data))
                value = len(data)
            else:
                self.directory_handles.remove(handle)
                del self.positions[handle], self.handles[handle]
                error = 6 if self.close_error else 0
            self.directory_io.append(dict(operation=ah, requested=count, returned=value, error=error))
            uc.reg_write(UC_X86_REG_AX, error or value)
            self.set_carry(bool(error))

        def open(self):
            self.key(0x2000)
            assert b'DIALING DIRECTORY' in self.text() and not self.directory_io
            self.key(13)
            assert self.directory_io[-1]['operation'] == 0x3d
            assert not any(r['operation'] == 0x3f for r in self.directory_io)

        def idle(self):
            before = len(self.directory_io)
            try:
                self.call('terminal_redisplay_idle', limit=1000000)
            except Exception:
                cs, ip = self.uc.reg_read(UC_X86_REG_CS), self.uc.reg_read(UC_X86_REG_IP)
                print('Reader idle failure', hex(cs), hex(ip), self.directory_io[-3:], flush=True)
                raise
            assert len(self.directory_io) - before <= 1

        def finish(self):
            for i in range(1500):
                if b'Reading directory...' not in self.text():
                    return
                self.idle()
            raise AssertionError('Directory did not finish')

    cases = []
    def check(name, function):
        n = function()
        cases.append(dict(case=name, inputs=n, passed=True))
        print(name, n, flush=True)

    def damaged_bindings():
        listing = transport.MAP.read_text()
        entries = {n: int(s, 16) * 16 + int(o, 16) for s, o, n in re.findall(
            r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$', listing, re.M | re.I)}
        image = binary.read_bytes()
        header = struct.unpack_from('<14H', image)
        module = header[4] * 16
        service = entries['directory_dos_read_service_']
        resident = entries['directory_dos_read_service__resident']
        relocation = next(header[12] + i * 4 for i in range(header[3]) if
            (lambda pair: pair[0] + pair[1] * 16)(struct.unpack_from('<HH', image, header[12] + i * 4)) == service + 3)
        inspect_terminal_memory(binary, transport.MAP)
        with tempfile.TemporaryDirectory(prefix='pcplus-directory-ABI-') as temporary:
            target = Path(temporary) / 'DAMAGED.EXE'
            for kind in ('callee-cleanup', 'forwarded-word', 'loader-relocation'):
                damaged = bytearray(image)
                if kind == 'callee-cleanup':damaged[module + service + 5] = 0xc3
                elif kind == 'forwarded-word':damaged[module + resident + 5] = 6
                else:struct.pack_into('<HH', damaged, relocation, 0, 0)
                target.write_bytes(damaged)
                try:inspect_terminal_memory(target, transport.MAP)
                except AssertionError:pass
                else:raise AssertionError(('Damaged directory ABI accepted', kind))
        return 3
    check('reject-damaged-DOS-read-stack-forwarding-cleanup-and-loader-relocation', damaged_bindings)

    def loading():
        m = Directory()
        m.put('connection_state', 6)
        m.put('terminal_directory_entry', 7)
        before = {n: m.get(n) for n in ('terminal_option_mask', 'terminal_directory_entry', 'connection_state')}
        m.uc.mem_write(m.symbols['terminal_dial_target'], b'CURRENT:23' + bytes(54))
        retained = {n: bytes(m.uc.mem_read(m.symbols[n], length)) for n, length in [
            ('terminal_dial_target',64),('terminal_directory_path',64),
            ('terminal_configuration_values',44),('terminal_modem_settings',368),
            ('terminal_directory_plan',214),('terminal_directory_context',496),
            ('terminal_keymap',948),('terminal_action_definitions',540),
            ('terminal_keyboard_path',64),('terminal_actions_path',64),('_terminal_transfer_preferences',66)]}
        m.uc.mem_write(m.symbols['redisplay_snapshot'] + 2788, b'CANARY-DIRECTORY')
        m.open()
        for i in range(8):
            m.idle()
            frame = bytearray(m.uc.mem_read(0xb8000, 4000))
            frame[1124:1134] = bytes(10)  # Only the reader's progress count changes.
            m.call('terminal_redisplay_before')
            ordinary(m, b'\x1b[5;1HBBS-DURING-LOAD\x1b[6n')
            m.idle()
            m.drain()
            assert b'Reading directory...' in m.text()
            after = bytearray(m.uc.mem_read(0xb8000, 4000))
            after[1124:1134] = bytes(10)
            assert after == frame
        m.finish()
        assert b'LoSs oF CoNtRoL' in m.text() and b'A..\xdb\xff' in m.text()
        assert b'SECRETA' not in m.text() and b'HIDDENPASS' not in m.text()
        assert m.leases == [1] and not m.directory_handles and not m.get('uart_rx_dropped')
        assert bytes(m.uc.mem_read(m.symbols['redisplay_snapshot'] + 2788, len(b'CANARY-DIRECTORY'))) == b'CANARY-DIRECTORY'
        m.key(27)
        assert b'BBS-DURING-LOAD' in m.text() and not m.get('_redisplay_active')
        assert {n: m.get(n) for n in before} == before and not m.get('terminal_quit')
        for name, original in retained.items():
            assert bytes(m.uc.mem_read(m.symbols[name], len(original))) == original, name
        assert bytes(m.tx) == b'\x1b[5;16R' * 8
        assert bytes(m.files['PCPLUS.DIR']) == fixture()
        return 8
    check('incremental-live-parser-replies-safe-fields-and-updated-frame-return', loading)

    def navigation():
        m = Directory()
        m.open()
        m.finish()
        for key in (0x4fe0, 0x49e0, 0x4700, 0x5100):
            m.key(key)
            m.finish()
        assert m.leases == [1, 191, 181, 1, 11]
        assert b'Node 011' in m.text()
        m.key(0x3f00)
        m.finish()
        assert m.leases[-1] == 11
        m.key(27)
        assert not m.handles and not m.tx and not m.get('terminal_quit')
        return 5
    check('enhanced-and-ordinary-page-home-end-navigation-and-explicit-reload', navigation)

    def cancel():
        for turns in (0, 1, 20, 46, 47):
            m = Directory()
            m.open()
            for i in range(turns):
                m.idle()
            m.key(27)
            m.idle()
            assert not m.get('_redisplay_active') and not m.handles
            assert sum(x['operation'] == 0x3e for x in m.directory_io) == 1
            assert not m.tx and bytes(m.files['PCPLUS.DIR']) == fixture()
        return 5
    check('cancel-open-read-probe-and-before-publication-close-exactly-once', cancel)

    def errors():
        for data in (None, fixture()[:-1], fixture() + b'X'):
            m = Directory(data=data)
            m.open()
            m.finish()
            assert b'Could not load' in m.text() and b'LoSs oF CoNtRoL' not in m.text(), (None if data is None else len(data), m.text()[320:640], m.directory_io[-2:])
            m.key(0x3c00)
            assert b'Enter: open directory' in m.text()
            m.key(27)
            assert not m.handles and not m.get('terminal_quit')
        m = Directory(close_error=True)
        m.open()
        m.finish()
        assert b'Close uncertain' in m.text()
        calls = len(m.directory_io)
        m.key(27)
        m.key(0x2000)
        m.key(0x3c00)
        m.key(13)
        m.idle()
        assert b'Close uncertain' in m.text() and len(m.directory_io) == calls
        m.key(27)
        return 4
    check('missing-size-and-uncertain-close-errors-never-display-partial-pages', errors)

    def ownership():
        for name in ('terminal_browser_screen_owned', 'terminal_editor_screen_owned'):
            m = Directory()
            m.put(name, 1, 1)
            m.key(0x2000)
            assert not m.get('_redisplay_active') and not m.directory_io
        m = Directory()
        m.open()
        before = bytes(m.uc.mem_read(m.symbols['_directory_view_scratch'], 512))
        assert m.call('terminal_directory_choose') == 2
        assert bytes(m.uc.mem_read(m.symbols['_directory_view_scratch'], 512)) == before
        m.call('terminal_redisplay_stop')
        assert not m.handles and not m.get('_redisplay_active')
        m = Directory()
        m.open()
        m.key(0x2d00)
        assert m.get('terminal_quit') and not m.handles
        return 4
    check('bidirectional-scratch-lease-and-stop-AltX-resource-retirement', ownership)

    def entry_paths():
        for via in ('reference', 'browser'):
            m = Directory()
            if via == 'reference':
                m.key(0x2c00)
                m.key(13)
            else:
                m.menu()
                m.key(0x4d00)
                m.key(ord('L'))
            assert b'DIALING DIRECTORY' in m.text()
            m.key(27)
            assert (b'COMMUNICATIONS' if via == 'reference' else b'Browse dialing directory') in m.text()
            m.key(27)
            assert not m.get('_redisplay_active') and not m.tx
        return 2
    check('reference-and-browser-entry-return-to-their-own-parent', entry_paths)

    result = dict(passed=True, cases=cases, inputs=sum(r['inputs'] for r in cases),
        binary_sha256=manifest['binary_sha256'],
        sources={str(p.relative_to(transport.ROOT)): sha(p) for p in
                 (Path(__file__).resolve(), transport.ROOT / 'standalone/directory_view_fixture.py')},
        scope=__doc__ + ' Actual compiled code with observed far page/scratch leases, bounded IO, both viewer entry paths, background parsing and exact reply bytes, cancel/stop/failure and unchanged selection/file. Live selection adoption and physical driver/serial acceptance remain open.')
    (binary.parent / 'directory-view-checks.json').write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    main()
