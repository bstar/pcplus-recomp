#!/usr/bin/env python3
"""Assemble recovered XLT units from source, without original inputs."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/translation'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    proof = json.loads((ROOT / 'reconstruction/translation/provenance.json').read_text())
    include = ROOT / 'reconstruction/uart/encodings.inc'
    sources = {str(include.relative_to(ROOT)): hashlib.sha256(include.read_bytes()).hexdigest()}
    for unit in proof['units']:
        source = ROOT / unit['file']
        stem = source.stem
        for kind in ('bin', 'obj'):
            command = ['nasm', '-f', kind, '-I', str(ROOT / 'reconstruction/uart') + '/']
            if kind == 'obj':
                command.append('-DTRANSLATION_OMF')
            # OMF THEADR records the input spelling; keep it checkout-relative.
            subprocess.run(command + [str(source.relative_to(ROOT)), '-o',
                           str((OUT / (stem + '.' + kind)).relative_to(ROOT))], cwd=ROOT, check=True)
        blob = (OUT / (stem + '.bin')).read_bytes()
        assert len(blob) == unit['bytes']
        assert hashlib.sha256(blob).hexdigest() == unit['sha256']
        sources[unit['file']] = hashlib.sha256(source.read_bytes()).hexdigest()
    (OUT / 'manifest.json').write_text(json.dumps({
        'exact_bytes': sum(u['bytes'] for u in proof['units']),
        'sources': sources,
        'original_inputs': [],
        'scope': 'Flat exact units and relocatable OMF objects; no runnable DOS application.',
    }, indent=2) + '\n')
    print('Built 176 exact XLT bytes and OMF objects from source')


if __name__ == '__main__':
    main()
