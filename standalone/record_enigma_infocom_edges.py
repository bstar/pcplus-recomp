#!/usr/bin/env python3
"""Bind save-read candidate, actual worker failure/recovery and DOS workflows."""
import argparse
from datetime import date
import json
from pathlib import Path
import sys

from build_native_mouse import ROOT, sha


def read(path):
    return json.loads(path.read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('candidate', 'server-root', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    for name in ('cancel-label', 'overwrite-label', 'corrupt-label'):
        parser.add_argument('--' + name, required=True)
    args = parser.parse_args()
    candidate = args.candidate.resolve()
    assert candidate.is_relative_to(ROOT / 'build')
    fixture = read(candidate / 'infocom-save-instance.json')
    stage = read(candidate / 'save-read-experiment.json')
    assert fixture['save_read_experiment']
    for name, digest in fixture['source_inputs'].items():
        assert sha(args.server_root / name) == digest
    for name, digest in fixture['fixture_inputs'].items():
        assert sha(candidate / name) == digest
    for name, digest in stage['inputs'].items():
        assert sha(ROOT / name) == digest
    sys.path.insert(0, str(ROOT / 'lab/bbs'))
    from enigma_infocom_edges_dos import audit, quetzal_identity
    from check_enigma_infocom_edges import save_policy
    story = (candidate / next(name for name in fixture['fixture_inputs'] if name.startswith('local/infocom/'))).read_bytes()
    routes, evidence = {}, []
    for mode, label, count, negatives in [('cancel', args.cancel_label, 13, 9),
        ('overwrite', args.overwrite_label, 14, 10), ('corrupt', args.corrupt_label, 14, 9)]:
        assert label.replace('-', '').replace('_', '').isalnum()
        folder = ROOT / 'build/bbs-lab/results/enigma' / label
        result = read(folder / 'infocom-edge-checks.json')
        negative = read(folder / 'infocom-edge-audit.json')
        assert result['passed'] and result['mode'] == mode and len(result['checks']) == count and all(result['checks'].values())
        assert negative['passed'] and len(negative['cases']) == negatives and all(case['rejected'] for case in negative['cases'])
        assert negative['runner_sha256'] == result['input_hashes']['runner'] == sha(ROOT / 'lab/bbs/enigma_infocom_edges_dos.py')
        assert negative['checker_sha256'] == sha(ROOT / 'lab/bbs/check_enigma_infocom_edges.py')
        for name, digest in negative['captures'].items():
            assert sha(ROOT / name) == digest
        for name, digest in fixture['fixture_inputs'].items():
            assert result['input_hashes']['candidate/' + name] == digest
        for name, digest in fixture['source_inputs'].items():
            assert result['input_hashes']['source/' + name] == digest
        assert result['input_hashes']['harness'] == sha(ROOT / 'lab/bbs/test_dos.py')
        for name in ('TERMINAL.EXE', 'ASPECT.EXE', 'ASPCOMP.EXE'):
            assert result['input_hashes']['staged/' + name] == sha(folder / 'program' / name)
        assert result['input_hashes']['login'] == sha(folder / 'program/LOGON.ASP')
        rows = [json.loads(line) for line in (folder / 'server-session.jsonl').read_text().splitlines()]
        assert all(audit(mode, (folder / 'display-clean.txt').read_text(), (folder / 'bbs-sent.bin').read_bytes(), rows).values())
        save_policy(result, result['snapshots'], story)
        for snapshot in result['snapshots']:
            assert sha(folder / snapshot['snapshot']) == snapshot['sha256']
            assert quetzal_identity((folder / snapshot['snapshot']).read_bytes(), story)
        routes[mode] = dict(checks=result['checks'], corruptions_rejected=negatives,
            saved_files=[dict(bytes=row['bytes'], sha256=row['sha256']) for row in result['saved_files']])
        evidence.extend([folder / 'infocom-edge-checks.json', folder / 'infocom-edge-audit.json'])
        evidence.extend(folder / snapshot['snapshot'] for snapshot in result['snapshots'])
        if mode == 'corrupt':
            assert (folder / 'broken-fixture.bin').read_bytes() == b'not a Quetzal save\n'
            evidence.append(folder / 'broken-fixture.bin')
    baseline_dir = ROOT / 'build/bbs-lab/infocom-edge-worker-01'
    fixed_dir = ROOT / 'build/bbs-lab/infocom-edge-worker-03'
    baseline, fixed = read(baseline_dir / 'checks.json'), read(fixed_dir / 'checks.json')
    assert baseline['completed_control_paths'] and not baseline['corrupt_restore_survived']
    assert baseline['errors'] == ['Not an IFF file'] and baseline['overwrite_changed_save']
    assert fixed['completed_control_paths'] and fixed['corrupt_restore_survived'] and fixed['overwrite_changed_save'] and not fixed['errors']
    assert baseline['runner_sha256'] == fixed['runner_sha256'] == sha(ROOT / 'lab/bbs/enigma_infocom_edge_worker.js')
    assert baseline['source_hashes'] == stage['original_core']
    assert fixed['source_hashes'] == {name: digest for name, digest in stage['staged_core'].items() if not name.endswith('/save_read.js')}
    unit_path = ROOT / 'build/bbs-lab/infocom-save-read-unit-01/checks.json'
    unit = read(unit_path)
    assert unit['passed'] and len(unit['cases']) == 49 and all(case['passed'] for case in unit['cases'])
    assert unit['checker_sha256'] == sha(ROOT / 'lab/bbs/patches/enigma-save-read/check.js')
    assert unit['source_hashes'] == stage['staged_core']
    assert unit['samples'] == {name: sha(fixed_dir / (name + '.glksave')) for name in ('north', 'west')}
    failed_init = ROOT / 'build/bbs-lab/infocom-edge-worker-02/failure.txt'
    assert 'Worker ended while waiting for initial game' in failed_init.read_text()
    application = read(ROOT / 'docs/validation/enigma-upload-time.json')
    for name, digest in application['source_hashes'].items():
        assert sha(ROOT / name) == digest
    for name, digest in application['source_products'].items():
        assert sha(ROOT / 'build' / name) == digest
    assert len(application['source_products']) == 31
    overwrite_save = routes['overwrite']['saved_files'][0]['sha256']
    assert any(saved['sha256'] == overwrite_save for saved in routes['corrupt']['saved_files'])
    for label in (args.cancel_label, args.overwrite_label, args.corrupt_label):
        result = read(ROOT / 'build/bbs-lab/results/enigma' / label / 'infocom-edge-checks.json')
        for name in ('terminal/TERMINAL.EXE', 'aspect-runner/ASPECT.EXE', 'aspect-compiler-dos/ASPCOMP.EXE'):
            assert result['input_hashes'][name] == application['source_products'][name]
    evidence.extend([candidate / 'infocom-save-instance.json', candidate / 'save-read-experiment.json',
        baseline_dir / 'checks.json', fixed_dir / 'checks.json', unit_path, failed_init,
        ROOT / 'docs/validation/enigma-upload-time.json'])
    sources = ['lab/bbs/enigma_infocom_edges_dos.py', 'lab/bbs/enigma_infocom_edge_worker.js',
        'lab/bbs/check_enigma_infocom_edges.py', 'lab/bbs/patches/enigma-save-read/check.js',
        'lab/bbs/patches/enigma-save-read/stage.py', 'lab/bbs/patches/enigma-save-read/save_read.js',
        'lab/bbs/patches/enigma-save-read/save-read.patch']
    dependencies = ['ifvms/src/common/file.js', 'ifvms/src/zvm/runtime.js', 'ifvms/src/zvm.js',
        'glkote-term/src/electrofs.js', 'glkote-term/src/glkapi.js']
    record = dict(date=date.today().isoformat(), passed=True, workflows=routes, component_checks=unit['cases'],
        modeled_component_boundaries=unit['modeled_boundaries'],
        original_worker_failure=dict(corrupt_restore_survived=False, error='Not an IFF file'),
        fixed_worker_survived=True, staged_server=stage, live_server_modified=False,
        retained_candidate_failure='First staged initializer read VM options before prepare; deferred stack-limit lookup fixes startup.',
        observed_dependency_sources={name: sha(candidate / 'node_modules' / name) for name in dependencies},
        source_products=application['source_products'], unchanged_application_products=31, application_code_changed=False,
        original_build_inputs=[], whole_application_gates_closed=[],
        sources={name: sha(ROOT / name) for name in sources}, recorder_sha256=sha(Path(__file__)),
        evidence=[dict(path=str(path.relative_to(ROOT)), sha256=sha(path)) for path in evidence],
        nix_inputs={name: sha(ROOT / name) for name in ('nix/flake.nix', 'nix/flake.lock')},
        limitations=['One owned Zork release, direct isolated ZORK menu, source-built DOS and modeled19200/HARD UART.',
            'Validation rejects the tested structural/story/bounds faults; it does not prove all variable values in structurally valid saves are meaningful.',
            'Immutable validated bytes prevent later file replacement from altering that read; concurrent save writers and write publication are unverified.',
            'Live deployment/menu route, physical modem, other doors and full F01–F16 reconstruction remain open.'])
    with args.output.open('x') as output:
        output.write(json.dumps(record, indent=2) + '\n')
    print(args.output)


if __name__ == '__main__':
    main()
