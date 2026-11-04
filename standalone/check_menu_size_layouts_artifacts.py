#!/usr/bin/env python3
"""Independent raw PRM/BIOS/video/UART/Telnet audit of the size-handoff matrix.

No physical carrier, SIP/DSP, BBS layout/editor or transfer acceptance.
"""
import argparse
import hashlib
import json
import struct
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def decode_telnet(raw):
    """Decode captured client wire without invoking the candidate codec."""
    data, dimensions = bytearray(), []
    index = 0
    while index < len(raw):
        byte = raw[index]
        index += 1
        if byte != 255:
            data.append(byte)
            continue
        assert index < len(raw)
        command = raw[index]
        index += 1
        if command == 255:
            data.append(255)
        elif command in (251, 252, 253, 254):
            assert index < len(raw)
            index += 1
        elif command == 250:
            sub = bytearray()
            while True:
                assert index < len(raw)
                byte = raw[index]
                index += 1
                if byte != 255:
                    sub.append(byte)
                    continue
                assert index < len(raw)
                byte = raw[index]
                index += 1
                if byte == 255:
                    sub.append(255)
                else:
                    assert byte == 240
                    break
            assert sub and sub[0] == 31 and len(sub) == 5
            dimensions.append(struct.unpack('>HH', sub[1:]))
        else:
            raise AssertionError(('unexpected Telnet command', command))
    return bytes(data), dimensions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--terminal', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run, out, binary = args.run.resolve(), args.output.resolve(), args.terminal.resolve()
    assert run.is_relative_to(ROOT / 'build') and out.is_relative_to(ROOT / 'build')
    out.mkdir(parents=True, exist_ok=False)
    report = json.loads((run / 'result.json').read_text())
    assert report['passed'] and report['terminal_sha256'] == sha(binary)
    manifest = json.loads((binary.parent / 'manifest.json').read_text())
    assert sha(binary.parent / 'manifest.json') == report['terminal_manifest_sha256']
    for source_set in (report['sources'], manifest['sources']):
        for name, digest in source_set.items():
            assert sha(ROOT / name) == digest, name
    stage_path = ROOT / report['stage_receipt']
    assert sha(stage_path) == report['stage_receipt_sha256']
    stage = json.loads(stage_path.read_text())
    assert stage['passed']
    for name, digest in stage['sources'].items():
        assert sha(ROOT / name) == digest, name
    for name, digest in stage['candidate'].items():
        assert sha(stage_path.parent / 'candidate' / name) == digest, name
    assert len(report['cases']) == 8
    assert {c['case'] for c in report['cases']} == {
        f'rows-{rows}-hidden-{hidden}' for rows in (25, 28, 43, 50) for hidden in (0, 1)}
    geom = out / 'GEOM.COM'
    subprocess.run(['nasm', '-fbin', str(ROOT / 'standalone/display_startup_geometry.asm'), '-o', str(geom)], check=True)
    cases = []
    for case in report['cases']:
        path = ROOT / case['path']
        assert sha(path) == case['sha256'] and case['passed']
        r = json.loads(path.read_text())
        assert r['passed'] and all(r['checks'].values()) and r['terminal_sha256'] == sha(binary)
        folder = path.parent
        for name, digest in r['sources'].items():
            assert sha(ROOT / name) == digest, name
        for name, digest in r['artifacts'].items():
            assert sha(folder / name) == digest, (case['case'], name)
        prm = (folder / 'TEST.PRM').read_bytes()
        hidden, selector, physical, mode = [struct.unpack_from('<H', prm, at)[0]
                                          for at in (0x1c2, 0x1c8, 0x1ca, 0x4ec)]
        assert case['case'] == f'rows-{physical}-hidden-{hidden}' and (selector, mode) == (2, 0)
        logical = physical - (not hidden)
        assert (r['physical_rows'], r['logical_rows'], r['status_hidden']) == (physical, logical, hidden)
        font = 14 if physical == 28 else 8 if physical in (43, 50) else 16
        rows, actual_font, mode_cols, page = struct.unpack('<4H', (folder / 'GEOM.BIN').read_bytes())
        assert (rows, actual_font, mode_cols, page >> 8) == (physical, font, 0x5003, 0)
        assert sha(geom) == sha(folder / 'GEOM.COM')
        sampler = out / (case['case'] + '-SNAP.COM')
        subprocess.run(['nasm', '-fbin', str(folder / 'sampler.asm'), '-o', str(sampler)], check=True)
        assert sha(sampler) == sha(folder / 'SNAP.COM')
        screen = (folder / 'SCREEN.BIN').read_bytes()
        assert len(screen) == 8000 and screen[:30:2] == b'FIRST BYTE SAFE'
        assert screen[(logical - 1) * 160:(logical - 1) * 160 + 22:2] == b'BRIDGE-AREA'
        last = screen[(physical - 1) * 160:physical * 160:2]
        if hidden:
            assert last.startswith(b'BRIDGE-AREA')
        else:
            assert last.startswith(b' Disconnected  ') and b'ANSI' in last and b'19200 N81' in last
        # The existing synthetic Hayes boundary forwards escape/ATH at shutdown;
        # these bytes are checked explicitly, never counted as modem acceptance.
        payload = b'\x1b[1;16R\x1b[?1;2cz+++ATH\r'
        expected = b'ATZ\rATD1\rloc\r\x1b' + f'[8;{logical};80t'.encode() + payload
        assert (folder / 'serial-in.bin').read_bytes() == expected
        decoded, dimensions = decode_telnet((folder / 'tcp-in.bin').read_bytes())
        assert decoded == payload == (folder / 'application-in.bin').read_bytes()
        assert dimensions == [(80, logical)]
        downstream = (folder / 'serial-out.bin').read_bytes()
        assert downstream.count(b'\x1b[18t') == 1
        assert downstream.endswith(b'\x1b[2J\x1b[99;1HBRIDGE-AREA\x1b[HFIRST BYTE SAFE\x1b[6n\x1b[0c')
        before = (folder / 'BEFORE.BIN').read_bytes()
        assert len(before) == 42 and before == (folder / 'AFTER.BIN').read_bytes()
        assert (folder / 'PASS.TXT').exists() and not (folder / 'FAIL.TXT').exists()
        assert 'cputype=8086' in (folder / 'dosbox.conf').read_text()
        cases.append(dict(case=case['case'], physical_rows=physical, logical_rows=logical,
                          font=font, decoded_NAWS=dimensions, passed=True))
    result = dict(passed=True, cases=cases, DOS_workflows=8, terminal_sha256=sha(binary),
                  report_sha256=sha(run / 'result.json'),
                  sources={str(Path(__file__).relative_to(ROOT)): sha(__file__)}, scope=__doc__)
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print('PASS independent DOS startup/bridge layouts:', len(cases))


if __name__ == '__main__':
    main()
