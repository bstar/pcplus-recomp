#!/usr/bin/env python3
"""Reject altered copies of an actual owned ENiGMA multiline draft capture."""
import argparse
import json
from pathlib import Path
from enigma_multiline import editor_checks
from product_inputs import ROOT, sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    capture, output = args.capture.resolve(), args.output.resolve()
    assert capture.is_relative_to(ROOT / 'build')
    assert output.is_relative_to(ROOT / 'build') and not output.exists()
    producer = json.loads((capture / 'proxy-integration.json').read_text())
    assert producer['passed'] and producer['multiline_editor']['mode'] == 'page-down'
    tx = (capture / 'serial-received.bin').read_bytes()
    display = (capture / 'display.bin').read_bytes()
    video = (capture / 'SCREEN.BIN').read_bytes()
    damaged = bytearray(video)
    # Row11 is the top-page edit retained in the final page-down viewport.
    assert damaged[10*160] == ord('U')
    damaged[10*160] = ord('X')
    output.mkdir(parents=True)
    reports = []
    for label, wire, screen, stream, reject in [
        ('unchanged', tx, video, display, None),
        ('missing-pageup', tx.replace(b'\x1b[5~', b''), video, display, 'real_page_up'),
        ('missing-pagedown', tx.replace(b'\x1b[6~', b''), video, display, 'real_page_down'),
        ('missing-line24', tx.replace(b'R24\r', b''), video, display, 'all24_lines_sent'),
        ('changed-body', tx, damaged, display, 'exact_numbered_body_window'),
        ('wrong-document-row', tx, video, display.replace(b'25,01', b'24,01'), 'real_page_up'),
    ]:
        folder = output / label
        folder.mkdir()
        for filename, data in [('SCREEN.BIN', screen), ('serial-received.bin', wire), ('display.bin', stream)]:
            (folder / filename).write_bytes(data)
        checks, _ = editor_checks(folder, wire, stream, 'page-down')
        passed = not checks[reject] if reject else all(checks.values())
        reports.append(dict(case=label, passed=passed, rejected=not all(checks.values()),
            checks=checks, files={p.name: sha(p) for p in folder.iterdir()}))
    result = dict(passed=all(r['passed'] for r in reports), cases=reports,
        original_captures={str(p.relative_to(ROOT)): sha(p) for p in
            [capture / name for name in ['proxy-integration.json', 'SCREEN.BIN', 'serial-received.bin', 'display.bin']]},
        sources={name: sha(ROOT / name) for name in ['lab/bbs/check_enigma_multiline_controls.py', 'lab/bbs/enigma_multiline.py']},
        scope=__doc__ + ' Declared copied-artifact mutations only; never execute DOS or send bytes to a server. '
            'Unchanged acceptance and five rejected counterexamples validate semantics, not whole-cell rendering.')
    (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print('PASS' if result['passed'] else 'FAIL', len(reports), 'multiline semantic controls')
    assert result['passed']


if __name__ == '__main__':
    main()
