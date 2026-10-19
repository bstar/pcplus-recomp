#!/usr/bin/env python3
"""Bind native SET, calibrated TXPACE and scoped current DOS/BBS evidence."""
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

    for directory, digest in (('terminal', parent), ('aspect-runner', child)):
        manifest = evidence(f'build/{directory}/manifest.json', False)
        assert manifest['binary_sha256'] == digest
        for source, expected in manifest['sources'].items():
            assert sha(source) == expected, source
    runtime = evidence('build/aspect-runtime/checks.json')
    assert runtime['DOS_summary'] == 'ASPECT_RUNTIME 853 cases 19000 checks 0 failures'
    assert runtime['binary_sha256'] == sha('build/aspect-runtime/EXECUTE.EXE')
    runtime_manifest = evidence('build/aspect-runtime/manifest.json', False)
    assert runtime['manifest_sha256'] == sha('build/aspect-runtime/manifest.json')
    for source, expected in runtime_manifest['sources'].items():
        assert sha(source) == expected, source
    settings = runtime_manifest['SET_family']
    assert len(settings['supported_subcommands']) == 11
    assert settings['unsupported_subcommands_tested'] == 245
    assert settings['integration_vectors'] == 38
    fixture = load('standalone/fixtures/aspect_set_runtime_vectors.json')
    assert len(fixture['vectors']) == 38
    txpace = evidence('build/aspect-txpace/checks.json')
    assert len(txpace['cpu']) == 6 and len(txpace['service_model']) == 15
    assert len(txpace['actual_dos']) == 2
    assert txpace['manifest_sha256'] == sha('build/aspect-txpace/manifest.json')
    txpace_manifest = evidence('build/aspect-txpace/manifest.json', False)
    for source, expected in txpace_manifest['sources'].items():
        assert sha(source) == expected, source
    linked = evidence('build/aspect-runner/txpace-linked-checks.json')
    assert linked['binary_sha256'] == child and len(linked['cases']) == 6
    consumers = evidence('build/aspect-find-case/checks.json')
    assert consumers['cases'] == 2642 and all(unit['all_instructions_visited'] for unit in consumers['native_unit_coverage'])
    assert consumers['manifest_sha256'] == sha('build/aspect-find-case/manifest.json')
    consumer_manifest = evidence('build/aspect-find-case/manifest.json', False)
    assert consumer_manifest['native_bytes'] == 401
    for source, expected in consumer_manifest['sources'].items():
        assert sha(source) == expected, source
    for folder, count, checks in (
        ('aspect-set-status-dos/set-a1b4', 6, 228),
        ('aspect-set-serial-dos/set-a1b4', 6, None),
        ('aspect-when-renderer-dos/set-a1b4', 8, 315),
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
    runner = evidence('build/aspect-runner/checks.json')
    assert runner['binary_sha256'] == child and runner['DOS_summary'] == 'RUNNER 21 cases 105 checks 0 failures'
    proof = evidence('docs/validation/application-components-source-build.json')
    assert proof['output_count'] == 124
    for path, digest in (('terminal/TERMINAL.EXE', parent), ('aspect-runner/ASPECT.EXE', child)):
        output = proof['outputs'][path]
        assert output['matches_workspace'] and output['sha256'] == output['workspace_sha256'] == digest
    bbs = {}
    for name, label, cancelled in (
        ('synchronet', 'set-a1b4-sync', 'draft_aborted'),
        ('enigma', 'set-a1b4-enigma30', 'no_post_saved'),
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
    sources = ('src/aspect/set_commands.asm', 'src/aspect/set_runtime.c', 'src/aspect/set_runtime.h',
               'src/aspect/runtime_bridge.asm', 'src/aspect/runtime.c', 'src/aspect/runner.c',
               'src/aspect/serial_runtime.c', 'src/aspect/serial_runtime.h',
               'src/aspect/txpace.c', 'src/aspect/txpace.h', 'src/aspect/txpace.asm',
               'standalone/fixtures/aspect_set_runtime_vectors.json',
               'standalone/test_aspect_set_serial_dos.py', 'standalone/test_aspect_set_status_dos.py',
               'standalone/check_aspect_txpace_linked.py', 'standalone/record_aspect_set_runtime.py',
               'docs/ASPECT_SET_RUNTIME.md', 'docs/ASPECT_TXPACE.md')
    record = dict(schema='aspect-set-runtime-v1', passed=True, original_inputs=[],
                  terminal_sha256=parent, runner_sha256=child,
                  sources={name: sha(name) for name in sources}, reports=reports, bbs=bbs,
                  retained_regressions=[dict(path='build/aspect-txpace-history/alignment-headroom-677a',
                    reason='Linked checker reproduced queue growth to2049 during post-admission alignment, '
                           'followed by unsafe successful measurement. ALIGN now rechecks headroom before busyloop.')],
                  scope='Eleven native SET setters and maintained IRQ-live calibrated TXPACE in the actual DOS child. '
                  'Source/CPU models, diagnostic snapshots, actual DOS UART/status and BBS workflows have separate scope. '
                  'FIND/CASE consumers, shared-session adoption, GET grammar and full application remain unfinished. '
                  'ENiGMA still uses explicit30ms buffering; immediate-forwarding and physical modem validation remain open.')
    target = ROOT/'docs/validation/aspect-set-runtime.json'
    target.write_text(json.dumps(record, indent=2)+'\n')
    print(target.relative_to(ROOT))


if __name__ == '__main__':
    main()
