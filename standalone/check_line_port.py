#!/usr/bin/env python3
"""Exhaust all 16-bit keys in flat and linked recovered selector bodies.

External bell/quiesce entry hooks record ordering. No UART or popup is modeled.
"""
import hashlib
import json
from pathlib import Path
import re
import struct
from unicorn import Uc, UC_ARCH_X86, UC_MODE_16, UC_HOOK_CODE
from unicorn.x86_const import (UC_X86_REG_CS, UC_X86_REG_DS, UC_X86_REG_SS,
    UC_X86_REG_ES, UC_X86_REG_SP, UC_X86_REG_BP, UC_X86_REG_SI,
    UC_X86_REG_DI, UC_X86_REG_BX, UC_X86_REG_EFLAGS)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/line-port'
NAMES = ['port', 'baud', 'parity', 'stop', 'bits']


def oracle(key, initial):
    state = list(initial)
    event = None
    if 0x31 <= key <= 0x39:
        state[1] = key - 0x31
    elif key < 256 and key in b'NOEMSnoems':
        state[2] = 'NOEMS'.index(chr(key).upper())
    elif key in (0x7800, 0x7900):
        state[3] = 1 + (key == 0x7900)
    elif key in (0x7e00, 0x7f00):
        state[4] = 7 + (key == 0x7f00)
    elif key in (0x1200, 0x3100):
        state[2:] = [2, 1, 7] if key == 0x1200 else [0, 1, 8]
    elif 0x3b00 <= key <= 0x4200 and key & 255 == 0:
        event = 'quiesce'
        state[0] = (key >> 8) - 0x3b
    else:
        event = 'bell'
    return tuple(state), event


class Machine:
    def __init__(self, linked):
        self.uc = u = Uc(UC_ARCH_X86, UC_MODE_16)
        u.mem_map(0, 0x100000)
        self.cs, self.ds = 0x1000, 0x4000
        if linked:
            raw = (OUT / 'LINEPORT.EXE').read_bytes()
            h = struct.unpack_from('<14H', raw)
            size = (h[2] - 1) * 512 + (h[1] or 512)
            u.mem_write(self.cs * 16, raw[h[4] * 16:size])
            for i in range(h[3]):
                off, seg = struct.unpack_from('<HH', raw, h[12] + 4 * i)
                at = self.cs * 16 + seg * 16 + off
                old = struct.unpack('<H', u.mem_read(at, 2))[0]
                u.mem_write(at, struct.pack('<H', (old + self.cs) & 65535))
            listing = (OUT / 'lineport.map').read_text()
            group = re.search(r'^DGROUP\s+([0-9a-f]+):', listing, re.M | re.I)
            self.ds = self.cs + int(group[1], 16)
            symbols = {name: self.cs * 16 + int(seg, 16) * 16 + int(off, 16)
                       for seg, off, name in re.findall(
                           r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',
                           listing, re.M | re.I)}
            self.entry = symbols['line_port_key']
            self.state = symbols['line_port_port']
            assert self.state - self.ds * 16 >= 128, 'padding must test group-relative externs'
            services = {name: symbols['line_port_' + name] for name in ('bell', 'quiesce')}
        else:
            self.entry = self.cs * 16 + 0xf05c
            self.state = self.ds * 16 + 0x1b84
            u.mem_write(self.entry, (OUT / 'key.bin').read_bytes())
            services = {'bell': self.cs * 16 + 0x376d, 'quiesce': self.cs * 16 + 0xadba}
            for at in services.values():
                u.mem_write(at, b'\xc3')  # declared external boundary only
        self.stop = self.cs * 16 + 0xfffe
        u.mem_write(self.stop, b'\xf4')
        for name, at in services.items():
            def record(uc, address, size, event):
                self.events.append((event, self.get_state()))
            u.hook_add(UC_HOOK_CODE, record, name, begin=at, end=at)
        u.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: uc.emu_stop(), begin=self.stop, end=self.stop)

    def get_state(self):
        return struct.unpack('<5H', self.uc.mem_read(self.state, 10))

    def run(self, key, initial):
        u = self.uc
        self.events = []
        u.mem_write(self.state, struct.pack('<5H', *initial))
        registers = {UC_X86_REG_CS: self.cs, UC_X86_REG_DS: self.ds,
                     UC_X86_REG_SS: self.ds, UC_X86_REG_ES: 0x5555,
                     UC_X86_REG_SP: 0xf000, UC_X86_REG_BP: 0x1234,
                     UC_X86_REG_SI: 0x5678, UC_X86_REG_DI: 0x9abc,
                     UC_X86_REG_BX: 0xdef0, UC_X86_REG_EFLAGS: 2}
        for reg, value in registers.items():
            u.reg_write(reg, value)
        u.mem_write(self.ds * 16 + 0xf000, struct.pack('<HH', 0xfffe, key))
        u.emu_start(self.entry, self.stop, count=200)
        assert u.reg_read(UC_X86_REG_SP) == 0xf002, (key, 'stack')
        for reg in (UC_X86_REG_DS, UC_X86_REG_SS, UC_X86_REG_ES, UC_X86_REG_BP,
                    UC_X86_REG_SI, UC_X86_REG_DI, UC_X86_REG_BX):
            assert u.reg_read(reg) == registers[reg], (key, 'register', reg)
        expected, event = oracle(key, initial)
        assert self.get_state() == expected, (key, initial, self.get_state(), expected)
        assert self.events == ([(event, initial)] if event else []), (key, self.events, event)


def main():
    for linked in (False, True):
        machine = Machine(linked)
        for initial in ((2, 4, 0, 1, 8), (0x9123, 0x8245, 0x7367, 0x6489, 0x55ab)):
            for key in range(65536):
                machine.run(key, initial)
        print(('linked OMF' if linked else 'exact flat') + ': 131072 key/state cases passed', flush=True)
    sources = ['standalone/check_line_port.py', 'standalone/build_line_port.py',
               'standalone/line_port_host.asm', 'reconstruction/line_port/key.asm',
               'reconstruction/line_port/provenance.json', 'reconstruction/uart/encodings.inc']
    (OUT / 'selector-results.json').write_text(json.dumps({
        'passed': True, 'cases': 262144, 'keys_per_initial_state': 65536,
        'initial_states_per_body': 2, 'bodies': ['exact flat', 'linked OMF'],
        'manifest': json.loads((OUT / 'manifest.json').read_text()),
        'sources': {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in sources},
        'checks': ['five-word state', 'external callback before state write',
                   'invalid keys bell once without mutation', 'cdecl stack and preserved registers',
                   'nonzero group-relative OMF data addresses'],
        'limitations': ['CPU emulation with declared external services; no popup, disk, UART or physical acceptance.']
    }, indent=2) + '\n')


if __name__ == '__main__':
    main()
