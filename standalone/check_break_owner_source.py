#!/usr/bin/env python3
"""Reproduce the owner and child using only declared source inputs."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/break-owner'
manifest = json.loads((OUT / 'manifest.json').read_text())
fresh = Path(tempfile.mkdtemp(prefix='source-only-', dir=OUT))
for name, digest in manifest['sources'].items():
    source = ROOT / name
    assert hashlib.sha256(source.read_bytes()).hexdigest() == digest, name
    target = fresh / name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
assert not (fresh / 'analysis').exists()
assert not list(fresh.rglob('*.exe')) and not list(fresh.rglob('*.EXE'))
subprocess.run([sys.executable, str(fresh / 'standalone/build_break_owner.py')], cwd=fresh, check=True)
for name, expected in [('BRKOWN.EXE', manifest['binary_sha256']),
                       ('BRKCHLD.COM', manifest['child_sha256'])]:
    assert hashlib.sha256((fresh / 'build/break-owner' / name).read_bytes()).hexdigest() == expected
receipt = dict(passed=True, inputs=len(manifest['sources']),
               binary_sha256=manifest['binary_sha256'], child_sha256=manifest['child_sha256'],
               fresh_tree=str(fresh.relative_to(ROOT)),
               scope='Fresh declared-source tree; no original executable, prior object or REA database.')
(OUT / 'source-checks.json').write_text(json.dumps(receipt, indent=2) + '\n')
print('Original-free source tree reproduced BRKOWN.EXE and BRKCHLD.COM')
