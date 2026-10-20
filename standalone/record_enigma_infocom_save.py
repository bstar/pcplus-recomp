#!/usr/bin/env python3
"""Publish a scoped DOS save/restore result without stories, saves or captures."""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label', required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--server-root', type=Path, required=True)
    parser.add_argument('--previous-failed-label')
    args = parser.parse_args()
    assert re.fullmatch(r'[A-Za-z0-9_-]+', args.label)
    candidate = args.candidate.resolve()
    assert candidate.is_relative_to(ROOT / 'build')
    folder = ROOT / 'build/bbs-lab/results/enigma' / args.label
    report_path = folder / 'infocom-save-checks.json'
    audit_path = folder / 'save-audit-negative-checks.json'
    report, audit = [json.loads(p.read_text()) for p in (report_path, audit_path)]
    assert report['passed'] and all(report['checks'].values())
    assert audit['passed'] and len(audit['negative_cases']) == 11
    assert all(c['rejected'] for c in audit['negative_cases'])
    assert audit['report_sha256'] == sha(report_path)
    for p, h in audit['inputs'].items():
        assert sha(ROOT / p) == h, p
    for p, h in report['artifacts'].items():
        assert sha(folder / p) == h, p
    meta = json.loads((candidate / 'infocom-save-instance.json').read_text())
    sources = {f'source/{p}': args.server_root / p for p in meta['source_inputs']}
    sources.update({f'candidate/{p}': candidate / p for p in meta['fixture_inputs']})
    sources.update(terminal=ROOT / 'build/terminal/TERMINAL.EXE',
        staged_terminal=folder / 'program/TERMINAL.EXE',
        runner=ROOT / 'lab/bbs/enigma_infocom_save_dos.py', harness=ROOT / 'lab/bbs/test_dos.py')
    assert report['input_hashes'] == {p: sha(f) for p, f in sources.items()}
    assert audit['runner_sha256'] == sha(sources['runner'])
    assert audit['checker_sha256'] == sha(ROOT / 'lab/bbs/check_enigma_infocom_save_audit.py')
    result = dict(passed=True, compatibility_complete=False, live_server_modified=False,
        physical_modem_validated=False, whole_application_gates_closed=[],
        terminal_sha256=sha(sources['terminal']), source_revision=report['source_revision'],
        source_inputs=meta['source_inputs'], fixture_inputs=meta['fixture_inputs'],
        story_sha256=meta['story_sha256'], story_version=meta['story_version'],
        checks=report['checks'], negative_cases=audit['negative_cases'],
        saved_files=[dict(bytes=s['bytes'], sha256=s['sha256']) for s in report['saved_files']],
        sources={p: sha(ROOT / p) for p in (
            'lab/bbs/enigma_infocom_save_fixture.py', 'lab/bbs/enigma_infocom_save_dos.py',
            'lab/bbs/check_enigma_infocom_save_audit.py', 'standalone/record_enigma_infocom_save.py')},
        evidence={str(p.relative_to(ROOT)): sha(p) for p in (
            report_path, audit_path, folder / 'display.bin', folder / 'bbs-sent.bin',
            folder / 'server-session.jsonl', candidate / 'infocom-save-instance.json')},
        scope=report['scope'], limitations=[
            'One story/release, exact owned door code on an isolated stock-base instance with the staged decoder.',
            'Direct synthetic ZORK route; live custom library/menu and live saves are untouched.',
            'No overwrite/cancel/invalid-save or full playthrough coverage.',
            'Live decoder deployment, other doors, physical modem and full application gates remain open.'])
    if args.previous_failed_label:
        assert re.fullmatch(r'[A-Za-z0-9_-]+', args.previous_failed_label)
        previous = ROOT / 'build/bbs-lab/results/enigma' / args.previous_failed_label
        previous_report = previous / 'infocom-save-checks.json'
        failed = json.loads(previous_report.read_text())
        assert not failed['passed'] and not failed['checks']['rooms_across_worker_restart']
        assert sha(previous / 'runner-attempt.py') == failed['input_hashes']['runner']
        for p, h in failed['artifacts'].items():
            assert sha(previous / p) == h, p
        result['retained_failed_attempt'] = dict(checks=failed['checks'],
            evidence={str(p.relative_to(ROOT)): sha(p) for p in (
                previous_report, previous / 'runner-attempt.py', previous / 'display.bin')},
            reason='Incorrect SOUTH-to-West route assertion; corrected recipe rerun in a fresh instance.')
    (ROOT / 'docs/validation/enigma-infocom-save.json').write_text(json.dumps(result, indent=2) + '\n')
    print('Recorded actual DOS SAVE/RESTORE across workers; full compatibility remains open.')


if __name__ == '__main__':
    main()
