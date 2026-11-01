#!/usr/bin/env python3
"""Exercise the real capture UI against a startup-owned call-log path in DOS."""
import argparse
import json
from pathlib import Path
import re
import struct
import subprocess
import test_connection_dos as terminal
from modem_fixtures import fixture
from build_phone_log_queue import ROOT, sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--terminal', type=Path, required=True)
    parser.add_argument('--label', required=True)
    args = parser.parse_args()
    assert re.fullmatch('[a-z0-9-]+', args.label)
    parent = args.terminal.resolve()
    manifest = json.loads((parent / 'manifest.json').read_text())
    assert manifest['experimental_phone_log_startup'] and manifest['experimental_phone_log_reservations']
    binary = parent / 'TERMINAL.EXE'
    assert sha(binary) == manifest['binary_sha256']
    terminal.BINARY = binary
    output = ROOT / 'build/phone-log-claim-terminal' / args.label
    assert not output.exists()
    output.mkdir(parents=True)
    observer = output / 'CLWATCH.COM'
    subprocess.run(['nasm', '-fbin', str(ROOT / 'standalone/phone_log_claim_watch.asm'), '-o', str(observer)], check=True)
    sources = dict(manifest['sources'])
    for name in ['standalone/test_phone_log_claim_terminal.py', 'standalone/phone_log_claim_watch.asm',
            'standalone/test_connection_dos.py', 'standalone/modem_fixtures.py',
            'standalone/terminal_config_fixtures.py', 'standalone/directory_test_support.py', 'standalone/test_terminal.py']:
        sources[name] = sha(ROOT / name)
    results = []
    for name, enabled, seed in [('claimed-new', 1, None), ('claimed-existing', 1, b'EXISTING\x1aLOG\r\n'), ('disabled-allows-capture', 0, None)]:
        settings = bytearray(fixture(timeout=5))
        struct.pack_into('<HH', settings, 0x4e4, 8, 4)
        struct.pack_into('<H', settings, 0x1e6, enabled)
        files = {'CLWATCH.COM': observer.read_bytes()}
        if seed is not None:
            files['PCPLUS.FON'] = seed
        keys = 'p900 enter p2400 a-f1 p500 p c p l u s . f o n enter p400 m 1 p1300 '
        if not enabled:
            keys += 'a-f1 p500 '
        keys += 'a-f1 p500 c a p . l o g enter p400 m 2 p1500 a-f1 p500 a-x'
        case = args.label + '-' + name
        folder = ROOT / 'build/connection-dos' / case
        assert not folder.exists()
        run = terminal.run(case, 'success', keys, prm=bytes(settings), files=files,
            observer='CLWATCH', working_drive='d', cpu='8086',
            online_triggers=[(b'm1', [(.1, b'PROBE\n')]), (b'm2', [(.1, b'CAPOK\n')])])
        packet = (folder / 'PLCLAIM.BIN').read_bytes()
        assert len(packet) == 494
        header = struct.unpack_from('<7H', packet)
        frames = [packet[14+n*160:14+(n+1)*160:2] for n in range(3)]
        log = folder / 'PCPLUS.FON'
        expected = seed if enabled else b'PROBE\r\n'
        checks = dict(normal_terminal=run['passed'], observer_magic=header[0] == 0x434c,
            same_log_protected=(log.read_bytes() if log.exists() else None) == expected,
            independent_capture_works=(folder / 'CAP.LOG').read_bytes() == b'CAPOK\r\n',
            capture_open_and_close_observed=header[1]&6 == 6 and b'Capture open' in frames[1] and b'Capture closed' in frames[2],
            refusal_policy=(header[1]&1 != 0 and b'Capture denied' in frames[0]) if enabled else header[1]&1 == 0,
            actual_filename_prompt=header[1]&8 != 0 and 0 < header[6] < (header[3] if enabled else header[4]),
            notice_order=(0 < header[3] < header[4] < header[5]) if enabled else 0 < header[4] < header[5])
        results.append(dict(case=name, passed=all(checks.values()), checks=checks, native=run,
            observer_header=header, expected_log_hex=expected.hex() if expected is not None else None))
    checks = dict(all_cases=all(r['passed'] for r in results),
        sources_unchanged=all(sha(ROOT / name) == digest for name, digest in sources.items()),
        binary_unchanged=sha(binary) == manifest['binary_sha256'])
    result = dict(passed=all(checks.values()), checks=checks, cases=results, sources=sources,
        terminal_sha256=sha(binary), original_inputs=[],
        scope=__doc__ + ' Actual BIOS Alt-F1 filename prompts and processed capture, passive video observation, '
            'real ANSI replies and independent exact file comparison. No product RAM writes/fake replies, logger event production, poll scheduling or physical claim.')
    (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(passed=result['passed'], checks=checks, failed=[r for r in results if not r['passed']]), indent=2))
    assert result['passed']


if __name__ == '__main__':
    main()
