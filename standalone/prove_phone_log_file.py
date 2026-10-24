#!/usr/bin/env python3
"""Reproduce checked append code/diagnostic from its declared source files only."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    out = a.output.resolve()
    assert out.is_relative_to(ROOT / 'build') and not out.exists()
    out.mkdir(parents=True)
    manifest = json.loads((ROOT / 'build/phone-log-file/manifest.json').read_text())
    tree = out / 'source'
    for name, digest in manifest['sources'].items():
        assert Path(name).parts[0] in ('src', 'standalone') and sha(ROOT / name) == digest
        target = tree / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    assert not (tree / 'analysis').exists() and not (tree / 'build').exists()
    with (out / 'build.log').open('w') as log:
        subprocess.run([sys.executable, str(tree / 'standalone/build_phone_log_file.py')], cwd=tree,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    built = tree / 'build/phone-log-file'
    assert sha(built / 'PHONEAPP.EXE') == manifest['binary_sha256']
    objects = {name: sha(built / name) for name in manifest['objects']}
    assert objects == manifest['objects']
    assert (built / 'model.txt').read_text() == 'PASS 138 append cases, 7239 assertions\n'
    assert all(sha(tree / name) == digest for name, digest in manifest['sources'].items())
    report = dict(passed=True, source_count=len(manifest['sources']), sources=manifest['sources'],
                  binary_sha256=sha(built / 'PHONEAPP.EXE'), objects=objects, original_inputs=[],
                  model_cases=138, model_assertions=7239, verifier_sha256=sha(Path(__file__)),
                  artifacts={str(path.relative_to(ROOT)): sha(path) for path in out.rglob('*') if path.is_file()},
                  scope='Fresh source tree without originals/old objects, exact DOS diagnostic and three production objects, repeated host failure model. Not terminal/banking/lifecycle integration.')
    (out / 'checks.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Reproduced DOS diagnostic and three production objects from', report['source_count'], 'sources')


if __name__ == '__main__':
    main()
