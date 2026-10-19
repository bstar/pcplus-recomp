#!/usr/bin/env python3
"""Bind full source-built status drawing, adapters and actual DOS proof."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    manifest_path = ROOT / 'build/status-renderer/manifest.json'
    manifest = json.loads(manifest_path.read_text())
    for name, digest in manifest['source_dependencies'].items():
        assert sha(ROOT / name) == digest, name
    binary = ROOT / 'build/status-renderer/STATUS.EXE'
    assert sha(binary) == manifest['binary_sha256']
    check_path = ROOT / 'build/status-renderer/checks.json'
    checks = json.loads(check_path.read_text())
    assert checks['passed'] and len(checks['cases']) == 9
    assert checks['binary_sha256'] == sha(binary)
    assert checks['manifest_sha256'] == sha(manifest_path)
    assert checks['checker_sha256'] == sha(ROOT / 'standalone/check_status_renderer.py')
    proof_path = ROOT / 'docs/validation/application-components-source-build.json'
    proof = json.loads(proof_path.read_text())
    assert proof['passed'] and proof['output_count'] == 112
    for name, path in (('status-renderer/STATUS.EXE', binary),
                       ('status-helpers/STATUS.EXE', ROOT / 'build/status-helpers/STATUS.EXE')):
        output = proof['outputs'][name]
        assert output['matches_workspace'] and output['sha256'] == output['workspace_sha256'] == sha(path)
    reports = {str(path.relative_to(ROOT)): dict(sha256=sha(path), result=json.loads(path.read_text()))
               for path in (manifest_path, check_path, proof_path, ROOT / 'docs/validation/status-helpers.json')}
    files = ('src/status/status_renderer_bridge.asm', 'standalone/status_renderer_host.asm',
             'standalone/status_renderer_state.inc', 'standalone/build_status_renderer.py',
             'standalone/check_status_renderer.py', 'standalone/record_status_renderer.py',
             'reconstruction/terminal_reset/status_refresh.asm',
             'reconstruction/terminal_reset/status_fill.asm', 'docs/STATUS_RENDERER.md')
    record = dict(schema='status-renderer-v1', passed=True, original_inputs=[],
                  sources={name: sha(ROOT / name) for name in files}, reports=reports,
                  scope='Source-built full native status component across real near/far bridges. ActualDOS video/stack/ABI and typed failures checked. Carrier remains a diagnostic word; production state staging, guarded parent STATUS RPC, SET lifetimes and full application remain unfinished.')
    out = ROOT / 'docs/validation/status-renderer.json'
    out.write_text(json.dumps(record, indent=2) + '\n')
    print(out.relative_to(ROOT))


if __name__ == '__main__':
    main()
