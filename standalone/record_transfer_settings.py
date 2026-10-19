#!/usr/bin/env python3
"""Collect current scoped transfer-settings evidence; never launches a test."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = 'd791eb10d984ec69348fa7815da8516cf38eca16161fe83345a76934ea0711d3'

def digest(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()

def main():
    reports = {}
    artifacts = {}
    sources = {}
    for label, path in {
        'model': 'build/setup-model/checks.json',
        'editor_regression': 'build/setup/checks.json',
        'transfer_UI': 'build/setup/transfer-settings-checks.json',
        'clipboard_regression': 'build/clipboard-settings-dos/checks.json',
    }.items():
        raw = json.loads((ROOT / path).read_text())
        assert raw['passed'] and all(c['passed'] and all(c.get('checks', {}).values()) for c in raw['cases']), label
        for source, expected in raw['sources'].items():
            assert digest(source) == expected, source
            sources[source] = expected
        artifacts[path] = digest(path)
        # Exclude synthetic login recipes and detailed wire reports from the
        # public summary; complete reports remain in the retained build tree.
        reports[label] = {k: v for k, v in raw.items() if k not in ('sources', 'cases')}
        reports[label]['cases'] = [
            {k: v for k, v in c.items() if k in
             ('case', 'inputs', 'passed', 'checks', 'full_file_exact',
              'screen_cursor_shape_page_restored', 'input_sha256', 'output_sha256')}
            for c in raw['cases']]
    assert sum(c['inputs'] for c in reports['model']['cases']) == 450
    assert len(reports['editor_regression']['cases']) == 12
    assert len(reports['transfer_UI']['cases']) == 7
    assert len(reports['clipboard_regression']['cases']) == 7
    editor = digest('build/setup/PRMEDIT.EXE')
    assert reports['editor_regression']['binaries']['PRMEDIT.EXE'] == editor
    for label in ('transfer_UI', 'clipboard_regression'):
        assert reports[label]['editor_sha256'] == editor
    assert reports['clipboard_regression']['binary_sha256'] == RUNTIME
    assert digest('build/terminal/TERMINAL.EXE') == RUNTIME
    application = json.loads((ROOT / 'docs/validation/application-components-source-build.json').read_text())
    assert application['passed'] and application['output_count'] == 64
    assert all(v['matches_workspace'] and digest('build/' + p) == v['sha256']
               for p, v in application['outputs'].items())
    assert application['outputs']['setup/PRMEDIT.EXE']['sha256'] == editor
    failure = 'build/setup/tests/transfer-settings-long-directory-invalid-key/fixture-failure.json'
    failed = json.loads((ROOT / failure).read_text())
    assert not failed['passed'] and failed['kind'] == 'unsupported-ADDKEY-token'
    assert failed['config_sha256'] == digest('build/setup/tests/transfer-settings-long-directory-invalid-key/dosbox.conf')
    for p in (failure, 'build/setup/tests/transfer-settings-long-directory-invalid-key/dosbox.conf',
              'docs/validation/application-components-source-build.json',
              'docs/validation/terminal-source-build.json',
              'build/application-source-proof/snapshot.json', 'build/application-source-proof/build.log'):
        artifacts[p] = digest(p)
    for p in ('standalone/record_transfer_settings.py', 'standalone/check_modem_import.py',
              'standalone/terminal_config_fixtures.py', 'src/config/prm.py', 'src/config/test_prm.py'):
        sources[p] = digest(p)
    result = dict(passed=True, runtime_sha256=RUNTIME, editor_sha256=editor,
                  reports=reports, retained_fixture_failure=failed,
                  source_only_rebuild=dict(outputs=64, byte_identical=True,
                                          snapshot_sha256=application['source_snapshot_sha256']),
                  sources=sources, artifacts=artifacts,
                  scope='Mapped transfer-setting editing and independent decoder only. Selected actual DOS owner/UI and existing live clipboard regressions pass. Terminal binary unchanged; startup/live transfer-setting adoption and automatic downloads are not implemented. All F01-F16 gates remain open.')
    (ROOT / 'docs/validation/transfer-settings.json').write_text(json.dumps(result, indent=2) + '\n')
    print('Transfer settings evidence:450 model inputs;12 existing +7 new DOS editor cases;7 live clipboard cases;64 source-only matching outputs.')

if __name__ == '__main__':
    main()
