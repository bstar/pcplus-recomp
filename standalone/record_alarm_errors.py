#!/usr/bin/env python3
"""Bind ALARM malformed operands, actual parent return and subsequent reuse."""
import json
import struct
import sys
from build_context_help import ROOT, sha
from alarm_error_fixtures import mutate
import aspect_exit_watch as watch
sys.path.insert(0, str(ROOT / 'src/aspect'))
from compiler import compile_source


def main():
    previous = ROOT / 'docs/validation/aspect-alarm-speaker.json'
    base = json.loads(previous.read_text())
    assert base['passed'] and not base['release_accepted']
    products = base['products']
    sources, receipts = {}, {str(previous.relative_to(ROOT)): sha(previous)}
    folder = ROOT / 'build/aspect-alarm-vm-dos/errors-groups-20261106'
    report = json.loads((folder / 'checks.json').read_text())
    speaker = json.loads((folder / 'speaker-checks.json').read_text())
    assert report['passed'] and speaker['passed'] and not speaker['enabled']
    assert report['terminal_sha256'] == products['TERMINAL.EXE']
    assert report['runner_sha256'] == products['ASPECT.EXE']
    expected = [7, 7, 7, 5, 5]
    assert len(report['cases']) == len(speaker['cases']) == 5
    for case, error in zip(report['cases'], expected):
        assert case['passed'] and all(case['checks'].values())
        assert case['passive_observer_header'][6] == error
        target = folder / case['case']
        kind = case['case'].removeprefix('alarm-vm-errors-')
        assert mutate(compile_source((target / 'LOGIN.ASP').read_text()), kind) == (target / 'LOGIN.ASX').read_bytes()
        wire = (target / 'serial.bin').read_bytes()
        assert b'KEYREADY' in wire and b'BADAFTER' not in wire and b'ready' in wire
        raw = (target / 'RENDER.BIN').read_bytes()
        assert struct.unpack('<7H', raw[-28:-14]) == (0, 0, 0, 0, 0, 4, 1)
    for path in folder.rglob('*'):
        if path.is_file():
            receipts[str(path.relative_to(ROOT))] = sha(path)
    path = ROOT / 'build/alarm-error-recovery-final-20261106/result.json'
    recovery = json.loads(path.read_text())
    assert recovery['passed'] and all(recovery['checks'].values())
    assert recovery['products'] == products
    for field in ('sources', 'inputs', 'artifacts'):
        for name, digest in recovery[field].items():
            assert sha(ROOT / name) == digest, name
            (sources if field == 'sources' else receipts)[name] = digest
    receipts[str(path.relative_to(ROOT))] = sha(path)
    capture = ROOT / 'build/connection-dos/alarm-error-recovery-final-20261106'
    telemetry = watch.read(capture / 'EXITSTAT.BIN')
    assert telemetry == recovery['exit_watch'] and telemetry['launches'] == 7
    assert [e['error'] for e in telemetry['exits']] == [0, *expected, 0]
    assert all(e['ds'] == e['ss'] and e['ds'] for e in telemetry['exits'])
    for name in ('standalone/test_aspect_alarm_vm_dos.py', 'standalone/alarm_error_fixtures.py',
                 'standalone/alarm_speaker_observer.py', 'standalone/test_aspect_pause_when_dos.py',
                 'standalone/test_aspect_keys_dos.py', 'standalone/test_aspect_renderer_dos.py',
                 'standalone/test_aspect_script_window_dos.py', 'standalone/record_alarm_errors.py'):
        sources[name] = sha(ROOT / name)
    result = dict(passed=True, release_accepted=False, products=products, sources=sources,
                  receipts=receipts, operand_cases=report['cases'], speaker=speaker,
                  same_parent_recovery=recovery, original_inputs=[], scope=__doc__, limitations=[
                      'Five authored invalid operands, not arbitrary ASX safety. Quiet standard BIOS/ANSI and passive UMB observers; no error injected while the ALARM tone/receive owner is active.',
                      'Native checking is retained but maintained errors abort; original unchecked/error-returning configurations are not reproduced here.',
                      'First single-case probe expected successful-alert screen text after failure; corrected before the accepted five-case run. Recovery attempts first lacked child executable staging, then misclassified the intentional child log as immutable; fresh final capture passes all original immutable-input checks.',
                      'No new application bytes, package selection, deployment, physical modem/SIP/audio, cold rebuild or modern BBS acceptance. Long-duration budgets and active-alert carrier/error cleanup remain open.'
                  ])
    (ROOT / 'docs/validation/aspect-alarm-errors.json').write_text(json.dumps(result, indent=2) + '\n')
    print('PASS five ALARM errors and seven same-parent invocations')


if __name__ == '__main__':
    main()
