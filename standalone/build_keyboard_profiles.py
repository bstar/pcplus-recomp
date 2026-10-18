#!/usr/bin/env python3
"""Source-owned optional KBD files; no original factory keyboard data."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/keyboard-profiles'
PROFILE_SIZE = 948
SLOT_SIZE = 12
OVERRIDES = {8: b'\x16', 54: b'\x16', 56: b'\x01', 76: b'\x01',
             57: b'\x05', 77: b'\x05'}


def profiles():
    OUT.mkdir(parents=True, exist_ok=True)
    source = ROOT / 'src/terminal/key_configuration.asm'
    text = source.read_text()
    assert text.count('keyboard_network_defaults:\n') == 1
    # Assemble the actual maintained db declarations instead of copying a second
    # default table or trying to interpret assembly literals in Python.
    asm = OUT / 'defaults.asm'
    raw = OUT / 'defaults.bin'
    asm.write_text('BITS 16\n' + text.split('keyboard_network_defaults:\n', 1)[1])
    subprocess.run(['nasm', '-f', 'bin', str(asm), '-o', str(raw)], check=True)
    table = bytearray(PROFILE_SIZE)
    encoded = raw.read_bytes()
    position = 0
    seen = set()
    while encoded[position] != 255:
        slot = encoded[position]
        position += 1
        assert slot < 79 and slot not in seen
        seen.add(slot)
        end = encoded.index(0, position)
        binding = encoded[position:end]
        assert len(binding) < SLOT_SIZE
        table[slot*SLOT_SIZE:slot*SLOT_SIZE+len(binding)] = binding
        position = end + 1
    assert position == len(encoded) - 1 and len(seen) == 79
    enigma = bytearray(table)
    for slot, binding in OVERRIDES.items():
        enigma[slot*SLOT_SIZE:(slot+1)*SLOT_SIZE] = binding.ljust(SLOT_SIZE, b'\0')
    # The loader selects zero-based profile 4 or 6 in the supported terminal.
    # Populate indices 0..6 without claiming support for other emulations.
    return {'NETWORK.KBD': bytes(table)*7, 'ENIGMA.KBD': bytes(enigma)*7}


def main():
    files = profiles()
    for name, contents in files.items():
        (OUT / name).write_bytes(contents)
    inputs = [ROOT/'src/terminal/key_configuration.asm', Path(__file__).resolve()]
    report = dict(outputs={name: hashlib.sha256(data).hexdigest() for name, data in files.items()},
                  sources={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in inputs},
                  enigma_overrides={str(slot): data.hex() for slot, data in OVERRIDES.items()},
                  scope='Source-owned network defaults and opt-in ENiGMA editor Home/End/Insert control bindings. Seven native 948-byte blocks, for supported profiles 4/6. No original KBD data or universal BBS compatibility claim.')
    (OUT/'manifest.json').write_text(json.dumps(report, indent=2)+'\n')
    print('Built', ', '.join(files))


if __name__ == '__main__':
    main()
