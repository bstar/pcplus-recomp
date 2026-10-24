#!/usr/bin/env python3
"""Authenticate, change width and navigate an isolated ENiGMA menu in real DOS."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

from enigma_peer_width_fixture import ROOT, PORT, owned, pid, verify
from product_inputs import select_product


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--terminal', type=Path, required=True)
    parser.add_argument('--label', required=True)
    parser.add_argument('--packet-delay-ms', type=int, choices=range(101), default=0,
                        help='Explicit byte-transparent modem batching experiment; default immediate')
    args = parser.parse_args()
    assert re.fullmatch(r'[A-Za-z0-9_-]+', args.label)
    candidate = owned(args.candidate)
    verify(candidate)
    assert pid(candidate), 'Start the owned fixture first'
    binary, product_sources = select_product(args.terminal, 'TERMINAL.EXE')
    output = ROOT / 'build/bbs-lab/results/enigma' / args.label
    wrapper = output.with_name(args.label + '-wrapper')
    assert not output.exists()
    wrapper.mkdir(exist_ok=False)
    event_file = candidate / 'logs/peer-width.jsonl'
    event_offset = event_file.stat().st_size if event_file.exists() else 0
    server_log = candidate / 'logs/enigma-bbs.log'
    log_offset = server_log.stat().st_size
    inputs = [binary, *product_sources, candidate / 'peer-width-instance.json',
              candidate / 'mods/pcplus_width/pcplus_width.js', candidate / 'config/config.hjson',
              candidate / 'config/menus/loc-main.hjson']
    inputs += [ROOT / 'lab/bbs' / n for n in ['enigma_peer_width_dos.py', 'enigma_peer_width_fixture.py',
               'peer_width_module.js', 'test_dos.py', 'editor_dos_probe.py', 'modem.py', 'editor-recipes.json']]
    before = {str(p.relative_to(ROOT)): sha(p) for p in inputs}
    canonical = json.loads((ROOT / 'lab/bbs/editor-recipes.json').read_text())['enigma_unsaved']['keyboard_input']
    prefix = canonical[:canonical.index('M enter')]
    manifest = json.loads((binary.parent / 'manifest.json').read_text())
    keys = ('p500 enter ' if manifest.get('special_edition') else '') + prefix
    keys += 'W I D T H enter p2500 right p1500 left p1500 n p1500 w p1500 q p2500 F enter p2000'
    command = [sys.executable, 'lab/bbs/editor_dos_probe.py', str(binary), 'enigma', '--port', str(PORT),
               '--server-log', str(server_log), '--label', args.label, '--keys', keys,
               '--wait', '1', '--timeout', '160', '--com', '2', '--baud', '19200', '--flow', 'HARD',
               '--dial-fixture', '--cpu', '8086', '--irq', '5', '--mouse-scales', '8', '4']
    command += ['--packet-delay-ms', str(args.packet_delay_ms)]
    (wrapper / 'command.json').write_text(json.dumps(command, indent=2) + '\n')
    with (wrapper / 'harness.log').open('w') as log:
        code = subprocess.call(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
    events_raw = event_file.read_bytes()[event_offset:] if event_file.exists() else b''
    (wrapper / 'peer-width.jsonl').write_bytes(events_raw)
    events = [json.loads(line) for line in events_raw.splitlines()]
    log_raw = server_log.read_bytes()[log_offset:]
    (wrapper / 'server-session.jsonl').write_bytes(log_raw)
    logs = [json.loads(line) for line in log_raw.splitlines()]
    result = json.loads((output / 'result.json').read_text()) if (output / 'result.json').exists() else {}
    cprs = [e['args'] for e in events if e['kind'] == 'cpr']
    paints = [(e['width'], e['selection']) for e in events if e['kind'] == 'paint']
    chunks = [bytes.fromhex(e['hex']) for e in events if e['kind'] == 'tcp_input']
    stream = b''.join(chunks)
    expected_stream = (b'\x1b[2;128R\x1b[C\x1b[2;128R\x1b[D\x1b[2;128Rn' +
                       b'\x1b[2;80Rw\x1b[2;128Rq')
    wire = (output / 'serial-received.bin').read_bytes() if (output / 'serial-received.bin').exists() else b''
    checks = dict(harness=code == 0 and result.get('passed', False),
                  authenticated=any(e['kind'] == 'enter' and e['user'] == 'loclab' for e in events),
                  exact_width_navigation=paints == [(132, 0), (132, 1), (132, 0), (80, 0), (132, 0)],
                  actual_server_CPR=cprs == [[2, 128], [2, 128], [2, 128], [2, 80], [2, 128]],
                  expected_CPR=all(e['args'] == e['expected'] for e in events if e['kind'] == 'cpr'),
                  UART_CPR=wire.count(b'\x1b[2;128R') == 4 and wire.count(b'\x1b[2;80R') == 1,
                  returned_to_main=any(e['kind'] == 'return' for e in events),
                  subsequent_file_menu=any(e.get('menuName') == 'fileBaseMainMenu' for e in logs),
                  exact_server_input=stream == expected_stream,
                  immutable_inputs=before == {str(p.relative_to(ROOT)): sha(p) for p in inputs})
    verify(candidate)
    report = dict(passed=all(checks.values()), checks=checks, binary_sha256=sha(binary),
                  inputs=before, paints=paints, cprs=cprs, modem_packet_delay_ms=args.packet_delay_ms,
                  server_input_chunks=[c.hex() for c in chunks],
                  artifacts={str(p.relative_to(ROOT)): sha(p) for p in [*output.glob('*'), *wrapper.glob('*')] if p.is_file()},
                  scope='Authenticated normal ENiGMA menu stack with explicit synthetic width menu; source-built DOS8086 UART replies and real arrow keys; modeled Hayes/Telnet transport. No physical, stock-menu-width or ASPECT ownership claim.')
    (wrapper / 'checks.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(passed=report['passed'], checks=checks, paints=paints, cprs=cprs), indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
