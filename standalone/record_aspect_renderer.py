#!/usr/bin/env python3
"""Bind current renderer evidence; never rerun tests or overwrite old checkpoints."""
import hashlib
import json
import importlib.util
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TERMINAL = 'dacbd777fbd5afaf441ad46ec559be2b95c53fd5ba9c1219ebfb865cd48e66ae'
RUNNER = '3369c3cb30c55153ad009be1c244af52efdb11117e5efd9d877fe50651d2ddbf'


def main():
    evidence, sources, reports = {}, {}, {}

    def sha(path):
        return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()

    def read(path):
        evidence[path] = sha(path)
        return json.loads((ROOT / path).read_text())

    def bind(path, digest):
        assert sha(path) == digest, ('source changed', path)
        assert path not in sources or sources[path] == digest, path
        sources[path] = digest

    def checked(path):
        value = read(path)
        assert value['passed'], path
        assert value.get('original_inputs', []) == [], path
        assert all(value.get('checks', {}).values()), path
        return value

    manifests = {}
    for folder, binary, digest in [('terminal', 'TERMINAL.EXE', TERMINAL),
                                    ('aspect-runner', 'ASPECT.EXE', RUNNER),
                                    ('aspect-renderer-policy', 'POLICY.EXE', None)]:
        value = read('build/' + folder + '/manifest.json')
        assert value.get('original_inputs', []) == [], folder
        for path, source_digest in value['sources'].items():
            bind(path, source_digest)
        actual = sha('build/' + folder + '/' + binary)
        expected = value.get('binary_sha256') or value['binaries'][binary]
        assert actual == expected and (digest is None or actual == digest), folder
        manifests[folder] = value

    product = checked('build/aspect-renderer-dos/final-history/checks.json')
    assert product['terminal_sha256'] == TERMINAL and product['runner_sha256'] == RUNNER
    assert len(product['cases']) == 10
    assert sum(len(case['checks']) for case in product['cases']) == 300
    for case in product['cases']:
        assert case['passed'] and all(case['checks'].values()), case['case']
        assert case['binary_sha256'] == TERMINAL and case['runner_sha256'] == RUNNER
    bind('standalone/test_aspect_renderer_dos.py', product['checker_sha256'])
    # Linker maps carry a creation timestamp. Recreate only the passive observer
    # from the current map; exact source equality proves every consumed binding.
    # No product execution, parser replacement or report mutation occurs here.
    spec = importlib.util.spec_from_file_location('renderer_observer_checkpoint',
                                                ROOT / 'standalone/test_aspect_renderer_dos.py')
    fixture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture)
    with tempfile.TemporaryDirectory(prefix='aspect-renderer-record-') as tmp:
        fixture.OUT = Path(tmp)
        fixture.observer(fixture.map_offsets(ROOT / 'build/terminal/terminal.map'))
        actual_observer = hashlib.sha256((Path(tmp) / 'observer.asm').read_bytes()).hexdigest()
    assert actual_observer == product['observer_source_sha256']
    evidence['build/terminal/terminal.map'] = sha('build/terminal/terminal.map')
    reports['product'] = dict(path='build/aspect-renderer-dos/final-history/checks.json',
                             passed=True, cases=10, checks=300,
                             case_names=[case['case'] for case in product['cases']],
                             executed_map_sha256=product['parent_map_sha256'],
                             current_map_observer_source_identical=True)

    policy = checked('build/aspect-renderer-policy/checks.json')
    assert policy['manifest_sha256'] == evidence['build/aspect-renderer-policy/manifest.json']
    assert policy['DOS_summary'] == 'checks=29206 failures=0'
    assert policy['cpu']['passed'] and policy['cpu']['count'] == 21
    assert policy['cpu']['cases'][0]['kind'] == 'independent_far_history_layout'
    layout = policy['cpu']['cases'][0]
    assert layout['history_segment'] != layout['parent_DS'] and layout['result'] == 0
    bind('standalone/check_aspect_renderer_policy.py', policy['checker_sha256'])
    reports['policy'] = dict(path='build/aspect-renderer-policy/checks.json', passed=True,
                            DOS_assertions=29206, CPU_probes=21,
                            independent_far_history_regression=True)

    for key, path, checker, binary, count, manifest in [
        ('parent_client', 'build/terminal/aspect-render-parent-client-checks.json',
         'standalone/check_aspect_render_parent_client.py', TERMINAL, 22, 'terminal'),
        ('child_client', 'build/aspect-render-client/checks.json',
         'standalone/check_aspect_render_client.py', RUNNER, 14, 'aspect-runner'),
        ('child_client_DOS', 'build/aspect-render-client-dos/checks.json',
         'standalone/test_aspect_render_client_dos.py', RUNNER, 5, 'aspect-runner')]:
        value = checked(path)
        assert value['binary_sha256'] == binary and len(value['cases']) == count, path
        assert value['manifest_sha256'] == evidence['build/' + manifest + '/manifest.json']
        bind(checker, value['checker_sha256'])
        if key == 'child_client':
            assert value['inputs'] == 38
        reports[key] = dict(path=path, passed=True, cases=count)

    sync_path = 'build/bbs-lab/script-login/render-v4-dac-sync/checks.json'
    sync = checked(sync_path)
    assert sync['terminal_sha256'] == TERMINAL and sync['runner_sha256'] == RUNNER
    assert sync['editor']['passed'] and all(sync['editor']['checks'].values())
    assert sync['run']['passed'] and all(sync['run']['checks'].values())
    assert sync['run']['name'] == 'synchronet'
    for path, digest in sync['sources'].items():
        bind(path, digest)
    reports['strict_synchronet'] = dict(path=sync_path, passed=True,
                                        authenticated=True, stock_editor=True,
                                        draft_aborted=True, physical_UART=False)

    history = [
        'build/aspect-renderer-dos/attempt-history.json',
        'build/aspect-renderer-policy/dos-run-002/binding-defect.json',
        'build/aspect-render-client-history/pre-CLI-transition/transition-window-failure.json',
        'build/aspect-renderer-dos/final-candidate/checks.json',
        'build/bbs-lab/script-login/render-v4-ef3-sync/checks.json',
    ]
    for path in history:
        evidence[path] = sha(path)
    bind('docs/ASPECT_RENDERER.md', sha('docs/ASPECT_RENDERER.md'))
    bind('standalone/record_aspect_renderer.py', sha('standalone/record_aspect_renderer.py'))
    output = dict(checkpoint_checks_passed=True, renderer_integrated=True,
                  full_application_complete=False, full_application_gates_F01_F16='open',
                  ENiGMA_success_claim=False, original_inputs=[],
                  products={'TERMINAL.EXE': TERMINAL, 'ASPECT.EXE': RUNNER},
                  reports=reports, sources=sources, local_evidence_sha256=evidence,
                  preserved_history=history,
                  limits=[
                      'Trusted-source partial63-slot ASPECT runtime; no arbitrary bytecode safety.',
                      'Profiles4/6, mode3 80x25 page0, checked closed owners and disabled sinks only.',
                      'Actual product tests use emulated UART/BIOS and controlled peer; no physical CTS/DCD proof.',
                      'Stack/MCB/ISR components and observed depth2 do not prove all parser streams or peak stack.',
                      'Strict Synchronet run is loopback; no ENiGMA success or complete application claim.',
                  ])
    (ROOT / 'docs/validation/aspect-renderer.json').write_text(json.dumps(output, indent=2) + '\n')
    print('Renderer checkpoint bound: 10 DOS cases/300 checks; strict Synchronet PASS; F01-F16 open')


if __name__ == '__main__':
    main()
