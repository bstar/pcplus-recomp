#!/usr/bin/env python3
"""Actual DOS width/arrow navigation against a private Synchronet shell fixture."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

from synchronet_peer_width_fixture import ROOT, PORT, owned, pid, verify
from product_inputs import select_product


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--terminal', type=Path, required=True)
    parser.add_argument('--label', required=True)
    args = parser.parse_args()
    assert re.fullmatch(r'[A-Za-z0-9_-]+', args.label)
    candidate = owned(args.candidate)
    verify(candidate)
    assert pid(candidate)
    binary, product_sources = select_product(args.terminal, 'TERMINAL.EXE')
    output = ROOT / 'build/bbs-lab/results/synchronet' / args.label
    wrapper = output.with_name(args.label + '-wrapper')
    assert not output.exists()
    wrapper.mkdir(exist_ok=False)
    event_file = candidate / 'data/peer-width.jsonl'
    event_offset = event_file.stat().st_size if event_file.exists() else 0
    server_log = candidate / 'instance.log'
    log_offset = server_log.stat().st_size
    metadata = json.loads((candidate / 'peer-width-instance.json').read_text())
    inputs = [binary, *product_sources, candidate / 'peer-width-instance.json']
    inputs += [candidate / n for n in metadata['fixture_inputs']]
    inputs += [ROOT / 'lab/bbs' / n for n in ['synchronet_peer_width_dos.py', 'synchronet_peer_width_fixture.py',
               'synchronet_peer_width_module.js', 'test_dos.py', 'editor_dos_probe.py', 'modem.py']]
    before = {str(p.relative_to(ROOT)): sha(p) for p in inputs}
    manifest = json.loads((binary.parent / 'manifest.json').read_text())
    keys = ('p500 enter ' if manifest.get('special_edition') else '')
    keys += ('p13000 L A B U S E R enter p2000 L A B P A S S 4 2 enter '
             'p8000 space p3000 Q enter p5000 space p4000 '
             'right p1500 left p1500 n p1500 w p1500 q p4000 space p4000 T p3000')
    command = [sys.executable, 'lab/bbs/editor_dos_probe.py', str(binary), 'synchronet', '--port', str(PORT),
               '--label', args.label, '--keys', keys, '--wait', '1', '--timeout', '120',
               '--com', '2', '--baud', '19200', '--flow', 'HARD', '--dial-fixture', '--cpu', '8086',
               '--irq', '5', '--mouse-scales', '8', '4']
    (wrapper / 'command.json').write_text(json.dumps(command, indent=2) + '\n')
    with (wrapper / 'harness.log').open('w') as log:
        code = subprocess.call(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
    raw = event_file.read_bytes()[event_offset:] if event_file.exists() else b''
    (wrapper / 'peer-width.jsonl').write_bytes(raw)
    events = [json.loads(line) for line in raw.splitlines()]
    server_raw = server_log.read_bytes()[log_offset:]
    (wrapper / 'server-session.log').write_bytes(server_raw)
    result = json.loads((output / 'result.json').read_text()) if (output / 'result.json').exists() else {}
    cprs = [e['position'] for e in events if e['kind'] == 'cpr']
    paints = [(e['width'], e['selection']) for e in events if e['kind'] == 'paint']
    wire = (output / 'serial-received.bin').read_bytes() if (output / 'serial-received.bin').exists() else b''
    display = (output / 'display.bin').read_bytes() if (output / 'display.bin').exists() else b''
    screen = (output / 'screen.txt').read_text() if (output / 'screen.txt').exists() else ''
    checks = dict(harness=code == 0 and result.get('passed', False),
                  authenticated=any(e['kind'] == 'enter' and e['user'] == 'LABUSER' for e in events),
                  exact_width_navigation=paints == [(132, 0), (132, 1), (132, 0), (80, 0), (132, 0)],
                  actual_server_CPR=cprs == [dict(x=128, y=2)] * 3 + [dict(x=80, y=2), dict(x=128, y=2)],
                  UART_CPR=wire.count(b'\x1b[2;128R') == 4 and wire.count(b'\x1b[2;80R') == 1,
                  returned_online=any(e['kind'] == 'return' and e['online'] for e in events),
                  stock_file_menu=(str(candidate / 'text/menu/transfer.').encode() in server_raw),
                  final_file_prompt='■ File ■' in screen,
                  immutable_inputs=before == {str(p.relative_to(ROOT)): sha(p) for p in inputs})
    verify(candidate)
    report = dict(passed=all(checks.values()), checks=checks, binary_sha256=sha(binary),
                  inputs=before, paints=paints, cprs=cprs, modem_packet_delay_ms=0,
                  artifacts={str(p.relative_to(ROOT)): sha(p) for p in [*output.glob('*'), *wrapper.glob('*')] if p.is_file()},
                  scope='Actual DOS8086 against private official Synchronet runtime with explicit synthetic command-shell wrapper; native server getxy/key parser and stock shell on return; immediate modeled Hayes/Telnet transport; no physical or full application claim.')
    (wrapper / 'checks.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(passed=report['passed'], checks=checks, paints=paints, cprs=cprs), indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
