#!/usr/bin/env python3
"""Check frozen package/launcher artifacts before publishing a scoped receipt."""
import argparse
import json
from pathlib import Path
import struct
import sys

from package_special_edition import ROOT, PRODUCTS, sha
from check_setup_model import image
sys.path.insert(0, str(ROOT / 'src/aspect'))
from compiler import compile_source


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('package', 'start', 'splash', 'setup', 'source-proof', 'observer-failure', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    args = p.parse_args()
    package = args.package.resolve()
    manifest = json.loads((package / 'manifest.json').read_text())
    assert manifest['card_written'] is False and manifest['contains_private_configuration'] is False
    assert set(manifest['files']) == set(PRODUCTS) | {'START.BAT', 'SETUP.BAT', 'README.TXT', 'VERSION.TXT'}
    for leaf, digest in manifest['files'].items():
        assert sha(package / 'PCPLUSSE' / leaf) == digest
    for name, digest in manifest['sources'].items():
        assert sha(ROOT / name) == digest, name
    proof_path = args.source_proof.resolve()
    proof = json.loads(proof_path.read_text())
    assert proof['passed'] and proof['original_inputs'] == []
    assert proof['package_manifest_sha256'] == sha(package / 'manifest.json')
    assert proof['files'] == manifest['files'] and proof['sources'] == manifest['sources']
    assert proof['checker_sha256'] == sha(ROOT / 'standalone/prove_special_package_source.py')
    assert proof['build_log_sha256'] == sha(proof_path.parent / 'build.log')
    for leaf, digest in proof['files'].items():
        assert sha(proof_path.parent / 'source/build/package/PCPLUSSE' / leaf) == digest
    cases = []
    for name in ('start', 'splash', 'setup'):
        folder = getattr(args, name).resolve()
        report = json.loads((folder / 'result.json').read_text())
        assert report['passed'] and report['cpu'] == '8086' and report['port'] == 2
        assert report['package_manifest_sha256'] == sha(package / 'manifest.json')
        assert report['package_files'] == manifest['files']
        assert report['launcher'] == ('SETUP' if name == 'setup' else 'START')
        assert report['resident_observer'] == (name != 'start')
        for relative, digest in report['artifacts'].items():
            assert sha(folder / relative) == digest, relative
        for relative, digest in report['sources'].items():
            assert sha(ROOT / relative) == digest, relative
        drive = folder / 'drive'
        app = drive / 'PCPLUSSE'
        assert (drive / 'RETURN.TXT').exists() and not (drive / 'FAIL.TXT').exists()
        assert (drive / 'BEFORE.BIN').read_bytes() == (drive / 'AFTER.BIN').read_bytes()
        env = (drive / 'ENV.TXT').read_bytes().upper().splitlines()
        assert b'PCPLUS=C:\\ORIGINAL' in env and not any(s.startswith(b'LOC_PCPLUS=') for s in env)
        raw = bytearray(image())
        struct.pack_into('<H', raw, 0, 1)
        struct.pack_into('<HH', raw, 0x4e4, 8, 4)
        assert (app / 'PCPLUS.PRM').read_bytes() == raw
        assert (app / 'PCPLUS.DIR').read_bytes() == b'PRIVATE-DIRECTORY-PRESERVATION-SENTINEL'
        assert (app / 'PCPLUS.XLT').read_bytes() == bytes(range(256))
        assert 'cputype=8086\n' in (folder / 'dosbox.conf').read_text()
        for leaf in PRODUCTS:
            assert sha(app / leaf) == manifest['files'][leaf]
        if name == 'start':
            source = (app / 'TEST.ASP').read_text()
            assert (app / 'TEST.ASX').read_bytes() == compile_source(source)
            assert (app / 'RESULT.BIN').read_bytes() == b'SPECIAL-COMPILED'
        else:
            video = (drive / 'SPLASH.BIN').read_bytes()
            at = (9 * 80 + 27) * 2
            assert len(video) == 8000 and video[at:at + 38:2] == b'LoC SPECIAL EDITION'
            assert video[at + 1:at + 38:2] == b'\x5f' * 19
            assert not (app / 'TEST.ASX').exists() and not (app / 'RESULT.BIN').exists()
        cases.append(dict(case=name, result=report, report_sha256=sha(folder / 'result.json'),
                          artifact_root=str(folder.relative_to(ROOT))))
    failed = args.observer_failure.resolve()
    video = failed / 'drive/SPLASH.BIN'
    assert b'ASPECT: out of memory (error 8' in video.read_bytes()[4000::2]
    assert not (failed / 'drive/PCPLUSSE/TEST.ASX').exists()
    assert not (failed / 'drive/PCPLUSSE/RESULT.BIN').exists()
    for leaf in PRODUCTS:
        assert sha(failed / 'drive/PCPLUSSE' / leaf) == manifest['files'][leaf]
    negative = dict(accepted=False, artifact_root=str(failed.relative_to(ROOT)),
                    observed='ASPECT error8; no compiled script or expected result',
                    caveat='Earlier instrumented diagnostic, not a pass of the final checker.',
                    artifacts={str(f.relative_to(failed)): sha(f) for f in failed.rglob('*') if f.is_file()})
    sources = dict(manifest['sources'])
    for case in cases:
        sources.update(case['result']['sources'])
    sources['standalone/record_special_package.py'] = sha(Path(__file__))
    sources['standalone/prove_special_package_source.py'] = sha(ROOT / 'standalone/prove_special_package_source.py')
    result = dict(passed=True, scope='Branded package START/nested compiler, START/splash and SETUP/cancel '
                  'on actual DOS8086 dummy COM2. No live BBS, removable-card write or physical modem acceptance.',
                  card_written=False, original_inputs=[], package=manifest,
                  package_manifest_sha256=sha(package / 'manifest.json'), sources=sources,
                  cases=cases, retained_failure=negative, source_reproduction=proof,
                  source_reproduction_report_sha256=sha(proof_path))
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print('PASS package receipt: three DOS workflows, retained memory failure; card unchanged')


if __name__ == '__main__':
    main()
