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
from unicorn.x86_const import (UC_X86_REG_AX, UC_X86_REG_BX, UC_X86_REG_CX, UC_X86_REG_CS, UC_X86_REG_IP, UC_X86_REG_BP, UC_X86_REG_EFLAGS,
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
            self.preview_leases = []
            super().__init__()
            if data is not None:
                self.files['PCPLUS.DIR'] = bytearray(data)
            self.uc.hook_add(UC_HOOK_CODE, self.observe)

        def observe(self, uc, address, size, user):
            if address == self.symbols.get('_directory_preview_stage'):
                assert uc.reg_read(UC_X86_REG_DS) == uc.reg_read(UC_X86_REG_SS) == self.ds
                at = self.data_base + uc.reg_read(UC_X86_REG_SP) + 4
                po, ps, entry, path, outo, outs = struct.unpack('<6H', uc.mem_read(at, 12))
                assert ps*16+po == self.symbols['redisplay_snapshot']+1394
                assert outs*16+outo == self.symbols['redisplay_snapshot']+2788
                assert self.get('_redisplay_active') and self.get('_command_menu_active')
                self.preview_leases.append(entry)
                return
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
            if manifest.get('experimental_directory_preview'):
                adapter = entries['_directory_preview_capture']
                reloc = next(header[12]+i*4 for i in range(header[3]) if
                    (lambda pair: pair[0]+pair[1]*16)(struct.unpack_from('<HH',image,header[12]+i*4)) == adapter+16)
                for kind in ('configured-policy','caller-word','capture-relocation'):
                    damaged = bytearray(image)
                    if kind == 'configured-policy':damaged[module+adapter+11] = 0
                    elif kind == 'caller-word':damaged[module+adapter+7] = 8
                    else:struct.pack_into('<HH',damaged,reloc,0,0)
                    target.write_bytes(damaged)
                    try:inspect_terminal_memory(target,transport.MAP)
                    except AssertionError:pass
                    else:raise AssertionError(('Damaged preview capture accepted',kind))
        return 6 if manifest.get('experimental_directory_preview') else 3
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

    preview_evidence = {}
    if manifest.get('experimental_directory_preview'):
        from check_setup_model import image
        from check_startup_import import terminal_expected
        from check_modem_import import expected as modem_expected
        from check_directory_live import word

        def publish(m, raw):
            source = m.stage_near(raw)
            name = '_hook_baseline_publish'
            segment, offset = m.entries[name]
            words = [m.return_offset, m.code_segment, source, 1]
            top = m.offset('terminal_stack_top')
            sp = top-2*len(words)
            m.uc.mem_write(m.data_base+sp, struct.pack('<4H', *words))
            for reg, value in [(UC_X86_REG_CS, m.base_segment+segment),
                               (UC_X86_REG_DS, m.ds), (UC_X86_REG_SS, m.ds),
                               (UC_X86_REG_SP, sp), (UC_X86_REG_BP, 0xbabe),
                               (UC_X86_REG_EFLAGS, 0x202)]:
                m.uc.reg_write(reg, value)
            m.returned = False
            m.uc.emu_start(m.symbols[name], 0, count=200000)
            assert m.returned and m.uc.reg_read(UC_X86_REG_AX) == 0
            assert m.uc.reg_read(UC_X86_REG_SP) == sp+4
            m.fixture_scratch_end = None

        def configured(*, raw=None, data=fixture(), mask=15):
            m = Directory(data=data)
            raw = image() if raw is None else raw
            publish(m, raw)
            serial = terminal_expected(image())
            m.uc.mem_write(m.symbols['terminal_configuration_values'], serial)
            modem = modem_expected(image())
            m.uc.mem_write(m.symbols['terminal_modem_settings'], modem)
            fields = {0:'terminal_port_number',2:'terminal_baud_low',4:'terminal_baud_high',
                6:'terminal_parity',8:'terminal_data_bits',10:'terminal_stop_bits',
                12:'uart_software_flow',14:'uart_hardware_flow',16:'csi_terminal_id',
                18:'attributes_normal_value',20:'attributes_bold_value',22:'attributes_preset_value',
                24:'attributes_reverse_value',26:'attributes_underline_value',
                28:'render_autowrap',30:'scroll_enabled',32:'uart_port_rbr',34:'uart_irq_indices',
                38:'terminal_macro_character_delay_units',40:'terminal_translation_mode',42:'_clipboard_separator'}
            for at, name in fields.items():
                m.put(name, struct.unpack_from('<H', serial, at)[0])
            m.put('terminal_macro_pause_character', serial[36], 1)
            m.put('terminal_modem_pause', modem[14], 1)
            m.put('terminal_break_delay_units', struct.unpack_from('<H', modem, 366)[0])
            # Actual transport intentionally differs from accepted/configured PRM.
            m.put('terminal_port_number', 3);m.put('uart_port_rbr', 0x3e8)
            m.put('uart_irq_indices', 5);m.put('terminal_baud_low', 38400)
            m.put('terminal_option_mask', mask)
            m.uc.mem_write(m.symbols['terminal_config_path'], b'ACCEPTED.PRM\0'+bytes(51))
            m.uc.mem_write(m.symbols['terminal_dial_target'], b'CURRENT:23'+bytes(54))
            m.put('connection_state', 6)
            m.open();m.finish()
            return m

        def state(m):
            # Entire near data before the stack is too broad: UI-private phase
            # and reader state must change. Bind every live adoption plane.
            names = [('terminal_configuration_values',44),('terminal_modem_settings',368),
                ('terminal_directory_plan',214),('terminal_directory_context',496),
                ('terminal_dial_target',64),('terminal_keymap',948),('terminal_action_definitions',540),
                ('terminal_keyboard_path',64),('terminal_actions_path',64),
                ('terminal_directory_path',64),('_terminal_transfer_preferences',66),
                ('terminal_baseline_storage',1272)]
            values = {n: bytes(m.uc.mem_read(m.symbols[n], size)) for n, size in names}
            for n in ('terminal_directory_entry','terminal_option_mask','connection_state',
                'terminal_port_number','terminal_baud_low','terminal_baud_high',
                'terminal_parity','terminal_data_bits','terminal_stop_bits',
                'uart_port_rbr','uart_irq_indices','uart_software_flow','uart_hardware_flow',
                'csi_terminal_id','terminal_translation_mode','terminal_break_delay_units'):
                values[n] = m.get(n)
            return values

        def prepare(m):
            io = len(m.directory_io)
            m.key(13)
            assert b'Checking the selected entry' in m.text()
            m.idle()
            assert len(m.directory_io) == io and not m.handles

        def proposed():
            m = configured()
            before = state(m)
            end = m.symbols['redisplay_snapshot']+3978
            m.uc.mem_write(end, b'AFTER-PROPOSAL')
            high = [0]
            def stack(uc, address, size, user):
                assert uc.reg_read(UC_X86_REG_SS) == m.ds
                used = m.offset('terminal_stack_top')-uc.reg_read(UC_X86_REG_SP)
                high[0] = max(high[0], used)
                assert 0 <= used <= 8192, 'full preview owner exceeded8KiB stack'
            hook = m.uc.hook_add(UC_HOOK_CODE, stack)
            prepare(m)
            m.uc.hook_del(hook)
            assert b'SELECTED ENTRY // PROPOSED SETTINGS' in m.text()
            assert b'LoSs oF CoNtRoL' in m.text() and b'38400' in m.text()
            proposal = bytes(m.uc.mem_read(m.symbols['redisplay_snapshot']+2788,1190))
            assert struct.unpack_from('<H',proposal,496)[0] == 3
            assert struct.unpack_from('<H',proposal,496+34)[0] == 5
            assert struct.unpack_from('<H',proposal,496+2)[0] == 38400
            assert struct.unpack_from('<H',proposal,496+16)[0] == 6
            assert proposal[496+412+35:496+412+39] == b'555\0'
            assert proposal[2:252] == fixture()[:250]
            assert proposal[252:366] == fixture()[250:364]
            assert b'SECRETA' not in m.text() and b'HIDDENPASS' not in m.text()
            assert m.preview_leases == [1]
            assert bytes(m.uc.mem_read(end,14)) == b'AFTER-PROPOSAL'
            assert state(m) == before and not m.tx
            # Real parser work/reply while the proposal remains on screen.
            m.call('terminal_redisplay_before');ordinary(m,b'\x1b[7;1HBBS-PREVIEW\x1b[6n')
            m.idle();m.drain()
            assert b'SELECTED ENTRY' in m.text() and bytes(m.tx) == b'\x1b[7;12R'
            m.key(27);assert b'LoSs oF CoNtRoL' in m.text() and b'PROPOSED SETTINGS' not in m.text()
            m.key(27);assert b'BBS-PREVIEW' in m.text() and not m.get('_redisplay_active')
            assert state(m) == before and bytes(m.files['PCPLUS.DIR']) == fixture()
            preview_evidence.update(maximum_full_owner_stack=high[0],stack_budget=8192,
                proposal_sha256=hashlib.sha256(proposal).hexdigest(),actual_COM=3,actual_IRQ=5,
                actual_DTE=38400,accepted_PRM_reread=False,adopted=False)
            return 1
        check('preview-accepted-baseline-actual-session-privacy-UART-return-and-full-stack',proposed)

        def refusals():
            cases_ = [(word(image(),0,4),fixture(),b'serial settings'),
                      (image(),fixture(),b'name is unsupported')]
            # Unsupported script spelling in a strictly published raw record.
            bad = bytearray(fixture());bad[250+0x34:250+0x3d] = b'BAD.EXE\0\0'
            cases_[1] = (image(),bytes(bad),b'name is unsupported')
            for raw, data, notice in cases_:
                m = configured(raw=raw,data=data)
                before = state(m)
                at = m.symbols['redisplay_snapshot']+2788
                m.uc.mem_write(at,b'\xcc'*1190)
                prepare(m)
                assert notice in m.text() and b'not been applied' in m.text()
                assert bytes(m.uc.mem_read(at,1190)) == b'\xcc'*1190 and state(m) == before
                m.key(27);m.key(27)
                assert not m.get('_redisplay_active') and not m.tx
            m = Directory();m.open();m.finish();prepare(m)
            assert b'Accepted PRM settings unavailable' in m.text()
            m.key(27);m.key(27)
            m = configured()
            store = m.symbols['terminal_baseline_image']
            m.uc.mem_write(store,b'\xff')
            prepare(m);assert b'Accepted PRM settings unavailable' in m.text()
            m.key(27);m.key(27)
            return 4
        check('preview-global-before-CLI-binding-missing-and-damaged-baseline-refusals',refusals)

        def preview_cancel():
            m = configured();before = state(m)
            m.key(13);assert b'Checking the selected entry' in m.text()
            m.key(27);m.idle()
            assert b'PROPOSED SETTINGS' not in m.text() and state(m) == before
            m.key(27)
            assert not m.get('_redisplay_active') and not m.handles and not m.tx
            return 1
        check('cancel-preview-before-preparation-retains-session-and-reader-ownership',preview_cancel)

        def long_path_and_rate():
            raw=bytearray(image());path=b'C:\\'+b'ABCDEFG\\'*7+b'LAST'
            assert len(path)==63
            raw[0x31c:0x35c]=path+b'\0'
            data=bytearray(fixture());struct.pack_into('<H',data,250+0x2e,8)
            m=configured(raw=bytes(raw),data=bytes(data),mask=0);before=state(m)
            prepare(m)
            assert b'115200' in m.text() and m.text()[1537:1600]==path
            assert state(m)==before and not m.tx
            m.key(27);m.key(27)
            return 1
        check('preview-full63-byte-download-path-and115200-baud-without-adoption',long_path_and_rate)

    result = dict(passed=True, cases=cases, inputs=sum(r['inputs'] for r in cases),
        binary_sha256=manifest['binary_sha256'],
        preview=preview_evidence,
        sources={str(p.relative_to(transport.ROOT)): sha(p) for p in
                 (Path(__file__).resolve(), transport.ROOT / 'standalone/directory_view_fixture.py')},
        scope=__doc__ + ' Actual compiled code with observed far page/scratch leases, bounded IO, both viewer entry paths, background parsing and exact reply bytes, cancel/stop/failure and unchanged selection/file. Live selection adoption and physical driver/serial acceptance remain open.')
    (binary.parent / 'directory-view-checks.json').write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    main()
