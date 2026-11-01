#!/usr/bin/env python3
"""Independently bind queue/claim DOS evidence, source reproduction and parent ABI."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re

from terminal_memory import inspect_terminal_memory
from omf_imports import records

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def verify_dos(folder, report):
    assert report['passed'] and all(report['checks'].values()) and report['original_inputs'] == []
    assert set(report['variants']) == {'near', 'far', 'bank'}
    assert all(sha(ROOT / name) == value for name, value in report['inputs'].items())
    heading = b'\r\nNAME                                NUMBER    DATE    ONLINE  OFFLINE  ELAPSED'
    start = b'\r\n' + b'LoC LAB'.ljust(22) + b' ' + b'5550100'.rjust(20) + b' 12/31/99 23:59:58 '
    assertions = 0
    for variant, result in report['variants'].items():
        directory = folder / variant
        assert result['passed'] and all(result['checks'].values()) and set(result['cases']) == set(map(str, range(5)))
        assert sha(directory / 'QUEUE.EXE') == result['binary_sha256']
        assert (directory / 'PASS.TXT').is_file() and not (directory / 'FAIL.TXT').exists()
        before, after = (directory / 'BEFORE.BIN').read_bytes(), (directory / 'AFTER.BIN').read_bytes()
        assert len(before) == 42 and before == after
        for case, row in result['cases'].items():
            location = directory / f'T{int(case):03}'
            assert row['passed'] and all(row['checks'].values())
            stdout = (location / 'RESULT.TXT').read_bytes()
            match = re.fullmatch(rb'LOGCLAIM (\d+) checks 0 failures\r\n', stdout)
            assert match and int(match[1]) == row['assertions'] and stdout.decode('ascii') == row['stdout']
            assert row['assertions'] >= 35
            assertions += row['assertions']
            expected = heading + start + (b'' if case == '2' else b'00:00:03 00:00:05')
            assert (location / 'CALLS.FON').read_bytes() == expected
            assert not (location / 'OTHER.FON').exists()
    return assertions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('terminal', 'dos', 'source', 'application', 'controls', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    parent, dos, source = args.terminal.resolve(), args.dos.resolve(), args.source.resolve()
    application_path = args.application.resolve()
    controls_path = args.controls.resolve()
    assert all(p.is_relative_to(ROOT / 'build') for p in (parent, dos, source, application_path, controls_path))
    native = read(dos / 'result.json')
    assertions = verify_dos(dos, native)
    manifest = read(parent / 'manifest.json')
    assert manifest['experimental_phone_log_reservations']
    assert sha(parent / 'TERMINAL.EXE') == manifest['binary_sha256']
    memory = inspect_terminal_memory(parent / 'TERMINAL.EXE', parent / 'terminal.map')
    assert memory == manifest['memory_layout']
    assert memory['phone_log_far_queue_bytes'] == 666 and memory['phone_log_claim_far_calls_verified'] == 2
    assert memory['phone_log_entry_pairs_verified'] == 10 and memory['phone_log_callback_pairs_verified'] == 18
    assert memory['near_spare_bytes'] > 0
    proof = read(source / 'result.json')
    assert proof['passed'] and proof['original_inputs'] == [] and proof['actual_DOS_workflows'] == 15
    assert proof['source_count'] == len(proof['sources']) and '--phone-log-reservations' in proof['flags']
    assert proof['terminal_sha256'] == manifest['binary_sha256'] and proof['terminal_memory'] == memory
    fresh = source / 'source'
    assert not (fresh / 'analysis').exists() and not (fresh / 'install').exists()
    for name, digest in proof['sources'].items():
        assert sha(ROOT / name) == sha(fresh / name) == digest
    rebuilt = fresh / 'build' / parent.name
    repeated_manifest = read(rebuilt / 'manifest.json')
    expected_manifest = copy.deepcopy(manifest)
    for field, variation in proof['source_path_object_variations'].items():
        assert field in ('compiler_object_sha256', 'normalized_object_sha256')
        assert variation['only_source_paths_differ']
        original, repeated = parent / variation['object'], rebuilt / variation['object']
        old, new = sha(original), sha(repeated)
        assert old == manifest['zmodem_compiler_helper_adapters'][field] == variation['reference_sha256']
        assert new == repeated_manifest['zmodem_compiler_helper_adapters'][field] == variation['rebuild_sha256']
        a, b = records(original.read_bytes()), records(repeated.read_bytes())
        assert len(a) == len(b)
        changed = []
        for index, (left, right) in enumerate(zip(a, b)):
            if left == right:
                continue
            assert left[0] == right[0]
            if left[0] == 0x80:
                offset = 0
            else:
                assert left[0] == 0x88 and left[1][:2] == right[1][:2] == b'\x80\xe9'
                assert left[1][:6] == right[1][:6]
                offset = 6
            x, y = left[1], right[1]
            assert x[offset] == len(x) - offset - 1 and y[offset] == len(y) - offset - 1
            first = Path(x[offset + 1:].decode('ascii')).relative_to(ROOT)
            second = Path(y[offset + 1:].decode('ascii')).relative_to(fresh)
            assert first == second and '..' not in first.parts
            assert sha(ROOT / first) == sha(fresh / second)
            changed.append(index)
        assert changed == variation['changed_records']
        expected_manifest['zmodem_compiler_helper_adapters'][field] = new
    assert repeated_manifest == expected_manifest
    assert sha(rebuilt / 'TERMINAL.EXE') == manifest['binary_sha256']
    replay = fresh / 'build/claims-regression'
    assert sha(replay / 'result.json') == proof['repeated_DOS_sha256']
    assert verify_dos(replay, read(replay / 'result.json')) == assertions
    application = read(application_path / 'checks.json')
    assert application['passed'] and all(application['checks'].values())
    assert application['terminal_sha256'] == manifest['binary_sha256'] and len(application['cases']) == 2
    assert all(sha(ROOT / name) == digest for name, digest in application['sources'].items())
    controls = read(controls_path)
    assert controls and all(sha(ROOT / name) == digest for name, digest in controls.items())
    # Counterexamples must fail even if a copied producer still says passed.
    mutations = []
    for label, mutate in (
        ('missing-case', lambda d: d['variants']['near']['cases'].pop('4')),
        ('false-count', lambda d: d['variants']['far']['cases']['0'].__setitem__('assertions', 1)),
        ('wrong-executable', lambda d: d['variants']['bank'].__setitem__('binary_sha256', '0' * 64)),
        ('failed-check', lambda d: d['variants']['near']['cases']['2']['checks'].__setitem__('exact_log', False)),
    ):
        damaged = copy.deepcopy(native)
        mutate(damaged)
        try:
            verify_dos(dos, damaged)
        except (AssertionError, KeyError):
            mutations.append(label)
        else:
            raise AssertionError('Accepted damaged evidence: ' + label)
    artifacts = {}
    for folder in (dos, source, parent, application_path):
        for path in folder.rglob('*'):
            if path.is_file():
                artifacts[str(path.relative_to(ROOT))] = sha(path)
    report = dict(passed=True, full_compatibility=False, accepted_for_deployment=False,
                  native_DOS_workflows=15, native_assertions=assertions,
                  source_DOS_workflows=15, source_count=proof['source_count'],
                  terminal_sha256=manifest['binary_sha256'], memory=memory,
                  terminal_DOS_cases=2, unchanged_controls=controls, rejected_mutations=mutations,
                  source_path_object_variations=proof['source_path_object_variations'],
                  checker_sha256=sha(Path(__file__)), artifacts=artifacts,
                  limitations=['Experimental queue/claim component and linked parent only; startup PRM/path, modem events and UART-aware poll scheduling remain unwired.',
                               'Ambiguous-close and removed-claim faults have explicit diagnostic models.',
                               'No original executables were build inputs; no physical modem/card/deployment or whole-application gate closes.'])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print('PASS:', assertions, 'native assertions;', len(artifacts), 'bound artifacts;', len(mutations), 'rejected mutations')


if __name__ == '__main__':
    main()
