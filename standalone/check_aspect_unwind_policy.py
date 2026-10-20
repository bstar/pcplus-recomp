#!/usr/bin/env python3
"""Replay actual scope/JFT recovery policy with declared DOS boundaries."""
import argparse
import json
from pathlib import Path
import struct
from build_aspect_process import ROOT, OUT, sha
from check_process_handles import Handles
from dos_image import DosImage
from unicorn import UC_HOOK_CODE, UC_HOOK_INTR, UC_HOOK_INSN
from unicorn.x86_const import *


class Scope(DosImage):
    def __init__(self):
        super().__init__(OUT / 'ASPECT.EXE', OUT / 'ASPECT.map')
        self.vector = (0x1234, 0x5678)
        self.paused = False
        self.uc.hook_add(UC_HOOK_INTR, self.interrupt)
        self.uc.hook_add(UC_HOOK_CODE, self.entry)
        for instruction in (UC_X86_INS_IN, UC_X86_INS_OUT):
            self.uc.hook_add(UC_HOOK_INSN, self.forbidden, None, 1, 0, instruction)
        self.uc.mem_write(self.data_base + 0xc200, b'PROBE.ASX\0')
        for register, value in [(UC_X86_REG_CS, self.base_segment),
                                (UC_X86_REG_DS, self.ds), (UC_X86_REG_SS, self.ds),
                                (UC_X86_REG_ES, self.ds), (UC_X86_REG_EFLAGS, 0x202),
                                (UC_X86_REG_SP, 0xe000)]:
            self.uc.reg_write(register, value)
        self.uc.mem_write(self.data_base + 0xe000, struct.pack('<3H', self.return_offset, 0xc200, 100))
        # Actual runtime admission/initialization; stop at the declared VM entry.
        # No ASX file, opcode, renderer, UART or DOS filesystem is modeled here.
        self.uc.emu_start(self.symbols['_aspect_runtime_run'], 0, count=100000)
        assert self.paused
        self.runtime_vector = self.vector

    def forbidden(self, *args):
        raise AssertionError('Scope policy reached port IO')

    def entry(self, uc, address, size, data):
        if address == self.symbols['_runtime_enter'] and not self.paused:
            self.paused = True
            uc.emu_stop()

    def interrupt(self, uc, number, data):
        assert number == 0x21 and uc.reg_read(UC_X86_REG_AL) == 0
        ah = uc.reg_read(UC_X86_REG_AH)
        if ah == 0x35:
            uc.reg_write(UC_X86_REG_ES, self.vector[0])
            uc.reg_write(UC_X86_REG_BX, self.vector[1])
        elif ah == 0x25:
            self.vector = (uc.reg_read(UC_X86_REG_DS), uc.reg_read(UC_X86_REG_DX))
        else:
            raise AssertionError('Undeclared DOS scope service: ' + hex(ah))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='unwind-policy.json')
    args = parser.parse_args()
    assert Path(args.output).name == args.output
    cases = []
    m = Scope()
    assert m.call('_runtime_external_scope', [1]) == 0
    assert m.call('_runtime_external_scope', [1]) == 10
    assert m.call('_runtime_external_scope_active') == 1
    assert m.call('_runtime_external_scope', [0]) == 0
    cases.append(dict(case='exclusive-scope-and-normal-retirement', passed=m.call('_runtime_external_scope_active') == 0))
    m = Scope()
    m.vector = (0x9999, 0x8888)
    cases.append(dict(case='foreign-vector-rejects-admission', passed=
                      m.call('_runtime_external_scope', [1]) == 10 and
                      m.call('_runtime_external_scope_active') == 0))
    m = Scope()
    assert m.call('_runtime_external_scope', [1]) == 0
    m.vector = (0x9999, 0x8888)
    result = m.call('_runtime_external_scope', [0])
    retained = m.call('_runtime_external_scope_active')
    m.vector = m.runtime_vector
    retry = m.call('_runtime_external_scope', [0])
    cases.append(dict(case='failed-vector-retirement-retains-scope-until-repaired',
                      passed=result == 10 and retained == 1 and retry == 0 and
                      m.call('_runtime_external_scope_active') == 0,
                      error=result, retained=retained, retry=retry))
    # BEGIN/END may be interrupted at any selected JFT entry. Recovery accepts
    # each saved byte or our FF mask, preserves unrelated slots, and flags any
    # third-party value while still reclaiming all entries it owns.
    for restored in range(8):
        m = Handles()
        original = bytearray(m.table())
        descriptors = [0, 2, 4, 6, 8, 10, 19]
        assert m.begin(descriptors) == 0
        for index in descriptors[:restored]:
            m.uc.mem_write(m.address + index, bytes([original[index]]))
        original[1] = 77
        m.uc.mem_write(m.address + 1, b'M')
        cases.append(dict(case='partial-JFT-' + str(restored), passed=
                          m.call('_process_handles_recover') == 0 and
                          m.table() == original and m.get('_process_handles_active') == 0 and
                          m.call('_process_handles_recover') == 0))
    m = Handles()
    original = m.table()
    assert m.begin([1, 3]) == 0
    m.uc.mem_write(m.address + 1, b'Z')
    cases.append(dict(case='foreign-JFT-change-errors-after-owned-restoration', passed=
                      m.call('_process_handles_recover') == 1 and m.table() == original and
                      m.get('_process_handles_active') == 0))
    report = dict(passed=all(c['passed'] for c in cases), cases=cases,
                  binary_sha256=sha(OUT / 'ASPECT.EXE'), checker_sha256=sha(Path(__file__)),
                  scope='Actual linked VM scope admission/retirement and partial JFT recovery. DOS vector/PSP services and VM entry are explicit boundaries; no full interpreter, EXEC or hardware claim.')
    (OUT / args.output).write_text(json.dumps(report, indent=2) + '\n')
    print('Unwind policy:', len(cases), 'cases', 'PASS' if report['passed'] else
          [c for c in cases if not c['passed']])
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
