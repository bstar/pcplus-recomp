#!/usr/bin/env python3
"""Independent byte-conservation and CRC oracle for the invitation recognizer.
Runs identical vectors against host C and source-built 8086 DOS C. No live
terminal, automatic file creation or BBS interoperability claim.
"""
import binascii
import ctypes as C
import fcntl
import hashlib
import json
import os
from pathlib import Path
import random
import re
import shutil
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/zmodem-autostart'
SRC = ROOT / 'src/transfer'

class State(C.Structure):
    _fields_ = [('count', C.c_uint), ('held', C.c_ubyte * 20)]

def invitation(fields=bytes(4)):
    body = b'\0' + fields
    return b'**\x18B' + (body + binascii.crc_hqx(body, 0).to_bytes(2, 'big')).hex().encode() + b'\r\n'

PATTERN = re.compile(rb'\*\*\x18B00[0-9a-fA-F]{12}\r[\n\x8a]')

def oracle(data):
    released = bytearray()
    events = []
    cursor = 0
    for match in PATTERN.finditer(data):
        decoded = bytes.fromhex(match[0][4:18].decode())
        if decoded[4] != 0 or binascii.crc_hqx(decoded[:5], 0) != int.from_bytes(decoded[5:], 'big'):
            continue
        released.extend(data[cursor:match.start()])
        events.append(match.end() - 1)
        cursor = match.end()
    released.extend(data[cursor:])
    return bytes(released), events

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    lock = (OUT / '.lock').open('w')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    subprocess.run(['gcc', '-std=c89', '-Wall', '-Wextra', '-Werror', '-shared', '-fPIC',
                    str(SRC / 'zmodem_autostart.c'), '-o', str(OUT / 'autostart.so')], check=True)
    lib = C.CDLL(str(OUT / 'autostart.so'))
    lib.za_reset.argtypes = [C.c_void_p]
    lib.za_feed.argtypes = [C.c_void_p, C.c_uint, C.c_void_p, C.c_void_p]
    lib.za_flush.argtypes = [C.c_void_p, C.c_void_p]
    vectors = []
    base = invitation()
    def case(data):
        expected, events = oracle(data)
        state = State()
        lib.za_reset(C.byref(state))
        actual = bytearray()
        found = []
        for i, byte in enumerate(data):
            output = C.create_string_buffer(b'\xa5' * 22, 22)
            count = C.c_uint(999)
            status = lib.za_feed(C.byref(state), byte, C.byref(output, 1), C.byref(count))
            assert status in (0, 1) and count.value <= 20 and state.count < 20
            assert output.raw[0] == 165 and output.raw[1 + count.value:] == b'\xa5' * (21 - count.value)
            actual.extend(output.raw[1:1 + count.value])
            if status == 1:
                found.append(i)
        output = C.create_string_buffer(b'\xa5' * 22, 22)
        count = lib.za_flush(C.byref(state), C.byref(output, 1))
        assert 0 <= count <= 19 and state.count == 0
        assert output.raw[0] == 165 and output.raw[1 + count:] == b'\xa5' * (21 - count)
        actual.extend(output.raw[1:1 + count])
        assert bytes(actual) == expected and found == events, (data, actual, expected, found, events)
        vectors.append(struct.pack('<HHH', len(data), len(expected), len(events)) + data + expected +
                       b''.join(struct.pack('<H', i) for i in events))
    case(b'')
    for i in range(21):
        case(base[:i])
        case(base[:i] + base + b'\x11BBS menu\r\n')
        case(base[:i] + b'?' + base)
    for i in range(20):
        for value in range(256):
            mutated = base[:i] + bytes([value]) + base[i + 1:]
            case(mutated)
    for i in range(256):
        case(invitation(bytes([i, 255 - i, i ^ 85, 0])))
        wire = invitation(bytes([i, 255 - i, i ^ 85, i ^ 170]))
        case(b'BBS\r\n' + b'*' * (i % 23) + wire + b'\x11menu')
        case(wire.upper().replace(b'\n', b'\x8a'))
    for kind in range(1, 256):
        raw = bytes([kind, 0, 0, 0, 0])
        wire = b'**\x18B' + (raw + binascii.crc_hqx(raw, 0).to_bytes(2, 'big')).hex().encode() + b'\r\n'
        case(wire + base)
    case(base * 100)
    case(b'*' * 2048)
    case(bytes(range(256)) * 8)
    rng = random.Random(0x4155544f)
    for _ in range(300):
        parts = [rng.randbytes(rng.randrange(30)), base, base[:-rng.randrange(1, 20)],
                 b'\x18' * 5, b'*' * rng.randrange(30), invitation(rng.randbytes(4))]
        rng.shuffle(parts)
        case(b''.join(parts))
    # Invalid input cannot alter state, output or the caller's release count.
    state = State(); lib.za_reset(C.byref(state))
    output = C.create_string_buffer(b'Z' * 20, 20); count = C.c_uint(777)
    before = bytes(state)
    assert lib.za_feed(C.byref(state), 256, output, C.byref(count)) == 2
    assert bytes(state) == before and output.raw == b'Z' * 20 and count.value == 777
    (OUT / 'VECTORS.BIN').write_bytes(b''.join(vectors))
    sources = [SRC / 'zmodem_autostart.c', SRC / 'zmodem_autostart.h',
               ROOT / 'standalone/zmodem_autostart_host.c', Path(__file__).resolve()]
    args = ['wcl', '-q', '-bt=dos', '-0', '-ms', '-s', '-w4', '-we', '-k8192', '-i=.', '-fe=AUTO.EXE',
            'zmodem_autostart.c', 'zmodem_autostart_host.c']
    for path in sources[:3]:
        shutil.copy2(path, OUT / path.name)
    subprocess.run(args, cwd=OUT, check=True)
    isolated = OUT / 'source-only'; isolated.mkdir(exist_ok=True)
    for path in sources[:3]:
        shutil.copy2(path, isolated / path.name)
    subprocess.run(args, cwd=isolated, check=True)
    assert (OUT / 'AUTO.EXE').read_bytes() == (isolated / 'AUTO.EXE').read_bytes()
    for name in ('PASS.TXT', 'FAIL.TXT', 'RESULT.TXT'):
        (OUT / name).unlink(missing_ok=True)
    config = f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
cycles=max
[mixer]
nosound=true
[autoexec]
@echo off
mount c "{OUT}"
c:
AUTO >RESULT.TXT
if errorlevel 1 goto fail
echo PASS>PASS.TXT
goto done
:fail
echo FAIL>FAIL.TXT
:done
exit
'''
    (OUT / 'dosbox.conf').write_text(config)
    with (OUT / 'dosbox.log').open('w') as log:
        subprocess.run(['dosbox-x', '-fastlaunch', '-nogui', '-conf', str(OUT / 'dosbox.conf')],
                       env=dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy'),
                       stdout=log, stderr=log, timeout=60, check=True)
    summary = (OUT / 'RESULT.TXT').read_text().strip()
    assert (OUT / 'PASS.TXT').exists() and not (OUT / 'FAIL.TXT').exists(), summary
    result = dict(passed=True, vectors=len(vectors), DOS_summary=summary,
                  isolated_source_build_byte_identical=True,
                  vectors_sha256=hashlib.sha256((OUT / 'VECTORS.BIN').read_bytes()).hexdigest(),
                  binary_sha256=hashlib.sha256((OUT / 'AUTO.EXE').read_bytes()).hexdigest(),
                  sources={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
                  scope='Canonical hex ZRQINIT recognizer only; host and actual 8086 DOS byte conservation, CRC and bounded output. Not integrated with terminal, settings, file owners or BBS sessions.')
    (OUT / 'checks.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
