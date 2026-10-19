#!/usr/bin/env python3
"""Exact environment instructions/CRT with only operands/realloc/error modeled."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from unicorn import Uc, UC_ARCH_X86, UC_MODE_16, UC_HOOK_CODE
from unicorn.x86_const import *
from build_aspect_environment import ROOT, OUT, sha

DATA = 0x30000
UPPER = bytes.maketrans(bytes(range(97, 123)), bytes(range(65, 91)))


class Machine:
    def __init__(self, original=None):
        self.u = Uc(UC_ARCH_X86, UC_MODE_16)
        self.u.mem_map(0, 0x100000)
        manifest = json.loads((OUT / 'manifest.json').read_text())
        self.units = manifest['units'] + manifest['reused']
        for unit in self.units:
            code = original[unit['file_start']:unit['file_start'] + unit['bytes']] if original else (ROOT / unit['output']).read_bytes()
            assert hashlib.sha256(code).hexdigest() == unit['sha256']
            self.u.mem_write(0x10000 + unit['start'], code)
        self.u.hook_add(UC_HOOK_CODE, self.hook)

    def word(self, at):
        return int.from_bytes(self.u.mem_read(DATA + at, 2), 'little')

    def string(self, at):
        return bytes(self.u.mem_read(DATA + at, 1024)).split(b'\0', 1)[0]

    def ret(self, value=0, pop=0):
        sp = self.u.reg_read(UC_X86_REG_SP)
        self.u.reg_write(UC_X86_REG_AX, value & 65535)
        self.u.reg_write(UC_X86_REG_IP, self.word(sp))
        self.u.reg_write(UC_X86_REG_SP, sp + 2 + pop)

    def hook(self, u, address, size, data):
        self.seen.add(address)
        if address == 0x1f800:
            self.returned = True
            u.emu_stop()
            return
        if address == 0x1f400 or address == 0x1f403 or address == 0x1f406:
            return
        if any(0x10000 + x['start'] <= address < 0x10000 + x['end'] for x in self.units):
            return
        fn = address - 0x10000
        sp = u.reg_read(UC_X86_REG_SP)
        if fn == 0xdf04:
            self.ret(0x5200 + self.reads * 0x100)
            self.reads += 1
        elif fn == 0xdf0b:
            self.destinations += 1
            self.ret(0x5800)
        elif fn == 0xe0a4:
            self.flushes += 1
            self.ret()
        elif fn == 0x4efb:
            assert self.word(sp + 2) == 3
            self.warnings += 1
            self.ret(pop=2)
        elif fn == 0xa7ca:
            pointer, count = self.word(sp + 2), self.word(sp + 4)
            assert pointer == 0x6000 and 2 <= count <= 64
            self.allocations.append(count)
            if self.fail:
                self.ret(0)
            else:
                u.mem_write(DATA + 0x6100, bytes(u.mem_read(DATA + pointer, min(self.old_size, count))))
                self.ret(0x6100)
        else:
            raise AssertionError(('unexpected boundary', hex(address)))

    def run(self, kind, text=b'A', entries=(b'A=ONE',), fail=False):
        u = self.u
        self.reads = self.destinations = self.flushes = self.warnings = 0
        self.allocations, self.seen, self.returned, self.fail = [], set(), False, fail
        before = bytearray((i * 37 + 11) & 255 for i in range(65536))
        before[0x4b04:0x4b06] = struct.pack('<H', 0x5000)
        before[0x7b43:0x7b45] = struct.pack('<H', 0x6000)
        before[0xd124:0xd126] = b'\xcd\xab'
        before[0x4942] = 0
        for i, value in enumerate(entries):
            at = 0x7000 + i * 0x200
            before[at:at + len(value) + 1] = value + b'\0'
            before[0x6000 + i * 2:0x6002 + i * 2] = struct.pack('<H', at)
        self.old_size = (len(entries) + 1) * 2
        before[0x6000 + len(entries) * 2:0x6002 + len(entries) * 2] = b'\0\0'
        before[0x5200:0x5200 + len(text) + 1] = text + b'\0'
        second = b'LOC_B=two'
        before[0x5300:0x5300 + len(second) + 1] = second + b'\0'
        before[0x5800:0x5809] = b'OLD-VALUE'
        before[0x5809] = 0
        before[0xf000:0xf002] = struct.pack('<H', 0xf800)
        direct = kind.endswith('-native')
        if direct:
            before[0xf002:0xf004] = struct.pack('<H', 0x5200)
        u.mem_write(DATA, bytes(before))
        for reg, value in ((UC_X86_REG_CS, 0x1000), (UC_X86_REG_DS, 0x3000),
                           (UC_X86_REG_SS, 0x3000), (UC_X86_REG_ES, 0x3000),
                           (UC_X86_REG_SP, 0xf000), (UC_X86_REG_BP, 0xbabe),
                           (UC_X86_REG_SI, 0x1234), (UC_X86_REG_DI, 0x5678),
                           (UC_X86_REG_EFLAGS, 0x202)):
            u.reg_write(reg, value)
        starts = dict(get=0xe76b, put=0xe823, **{'get-native': 0x8e12, 'put-native': 0x9600})
        if kind == 'alias':
            assert entries == () and text == b'LOC_A=one' and not fail
            code = b'\xe8' + struct.pack('<H', (0xe823 - 0xf403) & 65535)
            code += b'\xe8' + struct.pack('<H', (0xe823 - 0xf406) & 65535) + b'\xc3'
            u.mem_write(0x1f400, code)
            # Both reallocs see the vector size requested by the native code;
            # the second update is an in-place replacement, with no realloc.
            start = 0xf400
        else:
            start = starts[kind]
        u.emu_start(0x10000 + start, 0, count=100000)
        assert self.returned
        after = bytes(u.mem_read(DATA, 65536))
        allowed = [(0xee00, 0xf002), (0x5000, 0x5051), (0x5800, 0x5851),
                   (0x7b43, 0x7b45), (0xd124, 0xd126),
                   (0x6000, 0x6000 + (len(entries) + 2) * 2),
                   (0x6100, 0x6100 + (len(entries) + 2) * 2)]
        cursor = 0
        for first, last in sorted(allowed):
            assert after[cursor:first] == before[cursor:first], (kind, first)
            cursor = last
        assert after[cursor:] == before[cursor:]
        assert u.reg_read(UC_X86_REG_SP) == 0xf002
        assert [u.reg_read(r) for r in (UC_X86_REG_BP, UC_X86_REG_SI, UC_X86_REG_DI)] == [0xbabe, 0x1234, 0x5678]
        assert u.reg_read(UC_X86_REG_DS) == u.reg_read(UC_X86_REG_SS) == u.reg_read(UC_X86_REG_ES) == 0x3000
        assert not u.reg_read(UC_X86_REG_EFLAGS) & 0x400
        table = self.word(0x7b43)
        # Read only through the first terminator; guard bytes after it are not
        # extra environment entries.
        values = []
        for i in range(len(entries) + 2):
            pointer = self.word(table + 2 * i)
            if not pointer:
                break
            values.append(self.string(pointer))
        else:
            raise AssertionError('unterminated native environment vector')
        if kind.startswith('get'):
            name = text if direct else text.translate(UPPER)
            expected = next((value[len(name) + 1:] for value in entries if value.startswith(name + b'=')), None)
            assert self.word(0xd124) == 0xabcd
            if direct:
                pointer = u.reg_read(UC_X86_REG_AX)
                assert (None if pointer == 0 else self.string(pointer)) == expected
                assert self.flushes == self.destinations == self.reads == 0
            else:
                assert self.string(0x5800) == (expected or b'')[:80]
                assert self.warnings == int(expected is not None and len(expected) > 80)
                assert self.flushes == self.destinations == self.reads == 1
            assert values == list(entries)
        elif kind == 'alias':
            assert values == [b'LOC_B=TWO'] and self.word(0xd124) == 0
            assert self.reads == 2 and self.allocations == [4]
        else:
            value = text if direct else text.translate(UPPER)
            expected = list(entries)
            status = 65535
            allocations = []
            if b'=' in value:
                name, tail = value.split(b'=', 1)
                index = next((i for i, entry in enumerate(entries) if entry == name or entry.startswith(name + b'=')), None)
                status = 0
                if index is not None:
                    if tail:
                        expected[index] = value
                    else:
                        del expected[index]
                        allocations = [len(entries) * 2]
                elif tail:
                    allocations = [(len(entries) + 2) * 2]
                    if fail:
                        status = 65535
                    else:
                        expected.append(value)
            assert values == expected, (kind, text, values, expected)
            assert self.allocations == allocations
            assert self.word(0xd124) == (0xabcd if direct else status)
            if direct:
                assert u.reg_read(UC_X86_REG_AX) == status
            assert self.reads == (0 if direct else 1) and not self.flushes
        return after[:0xee00], self.allocations, self.warnings


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--original', type=Path)
    args = parser.parse_args()
    raw = args.original.read_bytes() if args.original else None
    if raw:
        assert hashlib.sha256(raw).hexdigest() == json.loads((ROOT / 'standalone/fixtures/aspect_environment_native_units.json').read_text())['original_sha256']
    models = [Machine()] + ([Machine(raw)] if raw else [])
    count, seen = 0, set()
    def case(*positional, **keywords):
        nonlocal count
        values = [m.run(*positional, **keywords) for m in models]
        assert all(value == values[0] for value in values)
        seen.update(models[0].seen)
        count += 1
    for name in (b'', b'A', b'a', b'AB', b'BAD', b'MISSING', b'lower', b'A=B', b'X' * 80):
        for entries in ((), (b'A=ONE', b'AB=TWO', b'lower=Mixed', b'=EMPTY', b'BAD'), (name.translate(UPPER) + b'=' + b'X' * 81,)):
            for kind in ('get', 'get-native'):
                case(kind, name, entries)
    for byte in range(1, 256):
        name = b'K' + bytes([byte])
        value = name.translate(UPPER) + b'=Mixed' + bytes([byte])
        case('get', name, (value,))
        case('put', name + b'=mixed', ())
    for text in (b'', b'A', b'A=', b'A=Mixed', b'AB=OTHER', b'=Value', b'=',
                 b'NEW=Value=Again', b'lower=changed', b'BAD=Fixed', b'A=' + b'x' * 78):
        for entries in ((), (b'A=ONE',), (b'A=ONE', b'AB=TWO', b'lower=Mixed', b'=EMPTY', b'BAD')):
            for fail in (False, True):
                for kind in ('put', 'put-native'):
                    case(kind, text, entries, fail)
    case('alias', b'LOC_A=one', ())
    result = dict(passed=True, cases=count, original_comparisons=count if raw else 0,
                  checker_sha256=sha(Path(__file__)), manifest_sha256=sha(OUT / 'manifest.json'),
                  instruction_addresses=len(seen),
                  scope='Actual wrappers/bounded-copy/lookup/update and five reused CRT primitives. Operand/near realloc/returning warning boundaries; direct and command case rules, missing/empty/long values, replacement/deletion/allocator failures and borrowed-buffer aliasing. Complete nonstack guard and BP/SI/DI/DS=SS/ES/DF checks. No maintained owner or real DOS lifetime claim.')
    (OUT / ('native-checks.json' if raw else 'checks.json')).write_text(json.dumps(result, indent=2) + '\n')
    print('Environment:', count, 'cases,', result['original_comparisons'], 'original comparisons PASS')


if __name__ == '__main__':
    main()
