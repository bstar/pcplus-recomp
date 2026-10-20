#!/usr/bin/env python3
"""Publish current DOS unwind evidence without widening application claims."""
import argparse
import json
from pathlib import Path
import re
import struct
from build_aspect_process import ROOT, sha


def read(path):
    return json.loads(path.read_text())


def sources_current(sources, frozen):
    for name, digest in sources.items():
        path = Path(name)
        assert not path.is_absolute() and '..' not in path.parts
        assert sha(ROOT / path) == sha(frozen / path) == digest, name


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fault-label', required=True, action='append')
    parser.add_argument('--parent-label', required=True)
    parser.add_argument('--raw-label', required=True)
    parser.add_argument('--source-label', required=True)
    args = parser.parse_args()
    for label in args.fault_label + [args.parent_label, args.raw_label, args.source_label]:
        assert re.fullmatch(r'[A-Za-z0-9_-]+', label)
    products = {name: sha(ROOT / 'build' / name) for name in (
        'terminal-process/TERMINAL.EXE', 'aspect-process-parent/ASPECT.EXE',
        'aspect-fault/ASPECT.EXE', 'aspect-process/ASPECT.EXE',
        'aspect-runner/ASPECT.EXE', 'terminal/TERMINAL.EXE')}
    assert products['aspect-runner/ASPECT.EXE'] == 'aef146fdf62846a2dfc5d73413f435a8bfe68ca4f68d639178083d4d21e559f5'
    assert products['terminal/TERMINAL.EXE'] == 'dbc5e7104ea32b2cec00a47030acc579bed4c46dd6fc19ff07750df513338b52'
    evidence = []
    fault_cases = []
    for label in args.fault_label:
        folder = ROOT / 'build/aspect-unwind/runs' / label
        run = read(folder / 'result.json')
        assert run['passed'] and run['checker_sha256'] == sha(ROOT / 'standalone/test_aspect_unwind_dos.py')
        assert run['parent_sha256'] == products['terminal-process/TERMINAL.EXE']
        assert run['child_sha256'] == products['aspect-fault/ASPECT.EXE']
        sources_current(run['sources'], folder / 'sources')
        assert run['observer_sha256'] == sha(folder / 'RENDER.COM')
        evidence.append(folder / 'result.json')
        for case in run['cases']:
            sub = folder / case['case']
            assert case['passed'] and all(case['checks'].values())
            assert case == read(sub / 'result.json')
            assert sha(sub / 'TERMINAL.EXE') == run['parent_sha256']
            assert sha(sub / 'ASPECT.EXE') == run['child_sha256']
            assert re.search(r'^cputype\s*=\s*8086\s*$', (sub / 'dosbox.conf').read_text(), re.M)
            words = list(struct.unpack('<20H', (sub / 'FAULT.BIN').read_bytes()))
            assert words == case['report_words']
            phase = case['phase']
            control = phase == 0
            assert words[0] == 0x4652 and words[1] == phase
            assert words[3] == (0 if control else 5 if case['kind'] in 'AL' else 12)
            assert words[4:10] == [0, int(not control), int(not control), 0, int(not control), 1]
            assert words[12:16] == [0, 1, 1, 1] and words[17] < 36 and words[19] == 1
            if phase in (9, 20):
                assert words[10] > words[11] == 6944 and words[18] == int(phase == 9)
            if control:
                assert words[16] == 12
            raw = (sub / 'RENDER.BIN').read_bytes()
            size = case['compared_parent_bytes']
            assert size == 10276 and raw[-size * 2:-size] == raw[-size:]
            assert (sub / 'BEFORE.BIN').read_bytes() == (sub / 'AFTER.BIN').read_bytes()
            assert case['owner_words'][7] == 0 and case['owner_words'][8] == case['owner_words'][9]
            fault_cases.append(dict(label=label, phase=phase, kind=case['kind'], port=case['port'],
                flow=case['flow'], checks=len(case['checks']), first_error=words[3],
                recovery_error=words[7], second_VM_error=words[4],
                backup_extent=words[10], frame_offset=words[11], arena_changed=words[18],
                elapsed_ticks=words[17]))
            evidence += [sub / name for name in ('result.json', 'FAULT.BIN', 'RENDER.BIN',
                                                  'BEFORE.BIN', 'AFTER.BIN', 'serial.bin')]
    expected = {(phase, kind, 1, 'H') for phase in range(1, 23) for kind in 'DAFL'}
    expected |= {(0, 'D', 1, 'H'), (9, 'D', 2, 'B'), (6, 'D', 1, 'S'), (10, 'D', 2, 'N')}
    assert len(fault_cases) == 92 and {(c['phase'], c['kind'], c['port'], c['flow']) for c in fault_cases} == expected
    parent_folder = ROOT / 'build/aspect-parent-process' / args.parent_label
    parent = read(parent_folder / 'result.json')
    assert parent['passed'] and len(parent['cases']) == 13
    assert parent['checker_sha256'] == sha(ROOT / 'standalone/test_aspect_parent_process_dos.py')
    sources_current(parent['source_hashes'], parent_folder / 'sources')
    assert parent['parent_sha256'] == products['terminal-process/TERMINAL.EXE']
    assert parent['child_sha256'] == products['aspect-process-parent/ASPECT.EXE']
    assert {c['case'] for c in parent['cases']} == {'G', 'T', 'W', 'R', 'F'} | {f'full-{p}-{f}' for p in (1, 2) for f in 'NSHB'}
    for case in parent['cases']:
        assert case['passed'] and all(case['checks'].values())
        sub = parent_folder / case['case']
        assert sha(sub / 'ASPECT.EXE') == parent['child_sha256']
        assert (sub / 'BEFORE.BIN').read_bytes() == (sub / 'AFTER.BIN').read_bytes()
    evidence.append(parent_folder / 'result.json')
    raw_folder = ROOT / 'build/aspect-process/runs' / args.raw_label
    raw = read(raw_folder / 'result.json')
    assert raw['passed'] and len(raw['cases']) == 56
    assert raw['checker_sha256'] == sha(ROOT / 'standalone/test_aspect_process_dos.py')
    assert raw['binary_sha256'] == products['aspect-process/ASPECT.EXE']
    manifest = read(raw_folder / 'manifest.json')
    assert sha(raw_folder / 'manifest.json') == raw['manifest_sha256']
    sources_current(manifest['sources'], raw_folder / 'sources')
    sources_current(raw['owned_sources'], raw_folder / 'sources')
    expected = {(p, f, k) for p in (1, 2) for f in 'NSHB'
                for k in ('full', 'fallback', 'large', 'memory', 'divide', 'abort', 'budget')}
    assert {(c['port'], c['flow'], c['kind']) for c in raw['cases']} == expected
    for case in raw['cases']:
        assert case['passed'] and all(case['checks'].values())
        sub = raw_folder / f"com{case['port']}-{case['flow']}-{case['kind']}"
        for name, digest in case['artifacts'].items():
            assert sha(sub / name) == digest, str(sub / name)
    evidence += [raw_folder / 'result.json', raw_folder / 'manifest.json']
    models = []
    for relative, checker, count, key, product in [
        ('aspect-process/unwind-policy.json', 'check_aspect_unwind_policy.py', 12, 'binary_sha256', 'aspect-process/ASPECT.EXE'),
        ('aspect-process/policy.json', 'check_aspect_process_policy.py', 16, 'binary_sha256', 'aspect-process/ASPECT.EXE'),
        ('aspect-process/handles.json', 'check_process_handles.py', 19, 'binary_sha256', 'aspect-process/ASPECT.EXE'),
        ('terminal-process/process-owner-checks.json', 'check_aspect_parent_process.py', 29, 'parent_sha256', 'terminal-process/TERMINAL.EXE'),
        ('aspect-process-parent/program-client-checks.json', 'check_aspect_program_client.py', 48, 'child_sha256', 'aspect-process-parent/ASPECT.EXE')]:
        path = ROOT / 'build' / relative
        model = read(path)
        assert model['passed'] and len(model['cases']) == count
        assert model[key] == products[product] and model['checker_sha256'] == sha(ROOT / 'standalone' / checker)
        if 'manifest_sha256' in model:
            assert model['manifest_sha256'] == sha(path.parent / 'manifest.json')
        assert all(case['passed'] for case in model['cases'])
        models.append(dict(path=str(path.relative_to(ROOT)), cases=count, scope=model['scope']))
        evidence.append(path)
    proof_folder = ROOT / 'build/aspect-unwind/source-proofs' / args.source_label
    proof = read(proof_folder / 'result.json')
    assert proof['passed'] and proof['exit_code'] == 0 and len(proof['products']) == 27 and proof['original_inputs'] == []
    assert proof['checker_sha256'] == sha(ROOT / 'standalone/check_aspect_unwind_source.py')
    assert proof['log_sha256'] == sha(proof_folder / 'build.log')
    sources_current(proof['sources'], proof_folder / 'source')
    for name, pair in proof['products'].items():
        assert pair['expected'] == pair['actual'] == sha(ROOT / 'build' / name) == sha(proof_folder / 'source/build' / name)
    # Authenticate the preceding checkpoint before comparing its independently
    # recorded component binaries to the current source rebuild.
    old_path = ROOT / 'build/aspect-parent-process/source-proofs/parent-source-04/result.json'
    old_ledger = read(ROOT / 'docs/validation/aspect-parent-process.json')
    assert sha(old_path) == old_ledger['evidence'][str(old_path.relative_to(ROOT))]
    old = read(old_path)
    component_baselines = {name: pair['actual'] for name, pair in old['products'].items()
                           if name.startswith(('native-', 'process-serial/'))}
    assert len(component_baselines) == 20
    assert all(sha(ROOT / 'build' / name) == digest for name, digest in component_baselines.items())
    counter_path = ROOT / 'build/aspect-process/unwind-policy-before.json'
    counter = read(counter_path)
    assert not counter['passed'] and counter['checker_sha256'] == sha(ROOT / 'standalone/check_aspect_unwind_policy.py')
    bad = [c for c in counter['cases'] if not c['passed']]
    assert len(bad) == 1 and bad[0]['error'] == 10 and bad[0]['retained'] == 0 and bad[0]['retry'] == 10
    assert counter['binary_sha256'] != products['aspect-process/ASPECT.EXE']
    evidence += [proof_folder / 'result.json', proof_folder / 'build.log', counter_path, old_path]
    failed_path = ROOT / 'build/aspect-unwind/runs/unwind-02/result.json'
    failed = read(failed_path)
    assert not failed['passed'] and [c['case'] for c in failed['cases'] if not c['passed']] == ['p08-D']
    overflow_path = ROOT / 'build/aspect-process-parent/fault-build.log'
    assert 'E2021: size of segment _TEXT exceeds 64k by 5 bytes' in overflow_path.read_text()
    retained = [dict(path=str(failed_path.relative_to(ROOT)), reason='Large environment bypassed the near-allocation probe; the expected fault did not fire. Phase8 now uses a compact environment.'),
                dict(path=str(overflow_path.relative_to(ROOT)), reason='Link rejected near CODE/AUTO five bytes beyond64KiB. No executable or DOS case is accepted from this attempt.')]
    evidence += [failed_path, overflow_path]
    report = dict(passed=True, experimental_only=True, normal_publication_changed=False,
        whole_application_gates_closed=[], capability=7, normal_capability=6,
        experimental_supported_slots=108, normal_supported_slots=105,
        fault_DOS_cases=92, fault_DOS_checks=sum(c['checks'] for c in fault_cases),
        parent_DOS_cases=13, parent_DOS_checks=sum(len(c['checks']) for c in parent['cases']),
        raw_DOS_cases=56, raw_DOS_assertions=sum(c['assertions'] for c in raw['cases']),
        actual_DOS_cases=161, independent_arena_bytes=15050, exact_parent_bytes_per_attempt=10276,
        fault_cases=fault_cases, linked_models=models, linked_model_cases=sum(m['cases'] for m in models),
        fresh_source_products=27, source_hashes=proof['sources'], products=proof['products'],
        prior_component_baselines=component_baselines, preserved_component_products=20,
        retained_vector_quarantine_counterexample=bad[0],
        retained_failed_attempts=retained,
        nix_inputs={name: sha(ROOT / name) for name in ('nix/flake.nix', 'nix/flake.lock')},
        recorder_sha256=sha(Path(__file__)),
        evidence={str(path.relative_to(ROOT)): sha(path) for path in evidence},
        limitations=['Synchronous foreground DS=SS recovery only; kernel/BIOS/allocator corruption and recursive recovery faults are not covered.',
            'Foreign DOS child divide faults retain neutral DOS exit12, distinct from parent interpreter faults.',
            'Actual parent evidence is restricted to admitted80x25/page0; macro keyboard, mouse/window/error notices and broader views remain open.',
            'No normal opcode publication or whole-application gate closes. Live BBS acceptance, loaded-input pressure, actual DOS kernels and physical modem/hardware remain open.'])
    (ROOT / 'docs/validation/aspect-unwind.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Recorded161 DOS cases,124 linked policy cases and27 fresh source products; normal publication unchanged.')


if __name__ == '__main__':
    main()
