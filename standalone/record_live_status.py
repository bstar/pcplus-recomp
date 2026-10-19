#!/usr/bin/env python3
"""Bind the current live STATUS products to scoped source/CPU/DOS evidence."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(name):
    return hashlib.sha256((ROOT / name).read_bytes()).hexdigest()


def load(name):
    return json.loads((ROOT / name).read_text())


def main():
    parent = sha('build/terminal/TERMINAL.EXE')
    child = sha('build/aspect-runner/ASPECT.EXE')
    manifests = {}
    for directory, digest in (('terminal', parent), ('aspect-runner', child)):
        name = f'build/{directory}/manifest.json'
        manifest = load(name)
        assert manifest['binary_sha256'] == digest
        for source, expected in manifest['sources'].items():
            assert sha(source) == expected, source
        manifests[name] = dict(sha256=sha(name), result=manifest)
    reports = {}

    def evidence(name):
        result = load(name)
        assert result['passed'], name
        reports[name] = dict(sha256=sha(name), result=result)
        return result

    linked = evidence('build/terminal/status-live-checks.json')
    assert linked['binary_sha256'] == parent and len(linked['cases']) == 85
    assert linked['checker_sha256'] == sha('standalone/check_status_live.py')
    client = evidence('build/aspect-render-client/checks.json')
    assert client['binary_sha256'] == child and client['inputs'] == 47
    assert len(client['cases']) == 16
    admission = evidence('build/terminal/aspect-render-parent-client-checks.json')
    assert admission['binary_sha256'] == parent and len(admission['cases']) == 22
    callbacks = evidence('build/aspect-render-client-dos/checks.json')
    assert callbacks['binary_sha256'] == child and len(callbacks['cases']) == 5
    for label, count, checks in (
        ('aspect-status-dos/final-03-phase', 4, 152),
        ('aspect-when-renderer-dos/status-e9c8', 8, 315),
    ):
        result = evidence(f'build/{label}/checks.json')
        assert result['terminal_sha256'] == parent and result['runner_sha256'] == child
        assert len(result['cases']) == count
        assert sum(len(case['checks']) for case in result['cases']) == checks
        assert all(case['passed'] and all(case['checks'].values()) for case in result['cases'])
    runtime = evidence('build/aspect-runtime/checks.json')
    assert runtime['binary_sha256'] == sha('build/aspect-runtime/EXECUTE.EXE')
    assert runtime['DOS_summary'] == 'ASPECT_RUNTIME 825 cases 18298 checks 0 failures'
    proof = evidence('docs/validation/application-components-source-build.json')
    assert proof['output_count'] == 112
    for name, digest in (('terminal/TERMINAL.EXE', parent), ('aspect-runner/ASPECT.EXE', child)):
        output = proof['outputs'][name]
        assert output['matches_workspace'] and output['sha256'] == output['workspace_sha256'] == digest
    bbs = {}
    for name, label, check in (
        ('synchronet', 'status-e9c8-sync', 'draft_aborted'),
        ('enigma', 'status-e9c8-enigma30', 'no_post_saved'),
    ):
        path = f'build/bbs-lab/script-login/{label}/checks.json'
        result = load(path)
        assert result['passed'] and all(result['checks'].values())
        assert result['terminal_sha256'] == parent and result['runner_sha256'] == child
        editor = result['editor']
        assert editor['passed'] and editor['checks'][check]
        assert all(editor['checks'].values()) and all(editor['observed_key_wire'].values())
        bbs[name] = dict(report=path, sha256=sha(path), checks=result['checks'],
                         editor_checks=editor['checks'], observed_key_wire=editor['observed_key_wire'],
                         packet_delay_ms=editor['modem_packet_delay_ms'])
    assert bbs['enigma']['packet_delay_ms'] == 30
    for name, digest in (('TERMINAL.EXE', parent), ('ASPECT.EXE', child)):
        assert sha('build/dos-package/' + name) == digest
    sources = (
        'src/terminal/status_live.asm', 'src/status/status_state.inc',
        'src/terminal/aspect_renderer.asm', 'src/aspect/resident_render.c',
        'src/aspect/resident_render.h', 'src/aspect/when_runtime.c',
        'src/aspect/runtime_bridge.asm', 'standalone/check_status_live.py',
        'standalone/test_aspect_status_dos.py', 'standalone/record_live_status.py',
        'standalone/prove_source_build.py', 'docs/LIVE_STATUS.md', 'docs/ASPECT_STATUS_DOS.md',
    )
    record = dict(schema='live-status-v1', passed=True, original_inputs=[],
                  terminal_sha256=parent, runner_sha256=child,
                  sources={name: sha(name) for name in sources},
                  manifests=manifests, reports=reports, bbs=bbs,
                  scope='Actual normal-row parent STATUS through capability2 during live UART lease. '
                  'Linked staging/API boundaries and emulated DOS/BBS proofs are distinct; report-time '
                  'map identities are preserved, not asserted equal to later deterministic-binary rebuild maps. '
                  'Only SET WHENCASE is production-enabled. Alternate live key labels, other SET settings, '
                  'full application and physical modem validation remain unfinished. ENiGMA immediate '
                  'forwarding Home/Insert failure remains unresolved; explicit30ms buffering is tested.')
    target = ROOT / 'docs/validation/live-status.json'
    target.write_text(json.dumps(record, indent=2) + '\n')
    print(target.relative_to(ROOT))


if __name__ == '__main__':
    main()
