#!/usr/bin/env python3
"""Actual startup geometry -> staged SynthModem -> loopback NAWS layout matrix.

Synthetic Hayes/Telnet peer; no installed service, BBS or physical acceptance.
"""
import argparse
import concurrent.futures
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stage', type=Path, required=True)
    p.add_argument('--terminal', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    stage, binary, out = a.stage.resolve(), a.terminal.resolve(), a.output.resolve()
    assert out.is_relative_to(ROOT / 'build')
    out.mkdir(parents=True, exist_ok=False)
    manifest = json.loads((binary.parent / 'manifest.json').read_text())
    assert manifest['experimental_display_startup'] and manifest['experimental_line_control']
    assert sha(binary) == manifest['binary_sha256']
    inputs = dict(manifest['sources'])
    for name in ['standalone/test_menu_size_layouts_dos.py', 'standalone/test_menu_size_bridge_dos.py',
                 'standalone/modem_fixtures.py', 'standalone/test_terminal.py',
                 'standalone/display_startup_geometry.asm']:
        inputs[name] = sha(ROOT / name)
    for name, digest in inputs.items():
        assert sha(ROOT / name) == digest, name

    def run(layout):
        rows, hidden = layout
        target = out / f'rows-{rows}-hidden-{hidden}'
        command = [sys.executable, str(ROOT / 'standalone/test_menu_size_bridge_dos.py'),
                   '--stage', str(stage), '--terminal', str(binary), '--output', str(target),
                   '--display-rows', str(rows), '--status-hidden', str(hidden)]
        with (out / (target.name + '.log')).open('w') as log:
            result = subprocess.run(command, cwd=ROOT, stdout=log, stderr=log, timeout=45)
        assert result.returncode == 0, target.name
        report = json.loads((target / 'result.json').read_text())
        assert report['passed'] and report['physical_rows'] == rows
        assert report['status_hidden'] == hidden and report['logical_rows'] == rows - (not hidden)
        print(target.name, 'PASS', flush=True)
        return dict(case=target.name, path=str((target / 'result.json').relative_to(ROOT)),
                    sha256=sha(target / 'result.json'), physical_rows=rows,
                    logical_rows=report['logical_rows'], status_hidden=hidden, passed=True)

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        cases = list(pool.map(run, [(rows, hidden) for rows in (25, 28, 43, 50) for hidden in (0, 1)]))
    for name, digest in inputs.items():
        assert sha(ROOT / name) == digest, name
    assert sha(binary) == manifest['binary_sha256']
    result = dict(passed=True, cases=cases, sources=inputs, terminal_sha256=sha(binary),
                  terminal_manifest_sha256=sha(binary.parent / 'manifest.json'),
                  stage_receipt=str((stage / 'result.json').relative_to(ROOT)),
                  stage_receipt_sha256=sha(stage / 'result.json'), scope=__doc__)
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    main()
