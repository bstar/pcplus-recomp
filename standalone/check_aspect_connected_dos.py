#!/usr/bin/env python3
"""Execute CONNECTED with a real DOS UART owner, independent TCP peer and ASIO return."""
import argparse
import json
from pathlib import Path
import test_aspect_script_serial_dos as serial


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runner', type=Path, required=True)
    p.add_argument('--compiler', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    out = a.output.resolve()
    assert out.is_relative_to(serial.ROOT/'build') and not out.exists()
    binary = a.runner.resolve()
    serial.COMPILER = a.compiler.resolve()
    for target in (binary, serial.COMPILER):
        m = json.loads(target.with_name('manifest.json').read_text())
        assert serial.sha(target) == m['binary_sha256']
        assert m['original_inputs'] == []
        for name, digest in m['sources'].items():
            assert serial.sha(serial.ROOT/name) == digest, name
    source = ('integer i\nlong l\nproc main\n'
              'i=connected\nl=connected+1L\n'
              'if i==128 && l==129L\ntransmit "UP"\nelse\ntransmit "BAD"\nendif\n'
              'waitfor "END" 5\n'
              'if connected==128\ntransmit "DONE^M"\nelse\ntransmit "BAD"\nendif\nendproc\n')
    results = []
    cases = []
    for flow in ('N', 'S', 'H', 'B'):
        resume = b'\x11' if flow in ('S', 'B') else b''
        pause = b'\x13' if resume else b''
        case = dict(name='carrier'+flow, source=source, hex=serial.compile_source(source).hex(),
                    serial=dict(input_hex=b'ENDTRAIL'.hex(), send_after_tx_hex=(resume+b'UP').hex()),
                    expected=dict(tx_hex=(resume+b'UPDONE\r'+pause).hex(),
                                  stdout_hex='', returned_hex=b'TRAIL'.hex()))
        cases.append((flow, case))
    start = 'proc main\nexecute "NEXT.ASP"\ntransmit "BAD"\nendproc\n'
    cases.append(('N', dict(cases[0][1], name='carriernested', source=start,
                           hex=serial.compile_source(start).hex(), source_scripts={'NEXT.ASP': source})))
    out.mkdir()
    (out/'predictions.json').write_text(json.dumps(cases, indent=2)+'\n')
    for flow, case in cases:
        driver = serial.build_driver(out/('driver'+flow), flow)
        result = serial.run(case, binary, out, driver)
        if case.get('source_scripts'):
            assert (out/case['name']/'NEXT.ASX').read_bytes() == serial.compile_source(source)
        results.append(result)
    report = dict(passed=all(r['passed'] for r in results), cases=results,
                  runner_sha256=serial.sha(binary), compiler_sha256=serial.sha(serial.COMPILER),
                  checker_sha256=serial.sha(Path(__file__)),
                  reused_checker_sha256=serial.sha(Path(serial.__file__)), original_inputs=[],
                  scope='Actual8086 DOS production UART, N/S/H/B flow, raw128/integer/long/comparison, '
                  'exact unread ASIO return and hardware restoration; one real nested DOS compilation. '
                  'DOSBox nullmodem holds DCD high. Low/drop semantics tested separately with declared '
                  'CPU IO/diagnostic models; no analog modem, SIP or physical BBS claim.')
    (out/'checks.json').write_text(json.dumps(report, indent=2)+'\n')
    assert report['passed'], [(r['name'], r['checks']) for r in results if not r['passed']]


if __name__ == '__main__':
    main()
