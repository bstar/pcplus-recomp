#!/usr/bin/env python3
"""Generated KBDs against actual linked default builder and keyboard/UART paths."""
import hashlib
import json
from pathlib import Path
from build_keyboard_profiles import OUT, OVERRIDES, PROFILE_SIZE, profiles
from check_transport import BINARY, Transport


def main():
    files = profiles()
    model = Transport()
    default = bytes(model.uc.mem_read(model.symbols['terminal_keymap'], PROFILE_SIZE))
    assert files['NETWORK.KBD'] == default * 7
    expected = bytearray(default)
    for slot, value in OVERRIDES.items():
        expected[slot*12:(slot+1)*12] = value.ljust(12, b'\0')
    assert files['ENIGMA.KBD'] == bytes(expected)*7
    cases = []
    # Physical keys, including both BIOS navigation banks, use the real linked
    # normalizer, classifier, dispatcher, TX ring and UART sender.
    keys = [(0x4700, b'\x01'), (0x47e0, b'\x01'),
            (0x4f00, b'\x05'), (0x4fe0, b'\x05'),
            (0x5200, b'\x16'), (0x52e0, b'\x16'),
            (0x4800, b'\x1b[A'), (0x50e0, b'\x1b[B'),
            (0x4b00, b'\x1b[D'), (0x4de0, b'\x1b[C'),
            (0x5300, b'\x1b[3~'), (0x53e0, b'\x1b[3~'),
            (0x4900, b'\x1b[5~'), (0x51e0, b'\x1b[6~'),
            (9, b'\t'), (13, b'\r')]
    for profile in (4, 6):
        for key, wire in keys:
            m = Transport([key])
            m.put('csi_terminal_id', profile)
            m.uc.mem_write(m.symbols['terminal_keymap'], files['ENIGMA.KBD'][profile*948:(profile+1)*948])
            m.call('terminal_poll_io')
            m.drain()
            assert bytes(m.tx) == wire and not m.get('terminal_quit'), (profile, key, bytes(m.tx), wire)
            cases.append(dict(profile=profile, bios_key=hex(key), wire=wire.hex(), passed=True))
    result = dict(passed=True, cases=cases, binary_sha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),
                  kbd_sha256={name: hashlib.sha256(data).hexdigest() for name, data in files.items()},
                  sources={str(p.relative_to(Path(__file__).resolve().parents[1])):
                           hashlib.sha256(p.read_bytes()).hexdigest() for p in
                           [Path(__file__).resolve(), Path(__file__).with_name('build_keyboard_profiles.py')]},
                  scope='Generated defaults match actual linked builder; 32 physical-key inputs through actual linked BIOS normalization, keyboard mapping and UART transmit. BIOS/ports modeled; explicit KBD DOS import and stock editor behavior tested separately.')
    (OUT/'checks.json').write_text(json.dumps(result, indent=2)+'\n')
    print('Keyboard profiles passed:', len(cases), 'linked inputs')


if __name__ == '__main__':
    main()
