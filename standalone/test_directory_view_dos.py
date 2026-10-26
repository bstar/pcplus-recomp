#!/usr/bin/env python3
"""Observe the real DOS live view, pages, background replies and return."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import test_connection_dos as driver
from modem_fixtures import fixture as modem_fixture
from directory_view_fixture import fixture
from test_command_reference_dos import png


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--terminal', type=Path, required=True)
    parser.add_argument('--label', required=True)
    parser.add_argument('--missing', action='store_true', help='Exercise an actual missing-file notice and live return')
    args = parser.parse_args()
    binary = args.terminal.resolve()
    manifest = json.loads((binary.parent / 'manifest.json').read_text())
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    assert manifest['experimental_directory_view'] and sha(binary) == manifest['binary_sha256']
    for name, digest in manifest['sources'].items():
        assert sha(driver.ROOT / name) == digest, name
    assert args.label and all(c.isalnum() or c in '-_' for c in args.label)
    out = driver.ROOT / 'build/directory-view-dos' / args.label
    out.mkdir(parents=True, exist_ok=False)
    observer = out / 'DIRWATCH.COM'
    subprocess.run(['nasm', '-fbin', str(driver.ROOT / 'standalone/directory_view_watch.asm'), '-o', str(observer)], check=True)
    prm = bytearray(modem_fixture(timeout=5))
    struct.pack_into('<2H', prm, 0, 2, 5)
    struct.pack_into('<H', prm, 0x178, 0x3e8)
    struct.pack_into('<H', prm, 0x188, 5)
    struct.pack_into('<HH', prm, 0x4e4, 8, 4)
    driver.BINARY = binary
    case = 'directory-view-' + args.label
    runout = driver.ROOT / 'build/connection-dos' / case
    assert not runout.exists()
    keys = 'p900 enter p3500 a-d p500 enter p3400 end p3400 escape p500 r e a d y p300 a-x'
    if args.missing:keys='p900 enter p3500 a-d p500 enter p900 escape p500 r e a d y p300 a-x'
    files={'DIRWATCH.COM': observer.read_bytes()}
    if not args.missing:files['PCPLUS.DIR']=fixture()
    result = driver.run(case, 'success', keys, prm=bytes(prm), com=3, irq=5, cpu='8086', working_drive='d',
        files=files, observer='DIRWATCH',
        online_updates=[(2.8 if args.missing else 3.0, b'\x1b[5;1HBBS-DURING-READ\x1b[6n')])
    capture = (runout / 'DIRVIEW.BIN').read_bytes()
    font = (runout / 'VGA16.BIN').read_bytes()
    assert len(capture) == 12006 and len(font) == 4096
    magic, flags, ticks = struct.unpack_from('<3H', capture)
    first, last, loading = (capture[6 + i * 4000:4006 + i * 4000] for i in range(3))
    wire = (runout / 'serial.bin').read_bytes()
    final = (runout / 'SCREEN.BIN').read_bytes()
    checks = dict(base_harness=result['passed'], passive_prompt_observed=magic == 0x4456 and bool(flags & 8),
        first_page=bool(flags & 1) and b'LoSs oF CoNtRoL' in first[::2],
        last_page=bool(flags & 2) and b'Node 191' in last[::2] and b'FINAL 200' in last[::2],
        loading_view=bool(flags & 4) and b'Reading directory...' in loading[::2],
        no_private_fields=all(b'HIDDENPASS' not in frame[::2] and b'SECRETA' not in frame[::2] for frame in (first, last, loading)),
        controls_sanitized_CP437_preserved=b'A..\xdb\xff' in first[::2],
        target_not_changed=result['commands'] == ['ATZ', 'ATDCaseTest:23'],
        BBS_query_replied=b'\x1b[5;16R' in wire, ordinary_keyboard_resumed=b'ready' in wire,
        updated_screen_restored=final[640:670:2] == b'BBS-DURING-READ',
        fixture_unchanged=not (runout/'PCPLUS.DIR').exists() if args.missing else (runout / 'PCPLUS.DIR').read_bytes() == fixture())
    if args.missing:
        for name in ('first_page','last_page','loading_view','controls_sanitized_CP437_preserved'):del checks[name]
        checks['actual_missing_notice']=bool(flags&4) and b'Could not load the directory.' in loading[::2]
    for name, frame in ([('error',loading)] if args.missing else [('first-page', first), ('last-page', last), ('loading', loading)]):
        (out / (name + '.bin')).write_bytes(frame)
        png(out / (name + '.png'), frame, font)
    report = dict(passed=all(checks.values()), checks=checks, binary_sha256=sha(binary), observer_flags=flags,
        observer_ticks=ticks, keyboard=keys, missing=args.missing, serial=dict(com=3, irq=5, baud=19200, cpu='8086'),
        sources={str(p.relative_to(driver.ROOT)): sha(p) for p in [Path(__file__).resolve(),
            driver.ROOT / 'standalone/directory_view_watch.asm', driver.ROOT / 'standalone/directory_view_fixture.py',
            driver.ROOT / 'standalone/test_connection_dos.py', driver.ROOT / 'standalone/test_command_reference_dos.py']},
        artifacts={str(p.relative_to(driver.ROOT)): sha(p) for p in [runout / n for n in
            ('DIRVIEW.BIN', 'VGA16.BIN', 'serial.bin', 'SCREEN.BIN', 'BEFORE.BIN', 'AFTER.BIN', 'TEST.PRM', *([] if args.missing else ['PCPLUS.DIR']))]},
        scope=__doc__ + ' Actual8086 DOS COM3/IRQ5 with synthetic Hayes peer, read-only kernel fixture and passive video observer. ROM-font PNGs. No live dialing/profile adoption, physical CTS/DCD/analog or complete rendering acceptance.')
    (out / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
