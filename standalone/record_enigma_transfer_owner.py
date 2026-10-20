#!/usr/bin/env python3
"""Bind isolated DOS recovery and modeled filesystem failures to staged source."""
import argparse
import json
from datetime import date
from pathlib import Path
import sys

from build_native_mouse import ROOT, sha


def read(path):
    return json.loads(path.read_text())


def current(sources):
    for name, digest in sources.items():
        assert not Path(name).is_absolute() and '..' not in Path(name).parts
        assert sha(ROOT / name) == digest, name


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('normal-candidate', 'fault-candidate', 'server-root', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    for name in ('normal-label', 'fault-label', 'download-label'):
        parser.add_argument('--' + name, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT / 'lab/bbs'))
    from check_enigma_upload_audit import replay, catalog, canceled_prefix, canceled_snapshot, cleanup_fault_evidence
    from enigma_upload_dos import metadata
    from enigma_upload_cancel_watch import events

    evidence = []
    results = {}
    experiments = []
    for fault, candidate, label in ((False, args.normal_candidate, args.normal_label),
                                   (True, args.fault_candidate, args.fault_label)):
        assert label.replace('-', '').replace('_', '').isalnum()
        candidate = candidate.resolve()
        assert candidate.is_relative_to(ROOT / 'build')
        folder = ROOT / 'build/bbs-lab/results/enigma' / label
        result = read(folder / 'upload-checks.json')
        negative = read(folder / 'upload-audit-negative-checks.json')
        assert result['passed'] and result['cancel_first'] and not result['errors']
        assert result['cleanup_error_expected'] is fault
        assert len(result['checks']) == (24 if fault else 21) and all(result['checks'].values())
        assert negative['passed'] and len(negative['cases']) == (26 if fault else 22)
        assert all(case['rejected'] for case in negative['cases'])
        assert negative['checker_sha256'] == result['input_hashes']['time_auditor'] == sha(ROOT / 'lab/bbs/check_enigma_upload_audit.py')
        assert negative['auditor_sha256'] == result['input_hashes']['auditor'] == sha(ROOT / 'lab/bbs/audit_zmodem.py')
        for name, digest in negative['capture_hashes'].items():
            assert sha(folder / name) == digest
        for key, name in [('runner', 'enigma_upload_dos.py'), ('harness', 'test_dos.py'),
                          ('observer', 'test_transfer_dos.py'), ('form_observer', 'enigma_upload_watch.py'),
                          ('cancel_observer', 'enigma_upload_cancel_watch.py'), ('fixture_owner', 'enigma_key_stream_fixture.py'),
                          ('observer_base', 'zmodem_label_watch.py')]:
            assert result['input_hashes'][key] == sha(ROOT / 'lab/bbs' / name)
        fixture = read(candidate / 'search-instance.json')
        assert fixture['upload_fixture'] and fixture['transfer_owner_experiment']
        instance = read(candidate / 'instance.json')
        assert sha(args.server_root / 'core/client.js') == instance['stock_client_sha256']
        for name, digest in {**fixture['fixture_inputs'], **fixture['source_modules']}.items():
            assert sha(candidate / name) == digest == result['input_hashes'][name]
        for name, digest in fixture['source_inputs'].items():
            assert sha(args.server_root / name) == digest
        experiment = read(candidate / 'transfer-owner-experiment.json')
        current(experiment['inputs'])
        for name, digest in experiment['original_core'].items():
            assert sha(args.server_root / name) == digest == fixture['source_inputs'][name]
        for name, digest in experiment['staged_core'].items():
            assert sha(candidate / name) == digest
        for name, source in experiment['authored_core'].items():
            assert sha(ROOT / source['source']) == source['sha256'] == sha(candidate / name)
        experiments.append(experiment)

        expected = {name: (folder / 'SEND' / name).read_bytes() for name in ('PCUP01.BIN', 'EMPTY.BIN')}
        assert len(expected['PCUP01.BIN']) == 65539 and expected['EMPTY.BIN'] == b''
        for name in expected:
            assert sha(folder / 'SEND' / name) == result['expected'][name]['sha256']
        sent = (folder / 'serial-received.bin').read_bytes()
        received = (folder / 'display.bin').read_bytes()
        trace = read(folder / 'trace.json')
        cancel = canceled_prefix(sent, received, trace, expected)
        assert cancel == result['canceled_protocol']
        replay(sent, received, trace, expected, True, True)
        snapshots = read(folder / 'cancel-upload-snapshots.json')
        assert snapshots == result['cancel_snapshots']
        canceled_snapshot(snapshots, fault)
        if fault:
            faults = read(folder / 'cleanup-fault-events.json')
            assert faults == result['filesystem_faults']
            cleanup_fault_evidence(faults, snapshots)
            assert result['input_hashes']['fault_preload'] == sha(ROOT / 'lab/bbs/patches/enigma-transfer-owner/fault-once.js')
            assert not any(p.is_file() for p in (candidate / 'runtime-tmp').rglob('*'))
        forms = events((folder / 'LABELS.BIN').read_bytes())
        assert forms == read(folder / 'upload-form-events.json')
        rows = metadata(candidate, list(expected))
        assert rows == read(folder / 'server-upload-metadata.json')
        catalog(rows, expected, candidate, result['received_date_bounds_ns'])
        results['modeled_cleanup_denial' if fault else 'normal_cleanup'] = dict(
            checks=result['checks'], corruptions_rejected=len(negative['cases']), form_events=forms,
            first_valid_packet_bytes=cancel['first_data']['length'], peer_ACK_position=cancel['ack']['position'],
            canceled_partial_retained=fault, source_files_unchanged=True,
            installed_files=result['expected'], terminal_sha256=result['terminal_sha256'])
        evidence.extend(folder / name for name in ('upload-checks.json', 'upload-audit-negative-checks.json',
            'cancel-upload-snapshots.json', 'LABELS.BIN', 'upload-form-events.json', 'server-upload-metadata.json'))
        if fault:
            evidence.append(folder / 'cleanup-fault-events.json')
        evidence.extend(candidate / name for name in ('search-instance.json', 'transfer-owner-experiment.json'))
    assert experiments[0] == experiments[1]
    assert args.download_label.replace('-', '').replace('_', '').isalnum()
    download_folder = ROOT / 'build/bbs-lab/results/enigma' / args.download_label
    download = read(download_folder / 'repeat-checks.json')
    download_negative = read(download_folder / 'audit-negative-checks.json')
    assert download['passed'] and not download['errors']
    assert len(download['checks']) == 13 and all(download['checks'].values())
    assert download_negative['passed'] and len(download_negative['cases']) == 7
    assert all(case['rejected'] for case in download_negative['cases'])
    assert download_negative['checker_sha256'] == sha(ROOT / 'lab/bbs/check_enigma_repeat_audit.py')
    assert download_negative['auditor_sha256'] == download['runner_sha256'] == sha(ROOT / 'lab/bbs/enigma_repeat_download_dos.py')
    assert download_negative['shared_auditor_sha256'] == sha(ROOT / 'lab/bbs/audit_zmodem.py')
    for name, digest in download_negative['capture_hashes'].items():
        assert sha(download_folder / name) == digest
    candidate = args.fault_candidate.resolve()
    fixture = read(candidate / 'search-instance.json')
    for name, digest in {**fixture['fixture_inputs'], **fixture['source_modules']}.items():
        assert sha(candidate / name) == digest == download['input_hashes'][name]
    for key, name in [('harness', 'test_dos.py'), ('observer', 'test_transfer_dos.py'),
                      ('auditor', 'audit_zmodem.py'), ('label_observer', 'zmodem_label_watch.py')]:
        assert download['input_hashes'][key] == sha(ROOT / 'lab/bbs' / name)
    from enigma_repeat_download_dos import audit, alias, file_state
    archives = fixture['archives'][1:3]
    names = [archive['name'].upper() for archive in archives]
    payloads = {archive['name'].upper(): (candidate / 'file_base/pcplus_games' / archive['name']).read_bytes() for archive in archives}
    transactions = audit((download_folder / 'display.bin').read_bytes(),
                         (download_folder / 'serial-received.bin').read_bytes(),
                         read(download_folder / 'trace.json'), names, payloads)
    assert transactions == download['transactions']
    assert file_state(download_folder / 'RECV') == download['snapshots'][-1]['files']
    for name in names:
        assert (download_folder / 'RECV' / alias(name)).read_bytes() == payloads[name]
    assert not any(p.is_file() for p in (candidate / 'runtime-tmp').rglob('*'))
    evidence.extend(download_folder / name for name in ('repeat-checks.json', 'audit-negative-checks.json', 'finish-file-snapshots.json', 'LABELS.BIN'))
    unit_root = ROOT / 'build/bbs-lab/transfer-owner-unit'
    unit = read(unit_root / 'owner-01/checks.json')
    assert unit['passed'] and len(unit['cases']) == 39 and all(case['passed'] for case in unit['cases'])
    assert unit['checker_sha256'] == sha(ROOT / 'lab/bbs/patches/enigma-transfer-owner/check.js')
    assert unit['exit_probe_sha256'] == sha(ROOT / 'lab/bbs/patches/enigma-transfer-owner/exit-probe.js')
    assert unit['core'] == {name: experiments[0]['staged_core'][name] for name in experiments[0]['changed']}
    rejection_path = ROOT / 'build/bbs-lab/upload-temp-faults/v1-rejection-01/checks.json'
    rejection = read(rejection_path)
    assert rejection['reproduced'] and rejection['completion_callbacks'] == 0
    assert rejection['free_time_depth'] == 0 and rejection['partial_retained']
    assert rejection['unhandled_rejection_code'] == 'EACCES'
    assert rejection['checker_sha256'] == sha(ROOT / 'lab/bbs/patches/enigma-upload-temp/reproduce-rejection.js')
    previous = read(ROOT / 'docs/validation/enigma-upload-cancel.json')
    assert rejection['transfer_sha256'] == previous['staged_server']['staged_core']['core/file_transfer.js']
    assert rejection['temptmp_sha256'] == sha(args.normal_candidate / 'node_modules/temptmp/index.js')
    upstream = read(unit_root / 'upstream-01/checks.json')
    assert upstream['passed'] and upstream['exit_code'] == 0
    assert '141 passing' in (unit_root / 'upstream-01/tests.log').read_text()
    preceding = read(ROOT / 'docs/validation/enigma-upload-time.json')
    current(preceding['source_hashes'])
    assert len(preceding['source_products']) == 31
    for name, digest in preceding['source_products'].items():
        assert sha(ROOT / 'build' / name) == digest
    assert all(r['terminal_sha256'] == preceding['source_products']['terminal/TERMINAL.EXE'] for r in results.values())
    assert download['terminal_sha256'] == preceding['source_products']['terminal/TERMINAL.EXE']
    evidence.extend([unit_root / 'owner-01/checks.json', rejection_path,
        unit_root / 'upstream-01/checks.json', unit_root / 'upstream-01/tests.log',
        ROOT / 'docs/validation/enigma-upload-cancel.json', ROOT / 'docs/validation/enigma-upload-time.json'])
    sources = [ROOT / 'lab/bbs' / n for n in ('enigma_upload_dos.py', 'enigma_key_stream_fixture.py', 'check_enigma_upload_audit.py', 'enigma_repeat_download_dos.py', 'check_enigma_repeat_audit.py')]
    sources.extend(p for p in (ROOT / 'lab/bbs/patches/enigma-transfer-owner').iterdir() if p.is_file() and p.suffix != '.md')
    sources.append(ROOT / 'lab/bbs/patches/enigma-upload-temp/reproduce-rejection.js')
    record = dict(date=date.today().isoformat(), passed=True, whole_application_gates_closed=[],
        workflows=results, ownership_checks=unit['cases'], modeled_filesystem_boundaries=unit['provider_faults_modeled'],
        repeated_download=dict(checks=download['checks'], corruptions_rejected=7,
            transfer_order=[transaction['kind'] for transaction in transactions],
            NFO_after_each_transfer=True, private_temporary_data_removed=True),
        retained_v1_failure=rejection, upstream_regressions=141, staged_server=experiments[0],
        live_client_sha256=sha(args.server_root / 'core/client.js'), live_server_modified=False,
        application_code_changed=False, unchanged_application_products=31, source_products=preceding['source_products'],
        original_build_inputs=[], evidence=[dict(path=str(p.relative_to(ROOT)), sha256=sha(p)) for p in evidence],
        sources={str(p.relative_to(ROOT)): sha(p) for p in sources}, recorder_sha256=sha(Path(__file__)),
        nix_inputs={n: sha(ROOT / n) for n in ('nix/flake.nix', 'nix/flake.lock')},
        limitations=['Separate decoder/transfer-owner candidates; running board remains unchanged.',
            'Deletion and other filesystem failures are modeled at provider boundaries; data and DOS/network workflows are real.',
            'No simultaneous BBS-session acceptance, physical modem or upload carrier-loss claim.',
            'Legacy synchronous protocol-spawn exceptions preserve the original throw after initiating cleanup; complete error UI remains open.',
            'Source-date preservation and full F01–F16 reconstruction remain open.'])
    with args.output.open('x') as output:
        output.write(json.dumps(record, indent=2) + '\n')
    print(args.output)


if __name__ == '__main__':
    main()
