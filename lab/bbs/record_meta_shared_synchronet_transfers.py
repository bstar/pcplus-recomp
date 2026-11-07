#!/usr/bin/env python3
"""Bind actual Synchronet transfers to the selected shared-parent package bytes."""
import argparse
import json
from pathlib import Path
from product_inputs import ROOT, sha


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runtime', type=Path, required=True)
    a = p.parse_args()
    runtime = a.runtime.resolve()
    package = ROOT / 'build/meta-shared-connection-candidate-20261107/package'
    manifest = json.loads((package / 'manifest.json').read_text())
    digest = sha(package / 'PCPLUS/TERMINAL.EXE')
    assert digest == manifest['files']['TERMINAL.EXE']
    receipts, sources, cases = {}, {}, {}
    for direction, size in (('download', 11521), ('upload', 65539)):
        label = f'meta-shared-sync-{direction}-20261107'
        wrapper = ROOT / 'build/bbs-lab' / (label + '-transfer')
        output = ROOT / 'build/bbs-lab/results/synchronet' / label
        bridge = ROOT / 'build/bbs-lab' / (label + '-proxy')
        result = json.loads((wrapper / 'result.json').read_text())
        protocol = json.loads((output / 'result.json').read_text())
        assert result['passed'] and all(result['checks'].values())
        assert protocol['passed'] and all(protocol['checks'].values()) and not protocol['errors']
        assert result['terminal_sha256'] == protocol['binary_sha256'] == digest
        assert protocol['cpu'] == '8086' and result['fixture']['bytes'] == size
        assert protocol['display_layout'] == dict(physical_rows=25, logical_rows=24, status_hidden=0)
        for mapping in ('products', 'server_inputs'):
            for name, expected in result[mapping].items():
                assert sha(ROOT / name) == expected, name
                assert name not in sources or sources[name] == expected
                sources[name] = expected
        for name, expected in result['proxy']['installed_sources'].items():
            assert sha(runtime / name) == expected, name
        for folder in (wrapper, output, bridge):
            for path in folder.rglob('*'):
                if path.is_file():receipts[str(path.relative_to(ROOT))] = sha(path)
        cases[direction] = dict(fixture=result['fixture'], checks=result['checks'],
                               protocol_checks=protocol['checks'], proxy_sources=result['proxy']['installed_sources'])
    states = []
    for phase in ('before', 'after'):
        path = ROOT / f'build/meta-shared-sync-server-{phase}-20261107.json'
        states.append(json.loads(path.read_text()))
        receipts[str(path.relative_to(ROOT))] = sha(path)
    before, after = states
    assert before['pid'] == after['pid'] and before['server_inputs'] == after['server_inputs']
    assert before['message_bodies'] == after['message_bodies']
    for name, expected in after['server_inputs'].items():
        assert sha(ROOT / 'build/bbs-lab/synchronet/runtime' / name) == expected, name
    for name in ('lab/bbs/record_meta_shared_synchronet_transfers.py', 'docs/META_SHARED_SYNCHRONET_TRANSFERS.md'):
        sources[name] = sha(ROOT / name)
    report = dict(checkpoint_verified=True, physical_verified=False, parent_sha256=digest,
                  package_manifest_sha256=sha(package / 'manifest.json'), cases=cases,
                  stock_server=dict(commit=after['source_commit'], binary_sha256=after['binary_sha256'],
                                    static_files=len(after['server_inputs']), upload_message_bodies_unchanged=True),
                  sources=sources, receipts=receipts, original_inputs=[],
                  limitations=[
                      'Owned stock loopback Synchronet and actual on-disk SynthModem proxy; independently audited serial-side transfers.',
                      'Server process/archive/static/message-body snapshots bracket upload, not the earlier download.',
                      'No physical Boca/SPA2102/CTS/SIP/audio timing or full original feature-parity claim.',
                      'No deployed application, BBS configuration or physical bridge service changes.'])
    output = ROOT / 'docs/validation/meta-shared-synchronet-transfers.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print('Verified installed-candidate byte identity with two actual Synchronet/SynthModem transfers')


if __name__ == '__main__':
    main()
