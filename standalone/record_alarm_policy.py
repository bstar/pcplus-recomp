#!/usr/bin/env python3
"""Bind actual-parent ALARM duration policy and BIOS completion-key captures."""
import json
from pathlib import Path
from build_context_help import ROOT, sha


def main():
    previous = ROOT / 'docs/validation/aspect-alarm-groups.json'
    base = json.loads(previous.read_text())
    assert base['passed'] and not base['release_accepted']
    products = base['products']
    receipts = {str(previous.relative_to(ROOT)): sha(previous)}
    sources = {}
    for folder in ('terminal-alarm-policy-admission-20261106',
                   'aspect-alarm-numeric-groups-final-20261106'):
        path = ROOT / 'build' / folder / 'manifest.json'
        manifest = json.loads(path.read_text())
        for name, digest in manifest['sources'].items():
            assert sha(ROOT / name) == digest, name
            sources[name] = digest
        receipts[str(path.relative_to(ROOT))] = sha(path)
    cases = []
    for label, variant in (('policy-ordered-groups-20261106', 'policy'),
                           ('keys-groups-20261106', 'keys')):
        folder = ROOT / 'build/aspect-alarm-vm-dos' / label
        for filename in ('checks.json', 'pause-checks.json'):
            path = folder / filename
            report = json.loads(path.read_text())
            assert report['passed'] and len(report['cases']) == 3
            receipts[str(path.relative_to(ROOT))] = sha(path)
            for case in report['cases']:
                assert case['passed'] and all(case['checks'].values())
            if filename == 'checks.json':
                assert report['terminal_sha256'] == products['TERMINAL.EXE']
                assert report['runner_sha256'] == products['ASPECT.EXE']
                for case in report['cases']:
                    target = folder / case['case']
                    assert sha(target / 'TERMINAL.EXE') == products['TERMINAL.EXE']
                    assert sha(target / 'ASPECT.EXE') == products['ASPECT.EXE']
                    assert case['checks']['keys_during_script_before_continuation']
                    assert case['checks']['ordinary_parent_keyboard_resumes']
                    source = (target / 'LOGIN.ASP').read_text()
                    if variant == 'keys':
                        assert 'alarm 32767\n' in source
                        assert case['passive_observer_header'][6] == 0
            else:
                assert report['parent_sha256'] == products['TERMINAL.EXE']
                assert report['runner_sha256'] == products['ASPECT.EXE']
                cases.extend(report['cases'])
                for name, digest in report['captures_sha256'].items():
                    path = folder / name
                    assert sha(path) == digest, path
                    receipts[str(path.relative_to(ROOT))] = digest
        if variant == 'policy':
            path = folder / 'policy-checks.json'
            policy = json.loads(path.read_text())
            assert policy['passed'] and len(policy['cases']) == 2
            for case in policy['cases']:
                assert case['passed'] and case['configured_default_observed']
                assert 3 <= case['configured_default_after_override_seconds'] <= 5
                if 'zero-default' in case['case']:
                    assert case['zero_returns_without_second_wait']
                    assert 0 <= case['first_alert_seconds'] <= 1
                else:
                    assert 1 <= case['first_alert_seconds'] <= 3
            receipts[str(path.relative_to(ROOT))] = sha(path)
    for name in ('standalone/test_aspect_alarm_vm_dos.py',
                 'standalone/test_aspect_pause_when_dos.py',
                 'standalone/test_aspect_keys_dos.py',
                 'standalone/test_aspect_script_window_dos.py',
                 'standalone/test_aspect_renderer_dos.py',
                 'standalone/test_connection_dos.py',
                 'standalone/test_aspect_window_query_dos.py',
                 'standalone/record_alarm_policy.py'):
        sources[name] = sha(ROOT / name)
    result = dict(
        passed=True, release_accepted=False, products=products, sources=sources,
        receipts=receipts, cases=cases, policy=policy,
        original_inputs=[], scope=__doc__,
        limitations=[
            'Standard BIOS/ANSI, quiet alerts and UMB passive observer; no physical modem or audible output test.',
            'Policy is reread from the actual parent for each command. Timing after an override does not directly sample restoration of the child duration word; exact native wrapper tests cover that separately.',
            '32767-count alerts are cancelled after about two seconds; this does not prove full-duration service budget sufficiency.',
            'The first policy attempt froze the zero-alert marker after the query in expected wire order and failed. Corrected ordering and later query were declared before the accepted fresh run; failed captures remain separate.',
            'Sound, malformed operands, long-duration service budgets and carrier/error cleanup remain open; no release selection, deployment or machine changes.'
        ])
    (ROOT / 'docs/validation/aspect-alarm-policy.json').write_text(
        json.dumps(result, indent=2) + '\n')
    print('PASS six actual-parent ALARM policy/key cases')


if __name__ == '__main__':
    main()
