#!/usr/bin/env python3
"""Independent datetime/native-layout oracle for maintained call-log formatting."""
import ctypes as C
import datetime as D
import hashlib
import json
from pathlib import Path
import random
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/phone-log-format'


class Stamp(C.Structure):
    _fields_ = [(name, C.c_uint) for name in ['year', 'month', 'day', 'hour', 'minute', 'second']]


def stamp(value):
    return Stamp(value.year, value.month, value.day, value.hour, value.minute, value.second)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    source = ROOT / 'src/directory/phone_log_format.c'
    model = ROOT / 'standalone/phone_log_clock_model.c'
    library = OUT / 'format.so'
    subprocess.run(['cc', '-shared', '-fPIC', '-std=c99', '-O2', '-Wall', '-Wextra', '-Werror',
                    '-Wno-misleading-indentation', '-DPHONE_LOG_HOST', '-D__cdecl=',
                    str(source), str(model), '-o', str(library)], check=True)
    lib = C.CDLL(str(library))
    seconds = lib.phone_log_stamp_seconds
    seconds.argtypes = [C.POINTER(Stamp), C.POINTER(C.c_ulong)]
    start = lib.phone_log_format_start
    start.argtypes = [C.c_char_p, C.c_char_p, C.POINTER(Stamp), C.c_void_p, C.c_uint, C.POINTER(C.c_uint)]
    end = lib.phone_log_format_end
    end.argtypes = [C.POINTER(Stamp), C.POINTER(Stamp), C.c_void_p, C.c_uint, C.POINTER(C.c_uint)]
    read_clock = lib.phone_log_read_stamp
    read_clock.argtypes = [C.POINTER(Stamp)]
    decode = lib.phone_log_decode_enabled
    decode.argtypes = [C.c_void_p, C.c_uint, C.POINTER(C.c_uint)]
    count = 0
    epoch = D.datetime(1980, 1, 1)
    days = (D.datetime(2100, 1, 1) - epoch).days
    for day in range(days):
        value = epoch + D.timedelta(days=day, seconds=(day * 379) % 86400)
        s, result = stamp(value), C.c_ulong(0xdeadbeef)
        assert seconds(C.byref(s), C.byref(result)) == 0
        assert result.value == int((value - epoch).total_seconds())
        count += 1
    value = D.datetime(2026, 10, 24, 12, 34, 56)
    s = stamp(value)
    for names in range(64):
        for numbers in range(64):
            name = bytes([219]) * names
            number = b'N' * numbers
            output, length = C.create_string_buffer(132), C.c_uint(999)
            assert start(name, number, C.byref(s), output, 132, C.byref(length)) == 0
            expected = b'\r\n' + name[:22].ljust(22) + b' ' + number.rjust(20) + b' 10/24/26 12:34:56 '
            assert output.value == expected and length.value == len(expected)
            old = bytes(output)
            assert start(name, number, C.byref(s), output, len(expected), C.byref(length)) == 1
            assert bytes(output) == old and length.value == len(expected)
            count += 2
    rng = random.Random(201)
    maximum = int((D.datetime(2099, 12, 31, 23, 59, 59) - epoch).total_seconds())
    pairs = [(0, maximum), (0, 0), (86399, 86400), (630719999, 630720005)]
    pairs += [tuple(sorted([rng.randrange(maximum + 1), rng.randrange(maximum + 1)])) for _ in range(1024)]
    for first, last in pairs:
        a, b = epoch + D.timedelta(seconds=first), epoch + D.timedelta(seconds=last)
        left, right = stamp(a), stamp(b)
        output, length = C.create_string_buffer(132), C.c_uint(999)
        assert end(C.byref(left), C.byref(right), output, 132, C.byref(length)) == 0
        duration = last - first
        expected = f'{b:%H:%M:%S} {duration // 3600:02}:{duration // 60 % 60:02}:{duration % 60:02}'.encode()
        assert output.value == expected and length.value == len(expected)
        if first != last:
            old = bytes(output)
            assert end(C.byref(right), C.byref(left), output, 132, C.byref(length)) == 2
            assert bytes(output) == old
        count += 1
    for scenario in range(4):
        lib.phone_clock_model(scenario)
        out = Stamp(7, 7, 7, 7, 7, 7)
        old = bytes(out)
        assert read_clock(C.byref(out)) == (2 if scenario in (2, 3) else 0)
        if scenario in (2, 3):
            assert bytes(out) == old
        else:
            assert bytes(out) == bytes(Stamp(2000, 1, 1, 0, 0, 5))
        assert lib.phone_clock_dates() == (4 if scenario == 1 else 6 if scenario == 2 else 2)
        count += 1
    for raw in [0, 1, 256, 65535]:
        image = bytearray((i * 37) & 255 for i in range(1264))
        image[0x1e6:0x1e8] = raw.to_bytes(2, 'little')
        buffer = C.create_string_buffer(bytes(image))
        out = C.c_uint(999)
        assert decode(buffer, 1264, C.byref(out)) == 0 and out.value == bool(raw)
        assert buffer.raw[:-1] == image
        out.value = 999
        assert decode(buffer, 1263, C.byref(out)) == 1 and out.value == 999
        count += 2
    for invalid in [Stamp(1979, 1, 1, 0, 0, 0), Stamp(2100, 1, 1, 0, 0, 0),
                    Stamp(2026, 2, 29, 0, 0, 0), Stamp(2000, 2, 30, 0, 0, 0),
                    Stamp(2000, 0, 1, 0, 0, 0), Stamp(2000, 1, 0, 0, 0, 0),
                    Stamp(2000, 1, 1, 24, 0, 0), Stamp(2000, 1, 1, 0, 60, 0), Stamp(2000, 1, 1, 0, 0, 60)]:
        out = C.c_ulong(123)
        assert seconds(C.byref(invalid), C.byref(out)) == 2 and out.value == 123
        count += 1
    names = ['src/directory/phone_log_format.c', 'src/directory/phone_log_format.h',
             'src/directory/phone_log_clock.h', 'src/config/prm_dos.h',
             'standalone/check_phone_log_format.py', 'standalone/phone_log_clock_model.c']
    report = dict(passed=True, inputs=count, calendar_days=days,
                  sources={name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in names},
                  scope='Actual maintained formatter compiled for host, independent Python datetime/layout oracle; explicit clock model. Native8086/far queue and application integration remain separate.')
    (OUT / 'checks.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Passed', count, 'format/calendar/preference inputs across', days, 'calendar days')


if __name__ == '__main__':
    main()
