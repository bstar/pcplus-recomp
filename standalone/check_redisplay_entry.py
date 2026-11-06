#!/usr/bin/env python3
"""Execute native Redisplay entry plus actual recovered display/cursor code.

The history viewer, heap, BIOS, CRT and alert endpoints are declared recorders.
--original additionally compares identified original-file slices, never an
analysis image. The ordinary build and source check do not need that file.
"""
import argparse
import itertools
import json
import struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_16, UC_HOOK_CODE, UC_HOOK_INTR, UC_HOOK_INSN
from unicorn.x86_const import *
from build_redisplay_entry import ROOT, CORE, sha


class Machine:
    def __init__(self, output, original=False):
        self.output = output
        self.manifest = json.loads((output / 'manifest.json').read_text())
        self.u = Uc(UC_ARCH_X86, UC_MODE_16)
        self.u.mem_map(0, 0x100000)
        self.units = self.manifest['units']
        assert sha(output / 'chat_sequence.bin') == self.manifest['artifacts']['chat_sequence.bin']
        self.u.mem_write(0x1f800, (output / 'chat_sequence.bin').read_bytes())
        image = None
        if original:
            path = ROOT / 'analysis/pcplus-originals/PCPLUS-main-2.01.EXE'
            assert sha(path) == json.loads((CORE / 'provenance.json').read_text())['original_sha256']
            image = path.read_bytes()
        for unit in self.units:
            path = output / (Path(unit['file']).stem + '.bin')
            assert sha(path) == unit['sha256']
            data = image[unit['file_offset']:unit['file_offset'] + unit['bytes']] if original else path.read_bytes()
            assert len(data) == unit['bytes']
            import hashlib
            assert hashlib.sha256(data).hexdigest() == unit['sha256']
            self.u.mem_write(0x10000 + unit['start'], data)
        # Explicit external boundaries. RETs are harness adapters, not recovered
        # implementation. The real snapshot/copy/free/cursor routines run above.
        for at, pop in [(0x860f, 0), (0x85fc, 0), (0xd95c, 0), (0x427f, 0),
                        (0x6e5a, 0), (0x6dca, 0), (0x376d, 0), (0x7722, 4)]:
            self.u.mem_write(0x10000 + at, b'\xc2' + struct.pack('<H', pop) if pop else b'\xc3')
        self.u.hook_add(UC_HOOK_CODE, self.code)
        self.u.hook_add(UC_HOOK_INTR, self.interrupt)
        self.u.hook_add(UC_HOOK_INSN, self.port_out, None, 1, 0, UC_X86_INS_OUT)

    def put(self, at, value):
        self.u.mem_write(0x50000 + at, struct.pack('<H', value & 65535))

    def word(self, at):
        return int.from_bytes(self.u.mem_read(at, 2), 'little')

    def get(self, at):
        return self.word(0x50000 + at)

    def interrupt(self, u, number, _):
        assert number == 0x10
        ah = u.reg_read(UC_X86_REG_AH)
        assert u.reg_read(UC_X86_REG_BH) == 0
        if ah == 3:
            u.reg_write(UC_X86_REG_DX, self.word(0x450))
        else:
            assert ah == 2
            self.u.mem_write(0x450, struct.pack('<H', u.reg_read(UC_X86_REG_DX)))

    def port_out(self, u, port, size, value, _):
        assert port in (0x3d4, 0x3d5) and size == 1
        self.ports.append((port, value))

    def code(self, u, at, size, _):
        if at == 0x1fe00:
            self.returned = True
            u.emu_stop()
            return
        sp = u.reg_read(UC_X86_REG_SP)
        stack = 0x50000 + sp
        if at == 0x1860f:
            assert self.word(stack + 2) == self.bytes
            self.events.append(('allocate', self.bytes))
            u.reg_write(UC_X86_REG_AX, 0 if self.fail else 0x20)
            u.reg_write(UC_X86_REG_DX, 0 if self.fail else 0x9000)
        elif at == 0x185fc:
            pointer = (self.word(stack + 2), self.word(stack + 4))
            assert pointer == self.pointer
            self.events.append(('free', *pointer))
        elif at in (0x1d95c, 0x1427f):
            self.events.append(('view' if at == 0x1d95c else 'empty',
                                self.get(0xe888), self.get(0x7a50)))
            assert self.get(0x397a) == 0x25 and self.get(0xe8a0) == 0
            assert self.get(0x7a50) == 10000
            if at == 0x1427f:
                assert u.reg_read(UC_X86_REG_BX) == 0x7692
            if not self.fail:
                assert bytes(u.mem_read(0x90020, self.bytes)) == self.video
            # Stand-in viewer draws and changes cursor. Native return must
            # restore the saved screen/cursor, not this deliberately different
            # view. History/head state is kept independent of the screen.
            u.mem_write(0xb8000, self.changed)
            u.mem_write(0x450, b'\x03\x02')
        elif at == 0x16e5a:
            self.events.append(('hide',))
        elif at == 0x16dca:
            self.events.append(('show',))
        elif at == 0x1376d:
            self.events.append(('alert',))
        elif at == 0x17722:
            self.events.append(('tone', self.word(stack + 2), self.word(stack + 4)))

    def call(self, entry, args=()):
        u = self.u
        self.events = []
        self.ports = []
        self.returned = False
        sp = 0xf400
        for value in reversed(args):
            sp -= 2
            self.put(sp, value)
        sp -= 2
        self.put(sp, 0xfe00)
        for reg, value in [(UC_X86_REG_CS, 0x1000), (UC_X86_REG_DS, 0x5000),
                           (UC_X86_REG_SS, 0x5000), (UC_X86_REG_SP, sp),
                           (UC_X86_REG_BP, 0xbabe), (UC_X86_REG_SI, 0x1234),
                           (UC_X86_REG_DI, 0x5678), (UC_X86_REG_EFLAGS, 0x202)]:
            u.reg_write(reg, value)
        u.emu_start(0x10000 + entry, 0, count=250000)
        assert self.returned and u.reg_read(UC_X86_REG_SP) == 0xf400
        assert u.reg_read(UC_X86_REG_DS) == u.reg_read(UC_X86_REG_SS) == 0x5000
        assert u.reg_read(UC_X86_REG_BP) == 0xbabe
        assert u.reg_read(UC_X86_REG_SI) == 0x1234 and u.reg_read(UC_X86_REG_DI) == 0x5678

    def entry(self, rows, policy, legacy, ring, fail, viewport, nested, depth):
        self.bytes = rows * 160
        self.fail = fail
        self.pointer = (0x20, 0x9000)
        self.video = bytes((i * 17 + 3) & 255 for i in range(self.bytes))
        self.changed = bytes((i * 29 + 7) & 255 for i in range(self.bytes))
        self.u.mem_write(0xb8000, self.video + b'END!')
        self.u.mem_write(0x9001e, b'\xa5' * (self.bytes + 4))
        self.u.mem_write(0x450, b'\x09\x07')
        self.u.mem_write(0x44e, b'\x00\x00')
        self.u.mem_write(0x463, b'\xd4\x03')
        start, head, end, wrapped = ring
        top = 0x7a3a + depth * 2
        for at, value in [(0x7a36, top), (0x7a38, 0x7a3a), (0x7a66, legacy), (0x7a72, 80),
                          (0x7a6c, policy), (0x7a7c, self.bytes), (0x7a8c, self.bytes // 2),
                          (0x7a78, 0xb800), (0x7a8e, 0), (0x7a84, viewport),
                          (0x7a7e, 79), (0x4eba, start), (0x4ebe, head),
                          (0x4ec6, end), (0x4ec8, wrapped), (0x2068, 23),
                          (0x7a50, 41), (0x397a, 99), (0xe8a0, 99), (0xe8a2, 99)]:
            self.put(at, value)
        self.call(0xf800 if nested else 0xd830)
        position = (end - 1 if wrapped and head == start else head - 1) & 65535
        active = wrapped or head != start
        expected = ([('hide',)] if policy else []) + [('allocate', self.bytes),
                     ('view' if active else 'empty', position, 10000)]
        expected += [('alert',), ('tone', 100, 440), ('alert',)] if fail else [('free', 0x20, 0x9000)]
        expected += [('show',)] if policy else []
        expected += [('show',)] if nested else []
        assert self.events == expected, (self.events, expected)
        assert self.get(0xe888) == position and self.get(0x7a50) == 23
        assert self.get(0xe8a2) == (viewport + 79 - 256) & 65535
        assert self.get(0x7a36) == top and self.get(0x7a38) == 0x7a3a and self.word(0x450) == 0x0709
        assert [self.get(at) for at in (0x4eba, 0x4ebe, 0x4ec6, 0x4ec8)] == list(ring)
        assert bytes(self.u.mem_read(0xb8000, self.bytes)) == (self.changed if fail else self.video)
        assert bytes(self.u.mem_read(0xb8000 + self.bytes, 4)) == b'END!'
        assert bytes(self.u.mem_read(0x9001e, 2)) == b'\xa5\xa5'
        assert bytes(self.u.mem_read(0x90020 + self.bytes, 2)) == b'\xa5\xa5'
        if fail:
            assert bytes(self.u.mem_read(0x90020, self.bytes)) == b'\xa5' * self.bytes
        else:
            assert bytes(self.u.mem_read(0x90020, self.bytes)) == self.video
        assert bool(self.ports) == (not legacy)
        return self.events, self.ports, position, self.get(0xe8a2)

    def wrapper(self, pointer):
        self.pointer = pointer
        self.bytes = 4000
        self.video = bytes((i * 7 + 13) & 255 for i in range(self.bytes))
        self.u.mem_write(0xb8000, b'\xa5' * self.bytes)
        for at, value in [(0x7a78, 0xb800), (0x7a8c, 2000), (0x7a8e, 0)]:
            self.put(at, value)
        linear = pointer[1] * 16 + pointer[0]
        if linear:
            self.u.mem_write(linear, self.video)
        self.call(0x4870, pointer)
        expected = [('free', *pointer)] if linear else [('alert',), ('tone', 100, 440), ('alert',)]
        assert self.events == expected
        assert bytes(self.u.mem_read(0xb8000, self.bytes)) == (self.video if linear else b'\xa5' * self.bytes)
        return self.events


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--original', action='store_true')
    args = parser.parse_args()
    output = args.output.resolve()
    machines = [Machine(output)] + ([Machine(output, True)] if args.original else [])
    rings = [(0, 0, 63000, 0), (0, 1, 63000, 0), (0x6000, 0x6000, 0x7000, 0),
             (0x6000, 0x6001, 0x7000, 0), (0x6000, 0x6fff, 0x7000, 0),
             (0x6000, 0x6000, 0x7000, 1), (0x6000, 0x6800, 0x7000, 1),
             (0x6000, 0x6fff, 0x7000, 1), (0x6000, 0x6000, 0x7000, 65535)]
    count = 0
    for values in itertools.product((25, 28, 43, 50), (0, 1, 65535), (0, 1), rings,
                                     (False, True), (0, 0xffff), (False, True), (0, 7)):
        results = [m.entry(*values) for m in machines]
        assert all(r == results[0] for r in results)
        count += 1
    for pointer in [(0x20, 0x9000), (0, 0x9000), (0x9000, 0), (0, 0)]:
        results = [m.wrapper(pointer) for m in machines]
        assert all(r == results[0] for r in results)
        count += 1
    report = dict(passed=True, cases=count, original_comparisons=count if args.original else 0,
                  manifest_sha256=sha(output / 'manifest.json'), checker_sha256=sha(Path(__file__)),
                  original_inputs=[] if not args.original else [
                      dict(path='analysis/pcplus-originals/PCPLUS-main-2.01.EXE',
                           sha256=json.loads((CORE / 'provenance.json').read_text())['original_sha256'])],
                  scope='Actual recovered entry/restore/copy/cursor instructions; heap, viewer, BIOS/CRT and alert endpoints modeled. No DOS, live Chat handoff, serial, hardware or acoustic acceptance.')
    (output / ('cpu-original.json' if args.original else 'cpu.json')).write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
