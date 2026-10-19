#!/usr/bin/env python3
"""Native nonzero TXPACE/caret/pause/duplex through an actual DOS UART lease."""
import argparse
import json
import re
from pathlib import Path
import test_aspect_script_serial_dos as serial

ROOT = serial.ROOT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label', required=True)
    parser.add_argument('--runner-sha256', required=True)
    args = parser.parse_args()
    assert re.fullmatch(r'[A-Za-z0-9_-]+', args.label)
    binary = ROOT / 'build/aspect-runner/ASPECT.EXE'
    assert serial.sha(binary) == args.runner_sha256
    fixture = ROOT / 'standalone/fixtures/aspect_set_runtime_vectors.json'
    cases = [c for c in json.loads(fixture.read_text())['vectors'] if c.get('serial')]
    assert len(cases) == 6
    output = ROOT / 'build/aspect-set-serial-dos' / args.label
    output.mkdir(parents=True, exist_ok=False)
    # Expectations and exact compiler outputs are frozen before DOS execution.
    for case in cases:
        assert serial.compile_source(case['source']) == bytes.fromhex(case['hex'])
    (output/'predictions.json').write_text(json.dumps(cases, indent=2)+'\n')
    driver = serial.build_driver(output)
    results = [serial.run(c, binary, output, driver) for c in cases]
    assert serial.sha(binary) == args.runner_sha256
    report = dict(passed=all(c['passed'] for c in results), cases=results,
                  runner_sha256=args.runner_sha256, checker_sha256=serial.sha(Path(__file__)),
                  reused_checker_sha256=serial.sha(Path(serial.__file__)),
                  fixture_sha256=serial.sha(fixture), original_inputs=[],
                  scope='Actual DOS native WAITCASE matching and TRANSMIT with nonzero TXPACE, NUL sentinel bypass, '
                  'pause-character suppression and HALF echo through COM1/38400/8N1/flowN. '
                  'Exact wire/stdout, unread return and IRQ/PIC/MCR/guards checked. '
                  'Timing belongs to separate calibration component evidence; no physical modem claim.')
    (output/'checks.json').write_text(json.dumps(report, indent=2)+'\n')
    assert report['passed']
    print('Native SET/UART:', len(results), 'cases PASS')


if __name__ == '__main__':
    main()
