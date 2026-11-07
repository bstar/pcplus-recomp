#!/usr/bin/env python3
"""Source-only build of the recovered Line/Port selector and diagnostic host."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/line-port'
CORE = ROOT / 'reconstruction/line_port'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    proof = json.loads((CORE / 'provenance.json').read_text())
    include = str(ROOT / 'reconstruction/uart') + '/'
    subprocess.run(['nasm', '-fbin', '-I', include, str(CORE / 'key.asm'),
                    '-o', str(OUT / 'key.bin')], check=True)
    assert (OUT / 'key.bin').stat().st_size == proof['bytes']
    assert sha(OUT / 'key.bin') == proof['sha256']
    objects = []
    for source in (CORE / 'key.asm', ROOT / 'standalone/line_port_host.asm'):
        target = OUT / (source.stem + '.obj')
        subprocess.run(['nasm', '-fobj', '-DLINE_PORT_OMF', '-I', include,
                        str(source), '-o', str(target)], check=True)
        objects.append(str(target))
    subprocess.run(['wlink', 'system', 'dos', 'option', 'quiet', 'option',
                    'map=' + str(OUT / 'lineport.map'), 'name', str(OUT / 'LINEPORT.EXE'),
                    'file', ','.join(reversed(objects))], check=True)
    sources = [CORE / 'key.asm', CORE / 'provenance.json',
               ROOT / 'reconstruction/uart/encodings.inc', Path(__file__).resolve(),
               ROOT / 'standalone/line_port_host.asm']
    (OUT / 'manifest.json').write_text(json.dumps({
        'original_inputs': [], 'exact_bytes': proof['bytes'],
        'flat_sha256': sha(OUT / 'key.bin'), 'exe_sha256': sha(OUT / 'LINEPORT.EXE'),
        'sources': {str(p.relative_to(ROOT)): sha(p) for p in sources},
        'scope': 'Recovered selector only; authored bell/quiesce recording callbacks. No popup or UART.'
    }, indent=2) + '\n')
    print('Built source-only Line/Port selector: 414 exact bytes and DOS OMF diagnostic')


if __name__ == '__main__':
    main()
