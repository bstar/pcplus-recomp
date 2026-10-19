#!/usr/bin/env python3
"""Publish scoped ENiGMA outcomes without private accounts, config or captures."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def read(path):
    return json.loads((ROOT / path).read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--files', required=True)
    parser.add_argument('--editor', required=True)
    parser.add_argument('--control', help='optional explicit ENiGMA control-key profile run')
    args = parser.parse_args()
    labels = [args.files, args.editor] + ([args.control] if args.control else [])
    for label in labels:
        assert label and all(c.isalnum() or c in '-_' for c in label)
    terminal = sha('build/terminal/TERMINAL.EXE')
    framer_path = 'build/bbs-lab/owned-enigma-framer-02/report.json'
    framer = read(framer_path)
    isolated = []
    for label, mode in [('owned-revision-framed-editor-02','editor'),
                        ('owned-revision-framed-transfer-01','editor-transfer')]:
        path = f'build/bbs-lab/results/enigma/{label}-wrapper/experiment.json'
        report = read(path)
        assert report['passed'] and report['inputs_unchanged']
        assert report['input_hashes']['build/terminal/TERMINAL.EXE'] == terminal
        assert [h for p,h in report['input_hashes'].items() if p.endswith('candidate/core/client.js')] == [framer['candidate_client_sha256']]
        assert [h for p,h in report['input_hashes'].items() if p.endswith('candidate/core/key_stream.js')] == [framer['candidate_key_stream_sha256']]
        assert report['message_count_before'] == report['message_count_after']
        run_path = f'build/bbs-lab/results/enigma/{label}/result.json'
        run = read(run_path)
        assert run['passed'] and all(run['checks'].values())
        item = dict(mode=mode, path=path, sha256=sha(path), checks=run['checks'])
        if mode == 'editor':
            audit_path = f'build/bbs-lab/results/enigma/{label}/semantic-audit.json'
            audit = read(audit_path)
            assert audit['passed'] and all(audit['checks'].values())
            item.update(editor_checks=audit['checks'], audit_sha256=sha(audit_path))
        else:
            item['payload_sha256'] = run['payload_sha256']
        isolated.append(item)
    live = []
    for label in labels:
        path = f'build/bbs-lab/results/enigma-owned/{label}/owned-server-checks.json'
        report = read(path)
        assert report['binary_sha256'] == terminal
        assert report['checks']['authenticated_probe'] and report['checks']['inputs_unchanged']
        assert report['checks']['no_post_saved'] and report['modem_packet_delay_ms'] == 0
        item = dict(path=path, sha256=sha(path), passed=report['passed'],
                    mode=report['mode'], checks=report['checks'], profile=report['keyboard_profile'])
        scroll_path = f'build/bbs-lab/results/enigma-owned/{label}/scroll-audit.json'
        if (ROOT / scroll_path).exists():
            item.update(scroll=read(scroll_path), scroll_sha256=sha(scroll_path))
        live.append(item)
    assert framer['passed'] and framer['stock_client_unchanged']
    for name in ('check.py', 'check_client.js', 'check_key_stream.js', 'key_stream.js', 'client.patch'):
        assert framer['inputs'][name] == sha('lab/bbs/patches/enigma-key-stream/' + name)
    results = [dict(name=t['name'], exit_code=t['exit_code'],
                    checks=t.get('result',{}).get('checks')) for t in framer['tests']]
    result = dict(evaluation_recorded=True, compatibility_complete=False,
        recorder_sha256=sha(Path(__file__).relative_to(ROOT)), terminal_sha256=terminal,
        server_revision=framer['upstream_revision'], stock_client_sha256=framer['stock_client_sha256'],
        isolated_candidate_client_sha256=framer['candidate_client_sha256'],
        candidate_report=dict(path=framer_path, sha256=sha(framer_path), tests=results),
        live_unmodified_runs=live, isolated_patched_runs=isolated,
        live_server_patched_by_this_work=False, modem_packet_delay_ms=0,
        whole_application_gates_closed=[], original_inputs=[],
        limitations=['The isolated decoder fix is not installed on the live service.',
                     'Live view-entry checks do not imply successful arrow/page-key navigation; inspect the separate scroll audit.',
                     'Captured runtime data and private account/config files remain ignored and unpublished.',
                     'Physical RS-232 Wi-Fi modem behavior and full application compatibility remain unverified.'])
    excluded = 'build/bbs-lab/results/enigma-owned/owned-editor-control-01/owned-server-checks.json'
    if (ROOT / excluded).exists():
        control = read(excluded)
        assert not control['passed'] and not control['checks']['inputs_unchanged']
        result['excluded_control_profile_run'] = dict(path=excluded, sha256=sha(excluded),
            checks=control['checks'], reason='File-menu configuration/module changed during capture. Retained as an unmatched failed run; no fallback compatibility claim.')
    (ROOT / 'docs/validation/enigma-owned.json').write_text(json.dumps(result, indent=2) + '\n')
    print('Recorded live unmodified outcomes separately from isolated patched editor/transfer passes')


if __name__ == '__main__':
    main()
