#!/usr/bin/env python3
"""Freeze sanitized original-compiler flow evidence; not a maintained compiler."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    ledger_path = ROOT/'analysis/aspect-vm-runtime/control-ledger/summary.json'
    ledger = json.loads(ledger_path.read_text())
    assert sha(ROOT/'standalone/aspect_flow_probe.py') == ledger['final_harness_sha256']
    count = accepted = 0
    for run in ledger['runs']:
        path = ROOT/run['path']
        assert sha(path) == run['report_sha256']
        report = json.loads(path.read_text())
        assert report['compiler_sha256'] == ledger['compiler_sha256']
        assert report['harness_sha256'] == run['recorded_harness_sha256']
        assert len(report['cases']) == run['cases']
        assert sum(c['success'] for c in report['cases']) == run['accepted']
        count += run['cases']; accepted += run['accepted']
    assert count == ledger['total_cases'] == 72 and accepted == ledger['accepted'] == 49
    assert len(ledger['cases']) == count
    records = [{k: v for k, v in case.items() if k != 'errors'} for case in ledger['cases']]
    result = dict(compiler_sha256=ledger['compiler_sha256'], total_cases=count, accepted=accepted,
        rejected=count-accepted, historical_runs=ledger['runs'], cases=records,
        observations=ledger['observations'], observed_address_fields=ledger['observed_address_fields'],
        limits=ledger['limits'], private_ledger_sha256=sha(ledger_path),
        sources={p: sha(ROOT/p) for p in ('standalone/aspect_flow_probe.py',
                                          'standalone/record_aspect_flow.py')})
    out = ROOT/'docs/validation/aspect-flow.json'
    out.write_text(json.dumps(result, indent=2)+'\n')
    print(f'Recorded72 compiler probes (49 accepted,23 rejected): {out.relative_to(ROOT)}')

if __name__ == '__main__':
    main()
