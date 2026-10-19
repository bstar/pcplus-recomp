#!/usr/bin/env python3
"""Build native environment wrappers/CRT and explicit borrowed-pointer control."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/aspect-environment'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    fixture = ROOT / 'standalone/fixtures/aspect_environment_native_units.json'
    proof = json.loads(fixture.read_text())
    source = ROOT / 'src/aspect/environment.asm'
    units, reused, objects = [], [], {}
    include = '-I' + str(ROOT / 'reconstruction/uart') + '/'
    for unit in proof['units']:
        path = OUT / (unit['name'] + '.bin')
        subprocess.run(['nasm', '-fbin', include, '-DASPECT_ENVIRONMENT_FLAT', '-DASPECT_ENVIRONMENT_UNIT=' + str(unit['unit']), str(source), '-o', str(path)], check=True)
        assert path.stat().st_size == unit['bytes'] and sha(path) == unit['sha256'], unit
        units.append(dict(unit, output=str(path.relative_to(ROOT))))
    for unit in proof['reused']:
        path = OUT / ('crt-' + unit['name'] + '.bin')
        subprocess.run(['nasm', '-fbin', include, str(ROOT / unit['source']), '-o', str(path)], check=True)
        assert path.stat().st_size == unit['bytes'] and sha(path) == unit['sha256'], unit
        reused.append(dict(unit, output=str(path.relative_to(ROOT))))
    for name, flags in [('environment', []), ('environment_unowned', ['-DASPECT_ENVIRONMENT_UNOWNED'])]:
        path = OUT / (name + '.obj')
        subprocess.run(['nasm', '-fobj', include, *flags, str(source.relative_to(ROOT)), '-o', str(path)], cwd=ROOT, check=True)
        objects[str(path.relative_to(ROOT))] = sha(path)
    sources = [source, fixture, Path(__file__), ROOT / 'reconstruction/uart/encodings.inc', *[ROOT / u['source'] for u in reused]]
    report = dict(passed=True, original_inputs=[], units=units, reused=reused,
                  native_bytes=sum(u['bytes'] for u in units), reused_bytes=sum(u['bytes'] for u in reused),
                  objects=objects, sources={str(p.relative_to(ROOT)): sha(p) for p in sources})
    (OUT / 'manifest.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Environment:', report['native_bytes'], 'exact native bytes +', report['reused_bytes'], 'reused bytes PASS')


if __name__ == '__main__':
    main()
