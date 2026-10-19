#!/usr/bin/env python3
"""Execute native frontends with recorded external executor/operand boundaries."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from unicorn import Uc, UC_ARCH_X86, UC_MODE_16, UC_HOOK_CODE
from unicorn.x86_const import *
from build_aspect_external import ROOT, OUT, sha

DATA = 0x30000
WHITESPACE = {9, 10, 11, 12, 13, 32}


class Machine:
    def __init__(self, original=None):
        self.u = Uc(UC_ARCH_X86, UC_MODE_16)
        self.u.mem_map(0, 0x100000)
        manifest = json.loads((OUT / 'manifest.json').read_text())
        self.units = manifest['units'] + manifest['reused']
        for unit in self.units:
            code = original[unit['file_start']:unit['file_start'] + unit['bytes']] if original else (ROOT / unit['output']).read_bytes()
            assert hashlib.sha256(code).hexdigest() == unit['sha256']
            self.u.mem_write(0x10000 + unit['start'], code)
        self.u.hook_add(UC_HOOK_CODE, self.hook)

    def word(self, at):
        return int.from_bytes(self.u.mem_read(DATA + at, 2), 'little')

    def string(self, at):
        return bytes(self.u.mem_read(DATA + at, 256)).split(b'\0', 1)[0]

    def ret(self, value=0):
        sp = self.u.reg_read(UC_X86_REG_SP)
        self.u.reg_write(UC_X86_REG_AX, value & 65535)
        self.u.reg_write(UC_X86_REG_IP, self.word(sp))
        self.u.reg_write(UC_X86_REG_SP, sp + 2)

    def hook(self, u, address, size, data):
        self.seen.add(address)
        if address == 0x1f800:
            self.returned = True
            u.emu_stop()
            return
        if any(0x10000 + x['start'] <= address < 0x10000 + x['end'] for x in self.units):
            return
        fn = address - 0x10000
        sp = u.reg_read(UC_X86_REG_SP)
        arg = lambda index: self.word(sp + index * 2)
        if fn == 0xdf04:
            self.reads.append('string')
            self.ret(0x5200)
        elif fn == 0xe0e4:
            self.reads.append('optional')
            self.ret(self.option is not None)
        elif fn == 0x4cb4:
            assert self.option is not None
            self.reads.append('option')
            self.ret(self.option)
        elif fn == 0x8e12:
            assert self.string(arg(1)) == b'COMSPEC'
            self.reads.append('COMSPEC')
            self.ret(0x5600 if self.comspec is not None else 0)
        elif fn == 0x433d:
            program, tail = arg(1), arg(2)
            self.calls.append((None if not program else self.string(program),
                               None if not tail else self.string(tail), arg(3), arg(4), arg(5)))
            self.ret(self.status)
        else:
            raise AssertionError(('unexpected boundary', hex(address)))

    def run(self, kind, text=b'CHILD ARG', option=None, status=0, comspec=b'C:\\COMMAND.COM'):
        self.option, self.status, self.comspec = option, status, comspec
        self.reads, self.calls, self.seen, self.returned = [], [], set(), False
        before = bytearray((i * 37 + 11) & 255 for i in range(65536))
        before[0xd124:0xd126] = b'\xcd\xab'
        before[0x318c:0x3194] = b'COMSPEC\0'
        before[0x7caf:0x7daf] = bytes(8 if i in WHITESPACE else 0 for i in range(256))
        before[0x5200:0x5200 + len(text) + 1] = text + b'\0'
        if comspec is not None:
            before[0x5600:0x5600 + len(comspec) + 1] = comspec + b'\0'
        before[0xf000:0xf002] = struct.pack('<H', 0xf800)
        u = self.u
        u.mem_write(DATA, bytes(before))
        for reg, value in ((UC_X86_REG_CS, 0x1000), (UC_X86_REG_DS, 0x3000),
                           (UC_X86_REG_SS, 0x3000), (UC_X86_REG_ES, 0x3000),
                           (UC_X86_REG_SP, 0xf000), (UC_X86_REG_BP, 0xbabe),
                           (UC_X86_REG_SI, 0x1234), (UC_X86_REG_DI, 0x5678),
                           (UC_X86_REG_EFLAGS, 0x202)):
            u.reg_write(reg, value)
        start = dict(dos=0xf1fc, run=0xf203, shell=0xdc34)[kind]
        u.emu_start(0x10000 + start, 0, count=10000)
        assert self.returned
        if kind == 'shell':
            expected = (comspec, None, 0, 0, 1)
            expected_reads = ['COMSPEC']
            comparison = 0xabcd
        else:
            program, tail = text, None
            if kind == 'run':
                at = 0
                while at < len(text) and text[at] in WHITESPACE:
                    at += 1
                program = text[at:]
                if b' ' in program:
                    program, tail = program.split(b' ', 1)
            expected = (program, tail, int(kind == 'dos'), int(option == 0x36), int(option != 0x25))
            expected_reads = ['string', 'optional'] + ([] if option is None else ['option'])
            comparison = status
        assert self.calls == [expected], (kind, text, option, self.calls, expected)
        assert self.reads == expected_reads
        assert self.word(0xd124) == comparison
        before[0xd124:0xd126] = struct.pack('<H', comparison)
        after = bytes(u.mem_read(DATA, 65536))
        assert after[:0xee00] == before[:0xee00] and after[0xf002:] == before[0xf002:]
        assert u.reg_read(UC_X86_REG_SP) == 0xf002
        assert [u.reg_read(r) for r in (UC_X86_REG_BP, UC_X86_REG_SI, UC_X86_REG_DI)] == [0xbabe, 0x1234, 0x5678]
        assert u.reg_read(UC_X86_REG_DS) == u.reg_read(UC_X86_REG_SS) == u.reg_read(UC_X86_REG_ES) == 0x3000
        assert not u.reg_read(UC_X86_REG_EFLAGS) & 0x400
        return self.calls, self.reads, after[:0xee00]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--original', type=Path)
    args = parser.parse_args()
    raw = args.original.read_bytes() if args.original else None
    fixture = json.loads((ROOT / 'standalone/fixtures/aspect_external_native_units.json').read_text())
    if raw:
        assert hashlib.sha256(raw).hexdigest() == fixture['original_sha256']
        mask = bytes(b & 8 for b in raw[0x25950 + 0x7caf:0x25950 + 0x7daf])
        assert hashlib.sha256(mask).hexdigest() == fixture['ctype_mask_sha256']
    models = [Machine()] + ([Machine(raw)] if raw else [])
    cases, seen = 0, set()
    def case(*positional, **keywords):
        nonlocal cases
        values = [m.run(*positional, **keywords) for m in models]
        assert all(v == values[0] for v in values)
        seen.update(models[0].seen)
        cases += 1
    for kind in ('dos', 'run'):
        for text in (b'', b' ', b'   ', b'CHILD', b'CHILD ARG', b'CHILD ', b'CHILD  ARG',
                     b' \t\rCHILD ARG', b'CHILD\tARG', b'CHILD\tARG MORE',
                     b'"C:\\PROGRAM X.EXE" /Q', b'COMMAND /C ECHO A|B', b'X' * 80):
            for option in (None, 0x25, 0x36):
                for status in (0, 1, 12, 247, 0x8000, 65535):
                    case(kind, text, option, status)
        for byte in range(1, 256):
            case(kind, bytes([byte]) + b'CHILD ARG', option=byte, status=byte)
    for option in range(256):
        case('dos', b'CHILD ARG', option, 0xffff)
        case('run', b'CHILD ARG', option, 0xffff)
    for comspec in (None, b'', b'C:\\COMMAND.COM', b'X' * 80):
        for status in (0, 1, 12, 247, 0x8000, 65535):
            case('shell', status=status, comspec=comspec)
    result = dict(passed=True, cases=cases, original_comparisons=cases if raw else 0,
                  manifest_sha256=sha(OUT / 'manifest.json'), checker_sha256=sha(Path(__file__)),
                  instruction_addresses=len(seen),
                  scope='Actual native frontends plus strcpy/strchr; modeled string/optional reads, COMSPEC lookup and five-argument application executor. Whitespace mask, literal-space split, options/statuses, null/empty COMSPEC, complete nonstack and DS=SS/stack/BP/SI/DI/ES/DF guards. No DOS child, display or UART ownership claim.')
    (OUT / ('native-checks.json' if raw else 'checks.json')).write_text(json.dumps(result, indent=2) + '\n')
    print('External frontends:', cases, 'cases,', result['original_comparisons'], 'original comparisons PASS')


if __name__ == '__main__':
    main()
