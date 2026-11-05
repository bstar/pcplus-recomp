#!/usr/bin/env python3
"""Bind the Gateway package rebuild, DOS launchers and Enigma transfer layouts."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'lab/bbs'))
from product_inputs import sha


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('package', 'source-proof', 'splash', 'setup', 'script', 'transfers', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args()
    out = a.output.resolve()
    assert out.is_relative_to(ROOT / 'build') and not out.exists()

    def bind(path):
        path = path.resolve()
        assert path.is_relative_to(ROOT / 'build')
        return dict(path=str(path.relative_to(ROOT)), sha256=sha(path))

    def checked(path):
        r = json.loads(path.read_text())
        assert r['passed'], path
        for name, digest in r.get('sources', {}).items():
            assert sha(ROOT / name) == digest, name
        return r

    manifest_path = a.package / 'manifest.json'
    package = json.loads(manifest_path.read_text())
    files = package['files']
    assert package['dos_directory'] == 'PCPLUS' and len(files) == 10
    for name, digest in files.items():
        assert sha(a.package / 'PCPLUS' / name) == digest, name
    source = checked(a.source_proof)
    assert source['package_manifest_sha256'] == sha(manifest_path)
    assert source['source_commit'] == package['source_base_commit']
    assert source['source_count'] == len(source['sources'])
    assert source['ancestor_git_unavailable'] and source['original_inputs'] == []
    assert source['files'] == files
    assert source['rebuilt_executables'] == {n: h for n, h in files.items() if n.endswith('.EXE')}
    launchers = []
    for name, path, launcher, omitted in [('splash', a.splash, 'START', False),
                                        ('setup', a.setup, 'SETUP', False),
                                        ('script', a.script, 'START', True)]:
        r = checked(path)
        assert r['package_manifest_sha256'] == sha(manifest_path) and r['package_files'] == files
        assert r['launcher'] == launcher and r['bios_port_omitted'] == omitted
        assert (r['cpu'], r['port'], r['irq']) == ('8086', 3, 5)
        for artifact, digest in r['artifacts'].items():
            assert sha(path.parent / artifact) == digest, artifact
        assert 'private PRM/DIR/XLT unchanged' in r['checks']
        if name == 'script':
            assert r['precompiled_before_terminal']
            assert 'script writes expected result' in r['checks']
        else:
            assert 'actual magenta splash captured by independent timer' in r['checks']
        launchers.append(dict(case=name, report=bind(path), checks=r['checks']))
    matrix = checked(a.transfers)
    assert matrix['terminal_sha256'] == files['TERMINAL.EXE']
    assert matrix['transferred_payload_bytes'] == 4 * 65539
    assert {(c['mode'], c['physical_rows'], c['status_hidden']) for c in matrix['cases']} == {
        (m, rows, hidden) for m in ('upload', 'download') for rows, hidden in [(25, 0), (50, 1)]}
    for c in matrix['cases']:
        path = ROOT / c['audit_path']
        assert c['passed'] and sha(path) == c['audit_sha256']
        audit = checked(path)
        assert audit['payload_bytes'] == c['payload_bytes'] == 65539
        assert audit['payload_sha256'] == c['payload_sha256'] and audit['all256_values']
        assert audit['payload_size_lookalikes'] > 0
        assert audit['NAWS'] == [[80, c['physical_rows'] - (not c['status_hidden'])]]
        for name, digest in audit.get('captures', {}).items():
            assert sha(ROOT / name) == digest, name
    result = dict(passed=True, package=bind(manifest_path), source_proof=bind(a.source_proof),
                  source_commit=source['source_commit'], source_count=source['source_count'],
                  files=files, launchers=launchers, transfers=bind(a.transfers), cases=matrix['cases'],
                  original_inputs=[], recorder_sha256=sha(Path(__file__)),
                  scope='Exact original-free package reconstruction and DOS8086 launcher checks; four independently audited stock Enigma upload/download cases at25/50physical rows. Separate processes per transfer direction. No physical runtime, analog/SIP/DSP, every-layout/protocol or full original feature-parity claim.')
    out.mkdir(parents=True)
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print('PASS exact five-executable/ten-file package, three DOS launcher cases, four Enigma transfer cases')


if __name__ == '__main__':
    main()
