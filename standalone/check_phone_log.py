#!/usr/bin/env python3
"""Execute recovered16-bit call-log policy with explicit external FILE/clock models."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import struct
import subprocess

from unicorn import Uc, UC_ARCH_X86, UC_MODE_16, UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_CS, UC_X86_REG_DS, UC_X86_REG_SS, UC_X86_REG_SP, UC_X86_REG_IP, UC_X86_REG_AX, UC_X86_REG_BX, UC_X86_REG_BP, UC_X86_REG_DI

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/phone-log'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def execute(blob, proof, enabled, stop, pending, exists, opened, write_ok, close_ok):
    machine = Uc(UC_ARCH_X86, UC_MODE_16)
    machine.mem_map(0, 1024 * 1024)
    code, data = 0x10000, 0x30000
    machine.mem_write(code + proof['start'], blob)
    strings = {'phone_log_filename': b'CALLS.FON', 'phone_log_append_mode': b'at',
               'phone_log_error_format': b'Error opening %s', 'phone_log_heading_name': b'NAME',
               'phone_log_heading_format': b'\n%-36sNUMBER    DATE    ONLINE  OFFLINE  ELAPSED',
               'phone_log_name': b'LoC LAB', 'phone_log_number': b'5550100',
               'phone_log_connect_format': b'\n%-22.22s %20s %s %s ',
               'phone_log_disconnect_format': b'%s %s', 'phone_log_elapsed': b'00:01:02'}
    state = {name: int(address, 16) for address, name in proof['state'].items()}
    for name, value in strings.items():
        machine.mem_write(data + state[name], value + b'\0')
    def word(address):
        return struct.unpack('<H', machine.mem_read(data + address, 2))[0]
    def put(address, value):
        machine.mem_write(data + address, struct.pack('<H', value))
    def string(address):
        result = bytearray()
        for i in range(100):
            value = machine.mem_read(data + address + i, 1)[0]
            if not value:
                return bytes(result)
            result.append(value)
        raise AssertionError('Unterminated diagnostic string')
    put(state['phone_log_enabled'], enabled)
    put(state['phone_log_pending'], pending)
    machine.mem_write(data + 0x6000, b'12:34:56\0')
    machine.mem_write(data + 0x6020, b'10/24/26\0')
    machine.mem_write(data + 0xeff0, struct.pack('<HH', 0x100, stop))
    for register, value in [(UC_X86_REG_CS, code >> 4), (UC_X86_REG_DS, data >> 4),
                            (UC_X86_REG_SS, data >> 4), (UC_X86_REG_SP, 0xeff0),
                            (UC_X86_REG_BP, 0xbabe), (UC_X86_REG_DI, 0x5678)]:
        machine.reg_write(register, value)
    trace = []
    services = {code + int(address, 16): name for address, name in proof['services'].items()}
    def hook(mu, address, size, user):
        if address == code + 0x100:
            mu.emu_stop()
            return
        if address not in services:
            return
        name = services[address]
        stack = mu.reg_read(UC_X86_REG_SP)
        arg = lambda number: word(stack + 2 + number * 2)
        result = 0
        if name.endswith('_clock'):
            trace.append((name,))
        elif name == 'phone_log_resolve':
            assert string(arg(0)) == b'CALLS.FON'
            result = arg(0)
            trace.append(('resolve',))
        elif name == 'phone_log_exists':
            assert string(arg(0)) == b'CALLS.FON'
            result = exists
            trace.append(('exists',))
        elif name == 'phone_log_prepare':
            assert string(arg(0)) == b'CALLS.FON'
            trace.append(('prepare',))
        elif name == 'phone_log_open':
            assert string(arg(0)) == b'CALLS.FON' and string(arg(1)) == b'at'
            result = 0xc000 if opened else 0
            trace.append(('open',))
        elif name == 'phone_log_sprintf':
            assert string(arg(1)) == b'Error opening %s' and string(arg(2)) == b'CALLS.FON'
            machine.mem_write(data + arg(0), b'Error opening CALLS.FON\0')
            trace.append(('sprintf',))
        elif name == 'phone_log_notice':
            assert string(mu.reg_read(UC_X86_REG_BX)) == b'Error opening CALLS.FON'
            trace.append(('notice',))
        elif name == 'phone_log_time':
            assert arg(0) == 1
            result = 0x6000
            trace.append(('time',))
        elif name == 'phone_log_date':
            result = 0x6020
            trace.append(('date',))
        elif name == 'phone_log_fprintf':
            assert arg(0) == 0xc000
            fmt = string(arg(1))
            if fmt == strings['phone_log_heading_format']:
                assert string(arg(2)) == b'NAME'
                trace.append(('heading',))
            elif fmt == strings['phone_log_connect_format']:
                assert [string(arg(n)) for n in range(2, 6)] == [b'LoC LAB', b'5550100', b'10/24/26', b'12:34:56']
                trace.append(('connect',))
            else:
                assert fmt == strings['phone_log_disconnect_format']
                assert [string(arg(n)) for n in range(2, 4)] == [b'12:34:56', b'00:01:02']
                trace.append(('disconnect',))
            result = 10 if write_ok else 65535
        elif name == 'phone_log_close':
            assert arg(0) == 0xc000
            trace.append(('close',))
            result = 0 if close_ok else 65535
        else:
            raise AssertionError(name)
        mu.reg_write(UC_X86_REG_AX, result)
        mu.reg_write(UC_X86_REG_IP, word(stack))
        mu.reg_write(UC_X86_REG_SP, stack + 2)
    machine.hook_add(UC_HOOK_CODE, hook)
    machine.emu_start(code + proof['start'], code + 0x100, count=100000)
    assert machine.reg_read(UC_X86_REG_SP) == 0xeff4
    assert machine.reg_read(UC_X86_REG_BP) == 0xbabe and machine.reg_read(UC_X86_REG_DI) == 0x5678
    assert machine.reg_read(UC_X86_REG_DS) == machine.reg_read(UC_X86_REG_SS) == data >> 4
    expected = [('phone_log_stop_clock' if stop else 'phone_log_start_clock',)]
    expected_pending = pending
    if not enabled:
        expected_pending = 0
    else:
        expected += [('resolve',), ('exists',)]
        if not stop or (pending and exists):
            expected += [('resolve',), ('prepare',), ('resolve',), ('open',)]
            if not opened:
                expected += [('sprintf',), ('notice',)]
            else:
                if not stop:
                    if not exists:
                        expected += [('heading',)]
                    expected += [('time',), ('date',), ('connect',)]
                else:
                    expected += [('time',), ('disconnect',)]
                expected += [('close',)]
                expected_pending = int(not stop)
    assert trace == expected, (enabled, stop, pending, exists, opened, trace, expected)
    assert word(state['phone_log_pending']) == expected_pending


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--original', type=Path)
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    source = ROOT / 'reconstruction/phone_log/controller.asm'
    proof = json.loads((source.parent / 'provenance.json').read_text())
    subprocess.run(['nasm', '-fbin', '-I' + str(ROOT / 'reconstruction/uart') + '/', str(source), '-o', str(OUT / 'controller.bin')], check=True)
    blob = (OUT / 'controller.bin').read_bytes()
    assert len(blob) == proof['bytes'] == 258 and sha(blob) == proof['sha256']
    original_verified = False
    if args.original:
        original = args.original.read_bytes()
        assert sha(original) == proof['source_sha256']
        assert original[proof['source_file_offset']:proof['source_file_offset'] + len(blob)] == blob
        original_verified = True
    count = 0
    for case in itertools.product([0, 1], [0, 1, 2, 65535], [0, 1, 65535], [0, 1], [False, True], [False, True], [False, True]):
        execute(blob, proof, *case)
        count += 1
    result = dict(passed=True, inputs=count, bytes=len(blob), sha256=sha(blob), original_verified=original_verified,
                  sources={str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in [Path(__file__), source, source.parent / 'provenance.json', ROOT / 'reconstruction/uart/encodings.inc']},
                  scope='Actual recovered16-bit instructions, exact CDECL/RET2 stack and BX notice convention; explicit FILE/path/clock models, including native ignored write/close failures. Not filesystem/UART/application acceptance.')
    (OUT / 'cpu-checks.json').write_text(json.dumps(result, indent=2) + '\n')
    print('Passed', count, 'native telephone-log policy/ABI inputs')


if __name__ == '__main__':
    main()
