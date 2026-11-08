#!/usr/bin/env python3
"""Bind original compiler vectors to source compilers, DOS runtime and UART checks."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src/aspect'))
from compiler import CompileError, compile_source


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def manifest(folder, leaf):
    m = read(folder/'manifest.json')
    assert m['original_inputs'] == []
    assert sha(folder/leaf) == m['binary_sha256']
    for name, digest in m['sources'].items():
        assert sha(ROOT/name) == digest, name
    return m


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('compiler', 'runtime', 'uart', 'dos', 'runner', 'output'):
        p.add_argument('--'+name, type=Path, required=True)
    a = p.parse_args()
    fixture = ROOT/'standalone/fixtures/aspect_connected_compiler_vectors.json'
    oracle = read(fixture)
    assert oracle['compiler_sha256'] == '5664fdfae375774da5303cc8b53c00ef773a6650132de73c7206e46ddc05039a'
    cc = read(a.compiler/'checks.json')
    assert cc['passed'] and cc['original_inputs'] == []
    cm = manifest(a.compiler, 'ASPCOMP.EXE')
    assert cc['binary_sha256'] == cm['binary_sha256']
    assert cc['manifest_sha256'] == sha(a.compiler/'manifest.json')
    assert cc['case_manifest_sha256'] == sha(a.compiler/'cases.json')
    assert cc['fixture_sources'][str(fixture.relative_to(ROOT))] == sha(fixture)
    rows = read(a.compiler/'cases.json')
    by_source = {r['source_sha256']: (i, r) for i, r in enumerate(rows)}
    accepted = 0
    for case in oracle['cases']:
        assert hashlib.sha256(case['source'].encode('cp437')).hexdigest() == case['source_sha256']
        try:
            data = compile_source(case['source'])
            ok = True
        except CompileError:
            ok = False
        assert ok == case['success'], case['label']
        i, row = by_source[case['source_sha256']]
        assert row['accepted'] == ok, case['label']
        if ok:
            expected = bytes.fromhex(case['hex'])
            assert data == expected, case['label']
            assert row['asx_sha256'] == hashlib.sha256(expected).hexdigest()
            assert (a.compiler/'tests'/f'P{i:05}.ASX').read_bytes() == expected
            accepted += 1
    rc = read(a.runtime/'checks.json')
    rm = manifest(a.runtime, 'EXECUTE.EXE')
    assert rc['passed'] and rc['original_inputs'] == []
    assert rc['binary_sha256'] == rm['binary_sha256']
    assert rc['manifest_sha256'] == sha(a.runtime/'manifest.json')
    assert rc['result_sha256'] == sha(a.runtime/'RESULT.TXT')
    run = (a.runtime/'RESULT.TXT').read_text()
    assert 'CONNECTED_API 7 checks' in run
    expected_lines = ['VALUE CN0.ASX integer0=0', 'VALUE CN128.ASX integer0=128',
                      'VALUE CN128.ASX long0=129', 'STRING CN128.ASX string0=313238',
                      'VALUE CNNOIO.ASX integer0=7', 'VALUE CNOFF.ASX integer0=7',
                      'VALUE CNBARE.ASX integer0=7', 'VALUE CNBOOL.ASX integer0=3']
    assert all(line in run.splitlines() for line in expected_lines)
    assert 'CASE CNNOIO.ASX error=3 ' in run and 'CASE CNOFF.ASX error=3 ' in run
    uc = read(a.uart/'checks.json')
    um = manifest(a.uart, 'SERIAL.EXE')
    assert uc['passed'] and uc['original_inputs'] == []
    assert uc['binary_sha256'] == um['binary_sha256']
    assert uc['checker_sha256'] == sha(ROOT/'standalone/check_aspect_serial.py')
    carrier = [g for g in uc['groups'] if g['case'].startswith('carrier-raw-DCD-')]
    assert len(carrier) == 1 and carrier[0]['inputs'] == 1028 and carrier[0]['passed']
    dc = read(a.dos/'checks.json')
    runner = manifest(a.runner, 'ASPECT.EXE')
    assert dc['passed'] and dc['original_inputs'] == []
    assert dc['runner_sha256'] == runner['binary_sha256']
    assert dc['compiler_sha256'] == cm['binary_sha256']
    assert dc['checker_sha256'] == sha(ROOT/'standalone/check_aspect_connected_dos.py')
    assert dc['reused_checker_sha256'] == sha(ROOT/'standalone/test_aspect_script_serial_dos.py')
    assert [r['name'] for r in dc['cases']] == ['carrierN', 'carrierS', 'carrierH', 'carrierB', 'carriernested']
    for case in dc['cases']:
        assert case['passed'] and all(case['checks'].values())
        assert case['binary_sha256'] == runner['binary_sha256']
        folder = a.dos/case['name']
        for leaf, key in [('ASPECT.EXE', 'binary_sha256'), ('CASE.ASP', 'source_sha256'),
                          ('CASE.ASX', 'asx_sha256'), ('SERTEST.EXE', 'parent_binary_sha256'),
                          ('dosbox.conf', 'config_sha256')]:
            assert sha(folder/leaf) == case[key]
        assert (folder/'transmitted.bin').read_bytes().hex() == case['tx_hex']
        assert (folder/'RETURN.BIN').read_bytes() == b'TRAIL'
    paths = [a.compiler/'checks.json', a.runtime/'checks.json', a.uart/'checks.json',
             a.dos/'checks.json', fixture, ROOT/'standalone/fixtures/aspect_connected_runtime_vectors.json']
    result = dict(passed=True, schema=1, original_inputs=[],
                  compiler_oracle=dict(cases=len(oracle['cases']), accepted=accepted,
                                       rejected=len(oracle['cases'])-accepted, exact_DOS_and_host_bytes=True),
                  compiler_regression=cc['DOS_summary'], runtime_regression=rc['DOS_summary'],
                  carrier_API_checks=7, UART_carrier_inputs=1028, UART_regression_inputs=uc['inputs'],
                  DOS_cases=[r['name'] for r in dc['cases']],
                  binaries=dict(compiler=cm['binary_sha256'], runner=runner['binary_sha256'],
                                runtime=rm['binary_sha256'], UART=um['binary_sha256']),
                  receipts={str(f.resolve().relative_to(ROOT)): sha(f) for f in paths},
                  recorder_sha256=sha(Path(__file__)),
                  limitations=['Raw DCD0/128 semantics recovered statically; original runtime not executed.',
                               'Serial diagnostic inputs and CPU IO are explicit models.',
                               'Production DOS nullmodem holds DCD high; no analog/SIP/physical acceptance.',
                               'Standalone runner only; matched full-child promotion/package remains pending.',
                               'Stable hardware-test package and selected installation unchanged.'])
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
