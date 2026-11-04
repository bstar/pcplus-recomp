#!/usr/bin/env python3
"""Execute the recovered pause body; its seven BIOS/UART/UI services are modeled."""
import argparse
import hashlib
import itertools
import json
import struct
import subprocess
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_16, UC_HOOK_CODE
from unicorn.x86_const import *

ROOT = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--output', type=Path, required=True)
p.add_argument('--original', type=Path)
a = p.parse_args()
a.output = a.output.resolve()
assert a.output.is_relative_to(ROOT / 'build')
a.output.mkdir(parents=True, exist_ok=False)
source = ROOT / 'reconstruction/local_controls/pause.asm'
binary = a.output / 'pause.bin'
subprocess.run(['nasm', '-fbin', '-DRECON_FLAT', str(source), '-o', str(binary)], check=True)
code = binary.read_bytes()
assert len(code) == 74 and hashlib.sha256(code).hexdigest() == '0f17a638de509720dd35dee87e26fadfd7eacd7bbf8846e8e54b2c528363c60e'
if a.original:
    original = a.original.read_bytes()
    assert hashlib.sha256(original).hexdigest() == '6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
    assert code == original[0xf3fe:0xf448]
cases = []
for count, row, key, seed in itertools.product((0, 1, 15, 80, 132), (0, 160, 320), (ord('x'), 27, 0x2d00, 0x4800), (7, 193)):
    u = Uc(UC_ARCH_X86, UC_MODE_16)
    u.mem_map(0, 0x100000)
    u.mem_write(0x1dd7e, code)
    for address, cleanup in ((0xab0b, 2), (0x6e5a, 0), (0x765c, 6), (0x3226, 0), (0x64fe, 0), (0x7682, 6), (0x6dca, 0)):
        u.mem_write(0x10000 + address, b'\xc2' + struct.pack('<H', cleanup) if cleanup else b'\xc3')
    video = bytes((i * 37 + seed) & 255 for i in range(4000))
    u.mem_write(0xb8000, video)
    u.mem_write(0x57a72, struct.pack('<H', count))
    u.mem_write(0x57a82, struct.pack('<H', row))
    u.mem_write(0x52eb4, struct.pack('<H', 0x1989))
    u.mem_write(0x5dffe, struct.pack('<H', 0xf000))
    u.mem_write(0x5dec0, b'GUARD!')
    for reg, value in ((UC_X86_REG_CS, 0x1000), (UC_X86_REG_DS, 0x5000), (UC_X86_REG_SS, 0x5000),
                       (UC_X86_REG_SP, 0xdffe), (UC_X86_REG_BP, 0xbabe)):
        u.reg_write(reg, value)
    events = []
    def observe(u, address, size, unused):
        sp = u.reg_read(UC_X86_REG_SP)
        args = lambda n: struct.unpack('<' + 'H' * n, u.mem_read(0x50000 + sp + 2, 2 * n))
        if address == 0x1ab0b:
            events.append(('send', args(1)[0]))
        elif address == 0x16e5a:
            events.append(('hide',))
        elif address in (0x1765c, 0x17682):
            n, start, pointer = args(3)
            assert (n, start, pointer) == (count, row, 0xdffe - 2 - 0x108)
            if address == 0x1765c:
                u.mem_write(0x50000 + pointer, video[start:start + n * 2])
                events.append(('save',))
            else:
                u.mem_write(0xb8000 + start, bytes(u.mem_read(0x50000 + pointer, n * 2)))
                events.append(('restore',))
        elif address == 0x13226:
            assert args(1)[0] == 0x1989
            u.mem_write(0xb8000 + row, b'\x20\x70' * count)
            events.append(('message',))
        elif address == 0x164fe:
            u.reg_write(UC_X86_REG_AX, key)
            events.append(('read-one-key', key))
        elif address == 0x16dca:
            events.append(('show',))
        elif address == 0x1f000:
            u.emu_stop()
    u.hook_add(UC_HOOK_CODE, observe)
    u.emu_start(0x1dd7e, 0, count=100)
    assert events == [('send', 19), ('hide',), ('save',), ('message',), ('read-one-key', key), ('restore',), ('show',), ('send', 17)]
    assert bytes(u.mem_read(0xb8000, 4000)) == video
    assert bytes(u.mem_read(0x5dec0, 6)) == b'GUARD!'
    assert u.reg_read(UC_X86_REG_SP) == 0xe000 and u.reg_read(UC_X86_REG_BP) == 0xbabe
    assert u.reg_read(UC_X86_REG_DS) == u.reg_read(UC_X86_REG_SS) == 0x5000
    cases.append(dict(cells=count, start=row, key=key, seed=seed, passed=True))
report = dict(passed=True, bytes=len(code), sha256=hashlib.sha256(code).hexdigest(), original_compared=bool(a.original),
              cases=cases, sources={str(f.relative_to(ROOT)): hashlib.sha256(f.read_bytes()).hexdigest() for f in (source, Path(__file__))},
              scope=__doc__ + ' Checks body ordering, native stack cleanup and selected cell region only; not native helper equivalence, live integration or hardware acceptance.')
(a.output / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
print('PASS recovered pause:', len(cases), 'boundary-modeled CPU cases')
