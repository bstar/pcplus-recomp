#!/usr/bin/env python3
"""Reproduce all nine package files in an empty tree of declared source inputs."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

from package_special_edition import ROOT, sha


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--package', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    package = args.package.resolve()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT / 'build') and not out.exists()
    manifest = json.loads((package / 'manifest.json').read_text())
    for leaf, digest in manifest['files'].items():
        assert sha(package / 'PCPLUSSE' / leaf) == digest
    out.mkdir(parents=True)
    fresh = out / 'source'
    for name, digest in manifest['sources'].items():
        path = Path(name)
        assert not path.is_absolute() and '..' not in path.parts
        assert path.parts[0] not in ('build', 'analysis')
        assert path.suffix.lower() not in ('.exe', '.com', '.obj', '.o', '.img', '.prm', '.dir', '.xlt')
        assert sha(ROOT / path) == digest, name
        target = fresh / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / path, target)
    assert not (fresh / 'build').exists()
    with (out / 'build.log').open('w') as log:
        subprocess.run([sys.executable, 'standalone/package_special_edition.py', '--build',
                        '--output', 'build/package'], cwd=fresh, check=True,
                       stdout=log, stderr=log, timeout=300)
    rebuilt = json.loads((fresh / 'build/package/manifest.json').read_text())
    assert rebuilt['files'] == manifest['files']
    for leaf, digest in rebuilt['files'].items():
        assert sha(fresh / 'build/package/PCPLUSSE' / leaf) == digest
    for name, digest in manifest['sources'].items():
        assert sha(ROOT / name) == digest
    result = dict(passed=True, package_manifest_sha256=sha(package / 'manifest.json'),
                  files=rebuilt['files'], sources=manifest['sources'], source_files=len(manifest['sources']),
                  original_inputs=[], build_log_sha256=sha(out / 'build.log'),
                  checker_sha256=sha(Path(__file__)), scope=__doc__)
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print('PASS package reproduction:', len(result['sources']), 'sources, nine files')


if __name__ == '__main__':
    main()
