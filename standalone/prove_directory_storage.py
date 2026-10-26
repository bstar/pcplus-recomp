#!/usr/bin/env python3
"""Rebuild the guarded directory owner in isolation and repeat actual DOS IO."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--commit')
    args = parser.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT/'build') and not out.exists()
    baseline = ROOT/'build/directory-storage'
    manifest = json.loads((baseline/'manifest.json').read_text())
    assert not manifest['original_inputs'] and sha(baseline/'STORAGE.EXE') == manifest['binary_sha256']
    sources = dict(manifest['sources'])
    for name in ['standalone/test_directory_storage_dos.py', 'standalone/test_terminal.py',
                 'standalone/prove_directory_storage.py']:
        sources[name] = sha(ROOT/name)
    for name, digest in sources.items():
        assert sha(ROOT/name) == digest, name
    commit = subprocess.check_output(['git', 'rev-parse', '--verify', '--end-of-options',
        args.commit+'^{commit}'], cwd=ROOT, text=True).strip() if args.commit else None
    out.mkdir(parents=True)
    with tempfile.TemporaryDirectory(prefix='pcplus-directory-storage-') as tmp:
        export = Path(tmp)/'source'
        export.mkdir()
        for name, digest in sources.items():
            relative = Path(name)
            assert not relative.is_absolute() and '..' not in relative.parts
            assert relative.parts[0] in ('src', 'standalone', 'reconstruction')
            target = export/relative
            target.parent.mkdir(parents=True, exist_ok=True)
            if commit:
                target.write_bytes(subprocess.check_output(['git', 'show', commit+':'+name], cwd=ROOT))
            else:
                shutil.copyfile(ROOT/name, target)
            assert sha(target) == digest, name
        assert not any((p/'.git').exists() for p in [export, *export.parents])
        assert not (export/'analysis').exists()
        with (out/'build.log').open('w') as log:
            subprocess.run([sys.executable, 'standalone/build_directory_storage.py'],
                cwd=export, stdout=log, stderr=log, check=True)
        built = export/'build/directory-storage'
        rebuilt = json.loads((built/'manifest.json').read_text())
        assert rebuilt == manifest
        for name, digest in manifest['objects'].items():
            assert sha(built/name) == digest, name
        assert sha(built/'STORAGE.EXE') == manifest['binary_sha256']
        with (out/'test.log').open('w') as log:
            subprocess.run([sys.executable, 'standalone/test_directory_storage_dos.py',
                '--output', str(export/'build/dos-tests')], cwd=export,
                stdout=log, stderr=log, check=True)
        tested = json.loads((export/'build/dos-tests/result.json').read_text())
        assert tested['passed'] and tested['case_count'] == 22 and tested['native_assertions'] == 704
        assert tested['hardware_restored'] and tested['CWD_decoy_preserved']
        assert tested['binary_sha256'] == manifest['binary_sha256']
        assert tested['sources'] == manifest['sources']
        for name, digest in tested['test_sources'].items():
            assert sources[name] == digest
        shutil.copytree(export, out/'export')
    for name, digest in sources.items():
        assert sha(ROOT/name) == digest, name
    result = dict(passed=True, exported_source_commit=commit, original_inputs=[],
        ancestor_git_unavailable=True, source_files=len(sources), sources=sources,
        binary_sha256=manifest['binary_sha256'], objects=manifest['objects'],
        DOS_workflows=tested['case_count'], native_assertions=tested['native_assertions'],
        hardware_restored=True, CWD_decoy_preserved=True, limitations=manifest['limitations'],
        artifacts={str(p.relative_to(out)): sha(p) for p in out.rglob('*') if p.is_file()})
    (out/'result.json').write_text(json.dumps(result, indent=2)+'\n')
    print('PASS', len(sources), 'sources; executable/eight objects exact;',
          tested['case_count'], 'DOS workflows /', tested['native_assertions'], 'assertions')


if __name__ == '__main__':
    main()
