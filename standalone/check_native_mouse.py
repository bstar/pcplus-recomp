#!/usr/bin/env python3
"""Run linked native mouse logic with explicit DOS/driver boundaries."""
import json
from pathlib import Path
import struct
from build_native_mouse import ROOT, OUT, sha
from dos_image import DosImage
from unicorn import UC_HOOK_INTR, UC_HOOK_INSN
from unicorn.x86_const import *


class Mouse(DosImage):
    def __init__(self, vector=(0x9000, 0x100), response=(0xffff, 3)):
        super().__init__(OUT / 'MOUSE.EXE', OUT / 'mouse.map')
        self.vector = vector
        self.response = response
        self.events = []
        self.faulted = False
        self.uc.hook_add(UC_HOOK_INTR, self.interrupt)
        for instruction in (UC_X86_INS_IN, UC_X86_INS_OUT):
            self.uc.hook_add(UC_HOOK_INSN, self.forbidden, None, 1, 0, instruction)

    def forbidden(self, *args):
        raise AssertionError('Mouse component reached port IO')

    def interrupt(self, uc, number, data):
        ax = uc.reg_read(UC_X86_REG_AX)
        if number == 0:
            self.faulted = True
            uc.emu_stop()
        elif number == 0x21:
            assert ax == 0x3533
            uc.reg_write(UC_X86_REG_ES, self.vector[0])
            uc.reg_write(UC_X86_REG_BX, self.vector[1])
        else:
            assert number == 0x33 and ax in (0, 0x21, 0x0b, 0x0c), (number, ax)
            self.events.append((ax, uc.reg_read(UC_X86_REG_CX), uc.reg_read(UC_X86_REG_ES), uc.reg_read(UC_X86_REG_DX)))
            if ax in (0, 0x21):
                uc.reg_write(UC_X86_REG_AX, self.response[0])
                uc.reg_write(UC_X86_REG_BX, self.response[1])

    def invoke(self, name, args=(), *, flags=0, x=0, y=0, foreign=False, fault=False):
        callback = name == 'mouse_callback'
        ss = 0x8000 if foreign else self.ds
        ds = 0x40 if foreign else self.ds
        for reg, value in [(UC_X86_REG_CS, self.base_segment), (UC_X86_REG_DS, ds),
                           (UC_X86_REG_SS, ss), (UC_X86_REG_EFLAGS, 0x202),
                           (UC_X86_REG_BP, 0xbabe), (UC_X86_REG_AX, flags),
                           (UC_X86_REG_SI, x & 65535), (UC_X86_REG_DI, y & 65535)]:
            self.uc.reg_write(reg, value)
        words = [self.return_offset] + ([self.base_segment] if callback else list(args))
        sp = 0xe000 - 2 * len(words)
        self.uc.mem_write(ss * 16 + sp, struct.pack('<' + 'H' * len(words), *words))
        self.uc.reg_write(UC_X86_REG_SP, sp)
        self.returned = False
        self.uc.emu_start(self.symbols[name], 0, count=100000)
        if fault:
            assert self.faulted and not self.returned
            return
        assert self.returned and not self.faulted
        assert self.uc.reg_read(UC_X86_REG_SP) == 0xe000
        assert self.uc.reg_read(UC_X86_REG_SS) == ss and self.uc.reg_read(UC_X86_REG_DS) == ds
        assert self.uc.reg_read(UC_X86_REG_BP) == 0xbabe
        if callback:
            assert not self.uc.reg_read(UC_X86_REG_EFLAGS) & 0x200
            assert self.uc.reg_read(UC_X86_REG_SI) == x & 65535
            assert self.uc.reg_read(UC_X86_REG_DI) == y & 65535
        return self.uc.reg_read(UC_X86_REG_AX)

    def scales(self):
        self.put('mouse_scale_x', 8)
        self.put('mouse_scale_y', 4)


def main():
    cases = []
    for vector in ((0, 0), (0, 1), (1, 0), (0x9000, 0x100)):
        for reset in (0, 1):
            for response in ((0xffff, 1), (0xffff, 2), (0xffff, 3), (0xffff, 0), (0xffff, 4), (0, 2)):
                m = Mouse(vector, response)
                result = m.invoke('mouse_probe', [reset])
                expected = 0 if vector == (0, 0) else response[0] if not reset or 1 <= response[1] <= 3 and response[0] == 65535 else 0
                assert result == expected
                assert [e[0] for e in m.events] == ([] if vector == (0, 0) else [0x21 if reset else 0])
                cases.append(dict(case='probe', vector=vector, reset=reset, response=response, passed=True))
    for present in (False, True):
        m = Mouse(response=(0xffff if present else 0, 3))
        m.uc.mem_write(m.symbols['mouse_flags'], b'\xa5' * 16)
        m.invoke('mouse_init', [4, 8, 1])
        assert m.get('mouse_present') == (65535 if present else 0)
        if present:
            assert m.get('mouse_scale_x') == 8 and m.get('mouse_scale_y') == 4
            assert bytes(m.uc.mem_read(m.symbols['mouse_flags'], 16)) == bytes(16)
            assert [e[0] for e in m.events] == [0x21, 0x0b, 0x0c]
            assert m.events[-1][1:] == (0x0b, m.base_segment, m.symbols['mouse_callback'] - m.base)
        else:
            assert bytes(m.uc.mem_read(m.symbols['mouse_flags'], 16)) == b'\xa5' * 16
            assert [e[0] for e in m.events] == [0x21]
        cases.append(dict(case='init', present=present, passed=True))
    for foreign in (False, True):
        for x in (-32768, -16, -8, -1, 0, 1, 8, 16, 32767):
            for y in (-8, 0, 8):
                m = Mouse()
                m.scales()
                m.invoke('mouse_callback', flags=1, x=x, y=y, foreign=foreign)
                dx, dy = int(x / 8), int(y / 4)
                count = max(abs(dx), abs(dy))
                code = (1 if dx > 0 else 3) if abs(dx) >= abs(dy) else (2 if dy > 0 else 0)
                assert m.get('mouse_count') == count
                if count:
                    assert m.get('mouse_code') == code
                assert m.get('mouse_base_x') == (x & 65535 if count else 0)
                assert m.get('mouse_base_y') == (y & 65535 if count else 0)
                assert m.get('mouse_depth') == 65535
                cases.append(dict(case='motion', x=x, y=y, foreign_DS_SS=foreign, passed=True))
    for flag, code in ((2, 4), (8, 5), (10, 4)):
        for enabled in (False, True):
            m = Mouse()
            m.put('mouse_count', 7)
            m.uc.mem_write(m.symbols['mouse_enabled'] + code, bytes([enabled]))
            m.invoke('mouse_callback', flags=flag, foreign=True)
            assert m.get('mouse_count') == (1 if enabled else 7)
            assert m.get('mouse_button_pending') == int(enabled)
            if enabled:
                assert m.get('mouse_code') == code
            cases.append(dict(case='button', flags=flag, enabled=enabled, passed=True))
    for busy in (False, True):
        m = Mouse()
        m.scales()
        m.put('mouse_count', 7)
        if busy:
            m.put('mouse_depth', 0)
        m.invoke('mouse_callback', flags=1, x=16, y=8, foreign=True)
        assert m.get('mouse_count') == 7 and m.get('mouse_base_x') == 0
        assert m.get('mouse_depth') == (0 if busy else 65535)
        assert m.get('mouse_motion_x') == (0 if busy else 16)
        cases.append(dict(case='pending-or-busy', busy=busy, passed=True))
    m = Mouse()
    m.scales()
    m.uc.mem_write(m.symbols['mouse_enabled'], bytes(6))
    m.invoke('mouse_callback', flags=1, x=16, y=8)
    assert m.get('mouse_count') == 0 and m.get('mouse_base_x') == 16 and m.get('mouse_base_y') == 8
    cases.append(dict(case='disabled-motion-still-rebases', passed=True))
    for base, x, count in ((32760, -32760, 2), (32767, -32768, 0)):
        m = Mouse()
        m.scales()
        m.put('mouse_base_x', base)
        m.invoke('mouse_callback', flags=1, x=x, y=0, foreign=True)
        assert m.get('mouse_count') == count
        assert m.get('mouse_base_x') == (x & 65535 if count else base)
        if count:
            assert m.get('mouse_code') == 1
        cases.append(dict(case='signed-counter-wrap', base=base, x=x, passed=True))
    for scale in ('mouse_scale_x', 'mouse_scale_y'):
        m = Mouse()
        m.scales()
        m.put(scale, 0)
        m.invoke('mouse_callback', flags=1, x=8, y=4, fault=True)
        cases.append(dict(case='unchecked-zero-scale-really-divides', scale=scale, passed=True))
    report = dict(passed=True, cases=cases, binary_sha256=sha(OUT / 'MOUSE.EXE'),
                  checker_sha256=sha(Path(__file__)),
                  scope='Actual linked native instructions, including far callback with foreign DS/SS. DOS vector and INT33 responses are explicit scalar boundaries. Zero-scale DIV is retained native behavior; no live application/hardware claim.')
    (OUT / 'checks.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Native mouse:', len(cases), 'linked cases PASS')


if __name__ == '__main__':
    main()
