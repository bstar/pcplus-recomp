#!/usr/bin/env python3
"""Freeze authored SET sources and original compiler outcomes, never binaries."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = 'analysis/aspect-set/compiler-01/report.json'
REPORT_SHA = 'c91a54f042a0063c1247d8f29c0e2e87eb16832b80dc837d8fdce38b5e513dd3'
PROBE_SHA = 'ebc530096a4b039e5047c37ecd9cf01bc3a814e43c0e928e19128fbfcb59c9c7'
FOLLOWUP = 'analysis/aspect-set/compiler-02/report.json'
FOLLOWUP_SHA = '8a34594b30bca7d839786bcf9a51d3f0066809a25a4ad5e33463aa7dffcfa350'
FOLLOWUP_PROBE_SHA = '766756b0bdd908de476ff57963da385f05db10180f942147c5a35c3052e9919d'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    raw = (ROOT / REPORT).read_bytes()
    assert sha(raw) == REPORT_SHA
    report = json.loads(raw)
    assert report['harness_sha256'] == PROBE_SHA
    assert sha((ROOT / 'analysis/aspect-set/compiler-probe.py').read_bytes()) == PROBE_SHA
    assert report['compiler_sha256'] == '5664fdfae375774da5303cc8b53c00ef773a6650132de73c7206e46ddc05039a'
    assert len(report['cases']) == 36
    followup_raw = (ROOT / FOLLOWUP).read_bytes()
    assert sha(followup_raw) == FOLLOWUP_SHA
    followup = json.loads(followup_raw)
    assert followup['compiler_sha256'] == report['compiler_sha256']
    assert followup['harness_sha256'] == FOLLOWUP_PROBE_SHA
    assert sha((ROOT / 'analysis/aspect-set/numeric-grammar-probe.py').read_bytes()) == FOLLOWUP_PROBE_SHA
    assert len(followup['cases']) == 16
    accepted, rejected = [], []
    for case in report['cases'] + followup['cases']:
        assert sha(case['source'].encode('cp437')) == case['source_sha256']
        vector = {key: case[key] for key in ('name', 'label', 'source', 'source_sha256')}
        if case['success']:
            assert sha(bytes.fromhex(case['hex'])) == case['asx_sha256']
            vector.update(hex=case['hex'], asx_sha256=case['asx_sha256'])
            accepted.append(vector)
        else:
            vector['errors'] = case['errors']
            rejected.append(vector)
    assert len(accepted) == 33 and len(rejected) == 19
    result = dict(schema='aspect-set-compiler-v1', compiler_sha256=report['compiler_sha256'],
                  private_report=REPORT, private_report_sha256=REPORT_SHA,
                  private_probe_sha256=PROBE_SHA, freezer_sha256=sha(Path(__file__).read_bytes()),
                  private_followup_report=FOLLOWUP, private_followup_report_sha256=FOLLOWUP_SHA,
                  private_followup_probe_sha256=FOLLOWUP_PROBE_SHA,
                  source_encoding='cp437', vectors=accepted, rejected=rejected,
                  scope='Selected SET source grammar/encoding only. This corpus does not establish runtime support or complete SET/compiler coverage.')
    out = ROOT / 'standalone/fixtures/aspect_set_compiler_vectors.json'
    out.write_text(json.dumps(result, indent=2) + '\n')
    print(out.relative_to(ROOT))


if __name__ == '__main__':
    main()
