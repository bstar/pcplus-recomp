#!/usr/bin/env python3
"""Execute recovered XLT instructions with explicit CRT/receive boundaries.

Optional --original repeats the cases using the SHA-bound original instructions.
No target EXE is launched; these are 8086 CPU tests, not DOS filesystem tests.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
from unicorn import Uc, UC_ARCH_X86, UC_MODE_16, UC_HOOK_CODE
from unicorn.x86_const import *

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/translation'
DATA = 0x1fb70
TABLE = 0xd00a
PROOF = ROOT / 'reconstruction/translation/provenance.json'


class Machine:
    def __init__(self, original=None):
        self.uc = Uc(UC_ARCH_X86, UC_MODE_16)
        self.uc.mem_map(0, 0x100000)
        if original is not None:
            # Only the verified resident image is used. No startup/private files.
            self.uc.mem_write(0x10000, original[0x1200:0xe2d0])
        else:
            proof = json.loads(PROOF.read_text())
            for unit in proof['units']:
                self.uc.mem_write(0x10000 + unit['start'],
                                 (OUT / (Path(unit['file']).stem + '.bin')).read_bytes())
        self.uc.hook_add(UC_HOOK_CODE, self.boundary)

    def word(self, offset, value):
        self.uc.mem_write(DATA + offset, struct.pack('<H', value))

    def boundary(self, uc, address, size, _):
        if address == 0x1fff0:
            self.finished = True
            uc.emu_stop()
            return
        services = {0x1353d: ('resolve', 1), 0x1841a: ('open', 2),
                    0x1845a: ('read', 4), 0x186ac: ('write', 4),
                    0x18318: ('close', 1), 0x1aa65: ('receive', 0),
                    0x15ca0: ('wait', 0), 0x1534e: ('script', 1),
                    0x10610: ('dispatch', 1)}
        if address not in services:
            return
        name, count = services[address]
        sp = uc.reg_read(UC_X86_REG_SP)
        values = struct.unpack('<' + 'H' * (count + 1), uc.mem_read(DATA + sp, 2 * (count + 1)))
        ip, args = values[0], list(values[1:])
        self.calls.append((name, args))
        result = 0
        if name == 'resolve':
            assert args == [0x4100]
            result = 0x4200
        elif name == 'open':
            assert args[0] == 0x4200
            result = self.open_result
        elif name in ('read', 'write'):
            assert args == [TABLE, 1, 256, self.open_result]
            if name == 'read':
                fragment = self.file_bytes[:256]
                if fragment:
                    uc.mem_write(DATA + TABLE, fragment)
                result = len(fragment)
            else:
                self.written = bytes(uc.mem_read(DATA + TABLE, 256))
                result = self.write_result
        elif name == 'close':
            assert args == [self.open_result]
            result = self.close_result
        elif name in ('receive', 'wait'):
            result = self.raw_byte
        elif name in ('script', 'dispatch'):
            assert args == [self.mapping[self.raw_byte]]
        uc.reg_write(UC_X86_REG_AX, result & 0xffff)
        # Script logger is callee-clean; the others are caller-clean.
        uc.reg_write(UC_X86_REG_SP, sp + (4 if name == 'script' else 2))
        uc.reg_write(UC_X86_REG_IP, ip)

    def call(self, address, args=()):
        self.calls = []
        self.finished = False
        self.written = None
        uc = self.uc
        for reg, value in [(UC_X86_REG_CS, 0x1000), (UC_X86_REG_DS, 0x1fb7),
                           (UC_X86_REG_SS, 0x1fb7), (UC_X86_REG_SP, 0xf000),
                           (UC_X86_REG_BP, 0xbabe), (UC_X86_REG_SI, 0x1234),
                           (UC_X86_REG_DI, 0x5678), (UC_X86_REG_ES, 0xbeef),
                           (UC_X86_REG_AX, 0xaaaa), (UC_X86_REG_BX, 0xbbbb)]:
            uc.reg_write(reg, value)
        uc.mem_write(DATA + 0xf000, struct.pack('<' + 'H' * (len(args) + 1), 0xfff0, *args))
        uc.emu_start(0x10000 + address, 0, count=10000)
        assert self.finished, hex(address)
        assert uc.reg_read(UC_X86_REG_SP) == 0xf002 + (4 if address == 0x4c74 else 0)
        for reg, value in [(UC_X86_REG_BP, 0xbabe), (UC_X86_REG_SI, 0x1234),
                           (UC_X86_REG_DI, 0x5678), (UC_X86_REG_ES, 0xbeef)]:
            assert uc.reg_read(reg) == value, (hex(address), reg)
        return uc.reg_read(UC_X86_REG_AX)


def exercise(machine):
    count = 0
    # Identity writes precisely the table, including NUL and FF.
    machine.uc.mem_write(DATA + TABLE - 1, bytes([0x97]) * 258)
    machine.call(0x3608)
    assert bytes(machine.uc.mem_read(DATA + TABLE - 1, 258)) == b'\x97' + bytes(range(256)) + b'\x97'
    assert not machine.calls
    count += 1
    mapping = bytes((i * 73 + 19) & 255 for i in range(256))
    machine.mapping = mapping
    machine.uc.mem_write(DATA + TABLE, mapping)
    for wait in (0, 1):
        for script in (0, 1):
            for dispatch in (0, 1):
                machine.word(0xe2f8, script)
                for raw in [*range(256), 0xffff, 0xfffe]:
                    machine.raw_byte = raw
                    result = machine.call(0x4c74, (dispatch, wait))
                    expected = [('wait' if wait else 'receive', [])]
                    if raw < 256:
                        if script:
                            expected.append(('script', [mapping[raw]]))
                        if dispatch:
                            expected.append(('dispatch', [mapping[raw]]))
                        assert result == mapping[raw]
                    else:
                        assert result == raw
                    assert machine.calls == expected
                    count += 1
    machine.word(0x324e, 0x4100)
    machine.close_result = 0
    machine.open_result = 0x4500
    machine.write_result = 256
    for length in (0, 1, 127, 255, 256, 257, 512):
        machine.file_bytes = bytes((i * 29 + 7) & 255 for i in range(length))
        machine.uc.mem_write(DATA + TABLE - 1, b'\x97' + b'\x55' * 256 + b'\x97')
        machine.call(0x35d7)
        expected = machine.file_bytes[:256] + b'\x55' * max(0, 256 - length)
        assert bytes(machine.uc.mem_read(DATA + TABLE - 1, 258)) == b'\x97' + expected + b'\x97'
        assert machine.calls == [('resolve', [0x4100]), ('open', [0x4200, 0x4723]),
                                 ('read', [TABLE, 1, 256, 0x4500]), ('close', [0x4500])]
        count += 1
    for write_result in (0, 1, 255, 256):
        for close_result in (0, 0xffff):
            machine.write_result, machine.close_result = write_result, close_result
            machine.uc.mem_write(DATA + TABLE, mapping)
            assert machine.call(0x35a6) == close_result
            assert machine.written == mapping
            assert machine.calls == [('resolve', [0x4100]), ('open', [0x4200, 0x4720]),
                                     ('write', [TABLE, 1, 256, 0x4500]), ('close', [0x4500])]
            count += 1
    # Evidence of unchecked fopen(NULL), at a controlled CRT boundary only.
    machine.open_result = 0
    machine.file_bytes = b''
    for entry in (0x35a6, 0x35d7):
        machine.call(entry)
        assert machine.calls[2][1][-1] == 0 and machine.calls[3] == ('close', [0])
        count += 1
    return count


def main(original=False):
    build = json.loads((OUT / 'manifest.json').read_text())
    for name, digest in build['sources'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    for unit in json.loads(PROOF.read_text())['units']:
        assert hashlib.sha256((OUT / (Path(unit['file']).stem + '.bin')).read_bytes()).hexdigest() == unit['sha256']
    count = exercise(Machine())
    original_count = 0
    proof = json.loads(PROOF.read_text())
    if original:
        blob = (ROOT / 'analysis/pcplus-originals/PCPLUS-main-2.01.EXE').read_bytes()
        assert hashlib.sha256(blob).hexdigest() == proof['source_sha256']
        for unit in proof['units']:
            assert blob[unit['file_offset']:unit['file_offset'] + unit['bytes']] == (OUT / (Path(unit['file']).stem + '.bin')).read_bytes()
        original_count = exercise(Machine(blob))
        assert count == original_count
    inputs = [Path(__file__), PROOF, ROOT / 'standalone/build_translation.py',
              ROOT / 'reconstruction/uart/encodings.inc']
    inputs += [ROOT / unit['file'] for unit in proof['units']]
    (OUT / 'cpu-results.json').write_text(json.dumps({
        'passed': True, 'cases': count, 'original_comparisons': original_count,
        'exact_bytes': 176,
        'flat_binaries': {Path(unit['file']).stem: unit['sha256'] for unit in proof['units']},
        'inputs': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
        'scope': 'Actual 8086 instructions, controlled CRT/receive/script/dispatch boundaries; not DOS filesystem or live terminal integration.',
        'observed_native_quirks': ['Partial reads retain the old suffix', 'Extra input is ignored after 256 bytes', 'Open/read/write/close failures are unchecked'],
    }, indent=2) + '\n')
    print(f'XLT native: {count} cases; {original_count} original comparisons passed')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--original', action='store_true')
    main(parser.parse_args().original)
