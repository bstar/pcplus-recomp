#!/usr/bin/env python3
"""Preserve and bind recorder publisher evidence, without terminal acceptance."""
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
    parser.add_argument('--host', type=Path, required=True)
    parser.add_argument('--dos', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    host, dos, output = (p.resolve() for p in (args.host, args.dos, args.output))
    assert all(p.is_relative_to(ROOT / 'build') for p in (host, dos))
    assert output.is_relative_to(ROOT / 'docs/validation') and not output.exists()
    custody = dos.parent / 'accepted'
    assert not custody.exists()
    h, d = read(host), read(dos)
    assert h['passed'] and h['host_model_only'] and h['case_count'] == len(h['cases']) == 31
    assert d['passed'] and len(d['cases']) == 16
    assert all(c['passed'] for c in h['cases'])
    selected = {host, dos, Path(__file__).resolve(), ROOT / 'Makefile'}
    for path, proof in ((host, h), (dos, d)):
        for name, digest in proof['inputs'].items():
            source, frozen = ROOT / name, path.parent / 'frozen-source' / name
            assert sha(source) == sha(frozen) == digest, name
            selected.update((source, frozen))
    assert sha(host.parent / 'file.so') == h['library_sha256']
    selected.add(host.parent / 'file.so')
    assert sha(dos.parent / 'RECORD.EXE') == d['binary_sha256']
    for name, digest in d['captures_sha256'].items():
        path = dos.parent / name
        assert path.resolve().is_relative_to(dos.parent)
        assert sha(path) == digest, name
        selected.add(path)
    expected_binaries = {
        'ASPECT.EXE': '4bdb0380720fe08a6ef2a6363e56577ba865db078825ebdcd0f8db6ccb0aff18',
        'ASPCOMP.EXE': '9f28f60621614846980dbf402e81a02cf6fc189f03607439d176e59b2d974e82',
    }
    for binary, digest in expected_binaries.items():
        assert sha(dos.parent / binary) == digest
    by_name = {c['case']: c for c in d['cases']}
    assert set(by_name) == {
        'ordinary', 'quoted-controls', 'long-control-prompt', 'timeout-no-payload',
        'writefail', 'cancel', 'replace', 'cwd-change', 'scratch-collision',
        'existing-target', 'readonly-target', 'shared-target-owner',
        'shared-other-owner', 'dual-record-owner', 'publish-race', 'restore-race',
    }
    for name, case in by_name.items():
        folder = dos.parent / name
        assert case['passed'] and all(case['checks'].values()) and not case['peer_errors']
        assert read(folder / 'result.json') == case
        status = list(map(int, (folder / 'STATUS.TXT').read_text().split()))
        assert status == case['status'] and len(status) == 19
        assert status[2:4] == [1, 1] and status[13] == status[15] == 0 and status[18] == 326
        assert (folder / 'PASS.TXT').exists() and not (folder / 'FAIL.TXT').exists()
        assert not (folder / 'ERROR.TXT').read_bytes()
        assert (folder / 'BEFORE.BIN').read_bytes() == (folder / 'AFTER.BIN').read_bytes()
        assert (folder / 'BEFORE.BIN').stat().st_size == 42
        wire = (folder / 'wire.bin').read_bytes()
        assert wire.hex() == case['actual_hex'] == case['expected_hex']
        assert (folder / 'peer-reply.bin').read_bytes() == b''.join(bytes.fromhex(x) for x in case['peer_replies'])
        assert status[8:11] == ([1, 1, 1] if name == 'restore-race' else [0, 0, 0])
        if not status[0]:
            payload = (folder / 'PAYLOAD.BIN').read_bytes()
            assert wire == b'READY>' + (b'' if name == 'timeout-no-payload' else payload)
            assert status[7] == 1 and (folder / 'CASE.ASX').is_file()
            assert (folder / 'CASE.ASP').stat().st_size == status[6]
        else:
            assert not wire and not (folder / 'CASE.ASX').exists() and status[7] == 0
    recovery = dos.parent / 'restore-race'
    assert (recovery / 'CASE.ASP').read_bytes() == b'RACED'
    assert (recovery / 'LPR00002.BAK').read_bytes() == b'ORIGINAL'
    assert (recovery / 'LPR00001.TMP').read_bytes().endswith(b'endproc\r\n')
    assert by_name['restore-race']['status'][16] != 0
    assert by_name['writefail']['status'][11] == 5
    assert by_name['shared-target-owner']['status'][11] == 0
    assert by_name['shared-target-owner']['status'][14] == 2
    custody.mkdir()
    kept = {}
    for path in sorted(selected):
        copy = custody / path.relative_to(ROOT)
        copy.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, copy)
        assert sha(copy) == sha(path)
        kept[str(copy.relative_to(ROOT))] = sha(copy)
    result = dict(
        passed=True, publisher_component_accepted=True, terminal_recording_accepted=False,
        host_model_cases=31, actual_DOS_cases=16, DOS_owner_bytes=326,
        host=dict(result=str(host.relative_to(ROOT)), sha256=sha(host)),
        DOS=dict(result=str(dos.relative_to(ROOT)), sha256=sha(dos)),
        binaries_sha256=expected_binaries, publisher_binary_sha256=d['binary_sha256'],
        custody_sha256=kept,
        scope='Source-owned NEW/REPLACE recorder publication. Host filesystem faults are explicit models; '
              'DOS cases use real kernel file operations, synthetic owned media, source-built compiler '
              'and UART replay. The read-only handle and raced-in targets are deliberate fixtures. '
              'Ambiguous close and disk-full paths are modeled, not physical fault observations. '
              'No terminal Record UI, foreground taps, distinct code-bank publisher, current-binary '
              'BBS/audio, physical modem, power-loss or F01-F16 whole-application acceptance.')
    with output.open('x') as stream:
        stream.write(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(passed=True, host_cases=31, DOS_cases=16, custody_files=len(kept))))


if __name__ == '__main__':
    main()
