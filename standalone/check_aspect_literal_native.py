#!/usr/bin/env python3
"""Optional private CPU oracle for original ASPCOMP 1.01 literal emission.

Executes original functions22A9/2230/2413/698E unmodified in Unicorn16.
Only CRT strlen/fputc/fwrite are intercepted. No DOS, BIOS or file I/O executes.
This is isolated function evidence, not a complete compiler/VM execution.
"""
import argparse
import ctypes
import hashlib
import json
import random
import struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_16, UC_HOOK_CODE, UC_HOOK_INTR
from unicorn.x86_const import (UC_X86_REG_CS, UC_X86_REG_DS, UC_X86_REG_SS,
    UC_X86_REG_ES, UC_X86_REG_IP, UC_X86_REG_SP, UC_X86_REG_BP,
    UC_X86_REG_SI, UC_X86_REG_DI, UC_X86_REG_AX)

ROOT = Path(__file__).resolve().parents[1]
SHA = '5664fdfae375774da5303cc8b53c00ef773a6650132de73c7206e46ddc05039a'
RANGES = [(0x22a9, 0x2380), (0x2230, 0x2267), (0x2413, 0x2444), (0x698e, 0x69f8)]
CRT = {0x6510: 'strlen', 0x6486: 'fputc', 0x637c: 'fwrite'}
CS, DS, STOP, STACK = 0x1000, 0x3000, 0xf000, 0xef00


def sha(data):
    return hashlib.sha256(data).hexdigest()


def original_emit(code, table, text, position, line, output_pass=1):
    u = Uc(UC_ARCH_X86, UC_MODE_16)
    u.mem_map(0, 0x100000)
    u.mem_write(CS*16, code)
    for reg, value in [(UC_X86_REG_CS, CS), (UC_X86_REG_DS, DS),
                       (UC_X86_REG_SS, DS), (UC_X86_REG_ES, DS),
                       (UC_X86_REG_SP, STACK), (UC_X86_REG_BP, 0xabba),
                       (UC_X86_REG_SI, 0x1234), (UC_X86_REG_DI, 0x5678)]:
        u.reg_write(reg, value)
    def put(offset, value, fmt):
        u.mem_write(DS*16+offset, struct.pack(fmt, value))
    def word(offset):
        return struct.unpack('<H', u.mem_read(DS*16+offset, 2))[0]
    put(0x08c2, output_pass, '<H')
    put(0x6444, position, '<I')
    put(0x08d2, line, '<I')
    put(0x08b2, 0x2000, '<H')
    u.mem_write(DS*16+0x41fc, table)
    u.mem_write(DS*16+0x1000, text+b'\0')
    u.mem_write(DS*16+STACK, struct.pack('<HH', STOP, 0x1000))
    output = bytearray()
    calls = {'strlen': 0, 'fputc': 0, 'fwrite': 0}
    entries = {f'{a:04x}': 0 for a, _ in RANGES}
    reached = False
    def on_code(cpu, address, size, _):
        nonlocal reached
        assert cpu.reg_read(UC_X86_REG_CS) == CS, 'Unexpected code segment'
        ip = address-CS*16
        if ip == STOP:
            reached = True
            cpu.emu_stop()
            return
        if f'{ip:04x}' in entries:
            entries[f'{ip:04x}'] += 1
        if ip in CRT:
            name = CRT[ip]
            calls[name] += 1
            sp = cpu.reg_read(UC_X86_REG_SP)
            args = [word(sp+i) for i in [2, 4, 6, 8]]
            if name == 'strlen':
                assert args[0] == 0x1000
                value = 0
                while cpu.mem_read(DS*16+args[0]+value, 1) != b'\0':
                    value += 1
                    assert value <= 80
            elif name == 'fputc':
                assert args[1] == 0x2000
                value = args[0] & 255
                output.append(value)
            else:
                pointer, size_, count, file_ = args
                assert pointer == 0x1000 and size_ == len(text) and count == 1 and file_ == 0x2000
                output.extend(cpu.mem_read(DS*16+pointer, size_*count))
                value = count
            cpu.reg_write(UC_X86_REG_AX, value)
            cpu.reg_write(UC_X86_REG_IP, word(sp))
            cpu.reg_write(UC_X86_REG_SP, sp+2)
            return
        assert any(a <= ip < b for a, b in RANGES), f'Unexpected native code {ip:04x}'
    def interrupt(cpu, number, _):
        raise AssertionError(f'Unexpected native interrupt {number}')
    u.hook_add(UC_HOOK_CODE, on_code)
    u.hook_add(UC_HOOK_INTR, interrupt)
    u.emu_start(CS*16+0x22a9, 0, count=50000)
    assert reached and u.reg_read(UC_X86_REG_SP) == STACK+4
    assert u.reg_read(UC_X86_REG_BP) == 0xabba
    assert u.reg_read(UC_X86_REG_SI) == 0x1234 and u.reg_read(UC_X86_REG_DI) == 0x5678
    assert u.reg_read(UC_X86_REG_DS) == u.reg_read(UC_X86_REG_SS) == DS
    for start, end in RANGES:
        assert u.mem_read(CS*16+start, end-start) == code[start:end]
    counter = struct.unpack('<I', u.mem_read(DS*16+0x6444, 4))[0]
    assert counter == (position+len(text)+2)&0xffffffff
    assert calls == dict(strlen=1, fputc=2 if output_pass else 0, fwrite=1 if output_pass else 0)
    if not output_pass:
        assert u.mem_read(DS*16+0x1000, len(text)) == text
    assert entries == {'22a9': 1, '2230': 2 if output_pass else 0,
                       '2413': 1 if output_pass else 0, '698e': 1 if output_pass else 0}
    return bytes(output), counter, calls, entries


class Result(ctypes.Structure):
    _fields_ = [('text_length', ctypes.c_uint), ('wire_length', ctypes.c_uint), ('stride', ctypes.c_uint)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler', type=Path, default=ROOT/'analysis/pcplus-install/ASPCOMP.EXE')
    parser.add_argument('--host-lib', type=Path, default=ROOT/'build/aspect-literal/literal.so')
    parser.add_argument('--require-host', action='store_true')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--random-cases', type=int, default=512)
    args = parser.parse_args()
    assert 0 <= args.random_cases <= 10000
    out = args.output.resolve()
    assert out.parent == ROOT/'analysis/aspect-compiler' and out.name.startswith('native-')
    original = args.compiler.read_bytes()
    assert sha(original) == SHA and not args.compiler.name.lower().endswith('.analysis.exe')
    code, table = original[0x600:], original[0x1057c:0x10589]
    fixtures = ROOT/'standalone/fixtures/aspect_literal_vectors.json'
    fixture_data = json.loads(fixtures.read_text())
    assert fixture_data['compiler_sha256'] == SHA
    library = None
    if args.host_lib.exists():
        library = ctypes.CDLL(str(args.host_lib.resolve()))
        library.aspect_literal_encode.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint32,
            ctypes.c_uint32, ctypes.c_void_p, ctypes.c_uint, ctypes.POINTER(Result)]
        library.aspect_literal_encode.restype = ctypes.c_uint
    assert library or not args.require_host, 'Host C codec missing'
    cases = [(f"corpus-{v['case']}-{v['index']}", bytes.fromhex(v['text_hex']),
              v['payload_offset'], v['source_line'], bytes.fromhex(v['wire_hex'])) for v in fixture_data['vectors']]
    boundaries = [0, 1, 2, 0xfffe, 0xffff, 0x10000, 0x10001, 0x7ffffffe,
                  0x7fffffff, 0x80000000, 0x80000001, 0xfffffffe, 0xffffffff]
    for position in boundaries:
        for line in boundaries:
            cases.append((f'boundary-{position:08x}-{line:08x}', b'High\x80\xff^M', position, line, None))
    rng = random.Random(0xa5c01)
    for i in range(args.random_cases):
        text = bytes(rng.randrange(1, 256) for _ in range(rng.randrange(1, 81)))
        cases.append((f'random-{i}', text, rng.randrange(1<<32), rng.randrange(1<<32), None))
    records = []
    for name, text, position, line, expected in cases:
        wire, counter, calls, entries = original_emit(code, table, text, position, line)
        if expected is not None:
            assert wire == expected, name
        comparison = None
        if library:
            source = ctypes.create_string_buffer(text)
            target = ctypes.create_string_buffer(82)
            result = Result()
            assert library.aspect_literal_encode(source, len(text), position, line, target, 82, ctypes.byref(result)) == 0, name
            comparison = bytes(target.raw[:result.wire_length])
            assert comparison == wire, name
            assert result.text_length == len(text) and result.wire_length == len(text)+2
        else:
            # Deliberately labeled fallback; fixture contexts independently anchor
            # behavior, random contexts compare only this Python reconstruction.
            stride = ((position+line)&0xffffffff)%12+1
            parity = position&1
            deltas = [(-x if (i+parity)&1 else x) for i, x in enumerate(table)]
            comparison = bytes([(table[0]+len(text))&255, (parity<<7)|(stride+len(text))] +
                [(x+deltas[((i+1)*stride)%13])&255 for i, x in enumerate(text)])
            assert comparison == wire, name
        records.append(dict(name=name, text_hex=text.hex(), position=position, source_line=line,
                            wire_hex=wire.hex(), final_counter=counter, calls=calls, native_entries=entries))
    # Pass1 must count n+2 without transforming input or invoking output CRT.
    for position in boundaries:
        for length in [1, 2, 79, 80]:
            wire, _, _, _ = original_emit(code, table, b'A'*length, position, 0xffffffff, output_pass=0)
            assert not wire
    out.mkdir(parents=True, exist_ok=False)
    report = dict(passed=True, cases=len(records), corpus_vectors=len(fixture_data['vectors']),
        boundary_cases=len(boundaries)**2, random_cases=args.random_cases, pass1_cases=len(boundaries)*4,
        compiler_sha256=SHA, harness_sha256=sha(Path(__file__).read_bytes()),
        fixture_sha256=sha(fixtures.read_bytes()), comparison='maintained host C codec' if library else 'Python formula fallback',
        host_library_sha256=sha(args.host_lib.read_bytes()) if library else None,
        native_ranges=[dict(start=f'{a:04x}', end=f'{b:04x}', sha256=sha(code[a:b])) for a, b in RANGES],
        crt_hooks=CRT, records=records,
        scope='Original isolated compiler emitter and unsigned remainder execute unmodified; CRT buffer IO simulated; no DOS interrupts, source parsing, complete compiler, or application VM exercised.')
    (out/'result.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ('records', 'native_ranges')}, indent=2))


if __name__ == '__main__':
    main()
