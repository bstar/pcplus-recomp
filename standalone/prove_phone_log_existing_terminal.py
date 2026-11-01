#!/usr/bin/env python3
"""Rebuild committed public sources and repeat existing-file and menu DOS tests."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from build_phone_log_queue import ROOT, sha
from prove_phone_log_startup_terminal import flags


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--terminal', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--commit', required=True)
    args = parser.parse_args()
    parent, output = args.terminal.resolve(), args.output.resolve()
    assert parent.is_relative_to(ROOT/'build') and output.is_relative_to(ROOT/'build')
    assert not output.exists()
    manifest = json.loads((parent/'manifest.json').read_text())
    assert manifest['experimental_phone_log_controls']
    assert sha(parent/'TERMINAL.EXE') == manifest['binary_sha256']
    revision = subprocess.check_output(['git', 'rev-parse', args.commit+'^{commit}'], text=True).strip()
    tracked = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', revision], text=True).splitlines()
    names = set(manifest['sources']) | {n for n in tracked if n.startswith('standalone/') and n.endswith('.py')}
    names |= {'standalone/phone_log_events_watch.asm', 'standalone/phone_log_close_fault.asm',
              'standalone/phone_log_write_fault.asm', 'standalone/program_handoff_child.asm',
              'nix/flake.nix', 'nix/flake.lock', 'tools/dev'}
    output.mkdir(parents=True)
    fresh, sources = output/'source', {}
    for name in sorted(names):
        relative = Path(name)
        assert not relative.is_absolute() and '..' not in relative.parts
        assert relative.parts[0] not in ('build', 'analysis', 'install', 'original', 'originals', '.git')
        assert relative.suffix.lower() not in ('.exe', '.obj', '.img', '.com', '.db', '.prm', '.fon')
        data = subprocess.check_output(['git', 'show', revision+':'+name])
        target = fresh/name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        stamp = (ROOT/name).stat()
        os.utime(target, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
        sources[name] = sha(target)
        assert sha(ROOT/name) == sources[name], name
    reports = {}
    with (output/'build.log').open('w') as log:
        subprocess.run([sys.executable, 'standalone/build_terminal.py', *flags(manifest, True)],
                       cwd=fresh, stdout=log, stderr=log, check=True)
        rebuilt = fresh/'build'/parent.name
        assert sha(rebuilt/'TERMINAL.EXE') == manifest['binary_sha256']
        for label, extra, expected in [('public-existing', ['--existing'], 5), ('public-controls', [], 19)]:
            subprocess.run([sys.executable, 'standalone/test_phone_log_events_terminal.py',
                            '--terminal', str(rebuilt), '--label', label, *extra],
                           cwd=fresh, stdout=log, stderr=log, check=True)
            path = fresh/'build/phone-log-events-terminal'/label/'result.json'
            report = json.loads(path.read_text())
            assert report['passed'] and all(report['checks'].values())
            assert len(report['cases']) == expected
            assert report['terminal_sha256'] == manifest['binary_sha256']
            assert all(row['passed'] and all(row['checks'].values()) for row in report['cases'])
            reports[label] = {'path': str(path.relative_to(ROOT)), 'sha256': sha(path), 'cases': expected}
    assert all(sha(fresh/name) == digest and sha(ROOT/name) == digest for name, digest in sources.items())
    result = dict(passed=True, source_commit=revision, source_count=len(sources), sources=sources,
                  terminal_sha256=sha(rebuilt/'TERMINAL.EXE'), reports=reports, original_inputs=[],
                  build_log_sha256=sha(output/'build.log'),
                  scope=__doc__+' Exact unchanged application; separate real partial-write/error fixtures; '
                  'no original installs, previous objects or Git metadata exported. '
                  'No physical disk failure, sustained transport or full-application acceptance.')
    (output/'result.json').write_text(json.dumps(result, indent=2)+'\n')
    print('PASS:', len(sources), 'public sources; exact terminal; five existing-file and 19 menu/disk cases')


if __name__ == '__main__':
    main()
