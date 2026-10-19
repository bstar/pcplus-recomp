#!/usr/bin/env python3
"""Bind mechanical bridge/unread proofs without claiming renderer integration."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    evidence, sources, reports = {}, {}, {}

    def sha(path):
        return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()

    def read(path):
        evidence[path] = sha(path)
        return json.loads((ROOT / path).read_text())

    def bind(path, digest):
        assert sha(path) == digest, path
        assert path not in sources or sources[path] == digest, path
        sources[path] = digest

    modules = {}
    for folder in ['aspect-resident-service', 'aspect-resident-bridge', 'aspect-serial', 'aspect-runner']:
        manifest = read('build/' + folder + '/manifest.json')
        assert manifest['original_inputs'] == []
        for path, digest in manifest['sources'].items():
            bind(path, digest)
        binaries = manifest.get('binaries', {})
        if not binaries:
            binaries = {'SERIAL.EXE' if folder == 'aspect-serial' else 'ASPECT.EXE': manifest['binary_sha256']}
        for leaf, digest in binaries.items():
            assert sha('build/' + folder + '/' + leaf) == digest
        modules[folder] = manifest
    for folder, leaf, checker in [
        ('aspect-resident-service', 'checks.json', 'check_aspect_resident_service.py'),
        ('aspect-resident-service', 'checks-dos.json', 'test_aspect_resident_service_dos.py'),
        ('aspect-resident-bridge', 'checks.json', 'check_aspect_resident_bridge.py'),
        ('aspect-resident-bridge', 'checks-dos.json', 'test_aspect_resident_bridge_dos.py'),
        ('aspect-serial', 'checks.json', 'check_aspect_serial.py'),
    ]:
        path = 'build/' + folder + '/' + leaf
        result = read(path)
        assert result['passed'] and result['original_inputs'] == [], path
        assert result['manifest_sha256'] == evidence['build/' + folder + '/manifest.json']
        bind('standalone/' + checker, result['checker_sha256'])
        assert all(result.get('checks', {}).values()), path
        for attempt in result.get('regression_history', []):
            assert sha(attempt['report']) == attempt['sha256'], attempt['report']
            evidence[attempt['report']] = attempt['sha256']
        reports[path] = result
    unread = read('build/aspect-serial-unread-dos/checks.json')
    assert unread['passed'] and len(unread['cases']) == 4
    bind('standalone/test_aspect_serial_unread_dos.py', unread['checker_sha256'])
    bind('standalone/test_aspect_serial_preload_dos.py', unread['fixture_checker_sha256'])
    for source, digest in unread['sources'].items():
        bind(source, digest)
    reports['build/aspect-serial-unread-dos/checks.json'] = unread
    metadata = read('build/aspect-script-directory-dos/checks.json')
    assert metadata['passed'] and len(metadata['cases']) == 15
    assert metadata['runner_sha256'] == modules['aspect-runner']['binary_sha256']
    bind('standalone/test_aspect_script_directory_dos.py', metadata['checker_sha256'])
    reports['build/aspect-script-directory-dos/checks.json'] = metadata
    runner = read('build/aspect-runner/checks.json')
    assert runner['passed'] and runner['binary_sha256'] == modules['aspect-runner']['binary_sha256']
    assert runner['manifest_sha256'] == evidence['build/aspect-runner/manifest.json']
    bind('standalone/check_aspect_runner.py', runner['checker_sha256'])
    bind('src/aspect/compiler.py', runner['compiler_sha256'])
    reports['build/aspect-runner/checks.json'] = runner
    proof = read('docs/validation/application-components-source-build.json')
    assert proof['passed'] and proof['output_count'] == 91
    assert not proof['original_executable_present'] and not proof['REA_database_present']
    for path, entry in proof['outputs'].items():
        assert entry['matches_workspace'] and sha('build/' + path) == entry['sha256'], path
    package = read('build/dos-package/manifest.json')
    assert package['files']['ASPECT.EXE'] == modules['aspect-runner']['binary_sha256']
    assert package['original_inputs'] == []
    for leaf, digest in package['files'].items():
        assert sha('build/dos-package/' + leaf) == digest
    bind('standalone/record_resident_service.py', sha('standalone/record_resident_service.py'))
    bind('Makefile', sha('Makefile'))
    output = dict(
        checkpoint_checks_passed=True, renderer_capability_published=False,
        full_application_complete=False, automatic_BBS_editor_gate_passed=False,
        modules=modules, reports=reports, sources=sources, local_evidence_sha256=evidence,
        limits=[
            'Mechanical bridge fixtures are separate from the actual terminal renderer.',
            'Touched stack bytes in tiny fixtures do not establish renderer maximum stack usage.',
            'Timer and controlled software interrupts do not establish physical UART IRQ behavior.',
            'Application lease/MCB/descriptor validation, owner guards and whole-service budgets remain.',
            'Full parser/callback integration, view adoption and MESSAGE/diagnostic routing remain.',
            'Strict automatic Synchronet editor failure remains retained in directory-scripts.json.',
            'All full-application gates, remaining ASPECT features and hardware validation remain.',
        ])
    (ROOT / 'docs/validation/aspect-resident-service.json').write_text(json.dumps(output, indent=2) + '\n')
    print('Mechanical resident-service checkpoint bound; renderer remains unintegrated')


if __name__ == '__main__':
    main()
