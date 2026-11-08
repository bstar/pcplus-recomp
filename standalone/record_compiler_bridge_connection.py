#!/usr/bin/env python3
"""Bind current-payload LoC, cancellation and live-source carrier evidence.

Publishes hashes and bounded software results only, never private art/config,
executables, packet captures or a physical/release acceptance claim.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('payload', 'loc', 'cancel', 'cancel-controls', 'carrier',
                 'carrier-audit', 'carrier-controls', 'observer-controls', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    receipts = {}

    def report(path):
        path = path.resolve()
        assert path.is_relative_to(ROOT / 'build')
        value = json.loads(path.read_text())
        assert value['passed'], path
        receipts[str(path.relative_to(ROOT))] = sha(path)
        for field in ('sources', 'captures'):
            for name, digest in value.get(field, {}).items():
                assert sha(ROOT / name) == digest, name
        return value

    payload = report(args.payload / 'package.json')
    assert len(payload['products']) == 9
    for name, digest in payload['products'].items():
        assert sha(args.payload / name) == digest, name
    parent = payload['products']['TERMINAL.EXE']
    loc = report(args.loc)
    cancel = report(args.cancel)
    carrier = report(args.carrier)
    audit = report(args.carrier_audit)
    observer = report(args.observer_controls)
    assert loc['binary_sha256'] == cancel['terminal_sha256'] == audit['terminal_sha256'] == parent
    assert carrier['live_source'] and carrier['cpu'] == '386' and carrier['explicit_UMB']
    assert not carrier['startup_probe'] and not carrier['exec_probe']
    assert all(carrier['checks'].values()) and not carrier['errors']
    assert not carrier['startup_source']['compile_before_parent']
    assert carrier['startup_source']['initial_ASX_absent']
    for name, product in carrier['products'].items():
        assert product['sha256'] == payload['products'][name], name
    assert loc['matched_reference_cells'] == 1920 and loc['matched_source_art_cells'] == 1906
    assert (loc['physical_rows'], loc['logical_rows'], loc['status_hidden'], loc['field_cells']) == (25, 24, 0, 14)
    assert cancel['partial_disk_bytes'] == 4096 and cancel['exact_retry']
    assert cancel['same_DOS_process'] and cancel['authenticated_sessions'] == cancel['proxy_connections'] == 1
    assert audit['exact_retry_bytes'] == cancel['payload_bytes'] == 65539
    assert audit['partial_disk_bytes'] == 4096
    assert audit['payload_sha256'] == cancel['payload_sha256']
    controls = {}
    for name, path in (('cancel', args.cancel_controls), ('carrier', args.carrier_controls)):
        value = report(path)
        assert all(case['passed'] for case in value['cases'])
        assert [case['case'] for case in value['cases'] if not case['rejected']] == ['unchanged']
        controls[name] = value['cases']
    assert observer['restored'] == 1
    record = dict(
        checkpoint_verified=True, application_bytes_changed=False,
        installed_changed=False, selector_changed=False, release_eligible=False,
        physical_verified=False, original_application_build_inputs=[],
        products=payload['products'],
        loc=dict(cpu='8086', physical_rows=25, logical_rows=24, status_hidden=0,
                 reference_cells=1920, source_art_cells=1906, field_cells=14,
                 actual_CPR=loc['actual_CPR'], all_39_native_labels=loc['all_39_native_labels'],
                 message_menu_return=loc['message_menu_return']),
        cancel=dict(bytes=65539, partial_disk_bytes=4096, exact_retry=True,
                    payload_sha256=cancel['payload_sha256'], same_DOS_process=True,
                    authenticated_sessions=1, proxy_connections=cancel['proxy_connections']),
        carrier=dict(cpu=carrier['cpu'], explicit_UMB=True, live_source_compile=True,
                     transfer_wait_ms=carrier['transfer_wait_ms'], checks=carrier['checks'],
                     partial_disk_bytes=audit['partial_disk_bytes'], exact_retry_bytes=65539,
                     sessions=audit['sessions'], notices=audit['notices']),
        negative_controls=controls, observer_controls=observer,
        receipts=receipts,
        sources={'standalone/record_compiler_bridge_connection.py': sha(__file__)},
        remaining=[
            'Physical Boca/SPA2102/SynthModem/LoC Enigma and Synchronet acceptance.',
            'Full release packaging and selected-package/deployment promotion.',
            'Full ASPECT, other emulations/protocols and Host parity.',
            'Other memory layouts, all live-board screens and physical timing.'
        ])
    args.output.write_text(json.dumps(record, indent=2) + '\n')
    print('Verified current compiler-bridge LoC/cancel/live-source carrier evidence')


if __name__ == '__main__':
    main()
