#!/usr/bin/env python3
"""Bind native DOS queries, compiler/VM/parent/ENiGMA and clean-build evidence."""
import json
from pathlib import Path
from build_aspect_system_query import ROOT, sha


def read(path):
    return json.loads((ROOT / path).read_text())


def main():
    paths = dict(native='build/aspect-system-query/checks.json',
                 original='build/aspect-system-query/native-checks.json',
                 host='build/aspect-system-query/compiler-checks.json',
                 compiler='build/aspect-compiler-dos/checks.json',
                 runtime='build/aspect-runtime/checks.json',
                 VM='build/aspect-system-query-dos/integrated-03/checks.json',
                 timestamps='build/aspect-file-times-dos/queries-regression-01/checks.json',
                 paths='build/aspect-paths-dos/queries-regression-01/checks.json',
                 parent='build/aspect-system-query-parent-dos/integrated-01/checks.json',
                 ENiGMA='build/bbs-lab/results/enigma/owned-system-queries-login-01/search-checks.json')
    reports = {name: read(path) for name, path in paths.items()}
    assert all(r['passed'] for r in reports.values())
    manifest_path = 'build/aspect-system-query/manifest.json'
    manifest = read(manifest_path)
    assert manifest['native_bytes'] == 167
    for path, digest in manifest['sources'].items():
        assert sha(ROOT / path) == digest
    for name in ('native', 'original'):
        report = reports[name]
        assert report['cases'] == 3782
        assert report['original_comparisons'] == (3782 if name == 'original' else 0)
        assert report['manifest_sha256'] == sha(ROOT / manifest_path)
        assert report['checker_sha256'] == sha(ROOT / 'standalone/check_aspect_system_query.py')
    host, compiler = reports['host'], reports['compiler']
    assert (host['accepted'], host['rejected']) == (38, 75)
    fixture = 'standalone/fixtures/aspect_system_query_compiler_vectors.json'
    assert host['fixture_sha256'] == compiler['fixture_sources'][fixture] == sha(ROOT / fixture)
    assert host['compiler_sha256'] == compiler['host_compiler_sha256'] == sha(ROOT / 'src/aspect/compiler.py')
    assert (compiler['case_count'], compiler['accepted'], compiler['rejected']) == (1879, 989, 890)
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
    assert runtime['supported_slot_count'] == 103 and runtime['unsupported_slot_cases'] == 112
    assert runtime['DOS_summary'] == 'ASPECT_RUNTIME 1113 cases 26730 checks 0 failures'
    assert runtime['binary_sha256'] == sha(ROOT / 'build/aspect-runtime/EXECUTE.EXE')
    for name, counts, checker in [('VM', (341, 2899), 'test_aspect_system_query_dos.py'),
                                  ('timestamps', (248, 2901), 'test_aspect_file_times_dos.py')]:
        report = reports[name]
        assert (report['cases'], report['assertions']) == counts and report['same_process_rounds'] == 31
        assert report['runner_sha256'] == runner and report['compiler_sha256'] == compiler_binary
        assert report['checker_sha256'] == sha(ROOT / 'standalone' / checker)
        folder = ROOT / Path(paths[name]).parent
        assert report['harness_sha256'] == sha(folder / 'harness.c')
        assert report['result_sha256'] == sha(folder / 'drive/RESULT.TXT')
    vm = reports['VM']
    folder = ROOT / Path(paths['VM']).parent
    assert vm['native_control_summary'] == 'NATIVE_QUERY_CONTROL 14 checks 0 failures DOSVER-global=OLD'
    assert vm['native_control_sha256'] == sha(folder / 'drive/NATIVE.EXE')
    assert vm['native_control_result_sha256'] == sha(folder / 'drive/NATIVE.TXT')
    assert vm['native_object_sha256'] == sha(ROOT / 'build/aspect-system-query/system_query.obj')
    assert vm['runtime_object_sha256'] == sha(ROOT / 'build/aspect-runtime/system_query.obj')
    assert vm['native_object_sha256'] != vm['runtime_object_sha256']
    core = {}
    for module in ('runtime', 'script_file_runtime', 'file_info_runtime', 'file_times_runtime',
                   'enumeration_runtime', 'file_io', 'script_path', 'serial_runtime',
                   'receive_runtime', 'directory_runtime', 'when_runtime', 'set_runtime', 'find_runtime'):
        digest = sha(ROOT / 'build/aspect-runtime' / (module + '.o'))
        for name in ('VM', 'timestamps'):
            assert digest == sha(ROOT / Path(paths[name]).parent / (module + '.o')), module
        core[module] = digest
    path_report = reports['paths']
    assert path_report['runner_sha256'] == runner and path_report['compiler_sha256'] == compiler_binary
    assert path_report['checker_sha256'] == sha(ROOT / 'standalone/test_aspect_paths_dos.py')
    assert path_report['scripts'] == 4 and path_report['status_checks'] == 19
    parent = reports['parent']
    assert parent['terminal_sha256'] == terminal and parent['runner_sha256'] == runner
    assert parent['checker_sha256'] == sha(ROOT / 'standalone/test_aspect_system_query_parent_dos.py')
    assert len(parent['cases']) == 1 and all(parent['cases'][0]['checks'].values())
    parent_folder = ROOT / Path(paths['parent']).parent / parent['cases'][0]['case']
    assert parent['query_trace_sha256'] == sha(parent_folder / 'QUERY.LOG')
    enigma = reports['ENiGMA']
    assert len(enigma['checks']) == 22 and all(enigma['checks'].values())
    assert enigma['terminal_sha256'] == terminal and enigma['runner_sha256'] == sha(ROOT / 'lab/bbs/enigma_search_dos.py')
    assert enigma['script_login']['runner_sha256'] == runner and enigma['script_login']['compiler_sha256'] == compiler_binary
    enigma_folder = ROOT / Path(paths['ENiGMA']).parent / 'program'
    assert enigma['script_login']['system_query_trace_sha256'] == sha(enigma_folder / 'QUERY.LOG')
    assert (enigma_folder / 'LOGIN.LOG').read_bytes() == b'STARTAUTHREADY'
    assert (enigma_folder / 'TIME.LOG').read_bytes() == b' 3-07-93|13:45'
    assert (enigma_folder / 'ATTR.LOG').read_bytes() == b'RHS|'
    assert (enigma_folder / 'FIND.LOG').read_bytes() == b'FILECHK.BIN|FILECHK|BIN|5'
    proof_path = 'docs/validation/application-components-source-build.json'
    proof = read(proof_path)
    assert proof['passed'] and proof['output_count'] == 258
    for name in ('terminal/TERMINAL.EXE', 'aspect-runner/ASPECT.EXE', 'aspect-compiler-dos/ASPCOMP.EXE', 'aspect-runtime/EXECUTE.EXE'):
        assert proof['outputs'][name]['sha256'] == sha(ROOT / 'build' / name)
    package = read('build/dos-package/manifest.json')
    for name, digest in [('TERMINAL.EXE', terminal), ('ASPECT.EXE', runner), ('ASPCOMP.EXE', compiler_binary)]:
        assert package['files'][name] == digest == sha(ROOT / 'build/dos-package' / name)
    bundle = 'analysis/aspect-system-query/rea-01.json'
    assert len(read(bundle)['records']) == 7
    result = dict(passed=True, terminal_sha256=terminal, runner_sha256=runner,
                  compiler_sha256=compiler_binary, native_bytes=167,
                  supported_opcodes=103, unsupported_opcodes=112,
                  evidence={name: dict(path=path, sha256=sha(ROOT / path)) for name, path in paths.items()},
                  component_cases=3782, original_comparisons=3782,
                  original_compiler=dict(cases=113, accepted=38, rejected=75),
                  DOS_compiler=dict(cases=1879, accepted=989, rejected=890),
                  VM=dict(cases=341, assertions=2899, rounds=31, native_control=vm['native_control_summary']),
                  runtime_summary=runtime['DOS_summary'], parent_checks=parent['cases'][0]['checks'],
                  ENiGMA_checks=enigma['checks'],
                  query_traces=dict(parent=(parent_folder / 'QUERY.LOG').read_text('ascii'),
                                    isolated_ENiGMA=(enigma_folder / 'QUERY.LOG').read_text('ascii')),
                  core_objects_identical=core,
                  REA=dict(bundle_sha256=sha(ROOT / bundle), evidence_ids=[r['evidence_id'] for r in read(bundle)['records']]),
                  source_build_proof=dict(path=proof_path, sha256=sha(ROOT / proof_path), outputs=258),
                  package_manifest_sha256=sha(ROOT / 'build/dos-package/manifest.json'), recorder_sha256=sha(Path(__file__)),
                  maintained_policy='DOSVER destination/flush; exact native GETDIR prefix/error and DISKFREE first-product truncation/comparison policies retained.',
                  retained_failures='Fixture used built-in Z as absent and misescaped generated paths. Corrected fresh fixture uses unmapped E/canonical paths. Native DOSVER control retains OLD global.',
                  live_server_modified=False, physical_modem_validated=False, whole_application_gates_closed=[],
                  remaining=['112 ASPECT opcode slots, remaining selectors, recorder and all F01-F16 application requirements.',
                             'Approved live ENiGMA decoder installation and full actual-catalog/editor/transfer acceptance.',
                             'Physical RS-232 Wi-Fi modem timing/flow control and filesystem/platform behavior.'])
    (ROOT / 'docs/validation/aspect-system-query.json').write_text(json.dumps(result, indent=2) + '\n')
    print('Recorded DOS system queries:103 slots,341 VM runs,22 ENiGMA checks,258 source-only products; all full gates open')


if __name__ == '__main__':
    main()
