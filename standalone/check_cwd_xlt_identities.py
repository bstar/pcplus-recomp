#!/usr/bin/env python3
"""Execute linked frozen XLT default binding and active identities; DOS modeled."""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from unicorn.x86_const import *
from check_directory_identity import Identity

ROOT = Path(__file__).resolve().parents[1]
CURRENT = b'D:\\WORK\\PCPLUS.XLT'
FALLBACK = b'D:\\ENV\\PCPLUS.XLT'
EXPLICIT = b'D:\\WORK\\CUSTOM.XLT'
TABLE = bytes(range(256))

class Model(Identity):
    def __init__(self, binary):
        super().__init__(binary)
        self.cwd = b'D:\\WORK'
        self.files = {}; self.handles = {}; self.opened = []; self.faults = set()
        self.put('process_psp', 0x100)
        self.environment(b'D:\\ENV')
        self.storage = self.stage_near(bytes(460))
        self.table = self.storage
        self.result = self.storage + 256
        self.executable = self.storage + 264
        self.tail = self.storage + 328
        self.path = self.storage + 396

    def environment(self, directory):
        blob = b'PCPLUS=' + directory + b'\0\0\x01\0D:\\APP\\TERMINAL.EXE\0'
        self.uc.mem_write(0x1000 + 0x2c, struct.pack('<H', 0x7000))
        self.uc.mem_write(0x6fff0, b'M\0\0' + struct.pack('<H', (len(blob)+15)//16))
        self.uc.mem_write(0x70000, blob)

    def string(self, pointer):
        return bytes(self.uc.mem_read(self.data_base+pointer, 128)).split(b'\0')[0]

    def interrupt(self, u, number, data):
        ax = u.reg_read(UC_X86_REG_AX); ah = ax >> 8
        assert number == 0x21, number
        error = answer = 0
        if ax == 0x6000:
            source = self.string(u.reg_read(UC_X86_REG_SI))
            self.calls.append(source)
            error = 5 if source in self.faults else 0
            if not error:
                absolute = source.upper() if source[1:2] == b':' else self.cwd+b'\\'+source.upper()
                u.mem_write(self.data_base+u.reg_read(UC_X86_REG_DI), absolute+b'\0')
        elif ah == 0x3d:
            name = self.string(u.reg_read(UC_X86_REG_DX)); self.opened.append(name)
            if name not in self.files: error = 2
            else:
                answer = 9; self.handles[answer] = [name, 0]
        elif ah == 0x3f:
            entry = self.handles[u.reg_read(UC_X86_REG_BX)]
            blob = self.files[entry[0]][entry[1]:entry[1]+u.reg_read(UC_X86_REG_CX)]
            entry[1] += len(blob); answer = len(blob)
            if blob: u.mem_write(self.data_base+u.reg_read(UC_X86_REG_DX), blob)
        elif ah == 0x3e:
            del self.handles[u.reg_read(UC_X86_REG_BX)]
        else: raise AssertionError(hex(ax))
        u.reg_write(UC_X86_REG_AX, error or answer)
        flags = u.reg_read(UC_X86_REG_EFLAGS)
        u.reg_write(UC_X86_REG_EFLAGS, flags | 1 if error else flags & ~1)

    def freeze(self, explicit=False):
        self.put('terminal_option_mask', 16384 if explicit else 0)
        self.bank('terminal_setup_translation_bind')

    def stage(self):
        return self.bank('_xlt_live_stage', [1, self.result])

    def active_name(self):
        assert self.bank('_xlt_live_editor', [0x100, self.executable, self.tail]) == 0
        assert self.string(self.executable) == b'D:\\APP\\XLTEDIT.EXE'
        return self.string(self.tail)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--terminal', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); binary = a.terminal.resolve(); out = a.output.resolve()
    assert out.is_relative_to(ROOT/'build') and not out.exists()
    out.mkdir(parents=True); cases = []
    for kind in ('current', 'fallback', 'explicit'):
        m = Model(binary); source = EXPLICIT if kind == 'explicit' else FALLBACK if kind == 'fallback' else CURRENT
        m.files[source] = TABLE
        m.uc.mem_write(m.data_base+m.path, b'CUSTOM.XLT\0')
        assert m.bank('_xlt_live_initialize', [0x100, 1, m.path if kind == 'explicit' else 0, m.table, m.result]) == 0
        m.freeze(kind == 'explicit'); frozen_calls = len(m.calls)
        assert m.active_name() == b' "'+source+b'"'
        m.cwd = b'D:\\OTHER'; m.environment(b'D:\\WRONG')
        m.files[b'D:\\OTHER\\PCPLUS.XLT'] = bytes(reversed(TABLE))
        assert m.bank('_xlt_live_reload', [0, 0, m.result]) == 0
        assert m.bank('_xlt_live_reload', [1, m.table, m.result]) == 0
        assert m.active_name() == b' "'+source+b'"'
        m.freeze(kind == 'explicit')
        assert len(m.calls) == frozen_calls
        expected = FALLBACK if kind == 'fallback' else CURRENT
        if kind == 'explicit':
            # Introduce the default only after explicit initialization. Its
            # startup canonical name must survive reload of CUSTOM.XLT.
            m.files[CURRENT] = TABLE
        assert m.stage() == 0
        assert m.opened[-1] == expected
        assert m.active_name() == b' "'+source+b'"'
        cases.append(kind)
    for fault in (b'PCPLUS.XLT', FALLBACK):
        m = Model(binary); m.faults.add(fault); m.freeze()
        m.faults.clear(); m.cwd = b'D:\\OTHER'; m.environment(b'D:\\WRONG')
        m.files[b'D:\\OTHER\\PCPLUS.XLT'] = TABLE
        calls = len(m.calls); m.freeze(); assert len(m.calls) == calls
        assert m.stage() == 6
        assert int.from_bytes(m.uc.mem_read(m.data_base+m.result+2, 2), 'little') == 5
        cases.append('frozen-error-'+fault.decode())
    sources = ['src/translation/xlt_live.c', 'src/terminal/setup_translation.asm',
               'standalone/check_cwd_xlt_identities.py', 'standalone/check_directory_identity.py',
               'standalone/dos_image.py']
    result = dict(passed=True, cases=cases, binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
                  sources={name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in sources},
                  original_inputs=[], scope=__doc__)
    (out/'result.json').write_text(json.dumps(result, indent=2)+'\n')
    print('PASS', len(cases), 'linked XLT CWD identity cases')

if __name__ == '__main__': main()
