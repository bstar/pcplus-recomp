#!/usr/bin/env python3
"""Rebuild both reader forms from an isolated export, then repeat real DOS IO."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--commit', help='Export only sources from this Git commit')
    args = parser.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT / 'build') and not out.exists()
    manifests = {name: json.loads((ROOT / 'build' / ('directory-reader' + suffix) / 'manifest.json').read_text())
                 for name, suffix in [('near', ''), ('bank', '-bank')]}
    sources = {}
    for name, manifest in manifests.items():
        assert not manifest['original_inputs']
        for path, digest in manifest['sources'].items():
            assert sha(ROOT / path) == digest
            assert path not in sources or sources[path] == digest
            sources[path] = digest
    for name in ('standalone/test_directory_reader_dos.py', 'standalone/test_terminal.py'):
        sources[name] = sha(ROOT / name)
    commit = subprocess.check_output(['git', 'rev-parse', '--verify', '--end-of-options',
        args.commit + '^{commit}'], cwd=ROOT, text=True).strip() if args.commit else None
    out.mkdir(parents=True)
    with tempfile.TemporaryDirectory(prefix='pcplus-directory-reader-') as tmp:
        export = Path(tmp) / 'source'
        export.mkdir()
        for path, digest in sources.items():
            relative = Path(path)
            assert not relative.is_absolute() and '..' not in relative.parts and relative.parts[0] in ('src', 'standalone')
            target = export / path
            target.parent.mkdir(parents=True, exist_ok=True)
            if commit:
                target.write_bytes(subprocess.check_output(['git', 'show', commit + ':' + path], cwd=ROOT))
            else:
                shutil.copyfile(ROOT / path, target)
            assert sha(target) == digest, path
        assert not any((p / '.git').exists() for p in [export, *export.parents])
        runs = {}
        for name, suffix in [('near', ''), ('bank', '-bank')]:
            command = [sys.executable, 'standalone/build_directory_reader.py'] + (['--bank'] if suffix else [])
            with (out / (name + '-build.log')).open('w') as log:
                subprocess.run(command, cwd=export, stdout=log, stderr=log, check=True)
            folder = export / 'build' / ('directory-reader' + suffix)
            rebuilt = json.loads((folder / 'manifest.json').read_text())
            assert rebuilt == manifests[name], name
            assert sha(folder / 'READER.EXE') == rebuilt['binary_sha256']
            for obj, digest in rebuilt['objects'].items():
                assert sha(folder / obj) == digest, obj
            with (out / (name + '-DOS.log')).open('w') as log:
                subprocess.run([sys.executable, 'standalone/test_directory_reader_dos.py',
                    '--build', str(folder), '--output', str(export / 'build' / (name + '-dos'))],
                    cwd=export, stdout=log, stderr=log, check=True)
            run = json.loads((export / 'build' / (name + '-dos/result.json')).read_text())
            assert run['passed'] and run['case_count'] == 25 and run['hardware_restored']
            assert run['binary_sha256'] == rebuilt['binary_sha256']
            runs[name] = dict(binary_sha256=run['binary_sha256'], objects=rebuilt['objects'],
                child_binary_sha256=rebuilt['child_binary_sha256'],DOS_cases=run['case_count'], DOS_assertions=run['native_assertions'],
                report='export/build/' + name + '-dos/result.json')
        shutil.copytree(export, out / 'export')
    for name, digest in sources.items():
        assert sha(ROOT / name) == digest, name
    captures = {str(p.relative_to(out)): sha(p) for p in out.rglob('*') if p.is_file()}
    result = dict(passed=True, source_files=len(sources), sources=sources,
        exported_source_commit=commit, ancestor_git_unavailable=True, original_inputs=[],
        runs=runs, DOS_cases=sum(r['DOS_cases'] for r in runs.values()),
        DOS_assertions=sum(r['DOS_assertions'] for r in runs.values()), captures_sha256=captures,
        checker_sha256=sha(Path(__file__)),
        toolchain_inputs={p: sha(ROOT / p) for p in ('nix/flake.nix', 'nix/flake.lock', 'tools/dev')},
        scope='Both exact DOS reader diagnostics, EXEC witness and eleven objects rebuilt from declared sources outside all Git ancestors;50 fresh8086 workflows repeat with independent complete-page/file/JFT/hardware audits. No original executables, user media, parent UI/serial integration or physical-driver timing claim.')
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(passed=True, sources=len(sources), DOS_cases=result['DOS_cases'], DOS_assertions=result['DOS_assertions'])))


if __name__ == '__main__':
    main()
