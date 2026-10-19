#!/usr/bin/env python3
"""Build recovered selected SET handlers and OMF using maintained source only."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/aspect-set'
SOURCE = ROOT / 'src/aspect/set_commands.asm'
BASELINE = ROOT / 'standalone/fixtures/aspect_set_native_units.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    baseline = json.loads(BASELINE.read_text())
    units = []
    for unit in baseline['units']:
        target = OUT / f"unit{unit['unit']}.bin"
        subprocess.run(['nasm', '-f', 'bin', '-I' + str(ROOT / 'reconstruction/uart') + '/',
                        '-DASPECT_SET_FLAT', f"-DASPECT_SET_UNIT={unit['unit']}",
                        str(SOURCE), '-o', str(target)], check=True)
        assert target.stat().st_size == unit['bytes']
        assert sha(target) == unit['sha256'], unit['unit']
        units.append(unit)
    target = OUT / 'set_commands.obj'
    subprocess.run(['nasm', '-f', 'obj', '-I' + str(ROOT / 'reconstruction/uart') + '/',
                    str(SOURCE.relative_to(ROOT)), '-o', str(target)], cwd=ROOT, check=True)
    result = dict(original_inputs=[], source_sha256=sha(SOURCE), builder_sha256=sha(Path(__file__)),
                  baseline_sha256=sha(BASELINE), object_sha256=sha(target), units=units,
                  native_bytes=sum(u['bytes'] for u in units),
                  source_dependencies={'reconstruction/uart/encodings.inc': sha(ROOT / 'reconstruction/uart/encodings.inc')})
    (OUT / 'manifest.json').write_text(json.dumps(result, indent=2) + '\n')
    print('Built', result['native_bytes'], 'selected SET bytes + OMF')


if __name__ == '__main__':
    main()
