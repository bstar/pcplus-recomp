#!/usr/bin/env python3
"""Record native mouse primitive evidence without claiming live integration."""
import argparse
import json
from pathlib import Path
import re
from build_native_mouse import ROOT, OUT, sha


def read(path):
    return json.loads(path.read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dos-label', required=True)
    parser.add_argument('--source-label', required=True)
    args = parser.parse_args()
    for label in (args.dos_label, args.source_label):
        assert re.fullmatch(r'[A-Za-z0-9_-]+', label)
    manifest = read(OUT / 'manifest.json')
    binary = sha(OUT / 'MOUSE.EXE')
    assert binary == manifest['binary_sha256'] and manifest['original_inputs'] == []
    assert all(sha(ROOT / name) == digest for name, digest in manifest['sources'].items())
    proof = read(ROOT / 'reconstruction/program_mouse/provenance.json')
    assert sum(unit['bytes'] for unit in proof['units']) == manifest['exact_native_bytes'] == 368
    for unit in proof['units']:
        assert sha(OUT / (Path(unit['file']).stem + '.bin')) == unit['sha256']
    model = read(OUT / 'checks.json')
    assert model['passed'] and len(model['cases']) == 117
    assert all(case['passed'] for case in model['cases'])
    assert model['binary_sha256'] == binary and model['checker_sha256'] == sha(ROOT / 'standalone/check_native_mouse.py')
    folder = OUT / 'runs' / args.dos_label
    run = read(folder / 'result.json')
    assert run['passed'] and all(run['checks'].values())
    assert run['binary_sha256'] == binary and run['checker_sha256'] == sha(ROOT / 'standalone/test_native_mouse_dos.py')
    for name, digest in run['artifacts'].items():
        assert sha(folder / name) == digest
    source = OUT / 'source-proofs' / args.source_label
    fresh = read(source / 'result.json')
    assert fresh['passed'] and fresh['exit_code'] == 0 and fresh['original_inputs'] == []
    assert fresh['expected'] == fresh['actual'] == binary == sha(source / 'source/build/native-mouse/MOUSE.EXE')
    assert fresh['checker_sha256'] == sha(ROOT / 'standalone/check_native_mouse_source.py')
    assert fresh['log_sha256'] == sha(source / 'build.log')
    for name, digest in fresh['sources'].items():
        assert sha(ROOT / name) == sha(source / 'source' / name) == digest
    evidence = [OUT / 'manifest.json', OUT / 'checks.json', folder / 'result.json',
                source / 'result.json', source / 'build.log']
    report = dict(passed=True, component_only=True, whole_application_gates_closed=[],
                  live_mouse_enabled=False, build_original_inputs=[], exact_native_bytes=368,
                  units=proof['units'], state=proof['state'], callback_analysis=proof['callback_analysis'],
                  linked_cases=117, actual_DOS_cases=1, actual_DOS_checks=run['checks'],
                  fresh_source_products=1, binary_sha256=binary, sources=manifest['sources'],
                  recorder_sha256=sha(Path(__file__)),
                  evidence={str(path.relative_to(ROOT)): sha(path) for path in evidence},
                  limitations=proof['limitations'] + [
                      'Actual DOS uses DOSBox-X INT33 and directly called source-owned motion/button events; physical mouse timing/input is not measured.',
                      'Normal interpreter/terminal publication, complete mouse event consumption/settings, ownership across PROGRAM/ASPECT, keyboard/window/error UI and broader BBS/hardware acceptance remain open.'])
    (ROOT / 'docs/validation/native-mouse.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Recorded368 native bytes,117 linked cases, actual8086 DOS and a fresh source-only build')


if __name__ == '__main__':
    main()
