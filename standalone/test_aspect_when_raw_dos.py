#!/usr/bin/env python3
"""Actual UART idle matching versus unread preservation without a renderer."""
import argparse
import hashlib
import json
from pathlib import Path
import types
import test_aspect_script_serial_dos as serial

ROOT = serial.ROOT


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label', required=True)
    args = parser.parse_args()
    assert args.label and all(c.isalnum() or c in '-_' for c in args.label)
    out = ROOT / 'build/aspect-when-raw-dos' / args.label
    out.mkdir(parents=True, exist_ok=False)
    # Keep the real ASIOv1 parent, UART sampler and exact handback assertions.
    # Only choose each authored expected suffix instead of SWHIT's old literal.
    text = Path(serial.__file__).read_text()
    old = "intended_return = b'TRAIL' if case['name'] == 'SWHIT' else b''"
    assert text.count(old) == 1
    text = text.replace(old, "intended_return = bytes.fromhex(model.get('return_hex', ''))")
    harness = types.ModuleType('when_raw_serial_harness')
    harness.__file__ = serial.__file__
    exec(compile(text, serial.__file__, 'exec'), harness.__dict__)
    worker = 'proc worker\ntransmit "EVENT"\nendproc\n'
    ready = 'transmit "READY"\npause 1\n'
    after = 'transmit "AFTER"\nendproc\n'
    cases = []
    for name, setup, body, handlers, incoming, outgoing, returned in (
        ('RAWIDLECALL', 'when 0 "A" call worker\n', ready, worker, b'A', b'READYEVENTAFTER', b''),
        ('RAWIDLETX', 'when 0 "A" transmit "EVENT"\n', ready, '', b'A', b'READYEVENTAFTER', b''),
        ('RAWKEEP', '', ready, '', b'RAW', b'READYAFTER', b'RAW'),
        ('RAWCANCEL', 'when 0 "A" transmit "BAD"\ncwhen 0\n', ready, '', b'RAW', b'READYAFTER', b'RAW'),
        ('RAWWAITFRAME', 'when 0 "A" call worker\n', 'transmit "READY"\nwaitfor "END" 5\n',
         worker.replace('proc worker\n', 'proc worker\ninteger local_value\nlocal_value = 37\n'), b'AEND', b'READYEVENTAFTER', b''),
    ):
        source = 'proc main\n' + setup + body + after + handlers
        wire = serial.compile_source(source)
        cases.append(dict(name=name, source=source, hex=wire.hex(),
                          serial=dict(input_hex=incoming.hex(), send_after_tx_hex=b'READY'.hex(), return_hex=returned.hex()),
                          expected=dict(tx_hex=outgoing.hex(), stdout_hex='')))
    binary = ROOT / 'build/aspect-runner/ASPECT.EXE'
    manifest = binary.parent / 'manifest.json'
    inputs = [Path(__file__), Path(serial.__file__), binary, manifest, ROOT / 'src/aspect/compiler.py']
    hashes = {str(p.relative_to(ROOT)): sha(p) for p in inputs}
    (out / 'predictions.json').write_text(json.dumps(dict(inputs=hashes, cases=cases), indent=2) + '\n')
    driver = harness.build_driver(out)
    results = [harness.run(case, binary, out, driver) for case in cases]
    assert hashes == {str(p.relative_to(ROOT)): sha(p) for p in inputs}
    report = dict(passed=all(r['passed'] for r in results), cases=results, original_inputs=[],
                  checker_sha256=sha(Path(__file__)), runner_sha256=sha(binary), inputs=hashes,
                  predictions_sha256=sha(out / 'predictions.json'),
                  scope='Five actual DOS ASIOv1 raw-backend cases with native COM1/38400/8N1/N and independent READY-gated peer. Active WHEN consumes and matches between ordinary commands; no renderer/pattern owner preserves exact raw suffixes, including after CWHEN. C8 executes with real FILE/frame ownership. No terminal engine or physical modem claim.')
    (out / 'checks.json').write_text(json.dumps(report, indent=2) + '\n')
    assert report['passed']
    print('WHEN raw backend: five actual UART cases pass')


if __name__ == '__main__':
    main()
