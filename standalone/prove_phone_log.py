#!/usr/bin/env python3
"""Rebuild and execute the native call-log component in an original-free tree."""
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
    manifest = json.loads((ROOT / 'build/phone-log/manifest.json').read_text())
    names = list(manifest['sources']) + ['standalone/check_phone_log.py']
    tree = out / 'source'
    sources = {}
    for name in names:
        assert Path(name).parts[0] in ('standalone', 'reconstruction')
        source = ROOT / name
        if name in manifest['sources']:
            assert sha(source) == manifest['sources'][name], name
        target = tree / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        sources[name] = sha(source)
    assert not (tree / 'analysis').exists() and not (tree / 'build').exists()
    with (out / 'build.log').open('w') as log:
        for name in ['standalone/build_phone_log.py', 'standalone/check_phone_log.py']:
            subprocess.run([sys.executable, str(tree / name)], cwd=tree, stdout=log, stderr=subprocess.STDOUT, check=True)
    built = tree / 'build/phone-log'
    assert sha(built / 'PHONELOG.EXE') == manifest['binary_sha256']
    cpu = json.loads((built / 'cpu-checks.json').read_text())
    assert cpu['passed'] and cpu['inputs'] == 384 and not cpu['original_verified']
    assert all(sha(tree / name) == digest for name, digest in sources.items())
    result = dict(passed=True, source_count=len(sources), sources=sources,
                  binary_sha256=sha(built / 'PHONELOG.EXE'), native_sha256=sha(built / 'controller.bin'),
                  CPU_inputs=cpu['inputs'], original_inputs=[],
                  artifacts={str(path.relative_to(ROOT)): sha(path) for path in out.rglob('*') if path.is_file()},
                  verifier_sha256=sha(Path(__file__)),
                  scope='Fresh source-only native-controller/FILE diagnostic rebuild and384 source-only16-bit policy/ABI inputs. No original executable, private file, REA database or old object in the source tree; not full application reconstruction.')
    (out / 'checks.json').write_text(json.dumps(result, indent=2) + '\n')
    print('Reproduced PHONELOG.EXE from', len(sources), 'declared source files and passed384 CPU inputs')


if __name__ == '__main__':
    main()
