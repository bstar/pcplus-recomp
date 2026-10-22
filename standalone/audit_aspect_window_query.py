#!/usr/bin/env python3
"""Independently audit the retained blocking-window query failure receipts.

This accepts evidence of the defect, never the application's compatibility.
No producer checker is imported or executed; no DOS inputs are modified.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(folder):
    folder = folder.resolve()
    receipt = json.loads((folder / 'query-checks.json').read_text())
    for relative, expected in receipt['captures_sha256'].items():
        path = (folder / relative).resolve()
        assert path.is_relative_to(folder), relative
        assert digest(path) == expected, relative
    events = json.loads((folder / 'peer-events.json').read_text())
    assert all(a['time'] <= b['time'] for a, b in zip(events, events[1:]))
    sent = [event for event in events if event['kind'] == 'send']
    assert [bytes.fromhex(event['hex']) for event in sent] == [
        b'\r\nOK\r\n',
        b'CONNECT\r\n\x1b[2J\x1b[HFIRST BYTE SAFE\x1b[6n\x1b[0cLOGIN:',
        b'\x1b[6n', b'END', b'\x1b[6n', b'\r\nOK\r\n',
    ]
    wire = b''.join(bytes.fromhex(event['hex']) for event in events
                    if event['kind'] == 'receive')
    assert wire == (b'ATZ\rATDCaseTest:23\r\x1b[1;16R\x1b[?62;2cKEYREADYkeys'
                    b'\x1b[1;22RdoneSynth42\r\x1b[1;25R ready+++ATH\r')
    case = folder / 'window-query-4'
    assert (case / 'serial.bin').read_bytes() == wire
    assert digest(case / 'TERMINAL.EXE') == receipt['parent_sha256']
    assert digest(case / 'ASPECT.EXE') == receipt['runner_sha256']
    observation = struct.unpack('<5H', (case / 'RENDER.BIN').read_bytes()[-10:])
    assert observation == (1, 0, 100, 4, 0)
    assert (case / 'BEFORE.BIN').read_bytes() == (case / 'AFTER.BIN').read_bytes()
    query_time = sent[2]['time']
    received = b''
    completion = None
    for event in events:
        if event['kind'] == 'receive' and event['time'] >= query_time:
            received += bytes.fromhex(event['hex'])
            if b'\x1b[1;22R' in received:
                completion = event['time']
                break
    assert completion is not None
    delay = completion - query_time
    assert abs(delay - receipt['reply_delay_seconds']) < 1e-9
    assert delay > 1.0 and not receipt['passed']
    assert receipt['checks'] == dict(
        DOS_functional_checks=True, window_observed=True,
        query_present_in_child_ring=True, reply_matches_logical_BBS_cursor=True,
        peer_complete_reply_within_one_second=False)
    return dict(path=str(folder.relative_to(ROOT)), reply_delay_seconds=delay,
                retained_files_verified=len(receipt['captures_sha256']),
                receipt_sha256=digest(folder / 'query-checks.json'),
                parent_sha256=receipt['parent_sha256'],
                runner_sha256=receipt['runner_sha256'],
                defect_reproduced=True, compatibility_accepted=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folders', nargs='+', type=Path)
    args = parser.parse_args()
    print(json.dumps(dict(evidence_verified=True,
                         cases=[audit(folder) for folder in args.folders],
                         auditor_sha256=digest(Path(__file__))), indent=2))


if __name__ == '__main__':
    main()
