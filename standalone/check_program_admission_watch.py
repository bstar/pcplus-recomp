#!/usr/bin/env python3
"""Execute the observer's real INT21 wrapper and check DOS results/IRET flags."""
import argparse
import json
import struct
import subprocess
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_16, UC_HOOK_CODE
from unicorn.x86_const import *
from build_path_session import ROOT, sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    assert output.is_relative_to(ROOT / 'build') and not output.exists()
    output.mkdir()
    source = output / 'wrapper.asm'
    fields = ['ISR_OFFSET', 'ISR_SEGMENT', 'DATA_SEGMENT', 'PSP', 'PROGRAM_KIND',
              'PROGRAM_STATUS', 'PROCESS_STATUS', 'DOS_ERROR', 'CHILD_STATUS', 'KEEP', 'RESULT']
    source.write_text('bits 16\ncpu 8086\norg 100h\n'
                      'dw admission_hook21,admission_old21,admission_open\n'
                      '%macro save 0\n%endmacro\n%macro restore 0\n%endmacro\n' +
                      ''.join(f'%define ADMISSION_{n} 0\n' for n in fields) +
                      '%include "' + str(ROOT / 'standalone/program_admission_watch.inc') + '"\n')
    binary = output / 'wrapper.bin'
    subprocess.run(['nasm', '-fbin', str(source), '-o', str(binary)], check=True)
    data = binary.read_bytes()
    entry, old, report = struct.unpack_from('<3H', data)
    cases = []
    for path, function in [(b'D:\\SYNC.ASX\0', 0x3d00), (b'D:\\SYNC.ASX\0', 0x6c00), (b'OTHER.DAT\0', 0x3d00),
                           (b'D:\\SYNC.ASX\0', 0x4300)]:
        for error, result in [(False, 6), (True, 2), (True, 5), (True, 8)]:
            u = Uc(UC_ARCH_X86, UC_MODE_16)
            u.mem_map(0, 0x100000)
            u.mem_write(0x10100, data)
            u.mem_write(0x10000 + old, struct.pack('<HH', 0, 0x3000))
            # Model only the predecessor DOS service: AX result and saved CF.
            stub = b'\x55\x89\xe5\xb8' + struct.pack('<H', result)
            stub += b'\x36\x83' + (b'\x4e\x06\x01' if error else b'\x66\x06\xfe')
            stub += b'\x5d\xcf'
            u.mem_write(0x30000, stub)
            u.mem_write(0x40200, path)
            u.mem_write(0x58ff0, struct.pack('<3H', 0x100, 0xf000, 0x0202))
            values = {UC_X86_REG_CS: 0x1000, UC_X86_REG_IP: entry, UC_X86_REG_SS: 0x5000,
                      UC_X86_REG_SP: 0x8ff0, UC_X86_REG_DS: 0x4000, UC_X86_REG_ES: 0xbeef,
                      UC_X86_REG_AX: function, UC_X86_REG_DX: 0x200, UC_X86_REG_BX: 0x3456,
                      UC_X86_REG_CX: 0x789a, UC_X86_REG_SI: 0x200 if function == 0x6c00 else 0x1234, UC_X86_REG_BP: 0x5678,
                      UC_X86_REG_EFLAGS: 2}
            for register, value in values.items():
                u.reg_write(register, value)
            returned = []
            def stop(machine, address, size, unused):
                if address == 0xf0100:
                    returned.append(True)
                    machine.emu_stop()
            u.hook_add(UC_HOOK_CODE, stop)
            u.emu_start(0x10000 + entry, 0, count=5000)
            assert returned and u.reg_read(UC_X86_REG_AX) == result
            assert u.reg_read(UC_X86_REG_EFLAGS) & 0x0203 == 0x0202 | error
            assert u.reg_read(UC_X86_REG_SP) == 0x8ff6
            for register in [UC_X86_REG_DS, UC_X86_REG_ES, UC_X86_REG_BX,
                             UC_X86_REG_CX, UC_X86_REG_DX, UC_X86_REG_SI, UC_X86_REG_BP]:
                assert u.reg_read(register) == values[register]
            recorded = struct.unpack('<4H', bytes(u.mem_read(0x10000 + report, 8)))
            matched = function in (0x3d00, 0x6c00) and b'SYNC.ASX' in path
            assert recorded[0] == int(matched)
            if matched:
                assert recorded[1] & 1 == error and recorded[2] == result and recorded[3] == function
            cases.append(dict(path=path.rstrip(b'\0').decode(), function=function,
                              error=error, result=result, passed=True))
    result = dict(passed=True, cases=cases,
                  sources={n: sha(ROOT / n) for n in ['standalone/check_program_admission_watch.py',
                           'standalone/program_admission_watch.inc']},
                  scope=__doc__ + ' Actual assembled hook; DOS predecessor modeled. No application or hardware acceptance.')
    (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print('PASS', len(cases), 'DOS wrapper success/error/filter and register/stack/FLAGS cases')


if __name__ == '__main__':
    main()
