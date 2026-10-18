#!/usr/bin/env python3
"""Execute BIOS acquisition, raw classification, binding and UART as one path."""
import hashlib
import json
from check_transport import Transport, ROOT, BINARY


def main():
    vectors = {0: 0x372a, 1: 0x4a2d, 2: 0x4e2b, 3: 0x532e, 4: 0xe02f,
               5: 0xe00d, 6: 0x0f09, 7: 0x0f00, 8: 0x5200, 9: 0x5300,
               10: 0x0e08, 11: 0x7700, 12: 0x7500, 13: 0x4900, 14: 0x5100,
               15: 0x0e7f, 72: 0x4800, 73: 0x5000, 74: 0x4b00, 75: 0x4d00,
               76: 0x4700, 77: 0x4f00, 78: 0x1c0d}
    for slot, scan in enumerate((0x52, 0x4f, 0x50, 0x51, 0x4b, 0x4c, 0x4d, 0x47, 0x48, 0x49), 28):
        vectors[slot] = (scan << 8) | (48 + slot - 28)
    for slot, scan in enumerate((0x48, 0x50, 0x4b, 0x4d, 0x52, 0x53, 0x47, 0x4f, 0x49, 0x51), 50):
        vectors[slot] = (scan << 8) | 0xe0
    for first, slot in ((0x3b, 16), (0x54, 38), (0x5e, 60)):
        vectors.update({slot + i: (first + i) << 8 for i in range(10)})
    vectors.update({26: 0x8500, 27: 0x8600, 48: 0x8700, 49: 0x8800, 70: 0x8900, 71: 0x8a00})
    assert set(vectors) == set(range(79))
    for slot, word in vectors.items():
        machine = Transport([word])
        value = f'SLOT{slot:02}'.encode() + b'\xff'
        machine.uc.mem_write(machine.symbols['terminal_keymap'] + slot * 12, value.ljust(12, b'\0'))
        machine.call('terminal_poll_io')
        machine.drain()
        assert bytes(machine.tx) == value[:-1] + b'\0', (slot, hex(word), bytes(machine.tx))
        assert not machine.keys and not machine.get('terminal_quit')

    for selection in (0, 1, 2):
        for bda in (0, 0x10, 0xef, 0xff):
            machine = Transport()
            machine.put('terminal_keyboard_bios_selection', selection)
            machine.uc.mem_write(0x496, bytes([bda]))
            want = 0x10 if selection == 1 or (selection == 2 and bda & 0x10) else 0
            assert machine.call('terminal_select_keyboard_bios') == want
            assert machine.get('keyboard_bios_mode', 1) == want
            assert not machine.keyboard_calls and not machine.tx

    for raw, slot in ((0x1ce0, 5), (0x35e0, 4)):
        machine = Transport([raw])
        machine.uc.mem_write(machine.symbols['terminal_keymap'] + slot * 12, b'ALIAS\0')
        machine.call('terminal_poll_io'); machine.drain()
        assert bytes(machine.tx) == b'ALIAS'

    for raw in (0x49e0, 0x51e0):
        machine = Transport([raw])
        slot = 58 if raw == 0x49e0 else 59
        machine.uc.mem_write(machine.symbols['terminal_keymap'] + slot * 12, bytes(12))
        machine.call('terminal_poll_io')
        assert machine.get('terminal_exit_code') == 4 and machine.get('terminal_quit') == 1
        assert not machine.tx and not machine.get('terminal_tx_count')

    proof = {'passed': True, 'binary_sha256': hashlib.sha256(BINARY.read_bytes()).hexdigest(),
             'cases': [{'case': 'all79-raw-keys-overridden-binding-and-wire-NUL', 'inputs': 79, 'passed': True},
                       {'case': 'AUTO-STANDARD-ENHANCED-BDA-selection', 'inputs': 12, 'passed': True},
                       {'case': 'alternate-keypad-representations-use-keypad-bindings', 'inputs': 2, 'passed': True},
                       {'case': 'empty-enhanced-page-binding-retains-local-action-boundary', 'inputs': 2, 'passed': True}],
             'scope': 'Actual linked BIOS acquisition/normalization, raw classifier, binding sender, TX ring and UART. Only hardware keyboard/ports/BDA modeled; no routine substituted.'}
    (ROOT / 'build/terminal/key-live-checks.json').write_text(json.dumps(proof, indent=2) + '\n')
    print(json.dumps(proof, indent=2))


if __name__ == '__main__':
    main()
