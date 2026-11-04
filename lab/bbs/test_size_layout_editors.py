#!/usr/bin/env python3
"""Authenticated owned BBS editor matrix with actual startup-size handoff.

Paced DOS8086/synthetic Hayes/staged proxy; no live service or physical acceptance.
"""
import argparse
import concurrent.futures
import json
import subprocess
import sys
from pathlib import Path

from product_inputs import ROOT, select_product, sha


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runtime', type=Path, required=True)
    p.add_argument('--terminal', type=Path, required=True)
    p.add_argument('--runner', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--layout', action='append', choices=[f'{r}-{h}' for r in (25,28,43,50) for h in (0,1)])
    a = p.parse_args()
    out, runtime = a.output.resolve(), a.runtime.resolve()
    assert out.is_relative_to(ROOT / 'build') and runtime.is_relative_to(ROOT / 'build')
    out.mkdir(parents=True, exist_ok=False)
    binary, sources = select_product(a.terminal, 'TERMINAL.EXE')
    child, child_sources = select_product(a.runner, 'ASPECT.EXE')
    sources += child_sources
    names = ['lab/bbs/test_size_layout_editors.py', 'lab/bbs/test_synthmodem_proxy_dos.py',
             'lab/bbs/test_synchronet_screen_reference_dos.py', 'lab/bbs/test_dos.py',
             'lab/bbs/editor_dos_probe.py', 'lab/bbs/modem.py', 'lab/bbs/audit_size_probe_screen.py',
             'lab/bbs/audit_screen_reference.py', 'lab/bbs/check_editor_dos.py',
             'lab/bbs/terminal_geometry.py', 'lab/bbs/synthmodem_proxy_serial.js',
             'standalone/test_ansi_reference_dos.py', 'standalone/display_startup_geometry.asm',
             'lab/bbs/audio_synchronet_editor_keys.asm', 'lab/bbs/editor-recipes.json']
    sources += [ROOT / n for n in names]
    frozen = {str(n.relative_to(ROOT)): sha(n) for n in sources}
    runtime_hashes = {str(n.relative_to(runtime)): sha(n) for n in runtime.rglob('*') if n.is_file()}
    layouts = a.layout or [f'{r}-{h}' for r in (25,28,43,50) for h in (0,1)]
    assert len(set(layouts)) == len(layouts)

    def run_peer(peer):
        results = []
        for layout in layouts:
            rows, hidden = map(int, layout.split('-'))
            label = out.name + '-' + peer + '-' + layout
            producer = ROOT / 'lab/bbs' / ('test_synthmodem_proxy_dos.py' if peer == 'enigma' else 'test_synchronet_screen_reference_dos.py')
            command = [sys.executable, str(producer), '--runtime', str(runtime), '--terminal', str(binary),
                       '--label', label, '--size-probe', '--display-rows', str(rows), '--status-hidden', str(hidden)]
            if peer == 'enigma':
                command += ['--byte-delay-ms', '20', '--framing-ms', '250', '--screen-reference']
            else:
                command += ['--runner', str(child)]
            with (out / (label + '.log')).open('w') as log:
                result = subprocess.run(command, cwd=ROOT, stdout=log, stderr=log, timeout=195)
            assert result.returncode == 0, ('producer', label)
            capture = ROOT / 'build/bbs-lab/results' / peer / label
            bridge = ROOT / 'build/bbs-lab' / (label + '-proxy')
            with (out / (label + '-audit.log')).open('w') as log:
                result = subprocess.run([sys.executable, str(ROOT / 'lab/bbs/audit_size_probe_screen.py'),
                                         '--output', str(capture), '--bridge', str(bridge)],
                                        cwd=ROOT, stdout=log, stderr=log, timeout=30)
            assert result.returncode == 0, ('independent audit', label)
            path = capture / 'size-probe-screen-audit.json'
            audit = json.loads(path.read_text())
            assert audit['passed'] and audit['different_cells'] == 0
            logical = rows - (not hidden)
            assert audit['NAWS'] == [[80, logical]] and audit['matched_cells'] == logical * 80
            record = dict(peer=peer, physical_rows=rows, status_hidden=hidden, logical_rows=logical,
                          matched_cells=audit['matched_cells'], delivered_bytes=audit['delivered_bytes'],
                          actual_CPR=audit['actual_CPR'], capture=str(capture.relative_to(ROOT)),
                          bridge=str(bridge.relative_to(ROOT)), audit_path=str(path.relative_to(ROOT)),
                          audit_sha256=sha(path), passed=True)
            results.append(record)
            (out / (label + '-accepted.json')).write_text(json.dumps(record, indent=2) + '\n')
            print(label, 'PASS', logical * 80, 'cells', flush=True)
        return results

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        groups = list(pool.map(run_peer, ['enigma', 'synchronet']))
    for n, digest in frozen.items():
        assert sha(ROOT / n) == digest, n
    assert runtime_hashes == {str(n.relative_to(runtime)): sha(n) for n in runtime.rglob('*') if n.is_file()}
    result = dict(passed=True, cases=[r for group in groups for r in group], sources=frozen,
                  runtime=str(runtime.relative_to(ROOT)), runtime_hashes=runtime_hashes,
                  terminal_sha256=sha(binary), interpreter_sha256=sha(child), scope=__doc__)
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    main()
