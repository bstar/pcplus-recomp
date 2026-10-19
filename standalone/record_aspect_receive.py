#!/usr/bin/env python3
"""Reconcile native receive code, compiler corpus, modeled VM and actual DOS."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = '6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'


def main():
    sources, local, modules = {}, {}, {}

    def sha(path):
        return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()

    def read(path):
        local[path] = sha(path)
        return json.loads((ROOT / path).read_text())

    def bind(path, digest):
        assert sha(path) == digest, path
        assert path not in sources or sources[path] == digest, path
        sources[path] = digest

    for name, binary in [('receive-commands', 'RECEIVE.EXE'), ('runtime', 'EXECUTE.EXE'), ('runner', 'ASPECT.EXE')]:
        base = f'build/aspect-{name}/'
        manifest, checks = read(base + 'manifest.json'), read(base + 'checks.json')
        assert checks['passed'] and manifest['original_inputs'] == checks['original_inputs'] == []
        assert manifest['binary_sha256'] == checks['binary_sha256'] == sha(base + binary)
        for path, digest in manifest['sources'].items():
            bind(path, digest)
        key = 'checker_sha256' if name == 'runner' else 'check_sha256'
        bind(f'standalone/check_aspect_{name.replace("-", "_")}.py', checks[key])
        for path, digest in checks.get('inherited_checker_sha256', {}).items():
            bind('standalone/' + path, digest)
        if 'manifest_sha256' in checks:
            assert checks['manifest_sha256'] == local[base + 'manifest.json']
        native = None
        if name != 'runner':
            comparison = read(base + 'checks-native.json')
            assert comparison['passed'] and comparison['binary_sha256'] == checks['binary_sha256']
            assert comparison[key] == checks[key]
            native = comparison['optional_original']
            assert native['original_sha256'] == ORIGINAL
        modules[name] = dict(manifest=manifest, checks=checks, optional_native=native)

    component = modules['receive-commands']
    assert component['manifest']['native_receive_bytes'] == component['checks']['native_receive_bytes'] == 435
    assert component['checks']['native_receive_ranges'] == 9 and component['checks']['all_component_ranges'] == 60
    assert component['checks']['cpu_scenarios'] == 696 and component['checks']['visited_instructions'] == 188
    assert component['checks']['DOS_summary'] == 'ASPECT_RECEIVE_COMMANDS 14500 checks 0 failures'
    runtime, runner = modules['runtime'], modules['runner']
    assert runtime['checks']['DOS_summary'] == 'ASPECT_RUNTIME 515 cases 9091 checks 0 failures'
    assert runtime['checks']['fixture_count'] == 351 and len(runtime['manifest']['supported_slots']) == 63
    assert runtime['checks']['unsupported_slot_cases'] == 152
    table = runtime['manifest']['fixture_data']
    assert table['schema'] == 'ACV1' and table['file'] == 'CASES.DAT' and table['cases'] == 351
    local['build/aspect-runtime/CASES.DAT'] = sha('build/aspect-runtime/CASES.DAT')
    assert table['sha256'] == local['build/aspect-runtime/CASES.DAT']
    assert runner['checks']['DOS_summary'] == 'RUNNER 21 cases 105 checks 0 failures'

    compiler = read('build/aspect-compiler/checks.json')
    assert compiler['success'] and compiler['original_inputs'] == []
    assert compiler['frozen_vectors_checked'] == compiler['presentation_variants_checked'] == 358
    bind('src/aspect/compiler.py', compiler['compiler_sha256'])
    bind('standalone/test_aspect_compiler.py', compiler['checker_sha256'])
    for group, digest in compiler['fixture_sha256'].items():
        bind(f'standalone/fixtures/aspect_{group}_vectors.json', digest)
    corpus = read('standalone/fixtures/aspect_receive_vectors.json')
    assert len(corpus['vectors']) == 54 and len(corpus['compiler_only']) == 2 and len(corpus['rejected']) == 35
    bind('standalone/aspect_receive_probe.py', corpus['probe_sha256'])
    bind('standalone/freeze_aspect_receive.py', corpus['freezer_sha256'])
    oracle = read(corpus['private_report'])
    assert local[corpus['private_report']] == corpus['private_report_sha256']
    assert len(oracle['cases']) == 91 and sum(c['success'] for c in oracle['cases']) == 56
    for vector in corpus['vectors']:
        assert runtime['manifest']['fixture_expectations'][vector['name']]['expected'] == vector['expected']

    terminal = read('build/terminal/manifest.json')
    assert terminal['binary_sha256'] == sha('build/terminal/TERMINAL.EXE')
    for path, digest in terminal['sources'].items():
        bind(path, digest)
    actual = read('build/aspect-script-receive-dos/checks.json')
    assert actual['passed'] and actual['original_inputs'] == []
    assert actual['runner_sha256'] == runner['manifest']['binary_sha256']
    assert actual['runner_manifest_sha256'] == local['build/aspect-runner/manifest.json']
    assert len(actual['cases']) == 15 and sum(len(c['checks']) for c in actual['cases']) == 135
    bind('standalone/test_aspect_script_receive_dos.py', actual['checker_sha256'])
    bind('standalone/test_aspect_script_serial_dos.py', actual['shared_parent_checker_sha256'])
    bind('src/aspect/compiler.py', actual['compiler_sha256'])
    bind('src/aspect/serial_handoff.h', actual['handoff_header_sha256'])
    assert all(c['passed'] and all(c['checks'].values()) for c in actual['cases'])
    assert all(c['runner_sha256'] == actual['runner_sha256'] for c in actual['cases'])

    regressions = {}
    for path in ['build/aspect-script-serial-dos/checks.json', 'build/aspect-serial-bbs/checks.json', 'build/script-launch-dos/checks.json']:
        report = read(path)
        assert report['passed'] and report['runner_sha256'] == runner['manifest']['binary_sha256']
        assert all(c['passed'] and all(c['checks'].values()) for c in report['cases'])
        if 'terminal_sha256' in report:
            assert report['terminal_sha256'] == terminal['binary_sha256']
            bind('standalone/test_script_launch_dos.py', report['source_sha256'])
        else:
            assert report['runner_manifest_sha256'] == local['build/aspect-runner/manifest.json']
            assert report['compiler_sha256'] == compiler['compiler_sha256']
        regressions[path] = report
    assert [len(r['cases']) for r in regressions.values()] == [28, 2, 5]
    previous = read('docs/validation/aspect-serial.json')
    historical_runner = previous['modules']['runner']['manifest']['binary_sha256']
    for item in regressions['build/script-launch-dos/checks.json'].get('regression_history', []):
        identity = read(item['runner_identity_source'])
        assert local[item['runner_identity_source']] == item['runner_identity_sha256']
        assert item['runner_sha256'] == identity['runner_sha256'] == historical_runner

    package = read('build/dos-package/manifest.json')
    assert package['original_inputs'] == [] and package['files']['ASPECT.EXE'] == actual['runner_sha256']
    for leaf, digest in package['files'].items():
        assert sha('build/dos-package/' + leaf) == digest
    for path, digest in package['sources'].items():
        bind(path, digest)
    proof = read('docs/validation/application-components-source-build.json')
    assert proof['passed'] and proof['output_count'] == 89
    assert not proof['original_executable_present'] and not proof['REA_database_present']
    for relative, output in proof['outputs'].items():
        assert output['matches_workspace'] and output['sha256'] == sha('build/' + relative), relative

    evidence = {}
    for path in ['analysis/aspect-expression/rea-receive-01.json', 'analysis/aspect-expression/rea-receive-02.json', 'analysis/aspect-expression/rea-receive-04.json']:
        bundle = read(path)
        for record in bundle['records']:
            evidence[record['evidence_id']] = dict(id=record['evidence_id'], operation=record['operation'],
                    parameters=record['parameters'], subject_sha256=record['subject']['digest']['sha256'])
    defaults = read('analysis/aspect-receive/platform-defaults-audit.json')
    assert defaults['source_sha256'] == ORIGINAL and not defaults['original_inputs_executed']
    for fact in defaults['facts']:
        if 'path' in fact:
            local[fact['path']] = sha(fact['path'])
    failures = {}
    for path in ['analysis/aspect-receive/maintained-byte-failed-01-reason.json', 'build/aspect-runtime/receive-wallclock-timeout-01/reason.json']:
        failures[path] = read(path)
    local['analysis/aspect-receive/corpus-superseded-03.json'] = sha('analysis/aspect-receive/corpus-superseded-03.json')
    bind('standalone/record_aspect_receive.py', sha('standalone/record_aspect_receive.py'))
    result = dict(passed=True, original_sha256=ORIGINAL, normal_build_original_inputs=[], sources=sources,
            local_evidence_sha256=local, modules=modules, compiler=compiler,
            receive_corpus=dict(runtime=54, compiler_only=2, rejected=35, original_attempts=91, original_accepted=56),
            actual_receive_DOS=actual, regression_DOS=regressions, terminal_sha256=terminal['binary_sha256'], package=package,
            static_evidence=list(evidence.values()), native_default_facts=defaults['facts'],
            retained_failures=failures, source_rebuild_outputs=89,
            limitations=['Full application and all F01-F16 gates remain open.',
              'Native4C74 translation, pattern monitoring and rendering remain platform dependencies; raw bytes can differ from native ANSI continuation consumption.',
              'COMGETC/CD use effective post-open display suppression; direct native RGET/WAITQUIET display is not reconstructed in the raw child.',
              'Production delayed read and receive-drain polling are maintained cooperative services, distinct from the native busy loop and cancellation gaps.',
              'Maintained RGET stops before an81st non-CR store; native zero-limit overflow remains diagnosed, not reproduced in production.',
              'Actual receive tests use virtual COM1/38400/8N1/N; existing BBS regressions here are greetings only.',
              'Physical UART/modem validation, full compiler, invocation/event services and terminal integration remain unfinished.',
              'Static synthetic analysis carriers were never executed.'])
    output = ROOT / 'docs/validation/aspect-receive.json'
    output.write_text(json.dumps(result, indent=2) + '\n')
    print('Receive checkpoint reconciled:435 native bytes,63 slots,515 modeled DOS cases,15 receive UART cases,89 source-only outputs')


if __name__ == '__main__':
    main()
