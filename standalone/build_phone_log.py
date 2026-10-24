#!/usr/bin/env python3
"""Build exact call-log OMF and a source-only DOS FILE diagnostic."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/phone-log'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    source = ROOT / 'reconstruction/phone_log/controller.asm'
    proof_path = source.parent / 'provenance.json'
    proof = json.loads(proof_path.read_text())
    include = '-I' + str(ROOT / 'reconstruction/uart') + '/'
    subprocess.run(['nasm', '-fbin', include, str(source), '-o', str(OUT / 'controller.bin')], check=True)
    assert (OUT / 'controller.bin').stat().st_size == proof['bytes'] and sha(OUT / 'controller.bin') == proof['sha256']
    subprocess.run(['nasm', '-fobj', '-DPHONE_LOG_OMF', include, str(source), '-o', str(OUT / 'controller.obj')], check=True)
    binding = ROOT / 'standalone/phone_log_bindings.asm'
    subprocess.run(['nasm', '-fobj', str(binding), '-o', str(OUT / 'bindings.obj')], check=True)
    diagnostic = ROOT / 'standalone/phone_log_diagnostic.c'
    subprocess.run(['wcl', '-q', '-bt=dos', '-0', '-ms', '-s', '-w4', '-we', '-k4096',
                    '-fm=PHONELOG.map', '-fe=PHONELOG.EXE', str(diagnostic), 'controller.obj', 'bindings.obj'], cwd=OUT, check=True)
    sources = [Path(__file__), source, proof_path, binding, diagnostic, ROOT / 'reconstruction/uart/encodings.inc']
    manifest = dict(kind='source-only-native-phone-log-FILE-diagnostic',
                    binary_sha256=sha(OUT / 'PHONELOG.EXE'), exact_bytes=proof['bytes'],
                    sources={str(path.relative_to(ROOT)): sha(path) for path in sources}, original_inputs=[],
                    limitations=['Actual DOS FILE/append/text translation; synthetic fixed date/clock and direct filename provider.',
                                 'Not application integration, native path/clock recovery or production persistence failure handling.'])
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print('Built source-only PHONELOG.EXE with', proof['bytes'], 'recovered instruction bytes')


if __name__ == '__main__':
    main()
