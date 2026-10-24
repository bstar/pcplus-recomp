#!/usr/bin/env python3
"""Seal actual near/far DOS queue evidence and source-only object rebuilds."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct

from record_phone_log_file import records
from test_phone_log_queue_dos import expected_file

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['near', 'far', 'source', 'output']:
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    build = ROOT / 'build/phone-log-queue'
    manifest = read(build / 'manifest.json')
    source_path = args.source.resolve()
    assert source_path.is_relative_to(ROOT / 'build')
    source = read(source_path / 'checks.json')
    formatter = read(ROOT / 'build/phone-log-format/checks.json')
    assert source['passed'] and source['outputs'] == manifest['outputs']
    assert source['sources'] == manifest['sources'] and source['source_count'] == 16
    assert not source['original_inputs'] and not manifest['original_inputs']
    assert not (source_path / 'source/analysis').exists()
    assert formatter['passed'] and formatter['inputs'] == 53071 and formatter['calendar_days'] == 43830
    artifacts = {}
    reports = [source, formatter]
    native_assertions = 0
    variants = {}
    for variant in ['near', 'far']:
        folder = getattr(args, variant).resolve()
        assert folder.is_relative_to(ROOT / 'build')
        report = read(folder / 'checks.json')
        assert report['passed'] and all(report['checks'].values()) and len(report['cases']) == 9
        expected_outputs = manifest['outputs'][variant]
        assert report['variant'] == variant
        assert report['binary_sha256'] == expected_outputs['binary_sha256'] == sha(build / variant / 'QUEUE.EXE')
        for name, digest in expected_outputs['objects'].items():
            path = build / variant / name
            normalized, raw = records(path.read_bytes()), records(path.with_suffix('.raw.obj').read_bytes())
            logical = 'src/capture/capture_fs.c' if name == 'capture_fs.obj' else 'src/directory/' + path.stem + '.c'
            assert normalized[0][0] == raw[0][0] == 0x80 and normalized[1:] == raw[1:]
            assert normalized[0][4:-1].decode('ascii') == logical
            assert raw[0][4:-1].decode('ascii') == str(ROOT / logical)
            assert sha(path) == digest == sha(source_path / 'source/build/phone-log-queue' / variant / name)
            for item in [path, path.with_suffix('.raw.obj')]:
                artifacts[str(item.relative_to(ROOT))] = sha(item)
        for case in range(9):
            witness = folder / f'T{case:03}'
            row = report['cases'][str(case)]
            assert row['passed'] and all(row['checks'].values())
            result = re.fullmatch(rb'PASS (\d+) queue assertions\r\n', (witness / 'RESULT.TXT').read_bytes())
            assert result
            native_assertions += int(result[1])
            assert list(struct.unpack('<6H3I', (witness / 'STATE.BIN').read_bytes())) == row['state']
            assert list(struct.unpack('<8H', (witness / 'CONTEXT.BIN').read_bytes())) == row['context']
            expected = expected_file(case, witness)
            actual = (witness / 'CALLS.FON').read_bytes() if (witness / 'CALLS.FON').exists() else None
            assert actual == expected
        before = (folder / 'BEFORE.BIN').read_bytes()
        assert len(before) == 42 and before == (folder / 'AFTER.BIN').read_bytes()
        variants[variant] = report
        reports.append(report)
        artifacts[str((folder / 'checks.json').relative_to(ROOT))] = sha(folder / 'checks.json')
    for report in reports:
        for name, digest in report.get('sources', {}).items():
            assert sha(ROOT / name) == digest
        for name, digest in report.get('inputs', {}).items() if isinstance(report.get('inputs'), dict) else []:
            assert sha(ROOT / name) == digest
        for name, digest in report.get('artifacts', {}).items():
            assert sha(ROOT / name) == digest
            artifacts[name] = digest
    for path in [build / 'manifest.json', source_path / 'checks.json', ROOT / 'build/phone-log-format/checks.json',
                 *[build / variant / 'QUEUE.EXE' for variant in variants]]:
        artifacts[str(path.relative_to(ROOT))] = sha(path)
    names = ['Makefile', 'tools/dev', 'tools/build', 'nix/flake.nix', 'nix/flake.lock',
             'src/config/prm.py', 'standalone/prove_phone_log_queue.py', 'standalone/record_phone_log_queue.py',
             'standalone/record_phone_log_file.py', 'standalone/test_phone_log_queue_dos.py']
    result = dict(passed=True, full_compatibility=False, accepted_for_deployment=False,
                  manifest=manifest, DOS=variants, source_rebuild=source, formatter=formatter,
                  native_assertions=native_assertions, artifacts=artifacts,
                  workflow_sources={name: sha(ROOT / name) for name in names},
                  limitations=['Standalone maintained queue/formatter/clock/PRM decoding, not terminal event or startup integration.',
                               'Four bounded RAM events; caller must handle FULL, explicit retry and recovery-required ambiguity.',
                               'Far data placement proved in diagnostics only. Application code banking, file reservations and UART-safe poll placement remain open.',
                               'Selected explicit DOS failure-result injection; not failing media, power loss, real modem or card acceptance.'])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print('Sealed18 DOS workflows/', native_assertions, 'native assertions,53071 formatter inputs and', len(artifacts), 'artifacts')


if __name__ == '__main__':
    main()
