#!/usr/bin/env python3
"""Bind the ASIOv2/input-policy checkpoint to current source and DOS evidence."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = '6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'


def main():
    sources, local, modules, reports = {}, {}, {}, {}

    def sha(path):
        return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()

    def read(path):
        local[path] = sha(path)
        return json.loads((ROOT / path).read_text())

    def bind(path, digest):
        assert sha(path) == digest, path
        assert path not in sources or sources[path] == digest, path
        sources[path] = digest

    for name, binary, checker in [
        ('aspect-receive-policy', 'POLICY.EXE', 'check_aspect_receive_policy.py'),
        ('aspect-runtime', 'EXECUTE.EXE', 'check_aspect_runtime.py'),
        ('aspect-runner', 'ASPECT.EXE', 'check_aspect_runner.py'),
        ('aspect-serial', 'SERIAL.EXE', 'check_aspect_serial.py'),
        ('terminal', 'TERMINAL.EXE', None),
    ]:
        base = 'build/' + name + '/'
        manifest = read(base + 'manifest.json')
        if name == 'terminal':
            assert manifest['kind'] == 'source-only-interactive-dos-terminal'
        else:
            assert manifest['original_inputs'] == []
        assert manifest['binary_sha256'] == sha(base + binary), base
        for path, digest in manifest['sources'].items():
            bind(path, digest)
        module = dict(manifest=manifest)
        if checker:
            check = read(base + 'checks.json')
            assert check['passed'] and check['original_inputs'] == []
            assert check['binary_sha256'] == manifest['binary_sha256']
            bind('standalone/' + checker, check.get('checker_sha256', check.get('check_sha256')))
            if 'manifest_sha256' in check:
                assert check['manifest_sha256'] == local[base + 'manifest.json']
            module['checks'] = check
        if name in ('aspect-receive-policy', 'aspect-runtime'):
            native = read(base + 'checks-native.json')
            assert native['passed'] and native['binary_sha256'] == manifest['binary_sha256']
            assert native['optional_original']['original_sha256'] == ORIGINAL
            assert native['check_sha256'] == check['check_sha256']
            module['optional_native'] = native['optional_original']
        modules[name] = module

    policy = modules['aspect-receive-policy']['checks']
    assert (policy['native_policy_bytes'], policy['reused_native_bytes'], policy['cpu_scenarios'],
            policy['visited_instructions']) == (83, 64, 8824, 37)
    assert policy['DOS_summary'] == 'ASPECT_RECEIVE_POLICY 424036 checks 0 failures'
    runtime = modules['aspect-runtime']
    assert runtime['checks']['DOS_summary'] == 'ASPECT_RUNTIME 515 cases 9091 checks 0 failures'
    assert runtime['checks']['fixture_count'] == 351 and runtime['checks']['unsupported_slot_cases'] == 152
    assert len(runtime['manifest']['supported_slots']) == 63
    assert runtime['manifest']['fixture_data']['sha256'] == sha('build/aspect-runtime/CASES.DAT')
    assert modules['aspect-runner']['checks']['DOS_summary'] == 'RUNNER 21 cases 105 checks 0 failures'
    assert modules['aspect-serial']['checks']['inputs'] == 59
    assert len(modules['aspect-serial']['checks']['groups']) == 14
    runner = modules['aspect-runner']['manifest']['binary_sha256']
    terminal = modules['terminal']['manifest']['binary_sha256']

    def case_report(path, count, checker, key='checker_sha256'):
        report = read(path)
        assert report['passed'] and len(report['cases']) == count, path
        assert all(case['passed'] and all(case['checks'].values()) for case in report['cases']), path
        assert report.get('original_inputs', []) == [], path
        bind('standalone/' + checker, report[key])
        if 'runner_sha256' in report:
            assert report['runner_sha256'] == runner
        if 'runner_manifest_sha256' in report:
            assert report['runner_manifest_sha256'] == local['build/aspect-runner/manifest.json']
        if 'terminal_sha256' in report:
            assert report['terminal_sha256'] == terminal
        for field, source in [('compiler_sha256', 'src/aspect/compiler.py'),
                              ('handoff_header_sha256', 'src/aspect/serial_handoff.h')]:
            if field in report:
                bind(source, report[field])
        for field in ('sources', 'parent_sources'):
            for source, digest in report.get(field, {}).items():
                if source.startswith('build/'):
                    assert sha(source) == digest
                    local[source] = digest
                else:
                    bind(source, digest)
        reports[path] = report
        return report

    backend = case_report('build/aspect-serial/dos-checks.json', 6, 'test_aspect_serial_dos.py')
    assert backend['binary_sha256'] == modules['aspect-serial']['manifest']['binary_sha256']
    assert backend['manifest_sha256'] == local['build/aspect-serial/manifest.json']
    direct = case_report('build/aspect-serial-translation-dos/checks.json', 4, 'test_aspect_serial_translation_dos.py')
    for leaf, digest in direct['binaries'].items():
        assert sha('build/aspect-serial-translation-dos/' + leaf) == digest
    actual = case_report('build/aspect-script-translation-dos/checks.json', 24, 'test_aspect_script_translation_dos.py')
    assert sum(len(c['checks']) for c in actual['cases']) == 192
    assert sha('build/aspect-script-translation-dos/XLTPAR.EXE') == actual['parent_sha256']
    assert sha('build/aspect-script-translation-dos/parent.c') == actual['parent_source_sha256']
    assert sha('build/aspect-script-translation-dos/predictions.json') == actual['predictions_sha256']
    for case in actual['cases']:
        assert case['runner_sha256'] == runner and case['parent_sha256'] == actual['parent_sha256']
    for folder, count, checker in [
        ('aspect-script-serial-dos', 28, 'test_aspect_script_serial_dos.py'),
        ('aspect-script-receive-dos', 15, 'test_aspect_script_receive_dos.py'),
        ('aspect-serial-bbs', 2, 'test_aspect_serial_bbs.py'),
        ('script-launch-dos', 7, 'test_script_launch_dos.py'),
    ]:
        case_report('build/' + folder + '/checks.json', count, checker,
                    'source_sha256' if folder == 'script-launch-dos' else 'checker_sha256')
    linked = read('build/terminal/script-launch-live-checks.json')
    assert linked['passed'] and linked['binary_sha256'] == terminal
    assert linked['inputs'] == 55 and len(linked['cases']) == 14
    assert linked['manifest_sha256'] == local['build/terminal/manifest.json']
    bind('standalone/check_script_launch_live.py', linked['checker_sha256'])
    for path, digest in linked['sources'].items():
        bind(path, digest)
    reports['build/terminal/script-launch-live-checks.json'] = linked
    for leaf in ('config-far-checks.json', 'program-actions-live-checks.json', 'command-menu-checks.json'):
        path = 'build/terminal/' + leaf
        report = read(path)
        assert report['passed'] and report['binary_sha256'] == terminal, path
        reports[path] = report

    compiler = read('build/aspect-compiler/checks.json')
    assert compiler['success'] and compiler['original_inputs'] == []
    assert compiler['frozen_vectors_checked'] == compiler['presentation_variants_checked'] == 358
    bind('src/aspect/compiler.py', compiler['compiler_sha256'])
    bind('standalone/test_aspect_compiler.py', compiler['checker_sha256'])
    for group, digest in compiler['fixture_sha256'].items():
        bind(f'standalone/fixtures/aspect_{group}_vectors.json', digest)

    historical = read('docs/validation/aspect-serial.json')['modules']['runner']['manifest']['binary_sha256']
    for item in reports['build/script-launch-dos/checks.json']['regression_history']:
        identity = read(item['runner_identity_source'])
        assert local[item['runner_identity_source']] == item['runner_identity_sha256']
        assert item['runner_sha256'] == identity['runner_sha256'] == historical
    proof = read('docs/validation/application-components-source-build.json')
    assert proof['passed'] and proof['output_count'] == 90
    assert not proof['original_executable_present'] and not proof['REA_database_present']
    for path, output in proof['outputs'].items():
        assert output['matches_workspace'] and output['sha256'] == sha('build/' + path), path
    package = read('build/dos-package/manifest.json')
    assert package['original_inputs'] == []
    assert package['files']['ASPECT.EXE'] == runner and package['files']['TERMINAL.EXE'] == terminal
    for leaf, digest in package['files'].items():
        assert sha('build/dos-package/' + leaf) == digest
    for path, digest in package['sources'].items():
        bind(path, digest)

    bundle = read('analysis/aspect-expression/rea-receive-policy-01.json')
    evidence = [dict(id=r['evidence_id'], operation=r['operation'], parameters=r['parameters'],
                     subject_sha256=r['subject']['digest']['sha256']) for r in bundle['records']]
    assert len(evidence) == 2
    defaults = read('analysis/aspect-receive/platform-defaults-audit.json')
    assert defaults['source_sha256'] == ORIGINAL and not defaults['original_inputs_executed']
    bind('standalone/record_aspect_input_policy.py', sha('standalone/record_aspect_input_policy.py'))
    result = dict(passed=True, normal_build_original_inputs=[], original_sha256=ORIGINAL,
                  sources=sources, local_evidence_sha256=local, modules=modules,
                  actual_DOS_and_linked_reports=reports, compiler=compiler, package=package,
                  static_evidence=evidence, native_default_facts=defaults['facts'], source_rebuild_outputs=90,
                  limitations=[
                      'All F01-F16 full-application gates remain open.',
                      '83 native policy bytes include64 already recovered bytes and19 adapter bytes.',
                      'Production uses native4C74 mapping with display0; native4C3C displayed adapter is component-tested only.',
                      'Full renderer/ANSI continuation consumption and WHEN pattern/event callbacks remain explicit unsupported services.',
                      'ASIOv2 is a maintained child interface, not an original PCPlus structure; oldv1 parents remain supported.',
                      'Seven-bit masking occurs at dequeue; unread ASIO handback remains raw.',
                      'BBS regressions here are greetings, not full login/menu/transfer compatibility.',
                      'Physical UART/Wi-Fi modem validation, full compiler/VM/recorder and remaining application integration are unfinished.',
                      'Static synthetic analysis carriers were never executed.'])
    (ROOT / 'docs/validation/aspect-input-policy.json').write_text(json.dumps(result, indent=2) + '\n')
    print('Input policy reconciled:24 DOS cases/192 checks,7 terminal workflows,90 source-only outputs')


if __name__ == '__main__':
    main()
