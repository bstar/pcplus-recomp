#!/usr/bin/env python3
"""Verify real DOS ALARM/UART captures and the matching cold source rebuild."""
import argparse, hashlib, itertools, json
from pathlib import Path
from build_context_help import ROOT, sha
from test_alarm_dos_uart import PAYLOAD


def verify(build, matrix, cold):
    sources, receipts = {}, {}

    def load(path, field):
        report = json.loads(path.read_text())
        assert report['passed'], str(path)
        receipts[str(path.relative_to(ROOT))] = sha(path)
        for name, digest in report[field].items():
            assert sha(ROOT / name) == digest, name
            if name in sources:
                assert sources[name] == digest, name
            sources[name] = digest
        return report

    manifest = load(build / 'manifest.json', 'sources')
    tests = load(matrix / 'result.json', 'inputs')
    proof = load(cold / 'result.json', 'sources')
    baseline = load(ROOT / 'docs/validation/aspect-alarm-cooperative.json', 'sources')
    binary = sha(build / 'ALARM.EXE')
    assert manifest['diagnostic_build'] and manifest['original_inputs'] == []
    assert manifest['main_bank'] != manifest['speaker_bank']
    assert binary == manifest['binary_sha256'] == tests['binary_sha256'] == proof['binary_sha256']
    assert tests['full_matrix'] and tests['payload_sha256'] == hashlib.sha256(PAYLOAD).hexdigest()
    expected = {f'{p}-{f}-{m}-S' for p, f, m in itertools.product((1, 2), 'NSHB', 'NQKFB')}
    expected |= {f'{p}-{f}-K-E' for p, f in itertools.product((1, 2), 'NSHB')}
    expected |= {'1-N-G-S', '2-S-G-E'}
    assert len(tests['cases']) == len(expected) == 50
    assert {r['case'] for r in tests['cases']} == expected
    for row in tests['cases']:
        label = row['case']
        assert row['passed'] and len(row['checks']) == 7 and all(row['checks'].values()), label
        assert row['assertions'] > 530 and row['callbacks'] > 1 and 0 < row['maximum'] <= 508, label
        assert row['captures'], label
        for name, digest in row['captures'].items():
            path = matrix / name
            assert path.resolve().is_relative_to(matrix.resolve())
            assert sha(path) == digest, name
        folder = matrix / label
        assert (folder / 'RX.BIN').read_bytes() == PAYLOAD, label
        assert (folder / 'wire.bin').read_bytes() == (b'\x11RPF\x13' if label.split('-')[1] in 'SB' else b'RPF'), label
        assert sha(folder / 'ALARM.EXE') == binary, label
    assert proof['source_files'] == len(proof['sources']) == 29 and proof['original_inputs'] == []
    assert proof['cases'] == ['1-N-N-S', '2-S-K-E', '1-N-G-S']
    repeated = cold / 'source/build/tests/result.json'
    assert sha(repeated) == proof['test_result_sha256']
    repeats = json.loads(repeated.read_text())
    assert repeats['passed'] and repeats['binary_sha256'] == binary
    assert [r['case'] for r in repeats['cases']] == proof['cases']
    assert baseline['summary']['DOS_cases'] == 94
    sources['standalone/record_alarm_dos.py'] = sha(Path(__file__))
    return dict(passed=True, sources=sources, receipts=receipts, binary_sha256=binary,
        summary=dict(DOS_cases=50, DOS_checks=sum(r['assertions'] for r in tests['cases']),
            exact_RX_bytes_per_case=len(PAYLOAD), cold_source_files=29, cold_repeated_cases=3),
        limitations=[
            'Standalone diagnostic only: no ALARM compiler/VM opcode, parent PRM policy, WHEN/key lease or terminal receive-renderer integration.',
            'Muted DOSBox8086 executes actual DOS clock, BIOS keys, banked PIT/speaker and UART ISR. No acoustic waveform, analog modem handshake, physical timing or SIP/BBS acceptance.',
            'Nullmodem holds CTS ready and does not enforce RTS. Software XOFF/XON is explicit; this is not physical hardware-flow stress coverage.',
            'Tone scheduling retains the cooperative adapter quantization and key cancellation changes documented in its baseline.',
            'Cold export reproduces the exact executable and repeats three selected cases, not the full50-case matrix.',
            'No package selection, deployment, private configuration, running BBS or bridge changes.'],
        scope=__doc__ + ' All508 bytes must be consumed within the alert. Covers COM1/2 and four flow modes, quiet/key/service-fault/busy-gate paths, enhanced keys, foreign speaker generation quarantine/recovery and UART/PIC/vector restoration. Native bytes retain the separate cooperative/native baseline provenance.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('build', 'matrix', 'cold', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.build.resolve(), args.matrix.resolve(), args.cold.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print('PASS real DOS ALARM platform:', result['summary'])


if __name__ == '__main__':
    main()
