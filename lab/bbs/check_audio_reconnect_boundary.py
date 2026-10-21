#!/usr/bin/env python3
"""Check the stop observer against the retained in-flight ACK failure."""
import argparse
import json
from pathlib import Path
from audio_synchronet import ROOT, sha
from audio_reconnect_boundary import acknowledged_prefix


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT / 'build') and not out.exists()
    retained = ROOT / 'build/bbs-lab/current-synchronet-reconnect-audio-01'
    receipt = json.loads((ROOT / 'docs/validation/current-synchronet-reconnect-audio-01.json').read_text())
    files = [retained / 'call-1/adapter-up.bin', retained / 'bbs-1/input.bin']
    for file in files:
        assert sha(file) == receipt['capture_sha256'][str(file.relative_to(retained))]
    upstream, wire = [p.read_bytes() for p in files]
    assert upstream.endswith(b'\x06') and len(upstream) == 113
    cases = dict(
        retained_inflight_ACK_waits=acknowledged_prefix(upstream, wire) is None,
        delivered_ACK_releases=acknowledged_prefix(upstream, wire + b'\x06') is not None,
        wrong_ACK_waits=acknowledged_prefix(upstream, wire + b'\x15') is None,
        duplicate_ACK_waits=acknowledged_prefix(upstream, wire + b'\x06\x06') is None,
        missing_prefix_byte_waits=acknowledged_prefix(upstream, wire[1:] + b'\x06') is None,
        non_ACK_tail_waits=acknowledged_prefix(upstream + b'X', wire + b'\x06X') is None,
        invalid_address_waits=acknowledged_prefix(b'example.com\r' + upstream.split(b'\r', 1)[1], wire + b'\x06') is None)
    result = dict(passed=all(cases.values()), checks=cases,
                  inputs={str(p.relative_to(ROOT)): sha(p) for p in [Path(__file__).resolve(), ROOT / 'lab/bbs/audio_reconnect_boundary.py', ROOT / 'lab/bbs/modem.py', *files]},
                  scope='Read-only stop-observer checks using the retained one-byte in-flight ACK discrepancy and isolated mutations. No new DOS/audio execution or compatibility acceptance; complete final upstream audits remain mandatory.')
    out.mkdir(parents=True)
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))
    assert result['passed']


if __name__ == '__main__':
    main()
