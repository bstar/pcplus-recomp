#!/usr/bin/env python3
"""Execute recovered Chat instructions with explicit keyboard/UI/UART boundaries."""
import argparse
import hashlib
import json
import struct
import subprocess
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_16, UC_HOOK_CODE
from unicorn.x86_const import *

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / 'reconstruction/chat'


def execute(code, keys, *, buffered=0, duplex=0, newline=0, rows=25, received=b'', translation=None, helper=None):
    u = Uc(UC_ARCH_X86, UC_MODE_16)
    u.mem_map(0, 0x100000)
    u.mem_write(0x1e828, code)
    def word(at, value):
        u.mem_write(0x50000 + at, struct.pack('<H', value))
    def read(at):
        return struct.unpack('<H', u.mem_read(0x50000 + at, 2))[0]
    def string(at):
        b = bytearray()
        while len(b) < 1024:
            value = bytes(u.mem_read(0x50000 + at + len(b), 1))[0]
            if not value:
                return bytes(b)
            b.append(value)
        raise AssertionError('unterminated source')
    for at, value in ((0x1d76, buffered), (0x1d1a, duplex), (0x3986, newline),
                      (0x7a74, rows), (0x7a84, (rows - 1) << 8), (0x8e20, len(received))):
        word(at, value)
    u.mem_write(0x5d00a, translation or bytes(range(256)))
    u.mem_write(0x57746, b'\n\0')
    queue = list(keys)
    rx = list(received)
    events = []
    if helper is None:
        word(0xf000, 0xf800)
        entry = 0xe828
    else:
        u.mem_write(0x56000, helper + b'\0')
        word(0xf000, 0xf800)
        word(0xf002, 0x6000)
        entry = 0xeaf2
    for reg, value in ((UC_X86_REG_CS, 0x1000), (UC_X86_REG_DS, 0x5000),
                       (UC_X86_REG_SS, 0x5000), (UC_X86_REG_SP, 0xf000),
                       (UC_X86_REG_SI, 0x1234), (UC_X86_REG_DI, 0x5678),
                       (UC_X86_REG_BP, 0x9abc), (UC_X86_REG_EFLAGS, 0x202)):
        u.reg_write(reg, value)
    cleanup = {0x6edc: 8, 0x6bf0: 6, 0x6e78: 2, 0x6e66: 4,
               0x5832: 2, 0xab0b: 2}
    services = {0x3fb0, 0x6edc, 0x6bf0, 0x6e78, 0x6e5a, 0x6e66, 0xaa65,
                0x3d94, 0x5832, 0x9b6, 0x798e, 0x6dca, 0x6530, 0x64fe,
                0xa62, 0xab0b, 0x6b5a, 0xd830, 0x6b42, 0x48cc, 0x1bbe}
    for address in services:
        n = cleanup.get(address, 0)
        u.mem_write(0x10000 + address, b'\xc2' + struct.pack('<H', n) if n else b'\xc3')
    stopped = []
    def hook(u, address, size, _):
        if address == 0x1f800:
            stopped.append(True)
            u.emu_stop()
            return
        address -= 0x10000
        if address not in services:
            return
        sp = u.reg_read(UC_X86_REG_SP)
        arg = read(sp + 2)
        if address in (0x9b6, 0x5832, 0xab0b, 0x48cc):
            events.append((address, arg))
        elif address == 0xa62:
            events.append((address, string(u.reg_read(UC_X86_REG_BX))))
        elif address == 0x3d94:
            events.append((address, arg, read(sp + 4), read(sp + 6)))
        elif address in (0x6b5a, 0xd830, 0x6b42):
            events.append((address,))
        elif address == 0x6530:
            assert queue, 'native Chat is waiting for a key'
            u.reg_write(UC_X86_REG_AX, 1)
        elif address == 0x64fe:
            u.reg_write(UC_X86_REG_AX, queue.pop(0))
        elif address == 0xaa65:
            assert rx
            u.reg_write(UC_X86_REG_AX, rx.pop(0))
            word(0x8e20, len(rx))
        elif address == 0x798e:
            u.reg_write(UC_X86_REG_AX, 0)
    u.hook_add(UC_HOOK_CODE, hook)
    u.emu_start(0x10000 + entry, 0, count=1000000)
    assert stopped and not queue and not rx
    assert u.reg_read(UC_X86_REG_SP) == 0xf002
    for reg, value in ((UC_X86_REG_BP, 0x9abc), (UC_X86_REG_SI, 0x1234),
                       (UC_X86_REG_DI, 0x5678), (UC_X86_REG_DS, 0x5000), (UC_X86_REG_SS, 0x5000)):
        assert u.reg_read(reg) == value
    return events


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--original', type=Path)
    args = p.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT / 'build') and not out.exists()
    out.mkdir()
    binary = out / 'chat.bin'
    source = MODULE / 'chat.asm'
    subprocess.run(['nasm', '-fbin', '-DRECON_FLAT', str(source), '-o', str(binary)], check=True)
    subprocess.run(['nasm', '-fobj', str(source), '-o', str(out / 'chat.obj')], check=True)
    code = binary.read_bytes()
    proof = json.loads((MODULE / 'provenance.json').read_text())
    assert len(code) == 760 and hashlib.sha256(code).hexdigest() == proof['sha256']
    if args.original:
        original = args.original.read_bytes()
        assert hashlib.sha256(original).hexdigest() == proof['original_sha256']
        assert code == original[108424:109184]
    cases = 0
    def run(keys, **kw):
        nonlocal cases
        cases += 1
        return execute(code, keys, **kw)
    def values(events, address):
        return [e[1] for e in events if e[0] == address]
    # Exact signed-byte promotion and the duplex gate in the native helper.
    for duplex in (0, 1, 2, 0xffff):
        for b in range(1, 256):
            e = run([], helper=bytes([b]), duplex=duplex)
            expected = [b if b < 128 else b | 0xff00] if duplex else []
            assert values(e, 0x9b6) == values(e, 0x5832) == expected
        e = run([], helper=b'', duplex=duplex)
        assert not e
    # Immediate versus buffered TX, LF option and echo, including caller cleanup.
    for rows in (25, 28, 29, 43, 50):
        for buffered in (0, 1):
            for duplex in (0, 1):
                for newline in (0, 1):
                    e = run([ord('A'), 13, 27], rows=rows, buffered=buffered, duplex=duplex, newline=newline)
                    if buffered:
                        assert values(e, 0xa62) == [b'A\r']
                        assert values(e, 0xab0b) == ([10] if newline or duplex else [])
                    else:
                        assert values(e, 0xab0b) == [65, 13]
                        assert not values(e, 0xa62)
                    assert values(e, 0x9b6) == values(e, 0x5832) == ([65, 13] + ([10] if buffered else []) if duplex else [])
                    pane = 32 if rows > 28 else 18
                    assert [v[2] for v in e if v[0] == 0x3d94] == [pane + 2] * 2
    for count in (0, 1, 297, 298, 299, 596, 597):
        e = run([65] * count + [27], buffered=1)
        assert values(e, 0xa62) == [b'A' * 298] * (count // 298)
    for keys, expected in (([65, 0xe08, 66, 13, 27], b'B\r'), ([0xe08, 65, 13, 27], b'A\r')):
        e = run(keys, buffered=1)
        assert values(e, 0xa62) == [expected]
    for key in (17, 19):
        e = run([key, 27], buffered=1)
        assert values(e, 0xab0b) == [key] and not values(e, 0xa62)
    e = run([65, 0xe00d, 27], buffered=1)
    assert values(e, 0xa62) == [b'A\r']
    e = run([0x6d00, 65, 27])
    assert [v[0] for v in e if v[0] in (0x6b5a, 0xd830, 0x6b42)] == [0x6b5a, 0xd830, 0x6b42]
    assert values(e, 0xab0b) == [65]
    for index in range(10):
        e = run([0x7800 + index * 256, 27])
        assert values(e, 0x48cc) == [0x3758 + index * 54]
        assert not values(e, 0xab0b)
    for translation in (bytes(range(256)), bytes(256)):
        e = run([27], received=b'\x00A\x80\xff', translation=translation)
        expected = [v for v in (translation[b] for b in b'\x00A\x80\xff') if v]
        assert values(e, 0x9b6) == values(e, 0x5832) == expected
        assert not values(e, 0xab0b)
    report = dict(passed=True, cases=cases, bytes=len(code), sha256=proof['sha256'],
                  original_compared=bool(args.original), sources={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in (source, MODULE / 'provenance.json', Path(__file__))},
                  scope='Actual native760-byte Chat/controller-helper instructions with modeled UI, keyboard, translation ring, TX, logger and history callees. No full callee equivalence, DOS/BBS/live serial, maintained ownership integration or physical acceptance.')
    (out / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
    print('PASS Chat native:', cases, 'cases')


if __name__ == '__main__':
    main()
