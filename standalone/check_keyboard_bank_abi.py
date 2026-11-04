#!/usr/bin/env python3
"""Check keyboard near/far bridges and reject corrupted, never-executed images."""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from dos_image import DosImage
from terminal_memory import inspect_terminal_memory

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--terminal', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
a.output.mkdir(parents=True, exist_ok=False)
mapping = a.terminal.parent / 'terminal.map'
layout = inspect_terminal_memory(a.terminal, mapping)
assert layout['keyboard_bank_bridge_pairs_verified'] == 29
m = DosImage(a.terminal, mapping)
start = struct.unpack_from('<14H', m.image)[4] * 16
contract = Path(__file__).resolve().parents[1] / 'src/terminal/keyboard_bank_targets.json'
mutations = [(name, m.symbols['keyboard_bank_' + name])
             for name in json.loads(contract.read_text())['targets']]
mutations.append(('bank-return', m.symbols['terminal_keyboard_dispatch_end'] - 1))
# The validated resident caller must keep its relocated far bank entry.
relative = m.symbols['terminal_keyboard_dispatch_far'] - m.base
pattern = b'\x9a' + struct.pack('<HH', relative % 16, relative // 16)
root = next(c for c in layout['code_segments'] if c['name'] == '_TEXT')
body = m.image[start:start + root['bytes']]
at = body.find(pattern)
assert at >= 0 and body.find(pattern, at + 1) == -1
mutations.append(('resident-dispatch', m.base + at))
cases = []
for name, address in mutations:
    damaged = bytearray(m.image)
    damaged[start + address - m.base] = 0x90
    path = a.output / (name + '.bad')
    path.write_bytes(damaged)
    try:
        inspect_terminal_memory(path, mapping)
    except AssertionError:
        cases.append(dict(case=name, rejected=True))
    else:
        raise AssertionError('Accepted damaged ABI: ' + name)
report = dict(passed=True, terminal_sha256=hashlib.sha256(m.image).hexdigest(),
              cases=cases, scope=__doc__)
(a.output / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
print('PASS keyboard bank ABI;', len(cases), 'corrupted images rejected')
