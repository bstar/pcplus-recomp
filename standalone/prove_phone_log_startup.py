#!/usr/bin/env python3
"""Export a public commit and rebuild/retest DOS log startup without originals."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from build_phone_log_queue import ROOT, sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--commit', required=True)
    parser.add_argument('--allow-queue-reservation-source-difference', action='store_true',
        help='Permit only the declared queue C/header source differences, still requiring exact objects/executables')
    args = parser.parse_args()
    build, output = args.build.resolve(), args.output.resolve()
    assert build.is_relative_to(ROOT / 'build') and output.is_relative_to(ROOT / 'build') and not output.exists()
    reference = json.loads((build / 'manifest.json').read_text())
    for name, digest in reference['sources'].items():
        assert sha(ROOT / name) == digest, name
    commit = subprocess.check_output(['git', 'rev-parse', args.commit + '^{commit}'], cwd=ROOT, text=True).strip()
    names = sorted(set(reference['sources']) | {'standalone/test_phone_log_startup_dos.py',
        'standalone/test_terminal.py', 'standalone/prove_phone_log_startup.py'})
    fresh = output / 'source'
    fresh.mkdir(parents=True)
    sources, differences = {}, {}
    permitted = {'src/directory/phone_log_queue.c', 'src/directory/phone_log_queue.h'} if args.allow_queue_reservation_source_difference else set()
    for name in names:
        data = subprocess.check_output(['git', 'show', commit + ':' + name], cwd=ROOT)
        path = fresh / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        sources[name] = sha(path)
        if sha(ROOT / name) != sources[name]:
            assert name in permitted, name
            differences[name] = dict(worktree_sha256=sha(ROOT / name), exported_sha256=sources[name])
    with (output / 'build.log').open('w') as log:
        subprocess.run([sys.executable, 'standalone/build_phone_log_startup.py', '--output', 'build/products'],
            cwd=fresh, stdout=log, stderr=log, check=True)
        repeated = json.loads((fresh / 'build/products/manifest.json').read_text())
        assert repeated['outputs'] == reference['outputs'], 'Executable/object bytes differ'
        subprocess.run([sys.executable, 'standalone/test_phone_log_startup_dos.py',
            '--build', 'build/products', '--output', 'build/native'], cwd=fresh,
            stdout=log, stderr=log, check=True)
    native = json.loads((fresh / 'build/native/result.json').read_text())
    assert native['passed'] and all(native['checks'].values())
    assert all(sha(fresh / name) == digest for name, digest in sources.items())
    result = dict(passed=True, source_commit=commit, source_count=len(sources), sources=sources,
        original_inputs=[], executable_and_object_bytes_identical=True,
        outputs=repeated['outputs'], repeated_native_workflows=sum(len(v['cases']) for v in native['variants'].values()),
        repeated_native_sha256=sha(fresh / 'build/native/result.json'),
        declared_queue_source_differences=differences, build_log_sha256=sha(output / 'build.log'),
        scope=__doc__ + ' No Git metadata, old objects or original installation is copied into the exported tree. '
            'Optional queue-source allowance does not relax exact binary/object agreement. '
            'No parent startup/banking, capture reservations, event hooks, scheduling or deployment acceptance.')
    (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print('PASS public-source rebuild:', len(sources), 'files;', result['repeated_native_workflows'], 'DOS workflows')


if __name__ == '__main__':
    main()
