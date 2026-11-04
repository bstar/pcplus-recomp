#!/usr/bin/env python3
"""Audit actual DOS size probe, captured BBS NAWS and CPR-bounded editor cells.

Owned80x24 loopback editor scope; no physical/SIP/DSP or all-screen acceptance.
"""
import argparse
import json
import struct
from pathlib import Path

from product_inputs import ROOT, sha
from audit_screen_reference import audit


def telnet(raw):
    """Independent client-wire decoder, retaining every subnegotiation."""
    data, subs, options = bytearray(), [], []
    i = 0
    while i < len(raw):
        b = raw[i]
        i += 1
        if b != 255:
            data.append(b)
            continue
        assert i < len(raw)
        command = raw[i]
        i += 1
        if command == 255:
            data.append(255)
        elif command in (251, 252, 253, 254):
            assert i < len(raw)
            options.append((command, raw[i]))
            i += 1
        elif command == 250:
            sub = bytearray()
            while True:
                assert i < len(raw)
                b = raw[i]
                i += 1
                if b != 255:
                    sub.append(b)
                    continue
                assert i < len(raw)
                b = raw[i]
                i += 1
                if b == 255:
                    sub.append(b)
                else:
                    assert b == 240
                    break
            assert sub
            subs.append(bytes(sub))
        else:
            raise AssertionError(('unexpected client Telnet command', command))
    return bytes(data), subs, options


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--bridge', type=Path, required=True)
    a = p.parse_args()
    out, bridge = a.output.resolve(), a.bridge.resolve()
    assert out.is_relative_to(ROOT / 'build') and bridge.is_relative_to(ROOT / 'build')
    producer = json.loads((out / 'proxy-integration.json').read_text())
    assert producer['passed']
    for name, digest in producer['product_inputs'].items():
        assert sha(ROOT / name) == digest, name
    ready = json.loads((bridge / 'ready.json').read_text())
    assert ready['terminalSizeProbe'] and ready['terminalRows'] == 24
    # Reuse the independently bounded ANSI/cell oracle and exact delivered-prefix
    # checks. NAWS is separately derived here, not inferred from ready metadata.
    cells = audit(out, bridge)
    assert cells['passed'] and cells['different_cells'] == 0
    prm = (out / 'TEST.PRM').read_bytes()
    words = [struct.unpack_from('<H', prm, at)[0] for at in (0x1c2, 0x1c8, 0x1ca, 0x4ec)]
    assert words == [0, 2, 25, 0]
    raw = (bridge / '1-telnet-input.bin').read_bytes()
    application, subs, options = telnet(raw)
    sizes = [struct.unpack('>HH', sub[1:]) for sub in subs if sub[0] == 31 and len(sub) == 5]
    assert sizes == [(80, 24)]
    assert all(sub[0] != 31 or len(sub) == 5 for sub in subs)
    wire = (bridge / '1-serial-input.bin').read_bytes()
    serial_output = (bridge / '1-serial-output.bin').read_bytes()
    report = b'\x1b[8;24;80t'
    assert serial_output.count(b'\x1b[18t') == 1
    assert wire.count(report) == 1 and report not in application
    assert b'UNSAVED' in application
    if producer.get('server') == 'Synchronet':
        assert b'LABUSER\r' in application and b'KEYTEST\r' in application
    else:
        authority = json.loads((out / 'semantic-audit.json').read_text())['authority']
        rows = [json.loads(line) for line in (out / 'server-session.jsonl').read_text().splitlines()]
        assert rows and all(r.get('sessionId') == authority['session_id'] for r in rows)
        server_sizes = [[r['width'], r['height']] for r in rows if r.get('source') == 'NAWS' and r.get('msg') == 'Telnet: Windows size updated']
        assert server_sizes == [[80, 24]]
    paths = [out / 'proxy-integration.json', out / 'TEST.PRM', out / 'screen-reference-audit.json',
             bridge / 'ready.json', bridge / '1-telnet-input.bin', bridge / '1-telnet-output.bin',
             bridge / '1-serial-input.bin', bridge / '1-serial-output.bin']
    result = dict(passed=True, server=producer.get('server', 'ENiGMA'),
                  binary_sha256=producer['binary_sha256'], NAWS=sizes,
                  different_cells=cells['different_cells'], actual_CPR=cells['actual_CPR'],
                  delivered_bytes=cells['delivered_bytes'], actual_query_count=1,
                  size_metadata_not_forwarded=True,
                  subnegotiations_hex=[sub.hex() for sub in subs],
                  application_bytes=len(application), captures={str(p.relative_to(ROOT)): sha(p) for p in paths},
                  sources={str(Path(__file__).relative_to(ROOT)): sha(Path(__file__))}, scope=__doc__)
    (out / 'size-probe-screen-audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print('PASS size probe and stock', result['server'], 'editor cells; NAWS', sizes)


if __name__ == '__main__':
    main()
