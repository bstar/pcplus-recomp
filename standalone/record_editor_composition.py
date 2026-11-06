#!/usr/bin/env python3
"""Seal Alt-A Enigma/transfer/recovery evidence without hiding failed controls."""
import argparse
import json
from pathlib import Path
from build_path_session import ROOT, sha
from terminal_memory import inspect_terminal_memory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    assert output.is_relative_to(ROOT / 'build') and not output.exists()
    binary = ROOT / 'build/editor-parent-v2-20261106/TERMINAL.EXE'
    digest = sha(binary)
    manifest = json.loads(binary.with_name('manifest.json').read_text())
    assert manifest['experimental_external_editor'] and manifest['binary_sha256'] == digest
    for name, expected in manifest['sources'].items():
        assert sha(ROOT / name) == expected, name

    def bind(path):
        return dict(path=str(path.relative_to(ROOT)), sha256=sha(path))

    def read(path, passed=True, product=digest):
        report = json.loads(path.read_text())
        assert report['passed'] == passed, path
        assert report['binary_sha256'] == product, path
        for name, expected in report.get('sources', report.get('product_inputs', {})).items():
            assert sha(ROOT / name) == expected, name
        if passed and 'checks' in report:
            assert all(report['checks'].values()), path
        return report

    base = ROOT / 'build/bbs-lab/results'
    enigma_path = base / 'enigma/editor-v2-enigma-framed-20261106/proxy-integration.json'
    enigma = read(enigma_path)
    child = enigma['external_viewer']
    assert child['passed'] and child['external_command_tool'] == 'editor'
    assert all(child['checks'].values()) and child['checks']['independent_viewer_setting']
    assert enigma['bridge']['inputSequenceTimeoutMs'] == 250
    assert enigma['bridge']['inputByteDelayMs'] == 20
    audit_path = enigma_path.with_name('screen-reference-audit.json')
    audit = read(audit_path)
    assert audit['matched_cells'] == 1920 and audit['different_cells'] == 0
    for path, expected in audit['captures'].items():
        assert sha(Path(path)) == expected, path

    transfer_path = ROOT / 'build/editor-transfers-20261106/result.json'
    transfer = read(transfer_path)
    assert transfer['external_command_tool'] == 'editor'
    assert {c['case'] for c in transfer['cases']} == {
        'x-rx-binary', 'x-tx-binary', 'y-rx-cancel-retry',
        'y-tx-binary', 'z-rx-default', 'z-tx-escape'}
    for case in transfer['cases']:
        assert case['passed'] and case['terminal_sha256'] == digest
        assert all(case['checks'].values()) and case['checks']['actual_external_child']
    retry = next(c for c in transfer['cases'] if c['case'] == 'y-rx-cancel-retry')
    assert all(retry['checks'][k] for k in ['actual_CAN_pair',
               'cancelled_and_resumed_before_retry', 'retry_completed_same_connection'])

    recovery = []
    for name in ['editor-child-carrier-20261106', 'editor-transfer-carrier-20261106']:
        path = ROOT / 'build' / name / 'result.json'
        report = read(path)
        assert report['external_command_tool'] == 'editor' and len(report['cases']) == 2
        for case in report['cases']:
            assert case['passed'] and all(case['checks'].values())
            for key in ['two_actual_connections', 'keyboard_after_redial', 'real_modem_loss']:
                assert case['checks'][key]
        recovery.append(bind(path))

    controls = []
    for label, product in [
        ('editor-v2-enigma-20261106', digest),
        ('viewer-v6-unframed-control-20261106',
         '2d626fb001bed53d3fb3c3a49ea1859f17e69b6ade07792c3a160043ff0a6c02')]:
        path = base / 'enigma' / label / 'proxy-integration.json'
        report = read(path, False, product)
        assert report['external_viewer']['passed']
        assert report['bridge']['inputSequenceTimeoutMs'] == 0
        assert report['bridge']['inputByteDelayMs'] == 2
        assert not report['checks']['semantic_audit'] and not report['checks']['exact_screen']
        controls.append(dict(report=bind(path), failed_checks=[k for k, v in report['checks'].items() if not v]))

    sync_path = base / 'synchronet/editor-v2-synchronet-run-20261106/proxy-integration.json'
    sync = read(sync_path, False)
    assert not sync['checks']['actual_ASPECT_login']
    sync_control_path = base / 'synchronet/viewer-v6-synchronet-control-20261106/proxy-integration.json'
    sync_control = read(sync_control_path, True,
                        '2d626fb001bed53d3fb3c3a49ea1859f17e69b6ade07792c3a160043ff0a6c02')
    assert sync_control['checks']['actual_ASPECT_login']
    assert sync['interpreter_sha256'] == sync_control['interpreter_sha256']
    assert sync['external_observer_segment'] == sync_control['external_observer_segment'] >= 0xa000
    assert sync['external_key_helper_segment'] == sync_control['external_key_helper_segment'] >= 0xa000
    old_binary = ROOT / 'build/editor-disabled-v6-20261106/TERMINAL.EXE'
    new_memory = inspect_terminal_memory(binary, binary.with_name('terminal.map'))
    old_memory = inspect_terminal_memory(old_binary, old_binary.with_name('terminal.map'))
    retained = new_memory['minimum_allocated_module_bytes']
    previous = old_memory['minimum_allocated_module_bytes']
    assert (retained, previous) == (482880, 482400)
    result = dict(passed=True, binary_sha256=digest, enigma=bind(enigma_path),
                  independent_screen=bind(audit_path), matched_cells=1920, different_cells=0,
                  transfers=bind(transfer_path), carrier_recovery=recovery,
                  framing_disabled_failures=controls, synchronet_unaccepted=bind(sync_path),
                  synchronet_reviewed_control=bind(sync_control_path),
                  retained_module_bytes=retained, reviewed_module_bytes=previous,
                  additional_parent_bytes=retained-previous,
                  synchronet_failed_checks=[k for k, v in sync['checks'].items() if not v],
                  application_changed=False, deployment_changed=False,
                  sources={n: sha(ROOT / n) for n in ['standalone/record_editor_composition.py', 'standalone/terminal_memory.py']},
                  limits=['Receipt seals the stated successes and failures; it does not accept every compatibility gate.',
                          'Enigma requires tested framing250ms and20ms paced serial input; disabled-framing failures remain explicit.',
                          'Synchronet editor candidate did not start its ASPECT login; remains unaccepted.',
                          'Synthetic DOS serial/DCD and loopback BBSes; physical SIP/audio/CTS and arbitrary children remain open.',
                          'No selected-package, private settings, live bridge or hardware changes.'])
    output.mkdir()
    (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print('PASS scoped Enigma/6 transfers/4 recovery receipts; preserve2 framing failures and unaccepted Synchronet')


if __name__ == '__main__':
    main()
