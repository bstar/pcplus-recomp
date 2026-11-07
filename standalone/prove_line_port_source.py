#!/usr/bin/env python3
"""Reproduce the component in a fresh tree containing declared public sources only."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/line-port'
DEST = OUT / 'source-proof'
SOURCES = ['standalone/build_line_port.py', 'standalone/line_port_host.asm',
           'standalone/test_line_port_dos.py', 'reconstruction/line_port/key.asm',
           'reconstruction/line_port/provenance.json', 'reconstruction/uart/encodings.inc']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    # A stale export must never silently supply an undeclared build input.
    DEST.mkdir(parents=True, exist_ok=False)
    tree = DEST / 'tree'
    for source in SOURCES:
        target = tree / source
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / source, target)
    for command in ('build_line_port.py', 'test_line_port_dos.py'):
        subprocess.run([sys.executable, str(tree / 'standalone' / command)], check=True, cwd=tree)
    for name in ('key.bin', 'LINEPORT.EXE'):
        assert (OUT / name).read_bytes() == (tree / 'build/line-port' / name).read_bytes(), name
    (DEST / 'result.json').write_text(json.dumps({
        'passed': True, 'sources': {p: sha(ROOT / p) for p in SOURCES},
        'exact_outputs': {p: sha(OUT / p) for p in ('key.bin', 'LINEPORT.EXE')},
        'dos_result': json.loads((tree / 'build/line-port/dos-results.json').read_text()),
        'scope': 'Six declared public files; no original executable, analysis tree, prior object or Git metadata. Outer pinned Nix environment supplies tools.'
    }, indent=2) + '\n')
    print('Six-file public-source export: exact flat/EXE reproduction and 40 DOS vectors passed')


if __name__ == '__main__':
    main()
