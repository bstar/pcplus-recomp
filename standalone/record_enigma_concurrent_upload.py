#!/usr/bin/env python3
"""Publish sanitized two-session acceptance, retaining earlier harness failures."""
import argparse
import json
from datetime import date
from pathlib import Path
import sys

from build_native_mouse import ROOT, sha


def read(path):
    return json.loads(path.read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--server-root', type=Path, required=True)
    parser.add_argument('--label', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert args.label.replace('-', '').replace('_', '').isalnum()
    candidate = args.candidate.resolve()
    assert candidate.is_relative_to(ROOT / 'build')
    folder = ROOT / 'build/bbs-lab/results/enigma' / args.label
    result = read(folder / 'concurrent-checks.json')
    negative = read(folder / 'concurrent-audit-negative-checks.json')
    assert result['passed'] and len(result['checks']) == 18 and all(result['checks'].values())
    assert len([event for event in result['interrupts'] if event['peer'] == 'locpeer']) >= 2
    assert [form['file'] for form in result['forms']] == ['CONCA.BIN', 'CONCB.BIN']
    for form in result['forms']:
        assert form['row'] in (6, 9, 14)
        assert form['tabs'] == ((2 if form['column'] >= 52 else 3) if form['row'] == 6 else 1 if form['row'] == 9 else 0)
    assert negative['passed'] and len(negative['cases']) == 19 and all(case['rejected'] for case in negative['cases'])
    fixture = read(candidate / 'search-instance.json')
    stage = read(candidate / 'transfer-owner-experiment.json')
    setup = read(candidate / 'concurrent-upload-instance.json')
    assert setup['setup_sha256'] == sha(ROOT / 'lab/bbs/enigma_concurrent_upload.py')
    for name, digest in {**fixture['fixture_inputs'], **fixture['source_modules']}.items():
        assert sha(candidate / name) == digest == result['input_hashes'][name]
    for name, digest in fixture['source_inputs'].items():
        assert sha(args.server_root / name) == digest
    for name, digest in stage['inputs'].items():
        assert sha(ROOT / name) == digest
    for key, name in [('runner', 'lab/bbs/enigma_concurrent_upload.py'), ('peer', 'lab/bbs/synchronet.py'),
                      ('auditor', 'lab/bbs/audit_zmodem.py'), ('encoder', 'standalone/check_zmodem_wire.py')]:
        assert result['input_hashes'][key] == sha(ROOT / name)
    assert result['input_hashes']['setup'] == sha(candidate / 'concurrent-upload-instance.json')
    assert negative['checker_sha256'] == sha(ROOT / 'lab/bbs/check_enigma_concurrent_audit.py')
    assert negative['auditor_sha256'] == sha(ROOT / 'lab/bbs/audit_zmodem.py')
    for name, digest in negative['capture_hashes'].items():
        assert sha(folder / name) == digest
    sys.path.insert(0, str(ROOT / 'lab/bbs'))
    from check_enigma_concurrent_audit import audit, load
    data = load(candidate, folder)
    assert audit(data, candidate) == negative['protocol']
    for name, expected in result['expected'].items():
        assert len(data['expected'][name]) == expected['bytes']
        assert sha(folder / name) == expected['sha256']
    preceding_path = ROOT / 'docs/validation/enigma-transfer-owner.json'
    preceding = read(preceding_path)
    assert preceding['passed'] and preceding['staged_server'] == stage
    assert sha(args.server_root / 'core/client.js') == preceding['live_client_sha256']
    assert len(preceding['source_products']) == 31
    for name, digest in preceding['source_products'].items():
        assert sha(ROOT / 'build' / name) == digest
    application = read(ROOT / 'docs/validation/enigma-upload-time.json')
    for name, digest in application['source_hashes'].items():
        assert sha(ROOT / name) == digest
    early = ROOT / 'build/bbs-lab/results/enigma/owned-transfer-concurrent-01'
    first = read(early / 'snapshots.json')
    assert len(first) == 1
    first_files = first[0]['temporary_files']
    assert len(first_files) == 1 and next(iter(first_files.values()))['bytes'] == 0
    failed = ROOT / 'build/bbs-lab/results/enigma/owned-transfer-concurrent-02'
    failure = read(failed / 'concurrent-checks.json')
    assert not failure['passed'] and failure['error'] == 'TimeoutError: scan pause'
    assert failure['checks']['A_cancel_retires_only_A'] and failure['checks']['canceled_A_not_installed']
    focus_failed = ROOT / 'build/bbs-lab/results/enigma/owned-transfer-concurrent-03/concurrent-checks.json'
    focus = read(focus_failed)
    assert not focus['passed'] and focus['error'] == "AssertionError: ('Unexpected details focus', 9, 52)"
    interrupt_failed = ROOT / 'build/bbs-lab/results/enigma/owned-transfer-concurrent-04/concurrent-checks.json'
    interrupted = read(interrupt_failed)
    assert not interrupted['passed'] and interrupted['error'] == 'TimeoutError: fileBaseSearch'
    assert interrupted['checks']['A_success_preserves_active_B']
    evidence = [folder / name for name in ('concurrent-checks.json', 'concurrent-audit-negative-checks.json',
        'snapshots.json', 'server-upload-metadata.json', 'loclab-protocol.json', 'locpeer-protocol.json')]
    evidence.extend([candidate / 'search-instance.json', candidate / 'transfer-owner-experiment.json',
        candidate / 'concurrent-upload-instance.json', early / 'snapshots.json',
        failed / 'concurrent-checks.json', focus_failed, interrupt_failed, preceding_path])
    record = dict(date=date.today().isoformat(), passed=True, checks=result['checks'],
        corruptions_rejected=len(negative['cases']), expected_files=result['expected'],
        concurrent_sessions=2, client='Declared reference Telnet/ZMODEM peers; not DOS',
        upload_A=['acknowledged partial', 'cancel', 'NFO', 'retry', 'details', 'NFO'],
        upload_B=['acknowledged source data continues during A recovery', 'completion', 'details', 'NFO'],
        active_partial_identity_and_source_preserved=True, all_temporary_data_removed=True,
        detail_form_focus=result['forms'],
        achievement_pauses_acknowledged=result['interrupts'],
        snapshot_prefix_bytes=[next(iter(snapshot['temporary_files'].values()))['bytes'] for snapshot in data['snapshots'][:3]],
        distinct_upload_owners_verified=True,
        retained_harness_failures=[dict(label='owned-transfer-concurrent-01',
            reason='Receiver acknowledged buffered 1KiB while its stdio file still had zero on-disk bytes. Harness now sends8KiB before its first ownership snapshot.'),
            dict(label='owned-transfer-concurrent-02', reason='Raw prompt matching missed ANSI-coloured scan pause. Harness now matches visible text within the processing response.'),
            dict(label='owned-transfer-concurrent-03', reason='The actual details cursor began in the year field. Reference peer now accepts description/tags/year/button positions, matching the established DOS observer.'),
            dict(label='owned-transfer-concurrent-04', reason='New-user upload achievements interrupted File Base entry. The reference peer now acknowledges both visible notices and waits for the actual command prompt before Search.')],
        staged_server=stage, live_client_sha256=preceding['live_client_sha256'], live_server_modified=False,
        application_code_changed=False, unchanged_application_products=31, source_products=preceding['source_products'],
        original_build_inputs=[], sources={name:sha(ROOT / name) for name in ('lab/bbs/enigma_concurrent_upload.py',
            'lab/bbs/check_enigma_concurrent_audit.py')}, recorder_sha256=sha(Path(__file__)),
        nix_inputs={name:sha(ROOT / name) for name in ('nix/flake.nix', 'nix/flake.lock')},
        evidence=[dict(path=str(path.relative_to(ROOT)), sha256=sha(path)) for path in evidence],
        whole_application_gates_closed=[], limitations=[
            'Two real reference-peer upload sessions; simultaneous DOS-client and physical modem acceptance remain open.',
            'This route covers cancellation and successful-upload cleanup while another receive is active, not all multiuser features.',
            'No concurrent file-list protocol network acceptance or simultaneous deletion-error combination is claimed.',
            'Staged keyboard and transfer-owner candidates are not installed on the live board.',
            'Upload carrier loss, original source dates, other doors and full F01–F16 reconstruction remain open.'])
    with args.output.open('x') as output:
        output.write(json.dumps(record, indent=2) + '\n')
    print(args.output)


if __name__ == '__main__':
    main()
