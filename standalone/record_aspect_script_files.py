#!/usr/bin/env python3
"""Bind native file-command recovery; keep application integration unclaimed."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def read(path):
    return json.loads((ROOT / path).read_text())


def main():
    manifest_path = 'build/aspect-script-files/manifest.json'
    manifest = read(manifest_path)
    assert manifest['passed'] and manifest['native_bytes'] == 572
    assert manifest['original_inputs'] == [] and len(manifest['units']) == 16
    for name, digest in manifest['sources'].items():
        assert sha(name) == digest, name
    for unit in manifest['units']:
        assert sha('build/aspect-script-files/' + unit['name'] + '.bin') == unit['sha256']
    checks = {}
    for name, path in [('source', 'build/aspect-script-files/checks.json'),
                       ('original', 'build/aspect-script-files/native-checks.json')]:
        data = read(path)
        assert data['passed'] and data['cases'] == 5828
        assert data['original_comparisons'] == (5828 if name == 'original' else 0)
        assert data['manifest_sha256'] == sha(manifest_path)
        assert data['checker_sha256'] == sha('standalone/check_aspect_script_files.py')
        checks[name] = dict(path=path, sha256=sha(path), checks=data)
    fixture_path = 'standalone/fixtures/aspect_script_file_compiler_vectors.json'
    fixture = read(fixture_path)
    oracle_path = 'analysis/aspect-script-files/compiler-03/report.json'
    oracle = read(oracle_path)
    assert fixture['oracle_sha256'] == sha(oracle_path)
    assert fixture['compiler_sha256'] == oracle['compiler_sha256']
    assert fixture['compiler_sha256'] == '5664fdfae375774da5303cc8b53c00ef773a6650132de73c7206e46ddc05039a'
    assert len(fixture['cases']) == len(oracle['cases']) == 229
    assert sum(c['success'] for c in fixture['cases']) == 119
    for frozen, observed in zip(fixture['cases'], oracle['cases']):
        for key, value in frozen.items():
            assert observed[key] == value
        assert frozen['source_sha256'] == hashlib.sha256(frozen['source'].encode('cp437')).hexdigest()
        if frozen['success']:
            assert frozen['asx_sha256'] == hashlib.sha256(bytes.fromhex(frozen['hex'])).hexdigest()
    bundles = {}
    evidence = []
    for suffix, count in [('02', 24), ('03', 1), ('04', 16)]:
        path = 'analysis/aspect-script-files/rea-evidence-' + suffix + '.json'
        records = read(path)['records']
        assert len(records) == count
        bundles[path] = sha(path)
        for record in records:
            assert record['subject']['digest']['sha256'] == '6cea4652377db36867cf1a663e8e0d7bbf0c296e3cb5c86dd67b6e442bb7a194'
            evidence.append(dict(operation=record['operation'],
                                 procedure=record['parameters']['procedure'],
                                 evidence_id=record['evidence_id']))
    assert len(evidence) == 41
    proof_path = 'docs/validation/application-components-source-build.json'
    proof = read(proof_path)
    assert proof['passed'] and proof['output_count'] == 215
    for unit in manifest['units']:
        name = 'aspect-script-files/' + unit['name'] + '.bin'
        assert proof['outputs'][name]['sha256'] == unit['sha256']
    for name, digest in manifest['objects'].items():
        assert proof['outputs']['aspect-script-files/' + name]['sha256'] == digest
    report = dict(passed=True, runtime_integrated=False, compiler_integrated=False,
                  native_instruction_bytes=572, command_count=13, helper_count=3,
                  units=manifest['units'], manifest_sha256=sha(manifest_path), checks=checks,
                  compiler_oracle=dict(fixture=fixture_path, fixture_sha256=sha(fixture_path),
                                       report_sha256=sha(oracle_path), accepted=119, rejected=110,
                                       original_compiler_sha256=fixture['compiler_sha256']),
                  REA=dict(bundle_hashes=bundles, evidence=evidence,
                           scope='Static assembly and pseudocode from synthetic overlay-entry image; never executed.'),
                  source_build_proof=dict(path=proof_path, sha256=sha(proof_path), outputs=215),
                  recorder_sha256=sha(Path(__file__).relative_to(ROOT)), whole_application_gates_closed=[],
                  remaining=['Owned six-slot stdio/FILE backend, mode/translation and warning/fatal policy.',
                             'Close/flush/replacement/error/abort/CHAIN resource ownership and borrowed streams.',
                             'Both maintained compilers, EOF destination and FGETS_CRLF setting.',
                             'Real DOS filesystem/long-position/error behavior and terminal child handoffs.'],
                  scope='Native component and original compiler facts only. Maintained application remains at76 supported opcode slots; no real filesystem or integrated script-file claim.')
    target = ROOT / 'docs/validation/aspect-script-files-native.json'
    target.write_text(json.dumps(report, indent=2) + '\n')
    print('Recorded script-file recovery:572B,5828 paired cases,119/110 original compiler corpus; integration pending')


if __name__ == '__main__':
    main()
