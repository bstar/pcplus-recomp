#!/usr/bin/env python3
"""Bind native serial recovery, composed DOS scripts, UART and terminal evidence."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = '6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'


def main():
    sources, retained, modules = {}, {}, {}

    def sha(path):
        return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()

    def read(path):
        retained[path] = sha(path)
        return json.loads((ROOT / path).read_text())

    def bind(path, digest):
        assert sha(path) == digest, path
        assert path not in sources or sources[path] == digest, path
        sources[path] = digest

    for name in ['serial-commands', 'serial', 'runtime', 'runner']:
        base = f'build/aspect-{name}/'
        manifest, checks = read(base + 'manifest.json'), read(base + 'checks.json')
        assert manifest['original_inputs'] == checks['original_inputs'] == []
        assert checks['passed'] and manifest['binary_sha256'] == checks['binary_sha256']
        binary = {'runtime': 'EXECUTE.EXE', 'runner': 'ASPECT.EXE'}.get(name, 'SERIAL.EXE')
        assert sha(base + binary) == manifest['binary_sha256']
        for path, digest in manifest['sources'].items():
            bind(path, digest)
        checker = f'standalone/check_aspect_{name.replace("-", "_")}.py'
        bind(checker, checks.get('check_sha256', checks.get('checker_sha256', sha(checker))))
        for path, digest in checks.get('inherited_checker_sha256', {}).items():
            bind('standalone/' + path, digest)
        if 'manifest_sha256' in checks:
            assert checks['manifest_sha256'] == retained[base + 'manifest.json']
        native = None
        if name in ['serial-commands', 'runtime']:
            comparison = read(base + 'checks-native.json')
            assert comparison['passed'] and comparison['binary_sha256'] == checks['binary_sha256']
            assert comparison['check_sha256'] == checks['check_sha256']
            native = comparison['optional_original']
            assert native['original_sha256'] == ORIGINAL
        modules[name] = dict(manifest=manifest, checks=checks, optional_native=native)

    native = modules['serial-commands']
    assert native['checks']['cpu_scenarios'] == 1261
    assert native['checks']['visited_instructions'] == 220
    assert native['optional_native']['all_component_ranges'] == 51
    assert native['optional_native']['exact_serial_bytes'] == 523
    assert native['checks']['DOS_summary'] == 'ASPECT_SERIAL_COMMANDS 11057 checks 0 failures'
    assert sum(u['end_exclusive'] - u['start'] for u in native['manifest']['units'] if u['name'].startswith('serial-commands')) == 523
    runtime = modules['runtime']
    assert runtime['checks']['DOS_summary'] == 'ASPECT_RUNTIME 465 cases 8047 checks 0 failures'
    assert runtime['checks']['fixture_count'] == 297
    assert runtime['checks']['unsupported_slot_cases'] == 156
    assert len(runtime['manifest']['supported_slots']) == 59
    runner = modules['runner']
    assert runner['checks']['DOS_summary'] == 'RUNNER 21 cases 105 checks 0 failures'
    assert len(runner['checks']['cases']) == 21

    compiler = read('build/aspect-compiler/checks.json')
    assert compiler['success'] and compiler['original_inputs'] == []
    assert compiler['frozen_vectors_checked'] == compiler['presentation_variants_checked'] == 302
    bind('src/aspect/compiler.py', compiler['compiler_sha256'])
    bind('standalone/test_aspect_compiler.py', compiler['checker_sha256'])
    for group, digest in compiler['fixture_sha256'].items():
        bind(f'standalone/fixtures/aspect_{group}_vectors.json', digest)
    corpus = read('standalone/fixtures/aspect_serial_vectors.json')
    assert len(corpus['vectors']) == 30 and len(corpus['compiler_only']) == 2 and len(corpus['rejected']) == 5
    bind('standalone/aspect_serial_probe.py', corpus['probe_sha256'])
    bind('standalone/freeze_aspect_serial.py', corpus['freezer_sha256'])
    original_compiler = read(corpus['private_report'])
    assert retained[corpus['private_report']] == corpus['private_report_sha256']
    assert len(original_compiler['cases']) == 37
    assert sum(c['success'] for c in original_compiler['cases']) == 32

    terminal = read('build/terminal/manifest.json')
    assert sha('build/terminal/TERMINAL.EXE') == terminal['binary_sha256']
    for path, digest in terminal['sources'].items():
        bind(path, digest)
    linked = read('build/terminal/script-launch-live-checks.json')
    assert linked['passed'] and linked['binary_sha256'] == terminal['binary_sha256']
    assert linked['inputs'] == 41
    for path, digest in linked['sources'].items():
        bind(path, digest)
    regressions = {}
    for label in ['program-actions-live', 'config-far', 'command-menu']:
        report = read(f'build/terminal/{label}-checks.json')
        assert report['passed'] and report['binary_sha256'] == terminal['binary_sha256']
        regressions[label] = report
    parent = read('build/script-launch-dos/checks.json')
    assert parent['passed'] and parent['terminal_sha256'] == terminal['binary_sha256']
    assert len(parent['cases']) == 5
    assert parent['runner_sha256'] == runner['manifest']['binary_sha256']
    assert all(c['passed'] and all(c['checks'].values()) for c in parent['cases'])
    bind('standalone/test_script_launch_dos.py', parent['source_sha256'])
    uart = read('build/aspect-serial/dos-checks.json')
    assert uart['passed'] and uart['binary_sha256'] == modules['serial']['manifest']['binary_sha256']
    assert len(uart['cases']) == 6 and all(c['passed'] for c in uart['cases'])
    bind('standalone/test_aspect_serial_dos.py', uart['checker_sha256'])
    assert uart['manifest_sha256'] == retained['build/aspect-serial/manifest.json']
    package = read('build/dos-package/manifest.json')
    assert package['original_inputs'] == []
    assert package['files']['ASPECT.EXE'] == runner['manifest']['binary_sha256']
    assert package['files']['TERMINAL.EXE'] == terminal['binary_sha256']
    for leaf, digest in package['files'].items():
        assert sha('build/dos-package/' + leaf) == digest
    for path, digest in package['sources'].items():
        bind(path, digest)

    wire = read('build/aspect-script-serial-dos/checks.json')
    bbs = read('build/aspect-serial-bbs/checks.json')
    for report, checker in [(wire, 'test_aspect_script_serial_dos.py'), (bbs, 'test_aspect_serial_bbs.py')]:
        assert report['passed'] and report['original_inputs'] == []
        assert report['runner_sha256'] == runner['manifest']['binary_sha256']
        assert report['runner_manifest_sha256'] == retained['build/aspect-runner/manifest.json']
        bind('src/aspect/serial_handoff.h', report['handoff_header_sha256'])
        bind('standalone/' + checker, report['checker_sha256'])
        bind('src/aspect/compiler.py', report['compiler_sha256'])
        assert all(c['passed'] and all(c['checks'].values()) for c in report['cases'])
        assert all(c.get('binary_sha256', c.get('runner_sha256')) == report['runner_sha256'] for c in report['cases'])
        assert all(c['parent_binary_sha256'] == report['parent_binary_sha256'] for c in report['cases'])
    assert len(wire['cases']) == 28 and len(bbs['cases']) == 2
    assert sum(len(c['checks']) for c in wire['cases']) == 224
    assert sum(len(c['checks']) for c in bbs['cases']) == 16
    assert wire['fixture_sha256'] == sha('standalone/fixtures/aspect_serial_vectors.json')
    bind('src/aspect/serial_handoff.h', wire['handoff_header_sha256'])
    bind('lab/bbs/modem.py', bbs['modem_source_sha256'])

    prompt_failures = {}
    for label in ['observer', 'no-observer', 'exit6']:
        path = f'build/script-launch-dos/failed-serial-handback-{label}/result.json'
        report = read(path)
        assert not report['passed']
        prompt_failures[label] = report
    failed = read('build/aspect-runtime/serial-failed-01.json')
    retained['build/aspect-runtime/serial-failed-01.txt'] = sha('build/aspect-runtime/serial-failed-01.txt')
    assert failed['result_sha256'] == retained['build/aspect-runtime/serial-failed-01.txt']
    assert failed['fixture_sha256'] == corpus['superseded']['corpus_sha256']
    rea = {}
    for path in ['analysis/aspect-expression/rea-serial-02.json', 'analysis/aspect-expression/rea-serial-05.json']:
        bundle = read(path)
        for record in bundle['records']:
            identity = record.get('id', record.get('evidence_id'))
            assert identity, record.keys()
            rea[identity] = dict(id=identity, operation=record['operation'],
                                 parameters=record['parameters'],
                                 subject_sha256=record['subject']['digest']['sha256'],
                                 limitations=record.get('limitations', []))
    proof = read('docs/validation/application-components-source-build.json')
    assert proof['passed'] and proof['output_count'] == 87
    assert not proof['original_executable_present'] and not proof['REA_database_present']
    for relative, output in proof['outputs'].items():
        assert output['matches_workspace'] and output['sha256'] == sha('build/' + relative), relative
    for relative in ['aspect-runner/ASPECT.EXE', 'aspect-runtime/EXECUTE.EXE', 'aspect-serial/SERIAL.EXE', 'aspect-serial-commands/SERIAL.EXE']:
        assert proof['outputs'][relative]['sha256'] == sha('build/' + relative)
    assert proof['outputs']['terminal/TERMINAL.EXE']['sha256'] == terminal['binary_sha256']
    bind('standalone/record_aspect_serial.py', sha('standalone/record_aspect_serial.py'))
    result = dict(passed=True, original_sha256=ORIGINAL, normal_build_original_inputs=[], sources=sources,
                  local_evidence_sha256=retained, modules=modules, compiler=compiler,
                  corpus=dict(runtime=30, compiler_only=2, rejected=5, original_accepted=32, original_attempts=37),
                  terminal=dict(binary_sha256=terminal['binary_sha256'], data_stack_bytes=terminal['data_stack_bytes'], linked=linked, actual_dos=parent, regressions=regressions),
                  package=package, actual_uart=uart, actual_script_uart=wire, local_bbs_greetings=bbs,
                  retained_prediction_failure=failed, retained_prompt_failures=prompt_failures, REA_records=list(rea.values()), source_proof_outputs=87,
                  limitations=['Full PCPlus application and all F01-F16 gates remain open.',
                               'Serial commands use raw child receive services, not the complete native renderer/capture/scheduler.',
                               'Nonzero calibrated intercharacter delay, SET and most application services remain unsupported.',
                               'Independent script wire cases use COM1/38400/8N1/N; UART owner covers other flow policies separately.',
                               'BBS tests here prove owned-local greetings and unread handback only, not login/menu compatibility.',
                               'Physical UART/Wi-Fi modem timing and real hardware validation remain outstanding.',
                               'Synthetic static carriers were never executed; patched inactive BB2F excluded from recovery claims.'])
    out = ROOT / 'docs/validation/aspect-serial.json'
    out.write_text(json.dumps(result, indent=2) + '\n')
    print('Serial checkpoint reconciled:', out, '59 slots; 465 runtime cases; 28 wire cases; 2 greeting cases; 87 source-only outputs')


if __name__ == '__main__':
    main()
