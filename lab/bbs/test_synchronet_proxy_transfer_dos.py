#!/usr/bin/env python3
"""Actual source DOS parent -> SynthModem Telnet proxy -> owned stock Synchronet.

The stock BBS helper owns ZMODEM. No SIP/audio, physical modem or UART timing
claim; fixtures and captures remain under ignored build storage.
"""
import argparse
import fcntl
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import time
from product_inputs import ROOT, select_product, sha
from synchronet import RUNTIME, LAB, COMMIT
from synchronet_transfer import AREA


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runtime', type=Path, required=True)
    p.add_argument('--terminal', type=Path, required=True)
    p.add_argument('--label', required=True)
    p.add_argument('--mode', choices=['download', 'upload'], required=True)
    a = p.parse_args()
    assert re.fullmatch('[a-z0-9-]+', a.label)
    lock = (LAB / '.dos-integration.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    binary, inputs = select_product(a.terminal, 'TERMINAL.EXE')
    manifest = json.loads(binary.with_name('manifest.json').read_text())
    assert manifest['experimental_meta_shared_runtime'] and manifest['experimental_original_reference']
    source = [ROOT / n for n in ('lab/bbs/test_synchronet_proxy_transfer_dos.py',
              'lab/bbs/test_zmodem_dos.py', 'lab/bbs/test_transfer_dos.py',
              'lab/bbs/modem.py', 'lab/bbs/audit_zmodem.py', 'lab/bbs/synthmodem_proxy_serial.js',
              'lab/bbs/synchronet.py', 'lab/bbs/synchronet_transfer.py', 'standalone/display_startup_geometry.asm')]
    frozen = {str(path.relative_to(ROOT)): sha(path) for path in inputs + source}
    server = [RUNTIME / n for n in ('exec/sbbs', 'exec/sexyz', 'ctrl/file.ini', 'ctrl/sbbs.ini')]
    server_frozen = {str(path.relative_to(ROOT)): sha(path) for path in server}
    wrapper = ROOT / 'build/bbs-lab' / (a.label + '-transfer')
    wrapper.mkdir(exist_ok=False)
    bridge = ROOT / 'build/bbs-lab' / (a.label + '-proxy')
    output = ROOT / 'build/bbs-lab/results/synchronet' / a.label
    assert not output.exists() and not bridge.exists()
    name = 'PCXTEST.BIN'
    fixture = AREA / name
    if a.mode == 'upload':
        name = 'P' + hashlib.sha256(a.label.encode()).hexdigest()[:6].upper() + '.BIN'
        fixture = wrapper / name
        pattern = bytes(range(256)) + b'\xff\xfb\x1f\xff\xfa\x1f\x1b[8;50;80t' + hashlib.sha256(a.label.encode()).digest()
        fixture.write_bytes((pattern * ((65539 + len(pattern) - 1) // len(pattern)))[:65539])
        assert not (AREA / name).exists()
    assert fixture.is_file()
    fixture_hash = sha(fixture)
    # Existing synthetic LABUSER login, bulletin exit, main menu and PCPLAB area.
    keys = ('p900 enter p2500 l o c enter p7000 L A B U S E R enter p2000 '
            'L A B P A S S 4 2 enter p8000 space p3000 Q enter p5000 space '
            'p3000 T p2000 J p1500 1 1 enter p2000 ')
    filename = ' '.join(name)
    if a.mode == 'download':
        keys += ('D p1500 ' + filename + ' enter p2000 Z p1500 N p1000 '
                 'a-z p3000 pgdown p300 f2 p150 f2 p300 D : \\ R E C V \\ enter ')
    else:
        keys += ('U p1500 ' + filename + ' enter p1500 Y p1000 '
                 'S y n t h L a b enter p2000 Z p1500 N p1000 '
                 'a-z p3000 pgup p300 f2 p150 f2 p300 D : \\ S E N D \\ * . B I N enter ')
    keys += 'p60000 space p2500 Q p3000'
    assert len('ADDKEY p1000 ' + keys + ' p8000 a-x') < 500
    proc = subprocess.Popen(['node', str(ROOT / 'lab/bbs/synthmodem_proxy_serial.js'),
                            '--runtime', str(a.runtime.resolve()), '--output', str(bridge),
                            '--bbs-port', '23231', '--framing-ms', '250', '--byte-delay-ms', '0',
                            '--terminal-rows', '24', '--probe-terminal-size'],
                            stdout=subprocess.DEVNULL, stderr=(wrapper / 'proxy.log').open('w'))
    try:
        deadline = time.monotonic() + 15
        while not (bridge / 'ready.json').exists():
            assert proc.poll() is None and time.monotonic() < deadline
            time.sleep(.05)
        ready = json.loads((bridge / 'ready.json').read_text())
        command = [sys.executable, str(ROOT / 'lab/bbs/test_zmodem_dos.py'), 'synchronet',
                   '--port', '23231', '--upstream-port', str(ready['endpoint']['port']),
                   '--binary', str(binary), '--sha256', sha(binary), '--label', a.label,
                   '--mode', a.mode, '--file', name + '=' + str(fixture), '--dial-fixture',
                   '--com', '3', '--irq', '5', '--cpu', '8086', '--mouse-scales', '8', '4',
                   '--display-rows', '25', '--status-hidden', '0', '--hangup-guard-ms', '500',
                   '--keys', keys, '--start-input-hex', ('D' if a.mode == 'download' else 'U').encode().hex(),
                   '--post-input-hex', b'Q'.hex(), '--post-menu', 'Read/Post Messages', '--timeout', '240', '--wait', '8']
        if a.mode == 'upload':
            audit = [str(ROOT / 'tools/bbs-dev'), '--command', 'python3',
                     str(ROOT / 'lab/bbs/synchronet_transfer.py'), 'audit', '--name', name,
                     '--expected', str(fixture)]
            command += ['--server-directory', str(AREA), '--server-audit-command-json', json.dumps(audit)]
        (wrapper / 'command.json').write_text(json.dumps(command, indent=2) + '\n')
        with (wrapper / 'harness.log').open('w') as log:
            code = subprocess.call(command, cwd=ROOT, stdout=log, stderr=log)
        deadline = time.monotonic() + 5
        while not (bridge / '1-closed.json').exists() and time.monotonic() < deadline:
            time.sleep(.05)
        protocol = json.loads((output / 'result.json').read_text())
        closed = json.loads((bridge / '1-closed.json').read_text()) if (bridge / '1-closed.json').exists() else None
        checks = dict(harness=code == 0 and protocol['passed'],
                      product_source_unchanged=all(sha(ROOT / n) == h for n, h in frozen.items()),
                      server_unchanged=all(sha(ROOT / n) == h for n, h in server_frozen.items()),
                      fixture_unchanged=sha(fixture) == fixture_hash,
                      proxy_closed=closed is not None,
                      proxy_source_unchanged=bool(closed and closed['source_unchanged']),
                      raw_upstream=protocol.get('raw_upstream') is True,
                      same_proxy_input=closed is not None and (bridge / '1-serial-input.bin').read_bytes() == (output / 'bbs-sent.bin').read_bytes(),
                      same_proxy_output=closed is not None and (bridge / '1-serial-output.bin').read_bytes() == (output / 'display.bin').read_bytes())
        result = dict(passed=all(checks.values()), checks=checks, mode=a.mode,
                      terminal_sha256=sha(binary), products=frozen, server_inputs=server_frozen,
                      server_commit=COMMIT, proxy=ready, protocol_checks=protocol.get('checks'),
                      protocol_errors=protocol.get('errors'),
                      fixture=dict(name=name, bytes=fixture.stat().st_size, sha256=fixture_hash), scope=__doc__)
        (wrapper / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps(dict(passed=result['passed'], checks=checks, errors=result['protocol_errors']), indent=2))
        assert result['passed']
    finally:
        proc.terminate()
        try:proc.wait(timeout=5)
        except subprocess.TimeoutExpired:proc.kill();proc.wait()


if __name__ == '__main__':
    main()
