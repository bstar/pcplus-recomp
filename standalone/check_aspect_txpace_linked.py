#!/usr/bin/env python3
"""Actual linked child pacing/calibration and transport admission instructions.
Only DOS/BIOS/UART inputs and tick edges are modeled; no service body is skipped.
"""
import json
import struct
from pathlib import Path
from unicorn.x86_const import *
import check_aspect_render_client as render

ROOT = render.q.ROOT


class Pacing(render.Client):
    def __init__(self, align_queue=False, cancel=False):
        self.clock_reads = self.units = 0
        self.step_address = None
        self.align_queue = align_queue
        self.cancel = cancel
        self.cancel_now = False
        self.phases = []
        super().__init__()

    def _code(self, uc, address, size, data):
        super()._code(uc, address, size, data)
        if address == self.symbols['_aspect_txpace_prepare']:
            sp = uc.reg_read(UC_X86_REG_SP)
            offset = struct.unpack('<H', uc.mem_read(self.data_base+sp+2, 2))[0]
            self.step_address = self.base+offset
        if address == self.step_address:
            sp = uc.reg_read(UC_X86_REG_SP)
            phase = struct.unpack('<H', uc.mem_read(self.data_base+sp+2, 2))[0]
            self.phases.append(phase)
            if phase == 1 and self.align_queue:
                self.put('uart_rx_count', 2049)
            if phase == 1 and self.cancel:
                self.cancel_now = True
        if address == self.symbols['_aspect_txpace_native_one']:
            self.units += 1
        if address == self.symbols['_aspect_txpace_ticks']:
            self.clock_reads += 1
            tick = 2 if self.units >= 8 else (1 if self.clock_reads >= 3 else 0)
            uc.mem_write(0x46c, struct.pack('<I', tick))

    def _interrupt(self, uc, number, data):
        if number == 0x16 and self.cancel_now:
            uc.reg_write(UC_X86_REG_AX, 0x011b)
            uc.reg_write(UC_X86_REG_EFLAGS, uc.reg_read(UC_X86_REG_EFLAGS)&~0x40)
            return
        return super()._interrupt(uc, number, data)


def main():
    cases = []
    for name, queued, align_queue, cancel, flags, result, native in (
        ('empty-ready', 0, False, False, 0x202, 0, 8),
        ('headroom-boundary', 2048, False, False, 0x202, 0, 8),
        ('admission-too-full', 2049, False, False, 0x202, 14, 0),
        ('alignment-consumes-headroom', 0, True, False, 0x202, 14, 0),
        ('alignment-cancel', 0, False, True, 0x202, 13, 0),
        ('IF0-before-hardware', 0, False, False, 2, 14, 0),
    ):
        machine = Pacing(align_queue, cancel)
        assert machine.open() == 0
        machine.put('uart_rx_count', queued)
        writes = list(machine.writes)
        value = machine.call('_runtime_serial_prepare_pacing', eflags=flags, limit=500000)
        assert value == result, (name, value, result, machine.units, machine.phases)
        assert machine.units == native, name
        assert machine.get('_runtime_error') == result
        assert machine.get('uart_rx_count') == (2049 if align_queue else queued)
        assert machine.writes == writes, 'Calibration must not change UART/PIC ownership'
        assert machine.uc.reg_read(UC_X86_REG_EFLAGS)&512 == flags&512
        assert machine.uc.reg_read(UC_X86_REG_DS) == machine.uc.reg_read(UC_X86_REG_SS) == machine.ds
        if not result:
            assert machine.call('_aspect_txpace_ready') == 1
            assert machine.get('_aspect_txpace_count') == 8*512//55
            assert machine.phases == [2, 1, 3]
        else:
            assert machine.get('_aspect_txpace_count') == 0
        cases.append(dict(name=name, passed=True, result=result,
                          native_units=native, callback_phases=machine.phases))
    report = dict(passed=True, binary_sha256=render.sha(render.q.BINARY),
                  checker_sha256=render.sha(Path(__file__)), cases=cases,
                  scope='Actual linked child calibration, native busyloop and transport admission. '
                  'Tick edges, queued count and BIOS Escape are explicit inputs. No product body '
                  'is skipped. Checks headroom during post-admission alignment, no dequeue, no '
                  'UART/PIC ownership writes, IF/DS=SS and typed failure. Physical timing and '
                  'sustained IRQ traffic require separate proofs.')
    out = ROOT / 'build/aspect-runner/txpace-linked-checks.json'
    out.write_text(json.dumps(report, indent=2)+'\n')
    print('Linked TXPACE:', len(cases), 'cases PASS')


if __name__ == '__main__':
    main()
