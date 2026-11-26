#!/usr/bin/env python3
"""Native HITKEY/queue/BIOS peek replay; optional preserved-original comparison."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess

from unicorn import Uc, UC_ARCH_X86, UC_MODE_16, UC_HOOK_CODE, UC_HOOK_INTR, UC_HOOK_MEM_READ
from unicorn.x86_const import *
from check_aspect_keyboard import expected

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = '6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
GETTER = bytes.fromhex('e8fb8a50e8af9dc3')
DEPENDENCIES = [('peek', 0x651a, 22, 0, 0x64fe),
                ('normalize', 0x77d2, 43, 1, 0x77d2),
                ('bios-peek', 0x7842, 21, 2, 0x7836)]
PEEK = [0x4800, 0x4d00, 0x5000, 0x4b00, 0x1c0d, 0x011b]
READ = [0x4800, 0x4d00, 0x5000, 0x4b00, 0x000d, 0x001b]
DATA, CODE, STACK, STOP = 0x40000, 0x10000, 0x8000, 0x100
CANARIES = [(0x5df0, 32), (0x7a5e, 12), (0x7abc, 12)]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class Hitkey:
    def __init__(self, units):
        self.u = Uc(UC_ARCH_X86, UC_MODE_16)
        self.u.mem_map(0, 0x100000)
        self.ranges = []
        for address, code in units:
            self.u.mem_write(CODE+address, code)
            self.ranges.append((CODE+address, CODE+address+len(code)))
        self.u.hook_add(UC_HOOK_CODE, self.code)
        self.u.hook_add(UC_HOOK_INTR, self.bios)
        self.u.hook_add(UC_HOOK_MEM_READ, self.table_read, None,
                        DATA+0x5df0, DATA+0x5e10)
        for at, size in CANARIES:
            self.u.mem_write(DATA+at, bytes((i*43+at)&255 for i in range(size)))
        self.u.mem_write(DATA+0x5df4, struct.pack('<6H', *PEEK))
        self.u.mem_write(DATA+0x5e00, struct.pack('<6H', *READ))
        self.u.mem_write(DATA+0x7a60, b'\x34\x12\0\0\0\0')
        self.calls = 0

    def put(self, offset, value, width=2):
        self.u.mem_write(DATA+offset, value.to_bytes(width, 'little'))

    def stage(self, mode, raw, available=True, count=0, index=0):
        self.mode, self.raw, self.available = mode, raw, available
        self.put(0x7ac0, mode, 1)
        self.put(0x7a62, count)
        self.put(0x7a64, index)

    def code(self, u, address, size, unused):
        if address == CODE+STOP:
            self.returned = True
            u.emu_stop()
            return
        assert any(start <= address < end for start, end in self.ranges), ('unexpected native path', hex(address))
        if address in (CODE+0x651a, CODE+0x77d2, CODE+0x7842):
            self.entries.append(address-CODE)

    def table_read(self, u, access, address, size, value, unused):
        self.table_reads.append((address-DATA, size))

    def bios(self, u, number, unused):
        assert number == 0x16
        function = u.reg_read(UC_X86_REG_AH)
        assert function == self.mode+1, ('HITKEY attempted consuming/read/nonpeek BIOS service', function)
        self.bios_calls += 1
        flags = u.reg_read(UC_X86_REG_EFLAGS)
        u.reg_write(UC_X86_REG_EFLAGS, flags & ~0x40 if self.available else flags | 0x40)
        # The empty case deliberately supplies nonzero AX. Native code must use
        # BIOS ZF rather than confuse the register value with availability.
        u.reg_write(UC_X86_REG_AX, self.raw if self.available else 0x6b31)

    def run(self, want, queued=False):
        u = self.u
        before = {at: bytes(u.mem_read(DATA+at, size)) for at, size in CANARIES}
        low_canary = b'LOW-STACK-CANARY!'
        u.mem_write(DATA+STACK-32, low_canary)
        frame = struct.pack('<H', STOP)+b'RETURN-CANARY'
        u.mem_write(DATA+STACK, frame)
        preserved = {UC_X86_REG_CX: 0x2345, UC_X86_REG_DX: 0x3456,
            UC_X86_REG_BP: 0x4567, UC_X86_REG_SI: 0x5678, UC_X86_REG_DI: 0x6789,
            UC_X86_REG_CS: CODE >> 4, UC_X86_REG_DS: DATA >> 4,
            UC_X86_REG_SS: DATA >> 4, UC_X86_REG_ES: 0x789a}
        for reg, value in preserved.items():
            u.reg_write(reg, value)
        u.reg_write(UC_X86_REG_SP, STACK)
        u.reg_write(UC_X86_REG_AX, 0xa55a)
        u.reg_write(UC_X86_REG_BX, 0x8abc)
        u.reg_write(UC_X86_REG_EFLAGS, 0x643)
        self.returned = False
        self.bios_calls = 0
        self.entries, self.table_reads = [], []
        available = self.available
        u.emu_start(CODE+0xda1c, 0, count=100)
        assert self.returned and u.reg_read(UC_X86_REG_SP) == STACK+2
        assert u.reg_read(UC_X86_REG_AX) == want, (self.mode, self.raw, queued, hex(want), hex(u.reg_read(UC_X86_REG_AX)))
        assert u.reg_read(UC_X86_REG_BX) == STACK-4, 'Native normalizer BX must retain its actual stack-frame address'
        assert all(u.reg_read(reg) == value for reg, value in preserved.items())
        assert u.reg_read(UC_X86_REG_EFLAGS)&0x600 == 0x600, 'IF/DF changed'
        assert self.available == available, 'Peek fixture consumed the offered key'
        assert bytes(u.mem_read(DATA+STACK, len(frame))) == frame
        assert bytes(u.mem_read(DATA+STACK-32, len(low_canary))) == low_canary
        assert all(bytes(u.mem_read(DATA+at, len(data))) == data for at, data in before.items())
        assert self.bios_calls == (0 if queued else 1)
        assert self.entries == ([0x651a, 0x77d2] if queued else [0x651a, 0x7842, 0x77d2])
        if queued:
            index = int.from_bytes(u.mem_read(DATA+0x7a64, 2), 'little')
            assert self.table_reads == [(0x5df4+2*index, 2)], self.table_reads
        else:
            assert not self.table_reads, self.table_reads
        self.calls += 1
        return u.reg_read(UC_X86_REG_AX)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--original', type=Path)
    args = p.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT/'build') and not out.exists()
    out.mkdir(parents=True)
    names = ['src/aspect/hitkey.asm', 'reconstruction/keyboard/core.asm',
        'reconstruction/keyboard/provenance.json', 'reconstruction/uart/encodings.inc',
        'standalone/check_aspect_hitkey_native.py', 'standalone/check_aspect_keyboard.py']
    sources = {name: sha(ROOT/name) for name in names}
    proof = json.loads((ROOT/'reconstruction/keyboard/provenance.json').read_text())
    getter = out/'hitkey.bin'
    subprocess.run(['nasm', '-fbin', '-DASPECT_HITKEY_FLAT',
        str(ROOT/'src/aspect/hitkey.asm'), '-o', str(getter)], check=True)
    assert getter.read_bytes() == GETTER
    units = [(0xda1c, GETTER)]
    regions = {}
    for i, record in enumerate(proof['ranges']):
        binary = out/('keyboard-region-'+str(i)+'.bin')
        subprocess.run(['nasm', '-fbin', '-DKEYBOARD_REGION='+str(i),
            '-I'+str(ROOT/'reconstruction/uart')+'/',
            str(ROOT/'reconstruction/keyboard/core.asm'), '-o', str(binary)], check=True)
        assert binary.stat().st_size == record['size'] and sha(binary) == record['sha256']
        regions[i] = binary.read_bytes()
    for _, address, length, region, start in DEPENDENCIES:
        units.append((address, regions[region][address-start:address-start+length]))
    original = None
    original_metadata = None
    if args.original:
        assert sha(args.original) == ORIGINAL
        original = args.original.read_bytes()
        mapping = ROOT/'analysis/pcplus-overlays/manifest.json'
        overlay = next(o for o in json.loads(mapping.read_text())['overlays'] if o['id'] == 16)
        base = overlay['source_file_offset']-overlay['relative_load_segment']*16
        assert original[base+0xda1c:base+0xda24] == GETTER
        thunk = struct.unpack_from('<H', original, 0x25950+0x4cb6+25*2)[0]
        assert thunk == 0xbbfb
        assert original[0x1200+thunk:0x1200+thunk+12] == bytes.fromhex('9aec02ec0a1000ea1cda0000')
        for i, record in enumerate(proof['ranges']):
            start = int(record['start'], 16)
            assert original[0x1200+start:0x1200+start+record['size']] == regions[i]
        original_units = [(0xda1c, original[base+0xda1c:base+0xda24])]
        for _, address, length, _, _ in DEPENDENCIES:
            original_units.append((address, original[0x1200+address:0x1200+address+length]))
        assert original_units == units
        original_metadata = dict(sha256=ORIGINAL, selector=25, resident_thunk='0xbbfb',
            overlay=16, getter_entry='0xda1c', getter_bytes=8, resident_dependency_bytes=86,
            complete_keyboard_region_bytes=sum(r['size'] for r in proof['ranges']),
            mapping_sha256=sha(mapping), scope='Original table/thunk/bytes checked statically; original loader and dispatcher do not execute.')

    machines = [('source', Hitkey(units))]
    if original is not None:
        machines.append(('original', Hitkey(original_units)))
    checks = []
    for label, m in machines:
        for mode in (0, 16):
            m.stage(mode, 0)
            for raw in range(65536):
                m.raw = raw
                m.run(expected(raw or 0x100))
            checks.append(dict(case='all-raw-BIOS-WORDs', implementation=label,
                mode=mode, inputs=65536, passed=True))
        for mode in (0, 16):
            for raw in (0, 0x1e61, 0x011b, 0x0e08, 0x0e7f, 0x4800,
                        0x48e0, 0xe00d, 0xe02f, 0x3920, 0x372a, 0x8061, 0xffff):
                m.stage(mode, raw)
                for repeat in range(3):
                    m.run(expected(raw or 0x100))
            m.stage(mode, 0, available=False)
            for repeat in range(3):m.run(0)
            # A genuinely new observation may change; peeking never removes it.
            m.available, m.raw = True, 0xe02f
            m.run(expected(0xe02f));m.run(expected(0xe02f))
            m.available = False;m.run(0)
            checks.append(dict(case='empty-occupied-zero-repeat-and-new-arrival',
                implementation=label, mode=mode, passed=True))
            for index in range(6):
                for count in (1, 2, 65535):
                    m.stage(mode, 0x1e61, available=True, count=count, index=index)
                    for repeat in range(3):m.run(expected(PEEK[index]), queued=True)
            # Count zero bypasses the unchecked index entirely and uses BIOS.
            m.stage(mode, 0x48e0, count=0, index=65535)
            m.run(expected(0x48e0))
            checks.append(dict(case='six-queue-events-repetitions-table-read-and-zero-count',
                implementation=label, mode=mode, queued_samples=54, passed=True))
        print('PASS HITKEY', label, m.calls, 'native getter calls', flush=True)
    assert all(sha(ROOT/name) == digest for name, digest in sources.items()), 'Source changed during native replay'
    evidence = dict(getter='ev_172f3e6ad25ed8638f5eb8f48e91838efeef253cd2edb73b1d08d430616d3c22',
        peek='ev_9bc44de1285653267fe1e2c64a2f8d8f3fffa0fb3fcccfe61137d4b9fbc4fcd5',
        normalizer='ev_cb670ed8c108fd2f8a4d03d1d83765074271c3cae5e31f2e0ac94f3c59873699',
        bios_peek='ev_f4cb5f36c1b098b06b477c53552e7fcc5d3215171f7c22073afbcd16d8385cb6')
    result = dict(passed=True, cases=checks, CPU_calls=sum(m.calls for _, m in machines),
        exhaustive_raw_WORDs_per_implementation=131072, original_comparison=original is not None,
        original=original_metadata, original_inputs=[str(args.original)] if args.original else [],
        getter_sha256=sha(getter), sources=sources, evidence=evidence,
        units=[dict(entry=hex(at), bytes=len(code), sha256=hashlib.sha256(code).hexdigest()) for at, code in units],
        scope=__doc__+' Actual8-byte getter and86-byte resident dependencies, both BIOS modes, '
        'all65536 raw WORDs per mode, repeated non-consuming observations, empty versus occupiedAX0, '
        'new arrivals, six mouse-queue indices/counts/peek-versus-dequeue read addresses and canaries. '
        'Exact native BX stack value, preserved other registers/IF/DF/DS=SS/SP checked; arithmetic '
        'FLAGS are volatile. INT16 availability/raw keys are explicit model inputs and consuming calls reject. '
        'Original nonzero-count indices outside0..5 are unchecked and intentionally not executed. '
        'No mouse driver/callback production, real BIOS, linked parent RPC/latch, scheduler or full ASPECT claim.')
    (out/'result.json').write_text(json.dumps(result, indent=2)+'\n')
    print('PASS HITKEY', result['CPU_calls'], 'total native getter calls')


if __name__ == '__main__':
    main()
