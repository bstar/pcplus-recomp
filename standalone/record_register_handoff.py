#!/usr/bin/env python3
"""Bind register API replay, DOS smoke captures and unchanged legacy products."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--linked', type=Path, required=True)
    parser.add_argument('--dos-label', action='append', required=True)
    parser.add_argument('--register-label', action='append', default=[])
    parser.add_argument('--source-proof', type=Path)
    parser.add_argument('--carrier', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    linked_path = args.linked.resolve() / 'result.json'
    assert linked_path.is_relative_to(ROOT / 'build')
    linked = json.loads(linked_path.read_text())
    assert linked['passed'] and all(case['passed'] for case in linked['cases'])
    assert linked['inputs'] == sum(case['inputs'] for case in linked['cases'])
    sources = dict(linked['sources'])
    custody = {str(linked_path.relative_to(ROOT)): sha(linked_path)}
    parent = ROOT / 'build/terminal-directory-keys-process-bank-session-capture-projection-bound-registers/TERMINAL.EXE'
    child = ROOT / 'build/aspect-register-parent/ASPECT.EXE'
    assert sha(parent) == linked['parent_sha256']
    assert sha(child) == linked['child_sha256']
    for binary in [parent, child]:
        manifest = binary.parent / 'manifest.json'
        current = json.loads(manifest.read_text())
        assert current['experimental_register_handoff']
        assert current['binary_sha256'] == sha(binary)
        for path in [binary, manifest, binary.parent / ('terminal.map' if binary == parent else 'ASPECT.map')]:
            custody[str(path.relative_to(ROOT))] = sha(path)
    dos_cases = []
    for label in args.dos_label:
        path = ROOT / 'build/directory-keys' / label / 'result.json'
        assert path.resolve().is_relative_to(ROOT / 'build/directory-keys')
        result = json.loads(path.read_text())
        assert result['passed'] and all(result['checks'].values())
        assert result['case'] == 'script' and result['banked_process']
        assert result['binary_sha256'] == sha(parent) and result['child_sha256'] == sha(child)
        folder = ROOT / 'build/connection-dos' / ('dirkeys-' + label)
        expected_wire = b'DIRSCRIPT\rDIRKBDready'
        assert result['expected_wire_hex'] == expected_wire.hex()
        assert expected_wire in (folder / 'serial.bin').read_bytes()
        for name, digest in result['sources'].items():
            assert name not in sources or sources[name] == digest, name
            sources[name] = digest
        for artifact in [path, *[p for p in folder.iterdir() if p.is_file()]]:
            custody[str(artifact.relative_to(ROOT))] = sha(artifact)
        dos_cases.append(dict(label=label, port=result['port'], passed=True))
    assert {case['port'] for case in dos_cases} == {1, 2}
    register_cases = []
    for label in args.register_label:
        path = ROOT / 'build/register-handoff-dos' / label / 'result.json'
        assert path.resolve().is_relative_to(ROOT / 'build/register-handoff-dos')
        result = json.loads(path.read_text())
        assert result['passed'] and result['cpu'] == '8086'
        assert result['DOS']['passed'] and all(result['DOS']['checks'].values())
        assert result['parent_sha256'] == sha(parent) and result['child_sha256'] == sha(child)
        assert result['DOS']['binary_sha256'] == sha(parent)
        package = path.parent / 'package'
        assert sha(package / 'TERMINAL.EXE') == sha(parent)
        assert sha(package / 'ASPECT.EXE') == sha(child)
        folder = ROOT / 'build/connection-dos' / ('register-' + label)
        for snapshot in result['snapshots']:
            index = snapshot['index']
            assert sha(folder / f'OWNER{index}.BIN') == snapshot['owner_sha256']
            assert sha(folder / f'CHILD{index}.BIN') == snapshot['child_sha256']
        wire = (folder / 'serial.bin').read_bytes()
        assert wire.index(b'OBSERVE\r') < wire.index(b'\x1b[0n')
        for name, digest in result['sources'].items():
            assert name not in sources or sources[name] == digest, name
            sources[name] = digest
        artifacts = [p for p in path.parent.iterdir() if p.is_file()]
        artifacts += [p for p in folder.iterdir() if p.is_file()]
        artifacts += [package / 'TERMINAL.EXE', package / 'ASPECT.EXE']
        for artifact in artifacts:
            custody[str(artifact.relative_to(ROOT))] = sha(artifact)
        register_cases.append(dict(label=label, case=result['case'], port=result['port'],
                                   snapshots=len(result['snapshots']), passed=True))
    if register_cases:
        kinds = {case['case'] for case in register_cases}
        assert {'normal', 'bad-token', 'missing-script', 'missing-helper'} <= kinds
        assert kinds <= {'normal', 'bad-token', 'missing-script', 'missing-helper', 'divide', 'budget', 'abort'}
        assert {(case['port'], case['case']) for case in register_cases} == {
            (port, case) for port in [1, 2] for case in kinds}
    source_proof = None
    if args.source_proof:
        path = args.source_proof.resolve() / 'result.json'
        assert path.is_relative_to(ROOT / 'build')
        proof = json.loads(path.read_text())
        assert proof['passed'] and proof['original_inputs'] == [] and len(proof['products']) == 6
        assert proof['checker_sha256'] == sha(ROOT / 'standalone/prove_directory_keys_source.py')
        for name, digest in proof['sources'].items():
            assert name not in sources or sources[name] == digest, name
            sources[name] = digest
        for name, digest in proof['products'].items():
            assert sha(ROOT / name) == digest, name
        assert proof['products'][str(parent.relative_to(ROOT))] == sha(parent)
        assert proof['products'][str(child.relative_to(ROOT))] == sha(child)
        for artifact in [path, path.parent / 'build.log']:
            custody[str(artifact.relative_to(ROOT))] = sha(artifact)
        sources['standalone/prove_directory_keys_source.py'] = proof['checker_sha256']
        source_proof = dict(source_files=proof['source_files'], products=proof['products'], passed=True)
    carrier_cases = []
    if args.carrier:
        path = args.carrier.resolve() / 'checks.json'
        assert path.is_relative_to(ROOT / 'build')
        proof = json.loads(path.read_text())
        assert proof['passed'] and proof['compatibility_accepted']
        assert not proof['gap_reproduced'] and not proof['expected_parent_gap']
        assert proof['parent_sha256'] == sha(parent) and proof['runner_sha256'] == sha(child)
        assert {case['case'] for case in proof['cases']} == {'TX-No', 'CALL-No', 'CALL-Yes', 'XOFF-error'}
        for case in proof['cases']:
            assert case['passed'] and all(case['checks'].values())
            folder = path.parent / case['case']
            assert 'cputype=8086' in (folder / 'dosbox.conf').read_text()
            for name, digest in case['captures'].items():
                assert sha(folder / name) == digest, name
                custody[str((folder / name).relative_to(ROOT))] = digest
            carrier_cases.append(dict(case=case['case'], checks=case['checks'], passed=True))
        for name, digest in proof['inputs'].items():
            if name.startswith('build/'):
                continue
            assert name not in sources or sources[name] == digest, name
            sources[name] = digest
        custody[str(path.relative_to(ROOT))] = sha(path)
    previous = ROOT / 'docs/validation/aspect-serial-bank.json'
    baseline = json.loads(previous.read_text())
    legacy = {}
    for name in ['build/terminal-directory-keys-process-bank-session-capture-projection-bound/TERMINAL.EXE',
                 'build/aspect-serial-bank-parent/ASPECT.EXE']:
        assert sha(ROOT / name) == baseline['products'][name], name
        legacy[name] = baseline['products'][name]
    custody[str(previous.relative_to(ROOT))] = sha(previous)
    for name in ['standalone/record_register_handoff.py', 'docs/REGISTER_HANDBACK.md']:
        sources[name] = sha(ROOT / name)
    for name, digest in sources.items():
        assert sha(ROOT / name) == digest, name
    output = args.output.resolve()
    assert output.is_relative_to(ROOT / 'build') or output.is_relative_to(ROOT / 'docs/validation')
    output.parent.mkdir(parents=True, exist_ok=True)
    report = dict(passed=True, linked_inputs=linked['inputs'], linked_cases=linked['cases'],
                  DOS_smoke_cases=dos_cases, DOS_register_workflows=register_cases,
                  source_proof=source_proof, carrier_workflows=carrier_cases,
                  parent_sha256=sha(parent), child_sha256=sha(child),
                  unchanged_legacy_products=legacy, sources=sources, custody_sha256=custody,
                  scope='Experimental maintained ASIO v7 register APIs and COM1/COM2 DOS script smoke. '
                        'Listed 8086 DOS register workflows inspect every bank byte, failure retention/retry '
                        'and post-child RX/parser/TX replies. Optional source proof reproduces six products; '
                        'optional virtual-modem cases check DCD loss during native confirmation, not a seeded '
                        'register-bank mutation during carrier loss. No HOOK, returned-settings, modern BBS '
                        'interaction or physical hardware acceptance is claimed.')
    output.write_text(json.dumps(report, indent=2) + '\n')
    print('PASS', report['linked_inputs'], 'linked cases;', len(register_cases),
          'DOS register workflows; COM1/COM2 DOS smoke; two exact legacy products')


if __name__ == '__main__':
    main()
