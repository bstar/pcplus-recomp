#!/usr/bin/env python3
"""Bind bounded default lookup to linked/DOS tests and full source-only build."""
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
    linked = read('build/terminal/resource-lookup-checks.json')
    dos = read('build/terminal/resource-lookup-dos-checks.json')
    generic = read('build/resource-path/checks.json')
    for report in [linked, dos, generic]:
        assert report['passed'];sources(report)
    assert linked['binary_sha256'] == dos['binary_sha256'] == runtime
    assert linked['inputs'] == 117 and linked['maximum_stack_bytes'] == 426
    assert len(dos['cases']) == 12 and generic['log'] == 'RESOURCE PATH PASS 30 checks'
    assert generic['binary_sha256'] == sha('build/resource-path/RESOURCE.EXE')
    frames = read('build/terminal/config-far-checks.json')
    assert frames['passed'] and frames['binary_sha256'] == runtime
    assert frames['configuration_bridge_pairs_verified'] == 33 and len(frames['rejected_mutations']) == 164
    regression = read('build/terminal/setup-profile-regression.json')
    assert regression['passed'] and regression['complete'] and regression['binary_sha256'] == runtime
    expected = subprocess.check_output(['make', '-n', 'test-terminal'], cwd=ROOT, text=True).splitlines()
    assert len(expected) == 68 and [c['command'] for c in regression['commands']] == expected
    assert all(c['exit_code'] == 0 for c in regression['commands'])
    proof = read('docs/validation/application-components-source-build.json')
    assert proof['passed'] and proof['output_count'] == 63
    for name, digest in [('terminal/TERMINAL.EXE', runtime),
                         ('resource-path/RESOURCE.EXE', generic['binary_sha256'])]:
        assert proof['outputs'][name]['sha256'] == digest and proof['outputs'][name]['matches_workspace']
    artifacts = ['build/resource-path/RESOURCE.EXE', 'build/resource-path/CHECKS.TXT',
                 'build/resource-path/checks.json', 'build/terminal/resource-lookup-checks.json',
                 'build/terminal/resource-lookup-dos-checks.json',
                 'build/terminal/setup-profile-regression.json', 'build/terminal/setup-profile-regression.log']
    if regression.get('continuation'):
        for name in ['build/terminal/resource-lookup-regression-attempt1.json',
                     'build/terminal/resource-lookup-regression-attempt1.log']:
            artifacts.append(name)
        prior = read('build/terminal/resource-lookup-regression-attempt1.json')
        assert prior['binary_sha256'] == runtime and not prior['passed']
        assert len(prior['commands']) == 27 and prior['commands'][-1]['exit_code'] == 1
        assert all(c['exit_code'] == 0 for c in prior['commands'][:-1])
        assert prior['commands'][:-1] == regression['commands'][:26]
    for case in dos['cases']:
        assert case['passed'] and all(case['checks'].values()) and case['binary_sha256'] == runtime
        folder = ROOT/'build/connection-dos'/case['case']
        assert folder.parent == ROOT/'build/connection-dos'
        assert (folder/'BEFORE.BIN').read_bytes() == (folder/'AFTER.BIN').read_bytes()
        for path in sorted(folder.rglob('*')):
            if path.is_file():
                artifacts.append(str(path.relative_to(ROOT)))
    scripts = ['standalone/record_resource_lookup.py', 'standalone/build_terminal.py',
               'standalone/test_resource_path_dos.py', 'standalone/resource_path_host.c',
               'standalone/check_resource_lookup.py', 'standalone/test_resource_lookup_dos.py',
               'standalone/test_connection_dos.py', 'standalone/check_config_far_live.py',
               'standalone/check_far_code_live.py',
               'standalone/terminal_memory.py', 'standalone/prove_source_build.py']
    report = dict(passed=True, binary_sha256=runtime, memory_layout=manifest['memory_layout'],
                  linked=linked, generic_DOS=generic, actual_DOS=dos, call_frames=frames,
                  terminal_regression=regression, runtime_sources=manifest['sources'],
                  source_rebuild=dict(report='docs/validation/application-components-source-build.json',
                                      output_count=proof['output_count'], source_snapshot_sha256=proof['source_snapshot_sha256']),
                  sources={p: sha(p) for p in scripts}, retained_artifacts={p: sha(p) for p in artifacts},
                  native_evidence=dict(original_sha256='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904',
                    assembly_evidence_id='ev_1cd43dbde8697560fddafd763fd3ab56971d91bd6badd8b88553d8e1cc1d6417',
                    pseudocode_evidence_id='ev_e36893dd21a8e0238063e007dda32a4fd0f457d6c1d4a7e9ad9eb4e7db399009',
                    scope='Reused retained REA static resolver exports. Maintained bounded C policy; no new original execution or native analysis session.'),
                  scope='Default saved-mode XLT startup only: checked current file, fallback only on open errors2/3, bounded inherited PCPLUS directory, exact256-byte commit. Explicit /X and modes0/2 bypass lookup.117 linked inputs,30 real DOS generic assertions,12 actual DOS startup cases,68-command terminal regression and63-output isolated source rebuild. Confirmed live mode adoption is recorded separately in live-translation.json. Other resource fallback, same-mode reload and physical UART/modem remain open.')
    (ROOT/'docs/validation/resource-lookup.json').write_text(json.dumps(report, indent=2)+'\n')
    print('Recorded resource lookup', runtime)


if __name__ == '__main__':
    main()
