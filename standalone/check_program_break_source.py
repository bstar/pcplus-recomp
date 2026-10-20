#!/usr/bin/env python3
"""Rebuild only declared source inputs in a fresh tree with originals absent."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/program-break'
manifest=json.loads((OUT/'manifest.json').read_text())
fresh=Path(tempfile.mkdtemp(prefix='source-only-',dir=OUT))
for name,digest in manifest['inputs'].items():
    source=ROOT/name
    assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
    target=fresh/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
assert not (fresh/'analysis').exists()
assert not list(fresh.rglob('*.exe')) and not list(fresh.rglob('*.EXE'))
subprocess.run([sys.executable,str(fresh/'standalone/build_program_break.py')],cwd=fresh,check=True)
binary=fresh/'build/program-break/BRKVEC.EXE'
assert hashlib.sha256(binary.read_bytes()).hexdigest()==manifest['binary_sha256']
(OUT/'source-checks.json').write_text(json.dumps(dict(passed=True,inputs=len(manifest['inputs']),
    binary_sha256=manifest['binary_sha256'],fresh_tree=str(fresh.relative_to(ROOT)),
    scope='Fresh tree contains only declared assembly/encoding/diagnostic/build source and numerical provenance. No original executable, prior object, analysis database or REA session is a build input.'),indent=2)+'\n')
print('Original-free source tree reproduced BRKVEC.EXE')
