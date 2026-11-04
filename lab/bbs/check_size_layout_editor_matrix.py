#!/usr/bin/env python3
"""Verify complete paired BBS layout evidence and every linked source/capture hash."""
import argparse
import json
from pathlib import Path
from product_inputs import ROOT, sha


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    run, out = a.run.resolve(), a.output.resolve()
    assert run.is_relative_to(ROOT / 'build') and out.is_relative_to(ROOT / 'build')
    out.mkdir(parents=True, exist_ok=False)
    report = json.loads((run / 'result.json').read_text())
    assert report['passed']
    for name, digest in report['sources'].items():
        assert sha(ROOT / name) == digest, name
    for name,digest in report.get('accepted_case_inputs',{}).items():
        assert sha(ROOT/name)==digest,name
    runtime = ROOT / report['runtime']
    for name, digest in report['runtime_hashes'].items():
        assert sha(runtime / name) == digest, name
    assert len(report['cases']) == 16
    expected = {(peer, rows, hidden) for peer in ('enigma', 'synchronet')
                for rows in (25,28,43,50) for hidden in (0,1)}
    assert {(c['peer'], c['physical_rows'], c['status_hidden']) for c in report['cases']} == expected
    cases = []
    for case in report['cases']:
        capture, bridge = ROOT / case['capture'], ROOT / case['bridge']
        path = ROOT / case['audit_path']
        assert path == capture / 'size-probe-screen-audit.json' and sha(path) == case['audit_sha256']
        audit = json.loads(path.read_text())
        logical = case['physical_rows'] - (not case['status_hidden'])
        assert audit['passed'] and case['passed'] and audit['different_cells'] == 0
        assert audit['matched_cells'] == logical * 80 and audit['logical_rows'] == logical
        assert audit['NAWS'] == [[80, logical]] and audit['size_metadata_not_forwarded']
        assert audit['binary_sha256'] == report['terminal_sha256']
        for filename in ('size-probe-screen-audit.json', 'screen-reference-audit.json', 'proxy-integration.json'):
            record = json.loads((capture / filename).read_text())
            assert record['passed']
            for group in ('sources', 'product_inputs'):
                for name, digest in record.get(group, {}).items():
                    assert sha(ROOT / name) == digest, name
            for name, digest in record.get('captures', {}).items():
                path = Path(name)
                assert sha(path if path.is_absolute() else ROOT / path) == digest, name
        base = json.loads((capture / 'result.json').read_text())
        assert base['passed'] and base['cpu'] == '8086'
        assert base['serial']['com'] == 3 and base['serial']['irq'] == 5
        producer = json.loads((capture / 'proxy-integration.json').read_text())
        if case['peer'] == 'synchronet':
            assert producer['interpreter_sha256'] == report['interpreter_sha256']
            for name in ('server_static_inputs_unchanged', 'message_bodies_unchanged',
                         'no_message_mail_or_transfer_writes', 'actual_ASPECT_login', 'draft_aborted'):
                assert producer['checks'][name], name
        else:
            semantic = json.loads((capture / 'semantic-audit.json').read_text())
            assert semantic['passed'] and semantic['checks']['no_post_saved']
        # Capture geometry observer and screen sampler identities are already
        # bound by the cell audit; include independent hardware restoration too.
        before = (capture / 'BEFORE.BIN').read_bytes()
        assert len(before) == 42 and before == (capture / 'AFTER.BIN').read_bytes()
        assert len((capture / 'SCREEN.BIN').read_bytes()) == 8000
        ready = json.loads((bridge / 'ready.json').read_text())
        assert ready['terminalSizeProbe'] and ready['terminalRows'] == logical
        cases.append(dict(peer=case['peer'], physical_rows=case['physical_rows'],
                          status_hidden=case['status_hidden'], logical_rows=logical,
                          matched_cells=logical*80, different_cells=0, passed=True))
    assert sum(c['matched_cells'] for c in cases) == 46080
    result = dict(passed=True, DOS_workflows=16, matched_cells=46080, different_cells=0,
                  cases=cases, terminal_sha256=report['terminal_sha256'],
                  interpreter_sha256=report['interpreter_sha256'], report_sha256=sha(run / 'result.json'),
                  sources={str(Path(__file__).relative_to(ROOT)): sha(Path(__file__))},
                  scope=__doc__ + ' Consistency/source/capture audit of actual paired geometry/cell/wire runs. It does not turn paced final-frame evidence into physical, every-frame, custom-menu or transfer acceptance.')
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print('PASS complete paired layout matrix:16 DOS workflows/46080 cells')


if __name__ == '__main__':
    main()
