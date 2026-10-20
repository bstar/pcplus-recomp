#!/usr/bin/env python3
"""Build recovered control-break component without original or analysis inputs."""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / 'reconstruction/program_break'
OUT = ROOT / 'build/program-break'
OUT.mkdir(parents=True, exist_ok=True)
proof = json.loads((CORE / 'provenance.json').read_text())
include = ['-I', str(CORE)+'/', '-I', str(ROOT / 'reconstruction/uart')+'/']
objects = []
for unit in proof['units']:
    source = ROOT / unit['file']
    target = OUT / (source.stem+'.bin')
    subprocess.run(['nasm', '-f', 'bin', *include, str(source), '-o', str(target)], check=True)
    assert hashlib.sha256(target.read_bytes()).hexdigest() == unit['sha256'], source
    obj = OUT / (source.stem+'.obj')
    subprocess.run(['nasm', '-f', 'obj', '-DPROGRAM_BREAK_OMF', *include, str(source), '-o', str(obj)], check=True)
    objects.append(str(obj))
host = ROOT / 'standalone/program_break_diagnostic.asm'
obj = OUT / 'host.obj'
subprocess.run(['nasm', '-f', 'obj', str(host), '-o', str(obj)], check=True)
subprocess.run(['wlink', 'system', 'dos', 'option', 'quiet', 'option', 'map='+str(OUT/'break.map'),
    'name', str(OUT/'BRKVEC.EXE'), 'file', ','.join([str(obj), *objects])], check=True)
sources = [CORE/'abi.inc', CORE/'provenance.json', ROOT/'reconstruction/uart/encodings.inc', host, Path(__file__)]
sources += [ROOT/u['file'] for u in proof['units']]
(OUT/'manifest.json').write_text(json.dumps(dict(binary_sha256=hashlib.sha256((OUT/'BRKVEC.EXE').read_bytes()).hexdigest(),
    recovered_bytes=sum(u['bytes'] for u in proof['units']),
    inputs={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}),indent=2)+'\n')
print('Built BRKVEC.EXE from',sum(u['bytes'] for u in proof['units']),'exact recovered bytes')
