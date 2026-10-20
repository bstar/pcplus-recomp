#!/usr/bin/env python3
"""Rebuild the native mouse executable from a blank declared-source tree."""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import uuid
from build_native_mouse import ROOT, OUT, sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label', default='source-' + uuid.uuid4().hex)
    args = parser.parse_args()
    assert re.fullmatch(r'[A-Za-z0-9_-]+', args.label)
    folder = OUT / 'source-proofs' / args.label
    folder.mkdir(parents=True, exist_ok=False)
    source = folder / 'source'
    manifest = json.loads((OUT / 'manifest.json').read_text())
    assert manifest['original_inputs'] == [] and sha(OUT / 'MOUSE.EXE') == manifest['binary_sha256']
    for name, digest in manifest['sources'].items():
        path = Path(name)
        assert not path.is_absolute() and '..' not in path.parts and path.parts[0] not in ('build', 'analysis')
        assert sha(ROOT / path) == digest
        target = source / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / path, target)
    assert not (source / 'analysis').exists() and not (source / 'build').exists()
    with (folder / 'build.log').open('w') as log:
        result = subprocess.run([sys.executable, 'standalone/build_native_mouse.py'], cwd=source,
                                stdout=log, stderr=log, timeout=60)
    actual = sha(source / 'build/native-mouse/MOUSE.EXE') if result.returncode == 0 else None
    report = dict(passed=actual == manifest['binary_sha256'], exit_code=result.returncode,
                  expected=manifest['binary_sha256'], actual=actual, original_inputs=[],
                  sources=manifest['sources'], checker_sha256=sha(Path(__file__)),
                  log_sha256=sha(folder / 'build.log'))
    (folder / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Native mouse fresh source:', 'PASS' if report['passed'] else 'FAIL', folder)
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
