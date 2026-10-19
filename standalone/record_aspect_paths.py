#!/usr/bin/env python3
"""Record native path recovery, compiler conformance and DOS product behavior."""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def read(path):
    return json.loads((ROOT / path).read_text())


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--filesystem-label', required=True)
    p.add_argument('--parent-label', required=True)
    a = p.parse_args()
    assert all(re.fullmatch(r'[A-Za-z0-9_-]+', value)
               for value in (a.filesystem_label, a.parent_label))
    manifest = read('build/aspect-paths/manifest.json')
    assert manifest['passed'] and manifest['original_inputs'] == []
    assert manifest['native_bytes'] == 210
    for name, digest in manifest['sources'].items():
        assert sha(name) == digest, name
    reports = {}
    for name, path in (
        ('native', 'build/aspect-paths/checks.json'),
        ('original_replay', 'build/aspect-paths/native-checks.json'),
        ('host_compiler', 'build/aspect-paths/compiler-checks.json'),
        ('DOS_compiler', 'build/aspect-compiler-dos/checks.json'),
        ('runtime', 'build/aspect-runtime/checks.json'),
        ('filesystem', f'build/aspect-paths-dos/{a.filesystem_label}/checks.json'),
        ('parent', f'build/aspect-paths-parent-dos/{a.parent_label}/checks.json')):
        data = read(path)
        assert data['passed'], path
        reports[name] = dict(path=path, sha256=sha(path), checks=data)
    native = reports['native']['checks']
    replay = reports['original_replay']['checks']
    assert native['cases'] == replay['cases'] == replay['original_comparisons'] == 1578
    assert native['original_comparisons'] == 0
    assert native['checker_sha256'] == replay['checker_sha256'] == sha('standalone/check_aspect_paths.py')
    assert native['manifest_sha256'] == replay['manifest_sha256'] == sha('build/aspect-paths/manifest.json')

    vectors_path = 'standalone/fixtures/aspect_path_compiler_vectors.json'
    vectors = read(vectors_path)
    oracle_path = 'analysis/aspect-paths/compiler-02/report.json'
    oracle = read(oracle_path)
    assert vectors['oracle_sha256'] == sha(oracle_path)
    assert oracle['compiler_sha256'] == vectors['compiler_sha256']
    assert len(oracle['cases']) == len(vectors['cases']) == 56
    for frozen, observed in zip(vectors['cases'], oracle['cases']):
        for key in ('name', 'label', 'source', 'source_sha256', 'success'):
            assert frozen[key] == observed[key], (frozen['name'], key)
        if frozen['success']:
            assert frozen['hex'] == observed['hex']
            assert frozen['asx_sha256'] == observed['asx_sha256']
    host = reports['host_compiler']['checks']
    assert (host['accepted'], host['rejected']) == (24, 32)
    assert host['fixture_sha256'] == sha(vectors_path)
    assert host['compiler_sha256'] == sha('src/aspect/compiler.py')
    dos = reports['DOS_compiler']['checks']
    assert dos['fixture_sources'][vectors_path] == sha(vectors_path)
    assert dos['binary_sha256'] == sha('build/aspect-compiler-dos/ASPCOMP.EXE')
    assert dos['host_compiler_sha256'] == sha('src/aspect/compiler.py')
    runtime = reports['runtime']['checks']
    assert runtime['supported_slot_count'] == 76 and runtime['unsupported_slot_cases'] == 139
    assert runtime['binary_sha256'] == sha('build/aspect-runtime/EXECUTE.EXE')
    runner = sha('build/aspect-runner/ASPECT.EXE')
    terminal = sha('build/terminal/TERMINAL.EXE')
    filesystem = reports['filesystem']['checks']
    assert filesystem['scripts'] == 4 and filesystem['status_checks'] == 19
    assert filesystem['runner_sha256'] == runner
    assert filesystem['compiler_sha256'] == dos['binary_sha256']
    assert filesystem['guard_file_preserved'] and filesystem['source_and_DOS_bytecode_equal']
    assert filesystem['checker_sha256'] == sha('standalone/test_aspect_paths_dos.py')
    parent = reports['parent']['checks']
    assert parent['terminal_sha256'] == terminal and parent['runner_sha256'] == runner
    assert parent['checker_sha256'] == sha('standalone/test_aspect_paths_parent_dos.py')
    assert len(parent['cases']) == 1
    assert all(parent['cases'][0]['checks'].values())

    bundle_path = 'analysis/aspect-paths/rea-01/evidence.json'
    bundle = read(bundle_path)
    assert len(bundle['records']) == 16
    evidence = []
    for record in bundle['records']:
        assert record['subject']['digest']['sha256'] == '6cea4652377db36867cf1a663e8e0d7bbf0c296e3cb5c86dd67b6e442bb7a194'
        evidence.append(dict(operation=record['operation'], procedure=record['parameters']['procedure'],
                             evidence_id=record['evidence_id']))
    proof_path = 'docs/validation/application-components-source-build.json'
    proof = read(proof_path)
    assert proof['passed'] and proof['output_count'] == 197
    for name in ('terminal/TERMINAL.EXE', 'aspect-runner/ASPECT.EXE', 'aspect-compiler-dos/ASPCOMP.EXE'):
        assert proof['outputs'][name]['sha256'] == sha('build/' + name)
    package_path = 'build/dos-package/manifest.json'
    package = read(package_path)
    assert package['original_inputs'] == []
    for name, digest in (('TERMINAL.EXE', terminal), ('ASPECT.EXE', runner), ('ASPCOMP.EXE', dos['binary_sha256'])):
        assert package['files'][name] == digest == sha('build/dos-package/' + name)
    report = dict(passed=True, native_instruction_bytes=210, numeric_error_entries=20,
                  original_sha256=read('standalone/fixtures/aspect_path_native_units.json')['original_sha256'],
                  terminal_sha256=terminal, runner_sha256=runner, compiler_sha256=dos['binary_sha256'],
                  reports=reports,
                  original_compiler_oracle=dict(path=oracle_path, sha256=sha(oracle_path),
                                                compiler_sha256=vectors['compiler_sha256'], accepted=24, rejected=32),
                  REA=dict(bundle_sha256=sha(bundle_path), records=evidence,
                           scope='Static synthetic overlay-entry analysis, never executed; native behavior separately tested.'),
                  source_build_proof=dict(path=proof_path, sha256=sha(proof_path), outputs=197),
                  package_manifest_sha256=sha(package_path), recorder_sha256=sha(Path(__file__).relative_to(ROOT)),
                  whole_application_gates_closed=[],
                  scope='Native path commands and DOS3+ backend; original compiler and instruction conformance, actual DOS filesystem/drive retention and parent login handoff. Maintained 76-slot runtime remains incomplete; arbitrary bytecode, crash recovery and physical modem validation are separate.')
    (ROOT / 'docs/validation/aspect-paths.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Recorded ASPECT paths: native210B,1578 paired cases,24/32 grammar,19 DOS statuses and parent login')


if __name__ == '__main__':
    main()
