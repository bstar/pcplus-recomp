#!/usr/bin/env python3
"""Build exact external command frontends without executing a target."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/aspect-external'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    fixture = ROOT / 'standalone/fixtures/aspect_external_native_units.json'
    proof = json.loads(fixture.read_text())
    source = ROOT / 'src/aspect/external_commands.asm'
    units, reused, objects = [], [], {}
    include = '-I' + str(ROOT / 'reconstruction/uart') + '/'
    for unit in proof['units']:
        path = OUT / (unit['name'] + '.bin')
        subprocess.run(['nasm', '-fbin', include, '-DASPECT_EXTERNAL_FLAT', '-DASPECT_EXTERNAL_UNIT=' + str(unit['unit']), str(source), '-o', str(path)], check=True)
        assert path.stat().st_size == unit['bytes'] and sha(path) == unit['sha256'], unit
        units.append(dict(unit, output=str(path.relative_to(ROOT))))
    for unit in proof['reused']:
        path = OUT / ('crt-' + unit['name'] + '.bin')
        subprocess.run(['nasm', '-fbin', include, str(ROOT / unit['source']), '-o', str(path)], check=True)
        assert path.stat().st_size == unit['bytes'] and sha(path) == unit['sha256'], unit
        reused.append(dict(unit, output=str(path.relative_to(ROOT))))
    for name, flags in [('external_commands', [])]:
        path = OUT / (name + '.obj')
        subprocess.run(['nasm', '-fobj', include, *flags, str(source.relative_to(ROOT)), '-o', str(path)], cwd=ROOT, check=True)
        objects[str(path.relative_to(ROOT))] = sha(path)
    linked = [str(OUT / 'external_commands.obj')]
    for name, path, define in [('boundary', 'standalone/aspect_external_boundary.asm', None),
                               ('strcpy', 'reconstruction/program_exec/strcpy.asm', 'PROGRAM_EXEC_OMF'),
                               ('strchr', 'reconstruction/program_exec/strchr.asm', 'PROGRAM_EXEC_OMF')]:
        target = OUT / (name + '.obj')
        subprocess.run(['nasm', '-fobj', include, *(['-D' + define] if define else []), path, '-o', str(target)], cwd=ROOT, check=True)
        linked.append(str(target))
    subprocess.run(['wcl', '-q', '-bt=dos', '-0', '-ms', '-ecc', '-s', '-w4', '-we', '-k4096',
                    '-i=' + str(ROOT / 'src/aspect'), '-fm=EXTERNAL.map', '-fe=EXTERNAL.EXE',
                    str(ROOT / 'standalone/aspect_external_diagnostic.c'), *linked], cwd=OUT, check=True)
    sources = [source, fixture, Path(__file__), ROOT / 'reconstruction/uart/encodings.inc', *[ROOT / u['source'] for u in reused]]
    sources += [ROOT / 'standalone/aspect_external_boundary.asm', ROOT / 'standalone/aspect_external_diagnostic.c', ROOT / 'src/aspect/external_runtime.h']
    report = dict(passed=True, original_inputs=[], units=units, reused=reused,
                  native_bytes=sum(u['bytes'] for u in units), reused_bytes=sum(u['bytes'] for u in reused),
                  diagnostic_sha256=sha(OUT / 'EXTERNAL.EXE'),
                  objects=objects, sources={str(p.relative_to(ROOT)): sha(p) for p in sources})
    (OUT / 'manifest.json').write_text(json.dumps(report, indent=2) + '\n')
    print('External frontends:', report['native_bytes'], 'exact native bytes +', report['reused_bytes'], 'reused bytes PASS')


if __name__ == '__main__':
    main()
