#!/usr/bin/env python3
"""Audit pressure captures without importing the producer or its expectations."""
import argparse
import hashlib
import json
import shutil
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(folder, during_pause=False):
    receipt = json.loads((folder / 'pressure-checks.json').read_text())
    assert receipt['passed'] and all(receipt['checks'].values())
    for name, digest in receipt['captures_sha256'].items():
        path = (folder / name).resolve()
        assert path.is_relative_to(folder) and sha(path) == digest, name
    events = json.loads((folder / 'peer-events.json').read_text())
    assert all(a['time'] <= b['time'] for a, b in zip(events, events[1:]))
    sends = [event for event in events if event['kind'] == 'send']
    assert len(sends) == (50 if during_pause else 49)
    assert bytes.fromhex(sends[0]['hex']) == b'\r\nOK\r\n'
    assert bytes.fromhex(sends[1]['hex']) == (
        b'CONNECT\r\n\x1b[2J\x1b[HFIRST BYTE SAFE\x1b[6n\x1b[0cLOGIN:')
    assert [bytes.fromhex(event['hex']) for event in sends[-3:]] == [
        b'END', b'\x1b[6n', b'\r\nOK\r\n']
    case = folder / 'window-pressure-4'
    screen = (case / 'SCREEN.BIN').read_bytes()
    assert len(screen) == 4000 and screen[:30:2] == b'FIRST BYTE SAFE'
    assert (case / 'BEFORE.BIN').stat().st_size == 42
    assert (case / 'BEFORE.BIN').read_bytes() == (case / 'AFTER.BIN').read_bytes()
    assert sha(case / 'TERMINAL.EXE') == receipt['parent_sha256']
    assert sha(case / 'ASPECT.EXE') == receipt['runner_sha256']
    raw = (case / 'RENDER.BIN').read_bytes()
    first, advanced, visible, help_seen, ticks, peak, menu = struct.unpack('<7H', raw[-14:])
    assert advanced == visible == 1 and ticks > 30
    assert first == receipt['first_render_tick'] and peak == receipt['child_ring_peak']
    assert ticks == receipt['window_ticks']
    assert struct.unpack_from('<7H', raw)[:4] == (0x524e, 1, 1, 1)
    assert struct.unpack_from('<7H', raw)[6] == 0
    replies, delays = [], []
    offered = 0
    for number, send in enumerate(sends[3 if during_pause else 2:-3]):
        row = number // 2 + 2
        column = 1 + 40 * (number % 2)
        expected_text = bytes(('PKT%02d:' % number), 'ascii') + bytes(
            65 + (number * 7 + offset * 11) % 26 for offset in range(26))
        expected_payload = bytes('\x1b[%d;%dH' % (row, column), 'ascii')
        for index, character in enumerate(expected_text):
            expected_payload += bytes('\x1b[%dm' % (31 + index % 2), 'ascii') + bytes([character])
        expected_payload += b'\x1b[0m\x1b[6n'
        assert bytes.fromhex(send['hex']) == expected_payload
        offered += len(expected_payload)
        cell = 2 * (80 * (row - 1) + column - 1)
        assert screen[cell:cell + 64:2] == expected_text
        assert screen[cell + 1:cell + 64:2] == bytes([4, 2] * 16)
        reply = bytes('\x1b[%d;%dR' % (row, column + 32), 'ascii')
        replies.append(reply)
        received = bytearray()
        for event in events:
            if event['kind'] != 'receive' or event['time'] < send['time']:
                continue
            received.extend(bytes.fromhex(event['hex']))
            if reply in received:
                delays.append(event['time'] - send['time'])
                break
        else:
            raise AssertionError('Missing packet reply %d' % number)
    assert offered == receipt['payload_bytes'] == 9114
    assert len(replies) == len(set(replies)) == receipt['packet_count'] == 44
    assert delays == receipt['packet_reply_delay_seconds'] and max(delays) <= 1
    elapsed = None
    if during_pause:
        assert bytes.fromhex(sends[2]['hex']) == b'HOLD'
        since = sends[2]['time']
        received = b''
        pause_end = None
        for event in events:
            if event['kind'] == 'receive' and event['time'] >= since:
                received += bytes.fromhex(event['hex'])
                if b'PAUSEDONE' in received:
                    pause_end = event['time']
                    break
        assert pause_end is not None
        elapsed = pause_end - since
        assert 6 <= elapsed <= 7 and elapsed == receipt['pause_elapsed_seconds']
        assert all(send['time'] + delay < pause_end for send,delay in zip(sends[3:-3],delays))
    wire = b''.join(bytes.fromhex(event['hex']) for event in events if event['kind'] == 'receive')
    assert wire == (b'ATZ\rATDCaseTest:23\r\x1b[1;16R\x1b[?62;2cKEYREADYkeys' +
                    b''.join(replies) + (b'PAUSEDONE' if during_pause else b'') + b'doneSynth42\r\x1b[23;76R ready+++ATH\r')
    assert (case / 'serial.bin').read_bytes() == wire
    assert screen[2 * (22 * 80 + 72):2 * (22 * 80 + 75):2] == b'END'
    return dict(passed=True, during_pause=during_pause, pause_elapsed_seconds=elapsed, payload_bytes=offered, packet_count=len(replies),
                verified_character_cells=1408, verified_attribute_cells=1408,
                max_reply_delay_seconds=max(delays), child_ring_peak=peak,
                window_visible_ticks=ticks, parent_sha256=receipt['parent_sha256'],
                runner_sha256=receipt['runner_sha256'], producer_receipt_sha256=sha(folder / 'pressure-checks.json'),
                whole_wire_sha256=hashlib.sha256(wire).hexdigest(), physical_flow_accepted=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder', type=Path)
    parser.add_argument('--during-pause',action='store_true')
    parser.add_argument('--cohort', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    folder, cohort, output = args.folder.resolve(), args.cohort.resolve(), args.output.resolve()
    assert folder.is_relative_to(ROOT / 'build') and cohort.is_relative_to(ROOT / 'build')
    assert not cohort.exists() and not output.exists() and output.is_relative_to(ROOT / 'docs/validation')
    result = audit(folder, args.during_pause)
    shutil.copytree(folder, cohort / 'captures')
    for relative in ['standalone/test_aspect_window_pressure_dos.py',
                     'standalone/test_aspect_window_query_dos.py', 'standalone/test_aspect_script_window_dos.py',
                     'standalone/test_aspect_keys_dos.py', 'standalone/test_aspect_renderer_dos.py',
                     'standalone/test_connection_dos.py', 'standalone/audit_aspect_window_pressure.py']:
        target = cohort / 'sources' / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    files = {str(p.relative_to(cohort)): sha(p) for p in cohort.rglob('*') if p.is_file()}
    (cohort / 'files.json').write_text(json.dumps(files, indent=2) + '\n')
    result.update(cohort=str(cohort.relative_to(ROOT)), frozen_files=len(files),
                  files_manifest_sha256=sha(cohort / 'files.json'), auditor_sha256=sha(Path(__file__)),
                  scope='Actual DOS parent/ASPECT at fixed6000 DOSBox-X cycles, COM1/38400/HARD fixture with an owned paced TCP modem peer. All44 independent tile/CPR responses,1408 characters/colors, exact whole wire, window/render witnesses, normal child exit and42-byte hardware restoration verified. UART CTS/RTS stalling is not represented by this transparent socket peer; physical flow, software XOFF/XON pressure, transfers, other wait contexts and full application remain unaccepted.')
    if args.during_pause:
        result['scope'] += ' All44 replies precede the script PAUSEDONE marker; the explicit six-second pause is independently timed from HOLD.'
    output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
