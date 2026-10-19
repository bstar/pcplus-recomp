#!/usr/bin/env python3
"""Bind native environment recovery and maintained process ownership evidence."""
import json
from pathlib import Path
from build_aspect_environment import ROOT, sha


def read(path):
    return json.loads((ROOT / path).read_text())


def main():
    paths = dict(native='build/aspect-environment/checks.json',
                 original='build/aspect-environment/native-checks.json',
                 host='build/aspect-environment/compiler-checks.json',
                 compiler='build/aspect-compiler-dos/checks.json', runtime='build/aspect-runtime/checks.json',
                 VM='build/aspect-environment-dos/integrated-02/checks.json',
                 queries='build/aspect-system-query-dos/environment-regression-01/checks.json',
                 timestamps='build/aspect-file-times-dos/environment-regression-01/checks.json',
                 parent='build/aspect-environment-parent-dos/integrated-01/checks.json',
                 ENiGMA='build/bbs-lab/results/enigma/owned-environment-login-01/search-checks.json')
    reports = {name: read(path) for name, path in paths.items()}
    assert all(r['passed'] for r in reports.values())
    manifest_path = 'build/aspect-environment/manifest.json'
    manifest = read(manifest_path)
    assert (manifest['native_bytes'], manifest['reused_bytes']) == (555, 237)
    for path, digest in manifest['sources'].items():
        assert sha(ROOT / path) == digest
    for name in ('native', 'original'):
        report = reports[name]
        assert report['cases'] == 697 and report['original_comparisons'] == (697 if name == 'original' else 0)
        assert report['manifest_sha256'] == sha(ROOT / manifest_path)
        assert report['checker_sha256'] == sha(ROOT / 'standalone/check_aspect_environment.py')
    host, compiler = reports['host'], reports['compiler']
    fixture = 'standalone/fixtures/aspect_environment_compiler_vectors.json'
    assert (host['accepted'], host['rejected']) == (19, 29)
    assert host['fixture_sha256'] == compiler['fixture_sources'][fixture] == sha(ROOT / fixture)
    assert host['compiler_sha256'] == compiler['host_compiler_sha256'] == sha(ROOT / 'src/aspect/compiler.py')
    assert (compiler['case_count'], compiler['accepted'], compiler['rejected']) == (1932, 1008, 924)
    case_path = 'build/aspect-compiler-dos/cases.json'
    assert compiler['case_manifest_sha256'] == sha(ROOT / case_path)
    cases = {case['source_sha256']: case for case in read(case_path)}
    for case in read(fixture)['cases']:
        actual = cases[case['source_sha256']]
        assert actual['accepted'] == case['success']
        if case['success']:
            assert actual['asx_sha256'] == case['asx_sha256']
    terminal = sha(ROOT / 'build/terminal/TERMINAL.EXE')
    runner = sha(ROOT / 'build/aspect-runner/ASPECT.EXE')
    compiler_binary = sha(ROOT / 'build/aspect-compiler-dos/ASPCOMP.EXE')
    assert compiler['binary_sha256'] == compiler_binary
    runtime = reports['runtime']
    assert runtime['supported_slot_count'] == 105 and runtime['unsupported_slot_cases'] == 110
    assert runtime['DOS_summary'] == 'ASPECT_RUNTIME 1111 cases 26686 checks 0 failures'
    assert runtime['binary_sha256'] == sha(ROOT / 'build/aspect-runtime/EXECUTE.EXE')
    for name, counts, checker in [('VM', (403, 3119), 'test_aspect_environment_dos.py'),
                                  ('queries', (341, 2905), 'test_aspect_system_query_dos.py'),
                                  ('timestamps', (248, 2907), 'test_aspect_file_times_dos.py')]:
        report = reports[name]
        assert (report['cases'], report['assertions']) == counts and report['same_process_rounds'] == 31
        assert report['runner_sha256'] == runner and report['compiler_sha256'] == compiler_binary
        assert report['checker_sha256'] == sha(ROOT / 'standalone' / checker)
        folder = ROOT / Path(paths[name]).parent
        assert report['harness_sha256'] == sha(folder / 'harness.c')
        assert report['result_sha256'] == sha(folder / 'drive/RESULT.TXT')
    vm = reports['VM']
    folder = ROOT / Path(paths['VM']).parent
    assert vm['native_control_summary'] == 'NATIVE_ENV_CONTROL 9 checks 0 failures first-value=missing second=TWO'
    for field, name in [('native_control_sha256', 'NATIVE.EXE'), ('native_result_sha256', 'NATIVE.TXT'),
                        ('exit_child_sha256', 'ENVEXIT.EXE'), ('exit_result_sha256', 'EXIT.OK'),
                        ('inheritance_child_sha256', 'ENVCHECK.EXE')]:
        assert vm[field] == sha(folder / 'drive' / name)
    assert (folder / 'drive/EXIT.OK').read_bytes() == b'RESTORED'
    assert vm['native_object_sha256'] == sha(ROOT / 'build/aspect-environment/environment_unowned.obj')
    assert vm['runtime_object_sha256'] == sha(ROOT / 'build/aspect-runtime/environment.obj')
    assert vm['native_object_sha256'] != vm['runtime_object_sha256']
    core = {}
    for module in ('runtime', 'environment_runtime', 'script_file_runtime', 'file_info_runtime', 'file_times_runtime',
                   'enumeration_runtime', 'file_io', 'script_path', 'serial_runtime', 'receive_runtime',
                   'directory_runtime', 'when_runtime', 'set_runtime', 'find_runtime'):
        digest = sha(ROOT / 'build/aspect-runtime' / (module + '.o'))
        for name in ('VM', 'queries', 'timestamps'):
            assert digest == sha(ROOT / Path(paths[name]).parent / (module + '.o')), module
        core[module] = digest
    parent = reports['parent']
    assert parent['terminal_sha256'] == terminal and parent['runner_sha256'] == runner
    assert parent['checker_sha256'] == sha(ROOT / 'standalone/test_aspect_environment_parent_dos.py')
    assert parent['reused_renderer_sha256'] == sha(ROOT / 'standalone/test_aspect_renderer_dos.py')
    assert len(parent['cases']) == 1 and all(parent['cases'][0]['checks'].values())
    trace = ROOT / Path(paths['parent']).parent / parent['cases'][0]['case'] / 'ENV.LOG'
    assert parent['environment_trace_sha256'] == sha(trace) and trace.read_bytes() == b'MiXeD|ONE|TWO|'
    enigma = reports['ENiGMA']
    assert len(enigma['checks']) == 23 and all(enigma['checks'].values())
    assert enigma['terminal_sha256'] == terminal and enigma['runner_sha256'] == sha(ROOT / 'lab/bbs/enigma_search_dos.py')
    assert enigma['script_login']['runner_sha256'] == runner and enigma['script_login']['compiler_sha256'] == compiler_binary
    enigma_folder = ROOT / Path(paths['ENiGMA']).parent / 'program'
    assert enigma['script_login']['environment_trace_sha256'] == sha(enigma_folder / 'ENV.LOG')
    for name, value in [('ENV.LOG', b'ONE|TWO|'), ('LOGIN.LOG', b'STARTAUTHREADY'),
                        ('TIME.LOG', b' 3-07-93|13:45'), ('ATTR.LOG', b'RHS|'), ('FIND.LOG', b'FILECHK.BIN|FILECHK|BIN|5')]:
        assert (enigma_folder / name).read_bytes() == value
    proof_path = 'docs/validation/application-components-source-build.json'
    proof = read(proof_path)
    assert proof['passed'] and proof['output_count'] == 271
    for name in ('terminal/TERMINAL.EXE', 'aspect-runner/ASPECT.EXE', 'aspect-compiler-dos/ASPCOMP.EXE', 'aspect-runtime/EXECUTE.EXE'):
        assert proof['outputs'][name]['sha256'] == sha(ROOT / 'build' / name)
    package = read('build/dos-package/manifest.json')
    for name, digest in [('TERMINAL.EXE', terminal), ('ASPECT.EXE', runner), ('ASPCOMP.EXE', compiler_binary)]:
        assert package['files'][name] == digest == sha(ROOT / 'build/dos-package' / name)
    bundle = 'analysis/aspect-environment/rea-01.json'
    assert len(read(bundle)['records']) == 7
    platform = ROOT / 'analysis/aspect-environment/platform-01'
    assert 'COPY 0 [NULL]' in (platform / 'RESULT.TXT').read_text()
    result = dict(passed=True, terminal_sha256=terminal, runner_sha256=runner, compiler_sha256=compiler_binary,
                  native_bytes=555, reused_bytes=237, component_cases=697, original_comparisons=697,
                  supported_opcodes=105, unsupported_opcodes=110,
                  evidence={name: dict(path=path, sha256=sha(ROOT / path)) for name, path in paths.items()},
                  original_compiler=dict(cases=48, accepted=19, rejected=29),
                  DOS_compiler=dict(cases=1932, accepted=1008, rejected=924),
                  VM=dict(cases=403, assertions=3119, rounds=31, native_control=vm['native_control_summary']),
                  runtime_summary=runtime['DOS_summary'], parent_checks=parent['cases'][0]['checks'], ENiGMA_checks=enigma['checks'],
                  core_objects_identical=core,
                  platform_probe={name: sha(platform / name) for name in ('probe.c', 'PROBE.EXE', 'RESULT.TXT')},
                  REA=dict(bundle_sha256=sha(ROOT / bundle), evidence_ids=[r['evidence_id'] for r in read(bundle)['records']]),
                  source_build_proof=dict(path=proof_path, sha256=sha(ROOT / proof_path), outputs=271),
                  package_manifest_sha256=sha(ROOT / 'build/dos-package/manifest.json'), recorder_sha256=sha(Path(__file__)),
                  maintained_policy='Native case-sensitive CRT/whole assignment uppercase; owned persistent vector/value storage, ordinary environ publication and automatic restore/free at process exit. Native deletion-shrink failure semantics retained.',
                  retained_characterization='Native command control loses first assignment through reused borrowed buffer. Watcom also borrows and rejects empty names. Initial harness missing stdlib failed before DOS execution.',
                  live_server_modified=False, physical_modem_validated=False, whole_application_gates_closed=[],
                  remaining=['110 ASPECT opcode slots, remaining selectors/recorder and full F01-F16 application requirements.',
                             'Original returning-warning UI; arbitrary native bytecode/table safety and external environment writers.',
                             'Approved live ENiGMA decoder installation and actual catalog/editor/transfer acceptance; physical RS-232 Wi-Fi modem validation.'])
    (ROOT / 'docs/validation/aspect-environment.json').write_text(json.dumps(result, indent=2) + '\n')
    print('Recorded environment:105 slots,403 VM invocations,23 ENiGMA checks,271 source products; all full gates remain open')


if __name__ == '__main__':
    main()
