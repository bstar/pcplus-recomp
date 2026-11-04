#!/usr/bin/env python3
"""Actual DOS8086 Screen Pause, incoming data, any-key resume and timer video."""
import argparse
import hashlib
import json
import re
import struct
import subprocess
from pathlib import Path
import test_connection_dos as harness
from modem_fixtures import fixture

ROOT = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--terminal', type=Path, required=True)
p.add_argument('--label', required=True)
a = p.parse_args()
assert re.fullmatch('[a-z0-9-]+', a.label)
binary = a.terminal.resolve()
assert binary.is_relative_to(ROOT / 'build')
out = ROOT / 'build/screen-pause-dos' / a.label
out.mkdir(parents=True, exist_ok=False)
watcher = out / 'PAUSEW.COM'
subprocess.run(['nasm', '-fbin', str(ROOT / 'standalone/pause_watch.asm'), '-o', str(watcher)], check=True)
harness.BINARY = binary
raw = bytearray(fixture(timeout=5))
struct.pack_into('<HH', raw, 0, 2, 5)
struct.pack_into('<H', raw, 0x178, 0x3e8)
struct.pack_into('<H', raw, 0x188, 5)
struct.pack_into('<HH', raw, 0x4e4, 8, 4)
struct.pack_into('<HH', raw, 0x1bc, 0, 0)
struct.pack_into('<H', raw, 0x1e6, 0)
banner = b'\x1b[2J\x1b[HFIRST BYTE SAFE\x1b[6n\x1b[0c'
cases = []
for mode, resume in (('direct', 'x'), ('reference', 'a-x'), ('partial-parser', 'escape')):
    name = a.label + '-' + mode
    assert not (ROOT / 'build/connection-dos' / name).exists()
    pause = ('a-z p200 ' if mode == 'reference' else '') + 'a-n'
    prefix = 'p900 enter p5000 '
    triggers = []
    if mode == 'partial-parser':
        prefix += 'd i r t y p200 '
        triggers.append((b'dirty', ((0, b'\x1b['), (.8, b'7;1H'))))
    triggers += [(b'\x13', b'\x1b[8;1HQUEUED\x1b[6n'), (b'\x11', banner)]
    keys = prefix + pause + ' p2500 ' + resume + ' p1500 r e a d y enter p2000 a-x'
    result = harness.run(name, 'success', keys, prm=bytes(raw), com=3, irq=5, cpu='8086', working_drive='d',
                         arguments='@D:\\TEST.PRM /D:CaseTest:23 /I:3', timeout=35,
                         files={'PAUSEW.COM': watcher.read_bytes()}, observer='PAUSEW',
                         online_triggers=tuple(triggers))
    assert result['passed'], result
    folder = ROOT / 'build/connection-dos' / name
    frames = (folder / 'PAUSE.BIN').read_bytes()
    assert len(frames) == 8000 and frames[:4000] == frames[4000:]
    assert b'Screen paused.' in frames[3840:4000:2]
    assert b'QUEUED' not in frames[::2], 'Incoming text rendered before resume'
    wire = (folder / 'serial.bin').read_bytes()
    assert wire.count(b'\x13') == wire.count(b'\x11') == 1
    assert re.findall(rb'\x1b\[\d+;\d+R', wire) == [b'\x1b[1;16R', b'\x1b[8;7R', b'\x1b[1;16R']
    assert wire.index(b'\x11') < wire.index(b'\x1b[8;7R') and wire.count(b'ready\r') == 1
    assert b'x' not in wire, 'Resume key escaped to the wire'
    cases.append(dict(case=mode, passed=True, result=str((folder / 'result.json').relative_to(ROOT)),
                      observed_video_sha256=hashlib.sha256(frames).hexdigest()))
report = dict(passed=True, terminal_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(), cases=cases,
              scope=__doc__ + ' Synthetic Hayes/UART peer on COM3/IRQ5; no SIP/DSP/analog or physical throughput acceptance.')
(out / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
print('PASS actual DOS Screen Pause:', len(cases), 'workflows')
