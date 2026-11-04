#!/usr/bin/env python3
"""Execute original call-timer instructions; DOS time and C library calls modeled."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import struct
import subprocess
import time
from unicorn import Uc, UC_ARCH_X86, UC_MODE_16, UC_HOOK_CODE
from unicorn.x86_const import *

ROOT = Path(__file__).resolve().parents[1]
UNITS = [('start', 0x3f61, 18, 'd5e45c8167791b38c96f5b7607f84ec53e1c0a7126c898a473cb6e050d8687df'),
         ('seconds', 0x3f73, 41, '6b5c5458529eff6cddc91a1f791184083e5eb8a7345467e45ff2e13e8ce13b5f'),
         ('update', 0x37a5, 161, '095bab1e4378dc54a6c09f2bb59c6d6e5b28867faa842a1ee1c0ce5c9b010970')]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--output', type=Path, required=True)
p.add_argument('--original', type=Path)
a = p.parse_args()
out = a.output.resolve();assert out.is_relative_to(ROOT / 'build')
out.mkdir(parents=True, exist_ok=False)
original = a.original.read_bytes() if a.original else None
if original:assert hashlib.sha256(original).hexdigest() == '6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
sources = [Path(__file__).resolve(), ROOT / 'reconstruction/uart/encodings.inc']
codes = {}
for name, entry, size, digest in UNITS:
    source = ROOT / f'reconstruction/local_controls/timer_{name}.asm';sources.append(source)
    for fmt, suffix, options in [('bin', 'bin', ['-DRECON_FLAT']), ('obj', 'obj', [])]:
        subprocess.run(['nasm', '-f'+fmt, '-I'+str(ROOT/'reconstruction/uart')+'/', *options,
                        str(source), '-o', str(out/(name+'.'+suffix))], check=True)
    code = (out/(name+'.bin')).read_bytes()
    assert len(code) == size and hashlib.sha256(code).hexdigest() == digest
    if original:assert code == original[0x1200+entry:0x1200+entry+size]
    codes[entry] = code

class Timer:
    def __init__(self):
        self.u = u = Uc(UC_ARCH_X86, UC_MODE_16)
        u.mem_map(0, 0x100000)
        for entry, code in codes.items():u.mem_write(0x10000+entry, code)
        for address, cleanup in [(0x778c, 2), (0x8d48, 8), (0x8da8, 8), (0x82b6, 0)]:
            u.mem_write(0x10000+address, b'\xc2'+struct.pack('<H', cleanup) if cleanup else b'\xc3')
        u.mem_write(0x5473b, b'%2.2d:%2.2d:%2.2d\0')
        u.hook_add(UC_HOOK_CODE, self.observe)
    def observe(self, u, address, size, unused):
        sp = u.reg_read(UC_X86_REG_SP)
        if address == 0x1778c:
            pointer = struct.unpack('<H', u.mem_read(0x50000+sp+2, 2))[0]
            seconds, hundredths = self.readings[self.read_at];self.read_at += 1
            words = (hundredths, seconds//3600, seconds//60%60, seconds%60)
            u.mem_write(0x50000+pointer, struct.pack('<4H', *words));self.events.append(('time', pointer, *words))
        elif address in (0x18d48, 0x18da8):
            dividend, divisor = struct.unpack('<II', u.mem_read(0x50000+sp+2, 8))
            assert 0 <= dividend < 86400 and divisor in (60, 3600)
            value = dividend//divisor if address == 0x18d48 else dividend%divisor
            u.reg_write(UC_X86_REG_AX, value&65535);u.reg_write(UC_X86_REG_DX, value>>16)
            self.events.append(('divide' if address == 0x18d48 else 'remainder', dividend, divisor))
        elif address == 0x182b6:
            dest, fmt, h, m, s = struct.unpack('<5H', u.mem_read(0x50000+sp+2, 10))
            assert dest == 0x2c7c and fmt == 0x473b
            self.formatted = f'{h:02d}:{m:02d}:{s:02d}'
            u.mem_write(0x50000+dest, self.formatted.encode()+b'\0')
            self.events.append(('format', h, m, s))
        elif address == 0x1f000:self.finished = True;u.emu_stop()
    def call(self, entry, readings):
        self.readings = readings;self.read_at = 0;self.events = [];self.formatted = None;self.finished = False
        u = self.u
        u.mem_write(0x5dffe, struct.pack('<H', 0xf000));u.mem_write(0x5dfb0, b'STACK!')
        for reg, value in [(UC_X86_REG_CS, 0x1000), (UC_X86_REG_DS, 0x5000), (UC_X86_REG_SS, 0x5000),
                           (UC_X86_REG_SP, 0xdffe), (UC_X86_REG_BP, 0xbabe), (UC_X86_REG_SI, 0xcafe), (UC_X86_REG_DI, 0x1234)]:u.reg_write(reg, value)
        u.emu_start(0x10000+entry, 0, count=1000)
        assert self.finished and self.read_at == len(readings)
        assert u.reg_read(UC_X86_REG_SP) == 0xe000 and u.reg_read(UC_X86_REG_BP) == 0xbabe
        assert u.reg_read(UC_X86_REG_DS) == u.reg_read(UC_X86_REG_SS) == 0x5000
        assert u.reg_read(UC_X86_REG_SI) == 0xcafe and u.reg_read(UC_X86_REG_DI) == 0x1234
        assert bytes(u.mem_read(0x5dfb0, 6)) == b'STACK!'
        return u.reg_read(UC_X86_REG_AX) | u.reg_read(UC_X86_REG_DX)<<16
    def anchor(self):return struct.unpack('<I', self.u.mem_read(0x5cd8e, 4))[0]

clock = Timer();start_time = time.monotonic();coverage = hashlib.sha256()
# Every legal time of day, including signed-low-word and 16-bit carry boundaries.
for second in range(86400):
    assert clock.call(0x3f73, [(second, second%100)]) == second
    assert len(clock.events) == 1
    coverage.update(struct.pack('<I', second))
print('PASS seconds conversion: all86400 legal times', flush=True)
anchors = [(0,0), (0,1), (59,60), (3599,3600), (65535,65536), (86399,0), (86399,86399)]
start_cases = 0
for first, second in anchors:
    for hundredths in (0, 99):
        clock.call(0x3f61, [(first, hundredths), (second, 1)])
        assert clock.anchor() == second and len(clock.events) == 2
        assert clock.events[0][1] == 0xcff2 and clock.events[1][1] != 0xcff2
        assert struct.unpack('<4H', clock.u.mem_read(0x5cff2, 8)) == (hundredths, first//3600, first//60%60, first%60)
        start_cases += 1
print('PASS separate stamp/start reads:', start_cases, flush=True)
boundary = [0,1,59,60,61,3599,3600,3601,32767,32768,65535,65536,65537,82799,82800,82801,86398,86399]
pairs = [(s,n) for s in boundary for n in boundary]
rng = random.Random(0x201)
pairs += [(rng.randrange(86400), rng.randrange(86400)) for _ in range(1024)]
pairs += [(86399, (86399+duration)%86400) for duration in range(0,86400,60)]
for first, second in pairs:
    clock.u.mem_write(0x5cd8e, struct.pack('<I', first))
    clock.u.mem_write(0x52c7c, b'XXXXXXXX\0');clock.u.mem_write(0x5cfec, b'\xff'*6)
    clock.call(0x37a5, [(second,99)])
    elapsed = (second-first)%86400
    expected = (elapsed//3600, elapsed//60%60, elapsed%60)
    assert struct.unpack('<3H', clock.u.mem_read(0x5cfec,6)) == expected
    assert clock.anchor() == first and clock.formatted == '%02d:%02d:%02d'%expected
    assert clock.events[1:] == [('divide',elapsed,3600), ('remainder',elapsed,3600),
                               ('divide',elapsed%3600,60), ('remainder',elapsed%3600,60), ('format',*expected)]
    coverage.update(struct.pack('<III', first, second, elapsed))
print('PASS elapsed/update boundaries:',len(pairs),flush=True)
# A new call resets the anchor; an update never does. No log enable/file service exists here.
clock.call(0x3f61, [(86395,0),(86395,1)])
clock.call(0x37a5, [(3,0)]);assert clock.formatted == '00:00:08'
clock.call(0x3f61, [(10,0),(10,1)])
clock.call(0x37a5, [(12,0)]);assert clock.formatted == '00:00:02' and clock.anchor() == 10
result = dict(passed=True, original_compared=original is not None, native_bytes=sum(row[2] for row in UNITS),
              cases=dict(seconds_conversion=86400,start_read_boundaries=start_cases,elapsed_update=len(pairs),start_update_reconnect_sequences=1),
              coverage_sha256=coverage.hexdigest(),seconds=round(time.monotonic()-start_time,3),
              sources={str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest() for path in sources},
              units=[dict(name=n,entry=hex(e),bytes=s,sha256=h) for n,e,s,h in UNITS],
              scope=__doc__+' Exact220 native bytes; all legal day times, one-day wrap, long arithmetic arguments, formatting arguments and stack/data ABI. DOS gettime, C long divide/remainder and sprintf are modeled. No live terminal binding, multi-day clock reconstruction, physical/DOS/BBS acceptance or application change.')
(out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
print('PASS native call timer:',json.dumps(result['cases']),flush=True)
