#!/usr/bin/env python3
"""Linked foreground delay ownership, native receive and cancellation checks.

The scalar parent endpoint is modeled, without a parser or query recognizer.
Actual DOS query, WHEN flow and elapsed-delay evidence is checked separately.
"""
import json
from pathlib import Path
from unicorn.x86_const import *
import check_aspect_render_client as client


class Keyboard(client.Client):
    def __init__(self, key=None):
        self.key = key
        self.frozen_clock = False
        super().__init__()

    def _code(self, uc, address, size, extra):
        super()._code(uc, address, size, extra)
        if self.frozen_clock and address == self.symbols['_aspect_serial_ticks']:
            uc.mem_write(0x46c, bytes(4))

    def _interrupt(self, uc, number, extra):
        if number == 0x16:
            function = uc.reg_read(UC_X86_REG_AX) >> 8
            assert function in (0, 1, 16, 17), function
            flags = uc.reg_read(UC_X86_REG_EFLAGS)
            if function in (1, 17):
                uc.reg_write(UC_X86_REG_EFLAGS,
                             flags | 0x40 if self.key is None else flags & ~0x40)
                if self.key is not None:
                    uc.reg_write(UC_X86_REG_AX, self.key)
            else:
                assert self.key is not None
                uc.reg_write(UC_X86_REG_AX, self.key)
                self.key = None
            return
        return super()._interrupt(uc, number, extra)


def poll(machine):
    result = machine.call('_runtime_when_delay_poll')
    assert machine.uc.reg_read(UC_X86_REG_SP) == 0xdfc0
    assert machine.uc.reg_read(UC_X86_REG_DS) == machine.uc.reg_read(UC_X86_REG_SS) == machine.ds
    return result


def main():
    cases = []
    for echo in (0, 1):
        machine = Keyboard()
        assert machine.open() == 0
        machine.call('_runtime_receive_reset')
        machine.put('_runtime_receive_display', echo)
        table = machine.symbols['_runtime_receive_translation_table']
        machine.uc.mem_write(table + ord('a'), b'b')
        machine.receive_irq(b'aC')
        machine.requests.clear()
        assert poll(machine) == 0
        assert machine.get('uart_rx_count') == 1
        assert machine.requests == ([(1, ord('b'))] if echo else [])
        assert poll(machine) == 0
        assert machine.get('uart_rx_count') == 0
        assert machine.requests == ([(1, ord('b')), (1, ord('C'))] if echo else [])
        before = machine.requests[:]
        assert poll(machine) == 0 and machine.requests == before
        cases.append(dict(name='one-native-mapped-lead-per-poll-display-' + str(echo), passed=True))
    for enter in ('_runtime_when_defer_begin', '_runtime_when_monitor_begin'):
        machine = Keyboard()
        assert machine.open() == 0
        machine.receive_irq(b'Q')
        machine.requests.clear()
        machine.call(enter)
        writes = len(machine.writes)
        assert poll(machine) == 1
        assert machine.get('_runtime_error') == 10
        assert machine.get('uart_rx_count') == 1 and machine.requests == []
        assert len(machine.writes) == writes
        cases.append(dict(name='reject-nested-' + enter, passed=True))
    machine = Keyboard()
    assert poll(machine) == 1
    assert machine.get('_runtime_error') == 10 and machine.requests == [] and not machine.writes
    cases.append(dict(name='reject-unattached-before-hardware', passed=True))
    machine = Keyboard()
    assert machine.open() == 0 and machine.call('_aspect_serial_close') == 0
    machine.requests.clear()
    writes = len(machine.writes)
    assert poll(machine) == 1
    assert machine.get('_runtime_error') == 14 and not machine.requests and len(machine.writes) == writes
    cases.append(dict(name='reject-closed-UART-before-device-or-parent-use', passed=True))
    machine = Keyboard()
    assert machine.open() == 0
    machine.call('_runtime_receive_reset')
    machine.receive_irq(b'A' * 65)
    machine.requests.clear()
    machine.frozen_clock = True
    assert poll(machine) == 0
    assert machine.get('uart_rx_count') == 1 and machine.requests == [(1,65)] * 64
    cases.append(dict(name='64-lead-bound-even-with-frozen-clock', passed=True))
    machine = Keyboard()
    assert machine.open() == 0
    machine.call('_runtime_receive_reset')
    machine.receive_irq(b'AB')
    machine.tick = 1573038
    assert poll(machine) == 0
    assert machine.get('uart_rx_count') == 1
    cases.append(dict(name='BIOS-midnight-tick-wrap-still-bounds-burst', passed=True))
    machine = Keyboard(0x011b)
    assert machine.open() == 0
    machine.receive_irq(b'Q')
    machine.requests.clear()
    assert poll(machine) == 1
    assert machine.get('_runtime_error') == 13 and machine.key is None
    assert machine.get('uart_rx_count') == 1 and machine.requests == []
    cases.append(dict(name='Escape-cancels-before-receive', passed=True))
    machine = Keyboard()
    assert machine.open() == 0 and machine.call('_aspect_render_finish') == 0
    machine.receive_irq(b'ABC')
    machine.requests.clear()
    assert machine.call('_runtime_serial_wait_second') == 0
    assert machine.get('uart_rx_count') == 3 and not machine.requests
    cases.append(dict(name='unattached-serial-second-retains-raw-RX', passed=True))
    output = client.q.ROOT / 'build/aspect-foreground-delay'
    output.mkdir(exist_ok=True)
    report = dict(passed=True, cases=cases, runner_sha256=client.sha(client.q.BINARY),
                  checker_sha256=client.sha(Path(__file__)),
                  reused_fixture_sha256=client.sha(Path(client.__file__)), scope=__doc__)
    (output / 'checks.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Foreground delay', len(cases), 'linked cases PASS')


if __name__ == '__main__':
    main()
