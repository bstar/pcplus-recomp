#!/usr/bin/env python3
"""Bind the directory-script checkpoint, including its failed real BBS gate."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--automatic-label', required=True)
    parser.add_argument('--manual-label', required=True)
    args = parser.parse_args()
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
    for folder, leaf in [('terminal', 'TERMINAL.EXE'), ('aspect-runner', 'ASPECT.EXE'),
                         ('aspect-runtime', 'EXECUTE.EXE'),
                         ('aspect-serial', 'SERIAL.EXE')]:
        manifest = read('build/' + folder + '/manifest.json')
        binary = ROOT / 'build' / folder / leaf
        assert binary.is_file(), binary
        assert sha(str(binary.relative_to(ROOT))) == manifest['binary_sha256']
        for path, digest in manifest['sources'].items():
            bind(path, digest)
        modules[folder] = manifest
    native = read('build/aspect-directory/manifest.json')
    bind('src/aspect/directory_builtins.asm', native['source_sha256'])
    modules['aspect-directory'] = native
    parent = modules['terminal']['binary_sha256']
    child = modules['aspect-runner']['binary_sha256']
    assert modules['aspect-runner']['original_inputs'] == []

    for path in [
        'build/terminal/script-launch-live-checks.json',
        'build/terminal/directory-live-checks.json',
        'build/terminal/directory-context-checks.json',
        'build/live-configuration/terminal-checks.json',
        'build/terminal/program-actions-live-checks.json',
        'build/terminal/command-menu-checks.json',
        'build/script-launch-dos/checks.json',
        'build/directory-script-dos/checks.json',
        'build/aspect-script-directory-dos/checks.json',
        'build/aspect-serial-preload-dos/checks.json',
        'build/aspect-serial/checks.json',
        'build/aspect-directory/checks.json',
        'build/aspect-runtime/checks.json',
    ]:
        result = read(path)
        assert result['passed'], path
        if '/terminal/' in path or path.endswith('live-configuration/terminal-checks.json'):
            assert result['binary_sha256'] == parent, path
        if 'terminal_sha256' in result:
            assert result['terminal_sha256'] == parent, path
        if 'runner_sha256' in result:
            assert result['runner_sha256'] == child, path
        for source, digest in result.get('sources', {}).items():
            bind(source, digest)
        reports[path] = result
    compiler = read('build/aspect-compiler/checks.json')
    assert compiler['success'] and compiler['frozen_vectors_checked'] == 377
    bind('src/aspect/compiler.py', compiler['compiler_sha256'])
    bind('standalone/test_aspect_compiler.py', compiler['checker_sha256'])

    workflows = {}
    for kind, label in [('automatic', args.automatic_label), ('manual', args.manual_label)]:
        assert label and all(c.isalnum() or c in '-_' for c in label)
        folder = 'build/bbs-lab/script-login/' + label + '/'
        result = read(folder + 'checks.json')
        assert result['terminal_sha256'] == parent and result['runner_sha256'] == child
        for source, digest in result['sources'].items():
            bind(source, digest)
        for leaf, digest in result['staged'].items():
            assert sha(folder + leaf) == digest, leaf
            evidence[folder + leaf] = digest
        assert sha(folder + 'predictions.json') == result['predictions_sha256']
        for path, digest in result['artifacts'].items():
            assert sha(path) == digest, path
            evidence[path] = digest
        if kind == 'automatic':
            assert not result['passed'] and not result['checks']['resumed_parent_editor']
            assert result['checks']['script_credentials_once'] and result['checks']['authenticated_display']
            assert result['checks']['DOS_harness'] and result['checks']['inputs_unchanged']
        else:
            assert result['passed'] and all(result['checks'].values())
            assert result['editor']['passed'] and all(result['editor']['checks'].values())
        workflows[kind] = result

    proof = read('docs/validation/application-components-source-build.json')
    assert proof['passed'] and proof['output_count'] == 91
    assert not proof['original_executable_present'] and not proof['REA_database_present']
    for path, entry in proof['outputs'].items():
        assert entry['matches_workspace'] and sha('build/' + path) == entry['sha256'], path
    package = read('build/dos-package/manifest.json')
    assert package['original_inputs'] == []
    assert package['files']['TERMINAL.EXE'] == parent and package['files']['ASPECT.EXE'] == child
    for path, digest in package['files'].items():
        assert sha('build/dos-package/' + path) == digest
    bind('standalone/record_directory_scripts.py', sha('standalone/record_directory_scripts.py'))
    result = dict(
        checkpoint_checks_passed=True, full_application_complete=False,
        automatic_BBS_editor_gate_passed=False, normal_build_original_inputs=[],
        modules=modules, sources=sources, local_evidence_sha256=evidence,
        component_reports=reports, compiler=compiler, BBS_workflows=workflows,
        remaining=[
            'Native WAITFOR shared renderer, raw parser continuations and synchronous replies.',
            'Screen/cursor/mode/history continuity across script execution and return.',
            'WHEN dispatch and remaining ASPECT opcode/expression/scheduling families.',
            'Original DOS compile-on-demand, KEY/META bindings and directory cycles.',
            'All sixteen full-application gates and physical RS-232 Wi-Fi modem validation.',
        ])
    output = ROOT / 'docs/validation/directory-scripts.json'
    output.write_text(json.dumps(result, indent=2) + '\n')
    print('Directory-script checkpoint bound; automatic BBS editor gate remains FAILED')


if __name__ == '__main__':
    main()
