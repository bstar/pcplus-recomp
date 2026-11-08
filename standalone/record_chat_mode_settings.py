#!/usr/bin/env python3
"""Verify the native byte-field proof and offline Chat-mode editor checkpoint."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    receipts = {}

    def read(name, passed=True):
        path = ROOT / name
        result = json.loads(path.read_text())
        assert not passed or result['passed'], name
        receipts[name] = sha(path)
        for source, digest in result.get('sources', {}).items():
            assert sha(ROOT / source) == digest, source
        return result

    native = read('analysis/chat-send-mode-20261108.rea.json', False)
    assert native['subject']['digest']['sha256'] == '4ae6ee164991ab772dcb0dba4974fe30d00ee97429719dbbe0b56d5756fbc868'
    instructions = native['normalized_result']['instructions']
    assert '0x1e9f7: CMP byte ptr [0x1d76], 0x0' in instructions
    assert '0x1e9fc: JZ 0x1000:ea44' in instructions
    assert '0x1ea45: CALL 0x1000:ab0b' in instructions
    models = []
    for name, fields, inputs in [('setup-model-chat', 49, 713), ('setup-model-mouse-chat', 51, 733)]:
        result = read('build/' + name + '/checks.json')
        assert result['experimental_chat_mode'] and result['field_count'] == fields
        assert all(row['passed'] for row in result['cases'])
        assert sum(row['inputs'] for row in result['cases']) == inputs
        models.append(dict(fields=fields, inputs=inputs, cases=result['cases']))
    ui = read('build/setup-chat-mode-ui-v4-20261108/result.json')
    assert len(ui['cases']) == 4 and all(row['passed'] and row['full_image_exact'] for row in ui['cases'])
    assert [row['mode'] for row in ui['cases']] == [0, 1, 255, 255]
    assert all(row['opaque_neighbor'] == 167 for row in ui['cases'])
    proof = read('build/setup-chat-mode-source-export-20261108/result.json')
    assert proof['files'] == 30 and proof['binary_sha256'] == ui['editor_sha256']
    legacy = read('build/setup-chat-mode-legacy-editor-final-20261108/manifest.json', False)
    previous = json.loads((ROOT / 'docs/validation/aspect-compiler-package.json').read_text())
    assert legacy['binary_sha256'] == previous['files']['PRMEDIT.EXE']
    assert sha(ROOT / 'build/setup-chat-mode-legacy-editor-final-20261108/PRMEDIT.EXE') == legacy['binary_sha256']
    result = dict(checkpoint_verified=True, tool_source_commit=subprocess.check_output(
        ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        original_evidence_id=native['evidence_id'], original_DS='1D76h', PRM_offset='01F2h',
        width_bytes=1, immediate_value=0, buffered_values='1..255', opaque_neighbor_preserved=True,
        models=models, UI=ui['cases'], optional_editor_sha256=ui['editor_sha256'],
        legacy_editor_sha256=legacy['binary_sha256'], source_export_files=30,
        receipts=receipts, sources={'standalone/record_chat_mode_settings.py': sha(Path(__file__).resolve())},
        terminal_frontend_connected=False, installed_changed=False, selector_changed=False,
        physical_verified=False, scope='Original static byte consumer plus source-built optional offline editor. DOS field-model and BIOS-key saves/reload/cancel; fresh declared-source export reproduces editor. Current terminal still forces buffered Chat. No physical settings or selected package changes.',
        failed_fixture_runs=['Initial Shift-Tab and Up recipes moved to the previous page and did not save; timed out. Retained v1/v2/v3 captures are excluded.',
                             'Renamed-main watchdog probe first rejected a near/far pointer declaration at compilation; corrected probe still timed out and is excluded.'])
    target = ROOT / 'docs/validation/chat-send-mode-settings.json'
    target.write_text(json.dumps(result, indent=2) + '\n')
    print('Verified native byte field,1446 model inputs,4 DOS UI cases and30-file source export')


if __name__ == '__main__':
    main()
