#!/usr/bin/env python3
"""Freeze authored console grammar and pre-execution native-source predictions."""
import json
from pathlib import Path
from aspect_console_probe import ROOT, COMPILER, corpus, sha

REPORT = 'analysis/aspect-console/compiler-03/report.json'
REPORT_SHA = '861a18a27b64f83362da43251378c07426e1cfe537927233821457e4273feba3'


def main():
    raw = (ROOT / REPORT).read_bytes()
    assert sha(raw) == REPORT_SHA
    report = json.loads(raw)
    assert report['compiler_sha256'] == COMPILER
    assert report['harness_sha256'] == sha((ROOT / 'standalone/aspect_console_probe.py').read_bytes())
    authored = corpus()
    accepted = [case for case in report['cases'] if case['success']]
    rejected = [case for case in report['cases'] if not case['success']]
    assert len(report['cases']) == 55 and len(accepted) == 33 and len(rejected) == 22
    vectors, compiler_only = [], []
    for case in accepted:
        prediction = authored[case['name']]
        assert prediction['source'] == case['source'] and prediction['expected'] is not None
        assert sha(case['source'].encode('cp437')) == case['source_sha256']
        assert sha(bytes.fromhex(case['hex'])) == case['asx_sha256']
        vector = {key: case[key] for key in ('name', 'source', 'source_sha256', 'hex', 'asx_sha256')}
        vector.update(source_encoding='cp437', expected=prediction['expected'])
        if 'dos_excluded_reason' in prediction:
            vector.update(dos_excluded=True, dos_excluded_reason=prediction['dos_excluded_reason'])
            compiler_only.append(vector)
        else:
            vector['dos_excluded'] = False
            vectors.append(vector)
    assert len(vectors) == 30 and len(compiler_only) == 3
    result = dict(
        compiler_sha256=COMPILER, private_report=REPORT, private_report_sha256=sha(raw),
        probe_sha256=report['harness_sha256'], freezer_sha256=sha(Path(__file__).read_bytes()),
        source_encoding='cp437', vectors=vectors, compiler_only=compiler_only,
        rejected=[{key: case[key] for key in ('name', 'source', 'source_sha256', 'errors')} for case in rejected],
        expectation_model='Predictions fixed in authored probe before composed VM execution. '
        'MESSAGE native4934 caret decoder then default CRLF (overlay02 D6EA resets E38A=1); '
        'EXIT native state1 terminates the script successfully, including caller continuations. '
        'PAUSE bounded integer read rejects negative values with native1; positive long delays excluded from DOS tests. '
        'TRANSMIT/WAITFOR have grammar evidence only, expect explicit unsupported stop. '
        'RSTRCMP uses unsigned raw-byte comparison, default count80, with fresh zeroed scratch backing; '
        'count81 faults native1. Status values are -1/0/1 as 16-bit words.',
        native_evidence=['analysis/aspect-expression/rea-console-defaults-01.json '
                         'ev_7f2a37333c76fe8f326ecc36a6ef20a640284f710c20b9e47a19c3288aa55d92',
                         'Recovered string_commands.asm EF00..EF1D and string_operands.asm EEF0..EEFF'],
        scope='55 authored compiler cases:33 accepted,22 rejected;30 runtime vectors and3 compiler-only long-delay cases. '
        'Prior compiler01/02 failures retained privately. No complete console, timer or serial-service claim.')
    output = ROOT / 'standalone/fixtures/aspect_console_vectors.json'
    output.write_text(json.dumps(result, indent=2) + '\n')
    print(output.relative_to(ROOT), sha(output.read_bytes()))


if __name__ == '__main__':
    main()
