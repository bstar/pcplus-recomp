#!/usr/bin/env python3
"""Seal checked source-recorder and raw-output component/DOS evidence."""
import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('host', 'raw', 'dos'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    target = args.output.resolve()
    assert target.is_relative_to(ROOT / 'docs/validation') and not target.exists()
    proofs = {}
    for name, count in [('host', 17), ('raw', 6), ('dos', 6)]:
        path = getattr(args, name).resolve()
        assert path.is_relative_to(ROOT / 'build')
        result = read(path)
        assert result['passed'] and len(result['cases']) == count
        assert all(case['passed'] and all(case.get('checks', {}).values()) for case in result['cases'])
        for source, digest in result['inputs'].items():
            assert sha(ROOT / source) == sha(path.parent / 'frozen-source' / source) == digest, source
        for capture, digest in result.get('captures_sha256', {}).items():
            assert sha(path.parent / capture) == digest, capture
        if name == 'host':
            assert result['case_count'] == count and sha(path.parent / 'recorder.so') == result['library_sha256']
            for case in result['cases']:
                if 'source_sha256' in case:
                    assert sha(path.parent / (case['case'] + '.ASP')) == case['source_sha256']
        proofs[name] = dict(result=str(path.relative_to(ROOT)), sha256=sha(path), cases=result['cases'])
    raw = args.raw.resolve().parent
    expected_raw = {'all-octets': bytes(range(256)), 'long-stream': bytes(range(256)) * 8,
                    'mixed-legacy': bytes.fromhex('00225e7eff') + b'AT\r',
                    'invalid-late': b'', 'invalid-odd': b'', 'no-attachment': b''}
    assert {case['case'] for case in proofs['raw']['cases']} == set(expected_raw)
    for name, data in expected_raw.items():
        assert (raw / name / 'wire.bin').read_bytes() == data, name
    dos = args.dos.resolve().parent
    expected_dos = {'ordinary': b'READY>' + bytes(range(256)),
                    'quoted-controls': b'READY>' + bytes(range(256)),
                    'long-control-prompt': b'READY>' + bytes(range(256)) * 8,
                    'timeout-no-payload': b'READY>', 'writefail': b'', 'cancel': b''}
    assert {case['case'] for case in proofs['dos']['cases']} == set(expected_dos)
    for name, data in expected_dos.items():
        assert (dos / name / 'wire.bin').read_bytes() == data, name
    for case in proofs['dos']['cases']:
        assert (dos / case['case'] / 'peer-reply.bin').read_bytes() == b''.join(bytes.fromhex(value) for value in case['peer_replies'])
    regressions = {}
    for name, location in [('runtime', 'aspect-runtime'), ('compiler', 'aspect-compiler-dos'),
                           ('runner', 'aspect-runner'), ('dispatch', 'aspect-dispatch')]:
        folder = ROOT / 'build' / location
        path = folder / 'checks.json'
        checks = read(path)
        assert checks['passed'] and not checks.get('original_inputs', [])
        assert sha(ROOT / 'standalone' / ('check_aspect_' + ('compiler_dos' if name == 'compiler' else name) + '.py')) == checks.get('checker_sha256', checks.get('check_sha256'))
        regressions[name] = dict(result=str(path.relative_to(ROOT)), sha256=sha(path), summary=checks['DOS_summary'])
        if name != 'dispatch':
            manifest_path = folder / 'manifest.json'
            manifest = read(manifest_path)
            assert not manifest['original_inputs']
            assert sha(manifest_path) == checks['manifest_sha256']
            for source, digest in manifest['sources'].items():
                assert sha(ROOT / source) == digest, source
    assert read(ROOT / 'build/aspect-runtime/checks.json')['DOS_summary'] == 'ASPECT_RUNTIME 1125 cases 27030 checks 0 failures'
    compiler = read(ROOT / 'build/aspect-compiler-dos/checks.json')
    assert compiler['case_count'] == 2025 and compiler['accepted'] == 1059 and compiler['rejected'] == 966
    compiler_cases = read(ROOT / 'build/aspect-compiler-dos/cases.json')
    raw_cases = read(ROOT / 'standalone/fixtures/aspect_raw_output_vectors.json')['vectors']
    for case in raw_cases:
        row = next(row for row in compiler_cases if 'source-extension:' + case['name'] in row['references'])
        assert row['accepted'] and row['source_sha256'] == case['source_sha256'] and row['asx_sha256'] == case['asx_sha256']
    runtime_text = (ROOT / 'build/aspect-runtime/RESULT.TXT').read_text()
    for name, data in [('RAWALL', bytes(range(256))), ('RAWREV', bytes(range(255, -1, -1)))]:
        assert bytes.fromhex(re.search(r'^TX ' + name + r'\.ASX ([0-9A-F]+)$', runtime_text, re.M)[1]) == data
    dispatch = read(ROOT / 'build/aspect-dispatch/checks.json')
    assert dispatch['flat_sha256'] == 'd2006fe5dd53b6416aec915c9bd58b4ae1a11fc003aafef090279fa2d37520a6'
    assert dispatch['cpu_cases'] == 590 and dispatch['DOS_summary'] == 'ASPECT_DISPATCH 3616 checks 0 failures'
    inputs = {str(path.relative_to(ROOT)): sha(path) for path in [Path(__file__).resolve(),
        ROOT / 'src/aspect/recorder.c', ROOT / 'src/aspect/recorder.h', ROOT / 'Makefile']}
    result = dict(passed=True, source_recorder_component_accepted=True, foreground_recording_accepted=False,
                  host_cases=17, actual_DOS_recorder_cases=6, actual_DOS_raw_UART_cases=6,
                  raw_extension=dict(opcode='D7/01', command='TRANSMITRAW', operand='0..80 even ASCII hexadecimal characters',
                                     original_native_slot_replaced=False, legacy_ASX_portable=False),
                  production_runner_sha256=sha(ROOT / 'build/aspect-runner/ASPECT.EXE'),
                  production_compiler_sha256=sha(ROOT / 'build/aspect-compiler-dos/ASPCOMP.EXE'),
                  proofs=proofs, regressions=regressions, inputs=inputs,
                  scope='Bounded40-byte transmitted groups and16-byte receive prompts, checked short writes/close '
                        'ownership, pending-tail flush, cancellation and first/secondary error preservation. '
                        'Host faults are modeled; DOS tests use actual far recorder callbacks, files, compiler '
                        'and production UART runner with exact raw bytes, matching prompts, timeout suppression, '
                        'read-only write failure and unpublished cancellation. Legacy formatted TRANSMIT and '
                        'native flat dispatcher remain separately checked. No foreground terminal recorder, '
                        'start/stop UI, shared owner/exclusion, broad modem/BBS/hardware or full F13 acceptance.')
    with target.open('x') as stream:
        stream.write(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(passed=True, host_cases=17, DOS_recorder_cases=6, DOS_raw_UART_cases=6)))


if __name__ == '__main__':
    main()
