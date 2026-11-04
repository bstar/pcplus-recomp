#!/usr/bin/env python3
"""Validate pause service calls/relocations and reject unexecuted corruptions."""
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
m = DosImage(a.terminal, mapping)
header = struct.unpack_from('<14H', m.image)
start = header[4] * 16
relocations = {seg * 16 + off for off, seg in (struct.unpack_from('<HH', m.image, header[12] + 4 * i) for i in range(header[3]))}


def inspect(path):
    layout = inspect_terminal_memory(path, mapping)
    assert layout['screen_pause_bridge_pairs_verified'] == 4
    image = path.read_bytes()
    first = m.symbols['terminal_screen_pause'] - m.base
    end = m.symbols['terminal_screen_pause_end'] - m.base
    body = image[start + first:start + end]
    sites = []
    for name, expected in (('terminal_pause_flow_far', 2), ('terminal_pause_poll_far', 1),
                           ('terminal_pause_peek_far', 1), ('terminal_pause_read_far', 1), ('terminal_pause_notice_flush_far', 1)):
        at = m.symbols[name] - m.code_base
        pattern = b'\x9a' + struct.pack('<HH', at, m.code_segment - m.base_segment)
        calls = [first + i for i in range(len(body) - 4) if body[i:i + 5] == pattern]
        assert len(calls) == expected and all(i + 3 in relocations for i in calls), name
        sites.extend((name + '-' + str(n), i) for n, i in enumerate(calls))
    return sites


sites = inspect(a.terminal)
mutations = [(name, start + address + 1) for name, address in sites]
mutations += [(name, start + m.symbols[name] - m.base) for name in
              ('terminal_pause_flow_far', 'terminal_pause_poll_far', 'terminal_pause_peek_far', 'terminal_pause_read_far')]
cases = []
for name, at in mutations:
    damaged = bytearray(m.image)
    damaged[at] ^= 0x40
    path = a.output / (name + '.bad')
    path.write_bytes(damaged)
    try:
        inspect(path)
    except AssertionError:
        cases.append(dict(case=name, rejected=True))
    else:
        raise AssertionError('Accepted damaged pause ABI: ' + name)
report = dict(passed=True, terminal_sha256=hashlib.sha256(m.image).hexdigest(), cases=cases, scope=__doc__)
(a.output / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
print('PASS pause ABI; six far calls, four adapters,', len(cases), 'corrupted images rejected')
