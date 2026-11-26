#!/usr/bin/env python3
"""Check recovered directory integer bodies; optional private original comparison."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import struct
import subprocess
from unicorn import Uc, UC_ARCH_X86, UC_MODE_16
from unicorn.x86_const import (UC_X86_REG_AX, UC_X86_REG_BX, UC_X86_REG_CX,
    UC_X86_REG_DX, UC_X86_REG_BP, UC_X86_REG_SI, UC_X86_REG_DI,
    UC_X86_REG_SP, UC_X86_REG_CS, UC_X86_REG_DS, UC_X86_REG_ES,
    UC_X86_REG_SS, UC_X86_REG_EFLAGS)

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = '6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
# name, operand selector, native entry, record offset, width
FIELDS = [('databit', 1, 0xd9ab, 49, 1), ('duplex', 2, 0xd9b0, 51, 1),
          ('mode', 4, 0xd9b9, 74, 1), ('parity', 5, 0xd9be, 48, 1),
          ('port', 6, 0xd9c3, 104, 1), ('stopbit', 8, 0xd9d5, 50, 1),
          ('term', 9, 0xd9da, 73, 1), ('total', 10, 0xd9df, 70, 2)]
THUNKS = [0xc657, 0xc6ab, 0xc6ff, 0xc76b, 0xc78f, 0xc837, 0xc88b, 0xc8eb]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--original', type=Path)
    a = p.parse_args()
    out = a.output.resolve()
    assert out.is_relative_to(ROOT/'build') and not out.exists()
    out.mkdir(parents=True)
    original = None
    if a.original:
        assert sha(a.original) == ORIGINAL
        original = a.original.read_bytes()
        overlays = json.loads((ROOT/'analysis/pcplus-overlays/manifest.json').read_text())
        overlay = next(o for o in overlays['overlays'] if o['id'] == 16)
        base = overlay['source_file_offset']-overlay['relative_load_segment']*16
    rng = random.Random(0xd9ab)
    cases = []
    for unit, (name, selector, start, offset, width) in enumerate(FIELDS, 1):
        binary = out/(name+'.bin')
        subprocess.run(['nasm', '-fbin', '-DASPECT_DIRECTORY_FIELDS_FLAT',
            '-DASPECT_DIRECTORY_FIELDS_UNIT='+str(unit),
            str(ROOT/'src/aspect/directory_fields.asm'), '-o', str(binary)], check=True)
        code = binary.read_bytes()
        expected = (b'\xa0'+struct.pack('<H', 0xe650+offset)+b'\x98\xc3' if width == 1
                    else b'\xa1'+struct.pack('<H', 0xe650+offset)+b'\xc3')
        assert code == expected, name
        if original is not None:
            assert original[base+start:base+start+len(code)] == code, name
            thunk = struct.unpack_from('<H', original, 0x25950+0x4cb6+selector*2)[0]
            assert thunk == THUNKS[unit-1]
            # Resident overlay stub selects overlay16 then far-jumps to the getter.
            assert original[0x1200+thunk:0x1200+thunk+12] == (
                bytes.fromhex('9a ec 02 ec 0a 10 00 ea')+struct.pack('<HH', start, 0))
        u = Uc(UC_ARCH_X86, UC_MODE_16)
        u.mem_map(0, 0x100000)
        u.mem_write(0x10000+start, code)
        count = 256 if width == 1 else 65536
        for value in range(count):
            record = bytearray(rng.randbytes(114))
            record[offset:offset+width] = value.to_bytes(width, 'little')
            u.mem_write(0x4e650, bytes(record))
            u.mem_write(0x48000, struct.pack('<H', 0x100))
            preserved = {r: rng.randrange(65536) for r in
                (UC_X86_REG_BX, UC_X86_REG_CX, UC_X86_REG_DX, UC_X86_REG_BP,
                 UC_X86_REG_SI, UC_X86_REG_DI, UC_X86_REG_ES)}
            preserved.update({UC_X86_REG_CS: 0x1000, UC_X86_REG_DS: 0x4000,
                              UC_X86_REG_SS: 0x4000})
            for reg, v in preserved.items():
                u.reg_write(reg, v)
            flags = (rng.randrange(0x10000) & 0x0cd5) | 2
            u.reg_write(UC_X86_REG_EFLAGS, flags)
            u.reg_write(UC_X86_REG_SP, 0x8000)
            u.reg_write(UC_X86_REG_AX, rng.randrange(65536))
            before_flags = u.reg_read(UC_X86_REG_EFLAGS)
            u.emu_start(0x10000+start, 0x10100, count=4)
            result = value if width == 2 or value < 128 else value | 0xff00
            assert u.reg_read(UC_X86_REG_AX) == result, (name, value)
            assert all(u.reg_read(reg) == v for reg, v in preserved.items())
            assert u.reg_read(UC_X86_REG_SP) == 0x8002
            assert u.reg_read(UC_X86_REG_EFLAGS) == before_flags
            assert bytes(u.mem_read(0x4e650, 114)) == record
        cases.append(dict(name=name, selector=selector, entry=hex(start),
                          resident_thunk=hex(THUNKS[unit-1]), offset=offset,
                          width=width, inputs=count, sha256=sha(binary)))
    result = dict(passed=True, cpu_cases=sum(c['inputs'] for c in cases), fields=cases,
        source_sha256=sha(ROOT/'src/aspect/directory_fields.asm'),
        checker_sha256=sha(Path(__file__)), original_inputs=[str(a.original)] if a.original else [],
        original_comparison=original is not None,
        scope='Exhaustive byte/word inputs for eight exact native bodies. Preserved registers, flags, DS=SS, near return and full record checked. No application loader, dispatcher or physical observation.')
    (out/'result.json').write_text(json.dumps(result, indent=2)+'\n')
    print('PASS', result['cpu_cases'], 'native directory field CPU cases')


if __name__ == '__main__':
    main()
