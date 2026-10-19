#!/usr/bin/env python3
"""Bind current FIND/CASE compiler, native/runtime and DOS ownership evidence."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(name):
    return hashlib.sha256((ROOT/name).read_bytes()).hexdigest()


def load(name):
    return json.loads((ROOT/name).read_text())


def main():
    parent = sha('build/terminal/TERMINAL.EXE')
    child = sha('build/aspect-runner/ASPECT.EXE')
    reports = {}

    def evidence(name, passed=True):
        data = load(name)
        if passed:
            assert data['passed'], name
        reports[name] = dict(sha256=sha(name), result=data)
        return data

    for directory, digest in (('terminal', parent), ('aspect-runner', child),
                              ('aspect-find-owner', sha('build/aspect-find-owner/OWNER.EXE'))):
        manifest = evidence(f'build/{directory}/manifest.json', False)
        assert manifest['binary_sha256'] == digest
        for source, expected in manifest['sources'].items():
            assert sha(source) == expected, source
    compiler = evidence('build/aspect-find-case-compiler/checks.json')
    assert compiler['compiler_sha256'] == sha('src/aspect/compiler.py')
    assert compiler['counts'] == dict(accepted=54, rejected=72, accepted_variants=54,
                                     rejected_variants=72, novel_emission=7)
    runtime = evidence('build/aspect-runtime/checks.json')
    assert runtime['DOS_summary'] == 'ASPECT_RUNTIME 878 cases 20586 checks 0 failures'
    assert runtime['binary_sha256'] == sha('build/aspect-runtime/EXECUTE.EXE')
    manifest = evidence('build/aspect-runtime/manifest.json', False)
    assert runtime['manifest_sha256'] == sha('build/aspect-runtime/manifest.json')
    for source, expected in manifest['sources'].items():
        assert sha(source) == expected, source
    assert len(manifest['supported_slots']) == 69 and manifest['unsupported_slot_cases'] == 146
    assert manifest['FIND_CASE_family']['integration_vectors'] == 28
    assert manifest['FIND_CASE_family']['near_failure_cases'] == 2
    owner = evidence('build/aspect-find-owner/checks.json')
    assert owner['DOS_summary'] == 'FIND_OWNER 186089 checks 0 failures 1787 operations'
    assert owner['binary_sha256'] == sha('build/aspect-find-owner/OWNER.EXE')
    assert owner['manifest_sha256'] == sha('build/aspect-find-owner/manifest.json')
    native = evidence('build/aspect-find-case/checks.json')
    assert native['cases'] == 2642 and all(u['all_instructions_visited'] for u in native['native_unit_coverage'])
    for folder, count, checks in (
        ('aspect-find-case-renderer-dos/find-integration01', 4, 152),
        ('aspect-when-renderer-dos/find-3306', 8, 315),
        ('aspect-set-status-dos/find-3306', 6, 228),
        ('aspect-set-serial-dos/find-3306', 6, None),
    ):
        result = evidence(f'build/{folder}/checks.json')
        assert result['runner_sha256'] == child and len(result['cases']) == count
        if 'terminal_sha256' in result:
            assert result['terminal_sha256'] == parent
        assert all(case['passed'] and all(case['checks'].values()) for case in result['cases'])
        if checks is not None:
            assert sum(len(c['checks']) for c in result['cases']) == checks
    client = evidence('build/aspect-render-client/checks.json')
    assert client['binary_sha256'] == child and client['inputs'] == 47
    callbacks = evidence('build/aspect-render-client-dos/checks.json')
    assert callbacks['binary_sha256'] == child and len(callbacks['cases']) == 5
    admission = evidence('build/terminal/aspect-render-parent-client-checks.json')
    assert admission['binary_sha256'] == parent and len(admission['cases']) == 22
    pacing = evidence('build/aspect-runner/txpace-linked-checks.json')
    assert pacing['binary_sha256'] == child and len(pacing['cases']) == 6
    runner = evidence('build/aspect-runner/checks.json')
    assert runner['binary_sha256'] == child and runner['DOS_summary'] == 'RUNNER 21 cases 105 checks 0 failures'
    proof = evidence('docs/validation/application-components-source-build.json')
    assert proof['output_count'] == 125
    for path, digest in (('terminal/TERMINAL.EXE', parent), ('aspect-runner/ASPECT.EXE', child)):
        output = proof['outputs'][path]
        assert output['matches_workspace'] and output['sha256'] == output['workspace_sha256'] == digest
    bbs = {}
    for name, label, cancelled in (
        ('synchronet', 'find-3306-sync', 'draft_aborted'),
        ('enigma', 'find-3306-enigma30', 'no_post_saved'),
    ):
        path = f'build/bbs-lab/script-login/{label}/checks.json'
        result = load(path)
        assert result['passed'] and all(result['checks'].values())
        assert result['terminal_sha256'] == parent and result['runner_sha256'] == child
        editor = result['editor']
        assert editor['passed'] and editor['checks'][cancelled]
        assert all(editor['checks'].values()) and all(editor['observed_key_wire'].values())
        bbs[name] = dict(report=path, sha256=sha(path), checks=result['checks'],
                         editor_checks=editor['checks'], key_wire=editor['observed_key_wire'],
                         packet_delay_ms=editor['modem_packet_delay_ms'])
    assert bbs['enigma']['packet_delay_ms'] == 30
    for leaf, digest in (('TERMINAL.EXE', parent), ('ASPECT.EXE', child)):
        assert sha('build/dos-package/'+leaf) == digest
    sources = ('src/aspect/compiler.py', 'src/aspect/find_commands.asm', 'src/aspect/case_commands.asm',
               'src/aspect/find_runtime.c', 'src/aspect/find_runtime.h', 'src/aspect/runtime_bridge.asm',
               'src/aspect/runtime.c', 'standalone/fixtures/aspect_find_case_runtime_vectors.json',
               'standalone/test_aspect_find_case_renderer_dos.py',
               'standalone/build_aspect_find_owner.py', 'standalone/check_aspect_find_owner.py',
               'standalone/record_aspect_find_case_runtime.py',
               'standalone/fixtures/aspect_find_case_compiler_vectors.json',
               'standalone/test_aspect_find_case_compiler.py',
               'docs/ASPECT_FIND_CASE_RUNTIME.md', 'docs/ASPECT_FIND_CASE_COMPILER.md')
    record = dict(schema='aspect-find-case-runtime-v1', passed=True, original_inputs=[],
                  terminal_sha256=parent, runner_sha256=child,
                  sources={name: sha(name) for name in sources}, reports=reports, bbs=bbs,
                  scope='Native FIND/SWITCH/CASE and FOUND in the actual DOS child, original-byte compiler '
                  'conformance and checked near temporary ownership. Diagnostic snapshots/injected failures, '
                  'standalone heap proof, actual UART/RGET/parent selection and BBS regressions have distinct '
                  'scope. Typed allocation abort deliberately differs from original unchecked NULL handling. '
                  '69 slots implemented;146 unsupported. Serial BREAK, full ASPECT/compiler/recorder, '
                  'other application gates and physical modem validation remain unfinished. ENiGMA uses30ms buffering.')
    target = ROOT/'docs/validation/aspect-find-case-runtime.json'
    target.write_text(json.dumps(record, indent=2)+'\n')
    print(target.relative_to(ROOT))


if __name__ == '__main__':
    main()
