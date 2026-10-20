#!/usr/bin/env python3
"""Audit the reference route plus preservation of preexisting cumulative files."""
import argparse
import copy
import json
from pathlib import Path

from enigma_key_stream_fixture import ROOT, owned, sha
from enigma_upload_dos import metadata
from enigma_combined_concurrent import files
from check_enigma_concurrent_audit import main as protocol_audit


def preserved(baseline, snapshots):
    if len(snapshots) != 4:
        return False
    expected = [[], [], ['CONCA.BIN'], ['CONCA.BIN', 'CONCB.BIN']]
    return all(row['preserved_files'] == baseline['files'] and row['preserved_catalog'] == baseline['catalog']
        and row['installed'] == added and row['installed_all'] == sorted([*baseline['files'], *added])
        for row, added in zip(snapshots, expected))


def run(args):
    candidate = owned(args.candidate)
    protocol_audit(args)
    root = ROOT / 'build/bbs-lab/results/enigma' / args.label
    baseline = json.loads((root / 'existing-upload-baseline.json').read_text())
    snapshots = json.loads((root / 'snapshots.json').read_text())
    report = json.loads((root / 'concurrent-checks.json').read_text())
    assert report['passed'] and report['composition_adapter']['unchanged']
    assert sha(root / 'existing-upload-baseline.json') == report['composition_adapter']['baseline_sha256']
    assert preserved(baseline, snapshots)
    current = files(candidate / 'file_base/pcplus_upload')
    assert {name: current[name] for name in baseline['files']} == baseline['files']
    assert metadata(candidate, sorted(baseline['files'])) == baseline['catalog']
    cases = []
    def reject(name, rows):
        assert not preserved(baseline, rows), name
        cases.append(dict(case=name, rejected=True))
    for field, value in [('inode', -1), ('bytes', -1), ('mtime_ns', -1), ('ctime_ns', -1), ('sha256', 'changed')]:
        rows = copy.deepcopy(snapshots)
        rows[1]['preserved_files'][next(iter(baseline['files']))][field] = value
        reject('earlier-file-' + field + '-changed', rows)
    rows = copy.deepcopy(snapshots)
    rows[1]['preserved_catalog'] = []
    reject('earlier-catalog-entry-lost', rows)
    rows = copy.deepcopy(snapshots)
    rows[1]['installed_all'].pop()
    reject('earlier-file-hidden-by-delta', rows)
    rows = copy.deepcopy(snapshots)
    rows[3]['installed_all'].append('UNEXPECTED.BIN')
    reject('unexpected-extra-file', rows)
    result = dict(passed=True, cases=cases, preserved_files=sorted(baseline['files']),
        checker_sha256=sha(Path(__file__)), captures={name: sha(root / name) for name in
            ('existing-upload-baseline.json', 'snapshots.json', 'concurrent-checks.json', 'concurrent-audit-negative-checks.json')},
        scope='Additional passive identity/content/catalog preservation audit for the nonempty combined fixture; reference peers, not concurrent DOS clients.')
    (root / 'existing-upload-audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print('Existing upload preservation:', len(cases), 'corruptions rejected')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--label', required=True)
    run(parser.parse_args())
