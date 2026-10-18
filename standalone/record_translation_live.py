#!/usr/bin/env python3
"""Bind the live translation checkpoint to current runtime and retained evidence."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(name):
    return hashlib.sha256((ROOT / name).read_bytes()).hexdigest()


def read(name):
    return json.loads((ROOT / name).read_text())


def main():
    binary = sha('build/terminal/TERMINAL.EXE')
    manifest = read('build/terminal/manifest.json')
    assert manifest['binary_sha256'] == binary
    for name, digest in manifest['sources'].items():
        assert sha(name) == digest, name
    linked = read('build/terminal/translation-live-checks.json')
    modes = read('build/terminal/translation-mode-checks.json')
    original_modes = read('docs/validation/translation-modes-original.json')
    dos = read('build/terminal/translation-dos-checks.json')
    frames = read('build/terminal/config-far-checks.json')
    regression = read('build/terminal/setup-profile-regression.json')
    for report in (linked, modes, original_modes, dos, frames, regression):
        assert report['passed'] and report['binary_sha256'] == binary
    assert linked['inputs'] == 783 and len(linked['cases']) == 4
    assert frames['configuration_bridge_pairs_verified'] == 36
    assert len(frames['rejected_mutations']) == 173
    assert modes['inputs'] == original_modes['inputs'] == 561
    assert len(original_modes['original_cases']) == 5
    assert original_modes['original_sha256'] == '6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
    for report in (modes, original_modes):
        for name, digest in report['sources'].items():
            assert sha(name) == digest, name
    assert regression['complete'] and len(regression['commands']) == 77
    assert all(command['exit_code'] == 0 for command in regression['commands'])
    proof = read('docs/validation/terminal-source-build.json')
    assert proof['passed'] and proof['binary_sha256'] == binary
    assert proof['matches_workspace_binary'] and proof['matches_workspace_manifest']
    assert dos['passed'] and len(dos['cases']) == 12
    editor = read('build/setup/checks.json')
    assert editor['passed'] and len(editor['cases']) == 12
    for name, digest in editor['sources'].items():
        assert sha(name) == digest, name
    for name, digest in editor['binaries'].items():
        assert sha('build/setup/' + name) == digest, name
    for name, digest in dos['sources'].items():
        assert sha(name) == digest, name
    artifacts = []
    for case in dos['cases']:
        assert case['passed'] and all(case['checks'].values())
        assert case['binary_sha256'] == binary
        name = case['case']
        assert Path(name).name == name
        folder = 'build/connection-dos/' + name
        assert (ROOT / folder / 'BEFORE.BIN').read_bytes() == (ROOT / folder / 'AFTER.BIN').read_bytes()
        assert len((ROOT / folder / 'BEFORE.BIN').read_bytes()) == 42
        for leaf in ['BEFORE.BIN', 'AFTER.BIN', 'SCREEN.BIN', 'serial.bin',
                     'TEST.PRM', 'SNAP.COM', 'dosbox.conf', 'result.json']:
            artifacts.append(folder + '/' + leaf)
        for leaf in ('TEST.XLT', 'PCPLUS.XLT'):
            if (ROOT / folder / leaf).exists():
                artifacts.append(folder + '/' + leaf)
    resource = read('docs/validation/resource-lookup.json')
    assert resource['passed'] and resource['binary_sha256'] == binary
    assert resource['linked']['inputs'] == 117 and len(resource['actual_DOS']['cases']) == 12
    adoption = read('docs/validation/live-translation.json')
    assert adoption['passed'] and adoption['binary_sha256'] == binary
    assert adoption['linked']['inputs'] == 331 and len(adoption['actual_DOS']['cases']) == 10
    scripts = ['standalone/check_translation_live.py', 'standalone/test_translation_live_dos.py',
               'standalone/test_connection_dos.py', 'standalone/test_terminal.py',
               'standalone/check_config_far_live.py', 'standalone/check_terminal_options.py',
               'standalone/terminal_memory.py', 'standalone/build_terminal.py',
               'standalone/check_translation_modes.py', 'standalone/test_setup_dos.py',
               'standalone/test_setup_live_dos.py', 'src/config/prm.py', 'src/config/test_prm.py',
               'standalone/record_translation_live.py']
    result = dict(passed=True, binary_sha256=binary,
                  memory_layout=manifest['memory_layout'], linked=linked, saved_modes=modes,
                  original_mode_oracle=original_modes, actual_DOS=dos, offline_editor_DOS=editor,
                  call_frames=frames, terminal_regression=regression,
                  source_rebuild=dict(report='docs/validation/terminal-source-build.json',
                                      source_snapshot_sha256=proof['source_snapshot_sha256']),
                  sources={name: sha(name) for name in scripts},
                  runtime_sources=manifest['sources'],
                  retained_artifacts={name: sha(name) for name in artifacts},
                  resource_lookup=dict(report='docs/validation/resource-lookup.json', linked_inputs=117, generic_DOS_assertions=30, actual_DOS_cases=12),
                  confirmed_live_adoption=dict(report='docs/validation/live-translation.json', linked_inputs=331, actual_DOS_cases=10),
                  scope='Saved PRM modes0/1/2, checked current-directory then bounded PCPLUS-environment default table lookup and explicit /X override, driver7-bit mask and binary-transfer rejection,44-byte serial/628-byte candidate ABI,46-field mode editor, default/decline deferral and confirmed live adoption. Linked561 mode inputs, five genuine-original selector cases,783 prior translation inputs,12 actual DOS translation and12 offline editor cases, full77-command terminal regression and isolated source rebuild. Offline XLTEDIT provides checked table editing/save/reload. Confirmed live changes bind namespaces, stage tables and commit mode/table/mask during the foreground handoff. Same-mode reload, a dedicated terminal XLT editor action, lookup for other resources and physical UART remain open.')
    (ROOT / 'docs/validation/translation-live.json').write_text(json.dumps(result, indent=2) + '\n')
    print('Recorded saved XLT modes:', modes['inputs'], 'mode inputs,12 DOS cases,77 regression commands')


if __name__ == '__main__':
    main()
