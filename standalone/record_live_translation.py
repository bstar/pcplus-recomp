#!/usr/bin/env python3
"""Bind confirmed live XLT selection to actual DOS and source-only builds."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def read(name):
    return json.loads((ROOT/name).read_text())


def sha(name):
    return hashlib.sha256((ROOT/name).read_bytes()).hexdigest()


def sources(report):
    for name, digest in report['sources'].items():
        assert sha(name) == digest, name


def main():
    runtime = sha('build/terminal/TERMINAL.EXE')
    manifest = read('build/terminal/manifest.json');sources(manifest)
    assert manifest['binary_sha256'] == runtime
    linked = read('build/terminal/live-translation-checks.json')
    dos = read('build/terminal/live-translation-dos-checks.json')
    for report in [linked, dos]:
        assert report['passed'];sources(report)
    assert linked['binary_sha256'] == dos['terminal_sha256'] == runtime
    assert linked['inputs'] == 331 and len(dos['cases']) == 10
    assert dos['editor_sha256'] == sha('build/setup/PRMEDIT.EXE')
    assert dos['child_sha256'] == sha('build/live-translation-child/CHDIR.EXE')
    frames = read('build/terminal/config-far-checks.json')
    assert frames['passed'] and frames['binary_sha256'] == runtime
    assert frames['configuration_bridge_pairs_verified'] == 60 and len(frames['rejected_mutations']) == 269
    regression = read('build/terminal/setup-profile-regression.json')
    assert regression['passed'] and regression['complete'] and regression['binary_sha256'] == runtime
    expected = subprocess.check_output(['make', '-n', 'test-terminal'], cwd=ROOT, text=True).splitlines()
    assert len(expected) == 77 and [c['command'] for c in regression['commands']] == expected
    assert all(c['exit_code'] == 0 for c in regression['commands'])
    proof = read('docs/validation/application-components-source-build.json')
    assert proof['passed'] and proof['output_count'] == 64
    for name, digest in [('terminal/TERMINAL.EXE', runtime),
                         ('live-translation-child/CHDIR.EXE', dos['child_sha256'])]:
        assert proof['outputs'][name]['sha256'] == digest and proof['outputs'][name]['matches_workspace']
    artifacts = ['build/terminal/live-translation-checks.json', 'build/terminal/live-translation-dos-checks.json',
                 'build/terminal/setup-profile-regression.json', 'build/terminal/setup-profile-regression.log',
                 'build/live-translation-child/manifest.json', 'build/live-translation-child/CHDIR.EXE']
    for case in dos['cases']:
        assert case['passed'] and all(case['checks'].values())
        name = case['case'];assert Path(name).name == name
        folder = ROOT/'build/setup-startup'/name
        assert (folder/'BEFORE.BIN').read_bytes() == (folder/'AFTER.BIN').read_bytes()
        for path in sorted(folder.rglob('*')):
            if path.is_file():
                artifacts.append(str(path.relative_to(ROOT)))
    scripts = ['standalone/record_live_translation.py', 'standalone/check_live_translation.py',
               'standalone/test_live_translation_dos.py', 'standalone/test_setup_startup_dos.py',
               'standalone/build_live_translation_child.py', 'standalone/live_translation_child.c',
               'standalone/check_config_far_live.py', 'standalone/terminal_memory.py',
               'standalone/build_terminal.py', 'standalone/prove_source_build.py']
    result = dict(passed=True, binary_sha256=runtime, memory_layout=manifest['memory_layout'],
                  linked=linked, actual_DOS=dos, call_frames=frames, terminal_regression=regression,
                  runtime_sources=manifest['sources'], sources={p: sha(p) for p in scripts},
                  retained_artifacts={p: sha(p) for p in artifacts},
                  source_rebuild=dict(report='docs/validation/application-components-source-build.json',
                                      source_snapshot_sha256=proof['source_snapshot_sha256'], output_count=proof['output_count']),
                  scope='Confirmed live PRM mode0/1/2 adoption with pre-child canonical current/PCPLUS namespaces, private exact256-byte staging and final guarded mode/table/mask commit before UART resumes. Explicit /X remains pinned; failures/declines retain active mode with independent edit adoption.331 linked inputs,10 actual DOS editor/namespace workflows,269 malformed frames/layouts,77-command regression and64 byte-identical isolated outputs. Explicit same-table reload has separate evidence in translation-reload.json. Dedicated terminal XLT editor action, original shared-memory PCSETUP ABI and physical modem remain open.')
    (ROOT/'docs/validation/live-translation.json').write_text(json.dumps(result, indent=2)+'\n')
    print('Recorded live translation', runtime)


if __name__ == '__main__':
    main()
