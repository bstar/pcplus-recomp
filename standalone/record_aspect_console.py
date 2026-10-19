#!/usr/bin/env python3
"""Reconcile source compiler, native console, production CLI and terminal launch."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = '6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'


def main():
    sources, local, modules = {}, {}, {}

    def sha(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def retain(path):
        local[path] = sha(ROOT / path)
        return json.loads((ROOT / path).read_text())

    def bind(path, expected):
        assert sha(ROOT / path) == expected, path
        assert path not in sources or sources[path] == expected, path
        sources[path] = expected

    for name in ['console', 'runtime', 'runner']:
        base = f'build/aspect-{name}/'
        manifest, checks = retain(base + 'manifest.json'), retain(base + 'checks.json')
        assert checks['passed'] and checks['original_inputs'] == manifest['original_inputs'] == []
        assert checks['binary_sha256'] == manifest['binary_sha256']
        for path, value in manifest['sources'].items():
            bind(path, value)
        key = 'checker_sha256' if name == 'runner' else 'check_sha256'
        bind(f'standalone/check_aspect_{name}.py', checks[key])
        if name != 'console':
            assert checks['manifest_sha256'] == local[base + 'manifest.json']
        native = None
        if name != 'runner':
            comparison = retain(base + 'checks-native.json')
            assert comparison['passed'] and comparison['binary_sha256'] == checks['binary_sha256']
            assert comparison[key] == checks[key]
            native = comparison['optional_original']
            assert native['original_sha256'] == ORIGINAL
            if name == 'runtime':
                assert comparison['manifest_sha256'] == checks['manifest_sha256']
                assert comparison['result_sha256'] == checks['result_sha256']
        modules[name] = dict(manifest=manifest, checks=checks, optional_native=native)
    console, runtime, runner = [modules[k] for k in ['console', 'runtime', 'runner']]
    assert console['optional_native']['exact_console_bytes'] == 296
    assert console['optional_native']['all_component_ranges'] == 44
    assert console['checks']['cpu_scenarios'] == console['optional_native']['paired_cpu_scenarios'] == 459
    assert console['checks']['visited_instructions'] == 145
    assert console['checks']['DOS_summary'] == 'ASPECT_CONSOLE 9384 checks 0 failures'
    inherited = console['checks']['inherited_checker_sha256']
    for path, value in inherited.items():
        bind('standalone/' + path, value)
    assert runtime['checks']['DOS_summary'] == 'ASPECT_RUNTIME 437 cases 6996 checks 0 failures'
    assert runtime['checks']['fixture_count'] == 267 and runtime['checks']['unsupported_slot_cases'] == 158
    assert len(runtime['manifest']['supported_slots']) == 57
    assert runner['checks']['DOS_summary'] == 'RUNNER 16 cases 80 checks 0 failures'
    assert len(runner['checks']['cases']) == 16

    compiler = retain('build/aspect-compiler/checks.json')
    assert compiler['success'] and compiler['original_inputs'] == []
    assert compiler['test_methods'] == 10
    assert compiler['frozen_vectors_checked'] == compiler['presentation_variants_checked'] == 270
    bind('src/aspect/compiler.py', compiler['compiler_sha256'])
    bind('standalone/test_aspect_compiler.py', compiler['checker_sha256'])
    for group, value in compiler['fixture_sha256'].items():
        bind(f'standalone/fixtures/aspect_{group}_vectors.json', value)
    corpus = retain('standalone/fixtures/aspect_console_vectors.json')
    bind('standalone/aspect_console_probe.py', corpus['probe_sha256'])
    bind('standalone/freeze_aspect_console.py', corpus['freezer_sha256'])
    original = retain(corpus['private_report'])
    assert local[corpus['private_report']] == corpus['private_report_sha256']
    assert len(original['cases']) == 55 and sum(c['success'] for c in original['cases']) == 33
    assert len(corpus['vectors']) == 30 and len(corpus['compiler_only']) == 3 and len(corpus['rejected']) == 22

    result_path = 'build/aspect-runtime/RESULT.TXT'
    data = (ROOT / result_path).read_bytes()
    local[result_path] = hashlib.sha256(data).hexdigest()
    assert local[result_path] == runtime['checks']['result_sha256']
    text = data.decode('ascii')
    rows = re.findall(r'CASE (\S+) error=(\d+) steps=(\d+) peak=(\d+) cleanup=(\d+) close=(\d+) int0=(\d+) long0=(\d+)', text)
    assert len(rows) == 437
    unsupported = [r for r in rows if re.fullmatch(r'U[0-9A-F]{3}\.ASX', r[0])]
    slots = {int(k, 16) for k in runtime['manifest']['supported_slots']}
    assert {int(r[0][1:4], 16) for r in unsupported} == set(range(215)) - slots
    for row in unsupported:
        assert tuple(map(int, [row[1], row[2], row[4], row[5]])) == (3, 1, 1, 1)
    outputs = dict(re.findall(r'OUTPUT (\S+) ([0-9A-F]*)', text))
    errors = {'unsupported': 3, 'float': 4, 'budget': 6, 'operand': 7, 'stack': 9,
              'divide_zero': 11, 'native_int0': 12, 'cancelled': 13}
    for name, fixture in runtime['manifest']['fixture_expectations'].items():
        expected = fixture['expected']
        row = next(r for r in rows if r[0] == name + '.ASX')
        assert int(row[1]) == errors.get(expected.get('error'), 0), name
        assert row[4] == row[5] == '1', name
        assert outputs[name + '.ASX'].lower() == expected.get('stdout_hex', '').lower(), name
    terminal = retain('build/terminal/manifest.json')
    for path, value in terminal['sources'].items():
        bind(path, value)
    assert terminal['data_stack_bytes'] == 65344
    linked = retain('build/terminal/script-launch-live-checks.json')
    assert linked['passed'] and linked['inputs'] == 30
    assert linked['binary_sha256'] == terminal['binary_sha256']
    for path, value in linked['sources'].items():
        bind(path, value)
    actual = retain('build/script-launch-dos/checks.json')
    assert actual['passed'] and len(actual['cases']) == 4
    assert actual['terminal_sha256'] == terminal['binary_sha256']
    assert actual['runner_sha256'] == runner['manifest']['binary_sha256']
    bind('standalone/test_script_launch_dos.py', actual['source_sha256'])
    for case in actual['cases']:
        assert case['passed'] and all(case['checks'].values())
    package = retain('build/dos-package/manifest.json')
    assert package['original_inputs'] == []
    for leaf, value in package['files'].items():
        assert sha(ROOT / 'build/dos-package' / leaf) == value, leaf
    assert package['files']['ASPECT.EXE'] == runner['manifest']['binary_sha256']
    assert package['files']['TERMINAL.EXE'] == terminal['binary_sha256']
    for path, value in package['sources'].items():
        bind(path, value)

    evidence = []
    for path in ['analysis/aspect-expression/rea-console-03.json',
                 'analysis/aspect-expression/rea-console-defaults-01.json']:
        bundle = retain(path)
        evidence += [dict(id=r['evidence_id'], operation=r['operation'], parameters=r['parameters'],
                          subject_sha256=r['subject']['digest']['sha256']) for r in bundle['records']]
    assert len(evidence) == 18
    proof = retain('docs/validation/application-components-source-build.json')
    assert proof['passed'] and proof['output_count'] == 85
    assert not proof['original_executable_present'] and not proof['REA_database_present']
    for relative, output in proof['outputs'].items():
        assert output['matches_workspace'] and sha(ROOT / 'build' / relative) == output['sha256'], relative
    sources['standalone/record_aspect_console.py'] = sha(Path(__file__))
    result = dict(passed=True, sources=sources, local_evidence=local, modules=modules,
                  compiler=compiler, terminal=terminal, launch_linked=linked, launch_DOS=actual,
                  package=package, static_evidence=evidence,
                  source_rebuild=dict(output_count=85, snapshot_sha256=proof['source_snapshot_sha256']),
                  limitations=['57of215 slots;158 abort; compiler subset only.',
                               'DOS child launch is not live terminal UART scripting.',
                               'Native unchecked pointers/frames/caret handling remain; trusted authored tests do not prove arbitrary-input safety.',
                               'All F01-F16 whole-application gates remain open; hardware modem testing remains unverified.'])
    out = ROOT / 'docs/validation/aspect-console.json'
    out.write_text(json.dumps(result, indent=2) + '\n')
    print(out.relative_to(ROOT))


if __name__ == '__main__':
    main()
