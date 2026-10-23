#!/usr/bin/env python3
"""Replay linked parent/child register owners; no DOS or UART service modeled."""
import argparse
import hashlib
import json
import re
import struct
from pathlib import Path

from unicorn import UC_HOOK_INTR, UC_HOOK_INSN
from unicorn.x86_const import *
from dos_image import DosImage

ROOT = Path(__file__).resolve().parents[1]


def seal(raw, token):
    value = token
    for byte in raw:
        value = (((value << 1) | (value >> 15)) & 65535) ^ byte
    return value


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Replay:
    def __init__(self, directory, binary, listing):
        self.directory = directory
        self.model = m = DosImage(directory / binary, directory / listing)
        self.uc = m.uc
        self.symbols = {
            name: (m.base_segment + int(segment, 16), int(offset, 16))
            for segment, offset, name in re.findall(
                r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',
                (directory / listing).read_text(), re.M | re.I)
        }
        self.top = m.offset('terminal_stack_top') if 'terminal_stack_top' in m.symbols else 0xe000
        def prohibited(*args):
            raise AssertionError('register API attempted interrupt or port IO')
        self.uc.hook_add(UC_HOOK_INTR, prohibited)
        for opcode in [UC_X86_INS_IN, UC_X86_INS_OUT]:
            self.uc.hook_add(UC_HOOK_INSN, prohibited, None, 1, 0, opcode)

    def call(self, name, args=(), flags=0x202, ds=None, ss=None):
        m, u = self.model, self.uc
        cs, ip = self.symbols[name]
        saved = {UC_X86_REG_CS: cs, UC_X86_REG_IP: ip,
                 UC_X86_REG_DS: m.ds if ds is None else ds,
                 UC_X86_REG_SS: m.ds if ss is None else ss,
                 UC_X86_REG_BP: 0xbabe, UC_X86_REG_SI: 0x1234,
                 UC_X86_REG_DI: 0x5678, UC_X86_REG_EFLAGS: flags}
        sp = self.top - 128
        for register, value in saved.items():
            u.reg_write(register, value)
        u.reg_write(UC_X86_REG_SP, sp)
        u.mem_write(saved[UC_X86_REG_SS] * 16 + sp,
                    struct.pack('<' + 'H' * (len(args) + 2),
                                m.return_offset, m.code_segment, *args))
        m.returned = False
        u.emu_start(cs * 16 + ip, 0, count=500000)
        assert m.returned, name
        assert u.reg_read(UC_X86_REG_SP) == sp + 4, name
        for register in [UC_X86_REG_DS, UC_X86_REG_SS, UC_X86_REG_BP, UC_X86_REG_SI, UC_X86_REG_DI]:
            assert u.reg_read(register) == saved[register], (name, register)
        return u.reg_read(UC_X86_REG_AX), u.reg_read(UC_X86_REG_DX)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    assert output.is_relative_to(ROOT / 'build') and not output.exists()
    output.mkdir(parents=True)
    parent_dir = ROOT / 'build/terminal-directory-keys-process-bank-session-capture-projection-bound-registers'
    child_dir = ROOT / 'build/aspect-register-parent'
    parent = Replay(parent_dir, 'TERMINAL.EXE', 'terminal.map')
    child = Replay(child_dir, 'ASPECT.EXE', 'ASPECT.map')
    p, u = parent.model, parent.uc
    owner = p.symbols['_terminal_register_owner']
    descriptor, exchange, accepted = owner + 8, owner + 66, owner + 904
    pointer = p.stage_near(bytes(896))
    base_address = p.data_base + pointer
    dest = pointer + 64
    original = bytearray(50)
    struct.pack_into('<I8H', original, 0, 0x4f495341, 6, 50, 0x800, p.ds, 0x100, 4096, 0, 0)
    struct.pack_into('<H', original, 20, 0xa510)
    u.mem_write(base_address, bytes(original))
    cases = []

    def done(name, count=1):
        cases.append(dict(case=name, inputs=count, passed=True))
        print(name, count, flush=True)

    def call(name, arguments=(), **kw):
        return parent.call('_terminal_register_' + name, arguments, **kw)[0]

    def prepare():
        u.mem_write(base_address, bytes(original))
        ax, dx = parent.call('_terminal_register_prepare', [pointer])
        assert dx * 16 + ax == descriptor

    def publish(raw, returned=True):
        token = int.from_bytes(u.mem_read(owner + 2, 2), 'little')
        u.mem_write(exchange, struct.pack('<4H', 0x5247, token, int(returned), seal(raw, token)) + raw)
        u.mem_write(descriptor + 22, b'\1\0')

    def snapshot(expected):
        u.mem_write(p.data_base + dest, b'X' * 830)
        assert call('snapshot', [dest, dest + 20]) == 0
        assert bytes(u.mem_read(p.data_base + dest, 830)) == expected

    raw = bytes(830)
    snapshot(raw)
    assert call('commit') == 1
    for flags, ds, ss in [(0x2, None, None), (0x602, None, None),
                          (0x202, p.ds + 1, None), (0x202, None, p.ds + 1)]:
        before = bytes(u.mem_read(owner, 1734))
        assert call('prepare', [pointer], flags=flags, ds=ds, ss=ss) == 0
        assert bytes(u.mem_read(owner, 1734)) == before
    done('initial-snapshot-and-context-rejection', 6)

    prepare()
    before = bytes(u.mem_read(owner, 1734))
    assert call('prepare', [pointer]) == 0
    assert bytes(u.mem_read(owner, 1734)) == before
    assert call('commit') == 1
    assert call('extract', [pointer, 1]) == 1
    snapshot(raw)
    done('busy-prepare-and-unvalidated-commit-refused', 3)

    # Nonzero tails and every integer word must survive publication. Subsequent
    # invocation resets integer values and first string bytes, preserving tails.
    for generation in range(1, 17):
        prepare()
        seeded = bytearray(raw)
        seeded[:20] = bytes(20)
        for index in range(10):
            seeded[20 + index * 81] = 0
        assert bytes(u.mem_read(exchange + 8, 830)) == bytes(seeded)
        raw = bytearray((generation * 13 + index * 7) & 255 for index in range(830))
        for index in range(10):
            raw[20 + index * 81 + 80] = 0
        raw = bytes(raw)
        publish(raw)
        assert call('extract', [pointer, 1]) == 0
        assert call('commit') == 0
        assert call('commit') == 1
        snapshot(raw)
    done('all-banks-publish-and-next-invocation-native-reset', 16)

    # Each field used for admission is independently damaged after a valid
    # publication. Refusal must leave the previously accepted bank intact.
    for offset in [0, 4, 6, 8, 10, 12, 14, 20, 22, 24, 26, 28, 30, 32, 34,
                   36, 38, 40, 42, 44, 46, 50, 52, 54, 56]:
        prepare()
        publish(bytes(830))
        at = descriptor + offset
        u.mem_write(at, bytes([u.mem_read(at, 1)[0] ^ 1]))
        assert call('extract', [pointer, 1]) == 1, offset
        snapshot(raw)
    done('descriptor-damage-refuses-without-accepted-bank-change', 25)
    for offset in [0, 2, 4, 6] + list(range(8, 838)):
        prepare()
        publish(bytes(830))
        at = exchange + offset
        u.mem_write(at, bytes([u.mem_read(at, 1)[0] ^ 1]))
        assert call('extract', [pointer, 1]) == 1, offset
        assert bytes(u.mem_read(accepted, 830)) == raw
    done('exchange-header-and-each-payload-byte-damage-refused', 834)

    prepare()
    publish(bytes(830), returned=False)
    assert call('extract', [pointer, 0]) == 0
    assert call('commit') == 0
    snapshot(raw)
    prepare()
    publish(bytes(830), returned=False)
    assert call('extract', [pointer, 1]) == 1
    snapshot(raw)
    prepare()
    publish(bytes(830))
    assert call('extract', [pointer, 1]) == 0
    u.mem_write(exchange + 8, b'\1')
    assert call('commit') == 1
    snapshot(raw)
    done('missing-child-publication-and-post-extract-damage', 3)

    for offset, value in [(16, 4097), (48, 4), (48, 2)]:
        prepare()
        publish(bytes(830))
        u.mem_write(descriptor + offset, struct.pack('<H', value))
        assert call('extract', [pointer, 1]) == 1
        snapshot(raw)
    prepare()
    unterminated = b'\0' * 20 + b'X' * 81 + b'\0' * 729
    publish(unterminated)
    assert call('extract', [pointer, 1]) == 1
    snapshot(raw)
    u.mem_write(owner + 2, b'\xff\xff')
    prepare()
    assert bytes(u.mem_read(owner + 2, 2)) == b'\1\0'
    call('discard')
    assert call('snapshot', [dest, dest + 19]) == 1
    assert call('snapshot', [0xfff0, dest]) == 1
    snapshot(raw)
    done('count-flow-terminator-token-wrap-and-output-bounds', 7)

    # Exercise the actual separately linked child with a far parent fixture.
    # There is no shared DS assumption: its two banks have distinct symbols.
    c, cu = child.model, child.uc
    far_descriptor, far_exchange = 0x90000, 0x91000
    desc = bytearray(58)
    struct.pack_into('<4H', desc, 50, 0, 0x9100, 838, 0x1234)
    seed = bytearray(raw)
    for index in range(10):
        seed[20 + index * 81] = 0
    seed = bytes(seed)
    packet = struct.pack('<4H', 0x5247, 0x1234, 0, seal(seed, 0x1234)) + seed
    cu.mem_write(far_descriptor, bytes(desc))
    cu.mem_write(far_exchange, packet)
    validate_args = [0, 0x9000, 0, 9, 0, 10, 0x2000, 9, 0, 0, 0, 0, 0, 0]
    assert child.call('_aspect_register_validate', validate_args)[0] == 0
    child.call('_aspect_register_attach', [0, 0x9000])
    assert child.call('_aspect_register_start')[0] == 0
    integers, strings = c.symbols['_runtime_integer_a'], c.symbols['_runtime_string_bank_a']
    assert bytes(cu.mem_read(integers, 20)) == bytes(20)
    assert bytes(cu.mem_read(strings, 810)) == seed[20:]
    cu.mem_write(integers, raw[:20])
    cu.mem_write(strings, raw[20:])
    assert child.call('_aspect_register_publish')[0] == 0
    assert bytes(cu.mem_read(far_exchange, 838)) == struct.pack('<4H', 0x5247, 0x1234, 1, seal(raw, 0x1234)) + raw
    before = bytes(cu.mem_read(far_exchange, 838))
    assert child.call('_aspect_register_publish')[0] == 0
    assert bytes(cu.mem_read(far_exchange, 838)) == before
    done('separately-linked-child-far-admission-init-and-publication', 5)

    for offset in [50, 52, 54, 56]:
        broken = bytearray(desc)
        broken[offset] ^= 1
        cu.mem_write(far_descriptor, bytes(broken))
        cu.mem_write(far_exchange, packet)
        assert child.call('_aspect_register_validate', validate_args)[0] == 1
    cu.mem_write(far_descriptor, bytes(desc))
    cu.mem_write(far_exchange, packet)
    child.call('_aspect_register_attach', [0, 0x9000])
    assert child.call('_aspect_register_start')[0] == 0
    cu.mem_write(strings, b'X' * 81)
    assert child.call('_aspect_register_publish')[0] == 1
    assert bytes(cu.mem_read(far_exchange, 838)) == packet
    done('child-invalid-extension-and-unterminated-string-refused', 5)

    for argument, value in [(2, 0x91001), (4, 0x91345), (6, far_exchange),
                            (8, far_exchange), (10, far_exchange), (12, far_exchange)]:
        invalid = list(validate_args)
        invalid[argument:argument + 2] = [value & 65535, value >> 16]
        cu.mem_write(far_exchange, packet)
        assert child.call('_aspect_register_validate', invalid)[0] == 1
    for offset, segment in [(32, 0x9000), (0xff00, 0x9100), (0, 0xffff)]:
        broken = bytearray(desc)
        struct.pack_into('<2H', broken, 50, offset, segment)
        cu.mem_write(far_descriptor, bytes(broken))
        assert child.call('_aspect_register_validate', validate_args)[0] == 1
    cu.mem_write(far_descriptor, bytes(desc))
    for index in range(10):
        invalid = bytearray(seed)
        invalid[20 + index * 81:20 + (index + 1) * 81] = b'X' * 81
        cu.mem_write(far_exchange, struct.pack('<4H', 0x5247, 0x1234, 0, seal(invalid, 0x1234)) + invalid)
        assert child.call('_aspect_register_validate', validate_args)[0] == 1
    done('child-allocation-overlaps-segment-wrap-and-all-string-bounds', 19)

    sources = {}
    for directory in [parent_dir, child_dir]:
        manifest = json.loads((directory / 'manifest.json').read_text())
        for name, digest in manifest['sources'].items():
            assert sha(ROOT / name) == digest, name
            sources[name] = digest
    for name in ['standalone/check_register_handoff.py', 'standalone/dos_image.py']:
        sources[name] = sha(ROOT / name)
    result = dict(passed=True, inputs=sum(case['inputs'] for case in cases), cases=cases,
                  parent_sha256=sha(parent_dir / 'TERMINAL.EXE'), child_sha256=sha(child_dir / 'ASPECT.EXE'),
                  sources=sources, scope='Linked 16-bit far APIs with CPU replay; no substituted product routine. Actual DOS EXEC, script parsing, UART continuity and hardware are separate acceptance requirements.')
    (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print('PASS', result['inputs'], 'linked register handoff cases')


if __name__ == '__main__':
    main()
