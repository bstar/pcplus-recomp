#!/usr/bin/env python3
"""Independently audit raw DOS trap witnesses, not only runner pass flags."""
import argparse
import hashlib
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('keyboard_label')
    parser.add_argument('mouse_label')
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--normal-keyboard', required=True)
    parser.add_argument('--normal-mouse', required=True)
    parser.add_argument('--mouse-owners', required=True)
    parser.add_argument('--source-label', required=True)
    args = parser.parse_args()
    evidence = []
    for mouse, label in [(False, args.keyboard_label), (True, args.mouse_label)]:
        assert Path(label).name == label
        folder = ROOT / 'build/terminal-trap-tests' / label
        report = json.loads((folder / 'result.json').read_text())
        assert report['passed'] and len(report['cases']) == 10
        for name, digest in report['sources'].items():
            assert sha(ROOT / name) == digest, name
            assert sha(folder / 'sources' / name) == digest, name
        assert {c['case'] for c in report['cases']} == {str(m)+str(b) for m in range(5) for b in range(2)}
        for case in report['cases']:
            mode, initial = case['mode'], case['initial_break']
            assert case['mouse'] == mouse and case['passed'] and all(case['checks'].values())
            run = folder / case['case']
            r = struct.unpack('<31H', (run / 'TRAPWIT.BIN').read_bytes())
            child = struct.unpack('<11H', (run / 'CHILTRAP.BIN').read_bytes())
            assert r[0:2] == (0x5452, mode) and r[2] != 0
            assert r[3] == (4 if mode == 4 else 0) and r[5] == 0
            assert r[4] == (2 if mode == 3 else 1 if mode in [1, 2] else 0)
            assert r[6] == initial and r[7] == (0 if mode == 4 else initial)
            assert r[10] == (0 if mode == 0 else 1) and r[30] == 1
            assert child[:4] == (0x4354, r[2], 2, 0)
            assert child[4:10] == r[12:18] and child[10] == initial
            if mode != 4:
                assert r[12:18] == r[18:24]
            else:
                assert r[18:20] == r[24:26] and r[28] == 0 and r[29] > 0
            if mode == 2:
                assert r[11] & 255 == 3
            if mode == 3:
                assert (r[8], r[9], r[11]) == (0x0801, 12, 0x0803)
            assert sha(run / 'TERMINAL.EXE') == case['child_sha256']
            assert sha(run / 'TROBS.EXE') == case['parent_sha256']
            assert sha(run / 'PRMEDIT.EXE') == case['startup_child_sha256']
            evidence.append(dict(mouse=mouse, case=case['case'],
                result=str((run / 'result.json').relative_to(ROOT)),
                files={n:sha(run / n) for n in ['result.json', 'TRAPWIT.BIN', 'CHILTRAP.BIN', 'TRAPPAR.OUT']},
                terminal_sha256=case['child_sha256']))
    model = ROOT / 'build/terminal-traps-mouse/trap-model.json'
    modeled = json.loads(model.read_text())
    assert modeled['passed']
    assert modeled['checker_sha256'] == sha(ROOT / 'standalone/check_terminal_traps.py')
    assert modeled['binary_sha256'] == sha(model.parent / 'TERMINAL.EXE')
    regressions = []
    selections = [
        ('aspect-parent-break-guarded-banked-traps', args.normal_keyboard, 'result.json', 13),
        ('aspect-parent-break-mouse-guarded-banked-traps', args.normal_mouse, 'result.json', 13),
        ('terminal-mouse-tests', args.mouse_owners, 'checks.json', 4),
    ]
    for base, label, filename, count in selections:
        assert Path(label).name == label
        path = ROOT / 'build' / base / label / filename
        receipt = json.loads(path.read_text())
        assert receipt['passed'] and len(receipt['cases']) == count
        for case in receipt['cases']:
            assert case['passed'] and all(case['checks'].values())
        for n, h in receipt.get('source_hashes', receipt.get('sources', {})).items():
            assert sha(ROOT / n) == h, n
        regressions.append(dict(receipt=str(path.relative_to(ROOT)), sha256=sha(path), cases=count,
            assertions=sum(len(case['checks']) for case in receipt['cases'])))
    assert Path(args.source_label).name == args.source_label
    source_path = ROOT / 'build/terminal-traps-source' / args.source_label / 'result.json'
    proof = json.loads(source_path.read_text())
    assert proof['passed'] and len(proof['products']) == 18 and proof['original_inputs'] == []
    for n, h in proof['sources'].items():
        assert sha(ROOT / n) == h, n
    assert all(v['actual'] == v['expected'] for v in proof['products'].values())
    assert proof['checker_sha256'] == sha(ROOT / 'standalone/check_terminal_traps_source.py')
    output = dict(passed=True, actual_DOS_cases=len(evidence), cases=evidence,
        linked_model=modeled, linked_model_receipt_sha256=sha(model),
        regressions=regressions, source_products=proof['products'], source_receipt_sha256=sha(source_path),
        auditor_sha256=sha(Path(__file__)),
        scope='Kernel Ctrl-C, synthetic INT1B/critical events, raw startup-child trap handoff, normal restoration and unknown-vector retention. Physical devices, full BBS acceptance and retained-ASPECT retry are not established by this receipt.')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2)+'\n')
    print('Independent raw DOS witness audit PASS:', len(evidence), 'cases')

if __name__ == '__main__':
    main()
