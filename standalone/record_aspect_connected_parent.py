#!/usr/bin/env python3
"""Record full-parent CONNECTED checks and the unresolved paired memory failure."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    receipts = {}

    def read(name):
        path = ROOT/name
        receipts[name] = sha(path)
        return json.loads(path.read_text())

    parent = read('build/chat-send-mode-parent-v2-20261108/manifest.json')
    child = read('build/connected-full-child-20261108/manifest.json')
    compiler = read('build/connected-full-compiler-20261108/manifest.json')
    for folder, leaf, manifest in [
        ('build/chat-send-mode-parent-v2-20261108', 'TERMINAL.EXE', parent),
        ('build/connected-full-child-20261108', 'ASPECT.EXE', child),
        ('build/connected-full-compiler-20261108', 'ASPCOMP.EXE', compiler)]:
        assert sha(ROOT/folder/leaf) == manifest['binary_sha256']
        assert manifest.get('original_inputs', []) == []
        for source, digest in manifest['sources'].items():
            assert sha(ROOT/source) == digest, source
    source = read('build/connected-parent-source-umb-20261108/checks.json')
    get = read('build/connected-parent-get-20261108/checks.json')
    for report, count in [(source, 2), (get, 6)]:
        assert report['passed'] and len(report['cases']) == count
        assert report['GET_VM'] and report['CONNECTED_probe']
        assert report['GET_compiler_sha256'] == compiler['binary_sha256']
        assert report['checker_sha256'] == sha(ROOT/'standalone/test_aspect_get_vm_dos.py')
        for case in report['cases']:
            assert case['passed'] and all(case['checks'].values())
            assert case['binary_sha256'] == parent['binary_sha256']
            assert case['runner_sha256'] == child['binary_sha256']
            assert case['checks']['CONNECTED_raw128_and_long129']
    assert source['source_compiler_residency_verified'] and get['stream_probe']
    bad = read('build/connected-full-capacity-observed-20261108/result.json')
    baseline_name = 'build/connected-capacity-baseline-source-20261108/build/paired'
    old = read(baseline_name+'/result.json')
    small = read('build/connected-full-capacity-128-20261108/result.json')
    ordinary = read('build/connected-full-capacity-20261108/result.json')
    for report in (old, bad, small, ordinary):
        assert not report['passed'] and report['binary_sha256'] == parent['binary_sha256']
        assert report['held_streams'] and report['streams_around_child']
        assert report['nested_child_count'] == 3 and report['emulate_profile_switch']
        assert not report['checks']['held_files_preserved']
    assert ordinary['interpreter_sha256'] == bad['interpreter_sha256'] == child['binary_sha256']
    assert old['interpreter_sha256'] == '20c5f38c00cb9244b65c31cbd9086a55b514c4f7b53780c963800b427dee6e8b'
    for leaf in ('FIRST.ASP', 'FIRST.ASX', 'SIX.ASP', 'SIX.ASX', 'MISSING.ASP', 'MISSING.ASX', 'NEST.COM'):
        old_folder=ROOT/baseline_name
        new_folder=ROOT/'build/connected-full-capacity-observed-20261108'
        if leaf.endswith('.ASX'):
            old_folder=ROOT/'build/connected-capacity-baseline-source-20261108/build/connection-dos/paired'
            new_folder=ROOT/'build/connection-dos/connected-full-capacity-observed-20261108'
        assert (old_folder/leaf).read_bytes() == (new_folder/leaf).read_bytes(), leaf
    failed_requests = []
    for report in (old, bad):
        assert report['cpu'] == '386' and report['exit_watch_high'] and report['heap_resize_watch']
        assert report['exit_watch']['resident_segment'] >= 0xa000
        failed = [r for r in report['exit_watch']['allocations'] if r['carry']]
        assert failed and all(r['ax'] == 8 and r['bx'] == 8607 and r['request_ah'] == 0x4a for r in failed)
        assert [r['exit'] for r in report['exit_watch']['exits']] == [7, 0, 0, 7]
        failed_requests.append([r['paragraphs'] for r in failed])
    assert all(new-old == 3 for old, new in zip(*failed_requests))
    result = dict(schema=1, checkpoint_verified=True, integration_eligible=False,
                  parent_sha256=parent['binary_sha256'], child_sha256=child['binary_sha256'],
                  compiler_sha256=compiler['binary_sha256'],
                  source_compilation_cases=2, GET_cases=6, carrier_value=128,
                  full_child_layout=child['GET_bank_layout'],
                  capacity=dict(passed=False, previous_child_also_fails=True,
                                baseline_source_commit='a234c8ad9a71e316fab9ae89c3b6e1a39bc8a9de',
                                baseline_requests=failed_requests[0], new_requests=failed_requests[1],
                                largest_possible_paragraphs=8607, failed_DOS_error=8,
                                child_exits=[7, 0, 0, 7],
                                smaller_128B_growth_also_fails=True),
                  receipts=receipts, recorder_sha256=sha(Path(__file__)),
                  installed_changed=False, selector_changed=False, physical_verified=False,
                  limits=['Synthetic serial peer; CONNECTED low/drop behavior belongs to separate modeled tests.',
                          'Observed source/GET runs use386 with diagnostic observers in UMB.',
                          'Initial8086 source run fails DOS load with131200B free versus136528B child minimum.',
                          'Heavy8086 unobserved capacity run and paired386/UMB observer runs fail.',
                          'Previous candidate also fails identical scripts; existing memory gap, not new regression.',
                          'No package promotion, whole-feature parity or physical acceptance.'])
    (ROOT/'docs/validation/aspect-connected-parent.json').write_text(json.dumps(result, indent=2)+'\n')
    print('Verified8 full-parent cases; recorded unchanged-parent paired memory gap; promotion refused')


if __name__ == '__main__':
    main()
