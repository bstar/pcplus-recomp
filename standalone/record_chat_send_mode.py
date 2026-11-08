#!/usr/bin/env python3
"""Bind live Chat mode behavior, module admission and cold source evidence."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    receipts = {}

    def read(name, require_pass=True):
        path = ROOT / name
        result = json.loads(path.read_text())
        assert not require_pass or result['passed'], name
        receipts[name] = sha(path)
        for field in ('sources', 'capture_files'):
            for source, digest in result.get(field, {}).items():
                assert sha(ROOT / source) == digest, source
        return result

    parent = read('build/chat-send-mode-parent-v2-20261108/manifest.json', False)
    assert parent['experimental_chat_send_mode'] and parent['chat_loader']['module']['api_version'] == 0x107
    for leaf, digest in {'TERMINAL.EXE': parent['binary_sha256'], 'PCCHAT.OVL': parent['chat_loader']['module']['binary_sha256']}.items():
        assert sha(ROOT / 'build/chat-send-mode-parent-v2-20261108' / leaf) == digest
    legacy = read('build/chat-send-mode-disabled-control-20261108/manifest.json', False)
    previous = json.loads((ROOT / 'docs/validation/aspect-compiler-package.json').read_text())
    assert legacy['binary_sha256'] == previous['files']['TERMINAL.EXE']
    assert sha(ROOT / 'build/chat-send-mode-disabled-control-20261108/TERMINAL.EXE') == legacy['binary_sha256']
    before, after = legacy['memory_layout'], parent['memory_layout']
    for name in ('near_bytes', 'near_spare_bytes', 'resident_CS_extent_bytes', 'history_bytes', 'native_reset_workspace_bytes', 'snapshot_bytes'):
        assert before[name] == after[name], name
    assert set(before['ui_screen_buffers']) == set(after['ui_screen_buffers'])
    for name, old in before['ui_screen_buffers'].items():
        new = after['ui_screen_buffers'][name]
        assert old['bytes'] == new['bytes'] and old['offset'] == new['offset'], name
        assert new['start_linear'] - old['start_linear'] == 80 and new['end_linear'] - old['end_linear'] == 80, name
    assert after['retained_parent_paragraphs'] - before['retained_parent_paragraphs'] == 5
    cases = []
    labels = ['immediate', '1', '255', 'live-1-to-0-v2', 'live-0-to-1', 'live-0-to-255', 'old-module-rejection']
    for label in labels:
        result = read('build/chat-send-mode-' + label + '-20261108/result.json')
        assert result['binary_sha256'] == parent['binary_sha256'] and all(result['checks'].values())
        cases.append({key: result[key] for key in ('mode', 'to_mode', 'rejected_module_sha256', 'checks', 'scope') if key in result})
    preferences = read('build/chat-send-mode-preferences-20261108/result.json')
    assert preferences['inputs'] == 295 and preferences['binary_sha256'] == parent['binary_sha256']
    compiled = read('build/chat-send-mode-source-lease-observed-20261108/checks.json')
    assert len(compiled['cases']) == 2 and compiled['source_lease_cases'] and compiled['source_compiler_residency_verified']
    for case in compiled['cases']:
        assert case['passed'] and case['binary_sha256'] == parent['binary_sha256'] and all(case['checks'].values())
        assert case['checks']['source_compiler_ASX_exact'] and case['checks']['compiler_result_success']
    proof = read('build/chat-send-mode-source-export-20261108/result.json')
    assert proof['DOS_cases'] == 2 and len(proof['sources']) == 1042 and proof['original_inputs'] == []
    assert proof['artifacts']['TERMINAL.EXE'] == parent['binary_sha256']
    assert proof['artifacts']['PCCHAT.OVL'] == parent['chat_loader']['module']['binary_sha256']
    result = dict(checkpoint_verified=True, tool_source_commit=subprocess.check_output(
        ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        parent_sha256=parent['binary_sha256'], module_sha256=parent['chat_loader']['module']['binary_sha256'], module_API='0107',
        original_field=dict(PRM_offset='01F2h', width_bytes=1, zero='immediate', nonzero='line buffered'),
        DOS_cases=cases, preference_inputs=295, preference_cases=preferences['cases'],
        nested_compile_cases=[dict(case=c['case'], checks=c['checks']) for c in compiled['cases']],
        source_export_files=1042, source_replayed_DOS_cases=2, source_artifacts=proof['artifacts'],
        legacy_parent_sha256=legacy['binary_sha256'], retained_growth_bytes=80, near_bytes=after['near_bytes'],
        history_bytes=after['history_bytes'], reset_workspace_bytes=after['native_reset_workspace_bytes'],
        receipts=receipts, sources={'standalone/record_chat_send_mode.py': sha(Path(__file__).resolve())},
        installed_changed=False, selector_changed=False, physical_verified=False, release_eligible=False,
        scope='Opt-in full parent/module configuration binding with actual DOS/synthetic serial and production settings child. Source proof reproduces parent/module/matching ASPECT/compiler and replays nested compilation. No new BBS/SIP/audio/physical acceptance; selected17-file candidate unchanged.',
        excluded=['First build refused stale source-digest pins before completion; refreshed pins retain compiler options and disabled bytes.',
                  'Initial source-lease invocation omitted allocation observation and ended with KeyError; excluded. Observed repeat and cold replay pass.',
                  'Initial live1-to0 report predates the corrected multi-digit CLI key serializer; superseded by the final v2 run.'])
    (ROOT / 'docs/validation/chat-send-mode-live.json').write_text(json.dumps(result, indent=2) + '\n')
    print('Verified7 DOS Chat cases,295 preference inputs,2 nested compiler cases and1042-file cold replay')


if __name__ == '__main__':
    main()
