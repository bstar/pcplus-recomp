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
    dos = read('build/terminal/translation-dos-checks.json')
    frames = read('build/terminal/config-far-checks.json')
    regression = read('build/terminal/setup-profile-regression.json')
    for report in (linked, dos, frames, regression):
        assert report['passed'] and report['binary_sha256'] == binary
    assert linked['inputs'] == 783 and len(linked['cases']) == 4
    assert frames['configuration_bridge_pairs_verified'] == 26
    assert len(frames['rejected_mutations']) == 119
    assert regression['complete'] and len(regression['commands']) == 60
    assert all(command['exit_code'] == 0 for command in regression['commands'])
    proof = read('docs/validation/terminal-source-build.json')
    assert proof['passed'] and proof['binary_sha256'] == binary
    assert proof['matches_workspace_binary'] and proof['matches_workspace_manifest']
    assert dos['passed'] and len(dos['cases']) == 7
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
        if (ROOT / folder / 'TEST.XLT').exists():
            artifacts.append(folder + '/TEST.XLT')
    scripts = ['standalone/check_translation_live.py', 'standalone/test_translation_live_dos.py',
               'standalone/test_connection_dos.py', 'standalone/test_terminal.py',
               'standalone/check_config_far_live.py', 'standalone/check_terminal_options.py',
               'standalone/terminal_memory.py', 'standalone/build_terminal.py',
               'standalone/record_translation_live.py']
    result = dict(passed=True, binary_sha256=binary,
                  memory_layout=manifest['memory_layout'], linked=linked, actual_DOS=dos,
                  call_frames=frames, terminal_regression=regression,
                  source_rebuild=dict(report='docs/validation/terminal-source-build.json',
                                      source_snapshot_sha256=proof['source_snapshot_sha256']),
                  sources={name: sha(name) for name in scripts},
                  runtime_sources=manifest['sources'],
                  retained_artifacts={name: sha(name) for name in artifacts},
                  scope='Explicit startup /X path and checked load, normal receive mapping, raw parser continuation/TX/dedicated owners, capture and RIS. Linked hardware/DOS models and seven actual DOS cases; complete current terminal regression and isolated source build. PRM selection, 7-bit alternative, editor/save/reload and physical UART remain open.')
    (ROOT / 'docs/validation/translation-live.json').write_text(json.dumps(result, indent=2) + '\n')
    print('Recorded live XLT:', linked['inputs'], 'linked inputs, seven DOS cases, 60 regression commands')


if __name__ == '__main__':
    main()
