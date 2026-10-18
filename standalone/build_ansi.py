#!/usr/bin/env python3
"""Link the recovered parameter reader into a source-only DOS parser diagnostic."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
output = ROOT / 'build/ansi'
output.mkdir(parents=True, exist_ok=True)
sources = [('transition', ROOT / 'reconstruction/ansi/transition.asm'),
           ('parameters', ROOT / 'reconstruction/ansi/parameters.asm'),
           ('decimal', ROOT / 'src/ansi/decimal.asm'),
           ('host', ROOT / 'standalone/ansi_host.asm')]
for name, source in sources:
    command = ['nasm', '-f', 'obj', '-I', str(ROOT / 'reconstruction/uart') + '/',
               '-o', str(output / (name + '.obj'))]
    if name in ('parameters','transition'):
        command.append('-DANSI_OMF')
    subprocess.run(command + [str(source)], cwd=ROOT, check=True)
subprocess.run(['wlink', 'system', 'dos', 'option', 'quiet', 'option',
                'map=' + str(output / 'parser.map'), 'name', str(output / 'PARSER.EXE'),
                'file', ','.join(str(output / (name + '.obj')) for name, _ in sources)],
               cwd=ROOT, check=True)
inputs = [source for _, source in sources] + [ROOT / 'reconstruction/uart/encodings.inc']
manifest = {
    'kind': 'source-only-dos-ansi-parameter-diagnostic',
    'binary': 'build/ansi/PARSER.EXE',
    'binary_sha256': hashlib.sha256((output / 'PARSER.EXE').read_bytes()).hexdigest(),
    'sources': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
    'limitations': ['Recovered parameter reader only; the full ANSI state machine is not yet linked.',
                    'Byte provider uses a memory fixture, not a live serial modem.',
                    'Maintained mode rejects oversized digits, numeric overflow, excess parameters and timeout.'],
}
(output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print('Built', manifest['binary'], manifest['binary_sha256'], flush=True)
