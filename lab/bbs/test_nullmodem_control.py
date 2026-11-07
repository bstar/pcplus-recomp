#!/usr/bin/env python3
"""Check serial-control framing separately from BBS/Telnet application bytes."""
import argparse
import hashlib
import json
from pathlib import Path
from nullmodem_control import Control

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT/'build') and not out.exists()
    checks = 0
    payload = bytes(range(256))*3
    encoded = Control.encode(payload)
    for split in range(len(encoded)+1):
        events = []
        control = Control(lambda *values: events.append(values))
        assert control.feed(encoded[:split])+control.feed(encoded[split:]) == payload
        assert not events and not control.pending
        checks += 1
    for flags in range(8):
        framed = b'A\xff'+bytes([flags])+b'B'
        for split in range(len(framed)+1):
            events = []
            control = Control(lambda *values: events.append(values))
            assert control.feed(framed[:split])+control.feed(framed[split:]) == b'AB'
            assert events == [(bool(flags&1),bool(flags&2),bool(flags&4))]
            checks += 1
    events = []
    control = Control(lambda *values: events.append(values))
    wire = b'\xff\x03'+encoded+b'\xff\x02'+encoded+b'\xff\x03'
    assert b''.join(control.feed(bytes([value])) for value in wire) == payload*2
    assert events == [(True,True,False),(False,True,False),(True,True,False)]
    checks += 1
    names = ['lab/bbs/test_nullmodem_control.py','lab/bbs/nullmodem_control.py']
    result = dict(passed=True, checks=checks,
                  sources={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in names},
                  scope='All binary byte values across every encoded split, all eight line states across every split, byte-at-a-time mixed control/data. No UART scheduling or physical flow-control acceptance.')
    out.mkdir(parents=True)
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS null-modem control:',checks,'cases')


if __name__ == '__main__':
    main()
