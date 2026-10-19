#!/usr/bin/env python3
"""Actual8086DOS full native status drawing through CONFIG/resident bridges."""
import hashlib
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/status-renderer'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    manifest_path = OUT / 'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    for name, digest in manifest['source_dependencies'].items():
        assert sha(ROOT / name) == digest, name
    assert sha(OUT / 'STATUS.EXE') == manifest['binary_sha256']
    fixture = ROOT / 'standalone/fixtures/status_formatter_vectors.json'
    vectors = json.loads(fixture.read_text())['cases']
    normal = bytes.fromhex(next(v for v in vectors if v['name'] == 'normal')['expected_hex'])
    assert len(normal) == 81 and normal.count(b'FDX') == 1
    half = normal.replace(b'FDX', b'HDX')
    def frame(text, emphasis=False):
        result = bytearray(b'\xcc' * 4004)
        for i, char in enumerate(text):
            result[3840+2*i] = char
            result[3841+2*i] = 0x1e if emphasis and 1 <= i <= 14 else 0x1f
        return bytes(result)
    expected = {'FDX.BIN': frame(normal, True), 'HDX.BIN': frame(half, True),
                'ALT.BIN': frame(b' ' * 80), 'HIDDEN.BIN': b'\xcc' * 4004,
                'MESSAGE.BIN': frame(b' ' * 36 + b'Esc:EXIT' + b' ' * 36)}
    expected['LABELS.BIN'] = frame(b'F1 HELP   F2 SAVE   F3 FIND   F4 SEND   F5 READ   F6 FILE   F7 EXIT   F8 MENU   ')
    failed_frame = bytearray(b'\xcc' * 4004)
    for i in range(1, 15):
        failed_frame[3841+2*i] = 0x1e
    expected.update({name: bytes(failed_frame) for name in ('FORMAT.BIN', 'OVERFLOW.BIN', 'ARGS.BIN')})
    predictions = dict(fixture_sha256=sha(fixture), binary_sha256=manifest['binary_sha256'],
                       frames={name: value.hex() for name, value in expected.items()})
    (OUT / 'predictions.json').write_text(json.dumps(predictions, indent=2) + '\n')
    for name in expected:
        (OUT / name).unlink(missing_ok=True)
    (OUT / 'RESULT.TXT').unlink(missing_ok=True)
    (OUT / 'RUN.BAT').write_bytes(b'@echo off\r\nSTATUS.EXE\r\nif errorlevel 1 goto BAD\r\necho PASS>RESULT.TXT\r\ngoto DONE\r\n:BAD\r\necho FAIL>RESULT.TXT\r\n:DONE\r\n')
    (OUT / 'dosbox.conf').write_text('[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=fixed 6000\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "' + str(OUT) + '"\nc:\ncall RUN.BAT\nexit\n')
    with (OUT / 'dosbox.log').open('w') as log:
        subprocess.run(['dosbox-x', '-fastlaunch', '-nogui', '-conf', str(OUT / 'dosbox.conf')],
                       env=dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy'),
                       stdout=log, stderr=log, check=True, timeout=30)
    assert (OUT / 'RESULT.TXT').read_text().strip() == 'PASS', 'DOS stack/ABI/operation checks failed'
    cases = []
    for name, wanted in expected.items():
        path = OUT / name
        got = path.read_bytes()
        assert got == wanted, (name, [(i, a, b) for i, (a, b) in enumerate(zip(got, wanted)) if a != b][:20])
        cases.append(dict(name=name, passed=True, bytes=len(got), sha256=sha(path),
                          after_visible_hex=got[4000:4004].hex()))
    report = dict(passed=True, original_inputs=[], binary_sha256=manifest['binary_sha256'],
                  manifest_sha256=sha(manifest_path), checker_sha256=sha(Path(__file__)),
                  predictions_sha256=sha(OUT / 'predictions.json'), cases=cases,
                  scope='Actual8086DOS full recovered515B status body and175B helpers, maintained far bounded formatter, real native text/UI VRAM functions, actual CONFIG/resident RETN/cdecl bridges. Six successful status cases plus three typed formatter failures compare all4004bytes including native81st cell, eight distinct key-label fields and emphasis attributes. Rejected formats/overflow/argument exhaustion return3/7/10; native post-format emphasis writes remain explicit in failure expectations. DS=SS, SP/BP/SI/DI/IF/DF and stack guards checked in DOS. Carrier is explicit diagnostic word; parent RPC, production state staging, physical DCD/CGA and full application integration remain open.')
    (OUT / 'checks.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Full native status:', len(cases), 'actual8086DOS cases PASS')


if __name__ == '__main__':
    main()
