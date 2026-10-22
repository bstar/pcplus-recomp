#!/usr/bin/env python3
"""Bind code templates, stable recorder owner and current terminal regressions."""
import argparse
import ast
import json
import shutil
from pathlib import Path
from record_recording_file import ROOT, read, sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--normal', type=Path, required=True)
    parser.add_argument('--banked', type=Path, required=True)
    parser.add_argument('--foreground', type=Path, required=True)
    parser.add_argument('--core-host', type=Path, required=True)
    parser.add_argument('--publisher-host', type=Path, required=True)
    parser.add_argument('--terminal-dos', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    normal, banked, foreground, core_host, publisher_host, terminal_dos, output = (p.resolve() for p in
        (args.normal, args.banked, args.foreground, args.core_host, args.publisher_host, args.terminal_dos, args.output))
    assert all(p.is_relative_to(ROOT / 'build') for p in (normal, banked, foreground, core_host, publisher_host, terminal_dos))
    assert output.is_relative_to(ROOT / 'docs/validation') and not output.exists()
    custody = foreground.parent / 'accepted'
    assert not custody.exists()
    selected = {Path(__file__).resolve(), ROOT / 'standalone/record_recording_file.py', ROOT / 'Makefile'}
    proofs = []
    for path, is_banked, is_foreground in ((normal, False, False), (banked, True, False), (foreground, True, True)):
        proof = read(path)
        assert proof['passed'] and proof['banked'] == is_banked and proof['foreground'] == is_foreground and len(proof['cases']) == 18
        selected.add(path)
        for name, digest in proof['inputs'].items():
            source, frozen = ROOT / name, path.parent / 'frozen-source' / name
            assert sha(source) == sha(frozen) == digest, name
            selected.update((source, frozen))
        for name, digest in proof['captures_sha256'].items():
            artifact = path.parent / name
            assert artifact.resolve().is_relative_to(path.parent) and sha(artifact) == digest, name
            selected.add(artifact)
        assert sha(path.parent / 'RECORD.EXE') == proof['binary_sha256']
        for directory, binary_name in (('aspect-runner', 'ASPECT.EXE'), ('aspect-compiler-dos', 'ASPCOMP.EXE')):
            manifest = read(path.parent / 'frozen-source/build' / directory / 'manifest.json')
            assert not manifest['original_inputs'] and sha(path.parent / binary_name) == manifest['binary_sha256']
            assert all(proof['inputs'][name] == digest for name, digest in manifest['sources'].items())
        for case in proof['cases']:
            folder = path.parent / case['case']
            assert case['passed'] and all(case['checks'].values()) and not case['peer_errors']
            assert read(folder / 'result.json') == case
            assert (folder / 'wire.bin').read_bytes().hex() == case['actual_hex'] == case['expected_hex']
            assert list(map(int, (folder / 'STATUS.TXT').read_text().split())) == case['status']
            if is_banked:
                resident, publisher, core, callback = map(int, (folder / 'BANK.TXT').read_text().split())
                assert resident == callback and publisher == core and resident != publisher
            if is_foreground:
                owner_cs, core_cs, ds_ss = map(int, (folder / 'FOREGND.TXT').read_text().split())
                assert owner_cs == core_cs and ds_ss == 1
        proofs.append(proof)
    for other, proof in ((banked, proofs[1]), (foreground, proofs[2])):
        assert [c['case'] for c in proofs[0]['cases']] == [c['case'] for c in proof['cases']]
        for a, b in zip(proofs[0]['cases'], proof['cases']):
            assert a['status'] == b['status'] and a['actual_hex'] == b['actual_hex']
            for leaf in ('CASE.ASP', 'CASE.ASX', 'LPR00001.TMP', 'LPR00002.BAK'):
                x, y = normal.parent / a['case'] / leaf, other.parent / b['case'] / leaf
                assert x.exists() == y.exists()
                if x.exists():
                    assert x.read_bytes() == y.read_bytes()
    host_records = {}
    for path, count, binary_name in ((core_host, 17, 'recorder.so'), (publisher_host, 31, 'file.so')):
        proof = read(path)
        assert proof['passed'] and proof['case_count'] == len(proof['cases']) == count
        assert all(case['passed'] for case in proof['cases'])
        assert sha(path.parent / binary_name) == proof['library_sha256']
        selected.update((path, path.parent / binary_name))
        for name, digest in proof['inputs'].items():
            source, frozen = ROOT / name, path.parent / 'frozen-source' / name
            assert sha(source) == sha(frozen) == digest, name
            selected.update((source, frozen))
        host_records[binary_name] = dict(cases=count, result=str(path.relative_to(ROOT)), sha256=sha(path))
    prior_ledger = ROOT / 'docs/validation/aspect-recorder-source.json'
    prior_reference = read(prior_ledger)['proofs']['host']
    prior_path = ROOT / prior_reference['result']
    assert sha(prior_path) == prior_reference['sha256']
    prior = read(prior_path)
    assert prior['passed'] and prior['cases'] == read(core_host)['cases']
    selected.update((prior_ledger, prior_path, prior_path.parent / 'recorder.so'))
    assert sha(prior_path.parent / 'recorder.so') == prior['library_sha256']
    for name, digest in prior['inputs'].items():
        frozen = prior_path.parent / 'frozen-source' / name
        assert sha(frozen) == digest
        selected.add(frozen)
    host_records['core_baseline_equivalence'] = dict(result=str(prior_path.relative_to(ROOT)),
        sha256=sha(prior_path), exact_case_results=17)
    manifest_path = ROOT / 'build/terminal/manifest.json'
    manifest = read(manifest_path)
    binary = ROOT / 'build/terminal/TERMINAL.EXE'
    assert sha(binary) == manifest['binary_sha256']
    assert manifest['kind'] == 'source-only-interactive-dos-terminal'
    selected.update((manifest_path, binary, binary.parent / 'terminal.map'))
    for name, digest in manifest['sources'].items():
        assert not name.startswith(('analysis/', 'build/')) and sha(ROOT / name) == digest
        selected.add(ROOT / name)
    memory = manifest['memory_layout']
    assert memory['recording_bank_functions_verified'] == 14
    assert memory['recording_resident_callbacks_verified'] == 9
    assert len(memory['recording_adapter_far_call_sites']) == 3
    assert memory['configuration_bridge_pairs_verified'] == 94 and memory['far_code_bridge_pairs_verified'] == 150
    assert memory['near_spare_bytes'] == 112 and memory['resident_code_spare_bytes'] == 478
    assert memory['recording_terminal_state_bytes'] == 392
    assert memory['recording_terminal_bank_functions_verified'] == 9
    assert len(memory['recording_terminal_far_call_sites']) == 2
    assert memory['recorder_code_literal_bytes_verified'] == 223
    assert len(memory['recorder_code_literal_sites']) == 9
    mouse_path = ROOT / 'build/terminal-mouse/manifest.json'
    mouse = read(mouse_path)
    assert sha(mouse_path.parent / 'TERMINAL.EXE') == mouse['binary_sha256']
    assert mouse['memory_layout']['recording_bank_functions_verified'] == 14
    assert mouse['memory_layout']['near_spare_bytes'] == 64
    assert mouse['memory_layout']['resident_code_spare_bytes'] == 330
    selected.update((mouse_path, mouse_path.parent / 'TERMINAL.EXE', mouse_path.parent / 'terminal.map'))
    for name, digest in mouse['sources'].items():
        assert not name.startswith(('analysis/', 'build/')) and sha(ROOT / name) == digest
        selected.add(ROOT / name)
    linked = {}
    for name, filename in [('capture', 'terminal-capture-live-checks.json'),
                           ('history', 'history-export-checks.json'),
                           ('ZMODEM', 'terminal-zmodem-live-checks.json'),
                           ('ABI', 'config-far-checks.json'), ('far_runtime', 'far-code-live-checks.json'), ('owner', 'recording-foreground-checks.json')]:
        path = binary.parent / filename
        proof = read(path)
        assert proof['passed'] and proof['binary_sha256'] == manifest['binary_sha256']
        if name == 'capture':
            assert sum(c['inputs'] for c in proof['cases']) == 24
        elif name == 'history':
            assert proof['inputs'] == 27
        elif name == 'ZMODEM':
            assert proof['inputs'] == len(proof['cases']) == 78 and all(c['passed'] for c in proof['cases'])
        elif name == 'ABI':
            assert proof['memory'] == memory and len(proof['rejected_mutations']) == 546
        elif name == 'owner':
            assert len(proof['cases']) == 6 and all(c['passed'] for c in proof['cases'])
            assert proof['source_sha256'] == sha(ROOT / 'standalone/check_recording_foreground_live.py')
        else:
            assert len(proof['cases']) == 3 and all(c['passed'] for c in proof['cases'])
        selected.add(path)
        linked[name] = dict(result=str(path.relative_to(ROOT)), sha256=sha(path))
    proof = read(terminal_dos)
    assert proof['passed'] and proof['binary_sha256'] == manifest['binary_sha256']
    assert len(proof['cases']) == 11 and all(c['passed'] and all(c['checks'].values()) for c in proof['cases'])
    selected.update(p for p in terminal_dos.parent.rglob('*') if p.is_file())
    def keep_local_imports(path):
        if path in selected:
            return
        selected.add(path)
        for node in ast.walk(ast.parse(path.read_text())):
            modules = [n.name for n in node.names] if isinstance(node, ast.Import) else (
                [node.module] if isinstance(node, ast.ImportFrom) and node.module else [])
            for module in modules:
                imported = path.parent / (module.split('.')[0] + '.py')
                if imported.is_file():
                    keep_local_imports(imported)
    for name in ('check_config_far_live.py', 'check_far_code_live.py', 'test_terminal_capture_dos.py',
                 'check_terminal_capture_live.py', 'check_history_export_live.py', 'check_terminal_zmodem_live.py',
                 'check_recording_foreground_live.py'):
        keep_local_imports(ROOT / 'standalone' / name)
    custody.mkdir()
    kept = {}
    for path in sorted(selected):
        copy = custody / path.relative_to(ROOT)
        copy.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, copy)
        assert sha(copy) == sha(path)
        kept[str(copy.relative_to(ROOT))] = sha(copy)
    result = dict(passed=True, recording_owner_component_accepted=True, terminal_recording_accepted=False,
        normal_DOS_cases=18, banked_DOS_cases=18, owner_DOS_cases=18, host_models=host_records,
        normal=dict(result=str(normal.relative_to(ROOT)), sha256=sha(normal)),
        banked=dict(result=str(banked.relative_to(ROOT)), sha256=sha(banked)),
        owner=dict(result=str(foreground.relative_to(ROOT)), sha256=sha(foreground)),
        terminal_sha256=manifest['binary_sha256'], memory_layout=memory, linked_regressions=linked,
        mouse_build_only=dict(binary_sha256=mouse['binary_sha256'], memory_layout=mouse['memory_layout'], runtime_accepted=False),
        terminal_DOS=dict(result=str(terminal_dos.relative_to(ROOT)), sha256=sha(terminal_dos), cases=len(proof['cases'])),
        custody_sha256=kept,
        scope='Nine immutable recorder templates occupy223 CONFIG_CODE bytes with explicit far reads '
              'and bounded near callback copies. The stable326-byte owner,64-byte filename and initialized '
              'cookie fit both terminal variants; assembly startup/shutdown call the far lifecycle APIs. '
              'Eighteen ordinary, eighteen banked and eighteen owner DOS cases preserve source/ASX/wire/status '
              'identity, including sliding prompts and shutdown cancellation. Dirty owner memory is deliberately '
              'seeded; modeled close/write faults remain distinct from real DOS operations and replay. '
              'Six current linked owner cases, current capture/history/ZMODEM/far regressions and546 ABI '
              'negatives pass. No Record controls, automatic foreground taps/exclusions, current BBS/audio, '
              'physical modem or F01-F16 full application acceptance.')
    with output.open('x') as stream:
        stream.write(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(passed=True, custody_files=len(kept))))


if __name__ == '__main__':
    main()
