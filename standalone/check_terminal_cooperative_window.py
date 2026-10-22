#!/usr/bin/env python3
"""Execute cooperative window ownership against actual linked DOS instructions.

BIOS is modeled by the existing window fixture. UART and the child VM are
deliberately absent here; actual DOS receive/query tests cover that boundary.
"""
import argparse
import json
import struct
from pathlib import Path
from unicorn.x86_const import *
import check_terminal_script_window as legacy

ROOT = legacy.ROOT


class Window(legacy.Window):
    def __init__(self, keys=()):
        self.copies = [0, 0]
        self.parent_boundary = False
        self.callbacks = []
        self.admission = 0
        super().__init__(keys, delay=-1)

    def observe(self, uc, address, size, extra):
        super().observe(uc, address, size, extra)
        if self.parent_boundary:
            if address == self.symbols['resident_bridge_caller_ds']:
                result = 0x9100
            elif address == self.symbols['_aspect_render_admit']:
                result = self.admission
            elif address == self.symbols['resident_bridge_callback']:
                self.callbacks.append((uc.reg_read(UC_X86_REG_AX), uc.reg_read(UC_X86_REG_BX)))
                result = 0
            else:
                result = None
            if result is not None:
                sp = uc.reg_read(UC_X86_REG_SP)
                ip = int.from_bytes(uc.mem_read(self.data_base + sp, 2), 'little')
                uc.reg_write(UC_X86_REG_AX, result)
                uc.reg_write(UC_X86_REG_SP, sp + 2)
                uc.reg_write(UC_X86_REG_IP, ip)
        for index, name in enumerate(('local_window_save', 'local_window_restore')):
            if address == self.symbols[name]:
                self.copies[index] += 1

    def interrupt(self, uc, number, extra):
        if number == 0x21 and self.parent_boundary:
            assert uc.reg_read(UC_X86_REG_AX) >> 8 == 0x62
            uc.reg_write(UC_X86_REG_BX, 0x9000)
            return
        return super().interrupt(uc, number, extra)

    def parent(self, operation, value=0):
        self.parent_boundary = True
        self.put('terminal_program_active', 1)
        self.put('terminal_program_kind', 4)
        self.put('render_attached', 1)
        self.put('render_child_psp', 0x9000)
        self.put('render_child_ds', 0x9100)
        return self.near('render_body', bx=value, ax=operation)

    def near(self, name, bx=0, interrupts=True, ax=0, far=False):
        uc = self.uc
        manifest = json.loads((ROOT / 'build' / legacy.PRODUCT / 'manifest.json').read_text())
        segment = self.base_segment + next(
            part['relative_segment'] for part in manifest['memory_layout']['code_segments']
            if part['name'] == 'ASPECT_CODE')
        uc.mem_write(segment * 16 + 0xfff0, b'\xcb')
        words = [self.return_offset, self.code_segment] if far else [0xfff0, self.return_offset, self.code_segment]
        sp = self.offset('terminal_stack_top') - 2 * len(words)
        for register, value in [
            (UC_X86_REG_CS, segment), (UC_X86_REG_DS, self.ds),
            (UC_X86_REG_SS, self.ds), (UC_X86_REG_SP, sp),
            (UC_X86_REG_BP, 0xbabe), (UC_X86_REG_SI, 0x1234),
            (UC_X86_REG_DI, 0x5678), (UC_X86_REG_ES, 0x7200),
            (UC_X86_REG_BX, bx), (UC_X86_REG_AX, ax), (UC_X86_REG_EFLAGS, 0x202 if interrupts else 2),
        ]:
            uc.reg_write(register, value)
        uc.mem_write(self.data_base + sp, struct.pack('<' + 'H' * len(words), *words))
        self.returned = False
        uc.emu_start(self.symbols[name], 0, count=1000000)
        assert self.returned and uc.reg_read(UC_X86_REG_SP) == sp + 2 * len(words), name
        assert name == 'render_body' or [uc.reg_read(register) for register in
                (UC_X86_REG_BP, UC_X86_REG_SI, UC_X86_REG_DI, UC_X86_REG_ES)] == [
                    0xbabe, 0x1234, 0x5678, 0x7200], name
        return uc.reg_read(UC_X86_REG_AX)

    def open(self):
        assert self.near('terminal_script_window_open') == 0
        assert self.get('terminal_script_window_cooperative') == 1
        assert self.get('keyboard_debug_gate') == 0x29
        assert b'TERMINAL KEYS' in bytes(self.uc.mem_read(0xb8000, 4000))[::2]

    def closed(self, frame=None, cursor=None):
        assert not self.get('terminal_script_window_active')
        assert not self.get('terminal_script_window_cooperative')
        assert self.get('keyboard_debug_gate') == 65535
        assert bytes(self.uc.mem_read(0xb8000, 4000)) == (self.frame if frame is None else frame)
        assert self.cursor == (0x111f if cursor is None else cursor)
        assert self.shape == 0x0607
        assert not self.get('terminal_tx_count') and not self.get('terminal_quit')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mouse', action='store_true')
    args = parser.parse_args()
    if args.mouse:
        legacy.PRODUCT = 'terminal-mouse'
    cases = []
    for mode in (0, 16):
        for name, raw, consumed, hook in [
            ('ordinary', 0x1e61, True, None), ('escape', 0x011b, True, None),
            ('F1', 0x3b00, False, None), ('E0-prefix', 0x48e0, False, None),
            ('control-1C', 0x001c, False, None), ('control-1D', 0x001d, False, None),
            ('control-1F', 0x001f, False, None), ('matching-hook', 0x1e61, False, 0x61),
            ('nonmatching-hook', 0x1e61, True, 0x62),
            ('signed-hook', 0x0080, True, 0x80),
        ]:
            window = Window([raw])
            window.put('keyboard_bios_mode', mode, 1)
            if hook is not None:
                window.put('keyboard_mapping_hook_enabled', 1)
                window.put('keyboard_mapping_hook_character', hook, 1)
            window.open()
            assert window.near('terminal_script_window_service', bx=1) == 0
            window.closed()
            assert window.keys == ([] if consumed else [raw]), name
            assert window.reads == ([raw] if consumed else []), name
            cases.append(dict(name=name, mode=mode, passed=True))

        window = Window([0x2c00])
        window.put('keyboard_bios_mode', mode, 1)
        window.open()
        window.near('terminal_script_window_service', bx=1)
        assert window.get('terminal_script_window_active') == 1
        assert b'SCRIPT KEYBOARD HELP' in bytes(window.uc.mem_read(0xb8000, 4000))[::2]
        assert window.reads == [0x2c00]
        window.near('terminal_script_window_hide')
        updated = bytes((i * 7 + 1) & 255 for i in range(4000))
        window.uc.mem_write(0xb8000, updated)
        window.cursor = 0x0316
        window.keys = [0x2c00]
        window.near('terminal_script_window_service', bx=0)
        assert bytes(window.uc.mem_read(0xb8000, 4000)) == updated
        window.near('terminal_script_window_service', bx=1)
        assert b'TERMINAL KEYS' in bytes(window.uc.mem_read(0xb8000, 4000))[::2]
        copies = window.copies[:]
        for _ in range(100):
            window.near('terminal_script_window_service', bx=1)
        assert window.copies == copies == [2, 1]
        window.near('terminal_script_window_close')
        window.closed(updated, 0x0316)
        window.near('terminal_script_window_close')
        assert window.copies == [2, 2]
        cases.append(dict(name='updated-frame-cursor-hidden-toggle-idle-copy-budget-idempotent-close',
                          mode=mode, passed=True))

    for field, value in [('terminal_script_window_active', 1),
                         ('terminal_aspect_active', 0), ('_redisplay_active', 1),
                         ('_command_menu_active', 1)]:
        window = Window()
        window.put(field, value)
        assert window.near('terminal_script_window_open') == 10
        assert not window.get('terminal_script_window_cooperative') and window.copies == [0, 0]
        cases.append(dict(name='reject-' + field, passed=True))
    window = Window()
    assert window.near('terminal_script_window_open', interrupts=False) == 10
    assert window.copies == [0, 0]
    cases.append(dict(name='reject-interrupts-disabled', passed=True))
    for disposition in ('END', 'revoke'):
        window = Window()
        window.open()
        if disposition == 'END':
            assert window.parent(2) == 0
            assert window.get('render_attached') == 0 and window.callbacks == []
        else:
            window.near('terminal_render_revoke', far=True)
            assert window.get('render_attached') == 0
        window.closed()
        cases.append(dict(name='actual-parent-' + disposition + '-closes-open-window', passed=True))
    for rejection, value, admission, wanted in [
        ('argument', 2, 0, 7), ('view-admission', 1, 3, 3),
    ]:
        window = Window()
        window.open()
        before = bytes(window.uc.mem_read(0xb8000, 4000))
        window.admission = admission
        assert window.parent(11, value) == wanted and window.callbacks == []
        assert bytes(window.uc.mem_read(0xb8000, 4000)) == before
        assert window.get('terminal_script_window_cooperative') == 1
        cases.append(dict(name='parent-service-rejects-' + rejection + '-without-window-mutation', passed=True))
    window = Window([0x011b])
    window.open()
    assert window.parent(11, 1) == 0 and window.callbacks == [(11, 0)]
    window.closed()
    cases.append(dict(name='parent-service-publishes-dismissal-after-restoration', passed=True))
    report = dict(passed=True, cases=cases,
                  terminal_sha256=legacy.sha(ROOT / 'build' / legacy.PRODUCT / 'TERMINAL.EXE'),
                  checker_sha256=legacy.sha(Path(__file__)),
                  modeled_BIOS_checker_sha256=legacy.sha(Path(legacy.__file__)),
                  scope=__doc__)
    folder = ROOT / 'build' / ('terminal-cooperative-window-mouse' if args.mouse else 'terminal-cooperative-window')
    folder.mkdir(exist_ok=True)
    (folder / 'cpu-results.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Cooperative window', legacy.PRODUCT, len(cases), 'cases PASS')


if __name__ == '__main__':
    main()
