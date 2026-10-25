#!/usr/bin/env python3
"""Run the branded DOS terminal through an actual proxy against stock lab ENiGMA.

Run inside tools/dev, with the separate tools/bbs-dev stock ENiGMA already up.
All credentials and posts belong to that synthetic fixture. No live service
configuration is imported, changed or restarted.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import time

from enigma import process_pid, SOURCE
from product_inputs import ROOT, select_product, sha
from check_editor_dos import audit


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runtime', type=Path, required=True)
    p.add_argument('--terminal', type=Path, required=True)
    p.add_argument('--label', required=True)
    p.add_argument('--framing-ms', type=int, choices=[0,250], default=0)
    p.add_argument('--byte-delay-ms', type=int, choices=range(21), default=2)
    args = p.parse_args()
    assert re.fullmatch('[A-Za-z0-9_-]+', args.label)
    assert process_pid(), 'Start the owned stock ENiGMA fixture first'
    binary, sources = select_product(args.terminal, 'TERMINAL.EXE')
    before = {str(f.relative_to(ROOT)): sha(f) for f in sources}
    base = ROOT/'build/bbs-lab'
    bridge = base/(args.label+'-proxy')
    output = base/'results/enigma'/args.label
    assert not bridge.exists() and not output.exists(), 'Use a new result label'
    log_path = base/(args.label+'-harness.log')
    assert not log_path.exists()
    proc = subprocess.Popen(['node', str(ROOT/'lab/bbs/synthmodem_proxy_serial.js'),
        '--runtime', str(args.runtime.resolve()), '--output', str(bridge),
        '--framing-ms', str(args.framing_ms), '--byte-delay-ms', str(args.byte_delay_ms)],
        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    try:
        deadline = time.monotonic()+15
        while not (bridge/'ready.json').exists():
            assert proc.poll() is None, 'Proxy exited: '+proc.stderr.read()
            assert time.monotonic() < deadline, 'Proxy readiness timeout'
            time.sleep(.05)
        ready = json.loads((bridge/'ready.json').read_text())
        keys = 'p900 enter p2500 l o c enter '+json.loads(
            (ROOT/'lab/bbs/editor-recipes.json').read_text())['enigma_unsaved']['keyboard_input']
        command = [sys.executable, str(ROOT/'lab/bbs/editor_dos_probe.py'), str(binary),
            'enigma', '--port', str(ready['endpoint']['port']),
            '--server-log', str(SOURCE/'logs/enigma-bbs.log'), '--label', args.label,
            '--com', '3', '--baud', '19200', '--flow', 'HARD', '--dial-fixture',
            '--irq', '5', '--mouse-scales', '8', '4', '--cpu', '8086',
            '--timeout', '160', '--wait', '2', '--raw-upstream', '--keys', keys]
        with log_path.open('w') as log:
            run = subprocess.run(command, cwd=ROOT, stdout=log, stderr=log, timeout=175)
        # Audit even a failed harness when artifacts exist. A normal DOS return
        # cannot substitute for actual authentication and editor semantics.
        semantic = audit('enigma', args.label, disconnect=True)
        closed = json.loads((bridge/'1-closed.json').read_text())
        video = (output/'SCREEN.BIN').read_bytes()
        text = '\n'.join(video[i:i+160:2].decode('cp437') for i in range(0,4000,160))
        checks = dict(harness=run.returncode == 0, semantic_audit=semantic,
            exact_screen=len(video)==4000 and 'UNSAVED' in text and 'OVR 01,08' in text,
            proxy_source_unchanged=closed['source_unchanged'],
            product_source_unchanged=all(sha(ROOT/n)==h for n,h in before.items()))
        result = dict(passed=all(checks.values()), checks=checks,
            bridge=ready, command=command, binary_sha256=sha(binary),
            screen_sha256=sha(output/'SCREEN.BIN'), product_inputs=before,
            scope='Actual DOS8086 COM3/IRQ5 terminal, synthetic Hayes/nullmodem, '
                  'actual SynthModem proxy and stock loopback ENiGMA. '
                  'Explicit paced serial delivery; no SIP/DSP, physical CTS or analog acceptance.')
        (output/'proxy-integration.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result,indent=2))
        return 0 if result['passed'] else 1
    finally:
        proc.terminate()
        try: proc.communicate(timeout=5)
        except subprocess.TimeoutExpired: proc.kill(); proc.communicate()


if __name__ == '__main__':
    raise SystemExit(main())
