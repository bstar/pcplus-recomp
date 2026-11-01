#!/usr/bin/env python3
"""Read live startup queue state from the normal full DOS terminal."""
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
    parser.add_argument('--terminal', required=True, type=Path)
    parser.add_argument('--label', required=True)
    args = parser.parse_args()
    assert re.fullmatch('[a-z0-9-]+', args.label)
    parent = args.terminal.resolve()
    manifest = json.loads((parent / 'manifest.json').read_text())
    assert manifest['experimental_phone_log_startup']
    binary = parent / 'TERMINAL.EXE'
    assert sha(binary) == manifest['binary_sha256']
    terminal.BINARY = binary
    listing = (parent / 'terminal.map').read_text()
    symbols = {name: (int(seg, 16), int(off, 16)) for seg, off, name in re.findall(
        r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$', listing, re.I | re.M)}
    defines = dict(IRQ_VECTOR=12, ISR_SEGMENT=symbols['uart_receive_interrupt'][0],
        ISR_OFFSET=symbols['uart_receive_interrupt'][1], DATA_SEGMENT=symbols['_terminal_phone_log_startup_status'][0],
        STATUS_OFFSET=symbols['_terminal_phone_log_startup_status'][1],
        QUEUE_SEGMENT=symbols['_phone_log_queue_store'][0], QUEUE_OFFSET=symbols['_phone_log_queue_store'][1])
    output = ROOT / 'build/phone-log-startup-terminal' / args.label
    assert not output.exists()
    output.mkdir(parents=True)
    observer = output / 'PLWATCH.COM'
    subprocess.run(['nasm', '-fbin', *[f'-D{k}={v}' for k, v in defines.items()],
        str(ROOT / 'standalone/phone_log_startup_watch.asm'), '-o', str(observer)], check=True)
    sources = dict(manifest['sources'])
    for name in ['standalone/test_phone_log_startup_terminal.py', 'standalone/phone_log_startup_watch.asm',
            'standalone/test_connection_dos.py', 'standalone/modem_fixtures.py',
            'standalone/terminal_config_fixtures.py', 'standalone/directory_test_support.py', 'standalone/test_terminal.py']:
        sources[name] = sha(ROOT / name)
    results = []
    for name, enabled, env, files, error, expected_path in [
        ('unconfigured', 0, 'BAD;DIR', {}, 0, b''),
        ('disabled', 0, 'BAD;DIR', {}, 0, b''),
        ('current', 1, '', {}, 0, b'D:\\PCPLUS.FON'),
        ('fallback', 256, 'D:\\ENV', {'ENV/KEEP.TXT': b'KEEP'}, 0, b'D:\\ENV\\PCPLUS.FON'),
        ('precedence', 65535, 'BAD;DIR', {'PCPLUS.FON': b'EXISTING'}, 0, b'D:\\PCPLUS.FON'),
        ('bad-env', 1, 'BAD;DIR', {}, 2, None),
        ('bad-parent', 1, 'D:\\MISSING', {}, 4, None),
    ]:
        settings = bytearray(fixture(timeout=5))
        struct.pack_into('<HH', settings, 0x4e4, 8, 4)
        struct.pack_into('<H', settings, 0x1e6, enabled)
        case = args.label + '-' + name
        folder = ROOT / 'build/connection-dos' / case
        assert not folder.exists()
        run = terminal.run(case, 'reject' if error else 'direct' if name == 'unconfigured' else 'success', 'p900 enter p4000 a-x',
            prm=bytes(settings), files={**files, 'PLWATCH.COM': observer.read_bytes()}, observer='PLWATCH',
            arguments='COM1 19200 HARD' if name == 'unconfigured' else None,
            working_drive='d', environment={'PCPLUS': env}, expected=7 if error else 0, cpu='8086')
        captured = (folder / 'PLSTART.BIN').read_bytes()
        assert len(captured) == 680
        header = struct.unpack_from('<7H', captured)
        queue = captured[14:]
        checks = dict(normal_terminal=run['passed'], observer_magic=header[0] == 0x4c53,
            no_log_creation=set(p.relative_to(folder).as_posix() for p in folder.rglob('*.FON') if p.is_file()) == ({'PCPLUS.FON'} if name == 'precedence' else set()))
        if error:
            checks['refused_before_UART_ownership'] = header[1] == 0
            checks['accurate_log_setup_notice'] = b'Call-log setup failed.' in (folder / 'SCREEN.BIN').read_bytes()[::2]
        else:
            retained = queue[42:106].split(b'\0', 1)[0]
            checks.update(actual_live_capture=header[1] == 1 and header[2] > 0 and header[3] > 0,
                startup_status=header[4] == 0, private_far_queue=header[5] != header[6],
                queue_flags=struct.unpack_from('<9H', queue) == (0x514d, 0, int(bool(enabled)), 0, 0, 0, 0, 0, 0),
                retained_path=retained == expected_path)
        results.append(dict(case=name, passed=all(checks.values()), checks=checks, native=run,
            observer_header=header, expected_path=expected_path.decode() if expected_path is not None else None))
    checks = dict(all_cases=all(r['passed'] for r in results),
        sources_unchanged=all(sha(ROOT / name) == digest for name, digest in sources.items()),
        binary_unchanged=sha(binary) == manifest['binary_sha256'])
    result = dict(passed=all(checks.values()), checks=checks, cases=results, sources=sources,
        terminal_sha256=sha(binary), observer_defines=defines,
        scope=__doc__ + ' Passive ISR/vector-derived memory observation only; no product RAM writes or fake replies. '
            'Accepted image import and real pre-UART failures; no connection-event logging or poll scheduling yet.')
    (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(passed=result['passed'], checks=checks, failed=[r for r in results if not r['passed']]), indent=2))
    assert result['passed']


if __name__ == '__main__':
    main()
