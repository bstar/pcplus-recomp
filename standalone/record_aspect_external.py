#!/usr/bin/env python3
"""Record exact external frontends/compiler separately from runtime admission."""
import json
from pathlib import Path
import re
from build_aspect_external import ROOT, sha


def read(path):
    return json.loads((ROOT / path).read_text())


def main():
    paths = dict(native='build/aspect-external/checks.json',
                 original='build/aspect-external/native-checks.json',
                 host='build/aspect-external/compiler-checks.json',
                 compiler='build/aspect-compiler-dos/checks.json', runtime='build/aspect-runtime/checks.json',
                 DOS='build/aspect-external-dos/integrated-01/checks.json',
                 ENiGMA='build/bbs-lab/results/enigma/external-compiler-regression-01/search-checks.json')
    reports = {name: read(path) for name, path in paths.items()}
    assert all(r['passed'] for r in reports.values())
    manifest_path = 'build/aspect-external/manifest.json'
    manifest = read(manifest_path)
    assert (manifest['native_bytes'], manifest['reused_bytes']) == (192, 92)
    for path, digest in manifest['sources'].items():
        assert sha(ROOT / path) == digest
    assert manifest['diagnostic_sha256'] == sha(ROOT / 'build/aspect-external/EXTERNAL.EXE')
    for name in ('native', 'original'):
        r = reports[name]
        assert r['cases'] == 1514 and r['original_comparisons'] == (1514 if name == 'original' else 0)
        assert r['manifest_sha256'] == sha(ROOT / manifest_path)
        assert r['checker_sha256'] == sha(ROOT / 'standalone/check_aspect_external.py')
    host, compiler = reports['host'], reports['compiler']
    fixture = 'standalone/fixtures/aspect_external_compiler_vectors.json'
    assert (host['accepted'], host['rejected']) == (29, 41)
    assert host['fixture_sha256'] == compiler['fixture_sources'][fixture] == sha(ROOT / fixture)
    assert host['compiler_sha256'] == compiler['host_compiler_sha256'] == sha(ROOT / 'src/aspect/compiler.py')
    assert (compiler['case_count'], compiler['accepted'], compiler['rejected']) == (2003, 1037, 966)
    case_path = 'build/aspect-compiler-dos/cases.json'
    assert compiler['case_manifest_sha256'] == sha(ROOT / case_path)
    cases = {c['source_sha256']: c for c in read(case_path)}
    for case in read(fixture)['cases']:
        actual = cases[case['source_sha256']]
        assert actual['accepted'] == case['success']
        if case['success']:
            assert actual['asx_sha256'] == case['asx_sha256']
    terminal = sha(ROOT / 'build/terminal/TERMINAL.EXE')
    runner = sha(ROOT / 'build/aspect-runner/ASPECT.EXE')
    compiler_binary = sha(ROOT / 'build/aspect-compiler-dos/ASPCOMP.EXE')
    prior = read('docs/validation/aspect-environment.json')
    assert terminal == prior['terminal_sha256'] and runner == prior['runner_sha256']
    assert compiler['binary_sha256'] == compiler_binary
    runtime = reports['runtime']
    assert runtime['supported_slot_count'] == 105 and runtime['unsupported_slot_cases'] == 110
    assert runtime['DOS_summary'] == 'ASPECT_RUNTIME 1111 cases 26686 checks 0 failures'
    assert runtime['binary_sha256'] == sha(ROOT / 'build/aspect-runtime/EXECUTE.EXE')
    runtime_manifest = read('build/aspect-runtime/manifest.json')
    assert runtime['manifest_sha256'] == sha(ROOT / 'build/aspect-runtime/manifest.json')
    assert runtime_manifest['sources']['src/aspect/compiler.py'] == sha(ROOT / 'src/aspect/compiler.py')
    published = {int(op, 16) for op in re.findall(r'%(?:el)?if op=(0x[0-9a-f]+)', (ROOT / 'src/aspect/runtime_bridge.asm').read_text())}
    assert len(published) == 105 and not published.intersection({0x28, 0x9b, 0xa3})
    dos = reports['DOS']
    assert (dos['frontend_DOS_cases'], dos['frontend_DOS_assertions'], dos['compiler_cases'], dos['accepted'], dos['rejected']) == (53, 436, 70, 29, 41)
    assert len(dos['unsupported_product_cases']) == 29 and not dos['runtime_enabled']
    assert dos['runner_sha256'] == runner and dos['compiler_sha256'] == compiler_binary
    assert dos['fixture_sha256'] == sha(ROOT / fixture)
    assert dos['checker_sha256'] == sha(ROOT / 'standalone/test_aspect_external_dos.py')
    folder = ROOT / Path(paths['DOS']).parent
    assert dos['harness_sha256'] == sha(folder / 'harness.c')
    for field, leaf in [('diagnostic_result_sha256', 'BOUNDARY.TXT'), ('rejection_harness_sha256', 'REJECT.EXE'),
                        ('rejection_result_sha256', 'REJECT.TXT'), ('sentinel_sha256', 'CHILD.COM')]:
        assert dos[field] == sha(folder / 'drive' / leaf)
    assert not (folder / 'drive/UNSAFE.OUT').exists()
    for case in dos['unsupported_product_cases']:
        assert case['opcode'] in {0x28, 0x9b, 0xa3}
        assert case['log_sha256'] == sha(folder / 'drive' / (case['case'] + '.LOG'))
    enigma = reports['ENiGMA']
    assert len(enigma['checks']) == 23 and all(enigma['checks'].values())
    assert enigma['terminal_sha256'] == terminal
    assert enigma['script_login']['runner_sha256'] == runner and enigma['script_login']['compiler_sha256'] == compiler_binary
    assert enigma['runner_sha256'] == sha(ROOT / 'lab/bbs/enigma_search_dos.py')
    proof_path = 'docs/validation/application-components-source-build.json'
    proof = read(proof_path)
    assert proof['passed'] and proof['output_count'] == 278
    for name in ('terminal/TERMINAL.EXE', 'aspect-runner/ASPECT.EXE', 'aspect-compiler-dos/ASPCOMP.EXE', 'aspect-runtime/EXECUTE.EXE', 'aspect-external/EXTERNAL.EXE'):
        assert proof['outputs'][name]['sha256'] == sha(ROOT / 'build' / name)
    package = read('build/dos-package/manifest.json')
    for name, digest in [('TERMINAL.EXE', terminal), ('ASPECT.EXE', runner), ('ASPCOMP.EXE', compiler_binary)]:
        assert package['files'][name] == digest == sha(ROOT / 'build/dos-package' / name)
    bundles = ['analysis/aspect-external-18-01.rea.json', 'analysis/aspect-external-shell-01.rea.json']
    assert [len(read(p)['records']) for p in bundles] == [3, 1]
    result = dict(passed=True, runtime_enabled=False, terminal_sha256=terminal, runner_sha256=runner,
                  compiler_sha256=compiler_binary, native_bytes=192, reused_bytes=92,
                  component_cases=1514, original_comparisons=1514,
                  supported_opcodes=105, unsupported_opcodes=110,
                  evidence={name: dict(path=path, sha256=sha(ROOT / path)) for name, path in paths.items()},
                  original_compiler=dict(cases=70, accepted=29, rejected=41),
                  DOS_compiler=dict(cases=2003, accepted=1037, rejected=966),
                  OMF_DOS_boundary=dict(cases=53, assertions=436, executor_is_model=True),
                  product_rejection=dict(cases=29, error=3, actual_opcodes=[0x28, 0x9b, 0xa3], side_effect_marker_absent=True),
                  runtime_summary=runtime['DOS_summary'], ENiGMA_regression=enigma['checks'],
                  REA=[dict(bundle_sha256=sha(ROOT / p), evidence_ids=[r['evidence_id'] for r in read(p)['records']]) for p in bundles],
                  source_build_proof=dict(path=proof_path, sha256=sha(ROOT / proof_path), outputs=278),
                  package_manifest_sha256=sha(ROOT / 'build/dos-package/manifest.json'), recorder_sha256=sha(Path(__file__)),
                  current_policy='Compilers emit exact native records; external runtime handlers remain unpublished. Native/OMF executor boundaries are models. No generic spawn substitute for pending PROGRAM controller.',
                  live_server_modified=False, physical_modem_validated=False, whole_application_gates_closed=[],
                  remaining=['Implement the full external application executor/controller checklist in docs/ASPECT_EXTERNAL.md before publishing DOS/RUN/SHELL.',
                             '110 runtime opcode slots, remaining selectors/recorder and complete F01-F16 application requirements.',
                             'Approved live ENiGMA deployment and full catalog/editor/transfers, physical RS-232 Wi-Fi modem validation.'])
    (ROOT / 'docs/validation/aspect-external.json').write_text(json.dumps(result, indent=2) + '\n')
    print('Recorded external frontends/compiler:1514 paired cases,53 DOS boundaries,29 explicit rejections; runtime remains105/110')


if __name__ == '__main__':
    main()
