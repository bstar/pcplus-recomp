#!/usr/bin/env python3
"""Source/native query replay with explicit operands, formatting and DOS replies."""
import argparse
import hashlib
import json
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_16, UC_HOOK_CODE, UC_HOOK_INTR
from unicorn.x86_const import *
from build_aspect_system_query import ROOT, OUT, sha

DATA = 0x30000


class Machine:
    def __init__(self, original=None):
        self.u = Uc(UC_ARCH_X86, UC_MODE_16)
        self.u.mem_map(0, 0x100000)
        self.units = json.loads((OUT / 'manifest.json').read_text())['units']
        for unit in self.units:
            code = (original[unit['file_start']:unit['file_start'] + unit['bytes']]
                    if original else (ROOT / unit['output']).read_bytes())
            assert hashlib.sha256(code).hexdigest() == unit['sha256']
            self.u.mem_write(0x10000 + unit['start'], code)
        self.u.hook_add(UC_HOOK_CODE, self.hook)
        self.u.hook_add(UC_HOOK_INTR, self.kernel)

    def word(self, at):
        return int.from_bytes(self.u.mem_read(DATA + at, 2), 'little')

    def ret(self, value):
        sp = self.u.reg_read(UC_X86_REG_SP)
        self.u.reg_write(UC_X86_REG_AX, value & 65535)
        self.u.reg_write(UC_X86_REG_IP, self.word(sp))
        self.u.reg_write(UC_X86_REG_SP, sp + 2)

    def hook(self, u, at, size, data):
        self.seen.add(at)
        if at == 0x1f800:
            self.returned = True
            u.emu_stop()
            return
        if any(0x10000 + x['start'] <= at < 0x10000 + x['end'] for x in self.units):
            return
        fn = at - 0x10000
        sp = u.reg_read(UC_X86_REG_SP)
        arg = lambda n: self.word(sp + n * 2)
        if fn == 0xdc48:
            self.calls.append('drive')
            self.ret(self.drive)
        elif fn in (0xde92, 0xdf04, 0xdf0b):
            self.calls.append({0xde92: 'long-dest', 0xdf04: 'source', 0xdf0b: 'string-dest'}[fn])
            self.ret(0x5800)
        elif fn == 0x82b6:
            assert arg(1) == 0x5800
            if self.kind == 'dosver':
                assert arg(2) == 0x778e
                assert (arg(3), arg(4)) == (self.version & 255, self.version >> 8)
                text = ('%d.%02d' % (arg(3), arg(4))).encode()
            else:
                assert arg(2) == 0x7796
                drive = self.drive or self.current + 1
                assert arg(3) == (drive + 64) & 65535
                text = bytes([(drive + 64) & 255]) + b':\\'
            self.calls.append('format')
            self.u.mem_write(DATA + arg(1), text + b'\0')
            self.ret(len(text))
        elif fn == 0xe0a4:
            self.calls.append('flush')
            self.ret(0xbeef)
        else:
            raise AssertionError(('Unexpected boundary', hex(at)))

    def kernel(self, u, number, data):
        assert number == 0x21
        ah = u.reg_read(UC_X86_REG_AX) >> 8
        self.calls.append('DOS%02x' % ah)
        if ah == 0x19:
            u.reg_write(UC_X86_REG_AX, 0xab00 | self.current)
        elif ah == 0x47:
            assert u.reg_read(UC_X86_REG_DX) == (self.drive or self.current + 1)
            assert u.reg_read(UC_X86_REG_SI) == 0x5803
            if not self.error:
                u.mem_write(DATA + 0x5803, self.directory + b'\0')
            u.reg_write(UC_X86_REG_AX, self.error or 0x1234)
            flags = u.reg_read(UC_X86_REG_EFLAGS)
            u.reg_write(UC_X86_REG_EFLAGS, (flags & ~1) | bool(self.error))
        elif ah == 0x36:
            assert u.reg_read(UC_X86_REG_DX) == self.drive
            for reg, value in zip((UC_X86_REG_AX, UC_X86_REG_BX, UC_X86_REG_CX), self.geometry):
                u.reg_write(reg, value)
            u.reg_write(UC_X86_REG_DX, 0xdead)
        elif ah == 0x30:
            u.reg_write(UC_X86_REG_AX, self.version)
            u.reg_write(UC_X86_REG_BX, 0xbeef)
            u.reg_write(UC_X86_REG_CX, 0x1234)
        else:
            raise AssertionError(('DOS', ah))

    def run(self, kind, drive=0, current=2, directory=b'', error=0,
            geometry=(8, 1234, 512), version=0x1606):
        self.kind, self.drive, self.current = kind, drive, current
        self.directory, self.error, self.geometry, self.version = directory, error, geometry, version
        self.seen, self.calls, self.returned = set(), [], False
        before = bytearray((i * 37 + 11) & 255 for i in range(65536))
        before[0xd124:0xd126] = b'\xcd\xab'
        before[0x778e:0x7796] = b'%d.%02d\0'
        before[0x7796:0x779b] = b'%c:\\\0'
        before[0xf000:0xf002] = b'\x00\xf8'
        u = self.u
        u.mem_write(DATA, bytes(before))
        for reg, value in ((UC_X86_REG_CS, 0x1000), (UC_X86_REG_DS, 0x3000),
                           (UC_X86_REG_SS, 0x3000), (UC_X86_REG_ES, 0x3000),
                           (UC_X86_REG_SP, 0xf000), (UC_X86_REG_BP, 0xbabe),
                           (UC_X86_REG_SI, 0x1234), (UC_X86_REG_DI, 0x5678),
                           (UC_X86_REG_EFLAGS, 0x202)):
            u.reg_write(reg, value)
        start = dict(diskfree=0xe6b9, dosver=0xe6d1, getdir=0xe721)[kind]
        u.emu_start(0x10000 + start, 0, count=1000)
        assert self.returned
        if kind == 'diskfree':
            a, b, c = geometry
            result = 0xffffffff if a == 65535 else ((a * c) & 65535) * b
            before[0x5800:0x5804] = result.to_bytes(4, 'little')
            expected = ['drive', 'long-dest', 'DOS36']
        elif kind == 'dosver':
            value = ('%d.%02d' % (version & 255, version >> 8)).encode() + b'\0'
            before[0x5800:0x5800 + len(value)] = value
            expected = ['DOS30', 'source', 'format']
        else:
            value = bytes([((drive or current + 1) + 64) & 255]) + b':\\\0'
            before[0x5800:0x5804] = value
            if not error:
                before[0x5803:0x5804 + len(directory)] = directory + b'\0'
            before[0xd124:0xd126] = error.to_bytes(2, 'little')
            expected = ['drive'] + ([] if drive else ['DOS19']) + ['string-dest', 'format', 'DOS47', 'flush']
        assert self.calls == expected, (kind, self.calls, expected)
        after = bytes(u.mem_read(DATA, 65536))
        assert after[:0xef80] == before[:0xef80] and after[0xf002:] == before[0xf002:]
        assert u.reg_read(UC_X86_REG_SP) == 0xf002
        assert [u.reg_read(r) for r in (UC_X86_REG_BP, UC_X86_REG_SI, UC_X86_REG_DI)] == [0xbabe, 0x1234, 0x5678]
        assert u.reg_read(UC_X86_REG_DS) == u.reg_read(UC_X86_REG_SS) == u.reg_read(UC_X86_REG_ES) == 0x3000
        assert not u.reg_read(UC_X86_REG_EFLAGS) & 0x400
        return after[:0xef80], self.calls


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--original', type=Path)
    args = parser.parse_args()
    raw = args.original.read_bytes() if args.original else None
    if raw:
        assert hashlib.sha256(raw).hexdigest() == json.loads((ROOT / 'standalone/fixtures/aspect_system_query_native_units.json').read_text())['original_sha256']
    models = [Machine()] + ([Machine(raw)] if raw else [])
    count = 0
    seen = set()
    def case(*positional, **keywords):
        nonlocal count
        results = [m.run(*positional, **keywords) for m in models]
        assert all(r == results[0] for r in results)
        count += 1
        seen.update(models[0].seen)
    for drive in (*range(256), 256, 32767, 32768, 65535):
        for geometry in ((1, 1, 512), (8, 65535, 512), (128, 1, 512),
                         (64, 65535, 1024), (65535, 123, 512),
                         (32768, 32768, 32768), (3, 13, 17), (0, 0, 0), (1, 65535, 65535)):
            case('diskfree', drive=drive, geometry=geometry)
    for drive in (*range(256), 256, 32767, 32768, 65535):
        for error in (0, 1, 3, 15, 65535):
            case('getdir', drive=drive, error=error, directory=b'GAMES\\ADVENT')
    for current in range(26):
        for directory in (b'', b'GAMES', b'X' * 63):
            case('getdir', current=current, directory=directory)
    for major in (0, 1, 3, 5, 6, 7, 10, 255):
        for minor in (0, 1, 9, 10, 22, 99, 100, 255):
            case('dosver', version=major | minor << 8)
    result = dict(passed=True, cases=count, original_comparisons=count if raw else 0,
                  checker_sha256=sha(Path(__file__)), manifest_sha256=sha(OUT / 'manifest.json'),
                  instruction_addresses=len(seen),
                  scope='Exact native handlers/helpers with modeled operand/format/DOS replies. Full nonstack DS, stack, BP/SI/DI/DS=SS/ES/DF checks; no real DOS filesystem or production adaptation claim.')
    (OUT / ('native-checks.json' if raw else 'checks.json')).write_text(json.dumps(result, indent=2) + '\n')
    print('System queries:', count, 'cases,', result['original_comparisons'], 'original comparisons PASS')


if __name__ == '__main__':
    main()
