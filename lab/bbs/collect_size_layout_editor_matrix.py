#!/usr/bin/env python3
"""Collect complete accepted per-case runs, preserving failed suite attempts.

An interrupted/failed suite is not treated as passing. Every selected case must
have its own successful producer and independent audit with current sources.
"""
import argparse
import json
from pathlib import Path
from product_inputs import ROOT, select_product, sha


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--case-run', type=Path, action='append', required=True)
    p.add_argument('--runtime', type=Path, required=True)
    p.add_argument('--terminal', type=Path, required=True)
    p.add_argument('--runner', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    out, runtime = a.output.resolve(), a.runtime.resolve()
    assert out.is_relative_to(ROOT / 'build') and runtime.is_relative_to(ROOT / 'build')
    assert not out.exists()
    binary, source_files = select_product(a.terminal, 'TERMINAL.EXE')
    child, child_files = select_product(a.runner, 'ASPECT.EXE')
    sources = {str(n.relative_to(ROOT)): sha(n) for n in source_files + child_files}
    sources[str(Path(__file__).relative_to(ROOT))] = sha(Path(__file__))
    cases, inputs = [], {}
    for folder in a.case_run:
        folder = folder.resolve()
        assert folder.is_relative_to(ROOT / 'build')
        for path in sorted(folder.glob('*-accepted.json')):
            case = json.loads(path.read_text())
            assert case['passed']
            audit_path = ROOT / case['audit_path']
            assert sha(audit_path) == case['audit_sha256']
            capture = ROOT / case['capture']
            for filename in ('proxy-integration.json', 'screen-reference-audit.json', 'size-probe-screen-audit.json'):
                record = json.loads((capture / filename).read_text())
                assert record['passed'] and record['binary_sha256'] == sha(binary)
                for group in ('sources', 'product_inputs'):
                    for name, digest in record.get(group, {}).items():
                        assert sha(ROOT / name) == digest, name
                        if name in sources:
                            assert sources[name] == digest
                        sources[name] = digest
            if case['peer'] == 'synchronet':
                assert json.loads((capture / 'proxy-integration.json').read_text())['interpreter_sha256'] == sha(child)
            ready = json.loads((ROOT / case['bridge'] / 'ready.json').read_text())
            for name, digest in ready['installed_sources'].items():
                assert sha(runtime / name) == digest, name
            cases.append(case)
            inputs[str(path.relative_to(ROOT))] = sha(path)
    expected = {(peer, rows, hidden) for peer in ('enigma', 'synchronet')
                for rows in (25,28,43,50) for hidden in (0,1)}
    assert len(cases) == 16
    assert {(c['peer'], c['physical_rows'], c['status_hidden']) for c in cases} == expected
    out.mkdir(parents=True)
    result = dict(passed=True, cases=cases, sources=sources, runtime=str(runtime.relative_to(ROOT)),
                  runtime_hashes={str(n.relative_to(runtime)): sha(n) for n in runtime.rglob('*') if n.is_file()},
                  terminal_sha256=sha(binary), interpreter_sha256=sha(child),
                  accepted_case_inputs=inputs, scope=__doc__)
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print('Collected16 independently accepted cases; run the complete-matrix checker next')


if __name__ == '__main__':
    main()
