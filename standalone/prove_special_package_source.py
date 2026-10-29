#!/usr/bin/env python3
"""Reproduce every package file in an empty tree of declared source inputs."""
import argparse
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile

from package_special_edition import ROOT, sha


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--package', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--commit', help='Export only these committed sources, excluding all working-tree changes')
    args = p.parse_args()
    package = args.package.resolve()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT / 'build') and not out.exists()
    manifest = json.loads((package / 'manifest.json').read_text())
    for leaf, digest in manifest['files'].items():
        assert sha(package / 'PCPLUSSE' / leaf) == digest
    out.mkdir(parents=True)
    fresh = out / 'source'
    source_commit=None
    for name, digest in manifest['sources'].items():
        path = Path(name)
        assert not path.is_absolute() and '..' not in path.parts
        assert path.parts[0] not in ('build', 'analysis')
        assert path.suffix.lower() not in ('.exe', '.com', '.obj', '.o', '.img', '.prm', '.dir', '.xlt')
        if not args.commit:
            assert sha(ROOT / path) == digest, name
            target = fresh / path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / path, target)
    if args.commit:
        source_commit=subprocess.check_output(['git','rev-parse','--verify','--end-of-options',
            args.commit+'^{commit}'],cwd=ROOT,text=True).strip()
        raw=subprocess.check_output(['git','archive','--format=tar',source_commit,'--',
                                     *sorted(manifest['sources'])],cwd=ROOT)
        fresh.mkdir()
        with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
            archive.extractall(fresh,filter='data')
    selected_sources={name:sha(fresh/name) for name in manifest['sources']}
    assert not (fresh / 'build').exists()
    environment=dict(os.environ,GIT_CEILING_DIRECTORIES=str(out))
    discover=subprocess.run(['git','rev-parse','--show-toplevel'],cwd=fresh,env=environment,capture_output=True)
    assert discover.returncode!=0,'Fresh source tree must not discover ancestor Git metadata'
    with (out / 'build.log').open('w') as log:
        subprocess.run([sys.executable, 'standalone/package_special_edition.py', '--build',
                        '--output', 'build/package',
                        '--source-base-commit',manifest['source_base_commit'],
                        *(['--custom-irq']if manifest.get('experimental_custom_irq')else[]),
                        *(['--original-keys']if manifest.get('experimental_original_keys')else[]),
                        *(['--original-reference']if manifest.get('experimental_original_reference')else[]),
                        *(['--directory-view']if manifest.get('experimental_directory_view')else[]),
                        *(['--directory-preview']if manifest.get('experimental_directory_preview')else[]),
                        *(['--directory-storage']if manifest.get('experimental_directory_storage')else[]),
                        *(['--directory-resource-cli']if manifest.get('experimental_directory_resource_cli')else[]),
                        *(['--directory-resource-owner']if manifest.get('experimental_directory_resource_owner')else[]),
                        *(['--directory-retirement']if manifest.get('experimental_directory_retirement')else[]),
                        *(['--directory-translation']if manifest.get('experimental_directory_translation')else[])], cwd=fresh, check=True,
                       stdout=log, stderr=log, timeout=300,env=environment)
    rebuilt = json.loads((fresh / 'build/package/manifest.json').read_text())
    assert rebuilt['files'] == manifest['files']
    for leaf, digest in rebuilt['files'].items():
        assert sha(fresh / 'build/package/PCPLUSSE' / leaf) == digest
    for name, digest in selected_sources.items():
        assert sha(fresh / name) == digest
        if not args.commit:assert sha(ROOT / name) == digest
    result = dict(passed=True, package_manifest_sha256=sha(package / 'manifest.json'),
                  files=rebuilt['files'], sources=selected_sources, source_files=len(selected_sources),
                  original_inputs=[], build_log_sha256=sha(out / 'build.log'),
                  source_base_commit=manifest['source_base_commit'],ancestor_git_unavailable=True,
                  exported_source_commit=source_commit,
                  checker_sha256=sha(Path(__file__)), scope=__doc__)
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print('PASS package reproduction:', len(result['sources']), 'sources,',len(result['files']),'files')


if __name__ == '__main__':
    main()
