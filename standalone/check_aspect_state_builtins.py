#!/usr/bin/env python3
"""Exhaust FROMDDIR/MONO native WORD getters; optional original byte comparison."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import struct
import subprocess

from unicorn import Uc, UC_ARCH_X86, UC_MODE_16
from unicorn.x86_const import UC_X86_REG_AX, UC_X86_REG_EFLAGS
from check_aspect_terminal_builtins import prepare, check_return, CODE, DATA, STACK, STOP

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = '6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
# name, original integer selector, overlay16 entry, original DS WORD, thunk
FIELDS = [('fromddir', 24, 0xda18, 0x4afe, 0xcd17),
          ('mono', 26, 0xda24, 0x7a86, 0xbc67)]
EVIDENCE = {
    'fromddir': 'ev_96a50639e4f0c4935b6840338745f63fdf6291ee495118fc722560e35e3d7e1e',
    'mono': 'ev_0a3f743642ba0d7946d987ba75937b67d1d5cdbc1c7ce217c88f7ff417c17809',
}
# Independent canaries include selected-entry DSE482 and profile flag DS8FF6:
# neither is the native FROMDDIR/physical-MONO backing word.
REGIONS = ((0x4af8, 18), (0x7a80, 26), (0x8ff0, 14), (0xe47c, 16))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--original', type=Path)
    args = parser.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT/'build') and not out.exists()
    out.mkdir(parents=True)
    source = ROOT/'src/aspect/state_builtins.asm'
    names = [str(source.relative_to(ROOT)), 'standalone/check_aspect_state_builtins.py',
             'standalone/check_aspect_terminal_builtins.py']
    sources = {name: sha(ROOT/name) for name in names}
    original = None
    original_metadata = None
    if args.original:
        assert sha(args.original) == ORIGINAL
        original = args.original.read_bytes()
        mapping = ROOT/'analysis/pcplus-overlays/manifest.json'
        overlay = next(o for o in json.loads(mapping.read_text())['overlays'] if o['id'] == 16)
        base = overlay['source_file_offset']-overlay['relative_load_segment']*16
        original_metadata = dict(sha256=ORIGINAL, mapping_sha256=sha(mapping),
            static_getter_bytes=8, static_thunk_bytes=24,
            table='DS4CB6 WORD callback slots24/26',
            runtime_original_comparisons=0,
            scope='Original getter bytes, callback-table bindings and resident overlay16 thunks compared statically. No original loader/dispatcher/producer executes.')
    rng = random.Random(0xda18)
    fields = []
    for unit, (name, selector, entry, address, thunk) in enumerate(FIELDS):
        binary = out/(name+'.bin')
        subprocess.run(['nasm', '-fbin', '-DASPECT_STATE_FLAT',
            '-DASPECT_STATE_UNIT='+str(unit), str(source), '-o', str(binary)], check=True)
        code = binary.read_bytes()
        assert code == b'\xa1'+struct.pack('<H', address)+b'\xc3', name
        if original is not None:
            assert original[base+entry:base+entry+4] == code, name
            assert struct.unpack_from('<H', original, 0x25950+0x4cb6+selector*2)[0] == thunk, name
            assert original[0x1200+thunk:0x1200+thunk+12] == (
                bytes.fromhex('9a ec 02 ec 0a 10 00 ea')+struct.pack('<HH', entry, 0)), name
        u = Uc(UC_ARCH_X86, UC_MODE_16)
        u.mem_map(0, 0x100000)
        u.mem_write(CODE+entry, code)
        regions = {at: bytearray(rng.randbytes(size)) for at, size in REGIONS}
        # Seed independent full WORDs, not synchronized Boolean/low-byte values.
        for other in (0x4afe, 0x7a86, 0x8ff6, 0xe482):
            at, region = next((at, region) for at, region in regions.items()
                              if at <= other and other+2 <= at+len(region))
            struct.pack_into('<H', region, other-at, rng.randrange(65536))
        for at, region in regions.items():
            u.mem_write(DATA+at, bytes(region))
        selected_at, selected = next((at, region) for at, region in regions.items()
                                    if at <= address and address+2 <= at+len(region))
        for value in range(65536):
            struct.pack_into('<H', selected, address-selected_at, value)
            u.mem_write(DATA+address, struct.pack('<H', value))
            preserved, _, frame = prepare(u, rng)
            # Include both IF states as well as DF and arithmetic status flags;
            # TF remains clear so the scalar getter cannot invoke a debug trap.
            u.reg_write(UC_X86_REG_EFLAGS, (rng.randrange(65536)&0x0ed5)|2)
            flags = u.reg_read(UC_X86_REG_EFLAGS)
            u.emu_start(CODE+entry, CODE+STOP, count=3)
            assert u.reg_read(UC_X86_REG_AX) == value, (name, value)
            check_return(u, preserved, frame, 0, flags)
            assert bytes(u.mem_read(DATA+STACK-8, 8)) == b'PRESTACK'
            for at, region in regions.items():
                assert bytes(u.mem_read(DATA+at, len(region))) == region, (name, value, at)
        fields.append(dict(name=name, selector=selector, entry=hex(entry),
            original_DS_word=hex(address), resident_thunk=hex(thunk), inputs=65536,
            bytes=4, binary_sha256=sha(binary), evidence_id=EVIDENCE[name]))
        print('PASS', name, '65536 full WORD values', flush=True)
    assert all(sha(ROOT/name) == digest for name, digest in sources.items()), 'Source changed during replay'
    report = dict(passed=True, CPU_cases=131072, fields=fields, sources=sources,
        original_comparison=original is not None,
        original_inputs=[str(args.original)] if args.original else [], original=original_metadata,
        producer_validation=False,
        related_producer_evidence=dict(
            fromddir_directory='ev_186cf7e819989310ab103a002a93c6fd62517af38d1568ce7d4d0885a258baa9',
            fromddir_manual_clear='ev_fed07cee314ea4408ae7f955c2b21d040fc7a9ffdbc91efbad33596d7c6d65b9',
            mono_geometry='ev_f023afd9e2ef7182dbaf48f2f4693299a3627322109a691056e99c4ce4e7eb6c'),
        scope=__doc__+' All65536 WORD values for each exact getter; full AX result, '
        'preserved non-result registers, FLAGS including IF/DF, DS=SS, near-return '
        'SP/caller frame and independently seeded neighboring/origin/display/profile/entry '
        'canaries checked. Native original bytes/table/thunks are optional static inputs only. '
        'Neither FROMDDIR launch-origin lifecycle nor MONO geometry/cache production '
        'executes here; related evidence identifiers are references, not test coverage. '
        'No linked parent RPC, actual DOS/BIOS/video, hardware or full ASPECT claim.')
    (out/'result.json').write_text(json.dumps(report, indent=2)+'\n')
    print('PASS', report['CPU_cases'], 'native state builtin WORD cases')


if __name__ == '__main__':
    main()
