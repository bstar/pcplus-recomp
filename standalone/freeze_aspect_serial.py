#!/usr/bin/env python3
"""Freeze authored serial scripts and native-derived predictions before execution."""
import json
from pathlib import Path
from aspect_serial_probe import ROOT, COMPILER, corpus, sha

REPORT = 'analysis/aspect-serial/compiler-04/report.json'
REPORT_SHA = '640274fd65c0f55ae9ec91060cf197a029d3f2c858c4e6279ce31166ad76b0cc'


def main():
    raw = (ROOT / REPORT).read_bytes()
    assert sha(raw) == REPORT_SHA
    report = json.loads(raw)
    assert report['compiler_sha256'] == COMPILER
    assert report['harness_sha256'] == sha((ROOT / 'standalone/aspect_serial_probe.py').read_bytes())
    authored = corpus()
    accepted = [case for case in report['cases'] if case['success']]
    rejected = [case for case in report['cases'] if not case['success']]
    assert len(report['cases']) == 37 and len(accepted) == 32 and len(rejected) == 5
    vectors, compiler_only = [], []
    for case in accepted:
        prediction = authored[case['name']]
        assert prediction['source'] == case['source'] and prediction['expected'] is not None
        assert sha(case['source'].encode('cp437')) == case['source_sha256']
        assert sha(bytes.fromhex(case['hex'])) == case['asx_sha256']
        vector = {key: case[key] for key in ('name', 'source', 'source_sha256', 'hex', 'asx_sha256')}
        vector.update(source_encoding='cp437', expected=prediction['expected'])
        if 'compiler_only_reason' in prediction:
            vector.update(dos_excluded=True, dos_excluded_reason=prediction['compiler_only_reason'])
            compiler_only.append(vector)
        else:
            vector.update(serial=prediction['serial'], dos_excluded=False)
            vectors.append(vector)
    assert len(vectors) == 30 and len(compiler_only) == 2
    result = dict(
        compiler_sha256=COMPILER, private_report=REPORT, private_report_sha256=sha(raw),
        probe_sha256=report['harness_sha256'], freezer_sha256=sha(Path(__file__).read_bytes()),
        source_encoding='cp437', vectors=vectors, compiler_only=compiler_only,
        rejected=[{key: case[key] for key in ('name', 'source', 'source_sha256', 'errors')} for case in rejected],
        expectation_model='Explicit authored predictions fixed before maintained VM/UART execution. '
        'Native TRANSMIT interprets caret controls, ^@ wireNUL, ^^ wire1E, and consumes default pausechar~ as10BIOS transitions. '
        'WAITFOR matches ASCII-insensitively by default, builtin28 reads nativeE39A (1match/0timeout), '
        'omitted timeout30seconds, FOREVER enum1A indefinite; numeric0 faults native1, positive timeout18BIOS ticks per second with day wrap. '
        'Its mismatch restart only retains a matching first character, so ABABAAB misses ABAAB. '
        'Empty needle with no queued RX immediately succeeds. '
        'SWSTRICT explicitly models case_sensitive backend state; SWMID models BIOS midnight. '
        'Neither is claimed as a production source setting or wall-clock DOS test.',
        superseded=dict(corpus_sha256='322c63d9aea6ac1f0f7a365f129ab47bc21077e9dc061936c60c22aab4c67f8f', reason='Initial timeout0 prediction was wrong: corrected static E9F5 recovery distinguishes numeric0 native1 from FOREVER enum1A. Prior32 sources preserved; failed composed evidence retained in build/aspect-runtime/serial-failed-01.txt/json.'),
        scope='37 authored original compiler cases,32 accepted5 rejected;30 bounded runtime vectors2 compiler-only waits. '
        'Independent actual DOS nullmodem peer eligibility recorded per vector; no physical-modem or complete PCPlus claim.')
    output = ROOT / 'standalone/fixtures/aspect_serial_vectors.json'
    output.write_text(json.dumps(result, indent=2) + '\n')
    print(output.relative_to(ROOT), sha(output.read_bytes()))


if __name__ == '__main__':
    main()
