#!/usr/bin/env python3
"""Execute linked owner/native composition with explicit allocator/driver/BIOS boundaries."""
import json
from pathlib import Path
import struct
from build_mouse_keyboard import ROOT, OUT, sha
from dos_image import DosImage
from unicorn import UC_HOOK_CODE, UC_HOOK_INTR, UC_HOOK_INSN
from unicorn.x86_const import *


class Owner(DosImage):
    def __init__(self):
        super().__init__(OUT / 'MOUSEKEY.EXE', OUT / 'MOUSEKEY.map')
        self.vector = (0x7000, 0x40)
        self.driver = bytes((i * 19 + 7) & 255 for i in range(256))
        self.original_driver = self.driver
        self.size = len(self.driver)
        self.present = True
        self.alloc_fail = False
        self.alloc_offset = 0x100
        self.corrupt_save = False
        self.allocations = {}
        self.events = []
        self.bios = []
        self.uc.hook_add(UC_HOOK_CODE, self.boundary)
        self.uc.hook_add(UC_HOOK_INTR, self.interrupt)
        for instruction in (UC_X86_INS_IN, UC_X86_INS_OUT):
            self.uc.hook_add(UC_HOOK_INSN, self.forbidden, None, 1, 0, instruction)

    def forbidden(self, *args):
        raise AssertionError('Owner reached undeclared port IO')

    def boundary(self, uc, address, size, data):
        if address not in (self.symbols['_fmalloc_'], self.symbols['_ffree_']):
            return
        ax, dx = uc.reg_read(UC_X86_REG_AX), uc.reg_read(UC_X86_REG_DX)
        if address == self.symbols['_fmalloc_']:
            self.events.append(('allocate', ax))
            assert ax == self.size + 32
            if self.alloc_fail:
                uc.reg_write(UC_X86_REG_AX, 0)
                uc.reg_write(UC_X86_REG_DX, 0)
            else:
                pointer = (0x9000, self.alloc_offset)
                assert pointer not in self.allocations
                self.allocations[pointer] = ax
                uc.mem_write(pointer[0] * 16 + pointer[1], bytes(ax))
                uc.reg_write(UC_X86_REG_AX, pointer[1])
                uc.reg_write(UC_X86_REG_DX, pointer[0])
        else:
            self.events.append(('free', dx, ax))
            assert (dx, ax) in self.allocations
            self.allocations.pop((dx, ax))
        sp, ss = uc.reg_read(UC_X86_REG_SP), uc.reg_read(UC_X86_REG_SS)
        uc.reg_write(UC_X86_REG_IP, int.from_bytes(uc.mem_read(ss * 16 + sp, 2), 'little'))
        uc.reg_write(UC_X86_REG_SP, sp + 2)

    def interrupt(self, uc, number, data):
        ax = uc.reg_read(UC_X86_REG_AX)
        if number == 0x21:
            assert ax == 0x3533, hex(ax)
            uc.reg_write(UC_X86_REG_ES, self.vector[0])
            uc.reg_write(UC_X86_REG_BX, self.vector[1])
            self.events.append(('vector', *self.vector))
        elif number == 0x16:
            ah = ax >> 8
            assert ah in (0, 1)
            self.events.append(('BIOS', ah))
            if ah == 0:
                assert self.bios
                uc.reg_write(UC_X86_REG_AX, self.bios.pop(0))
            else:
                flags = uc.reg_read(UC_X86_REG_EFLAGS)
                uc.reg_write(UC_X86_REG_EFLAGS, flags & ~0x40 if self.bios else flags | 0x40)
                if self.bios:
                    uc.reg_write(UC_X86_REG_AX, self.bios[0])
        else:
            assert number == 0x33 and ax in (0x15, 0x16, 0x17, 0x21, 0x0b, 0x0c), (number, hex(ax))
            self.events.append(('driver', ax))
            if ax == 0x15:
                uc.reg_write(UC_X86_REG_BX, self.size)
            elif ax in (0x16, 0x17):
                address = uc.reg_read(UC_X86_REG_ES) * 16 + uc.reg_read(UC_X86_REG_DX)
                if ax == 0x16:
                    uc.mem_write(address, self.driver)
                    if self.corrupt_save:
                        uc.mem_write(address - 1, b'\x00')
                else:
                    self.driver = bytes(uc.mem_read(address, self.size))
            elif ax == 0x21:
                self.driver = bytes(self.size)
                uc.reg_write(UC_X86_REG_AX, 65535 if self.present else 0)
                uc.reg_write(UC_X86_REG_BX, 3)
            elif ax == 0x0c:
                self.driver = struct.pack('<3H', uc.reg_read(UC_X86_REG_CX),
                    uc.reg_read(UC_X86_REG_ES), uc.reg_read(UC_X86_REG_DX)) + self.driver[6:]

    def invoke(self, name, args=(), *, flags=0x202, foreign_ss=False):
        ss = 0x8000 if foreign_ss else self.ds
        for register, value in [(UC_X86_REG_CS, self.base_segment), (UC_X86_REG_DS, self.ds),
                                (UC_X86_REG_SS, ss), (UC_X86_REG_EFLAGS, flags),
                                (UC_X86_REG_BP, 0xbabe), (UC_X86_REG_SI, 0x1234), (UC_X86_REG_DI, 0x5678)]:
            self.uc.reg_write(register, value)
        words = [self.return_offset, *args]
        sp = 0xe000 - 2 * len(words)
        self.uc.mem_write(ss * 16 + sp, struct.pack('<' + 'H' * len(words), *words))
        self.uc.reg_write(UC_X86_REG_SP, sp)
        self.returned = False
        self.uc.emu_start(self.symbols[name], 0, count=500000)
        assert self.returned and self.uc.reg_read(UC_X86_REG_SP) == sp + 2, name
        assert self.uc.reg_read(UC_X86_REG_DS) == self.ds and self.uc.reg_read(UC_X86_REG_SS) == ss
        for register, value in [(UC_X86_REG_BP, 0xbabe), (UC_X86_REG_SI, 0x1234), (UC_X86_REG_DI, 0x5678)]:
            assert self.uc.reg_read(register) == value, (name, register)
        return self.uc.reg_read(UC_X86_REG_AX)

    def config(self, x=8, y=4, enabled=bytes([1] * 6)):
        self.uc.mem_write(self.data_base + 0x6000, struct.pack('<2H', x, y) + enabled)
        return 0x6000

    def native(self):
        return bytes(self.uc.mem_read(self.symbols['mouse_scale_x'], 22)) + bytes(self.uc.mem_read(self.symbols['mouse_enabled'], 6))

    def phase(self):
        return self.invoke('_mouse_owner_phase')

    def close(self):
        assert self.invoke('_mouse_owner_close') == 0 and self.phase() == 0
        assert not self.allocations and self.driver == self.original_driver


def main():
    cases = []
    for x in (0, 1, 30, 999, 1000, 32767, 65535):
        for y in (0, 1, 28, 999, 1000, 32767, 65535):
            m = Owner()
            image = bytearray([0xa5] * 0x4f0)
            struct.pack_into('<2H', image, 0x4e4, x, y)
            m.uc.mem_write(m.data_base + 0x5000, bytes(image))
            m.uc.mem_write(m.data_base + 0x6000, b'\xcc' * 10)
            result = m.invoke('_mouse_settings_decode', [0x5000, len(image), 0x6000])
            expected = 0 if 1 <= x <= 999 and 1 <= y <= 999 else 1
            assert result == expected and not m.events
            assert bytes(m.uc.mem_read(m.data_base + 0x5000, len(image))) == image
            output = bytes(m.uc.mem_read(m.data_base + 0x6000, 10))
            assert output == (struct.pack('<2H', x, y) + bytes([1] * 6) if not expected else b'\xcc' * 10)
            cases.append(dict(case='PRM-ranges', x=x, y=y, passed=True))
    for pointers in ((0, 0x4f0, 0x6000), (0xff00, 0x4f0, 0x6000),
                     (0x5000, 0x4ef, 0x6000), (0x5000, 0x4f0, 0),
                     (0x5000, 0x4f0, 0xfffc), (0x5000, 0x4f0, 0x5001)):
        m = Owner()
        assert m.invoke('_mouse_settings_decode', pointers) == 1 and not m.events
        cases.append(dict(case='PRM-pointer-size-overlap', args=pointers, passed=True))
    for flags, foreign in ((2, False), (0x202, True)):
        m = Owner()
        before = m.native()
        assert m.invoke('_mouse_owner_open', [m.config()], flags=flags, foreign_ss=foreign) == 1
        assert not m.events and m.native() == before and m.phase() == 0
        cases.append(dict(case='admit-IF-and-SS', flags=flags, foreign_SS=foreign, passed=True))
    for kind in ('invalid-x', 'invalid-y', 'invalid-enable', 'missing', 'size-zero', 'size-overflow', 'allocate', 'wrap', 'guard'):
        m = Owner()
        before = m.native()
        cfg = m.config(0 if kind == 'invalid-x' else 8, 1000 if kind == 'invalid-y' else 4,
                       bytes([2, 1, 1, 1, 1, 1]) if kind == 'invalid-enable' else bytes([1] * 6))
        if kind == 'missing':
            m.vector = (0, 0)
        elif kind == 'size-zero':
            m.size = 0
        elif kind == 'size-overflow':
            m.size = 65535
        elif kind == 'allocate':
            m.alloc_fail = True
        elif kind == 'wrap':
            m.alloc_offset = 65520
        elif kind == 'guard':
            m.corrupt_save = True
        expected = 1 if kind.startswith('invalid') else 3 if kind in ('missing', 'size-zero', 'size-overflow') else 4 if kind in ('allocate', 'wrap') else 2
        assert m.invoke('_mouse_owner_open', [cfg]) == expected
        assert m.phase() == 0 and not m.allocations and m.native() == before
        assert not any(e == ('driver', 0x21) for e in m.events)
        cases.append(dict(case='rejected-open-' + kind, passed=True))
    m = Owner()
    before = m.native()
    assert m.invoke('_mouse_owner_open', [m.config()]) == 0 and m.phase() == 1
    assert m.symbols['mouse_count'] == m.symbols['keyboard_queue_count']
    assert m.symbols['mouse_code'] == m.symbols['keyboard_queue_index']
    assert m.symbols['mouse_button_pending'] == m.symbols['keyboard_queue_active']
    m.bios = [0x256b]
    assert m.invoke('_mouse_test_emit', [1, 16, 8]) == 1
    assert m.get('mouse_count') == 2
    for expected in (0x4d00, 0x4d00, 0x6b):
        assert m.invoke('_mouse_owner_key', [0x6100]) == 0
        assert int.from_bytes(m.uc.mem_read(m.data_base + 0x6100, 2), 'little') == expected
    assert not m.bios and m.get('mouse_count') == 0
    m.uc.mem_write(m.data_base + 0x6100, b'\xaa\xaa')
    assert m.invoke('_mouse_owner_key', [0x6100]) == 5
    assert bytes(m.uc.mem_read(m.data_base + 0x6100, 2)) == b'\xaa\xaa'
    for flags, expected in ((2, 13), (8, 27)):
        assert m.invoke('_mouse_test_emit', [flags, 16, 8]) == 1
        assert m.invoke('_mouse_owner_key', [0x6100]) == 0
        assert int.from_bytes(m.uc.mem_read(m.data_base + 0x6100, 2), 'little') == expected
        assert m.get('mouse_button_pending') == 0
    assert m.invoke('_mouse_owner_suspend') == 0 and m.phase() == 2
    assert m.invoke('_mouse_owner_key', [0x6100]) == 2
    m.driver = b'C' * m.size
    assert m.invoke('_mouse_owner_resume') == 0 and m.phase() == 1
    assert m.get('mouse_count') == 0 and m.get('mouse_scale_x') == 8 and m.get('mouse_scale_y') == 4
    m.close()
    assert m.native() == before
    cases.append(dict(case='actual-native-queue-BIOS-and-driver-lifecycle', passed=True))
    for kind in ('vector', 'guard', 'queue-index', 'scale', 'depth', 'driver-size'):
        m = Owner()
        assert m.invoke('_mouse_owner_open', [m.config()]) == 0
        vector = m.vector
        if kind == 'vector':
            m.vector = (0, 0)
        elif kind == 'guard':
            m.uc.mem_write(0x90100, b'\x00')
        elif kind == 'queue-index':
            m.put('mouse_count', 1)
            m.put('mouse_code', 6)
        elif kind == 'scale':
            m.put('mouse_scale_x', 0)
        elif kind == 'depth':
            m.put('mouse_depth', 0)
        else:
            m.size = 512
        prior_events = len(m.events)
        assert m.invoke('_mouse_owner_key', [0x6100]) == 2 and m.phase() == 3
        assert m.allocations and not any(e[0] == 'driver' and e[1] != 0x15 for e in m.events[prior_events:])
        m.vector = vector
        m.size = 256
        m.uc.mem_write(0x90100, b'\xa5')
        m.put('mouse_depth', 65535)
        m.close()
        cases.append(dict(case='quarantine-and-repaired-close-' + kind, passed=True))
    m = Owner()
    before = m.native()
    m.present = False
    assert m.invoke('_mouse_owner_open', [m.config()]) == 3 and m.phase() == 3
    assert len(m.allocations) == 1
    m.close()
    assert m.native() == before
    cases.append(dict(case='failed-native-init-retains-owned-baseline-for-close', passed=True))
    m = Owner()
    assert m.invoke('_mouse_owner_open', [m.config()]) == 0
    m.present = False
    assert m.invoke('_mouse_owner_suspend') == 3 and m.phase() == 3
    assert len(m.allocations) == 1
    m.close()
    cases.append(dict(case='failed-native-suspend-retains-owned-baseline-for-close', passed=True))
    m = Owner()
    for name, args in [('_mouse_owner_resume', []), ('_mouse_owner_suspend', []), ('_mouse_owner_key', [0x6100])]:
        assert m.invoke(name, args) == 2 and not m.events
    assert m.invoke('_mouse_owner_open', [m.config()]) == 0
    old = list(m.events)
    assert m.invoke('_mouse_owner_resume') == 2 and m.phase() == 1 and m.events == old
    assert m.invoke('_mouse_owner_suspend') == 0
    old = list(m.events)
    assert m.invoke('_mouse_owner_suspend') == 2 and m.phase() == 2 and m.events == old
    m.close()
    old = list(m.events)
    assert m.invoke('_mouse_owner_close') == 0 and m.events == old
    cases.append(dict(case='lifecycle-reentry-rejects-before-driver-and-close-is-idempotent', passed=True))
    report = dict(passed=True, cases=cases, binary_sha256=sha(OUT / 'MOUSEKEY.EXE'),
                  checker_sha256=sha(Path(__file__)),
                  scope='Actual linked C owner, native producer/keyboard consumer and foreign-DS/SS callback bridge. Far heap, INT33 state/vector and BIOS input are explicit modeled boundaries; DOS child/driver execution is separate.')
    (OUT / 'checks.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Mouse/keyboard owner:', len(cases), 'linked cases PASS')


if __name__ == '__main__':
    main()
