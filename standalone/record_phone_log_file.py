#!/usr/bin/env python3
"""Independently bind checked append state/files and exact OMF/source identities."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def records(data):
    result = []
    at = 0
    while at < len(data):
        end = at + 3 + int.from_bytes(data[at + 1:at + 3], 'little')
        assert at + 3 < end <= len(data) and sum(data[at:end]) & 255 == 0
        result.append(data[at:end])
        at = end
    assert at == len(data)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dos', type=Path, required=True)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    build = ROOT / 'build/phone-log-file'
    manifest = read(build / 'manifest.json')
    dos_path, source_path = a.dos.resolve(), a.source.resolve()
    assert all(path.is_relative_to(ROOT / 'build') for path in [dos_path, source_path])
    dos, source = read(dos_path / 'checks.json'), read(source_path / 'checks.json')
    assert manifest['model_cases'] == 138 and manifest['model_assertions'] == 7239
    assert (build / 'model.txt').read_text() == 'PASS 138 append cases, 7239 assertions\n'
    assert dos['passed'] and all(dos['checks'].values()) and len(dos['cases']) == 18
    assert source['passed'] and source['source_count'] == 9 and source['model_cases'] == 138
    assert not manifest['original_inputs'] and not source['original_inputs']
    assert source['binary_sha256'] == dos['binary_sha256'] == manifest['binary_sha256'] == sha(build / 'PHONEAPP.EXE')
    assert source['objects'] == manifest['objects']
    assert not (source_path / 'source/analysis').exists()
    for name, digest in manifest['sources'].items():
        assert sha(ROOT / name) == sha(source_path / 'source' / name) == digest
    objects = {}
    for name, logical in [('file', 'src/directory/phone_log_file.c'), ('capture', 'src/capture/capture_fs.c'), ('rollback', 'src/directory/phone_log_fs.c')]:
        path = build / (name + '.obj')
        raw = records((build / (name + '.raw.obj')).read_bytes())
        normalized = records(path.read_bytes())
        assert raw[0][0] == normalized[0][0] == 0x80 and raw[1:] == normalized[1:]
        assert normalized[0][4:-1].decode('ascii') == logical
        assert raw[0][4:-1].decode('ascii') == str(ROOT / logical)
        assert sha(path) == manifest['objects'][name + '.obj']
        assert sha(source_path / 'source/build/phone-log-file' / path.name) == sha(path)
        objects[name] = dict(sha256=sha(path), raw_sha256=sha(build / (name + '.raw.obj')), later_records_identical=True)
    native_assertions = 0
    for case in range(18):
        folder = dos_path / f'T{case:03}'
        row = dos['cases'][str(case)]
        assert row['passed'] and all(row['checks'].values())
        text = (folder / 'RESULT.TXT').read_bytes()
        match = re.fullmatch(rb'PASS (\d+) checked-append assertions\r\n', text)
        assert match
        native_assertions += int(match[1])
        state = struct.unpack('<15H2I128s', (folder / 'STATE.BIN').read_bytes())
        assert list(state[:17]) == row['state']
        initial = 70001 if case in (10, 16) else 0 if case in (11, 15) else 8
        expected = bytes((i * 37 + 11) & 255 for i in range(initial))
        if case in (0, 1, 2, 3, 10, 11, 15, 16, 17):
            expected += bytes(range(256)) if case == 17 else (b'HEADING\r\n' if not initial else b'') + b'EVENT\r\n'
            assert state[:2] == (1, 0) and state[5:9] == (0, 0, 0, 1)
            assert state[15:17] == (initial, len(expected))
        elif case in (4, 5, 6, 7, 8, 9):
            expected += b'EVE' if case in (4, 5) else b'EVENT\r\n' if case in (8, 9) else b''
            assert state[0] == 3 and state[7:9] == (1, 0) and state[14] == 1
            assert state[15:17] == (initial, len(expected))
        elif case in (12, 14):
            assert state[:3] == (2, 5 if case == 14 else 4, 3 if case == 14 else 5)
        else:
            assert state[:15] == (0,) * 15
        assert (folder / 'CALLS.FON').read_bytes() == expected
    before = (dos_path / 'BEFORE.BIN').read_bytes()
    assert len(before) == 42 and before == (dos_path / 'AFTER.BIN').read_bytes()
    artifacts = {}
    for report in [dos, source]:
        for name, digest in report.get('inputs', {}).items():
            assert sha(ROOT / name) == digest, name
        for name, digest in report['artifacts'].items():
            assert sha(ROOT / name) == digest, name
            artifacts[name] = digest
    for path in [build / 'manifest.json', build / 'model.txt', build / 'PHONEAPP.EXE',
                 dos_path / 'checks.json', source_path / 'checks.json',
                 *[build / (name + suffix) for name in objects for suffix in ('.obj', '.raw.obj')]]:
        artifacts[str(path.relative_to(ROOT))] = sha(path)
    names = ['Makefile', 'tools/dev', 'tools/build', 'nix/flake.nix', 'nix/flake.lock',
             'standalone/prove_phone_log_file.py', 'standalone/record_phone_log_file.py']
    result = dict(passed=True, full_compatibility=False, accepted_for_deployment=False,
                  manifest=manifest, DOS=dos, source_rebuild=source, objects=objects,
                  native_assertions=native_assertions, artifacts=artifacts,
                  workflow_sources={name: sha(ROOT / name) for name in names},
                  limitations=['Maintained checked append backend; not the exact native controller or integrated terminal logging.',
                               'Actual DOS prefix writes/seek/truncate/commit/close with explicitly injected failure results, not actual failing media or power-loss proof.',
                               'Uncertain close/failed rollback blocks retries. Cross-application reservations, date/clock/PRM bindings, event ownership/banking and modem/card acceptance remain open.',
                               'No external concurrent writers, replacement, drive remapping or crash-atomic FAT guarantee.'])
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2) + '\n')
    print('Sealed138 model cases/7239 assertions,18 DOS workflows/', native_assertions,
          'native assertions, nine-source rebuild and', len(artifacts), 'artifacts')


if __name__ == '__main__':
    main()
