#!/usr/bin/env python3
"""Record compiler, real VM/file lifetime, parent and isolated ENiGMA integration."""
import hashlib
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads((ROOT / path).read_text())


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def main():
    paths = dict(native='build/aspect-script-files/checks.json',
                 original='build/aspect-script-files/native-checks.json',
                 host='build/aspect-script-files/compiler-checks.json',
                 compiler='build/aspect-compiler-dos/checks.json',
                 runtime='build/aspect-runtime/checks.json',
                 VM='build/aspect-script-files-dos/integrated-04/checks.json',
                 parent='build/aspect-script-files-parent-dos/files-parent-01/checks.json',
                 ENiGMA='build/bbs-lab/results/enigma/owned-file-script-login-02/search-checks.json')
    reports = {name: read(path) for name, path in paths.items()}
    assert all(r['passed'] for r in reports.values())
    native_manifest = read('build/aspect-script-files/manifest.json')
    assert native_manifest['native_bytes'] == 580 and native_manifest['reused_boolean']['bytes'] == 34
    for name, digest in native_manifest['sources'].items():
        assert sha(name) == digest, name
    for name in ('native', 'original'):
        r = reports[name]
        assert r['cases'] == 6090 and r['original_comparisons'] == (6090 if name == 'original' else 0)
        assert r['checker_sha256'] == sha('standalone/check_aspect_script_files.py')
        assert r['manifest_sha256'] == sha('build/aspect-script-files/manifest.json')
    host, compiler = reports['host'], reports['compiler']
    assert (host['accepted'], host['rejected']) == (126, 119)
    assert host['compiler_sha256'] == compiler['host_compiler_sha256'] == sha('src/aspect/compiler.py')
    cases_path = 'build/aspect-compiler-dos/cases.json'
    assert compiler['case_manifest_sha256'] == sha(cases_path)
    cases = {c['source_sha256']: c for c in read(cases_path)}
    for path, digest in host['fixtures'].items():
        assert sha(path) == compiler['fixture_sources'][path] == digest
        for case in read(path)['cases']:
            actual = cases[case['source_sha256']]
            assert actual['accepted'] == case['success'], case['label']
            if case['success']:
                assert actual['asx_sha256'] == case['asx_sha256']
    validation_path = 'standalone/fixtures/aspect_script_file_validation_vectors.json'
    assert host['additional_invalid'] == 6 and host['validation_fixture_sha256'] == sha(validation_path)
    for case in read(validation_path)['cases']:
        digest = hashlib.sha256(case['source'].encode('cp437')).hexdigest()
        assert not cases[digest]['accepted']
    assert compiler['checker_sha256'] == sha('standalone/check_aspect_compiler_dos.py')
    assert compiler['case_count'] == 1480
    runner = sha('build/aspect-runner/ASPECT.EXE')
    terminal = sha('build/terminal/TERMINAL.EXE')
    compiler_binary = sha('build/aspect-compiler-dos/ASPCOMP.EXE')
    assert compiler_binary == compiler['binary_sha256']
    runtime = reports['runtime']
    assert runtime['supported_slot_count'] == 89 and runtime['unsupported_slot_cases'] == 126
    assert len(runtime['SET_family']['supported_subcommands']) == 13
    assert runtime['SET_family']['unsupported_subcommands_tested'] == 243
    assert runtime['binary_sha256'] == sha('build/aspect-runtime/EXECUTE.EXE')
    vm = reports['VM']
    assert vm['cases'] == 341 and vm['assertions'] == 4727 and vm['same_process_rounds'] == 31
    assert vm['runner_sha256'] == runner and vm['compiler_sha256'] == compiler_binary
    assert vm['source_compiler_and_host_equal'] == 13 and vm['source_cli_child_verified']
    assert vm['checker_sha256'] == sha('standalone/test_aspect_script_files_dos.py')
    vm_base = Path(paths['VM']).parent
    assert vm['harness_sha256'] == sha(vm_base / 'harness.c')
    assert vm['result_sha256'] == sha(vm_base / 'drive/RESULT.TXT')
    for name, digest in vm['native_objects'].items():
        assert sha('build/aspect-runtime/' + name + '.obj') == digest
    # The repeated-invocation harness used these exact core C objects, independently
    # linked from the same sources as the composed runtime regression.
    core = {}
    for name in ('runtime', 'script_file_runtime', 'file_io', 'script_path', 'serial_runtime',
                 'receive_runtime', 'directory_runtime', 'when_runtime', 'set_runtime', 'find_runtime'):
        digest = sha(vm_base / (name + '.o'))
        assert digest == sha('build/aspect-runtime/' + name + '.o'), name
        core[name] = digest
    for name, fact in vm['files'].items():
        assert sha(vm_base / 'drive' / name) == fact['sha256']
    parent = reports['parent']
    assert parent['terminal_sha256'] == terminal and parent['runner_sha256'] == runner
    assert parent['checker_sha256'] == sha('standalone/test_aspect_script_files_parent_dos.py')
    assert len(parent['cases']) == 3 and all(all(c['checks'].values()) for c in parent['cases'])
    for name, fact in parent['files'].items():
        assert sha(Path(paths['parent']).parent / name / fact['name']) == fact['sha256']
    enigma = reports['ENiGMA']
    assert len(enigma['checks']) == 17 and all(enigma['checks'].values())
    assert enigma['terminal_sha256'] == terminal
    assert enigma['runner_sha256'] == sha('lab/bbs/enigma_search_dos.py')
    assert enigma['script_login']['runner_sha256'] == runner
    assert enigma['script_login']['compiler_sha256'] == compiler_binary
    trace = Path(paths['ENiGMA']).parent / 'program/LOGIN.LOG'
    assert (ROOT / trace).read_bytes() == b'STARTAUTHREADY'
    assert enigma['script_login']['trace_sha256'] == sha(trace)
    package = read('build/dos-package/manifest.json')
    for name, digest in (('TERMINAL.EXE', terminal), ('ASPECT.EXE', runner), ('ASPCOMP.EXE', compiler_binary)):
        assert package['files'][name] == digest == sha('build/dos-package/' + name)
    proof_path = 'docs/validation/application-components-source-build.json'
    proof = read(proof_path)
    assert proof['passed'] and proof['output_count'] == 219
    for name in ('terminal/TERMINAL.EXE', 'aspect-runner/ASPECT.EXE', 'aspect-compiler-dos/ASPCOMP.EXE'):
        assert proof['outputs'][name]['sha256'] == sha('build/' + name)
    setting_path = 'analysis/aspect-script-files/rea-setting-01.json'
    setting = read(setting_path)['records']
    assert len(setting) == 1 and setting[0]['parameters']['procedure'] == '0x1ea14'
    evidence = {name: dict(path=path, sha256=sha(path)) for name, path in paths.items()}
    record = dict(passed=True, terminal_sha256=terminal, runner_sha256=runner, compiler_sha256=compiler_binary,
                  supported_opcodes=89, unsupported_opcodes=126, supported_SET_FETCH=13,
                  evidence=evidence, native_instruction_bytes=580, reused_boolean_bytes=34,
                  native=reports['native'], original_replay=reports['original'],
                  host_compiler=host, DOS_compiler=compiler, runtime=runtime,
                  VM=vm, core_C_objects_identical=core,
                  parent=dict(checks=[dict(case=c['case'], checks=c['checks']) for c in parent['cases']], files=parent['files']),
                  ENiGMA=dict(checks=enigma['checks'], script_login=enigma['script_login'],
                              source_modules=enigma['source_modules'], scope=enigma['scope']),
                  SET_recovery=dict(bundle_sha256=sha(setting_path), evidence_id=setting[0]['evidence_id']),
                  source_build_proof=dict(path=proof_path, sha256=sha(proof_path), outputs=219),
                  package_manifest_sha256=sha('build/dos-package/manifest.json'),
                  recorder_sha256=sha(Path(__file__).relative_to(ROOT)), live_server_modified=False,
                  physical_modem_validated=False, whole_application_gates_closed=[],
                  retained_fixture_failure='integrated-01 counted a missing chained ASX as an extra failed data-file FOPEN; all31 CHFAIL expectations failed, while the actual open/close counts were1/1. Corrected fixture passes without product changes.',
                  remaining=['Original interactive returning-warning/unchecked closed-slot policy and broader CRT equivalence.',
                             'Remaining ASPECT commands/recorder and complete application gates.',
                             'Approved live ENiGMA decoder installation, actual catalog and physical modem validation.'])
    target = ROOT / 'docs/validation/aspect-script-file-runtime.json'
    target.write_text(json.dumps(record, indent=2) + '\n')
    print('Recorded file VM integration:89 slots,245 compiler oracle cases,341 VM/3parent/17ENiGMA checks; all gates open')


if __name__ == '__main__':
    main()
