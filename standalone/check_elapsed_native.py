#!/usr/bin/env python3
"""Recover Elapsed Time's native control flow with explicit UI/clock boundaries."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import struct
import subprocess
from unicorn import Uc, UC_ARCH_X86, UC_MODE_16, UC_HOOK_CODE
from unicorn.x86_const import *

ROOT = Path(__file__).resolve().parents[1]
ENTRY, SIZE, FILE_OFFSET = 0xdb04, 149, 0xf184
EXPECTED = 'ac8abc402f07e3ea9a402bc19c9e95216321800645e716d1eaefd1aa7353243d'
ORIGINAL = '6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--output', type=Path, required=True)
p.add_argument('--original', type=Path)
a = p.parse_args()
out = a.output.resolve()
assert out.is_relative_to(ROOT / 'build')
out.mkdir(parents=True, exist_ok=False)
source = ROOT / 'reconstruction/local_controls/elapsed.asm'
subprocess.run(['nasm', '-fbin', '-DRECON_FLAT', str(source), '-o', str(out / 'elapsed.bin')], check=True)
code = (out / 'elapsed.bin').read_bytes()
assert len(code) == SIZE and hashlib.sha256(code).hexdigest() == EXPECTED
# Also admit relocation-bearing source assembly without any original input.
subprocess.run(['nasm', '-fobj', str(source), '-o', str(out / 'elapsed.obj')], check=True)
if a.original:
    original = a.original.read_bytes()
    assert hashlib.sha256(original).hexdigest() == ORIGINAL
    assert code == original[FILE_OFFSET:FILE_OFFSET + SIZE]
    assert struct.unpack_from('<H', original, 153936 + 0x44e0 + 0x14 * 2)[0] == 0xba1b
    assert original[0xcc1b:0xcc27] == bytes.fromhex('9aec02ec0a0300ea04db0000')
cases = []
for online, loops, key, handle in itertools.product((0, 1, 0xffff), (0, 1, 3, 7), (ord('x'), 27, 0x2d00, 0x4800), ((0x120, 0x4567), (0, 0), (0xffff, 0x8000))):
    u = Uc(UC_ARCH_X86, UC_MODE_16)
    u.mem_map(0, 0x100000)
    u.mem_write(0x10000 + ENTRY, code)
    # All named service bodies are explicit boundaries, not native UI/timer code.
    for address, cleanup in ((0x3fc7, 0), (0x36d4, 0), (0x6bf0, 6), (0xaa5c, 0),
                             (0x37a5, 0), (0x498b, 0), (0x6530, 0), (0x64fe, 0), (0x4015, 0)):
        u.mem_write(0x10000 + address, b'\xc2' + struct.pack('<H', cleanup) if cleanup else b'\xc3')
    for address, value in ((0x1f7c, 0x1e), (0x2ea4, 0x7100), (0x2ea6, 0x7200)):
        u.mem_write(0x50000 + address, struct.pack('<H', value))
    video = bytes((i * 37 + 13) & 255 for i in range(4000))
    u.mem_write(0xb8000, video)
    u.mem_write(0x5dffe, struct.pack('<H', 0xf000))
    u.mem_write(0x5dfd0, b'STACK!')
    for reg, value in ((UC_X86_REG_CS, 0x1000), (UC_X86_REG_DS, 0x5000), (UC_X86_REG_SS, 0x5000),
                       (UC_X86_REG_SP, 0xdffe), (UC_X86_REG_BP, 0xbabe), (UC_X86_REG_SI, 0xcafe)):
        u.reg_write(reg, value)
    events, carriers, prints = [], [], []
    polls = reads = updates = 0
    def observe(u, address, size, unused):
        global polls, reads, updates
        sp = u.reg_read(UC_X86_REG_SP)
        def args(n):return struct.unpack('<' + 'H' * n, u.mem_read(0x50000 + sp + 2, n * 2))
        def ax(value):u.reg_write(UC_X86_REG_AX, value)
        if address == 0x13fc7:
            assert args(1) == (0x3294,)
            assert bytes(u.mem_read(0x5397a, 2)) == b'\x0a\0'
            ax(handle[0]);u.reg_write(UC_X86_REG_DX, handle[1])
            u.mem_write(0xb8000, b'\x20\x70' * 2000)
            events.append('open')
        elif address == 0x136d4:ax(0x7300);events.append('date')
        elif address == 0x16bf0:
            prints.append(args(3));events.append('print')
            u.reg_write(UC_X86_REG_DX, 0xdead)
        elif address == 0x1aa5c:
            value = online if not carriers else (1 if len(carriers) & 1 else 0)
            carriers.append(value);ax(value);events.append('carrier')
        elif address == 0x137a5:updates += 1;events.append('update')
        elif address == 0x1498b:
            assert args(1) == (0,);ax(0x7400);events.append('time')
        elif address == 0x16530:
            ax(int(polls >= loops));polls += 1;events.append('poll')
        elif address == 0x164fe:ax(key);reads += 1;events.append('consume')
        elif address == 0x14015:
            assert args(3) == (0x3294, *handle)
            u.mem_write(0xb8000, video);events.append('close')
        elif address == 0x1f000:u.emu_stop()
    u.hook_add(UC_HOOK_CODE, observe)
    u.emu_start(0x10000 + ENTRY, 0, count=3000)
    assert polls == loops + 1 and reads == 1 and len(carriers) == loops + 1
    assert updates == sum(bool(c) for c in carriers[1:])
    assert prints == [(0x7300, 0x1e, 0x0a2f), (0x7100 if online else 0x7200, 0x1e, 0x0c1b)] + [(0x7400, 0x1e, 0x0a1e), (0x2c7c, 0x1e, 0x0c33)] * loops
    expected_events = ['open', 'date', 'print', 'carrier', 'print', 'poll']
    for c in carriers[1:]:expected_events += ['carrier'] + (['update'] if c else []) + ['time', 'print', 'print', 'poll']
    assert events == expected_events + ['consume', 'close']
    assert u.reg_read(UC_X86_REG_SP) == 0xe000 and u.reg_read(UC_X86_REG_BP) == 0xbabe and u.reg_read(UC_X86_REG_SI) == 0xcafe
    assert u.reg_read(UC_X86_REG_DS) == u.reg_read(UC_X86_REG_SS) == 0x5000
    assert bytes(u.mem_read(0x5dfd0, 6)) == b'STACK!' and bytes(u.mem_read(0xb8000, 4000)) == video
    cases.append(dict(online=online, refresh_iterations=loops, timer_updates=updates, key=key, handle=handle, passed=True))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
result = dict(passed=True, native_bytes=SIZE, native_sha256=EXPECTED, original_compared=a.original is not None,
              cases=cases, sources={str(path.relative_to(ROOT)):sha(path) for path in (source, Path(__file__).resolve())},
              scope=__doc__ + ' Actual 149 control bytes, stack and preserved registers with modeled window/date/time/carrier/poll/print services. Synthetic analysis image is never executed. No linked live command, timer-service equivalence, BBS or physical acceptance.')
(out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
print('PASS original Elapsed Time control:', len(cases), 'boundary-modeled cases')
