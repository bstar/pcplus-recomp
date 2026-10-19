#!/usr/bin/env python3
"""Bind real DOS file-handler/backend effects and retain integration boundaries."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads((ROOT / path).read_text())


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def main():
    manifest_path = 'build/aspect-script-file-backend/manifest.json'
    manifest = read(manifest_path)
    assert manifest['original_inputs'] == []
    binary = 'build/aspect-script-file-backend/SCRIPTIO.EXE'
    assert sha(binary) == manifest['binary_sha256']
    for path, digest in manifest['sources'].items():
        assert sha(path) == digest, path
    checks_path = 'build/aspect-script-file-backend/checks.json'
    checks = read(checks_path)
    assert checks['passed'] and checks['assertions'] == 7976
    assert checks['cycles'] == 100 and checks['simultaneous_slots'] == 6
    assert checks['binary_sha256'] == sha(binary)
    assert checks['manifest_sha256'] == sha(manifest_path)
    assert checks['checker_sha256'] == sha('standalone/check_aspect_script_file_backend.py')
    stage = Path(checks['run'])
    assert stage.is_relative_to('build/aspect-script-file-backend/tests')
    assert checks['result_sha256'] == sha(stage / 'RESULT.TXT')
    assert len(checks['files']) == 16
    for name, fact in checks['files'].items():
        assert sha(stage / name) == fact['sha256']
        assert (ROOT / stage / name).stat().st_size == fact['bytes']
    native = {}
    for name in ('checks', 'native-checks'):
        path = 'build/aspect-script-files/' + name + '.json'
        r = read(path)
        assert r['passed'] and r['cases'] == 5828
        assert r['original_comparisons'] == (5828 if name == 'native-checks' else 0)
        assert r['checker_sha256'] == sha('standalone/check_aspect_script_files.py')
        assert r['manifest_sha256'] == sha('build/aspect-script-files/manifest.json')
        native[path] = dict(sha256=sha(path), checks=r)
    rea = {}
    for label in ('lifetime', 'seek'):
        path = 'analysis/aspect-script-files/rea-' + label + '-01.json'
        bundle = read(path)
        assert len(bundle['records']) == 3
        rea[label] = dict(bundle_sha256=sha(path), records=[dict(
            operation=r['operation'], procedure=r['parameters']['procedure'],
            evidence_id=r['evidence_id'], target_sha256=r['subject']['digest']['sha256'])
            for r in bundle['records']])
    initializer_path = 'analysis/pcplus-overlay-anchored-02/functions/0x1d6ea.asm'
    initializer = (ROOT / initializer_path).read_text()
    assert ('0x1d702: MOV AX, 0x1\n0x1d705: MOV [0xe37e], AX\n'
            '0x1d708: MOV [0xe38a], AX\n0x1d70b: MOV [0xe388], AX') in initializer
    initializer_unit = next(u for u in read('analysis/aspect-vm/inventory-02.json')['recovered_coordinates']
                            if u['name'] == 'loader-state-defaults')
    proof_path = 'docs/validation/application-components-source-build.json'
    proof = read(proof_path)
    assert proof['passed'] and proof['output_count'] == 216
    assert proof['outputs']['aspect-script-file-backend/SCRIPTIO.EXE']['sha256'] == sha(binary)
    for name in ('terminal/TERMINAL.EXE', 'aspect-runner/ASPECT.EXE', 'aspect-compiler-dos/ASPCOMP.EXE'):
        assert proof['outputs'][name]['sha256'] == sha('build/' + name)
    record = dict(passed=True, runtime_integrated=False, compiler_integrated=False,
                  binary_sha256=sha(binary), manifest_sha256=sha(manifest_path),
                  DOS=dict(path=checks_path, sha256=sha(checks_path), checks=checks),
                  native=native, REA=rea,
                  original_initializer=dict(unit=initializer_unit, assembly_sha256=sha(initializer_path),
                                            FGETS_CRLF_default=1),
                  source_build_proof=dict(path=proof_path, sha256=sha(proof_path), outputs=216),
                  recorder_sha256=sha(Path(__file__).relative_to(ROOT)), whole_application_gates_closed=[],
                  retained_failures=['backend-01: one negative absolute seek comparison failed.',
                                     'backend-02 and backend-seek-probe-01: querying DOS position did not reproduce the original CRT negative-target guard; nativeA22E evidence then established the needed precheck.'],
                  remaining=['Both compilers and runtime dispatch; FGETS_CRLF SET/FETCH.',
                             'Actual VM completion/error/abort/cancel/EXECUTE and repeated invocations.',
                             'Terminal child handoffs and broader original CRT/borrowed-warning equivalence.'],
                  scope='Native13 handlers/3helpers over owned real DOS stdio with declared typed operand/writeback/warning/lowercase fixture boundaries. Actual filesystem and backend finish API verified; packaged runtime still has76 supported slots.')
    target = ROOT / 'docs/validation/aspect-script-file-backend.json'
    target.write_text(json.dumps(record, indent=2) + '\n')
    print('Recorded real DOS script-file backend:7976 checks,16 exact files,100 six-slot rounds; VM integration pending')


if __name__ == '__main__':
    main()
