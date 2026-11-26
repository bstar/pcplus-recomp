#!/usr/bin/env python3
"""Exhaust native screen WORD getters; optional preserved-original comparison."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import struct
import subprocess

from unicorn import Uc, UC_ARCH_X86, UC_MODE_16, UC_HOOK_CODE
from unicorn.x86_const import (UC_X86_REG_AX, UC_X86_REG_BX, UC_X86_REG_CX,
    UC_X86_REG_DX, UC_X86_REG_BP, UC_X86_REG_SI, UC_X86_REG_DI,
    UC_X86_REG_SP, UC_X86_REG_IP, UC_X86_REG_CS, UC_X86_REG_DS,
    UC_X86_REG_ES, UC_X86_REG_SS, UC_X86_REG_EFLAGS)

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = '6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
# name, selector, overlay16 entry, original DS word, resident overlay thunk
FIELDS = [
    ('col', 0, 0xd9a7, 0x399e, 0xc5df),
    ('row', 12, 0xd9e8, 0x399c, 0xc963),
    ('cols', 13, 0xd9ec, 0x7a72, 0xc9e7),
    ('rows', 14, 0xd9f0, 0x7a74, 0xca2f),
    ('bold', 15, 0xd9f4, 0x1d34, 0xca77),
    ('dim', 16, 0xd9f8, 0x1d36, 0xcabf),
    ('norm', 17, 0xd9fc, 0x1d32, 0xcb07),
    ('rev', 18, 0xda00, 0x1d38, 0xcb43),
    ('uline', 19, 0xda04, 0x1d3a, 0xcb8b),
]
# Retained original D988 assembly, including signed upper-bound branch and RET2.
DISPATCH = bytes.fromhex(
    '55 8b ec 83 7e 04 1d 7f 0b 8b 5e 04 d1 e3 ff 97 b6 4c '
    'eb 05 e8 e9 75 2b c0 8b e5 5d c2 02 00')
DATA, CODE, STACK, STOP = 0x40000, 0x10000, 0x8000, 0x0100
REGISTERS = (UC_X86_REG_BX, UC_X86_REG_CX, UC_X86_REG_DX,
             UC_X86_REG_BP, UC_X86_REG_SI, UC_X86_REG_DI, UC_X86_REG_ES)
REGIONS = ((0x1d2e, 18), (0x3998, 14), (0x7a6e, 14))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(u, rng, selector=None):
    preserved = {reg: rng.randrange(65536) for reg in REGISTERS}
    preserved.update({UC_X86_REG_CS: CODE >> 4, UC_X86_REG_DS: DATA >> 4,
                      UC_X86_REG_SS: DATA >> 4})
    for reg, value in preserved.items():
        u.reg_write(reg, value)
    u.reg_write(UC_X86_REG_AX, rng.randrange(65536))
    u.reg_write(UC_X86_REG_EFLAGS, (rng.randrange(65536) & 0x0cd5) | 2)
    u.reg_write(UC_X86_REG_SP, STACK)
    frame = struct.pack('<HH', STOP, selector if selector is not None else 0x6ab9)
    u.mem_write(DATA+STACK-8, b'PRESTACK'+frame+b'POSTSTACK')
    return preserved, u.reg_read(UC_X86_REG_EFLAGS), frame


def check_return(u, preserved, frame, cleanup, flags=None):
    assert u.reg_read(UC_X86_REG_IP) == STOP
    assert u.reg_read(UC_X86_REG_SP) == STACK+2+cleanup
    assert all(u.reg_read(reg) == value for reg, value in preserved.items())
    if flags is not None:
        assert u.reg_read(UC_X86_REG_EFLAGS) == flags
    # The getter may not write the caller's return/argument/outer-stack bytes.
    assert bytes(u.mem_read(DATA+STACK, len(frame)+9)) == frame+b'POSTSTACK'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--original', type=Path)
    args = parser.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT/'build') and not out.exists()
    out.mkdir(parents=True)
    original = None
    original_sources = {}
    if args.original:
        assert sha(args.original) == ORIGINAL
        original = args.original.read_bytes()
        mapping = ROOT/'analysis/pcplus-overlays/manifest.json'
        overlay = next(o for o in json.loads(mapping.read_text())['overlays'] if o['id'] == 16)
        base = overlay['source_file_offset']-overlay['relative_load_segment']*16
        assert original[base+0xd988:base+0xd9a7] == DISPATCH
        original_sources[str(mapping.relative_to(ROOT))] = sha(mapping)

    rng = random.Random(0xd9a7)
    fields, binaries = [], {}
    for unit, (name, selector, entry, address, thunk) in enumerate(FIELDS):
        binary = out/(name+'.bin')
        subprocess.run(['nasm', '-fbin', '-DASPECT_TERMINAL_FLAT',
            '-DASPECT_TERMINAL_UNIT='+str(unit),
            str(ROOT/'src/aspect/terminal_builtins.asm'), '-o', str(binary)], check=True)
        code = binary.read_bytes()
        # Independent encoding and original DS address, not a masked result model.
        assert code == b'\xa1'+struct.pack('<H', address)+b'\xc3', name
        if original is not None:
            assert original[base+entry:base+entry+len(code)] == code, name
            assert struct.unpack_from('<H', original, 0x25950+0x4cb6+selector*2)[0] == thunk
            assert original[0x1200+thunk:0x1200+thunk+12] == (
                bytes.fromhex('9a ec 02 ec 0a 10 00 ea')+struct.pack('<HH', entry, 0))
        binaries[name] = code
        u = Uc(UC_ARCH_X86, UC_MODE_16)
        u.mem_map(0, 0x100000)
        u.mem_write(CODE+entry, code)
        regions = {at: bytearray(rng.randbytes(size)) for at, size in REGIONS}
        # Every unrelated word is independently seeded, including neighboring
        # attributes, row/column and width/height, with untouched outer canaries.
        for _, _, _, other, _ in FIELDS:
            for at, region in regions.items():
                if at <= other < at+len(region):
                    struct.pack_into('<H', region, other-at, rng.randrange(65536))
        for at, region in regions.items():
            u.mem_write(DATA+at, bytes(region))
        selected = next((at, region) for at, region in regions.items() if at <= address < at+len(region))
        for value in range(65536):
            struct.pack_into('<H', selected[1], address-selected[0], value)
            u.mem_write(DATA+address, struct.pack('<H', value))
            preserved, flags, frame = prepare(u, rng)
            u.emu_start(CODE+entry, CODE+STOP, count=3)
            assert u.reg_read(UC_X86_REG_AX) == value, (name, value)
            check_return(u, preserved, frame, 0, flags)
            for at, region in regions.items():
                assert bytes(u.mem_read(DATA+at, len(region))) == region, (name, value, at)
            assert bytes(u.mem_read(DATA+STACK-8, 8)) == b'PRESTACK'
        fields.append(dict(name=name, selector=selector, entry=hex(entry),
            ds_word=hex(address), resident_thunk=hex(thunk), inputs=65536,
            bytes=len(code), sha256=sha(binary)))
        print('PASS', name, '65536 WORD inputs', flush=True)

    dispatch_cases = []
    if original is not None:
        u = Uc(UC_ARCH_X86, UC_MODE_16)
        u.mem_map(0, 0x100000)
        u.mem_write(CODE+0xd988, original[base+0xd988:base+0xd9a7])
        u.mem_write(DATA+0x4cb6, original[0x25950+0x4cb6:0x25950+0x4cb6+60])
        thunks = {thunk: entry for _, _, entry, _, thunk in FIELDS}
        visited = []

        def overlay_boundary(cpu, at, size, unused):
            if at-CODE in thunks:
                visited.append(at-CODE)
                # Model the original overlay loader's transfer only. The exact
                # resident thunk bytes were checked above; never execute a
                # synthetic analysis image or claim the loader was exercised.
                cpu.reg_write(UC_X86_REG_IP, thunks[at-CODE])

        u.hook_add(UC_HOOK_CODE, overlay_boundary)
        for name, selector, entry, address, thunk in FIELDS:
            u.mem_write(CODE+entry, original[base+entry:base+entry+4])
            u.mem_write(CODE+thunk, original[0x1200+thunk:0x1200+thunk+12])
        for name, selector, entry, address, thunk in FIELDS:
            for value in (0, 1, 14, 15, 127, 128, 255, 256, 0x1234, 0x7fff, 0x8000, 0xff00, 0xffff):
                for _, _, _, other, _ in FIELDS:
                    u.mem_write(DATA+other, struct.pack('<H', rng.randrange(65536)))
                u.mem_write(DATA+address, struct.pack('<H', value))
                before = {at: bytes(u.mem_read(DATA+at, size)) for at, size in REGIONS}
                preserved, _, frame = prepare(u, rng, selector)
                # Native dispatcher uses BX for the callback-table index and
                # changes arithmetic flags; its getter preserves both.
                preserved[UC_X86_REG_BX] = selector*2
                visited.clear()
                u.emu_start(CODE+0xd988, CODE+STOP, count=30)
                assert u.reg_read(UC_X86_REG_AX) == value, (name, value)
                check_return(u, preserved, frame, 2)
                assert visited == [thunk], (name, visited)
                assert all(bytes(u.mem_read(DATA+at, len(data))) == data for at, data in before.items())
                dispatch_cases.append(dict(name=name, selector=selector, value=value))

    sources = ['src/aspect/terminal_builtins.asm', str(Path(__file__).relative_to(ROOT))]
    result = dict(passed=True, cpu_cases=9*65536+len(dispatch_cases),
        exhaustive_word_cases=9*65536, fields=fields, original_comparison=original is not None,
        original_inputs=[str(args.original)] if args.original else [],
        original_sources=original_sources, dispatcher_cases=dispatch_cases,
        original_dispatcher_bytes=len(DISPATCH) if original is not None else 0,
        original_getter_bytes=36 if original is not None else 0,
        original_thunk_bytes=108 if original is not None else 0,
        sources={name: sha(ROOT/name) for name in sources},
        scope='All65536 WORD values for each of nine exact native getters. '
        'Independent neighboring field/canary bytes, all non-result registers, '
        'FLAGS, DS=SS and near-return ABI checked. Optional original input checks '
        'all getter/dispatcher/thunk bytes and real DS callback-table bindings, '
        'then replays original dispatcher/getters over117 boundary cases. '
        'Overlay-loader transfer is explicitly modeled; its code is not executed. '
        'No linked renderer/RPC, application owner, DOS/BIOS/video, arbitrary '
        'selector, hardware or BBS acceptance claim.')
    (out/'result.json').write_text(json.dumps(result, indent=2)+'\n')
    print('PASS', result['cpu_cases'], 'native terminal integer CPU cases', flush=True)


if __name__ == '__main__':
    main()
