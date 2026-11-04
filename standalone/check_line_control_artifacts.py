#!/usr/bin/env python3
"""Independently verify owned DOS line-cycle BIOS, VRAM and exact wire artifacts.

No physical modem, SIP, online resize or live BBS acceptance is established.
"""
import argparse
import hashlib
import json
import struct
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def selections(initial, preferred, mode, count, blocked):
    """Derive physical outcomes from the PRM and recovered selector policy."""
    accepted = initial
    result = []
    for index in range(count):
        if index and not blocked:
            accepted = accepted % (4 if mode else 2) + 1
        # All fixtures start in baseline text mode. Selector3 retains the
        # scanline setting of the preceding preferred-row request; AH=0 mode3
        # after350 scanlines therefore has14-pixel glyphs, not16.
        font = 16
        if accepted in (3, 4) and mode == 18:
            accepted = 1
        physical = preferred if accepted in (2, 4) else 25
        if physical == 28:
            font = 14
        elif physical in (43, 50):
            font = 8
        elif accepted == 3 and preferred == 43:
            font = 14
        result.append((physical, font))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run, out = args.run.resolve(), args.output.resolve()
    assert run.is_relative_to(ROOT / 'build') and out.is_relative_to(ROOT / 'build')
    out.mkdir(parents=True, exist_ok=False)
    report = json.loads((run / 'result.json').read_text())
    assert report['passed']
    for name, digest in report['sources'].items():
        assert sha(ROOT / name) == digest, name
    binary = ROOT / report['terminal_path']
    manifest = json.loads((binary.parent / 'manifest.json').read_text())
    assert manifest['experimental_line_control']
    assert sha(binary) == manifest['binary_sha256'] == report['terminal_sha256']
    for name, digest in manifest['sources'].items():
        assert sha(ROOT / name) == digest, name
    expected = {f'rows-{rows}-mode-{mode}-hidden-{hidden}'
                for rows in (28, 43, 50) for mode in (0, 3) for hidden in (0, 1)}
    expected |= {'graphics-fallback-next-key', 'tracked-online-refusal', 'missing-import-refusal'}
    assert len(report['cases']) == 15
    assert {r['case']['name'] for r in report['cases']} == expected
    geometry = out / 'GEOM.COM'
    subprocess.run(['nasm', '-fbin', str(ROOT / 'standalone/display_startup_geometry.asm'),
                    '-o', str(geometry)], check=True)
    cases = []
    for r in report['cases']:
        assert r['passed'] and all(r['checks'].values())
        assert r['terminal_sha256'] == sha(binary)
        for name, digest in r['artifacts'].items():
            assert sha(ROOT / name) == digest, name
        c = r['case']
        name = c['name']
        online = name == 'tracked-online-refusal'
        missing = name == 'missing-import-refusal'
        folder = (ROOT / r['parent_result']).parent
        raw = (folder / 'TEST.PRM').read_bytes()
        hidden, initial, preferred, mode = [struct.unpack_from('<H', raw, at)[0]
                                          for at in (0x1c2, 0x1c8, 0x1ca, 0x4ec)]
        assert (hidden, initial, preferred, mode) == tuple(c[k] for k in ('hidden', 'initial', 'preferred', 'mode'))
        if name.startswith('rows-'):
            assert name == f'rows-{preferred}-mode-{mode}-hidden-{hidden}' and initial == 1
            count = 5 if mode else 3
        elif online:
            assert (hidden, initial, preferred, mode) == (0, 2, 43, 0)
            count = 2
        elif missing:
            assert (hidden, initial, preferred, mode) == (0, 1, 50, 3)
            count = 2
        else:
            assert (hidden, initial, preferred, mode) == (0, 1, 43, 18)
            count = 4
        stages = selections(initial, preferred, mode, count, online or missing)
        witness = out / ('W-' + name + '.COM')
        mask = (1 << count) - 1
        subprocess.run(['nasm', '-fbin', '-DEXPECTED_MASK=' + str(mask),
                        str(ROOT / 'standalone/line_control_watch.asm'), '-o', str(witness)], check=True)
        assert sha(folder / 'LINEW.COM') == sha(witness)
        assert sha(folder / 'GEOM.COM') == sha(geometry)
        samples = (folder / 'LINES.BIN').read_bytes()
        assert len(samples) == 1676 and struct.unpack_from('<3H', samples) == (0x4c43, 1, mask)
        wire = b'ATZ\rATDCaseTest:23\r\x1b[1;16R\x1b[?1;2c' if online else b'\x1b[0n\x1b[1;16R\x1b[?1;2c'
        for index, (physical, font) in enumerate(stages):
            rows, actual_font, cursor, shape, video_mode, cols, page = struct.unpack_from('<7H', samples, 6 + index * 334)
            assert (rows, actual_font, video_mode, cols, page) == (physical, font, 3, 80, 0), (name, index)
            tail = samples[20 + index * 334:340 + index * 334:2]
            logical = physical - (not hidden)
            tag = f'STEP-{chr(65 + index)}'.encode()
            assert tail[80 if hidden else 0:][:6] == tag
            assert (b'Alt-Z FOR HELP' in tail[80:]) == (not hidden)
            wire += bytes([97 + index]) + b'\x1b' + f'[8;{logical};80t'.encode() + b'\x1b' + f'[{logical};80R'.encode()
        if online:
            wire += b'+++ATH\r'
        assert (folder / 'serial.bin').read_bytes() == wire, name
        assert (folder / 'PASS.TXT').exists() and not (folder / 'FAIL.TXT').exists()
        before = (folder / 'BEFORE.BIN').read_bytes()
        assert len(before) == 42 and before == (folder / 'AFTER.BIN').read_bytes()
        assert 'cputype=8086' in (folder / 'dosbox.conf').read_text()
        final_rows, final_font, mode_cols, page_word = struct.unpack('<4H', (folder / 'GEOM.BIN').read_bytes())
        assert (final_rows, final_font) == stages[-1] and mode_cols == 0x5003 and page_word >> 8 == 0
        screen = (folder / 'SCREEN.BIN').read_bytes()
        logical = final_rows - (not hidden)
        assert len(screen) == 8000 and screen[:30:2] == b'FIRST BYTE SAFE'
        assert screen[(logical - 1) * 160:(logical - 1) * 160 + 12:2] == f'STEP-{chr(64 + count)}'.encode()
        cases.append(dict(case=name, stages=count, physical_font_sequence=stages, passed=True))
    result = dict(passed=True, DOS_workflows=len(cases), geometry_stages=sum(c['stages'] for c in cases),
                  cases=cases, report_sha256=sha(run / 'result.json'), terminal_sha256=sha(binary),
                  sources={str(Path(__file__).relative_to(ROOT)): sha(__file__)}, scope=__doc__)
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print('PASS independent line controls:', result['DOS_workflows'], 'DOS workflows,', result['geometry_stages'], 'stages')


if __name__ == '__main__':
    main()
