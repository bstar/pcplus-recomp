#!/usr/bin/env python3
"""Build the source-only DOS serial diagnostic; no baseline artifact is read."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
output = ROOT / 'build/standalone'
output.mkdir(parents=True, exist_ok=True)
sources = [('uart', ROOT / 'reconstruction/uart/core.asm'),
           ('data', ROOT / 'standalone/data.asm'),
           ('services', ROOT / 'standalone/services.asm'),
           ('serial', ROOT / 'standalone/serial.asm')]
for name, source in sources:
    command = ['nasm', '-f', 'obj', '-I', str(ROOT / 'reconstruction/uart') + '/',
               '-o', str(output / (name + '.obj'))]
    if name == 'uart':
        command += ['-DUART_OMF']
    subprocess.run(command + [str(source)], cwd=ROOT, check=True)
subprocess.run(['wlink', 'system', 'dos', 'option', 'quiet', 'option',
                'map=' + str(output / 'serial.map'), 'name', str(output / 'SERIAL.EXE'),
                'file', ','.join(str(output / (name + '.obj')) for name, _ in sources)],
               cwd=ROOT, check=True)
inputs = [source for _, source in sources] + list((ROOT / 'reconstruction/uart').glob('*.inc'))
manifest = {
    'kind': 'source-only-dos-uart-diagnostic',
    'binary': 'build/standalone/SERIAL.EXE',
    'binary_sha256': hashlib.sha256((output / 'SERIAL.EXE').read_bytes()).hexdigest(),
    'sources': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
    'limitations': ['Serial module diagnostic; not the complete PCPlus application.',
                    'Host services implement DOS seconds; presentation callbacks intentionally do nothing.',
                    'COM1 IRQ4, 38400 8N1; original serial behavior retained.'],
}
(output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print('Built', manifest['binary'], manifest['binary_sha256'], flush=True)
