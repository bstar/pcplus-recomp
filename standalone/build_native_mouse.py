#!/usr/bin/env python3
"""Build exact mouse primitives without original executables or REA inputs."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/native-mouse'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    proof_path = ROOT / 'reconstruction/program_mouse/provenance.json'
    proof = json.loads(proof_path.read_text())
    sources = [ROOT / unit['file'] for unit in proof['units']]
    for source, unit in zip(sources, proof['units']):
        output = OUT / (source.stem + '.bin')
        subprocess.run(['nasm', '-fbin', '-I' + str(ROOT / 'reconstruction/uart') + '/',
                        str(source), '-o', str(output)], check=True)
        assert len(output.read_bytes()) == unit['bytes'] and sha(output) == unit['sha256']
    sources.append(ROOT / 'standalone/native_mouse_host.asm')
    objects = []
    for source in sources:
        output = OUT / (source.stem + '.obj')
        subprocess.run(['nasm', '-fobj', '-DPROGRAM_MOUSE_OMF',
                        '-I' + str(ROOT / 'reconstruction/uart') + '/', str(source), '-o', str(output)], check=True)
        objects.append(str(output))
    subprocess.run(['wlink', 'system', 'dos', 'option', 'quiet',
                    'option', 'map=' + str(OUT / 'mouse.map'), 'name', str(OUT / 'MOUSE.EXE'),
                    'file', ','.join(objects)], check=True)
    sources += [proof_path, Path(__file__), ROOT / 'reconstruction/uart/encodings.inc']
    report = dict(binary_sha256=sha(OUT / 'MOUSE.EXE'), exact_native_bytes=sum(u['bytes'] for u in proof['units']),
                  original_inputs=[], sources={str(p.relative_to(ROOT)): sha(p) for p in sources},
                  scope='Native mouse primitives with source-owned DOS self-check. No live terminal/PROGRAM publication or physical input claim.')
    (OUT / 'manifest.json').write_text(json.dumps(report, indent=2) + '\n')
    print('MOUSE.EXE', report['binary_sha256'], report['exact_native_bytes'], 'exact native bytes')


if __name__ == '__main__':
    main()
