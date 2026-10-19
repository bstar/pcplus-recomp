#!/usr/bin/env python3
"""Freeze compiler-proven receive grammar and independent native-source predictions."""
import json
from pathlib import Path
from aspect_receive_probe import ROOT, COMPILER, corpus, sha

REPORT = 'analysis/aspect-receive/compiler-04/report.json'
REPORT_SHA = '06e0e102f9007d02032307b2278d0b0547f74e85769220caceb6d11e49987c14'


def main():
    raw = (ROOT / REPORT).read_bytes()
    assert sha(raw) == REPORT_SHA
    report = json.loads(raw)
    assert report['compiler_sha256'] == COMPILER
    assert report['harness_sha256'] == sha((ROOT / 'standalone/aspect_receive_probe.py').read_bytes())
    authored = corpus()
    accepted = [case for case in report['cases'] if case['success']]
    rejected = [case for case in report['cases'] if not case['success']]
    assert len(report['cases']) == 91 and len(accepted) == 56 and len(rejected) == 35
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
    assert len(vectors) == 54 and len(compiler_only) == 2
    result = dict(
        compiler_sha256=COMPILER, private_report=REPORT, private_report_sha256=sha(raw),
        probe_sha256=report['harness_sha256'], freezer_sha256=sha(Path(__file__).read_bytes()),
        source_encoding='cp437', vectors=vectors, compiler_only=compiler_only,
        rejected=[{key: case[key] for key in ('name', 'source', 'source_sha256', 'errors')} for case in rejected],
        expectation_model='Authored predictions fixed before composed VM execution from retained native contracts. '
        'COMGETC immediatebyte/FFFF and COMGETCD <=36 observed BIOS lowword transitions; '
        'loaderD770 incrementsE382 afterD6EAreset, so effective display1/suppress1 means no default COMbyte echo. '
        'RGET max80/defaulttimeout30, timeout0 skipsloop/failure1, max0 pointer-limit quirk retained for safe empty case; '
        'CR terminates without storing CR, maxfull and CR completion setfailure0, timeoutfailure1. '
        'RGET binary bytes behindNUL independently exposed viaSTRPEEK; COMDATA reports remaining bytes. '
        'WAITQUIET defaultsquiet15,total30; numericquiet0 skipsloop/success; total0/negative faults native1; '
        'inputdrain resetsquiet, total continues, quiet completion wins simultaneous expiration. '
        'RGET bothoptions and WAITQUIET quiet FOREVER use genericbuiltin22=1; WAITQUIET total and WAITFOR timeout use specialenum1A indefinite. '
        'RGET DOS-seconds models use seconds_step0 for queued data and1 for timeouts; RGWRAP begins59. '
        'RX/clock fixtures are explicit diagnostic platform inputs, not physical modem timing or a production source setting.',
        native_evidence=['analysis/aspect-expression/rea-receive-01.json: resident50C7,52D0,6BB6',
                         'analysis/aspect-expression/rea-receive-03.json:5440,5431,5438,DD68',
                         'analysis/aspect-expression/rea-receive-04.json:FOREVER22 DA10 MOVAX1RET;COMDATA20 DA08;FOUND23 DA14',
                         'Native loaderD6EA+D770 effective echo-suppression lifetime, independently traced by root.'],
        superseded=dict(corpus_sha256='cbc087b560986b4dfb2cbdfad9b8191f662eee1fececb1e06d75a30c61b2a7c9', reason='Maintained compiler byte comparison caught WAITQUIET totalFOREVER specialenum1A before composedexecution; initial model explanation overgeneralized genericFOREVER. Existing expected values unchanged, newWQFSTRM differentiates indefinite total.'),
        scope='91 original compiler attempts56 accepted35 rejected;54 bounded modeled-serial runtime vectors2 compiler-only. '
        'Rejected reservedWAIT variable attempt and initial grammar attempts retained in compiler01/02 privately. '
        'No composed runtime outcomes inform these predictions; no whole compiler, renderer, event/capture or physical-modem claim.')
    output = ROOT / 'standalone/fixtures/aspect_receive_vectors.json'
    output.write_text(json.dumps(result, indent=2) + '\n')
    print(output.relative_to(ROOT), sha(output.read_bytes()))


if __name__ == '__main__':
    main()
