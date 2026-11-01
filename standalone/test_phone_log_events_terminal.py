#!/usr/bin/env python3
"""Observe real terminal event hooks without modifying product memory or replies."""
import argparse
import datetime as dt
import json
from pathlib import Path
import re
import struct
import subprocess
import test_connection_dos as terminal
from modem_fixtures import fixture
from directory_fixtures import directory
from build_phone_log_queue import ROOT, sha


def inspect_record(raw, calls, enabled, name, target):
    meta = struct.unpack_from('<6H', raw)
    life = raw[12:50]
    queue = raw[50:]
    generation = struct.unpack_from('<I', life, 2)[0]
    flags = struct.unpack_from('<4H', life, 6)
    qflags = struct.unpack_from('<9H', queue)
    started, ended, committed = struct.unpack_from('<3I', queue, 18)
    checks = dict(final_kind=meta[0] == 2, startup_ok=meta[5] == 0,
        lifecycle_idle=struct.unpack_from('<H', life)[0] == 0x4c45 and flags == (0, 0, 0, 0),
        generation=generation == calls,
        queue_flags=qflags == (0x514d, 0, enabled, 0, calls * 2, 0, 0, 0, 0),
        queue_generations=(started, ended, committed) == (calls, calls, 0),
        final_status=meta[2] == (512 if calls else 0))
    rows = []
    previous = None
    for index in range(calls * 2):
        at = 106 + index * 140
        count, kind, gen = struct.unpack_from('<HHI', queue, at)
        text = queue[at + 8:at + 8 + count]
        valid = 0 < count < 132 and queue[at + 8 + count] == 0 and kind == index % 2 + 1 and gen == index // 2 + 1
        try:
            if index % 2 == 0:
                prefix = b'\r\n' + name[:22].ljust(22) + b' ' + target.rjust(20) + b' '
                valid &= text.startswith(prefix)
                stamp = dt.datetime.strptime(text[len(prefix):].decode('ascii'), '%m/%d/%y %H:%M:%S ')
                previous = stamp
                if gen == calls:
                    actual = struct.unpack_from('<6H', life, 14)
                    valid &= actual[1:] == (stamp.month, stamp.day, stamp.hour, stamp.minute, stamp.second) and actual[0] % 100 == stamp.year % 100
            else:
                match = re.fullmatch(rb'(\d\d):(\d\d):(\d\d) (\d\d):(\d\d):(\d\d)', text)
                valid &= bool(match)
                if match:
                    h, m, s, elapsed_h, elapsed_m, elapsed_s = map(int, match.groups())
                    elapsed = elapsed_h * 3600 + elapsed_m * 60 + elapsed_s
                    finish = previous + dt.timedelta(seconds=elapsed)
                    valid &= elapsed_m < 60 and elapsed_s < 60 and 0 <= elapsed < 30 and (finish.hour, finish.minute, finish.second) == (h, m, s)
        except (ValueError, UnicodeError, TypeError):
            valid = False
        rows.append(dict(index=index, count=count, kind=kind, generation=gen,
                         text=text.decode('cp437'), valid=bool(valid)))
    checks['exact_event_records'] = all(r['valid'] for r in rows)
    return checks, rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--terminal', type=Path, required=True)
    parser.add_argument('--label', required=True)
    parser.add_argument('--case', choices=['success', 'hangup', 'busy', 'silence', 'redial', 'disabled', 'direct', 'capacity'])
    args = parser.parse_args()
    assert re.fullmatch('[a-z0-9-]+', args.label)
    parent = args.terminal.resolve()
    manifest = json.loads((parent / 'manifest.json').read_text())
    assert manifest['experimental_phone_log_events']
    binary = parent / 'TERMINAL.EXE'
    assert sha(binary) == manifest['binary_sha256']
    terminal.BINARY = binary
    symbols = {n: (int(s, 16), int(o, 16)) for s, o, n in re.findall(
        r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$', (parent / 'terminal.map').read_text(), re.M | re.I)}
    defines = dict(IRQ_VECTOR=12, ISR_SEGMENT=symbols['uart_receive_interrupt'][0],
        ISR_OFFSET=symbols['uart_receive_interrupt'][1], DATA_SEGMENT=symbols['_terminal_phone_log_event_status'][0],
        EVENT_STATUS_OFFSET=symbols['_terminal_phone_log_event_status'][1], EPOCH_OFFSET=symbols['_terminal_phone_log_event_epoch'][1],
        LIFECYCLE_OFFSET=symbols['_phone_log_lifecycle_store'][1], QUEUE_SEGMENT=symbols['_phone_log_queue_store'][0],
        QUEUE_OFFSET=symbols['_phone_log_queue_store'][1], CONNECTION_STATE_OFFSET=symbols['connection_state'][1],
        CONNECTION_STATUS_OFFSET=symbols['connection_status'][1], STARTUP_STATUS_OFFSET=symbols['_terminal_phone_log_startup_status'][1])
    output = ROOT / 'build/phone-log-events-terminal' / args.label
    assert not output.exists()
    output.mkdir(parents=True)
    observer = output / 'PLWATCH.COM'
    subprocess.run(['nasm', '-fbin', *[f'-D{k}={v}' for k, v in defines.items()],
        str(ROOT / 'standalone/phone_log_events_watch.asm'), '-o', str(observer)], check=True)
    sources = dict(manifest['sources'])
    for name in ('standalone/test_phone_log_events_terminal.py', 'standalone/phone_log_events_watch.asm',
        'standalone/test_connection_dos.py', 'standalone/modem_fixtures.py', 'standalone/directory_fixtures.py',
        'standalone/terminal_config_fixtures.py', 'standalone/directory_test_support.py', 'standalone/test_terminal.py'):
        sources[name] = sha(ROOT / name)
    cases = [('success', 'success', 'p3500 a-x', 1, 1),
        ('hangup', 'hangup', 'p3000 a-h p2200 a-x', 1, 1),
        ('busy', 'busy', 'p4000 a-x', 1, 0),
        ('silence', 'silence', 'p4500 a-x', 1, 0),
        ('redial', 'redial', 'p3500 a-d p3500 a-x', 1, 1),
        ('disabled', 'success', 'p3500 a-x', 0, 0),
        ('direct', 'direct', 'p3500 a-x', 1, 1),
        ('capacity', 'direct', 'p2000 a-h p300 a-d p500 a-h p300 a-d p500 a-x', 1, 2)]
    results, artifacts = [], {}
    for name, mode, keys, enabled, calls in cases:
        if args.case and args.case != name:
            continue
        settings = bytearray(fixture(timeout=2 if mode == 'silence' else 5))
        struct.pack_into('<HH', settings, 0x4e4, 8, 4)
        struct.pack_into('<H', settings, 0x1e6, enabled)
        selected = directory(direct=1) if mode == 'direct' else None
        options = dict(directory=selected, arguments='@D:\\TEST.PRM /E:D:\\TEST.DIR /N:1', accounting_delta=calls) if selected else {}
        case = args.label + '-' + name
        folder = ROOT / 'build/connection-dos' / case
        assert not folder.exists()
        native = terminal.run(case, mode, 'p900 enter ' + keys, prm=bytes(settings),
            files={'PLWATCH.COM': observer.read_bytes()}, observer='PLWATCH', working_drive='d',
            expected=12 if calls else 0, cpu='8086', **options)
        captured = (folder / 'PLSTATE.BIN').read_bytes()
        assert len(captured) == 5748
        header = struct.unpack_from('<10H', captured)
        final = captured[20 + (header[2] - 1) * 716:20 + header[2] * 716]
        checks, rows = inspect_record(final, calls, enabled, b'LAB NODE 001' if selected else b'MODEM', b'' if selected else b'CaseTest:23')
        screen = (folder / 'SCREEN.BIN').read_bytes()[::2]
        checks.update(normal_terminal=native['passed'], observer_final=header[0] == 0x4c45 and header[1] > 0 and 0 < header[2] <= 8 and header[3] == 1,
            actual_live_segments=header[4] > 0 and header[5] != header[6],
            actual_exit=header[9] == (12 if calls else 0),
            no_log_disk_write=not any(folder.rglob('*.FON')),
            unsaved_notice=(b'Call log pending; records were not saved.' in screen) == bool(calls))
        if name == 'capacity':
            checks['capacity_refusal_visible'] = b'Call log blocked' in screen
        results.append(dict(case=name, passed=all(checks.values()), checks=checks,
            observer_header=header, final_metadata=list(struct.unpack_from('<6H', final)), records=rows, native=native))
        artifacts.update({str(p.relative_to(ROOT)): sha(p) for p in folder.rglob('*') if p.is_file()})
        print(name, 'PASS' if results[-1]['passed'] else 'FAIL', flush=True)
    checks = dict(all_cases=all(r['passed'] for r in results), sources_unchanged=all(sha(ROOT / n) == d for n, d in sources.items()),
        binary_unchanged=sha(binary) == manifest['binary_sha256'])
    result = dict(passed=all(checks.values()), checks=checks, cases=results, sources=sources,
        terminal_sha256=sha(binary), observer_defines=defines, artifacts=artifacts, original_inputs=[],
        scope=__doc__ + ' Stable timer snapshots and parent INT21/4C before deallocation; no product RAM writes or synthesized terminal replies. '
        'RAM events only: nonempty logs deliberately fail shutdown with error12 until a disk scheduler is added. '
        'These cases do not prove physical DCD, failed-hangup continuity, child-clock ownership or durable log persistence.')
    (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(passed=result['passed'], checks=checks, failed=[r for r in results if not r['passed']]), indent=2))
    assert result['passed']


if __name__ == '__main__':
    main()
