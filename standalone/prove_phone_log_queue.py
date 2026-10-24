#!/usr/bin/env python3
"""Rebuild near/far queue diagnostics and production objects from declared sources."""
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--bank', action='store_true')
    args = parser.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT / 'build') and not out.exists()
    out.mkdir(parents=True)
    product = 'phone-log-bank' if args.bank else 'phone-log-queue'
    manifest = json.loads((ROOT / 'build' / product / 'manifest.json').read_text())
    tree = out / 'source'
    for name, digest in manifest['sources'].items():
        assert Path(name).parts[0] in ('src', 'standalone') and sha(ROOT / name) == digest
        target = tree / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    assert not (tree / 'analysis').exists() and not (tree / 'build').exists()
    with (out / 'build.log').open('w') as log:
        subprocess.run([sys.executable, str(tree / 'standalone' / ('build_' + product.replace('-', '_') + '.py'))], cwd=tree,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    built = tree / 'build' / product
    outputs = {}
    for variant, expected in manifest['outputs'].items():
        folder = built if args.bank else built / variant
        outputs[variant] = dict(binary_sha256=sha(folder / 'QUEUE.EXE'),
                               objects={name: sha(folder / name) for name in expected['objects']})
        assert outputs[variant] == expected
    assert all(sha(tree / name) == digest for name, digest in manifest['sources'].items())
    report = dict(passed=True, source_count=len(manifest['sources']), sources=manifest['sources'],
                  outputs=outputs, original_inputs=[], verifier_sha256=sha(Path(__file__)),
                  artifacts={str(path.relative_to(ROOT)): sha(path) for path in out.rglob('*') if path.is_file()},
                  scope='Fresh declared source tree, exact recorded DOS executables and production/adapter objects; no original executables or old objects. Not terminal event integration.')
    (out / 'checks.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Reproduced', len(outputs), 'DOS executables and', sum(len(row['objects']) for row in outputs.values()),
          'objects from', report['source_count'], 'sources')


if __name__ == '__main__':
    main()
