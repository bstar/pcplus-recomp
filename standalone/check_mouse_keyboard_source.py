#!/usr/bin/env python3
"""Reproduce the composed mouse/keyboard diagnostic and children from source only."""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import uuid
from build_mouse_keyboard import ROOT, OUT, sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label', default='source-' + uuid.uuid4().hex)
    args = parser.parse_args()
    assert re.fullmatch(r'[A-Za-z0-9_-]+', args.label)
    folder = OUT / 'source-proofs' / args.label
    folder.mkdir(parents=True, exist_ok=False)
    source = folder / 'source'
    manifest = json.loads((OUT / 'manifest.json').read_text())
    assert manifest['original_inputs'] == []
    for name, digest in manifest['sources'].items():
        path = Path(name)
        assert not path.is_absolute() and '..' not in path.parts and path.parts[0] not in ('analysis', 'build')
        assert sha(ROOT / path) == digest
        target = source / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / path, target)
    assert not (source / 'build').exists() and not (source / 'analysis').exists()
    with (folder / 'build.log').open('w') as log:
        result = subprocess.run([sys.executable, 'standalone/build_mouse_keyboard.py'], cwd=source,
                                stdout=log, stderr=log, timeout=60)
    products = {name: dict(expected=sha(OUT / name), actual=sha(source / 'build/mouse-keyboard' / name))
                for name in ('MOUSEKEY.EXE', 'MUTATE.COM', 'VECTOR.COM')} if result.returncode == 0 else {}
    report = dict(passed=len(products) == 3 and all(v['expected'] == v['actual'] for v in products.values()),
                  exit_code=result.returncode, products=products, sources=manifest['sources'],
                  original_inputs=[], checker_sha256=sha(Path(__file__)), log_sha256=sha(folder / 'build.log'))
    (folder / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Mouse/keyboard fresh source:', 'PASS' if report['passed'] else 'FAIL', folder)
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
