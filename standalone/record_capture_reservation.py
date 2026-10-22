#!/usr/bin/env python3
"""Bind canonical reservation, bank ABI and current-terminal regression evidence."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cohort', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    cohort = args.cohort.resolve()
    target = args.output.resolve()
    assert cohort.is_relative_to(ROOT / 'build') and not target.exists()
    assert target.is_relative_to(ROOT / 'docs/validation')
    proof = read(cohort / 'result.json')
    custody = cohort / 'accepted'
    assert not custody.exists()
    selected = set()
    assert proof['passed'] and all(proof['checks'].values())
    assert proof['checks']['real_far_code_bank_and_resident_helper']
    expected = dict(NORMAL=119, TARGET=16, SCRATCH=16, BANK=119, BNKTARG=16, BNKSCR=16)
    assert set(proof['logs']) == set(expected)
    for name, count in expected.items():
        assert proof['logs'][name].splitlines()[-1] == f'RESERVATION {count} checks 0 failures'
    for name, digest in proof['inputs'].items():
        assert sha(ROOT / name) == sha(cohort / 'frozen-source' / name) == digest, name
        selected.add(ROOT / name)
    for name, digest in proof['captures_sha256'].items():
        assert sha(cohort / name) == digest, name
    for name, digest in proof['binaries'].items():
        assert sha(cohort / name) == digest, name
    binary = ROOT / 'build/terminal/TERMINAL.EXE'
    manifest_path = ROOT / 'build/terminal/manifest.json'
    manifest = read(manifest_path)
    selected.update((binary, manifest_path, ROOT / 'build/terminal/terminal.map'))
    digest = sha(binary)
    assert manifest['kind'] == 'source-only-interactive-dos-terminal' and manifest['binary_sha256'] == digest
    for name, source_digest in manifest['sources'].items():
        assert not name.startswith(('analysis/', 'build/')) and sha(ROOT / name) == source_digest, name
        selected.add(ROOT / name)
    memory = manifest['memory_layout']
    assert memory['near_bytes'] == manifest['data_stack_bytes'] == 64912
    assert memory['resident_code_bytes'] == 65336 and memory['near_spare_bytes'] == 624
    assert memory['resident_code_spare_bytes'] == 200
    assert memory['configuration_bridge_pairs_verified'] == 80 and memory['far_code_bridge_pairs_verified'] == 136
    assert memory['capture_reservation_far_bindings_verified'] == 2 and memory['capture_reservation_initialized_bytes'] == 8
    regressions = {}
    for name in ('capture-file', 'capture-owners', 'capture-session', 'monitor-file'):
        path = ROOT / 'build' / name / 'result.json'
        result = read(path)
        selected.add(path)
        assert result['passed'] and all(result['checks'].values())
        for source, source_digest in result['sources'].items():
            assert sha(ROOT / source) == source_digest, source
            selected.add(ROOT / source)
        for binary_name, binary_digest in result['binaries'].items():
            assert sha(path.parent / binary_name) == binary_digest, binary_name
            selected.add(path.parent / binary_name)
        selected.update(path.parent.joinpath('run').glob('*.TXT'))
        if name in ('capture-owners', 'monitor-file'):
            assert result['static_state_bytes'] == 928 and result['external_reservation_bytes'] == 8
            assert result['snapshot_abi_bytes'] == 96 and result['owner_descriptor_bytes'] == 134
        regressions[name] = dict(result=str(path.relative_to(ROOT)), sha256=sha(path), check_count=len(result['checks']))
    terminal_cases = {}
    for name, filename in [('capture', 'terminal-capture-live-checks.json'),
                           ('history', 'history-export-checks.json'),
                           ('ZMODEM', 'terminal-zmodem-live-checks.json'),
                           ('ABI', 'config-far-checks.json')]:
        path = ROOT / 'build/terminal' / filename
        result = read(path)
        selected.add(path)
        assert result['passed'] and result['binary_sha256'] == digest
        if name == 'capture':
            assert sum(case['inputs'] for case in result['cases']) == 24
        elif name == 'history':
            assert result['inputs'] == 27
            for source, source_digest in result['sources'].items():
                assert sha(ROOT / source) == source_digest, source
        elif name == 'ZMODEM':
            assert result['inputs'] == len(result['cases']) == 78
            assert all(case['passed'] for case in result['cases'])
            assert result['test_sha256'] == sha(ROOT / 'standalone/check_terminal_zmodem_live.py')
        else:
            assert result['memory'] == memory and len(result['rejected_mutations']) == 409
        terminal_cases[name] = dict(result=str(path.relative_to(ROOT)), sha256=sha(path))
    dos_path = ROOT / 'build/terminal-capture-dos/reservation-01/checks.json'
    dos = read(dos_path)
    assert dos['passed'] and dos['binary_sha256'] == digest
    assert {case['case'] for case in dos['cases']} == {'default-filename', 'pause-resume', 'shutdown-flush',
                                                     'readonly-open-failure', 'capture-XMODEM-coexistence'}
    assert len(dos['cases']) == 5 and all(case['passed'] and all(case['checks'].values()) for case in dos['cases'])
    captures = {str(path.relative_to(ROOT)): sha(path) for path in dos_path.parent.rglob('*') if path.is_file()}
    selected.update(ROOT / name for name in captures)
    inputs = {str(path.relative_to(ROOT)): sha(path) for path in [Path(__file__).resolve(),
        ROOT / 'Makefile', ROOT / 'standalone/check_config_far_live.py', ROOT / 'standalone/terminal_memory.py']}
    selected.update(ROOT / name for name in inputs)
    custody.mkdir()
    kept = {}
    for path in sorted(selected):
        copy = custody / path.relative_to(ROOT)
        copy.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, copy)
        assert sha(copy) == sha(path)
        kept[str(copy.relative_to(ROOT))] = sha(copy)
    result = dict(passed=True, reservation_component_accepted=True, recorder_publisher_accepted=False,
                  canonical_reservation_assertions=sum(expected.values()), normal_assertions=238,
                  modeled_ambiguous_close_assertions=64, snapshot_ABI_bytes=96, owner_descriptor_bytes=134,
                  fixed_owner_state_bytes=920, reservation_state_bytes=8,
                  terminal_sha256=digest, terminal_manifest_sha256=sha(manifest_path),
                  terminal_source_inputs=manifest['sources'], memory_layout=memory,
                  standalone=dict(result=str((cohort / 'result.json').relative_to(ROOT)), sha256=sha(cohort / 'result.json')),
                  file_regressions=regressions, linked_regressions=terminal_cases,
                  actual_DOS_capture=dict(result=str(dos_path.relative_to(ROOT)), sha256=sha(dos_path),
                                          cases=[case['case'] for case in dos['cases']], captures_sha256=captures),
                  inputs=inputs, custody_sha256=kept,
                  scope='One stable external far probe/context reserves canonical identities alongside four fixed '
                        'capture/screen/monitor/history owners. Existing open and ambiguous owners reject registration; '
                        'later colliding opens reject before mutation or IO, while independent paths remain available. '
                        'Probe reentry and wrong-owner release are guarded. Normal DOS and a genuinely separate '
                        'code-bank campaign each pass119 assertions; four16-assertion ambiguous-close campaigns use '
                        'declared kernel models. Two compiled far call sites/relocations and eight initialized bytes '
                        'are checked in the current terminal, with409 damaged ABI/layout cases rejecting. '
                        'Current five DOS capture,24 linked capture,27 history and78 ZMODEM workflows pass. '
                        'No recorder scratch publisher, Record UI, new current-binary BBS/audio, external-process '
                        'lock, host inode identity, physical hardware or F01-F16 whole-application acceptance.')
    with target.open('x') as stream:
        stream.write(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(passed=True, reservation_assertions=302, ABI_negatives=409, terminal_sha256=digest)))


if __name__ == '__main__':
    main()
