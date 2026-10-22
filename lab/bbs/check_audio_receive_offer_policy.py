#!/usr/bin/env python3
"""Reject changed receive-policy declarations against immutable audio captures.

Each auditor subprocess reads links to the original captures and a private copy
of result.json. Only that declaration changes. This checks the independent
download audit stage, not the producer or full acceptance recorder. No product,
protocol peer, bridge or hardware run is performed.
"""
import argparse
import copy
import json
import subprocess
import sys
from pathlib import Path
from synthmodem_vm_control import ROOT, sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('cohort', type=Path)
    parser.add_argument('--output', type=Path, required=True,
                        help='Fresh owned directory below build/.')
    args = parser.parse_args()
    cohort = args.cohort.resolve()
    output = args.output.resolve()
    assert cohort.is_relative_to(ROOT / 'build') and cohort.is_dir()
    assert output.is_relative_to(ROOT / 'build') and not output.exists()
    assert not output.is_relative_to(cohort) and not cohort.is_relative_to(output)
    read = lambda name: json.loads((cohort / name).read_text())
    producer = read('result.json')
    audit = read('download-audit.json')
    assert producer['passed'] and all(producer['checks'].values())
    assert audit['passed'] and all(audit['checks'].values())
    assert producer['expected_receive_offer'] is not None
    assert audit['checks']['native_receive_offer_policy']
    entrypoint = ROOT / 'lab/bbs/audit_audio_download_bound.py'
    auditor = ROOT / 'lab/bbs/audit_audio_download.py'
    assert audit['auditor_sha256'] == sha(auditor)
    # Include the manifest itself: the auditor's producer capture map excludes
    # its own result.json, while this experiment must preserve that file too.
    originals = dict(producer['captures_sha256'])
    originals.update(audit['capture_sha256'])
    originals['download-audit.json'] = sha(cohort / 'download-audit.json')
    for name, digest in originals.items():
        assert sha(cohort / name) == digest, name
    output.mkdir(parents=True)
    cases = []

    def run(name, altered, declaration_error=False, baseline=False):
        target = output / name
        target.mkdir()
        for path in cohort.iterdir():
            if path.name != 'result.json':
                (target / path.name).symlink_to(path, target_is_directory=path.is_dir())
        (target / 'result.json').write_text(json.dumps(altered, indent=2) + '\n')
        receipt = target / 'policy-audit.json'
        with (target / 'stdout').open('w') as stdout, (target / 'stderr').open('w') as stderr:
            process = subprocess.run([sys.executable, str(entrypoint), str(target),
                                      '--output', str(receipt)], cwd=ROOT,
                                     stdout=stdout, stderr=stderr)
        if declaration_error:
            assert process.returncode != 0 and not receipt.exists(), name
            detail = (target / 'stderr').read_text()
            assert "assert r['expected_receive_offer']==offer" in detail, detail
            assert 'AssertionError' in detail, detail
        else:
            result = json.loads(receipt.read_text())
            assert result['protocol'] == audit['protocol'], name
            assert result['errors'] == audit['errors'] == [], name
            assert result['source_sha256'] == audit['source_sha256'], name
            assert result['received_sha256'] == audit['received_sha256'], name
            failed = {key for key, value in result['checks'].items() if not value}
            assert failed == (set() if baseline else {'native_receive_offer_policy'}), (name, failed)
            assert result['passed'] == baseline and (process.returncode == 0) == baseline, name
        cases.append(dict(case=name, baseline=baseline, rejected=not baseline,
                          declaration_error=declaration_error, exit_code=process.returncode,
                          declaration=altered['expected_receive_offer'],
                          capture_sha256={n: sha(target / n) for n in
                                          ('result.json', 'stdout', 'stderr')},
                          audit_sha256=sha(receipt) if receipt.exists() else None))
        print(json.dumps(dict(case=name, expected_result_observed=True)), flush=True)

    run('unchanged-baseline', copy.deepcopy(producer), baseline=True)
    actual = producer['expected_receive_offer']['credit']
    for credit in (1, 255, 256, 257, 8191, 8192, None):
        selected = credit or 8192
        if selected == actual:
            continue
        altered = copy.deepcopy(producer)
        flags = 33 if selected < 8192 else 35
        altered['zmodem_receive_credit'] = credit
        altered['expected_receive_offer'] = dict(credit=selected, flags=flags,
                                                position=(flags << 24) | selected)
        run('changed-credit-' + str(credit), altered)
    for field in ('flags', 'position'):
        altered = copy.deepcopy(producer)
        altered['expected_receive_offer'][field] ^= 2
        run('inconsistent-' + field, altered, declaration_error=True)
    for name, digest in originals.items():
        assert sha(cohort / name) == digest, name
    result = dict(passed=True, verifier_only=True, cohort=str(cohort.relative_to(ROOT)),
                  baseline_passed=True, negative_cases=sum(row['rejected'] for row in cases),
                  cases=cases, original_captures_unchanged=True,
                  original_capture_sha256=originals,
                  inputs={str(path.relative_to(ROOT)): sha(path) for path in
                          (Path(__file__).resolve(), entrypoint, auditor)},
                  scope=__doc__)
    with (output / 'result.json').open('x') as stream:
        stream.write(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(passed=True, negative_cases=result['negative_cases'])))


if __name__ == '__main__':
    main()
