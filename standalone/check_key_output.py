#!/usr/bin/env python3
"""Execute linked key-binding output, actual TX ring and UART instructions."""
import hashlib
import json
from pathlib import Path
from unicorn.x86_const import UC_X86_REG_BP, UC_X86_REG_SI, UC_X86_REG_DI, UC_X86_REG_ES
from check_transport import Transport, BINARY, ROOT


def main():
    cases = []

    def result(name, inputs):
        cases.append({'case': name, 'inputs': inputs, 'passed': True})

    def binding(machine, slot, data):
        assert len(data) <= 12
        machine.uc.mem_write(machine.symbols['terminal_keymap'] + slot * 12, data.ljust(12, b'\0'))

    def emit(machine, slot):
        status = machine.call('terminal_enqueue_key_slot', ax=slot)
        for register, value in ((UC_X86_REG_BP, 0xbabe), (UC_X86_REG_SI, 0x1234),
                                (UC_X86_REG_DI, 0x5678), (UC_X86_REG_ES, 0xb800)):
            assert machine.uc.reg_read(register) == value
        return status

    for slot in range(79):
        machine = Transport()
        data = bytes(0xff if i == 2 else 33 + (slot + i) % 90 for i in range(slot % 12))
        binding(machine, slot, data)
        assert emit(machine, slot) == 0
        machine.drain()
        assert bytes(machine.tx) == data.replace(b'\xff', b'\0')
    result('all79-slots-empty-through11-bytes-and-FF-to-wire-NUL', 79)

    for slot in (79, 80, 255, 32767, 65535):
        machine = Transport()
        assert emit(machine, slot) == 2
        assert (machine.get('terminal_quit'), machine.get('terminal_exit_code')) == (1, 4)
        assert not machine.tx and machine.get('terminal_tx_count') == 0
    for slot in (0, 1, 78):
        machine = Transport()
        binding(machine, slot, b'X' * 12)
        assert emit(machine, slot) == 3
        assert (machine.get('terminal_quit'), machine.get('terminal_exit_code')) == (1, 4)
        assert not machine.tx and machine.get('terminal_tx_count') == 0
    result('invalid-slot-and-unterminated-binding-no-partial-queue-or-wire', 8)

    machine = Transport()
    machine.enqueue(b'A' * 1020)
    binding(machine, 78, b'B\xffCD')
    assert emit(machine, 78) == 0 and machine.get('terminal_tx_count') == 1024
    machine.drain()
    assert bytes(machine.tx) == b'A' * 1020 + b'B\0CD'
    machine = Transport()
    machine.enqueue(b'A' * 1021)
    binding(machine, 0, b'B\xffCD')
    tail = machine.get('terminal_tx_tail')
    assert emit(machine, 0) == 4
    assert machine.get('terminal_tx_count') == 1021 and machine.get('terminal_tx_tail') == tail
    assert machine.get('terminal_exit_code') == 3 and not machine.tx
    result('exact-capacity-with-binary-NUL-and-whole-binding-overflow-atomicity', 2)

    machine = Transport()
    machine.enqueue(b'A' * 600)
    for _ in range(598):
        machine.call('terminal_poll_io')
    binding(machine, 4, b'Z' * 11)
    assert emit(machine, 4) == 0
    machine.drain()
    assert bytes(machine.tx) == b'A' * 600 + b'Z' * 11
    machine = Transport()
    machine.put('terminal_quit', 1)
    machine.put('terminal_exit_code', 7)
    assert emit(machine, 0) == 5 and machine.get('terminal_exit_code') == 7
    assert not machine.tx and not machine.get('terminal_tx_count')
    result('ring-progress-and-existing-stop-preservation', 2)

    proof = {'passed': True, 'binary_sha256': hashlib.sha256(BINARY.read_bytes()).hexdigest(),
             'inputs': sum(case['inputs'] for case in cases), 'cases': cases,
             'scope': 'Actual linked bounded key-slot sender, TX ring and recovered UART code. Hardware model only; no key-selection/default-profile or physical-modem claim.'}
    (ROOT / 'build/terminal/key-output-checks.json').write_text(json.dumps(proof, indent=2) + '\n')
    print(json.dumps(proof, indent=2))


if __name__ == '__main__':
    main()
