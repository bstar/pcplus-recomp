#!/usr/bin/env python3
"""Bind shared-parent stock Enigma transfers through the actual SynthModem proxy."""
import argparse
import json
from pathlib import Path
from product_inputs import ROOT, sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', type=Path, required=True)
    args = parser.parse_args()
    runtime = args.runtime.resolve()
    parent = ROOT / 'build/meta-shared-help-seventh-20261107/TERMINAL.EXE'
    receipts, sources, cases = {}, {}, {}
    for direction, label, size in (
            ('download', 'meta-shared-enigma-transfer-sized-20261107', 11521),
            ('upload', 'meta-shared-enigma-transfer-upload-20261107', 65539)):
        wrapper = ROOT / 'build/bbs-lab' / (label + '-transfer')
        output = ROOT / 'build/bbs-lab/results/enigma' / label
        bridge = ROOT / 'build/bbs-lab' / (label + '-proxy')
        path = wrapper / 'result.json'
        result = json.loads(path.read_text())
        assert result['passed'] and all(result['checks'].values())
        assert all(result['protocol_checks'].values()) and not result['protocol_errors']
        assert result['terminal_sha256'] == sha(parent) and result['mode'] == direction
        assert result['fixture']['bytes'] == size
        assert result['display_layout'] == dict(physical_rows=25, logical_rows=24, status_hidden=0)
        protocol = json.loads((output / 'result.json').read_text())
        assert protocol['passed'] and protocol['binary_sha256'] == sha(parent)
        assert protocol['cpu'] == '8086' and protocol['raw_upstream']
        for mapping in ('product_inputs', 'server_inputs'):
            for name, expected in result[mapping].items():
                assert sha(ROOT / name) == expected, name
                assert name not in sources or sources[name] == expected
                sources[name] = expected
        for name, expected in result['proxy']['installed_sources'].items():
            assert sha(runtime / name) == expected, name
        for folder in (wrapper, output, bridge):
            for capture in folder.rglob('*'):
                if capture.is_file():
                    receipts[str(capture.relative_to(ROOT))] = sha(capture)
        cases[direction] = dict(fixture=result['fixture'], checks=result['checks'],
                                protocol_checks=result['protocol_checks'], cpu=protocol['cpu'],
                                display_layout=result['display_layout'],
                                proxy_sources=result['proxy']['installed_sources'])
    for name in ('lab/bbs/record_meta_shared_transfers.py', 'docs/META_SHARED_ENIGMA_TRANSFERS.md'):
        sources[name] = sha(ROOT / name)
    report = dict(checkpoint_verified=True, release_eligible=False, installed_changed=False,
                  physical_verified=False, parent_sha256=sha(parent), cases=cases,
                  sources=sources, receipts=receipts,
                  limitations=[
                      'Owned stock loopback Enigma and actual on-disk SynthModem Telnet proxy; Hayes shim supplies serial modem commands only.',
                      'No physical Boca, SPA2102, SIP/audio or actual RTS/CTS timing acceptance.',
                      'First unspecified-display fixture stopped before connection; accepted cases explicitly set VGA25/status-visible.',
                      'Synchronet current-product UI coverage is separate from these Enigma transfers; full original feature parity remains open.'])
    output = ROOT / 'docs/validation/meta-shared-enigma-transfers.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print('Verified actual Enigma/SynthModem transfers:', len(cases))


if __name__ == '__main__':
    main()
