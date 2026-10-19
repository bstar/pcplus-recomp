#!/usr/bin/env python3
"""Execute recovered SET instructions with explicit byte/bounds/UI boundaries.

No original executable, overlay or initialized original data is read. This is
component coverage, not a DOS application, real renderer or GET command proof.
"""
import argparse
import hashlib
import json
import struct
import subprocess
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_16, UC_HOOK_CODE, UC_HOOK_INTR
from unicorn.x86_const import *

ROOT = Path(__file__).resolve().parents[1]
CODE, DATA = 0x10000, 0x30000
BINDINGS = {0x12: (0xE37E, 0xE953), 0x18: (0x1D1A, 0xE993),
            0x23: (0xE392, 0xEA1C), 0x29: (0xE380, 0xEA49),
            0x2E: (0xE38A, 0xEA6D), 0x30: (0x1D66, 0xEAAD),
            0x3B: (0xE382, 0xEBB4), 0x44: (0xE394, 0xEC77),
            0x4C: (0x1D68, 0xED76), 0x55: (0xE396, 0xEE37),
            0x56: (0xE398, 0xEE3F)}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Machine:
    def __init__(self, units, selector, value=0):
        self.uc = Uc(UC_ARCH_X86, UC_MODE_16)
        self.uc.mem_map(0, 0x100000)
        self.uc.mem_write(DATA, bytes([0xA5]) * 65536)
        for start, blob in units:
            self.uc.mem_write(CODE + start, blob)
        for reg, val in ((UC_X86_REG_CS, CODE >> 4), (UC_X86_REG_DS, DATA >> 4),
                         (UC_X86_REG_SS, DATA >> 4), (UC_X86_REG_ES, 0x4321),
                         (UC_X86_REG_BP, 0x8700), (UC_X86_REG_SI, 0x1234),
                         (UC_X86_REG_DI, 0x5678), (UC_X86_REG_SP, 0x8800),
                         (UC_X86_REG_EFLAGS, 0x602)):
            self.uc.reg_write(reg, val)
        self.put(0x8800, 0xF000)
        self.put(0xE38E, 0x1234)
        for key, (_, entry) in BINDINGS.items():
            self.put(0x4D24 + 2 * key, entry)
        self.bytes = [selector, value]
        self.value = value
        self.refreshed = 0
        self.queries = []
        self.bounds = []
        self.error = False
        self.visited = set()
        self.uc.hook_add(UC_HOOK_CODE, self.hook)
        self.uc.hook_add(UC_HOOK_INTR, self.interrupt)

    def get(self, offset):
        return struct.unpack('<H', self.uc.mem_read(DATA + offset, 2))[0]

    def put(self, offset, value):
        self.uc.mem_write(DATA + offset, struct.pack('<H', value & 65535))

    def scalar(self, value, cleanup=0):
        sp = self.uc.reg_read(UC_X86_REG_SP)
        self.uc.reg_write(UC_X86_REG_AX, value & 65535)
        self.uc.reg_write(UC_X86_REG_IP, self.get(sp))
        self.uc.reg_write(UC_X86_REG_SP, sp + 2 + cleanup)

    def interrupt(self, *args):
        raise AssertionError('Unexpected OS/hardware interrupt')

    def hook(self, uc, address, size, user):
        if address == CODE + 0xF000:
            uc.emu_stop()
        elif address == CODE + 0x4CB4:
            assert self.bytes, 'Read beyond declared byte input'
            self.scalar(self.bytes.pop(0))
        elif address == CODE + 0x2FB8:
            self.refreshed += 1
            self.scalar(0)
        elif address == CODE + 0xDE3A:
            self.queries.append(self.get(uc.reg_read(UC_X86_REG_SP) + 2))
            self.scalar(0, 2)
        elif address == CODE + 0xDD68:
            sp = uc.reg_read(UC_X86_REG_SP)
            upper, lower = self.get(sp + 2), self.get(sp + 4)
            self.bounds.append((lower, upper))
            if not lower <= self.value <= upper:
                self.error = True
                uc.emu_stop()
            else:
                self.scalar(self.value, 4)
        else:
            self.visited.add(address - CODE)

    def run(self, entry=0x5458, argument=None):
        if argument is not None:
            self.put(0x8802, argument)
        self.uc.emu_start(CODE + entry, CODE + 65535, count=10000)
        if not self.error:
            assert self.uc.reg_read(UC_X86_REG_IP) == 0xF000
            assert self.uc.reg_read(UC_X86_REG_SP) == 0x8802 + (2 if argument is not None else 0)
            for reg, val in ((UC_X86_REG_BP, 0x8700), (UC_X86_REG_SI, 0x1234),
                             (UC_X86_REG_DI, 0x5678), (UC_X86_REG_ES, 0x4321),
                             (UC_X86_REG_DS, DATA >> 4), (UC_X86_REG_SS, DATA >> 4)):
                assert self.uc.reg_read(reg) == val
            assert self.uc.reg_read(UC_X86_REG_EFLAGS) & 0x600 == 0x600


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--original', type=Path, help='Optional hash-bound offline byte comparison only')
    args = parser.parse_args()
    manifest_path = ROOT / 'build/aspect-set/manifest.json'
    manifest = json.loads(manifest_path.read_text())
    assert manifest['source_sha256'] == sha(ROOT / 'src/aspect/set_commands.asm')
    units = []
    expected_addresses = set()
    for unit in manifest['units']:
        path = ROOT / f"build/aspect-set/unit{unit['unit']}.bin"
        assert sha(path) == unit['sha256']
        units.append((unit['start'], path.read_bytes()))
        listing = subprocess.check_output(['ndisasm', '-b', '16', '-o', str(unit['start']), str(path)], text=True)
        expected_addresses.update(int(line.split()[0], 16) for line in listing.splitlines()
                                  if len(line.split()[0]) == 8)
    original_inputs = []
    if args.original:
        blob = args.original.read_bytes()
        digest = hashlib.sha256(blob).hexdigest()
        assert digest == '6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
        for unit, (_, code) in zip(manifest['units'], units):
            assert code == blob[unit['file_offset']:unit['file_offset'] + unit['bytes']]
        original_inputs.append(dict(sha256=digest, scope='Static exact selected byte comparison'))
    count = 0
    visited = set()
    def finish(m):
        nonlocal count
        count += 1
        visited.update(m.visited)
    for selector, (target, entry) in BINDINGS.items():
        if selector in (0x30, 0x4C):
            continue
        for value in range(256):
            m = Machine(units, selector, value)
            m.put(0xE382, 2)
            m.run()
            assert m.get(0xE38E) == 0 and m.get(target) == value
            assert m.refreshed == 1 and not m.bytes and not m.queries
            if selector != 0x3B:
                assert m.get(0xE382) == 2
            finish(m)
    for selector, lower, upper in ((0x30, 32, 126), (0x4C, 0, 999)):
        for value in [lower - 1, *range(lower, upper + 1), upper + 1, 65535]:
            m = Machine(units, selector, value)
            target = BINDINGS[selector][0]
            m.run()
            valid = lower <= value <= upper
            assert m.error == (not valid) and m.refreshed == int(valid)
            assert m.bounds == [(lower, upper)]
            if valid:
                assert m.get(target) == ((0xA500 | value) if selector == 0x30 else value)
            else:
                assert m.get(target) == 0xA5A5
            finish(m)
    for selector, (target, entry) in BINDINGS.items():
        for value in (0, 1, 127, 128, 255, 0x1234, 65535):
            m = Machine(units, selector)
            m.put(0xE38E, 1)
            m.put(target, value)
            m.run(entry)
            expected = value
            if selector == 0x30:
                expected = (value & 255) if value & 128 == 0 else (value & 255) | 0xFF00
            assert m.queries == [expected] and m.refreshed == 0
            assert m.get(target) == value
            finish(m)
    for digits in range(1, 6):
        m = Machine(units, 0)
        m.value = 0
        m.run(0xDDA7, argument=digits)
        assert m.bounds == [(0, (10 ** digits - 1) & 65535)]
        finish(m)
    assert visited == expected_addresses, ('Missing/extra source instructions', expected_addresses - visited, visited - expected_addresses)
    report = dict(passed=True, cases=count, native_bytes=manifest['native_bytes'],
                  instruction_count=len(expected_addresses), all_source_instructions_visited=True,
                  instruction_addresses=[hex(v) for v in sorted(visited)],
                  original_inputs=original_inputs, checker_sha256=sha(Path(__file__)),
                  manifest_sha256=sha(manifest_path), source_sha256=manifest['source_sha256'],
                  scope='Actual225 recovered SET instructions with explicit byte reader, bounded integer operand, GET destination and status refresh models. Tests dispatcher/table, raw boolean/counter writes, all valid selected numeric values, rejects, GET helpers, byte sign extension, decimal16-bit arithmetic and near ABI. No full GET grammar, original UI/renderer, actual DOS application, UART or modem claim.')
    out = ROOT / 'build/aspect-set' / ('checks-original.json' if args.original else 'checks.json')
    out.write_text(json.dumps(report, indent=2) + '\n')
    print('Selected SET:', count, 'CPU cases,', len(visited), 'instruction addresses PASS')


if __name__ == '__main__':
    main()
