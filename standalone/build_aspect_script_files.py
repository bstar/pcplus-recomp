#!/usr/bin/env python3
"""Build native script-file handlers/helpers without original inputs."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/aspect-script-files'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    fixture = ROOT / 'standalone/fixtures/aspect_script_file_native_units.json'
    proof = json.loads(fixture.read_text())
    for unit in proof['units']:
        key = 'ASPECT_SCRIPT_FILE' + ('_SERVICE' if unit['group'] == 'service' else '')
        target = OUT / (unit['name'] + '.bin')
        subprocess.run(['nasm', '-fbin', '-Ireconstruction/uart/', '-D' + key + '_FLAT',
                        '-D' + key + '_UNIT=' + str(unit['unit']), unit['source'],
                        '-o', str(target)], cwd=ROOT, check=True)
        assert target.stat().st_size == unit['bytes'] and sha(target) == unit['sha256'], unit['name']
    sources = sorted({u['source'] for u in proof['units']})
    objects = {}
    for source in sources:
        obj = OUT / (Path(source).stem + '.obj')
        subprocess.run(['nasm', '-fobj', '-Ireconstruction/uart/', source,
                        '-o', str(obj)], cwd=ROOT, check=True)
        objects[obj.name] = sha(obj)
    report = dict(passed=True, native_bytes=proof['native_bytes'], units=proof['units'],
                  objects=objects, original_inputs=[],
                  sources={str(p.relative_to(ROOT)): sha(p) for p in
                           [*[ROOT / s for s in sources], fixture, Path(__file__),
                            ROOT / 'reconstruction/uart/encodings.inc']},
                  scope=proof['scope'])
    (OUT / 'manifest.json').write_text(json.dumps(report, indent=2) + '\n')
    print('ASPECT script files:', report['native_bytes'], 'native instruction bytes PASS')


if __name__ == '__main__':
    main()
