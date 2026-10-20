#!/usr/bin/env python3
"""Require complete accepted routes, audits and frozen identities in one suite."""
import argparse
import copy
import json
from pathlib import Path

from enigma_key_stream_fixture import ROOT, owned, sha

REPORTS = {
    'download': ('repeat-checks.json', 'audit-negative-checks.json'),
    'upload': ('upload-checks.json', 'upload-audit-negative-checks.json'),
    'save-cancel': ('infocom-edge-checks.json', 'infocom-edge-audit.json'),
    'save-overwrite': ('infocom-edge-checks.json', 'infocom-edge-audit.json'),
    'save-corrupt': ('infocom-edge-checks.json', 'infocom-edge-audit.json'),
    'bre': ('v86-door-checks.json', 'v86-door-audit.json'),
    'gwar': ('v86-door-checks.json', 'v86-door-audit.json'),
}


def audit(suite, reports, actual_hashes):
    expected = [step for name in REPORTS for step in (name, name + '-audit')]
    return dict(all_fourteen_steps_in_order=[r['name'] for r in suite['steps']] == expected,
        all_processes_accepted=bool(suite['steps']) and all(r['exit_code'] == 0 for r in suite['steps']),
        all_workflow_and_audit_reports=set(reports) == set(REPORTS) and all(
            result.get('passed') is True and all(result.get('checks', {}).values())
            for pair in reports.values() for result in pair),
        every_audit_has_rejected_corruptions=all(pair[1].get('cases') and
            all(case.get('rejected') is True for case in pair[1]['cases']) for pair in reports.values()),
        frozen_input_identities_match=bool(suite['input_hashes']) and suite['input_hashes'] == actual_hashes)


def run(args):
    assert args.prefix.replace('-', '').replace('_', '').isalnum()
    candidate = owned(args.candidate)
    root = ROOT / 'build/bbs-lab/results/enigma'
    folder = root / (args.prefix + '-suite')
    suite = json.loads((folder / 'suite.json').read_text())
    assert suite['passed'] and suite['candidate'] == str(candidate)
    reports, captures = {}, {}
    for name, files in REPORTS.items():
        paths = [root / (args.prefix + '-' + name) / file for file in files]
        reports[name] = [json.loads(path.read_text()) for path in paths]
        captures.update({str(path.relative_to(ROOT)): sha(path) for path in paths})
    actual_hashes = {name: sha(candidate / name[10:] if name.startswith('candidate/') else ROOT / name)
                     for name in suite['input_hashes']}
    checks = audit(suite, reports, actual_hashes)
    assert all(checks.values()), checks
    cases = []
    def reject(name, current=suite, results=reports, hashes=actual_hashes):
        assert not all(audit(current, results, hashes).values()), name
        cases.append(dict(case=name, rejected=True))
    changed = copy.deepcopy(suite)
    changed['steps'].pop()
    reject('last-audit-not-run', current=changed)
    changed = copy.deepcopy(suite)
    changed['steps'][2]['exit_code'] = 1
    reject('failed-step-hidden-by-summary', current=changed)
    changed = copy.deepcopy(suite)
    changed['steps'][0], changed['steps'][1] = changed['steps'][1], changed['steps'][0]
    reject('audit-before-runtime', current=changed)
    for name in REPORTS:
        changed = copy.deepcopy(reports)
        changed[name][0]['passed'] = False
        reject('failed-' + name + '-workflow', results=changed)
    changed = copy.deepcopy(reports)
    changed['bre'][1]['cases'] = []
    reject('missing-negative-evidence', results=changed)
    changed = dict(actual_hashes)
    changed[next(iter(changed))] = 'mutated'
    reject('frozen-input-was-edited', hashes=changed)
    captures[str((folder / 'suite.json').relative_to(ROOT))] = sha(folder / 'suite.json')
    result = dict(passed=True, checks=checks, cases=cases, captures=captures,
        workflows={name: dict(checks=len(pair[0]['checks']), corruptions_rejected=len(pair[1]['cases']))
                   for name, pair in reports.items()}, checker_sha256=sha(Path(__file__)),
        scope='Passive cumulative acceptance for seven specific DOS workflows and audits on one frozen configuration. Requires actual report acceptance and current immutable inputs, not process exit alone. No live, physical or full application claim.')
    (folder / 'combined-audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print('Combined audit:', len(cases), 'corruptions rejected')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--prefix', required=True)
    run(parser.parse_args())
