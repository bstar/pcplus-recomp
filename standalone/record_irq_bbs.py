#!/usr/bin/env python3
"""Bind optional IRQ products to stock BBS, compact observer and decoder evidence."""
import argparse
import json
from pathlib import Path
import struct

from build_guarded_helper import ROOT, LOOKUP
from record_hook_bbs import verify_case, sha


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--case', action='append', required=True, help='server:label:accept|reject:delay:irq')
    p.add_argument('--immediate-label', required=True)
    p.add_argument('--decoder-replay', type=Path, required=True)
    p.add_argument('--counterexamples', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    terminal = ROOT / 'build' / (LOOKUP + '-custom-irq') / 'TERMINAL.EXE'
    runner = ROOT / 'build/aspect-register-parent-custom-irq/ASPECT.EXE'
    sources = {}
    artifacts = {}

    def merge(mapping):
        for name, digest in mapping.items():
            assert sha(ROOT / name) == digest and (name not in sources or sources[name] == digest), name
            sources[name] = digest

    for product in (terminal, runner):
        m = json.loads((product.parent / 'manifest.json').read_text())
        assert m['experimental_custom_irq'] and sha(product) == m['binary_sha256']
        merge(m['sources'])
    parent_path=ROOT/'docs/validation/parent-custom-irq.json'
    parent=json.loads(parent_path.read_text())
    assert parent['passed'] and parent['dos']['products']['TERMINAL.EXE']==sha(terminal)
    assert parent['dos']['products']['ASPECT.EXE']==sha(runner)
    rows = []
    matrix = set()
    for spec in args.case:
        server, label, mode, delay, irq = spec.split(':')
        delay, irq = int(delay), int(irq)
        assert irq in (5, 7)
        immediate = label == args.immediate_label
        row = verify_case(server, label, mode, delay, terminal, runner,
                          immediate=immediate, expected_cpu='8086', expected_irq=irq)
        stage = ROOT / 'build/bbs-lab/script-login' / label
        output = ROOT / 'build/bbs-lab/results' / server / label
        report = json.loads((stage / 'checks.json').read_text())
        assert report['observer_compact'] and not report['observer_high']
        observed = (output / 'SCRIPT.BIN').read_bytes()
        magic, bits, ticks, segment = struct.unpack('<4H', observed)
        assert magic == 0x4d43 and ticks > 0 and not bits & 6 and segment < 0xa000
        assert (stage / 'SCRIPT.COM').stat().st_size < 1024
        config = (output / 'dosbox.conf').read_text()
        assert f'serial2=nullmodem irq:{irq} ' in config
        settings = (output / 'TEST.PRM').read_bytes()
        assert struct.unpack_from('<H', settings, 0x186)[0] == irq
        assert (output / 'BEFORE.BIN').read_bytes() == (output / 'AFTER.BIN').read_bytes()
        assert len((output / 'BEFORE.BIN').read_bytes()) == 42
        if not immediate:
            matrix.add((server, irq, mode, delay))
        else:
            assert server == 'enigma' and delay == 0
        merge(row.pop('sources'))
        artifacts.update(row.pop('artifacts'))
        row.update(cpu='8086', observer_compact=True, observer_bytes=len(observed), observer_segment=segment)
        rows.append(row)
    assert matrix == {('synchronet', 5, 'accept', 0), ('synchronet', 7, 'reject', 0),
                      ('enigma', 7, 'accept', 30), ('enigma', 5, 'reject', 30)}
    assert len(rows) == 5
    # Existing deterministic replay is reused only after current stock source,
    # input/tool pins and frozen log hashes have all been checked.
    replay_path = args.decoder_replay.resolve() / 'report.json'
    replay = json.loads(replay_path.read_text())
    server = ROOT / 'build/bbs-lab/enigma/source'
    assert replay['passed'] and replay['stock_client_unchanged']
    assert replay['stock_client_sha256'] == sha(server / 'core/client.js')
    for row in rows:
        if row['server']=='enigma':
            assert row['server_revision']==replay['upstream_revision']
            for name,digest in row['server_sources'].items():assert sha(server/name)==digest,name
    assert replay['nix_lock_sha256'] == sha(ROOT / 'nix/flake.lock')
    assert replay['upstream_package_lock_sha256'] == sha(server / 'package-lock.json')
    merge({'nix/flake.lock': replay['nix_lock_sha256']})
    for name, digest in replay['inputs'].items():
        merge({'lab/bbs/patches/enigma-key-stream/' + name: digest})
    tests = {t['name']: t for t in replay['tests']}
    for name, test in tests.items():
        assert test['exit_code'] == 0
        assert sha(replay_path.parent / (name + '.log')) == test['log_sha256']
    stock = tests['stock-counterexample']['result']
    candidate = tests['candidate-client-editor']['result']
    assert stock['passed'] and not stock['fixed']
    assert stock['demonstrated_fragmentation_failures'] == 84 and stock['editor_fragmentation_failures'] == 9
    assert candidate['passed'] and candidate['fixed']
    assert candidate['demonstrated_fragmentation_failures'] == candidate['editor_fragmentation_failures'] == 0
    for path in replay_path.parent.iterdir():
        if path.is_file():
            artifacts[str(path.relative_to(ROOT))] = sha(path)
    retained = []
    for board, label in [('synchronet', 'irq-bbs-sync5-01'), ('enigma', 'irq-bbs-enigma7-30-01')]:
        stage = ROOT / 'build/bbs-lab/script-login' / label
        output = ROOT / 'build/bbs-lab/results' / board / label
        run = json.loads((output / 'result.json').read_text())
        assert run['passed'] and run['cpu'] == '8086'
        assert not (stage / 'LOGON.ASX').exists()
        sample = (output / 'SCRIPT.BIN').read_bytes()
        assert len(sample) == 4008
        _, _, ticks, segment = struct.unpack('<4H', sample[:8])
        assert ticks > 0 and segment < 0xa000
        assert '--observer-high' in json.loads((stage / 'predictions.json').read_text())['command']
        assert sha(stage / 'TERMINAL.EXE') == sha(terminal) and sha(stage / 'ASPECT.EXE') == sha(runner)
        retained.append(dict(server=board, label=label, accepted=False, generic_transport_passed=True,
                             source_compiled=False, requested_high_observer_segment=segment,
                             scope='Historical failed pilot; upper placement was not achieved and no ASX was produced. Not a current harness pass.'))
        for folder in (stage, output):
            for path in folder.iterdir():
                if path.is_file():
                    artifacts[str(path.relative_to(ROOT))] = sha(path)
    for name in ('standalone/record_irq_bbs.py', 'standalone/record_hook_bbs.py'):
        merge({name: sha(ROOT / name)})
    counter_path=args.counterexamples.resolve()
    counter=json.loads(counter_path.read_text())
    assert counter['passed'] and counter['files_unchanged'] and len(counter['cases'])==5
    assert all(c['rejected']for c in counter['cases'])
    assert counter['checker_sha256']==sha(ROOT/'standalone/check_irq_bbs_evidence.py')
    assert counter['verifier_sha256']==sha(ROOT/'standalone/record_hook_bbs.py')
    for name,digest in counter['inputs'].items():assert sha(ROOT/name)==digest,name
    merge({'standalone/check_irq_bbs_evidence.py':counter['checker_sha256']})
    result = dict(outcomes_verified=True, compatibility_complete=False, cases=rows,
                  terminal_sha256=sha(terminal), runner_sha256=sha(runner), sources=sources,
                  artifacts=artifacts, retained_failed_pilots=retained, decoder_replay=replay,
                  evidence_counterexamples=counter,counterexamples_sha256=sha(counter_path),
                  parent_acceptance_sha256=sha(parent_path),
                  scope='Actual owned stock BBSes, DOS8086 custom IRQ5/7, DOS source login, guarded helper '
                  'adoption/rejection and unsaved editors with compact passive observer. ENiGMA30ms buffering '
                  'and immediate forwarding are separate measured outcomes. Existing decoder replay is '
                  'hash-verified historical evidence, not a fresh run or deployed fix. No physical/card/LAN-board acceptance.')
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print('PASS IRQ BBS receipt: five outcomes verified; compatibility remains incomplete')


if __name__ == '__main__':
    main()
