#!/usr/bin/env python3
"""Source-only exact metadata helpers with explicit synthetic DOS diagnostic."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/transfer-metadata'
MODULE = ROOT / 'reconstruction/transfer_metadata'
OUT.mkdir(parents=True, exist_ok=True)
proof = json.loads((MODULE / 'provenance.json').read_text())
for unit in proof['units']:
    output = OUT / (Path(unit['source']).stem + '.bin')
    subprocess.run(['nasm', '-fbin', '-I', str(ROOT / 'reconstruction/uart') + '/',
                    str(MODULE / unit['source']), '-o', str(output)], check=True)
    raw = output.read_bytes()
    assert len(raw) == unit['bytes'], unit['source']
    assert hashlib.sha256(raw).hexdigest() == unit['sha256'], unit['source']

sources = ([MODULE / unit['source'] for unit in proof['units']]
           + [ROOT / path for path in proof['reused_sources']]
           + [ROOT / 'standalone/transfer_metadata_host.asm'])
objects = []
for index, source in enumerate(sources):
    obj = OUT / f'{index:02d}-{source.stem}.obj'
    objects.append(str(obj))
    subprocess.run(['nasm', '-fobj', '-DTRANSFER_METADATA_OMF', '-DMETA_KEYS_OMF',
                    '-DDIRECTORY_DIAL_OMF', '-DPROGRAM_EXEC_OMF',
                    '-DTRANSFER_RECEIVE_OMF', '-DTRANSFER_BLOCKS_OMF',
                    '-I', str(ROOT / 'reconstruction/uart') + '/',
                    str(source), '-o', str(obj)], check=True)
main = OUT / 'main.c'
main.write_text('unsigned __cdecl transfer_metadata_dos_test(void);\n'
                'int main(void) { return transfer_metadata_dos_test(); }\n')
subprocess.run(['wcl', '-q', '-bt=dos', '-0', '-ms', '-s', '-w4', '-we',
                '-k8192', '-fm=transfer_metadata.map', '-fe=METADATA.EXE',
                str(main), *objects], cwd=OUT, check=True)
result = {
    'kind': 'source-only-exact-transfer-metadata-memory-UART-fixture',
    'binary_sha256': hashlib.sha256((OUT / 'METADATA.EXE').read_bytes()).hexdigest(),
    'exact_metadata_bytes': sum(unit['bytes'] for unit in proof['units']),
    'sources': {str(source.relative_to(ROOT)): hashlib.sha256(source.read_bytes()).hexdigest()
                for source in sources},
    'limitations': ['Synthetic UART, timing, stat, display and cancel/carrier boundaries; '
                    'nonlocal unwind is an explicit INT3 boundary.',
                    'No live UART, actual file stat, batch owner or complete transfer session.'],
}
(OUT / 'manifest.json').write_text(json.dumps(result, indent=2) + '\n')
print('Built METADATA.EXE;', result['exact_metadata_bytes'], 'exact metadata bytes')
