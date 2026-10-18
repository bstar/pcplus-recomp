#!/usr/bin/env python3
"""Optional original-instruction IO replay with synthetic in-memory directories.

Requires an explicitly supplied, SHA-verified original EXE. Never reads a DIR,
DTP, PRM, installation, user's phone numbers, or an actual filesystem stream.
C stdio/path resolution and far-memory copy are declared modeled boundaries.
"""
import argparse
import hashlib
import json
import random
import struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_16, UC_HOOK_CODE
from unicorn.x86_const import (UC_X86_REG_CS, UC_X86_REG_DS, UC_X86_REG_SS,
                              UC_X86_REG_ES, UC_X86_REG_SP, UC_X86_REG_IP,
                              UC_X86_REG_AX)
from codec import DialingDirectory201, DIRECTORY_SIZE

EXPECTED = '6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
# Saved REA overlay manifest, verified directly against the selected EXE.
OVERLAYS = ((64208, 3808, 0xd4d0), (76592, 1536, 0xe3b0))
DS = 0x30000
XMS = 0x60000


class OriginalIO:
    def __init__(self, original):
        self.uc = Uc(UC_ARCH_X86, UC_MODE_16)
        self.uc.mem_map(0, 0x100000)
        self.uc.mem_write(0x10000, original[0x1200:0x1200 + 53456])
        for start, length, destination in OVERLAYS:
            self.uc.mem_write(0x10000 + destination, original[start:start + length])
        self.uc.mem_write(DS, original[153936:153936 + 60080])
        for reg, value in ((UC_X86_REG_CS, 0x1000), (UC_X86_REG_DS, DS >> 4),
                           (UC_X86_REG_SS, DS >> 4), (UC_X86_REG_ES, DS >> 4)):
            self.uc.reg_write(reg, value)
        # Far table starts at6000:0000; real slot0 remains unused.
        self.uc.mem_write(DS + 0xe64a, struct.pack('<3H', XMS >> 4, 0, DS >> 4))
        self.file = bytearray()
        self.position = 0
        self.events = []
        self.uc.hook_add(UC_HOOK_CODE, self.hook)

    def hook(self, uc, address, size, unused):
        if address == 0x1c000:
            uc.emu_stop()
            return
        functions = {0x1353d, 0x1841a, 0x1845a, 0x186ac, 0x1853a,
                     0x19286, 0x198b0, 0x18c54, 0x1335c}
        if address not in functions:
            return
        sp = uc.reg_read(UC_X86_REG_SP)
        ret, *args = struct.unpack('<7H', uc.mem_read(DS + sp, 14))
        result = 0
        if address == 0x1353d:
            result = args[0]  # Program path resolver, synthetic path unchanged.
        elif address == 0x1841a:
            result = 1  # Existing synthetic FILE handle.
            self.position = 0
        elif address in (0x1845a, 0x186ac):
            pointer, item_size, count, handle = args[:4]
            assert handle == 1 and item_size > 0
            amount = item_size * count
            self.events.append(('read' if address == 0x1845a else 'write',
                                self.position, item_size, count))
            if address == 0x1845a:
                data = self.file[self.position:self.position + amount]
                uc.mem_write(DS + pointer, bytes(data))
                self.position += len(data)
                result = len(data) // item_size
            else:
                end = self.position + amount
                if end > len(self.file):
                    self.file.extend(bytes(end - len(self.file)))
                self.file[self.position:end] = uc.mem_read(DS + pointer, amount)
                self.position = end
                result = count
        elif address == 0x1853a:
            handle, low, high, whence = args[:4]
            assert handle == 1 and whence == 0
            self.position = low | high << 16
            self.events.append(('seek', self.position))
        elif address == 0x19286:
            source_segment, source_offset, target_segment, target_offset, amount = args[:5]
            uc.mem_write(target_segment * 16 + target_offset,
                         bytes(uc.mem_read(source_segment * 16 + source_offset, amount)))
        elif address == 0x1335c:
            raise AssertionError('Unexpected original directory error-dialog path')
        # 98b0/8c54 model flush; file bytes are already in the synthetic stream.
        uc.reg_write(UC_X86_REG_AX, result)
        uc.reg_write(UC_X86_REG_SP, sp + 2)
        uc.reg_write(UC_X86_REG_IP, ret)

    def call(self, entry, *args):
        self.uc.reg_write(UC_X86_REG_SP, 0xf000)
        self.uc.mem_write(DS + 0xf000, struct.pack('<' + 'H' * (len(args) + 1), 0xc000, *args))
        self.uc.emu_start(0x10000 + entry, 0x20000, count=200000)
        assert self.uc.reg_read(UC_X86_REG_IP) == 0xc000, 'Unexpected service or nontermination'
        return self.uc.reg_read(UC_X86_REG_AX)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('original', type=Path)
    parser.add_argument('--output', type=Path, default=Path('build/directory/original-replay.json'))
    args = parser.parse_args()
    original = args.original.read_bytes()
    if hashlib.sha256(original).hexdigest() != EXPECTED:
        raise ValueError('Original EXE does not match the proved PCPlus2.01 revision')
    checks = []
    machine = OriginalIO(original)
    # Original creator emits startup header and 200 copies of its true template.
    machine.call(0xe8ce, 0x66d2)
    assert bytes(machine.file) == DialingDirectory201.blank().to_bytes()
    assert machine.events[0] == ('write', 0, 25, 10)
    assert len(machine.events) == 201
    checks.append('original-creator-e8ce-matches-source-blank-byte-for-byte')

    rng = random.Random(201)
    raw = rng.randbytes(DIRECTORY_SIZE)
    machine.file = bytearray(raw)
    machine.events.clear()
    machine.uc.mem_write(XMS, bytes([0xa5]) * 114)
    assert machine.call(0xe812, 0x66d2, 1) == 1
    assert bytes(machine.uc.mem_read(DS + 0xe484, 250)) == raw[:250]
    assert bytes(machine.uc.mem_read(XMS, 114)) == bytes([0xa5]) * 114
    assert bytes(machine.uc.mem_read(XMS + 114, 200 * 114)) == raw[250:]
    assert machine.events[0] == ('read', 0, 25, 10)
    assert machine.events[1:] == [('read', 250 + i * 570, 114, 5) for i in range(40)]
    checks.append('original-reader-e812-header-and200records-synthetic-random-bytes')

    for index in (1, 97, 200):
        offset = 250 + (index - 1) * 114
        machine.call(0xddb6, index)
        assert bytes(machine.uc.mem_read(DS + 0xe650, 114)) == bytes(machine.file[offset:offset + 114])
        replacement = rng.randbytes(114)
        machine.uc.mem_write(DS + 0xe650, replacement)
        machine.call(0xdd94, index)
        assert bytes(machine.uc.mem_read(XMS + index * 114, 114)) == replacement
        before = bytes(machine.file)
        machine.call(0xdd28, index, 1)
        assert bytes(machine.file) == before[:offset] + replacement + before[offset + 114:]
        # Then modify all bytes in memory; partial path must store date/count only.
        next_record = rng.randbytes(114)
        machine.uc.mem_write(XMS + index * 114, next_record)
        before = bytes(machine.file)
        machine.call(0xdd28, index, 0)
        start = offset + 0x3d
        assert bytes(machine.file) == before[:start] + next_record[0x3d:0x48] + before[start + 11:]
    checks.append('original-ddb6-dd94-load-store-dd28-full-and11byte-date-count-writes-at1-97-200')

    machine.file = bytearray(raw[:-1])
    assert machine.call(0xe812, 0x66d2, 1) == 0
    checks.append('original-reader-rejects-short-final-record-in-nondialog-mode')
    result = {'passed': True, 'source_sha256': EXPECTED, 'checks': checks,
              'scope': 'Actual original e812/e8ce/ddb6/dd94/dd28 instructions. Synthetic memory-only FILE; modeled C path/stdio and far copy; no original directory or private content read.'}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
