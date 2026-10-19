#!/usr/bin/env python3
"""Record source SET component proof and retained original recovery evidence."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(relative):
    path = ROOT / relative
    return dict(sha256=sha(path), result=json.loads(path.read_text()))


def main():
    findings_path = ROOT / 'analysis/aspect-set/findings.json'
    assert sha(findings_path) == '6f95b9f26588d2a3ed69e891a662a0931fee7b23f3c61f767e624f16afef603e'
    findings = json.loads(findings_path.read_text())
    retained = {}
    for name in ('analysis/aspect-set/native-replay-01.json',
                 'analysis/aspect-set/display-policy-replay-01.json'):
        assert sha(ROOT / name) == findings['files'][name]
        retained[name] = read(name)
        assert retained[name]['result']['passed']
    for item in findings['retained_REA'].values():
        assert sha(ROOT / item['path']) == item['sha256']
    reports = {name: read(name) for name in (
        'build/aspect-set/manifest.json', 'build/aspect-set/checks.json',
        'build/aspect-set/checks-original.json', 'build/terminal-reset/checks-original.json',
        'build/terminal-reset/dos-results.json',
        'docs/validation/application-components-source-build.json')}
    for name, item in reports.items():
        if not name.endswith('manifest.json'):
            assert item['result']['passed']
    manifest = reports['build/aspect-set/manifest.json']['result']
    for name in ('checks.json', 'checks-original.json'):
        report = reports['build/aspect-set/' + name]['result']
        assert report['manifest_sha256'] == reports['build/aspect-set/manifest.json']['sha256']
        assert report['source_sha256'] == sha(ROOT / 'src/aspect/set_commands.asm')
        assert report['checker_sha256'] == sha(ROOT / 'standalone/check_aspect_set.py')
        assert report['all_source_instructions_visited'] and report['cases'] == 3487
    assert reports['build/terminal-reset/checks-original.json']['result']['binary_sha256'] == sha(ROOT / 'build/terminal-reset/RESET.EXE')
    assert reports['build/terminal-reset/dos-results.json']['result']['binary_sha256'] == sha(ROOT / 'build/terminal-reset/RESET.EXE')
    files = ('src/aspect/set_commands.asm', 'standalone/build_aspect_set.py',
             'standalone/check_aspect_set.py', 'standalone/fixtures/aspect_set_native_units.json',
             'reconstruction/terminal_reset/status_refresh.asm',
             'reconstruction/terminal_reset/recover.py', 'reconstruction/terminal_reset/provenance.json',
             'standalone/terminal_reset_host.asm', 'standalone/check_terminal_reset.py',
             'standalone/prove_source_build.py', 'docs/ASPECT_SET_NATIVE.md',
             'standalone/record_aspect_set.py')
    result = dict(schema='aspect-set-native-validation-v1', passed=True,
                  scope='Recovered source component and script-label relocation. ASPECT.EXE still supports SET WHENCASE only; full native status/RPC and application gates remain open.',
                  sources={name: sha(ROOT / name) for name in files},
                  native_bytes=manifest['native_bytes'], reports=reports, retained_original_replay=retained,
                  retained_REA=findings['retained_REA'], native_bindings=findings['native_bindings'],
                  frozen_discovery_ledger_sha256=sha(findings_path),
                  discovery_note='The retained discovery ledger predates the D464 relocation correction; current corrected source and linked regression are bound above.')
    out = ROOT / 'docs/validation/aspect-set-native.json'
    out.write_text(json.dumps(result, indent=2) + '\n')
    print(out.relative_to(ROOT))


if __name__ == '__main__':
    main()
