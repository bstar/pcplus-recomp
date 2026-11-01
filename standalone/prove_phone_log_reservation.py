#!/usr/bin/env python3
"""Reproduce the claim-linked parent and repeat its DOS composition from public sources."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

from omf_imports import records

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_source_paths(original, repeated, fresh):
    a, b = records(original.read_bytes()), records(repeated.read_bytes())
    assert len(a) == len(b)
    changed = []
    for index, (left, right) in enumerate(zip(a, b)):
        if left == right:
            continue
        assert left[0] == right[0]
        if left[0] == 0x80:  # THEADR: filename length and filename.
            offset = 0
        else:  # Watcom dependency comment: class, timestamp, filename.
            assert left[0] == 0x88 and left[1][:2] == right[1][:2] == b'\x80\xe9'
            assert left[1][:6] == right[1][:6]
            offset = 6
        x, y = left[1], right[1]
        assert x[offset] == len(x) - offset - 1 and y[offset] == len(y) - offset - 1
        old_name = Path(x[offset + 1:].decode('ascii')).relative_to(ROOT)
        new_name = Path(y[offset + 1:].decode('ascii')).relative_to(fresh)
        assert old_name == new_name and '..' not in old_name.parts
        assert sha(ROOT / old_name) == sha(fresh / new_name)
        changed.append(index)
    return changed


def flags_for(manifest):
    fields = {'experimental_external_render': 'external-render', 'experimental_mouse': 'mouse',
              'experimental_notice_input': 'notice-input', 'experimental_aspect_keys': 'aspect-keys',
              'experimental_directory_keys': 'directory-keys', 'terminal_exit_guard': 'exit-guard',
              'banked_process': 'process-bank', 'experimental_session_capture': 'session-capture',
              'experimental_session_projection': 'session-projection', 'experimental_session_baseline': 'session-baseline',
              'experimental_register_handoff': 'register-handoff', 'experimental_session_controls': 'session-controls',
              'experimental_hook_return': 'hook-return', 'experimental_hook_execute': 'hook-execute',
              'experimental_hook_modem': 'hook-modem', 'experimental_hook_input': 'hook-input',
              'experimental_hook_apply': 'hook-apply', 'experimental_hook_lookup': 'hook-lookup',
              'terminal_traps': 'traps', 'experimental_custom_irq': 'custom-irq', 'special_edition': 'special-edition',
              'experimental_native_reset_bank': 'native-reset-bank', 'native_reset_transaction': 'native-reset-transaction'}
    flags = ['--' + flag for field, flag in fields.items() if manifest.get(field)]
    if manifest.get('experimental_notice_input'):
        flags += ['--notice-sound']
    if manifest.get('experimental_native_reset_bank') and not manifest.get('native_reset_overlay'):
        flags += ['--native-reset-static']
    return flags + ['--phone-log-reservations'] + (['--phone-log-startup'] if manifest.get('experimental_phone_log_startup') else [])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--terminal', type=Path, required=True)
    parser.add_argument('--dos', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    parent, dos, out = args.terminal.resolve(), args.dos.resolve(), args.output.resolve()
    assert all(p.is_relative_to(ROOT / 'build') for p in (parent, dos, out)) and not out.exists()
    manifest = json.loads((parent / 'manifest.json').read_text())
    reference = json.loads((dos / 'result.json').read_text())
    assert manifest['experimental_phone_log_reservations'] and reference['passed']
    assert all(sha(ROOT / name) == digest for name, digest in reference['inputs'].items())
    assert sha(parent / 'TERMINAL.EXE') == manifest['binary_sha256']
    sources = dict(manifest['sources'])
    # Builder imports and the DOS runner are public source too; no generated
    # Python state, native originals, install tree or analysis DB is copied.
    for path in (ROOT / 'standalone').rglob('*.py'):
        if '__pycache__' not in path.parts:
            sources[str(path.relative_to(ROOT))] = sha(path)
    for name in (*reference['inputs'], 'standalone/phone_log_bank_client.asm',
                 'standalone/phone_log_reservation_diagnostic.c', 'nix/flake.nix', 'nix/flake.lock', 'tools/dev'):
        sources[name] = sha(ROOT / name)
    fresh = out / 'source'
    for name, digest in sources.items():
        path = Path(name)
        assert not path.is_absolute() and '..' not in path.parts
        assert path.parts[0] not in ('build', 'analysis', 'install', 'original', 'originals', '.git')
        assert path.suffix.lower() not in ('.exe', '.obj', '.img', '.com', '.db', '.prm', '.fon')
        assert sha(ROOT / name) == digest
        target = fresh / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, target)
    assert not (fresh / 'build').exists() and not (fresh / 'analysis').exists()
    commands = [
        ('parent.log', [sys.executable, 'standalone/build_terminal.py', *flags_for(manifest)]),
        ('DOS.log', [sys.executable, 'standalone/test_phone_log_reservation_dos.py',
                     '--output', 'build/claims-regression']),
    ]
    for filename, command in commands:
        with (out / filename).open('w') as log:
            subprocess.run(command, cwd=fresh, stdout=log, stderr=log, check=True, timeout=180)
    rebuilt = fresh / 'build' / parent.name
    assert sha(rebuilt / 'TERMINAL.EXE') == manifest['binary_sha256']
    rebuilt_manifest = json.loads((rebuilt / 'manifest.json').read_text())
    expected_manifest = copy.deepcopy(manifest)
    variations = {}
    # The established ZMODEM builder retains source paths in THEADR/dependency
    # records. Preserve timestamps and verify those sole filename differences.
    for field in ('compiler_object_sha256', 'normalized_object_sha256'):
        old = manifest['zmodem_compiler_helper_adapters'][field]
        new = rebuilt_manifest['zmodem_compiler_helper_adapters'][field]
        if old != new:
            matches = [p for p in parent.glob('*.obj') if sha(p) == old]
            assert len(matches) == 1
            original, repeated = matches[0], rebuilt / matches[0].name
            assert sha(repeated) == new
            changed = verify_source_paths(original, repeated, fresh)
            variations[field] = dict(object=original.name, reference_sha256=old,
                                     rebuild_sha256=new, only_source_paths_differ=True,
                                     changed_records=changed)
            expected_manifest['zmodem_compiler_helper_adapters'][field] = new
    assert rebuilt_manifest == expected_manifest
    repeated = json.loads((fresh / 'build/claims-regression/result.json').read_text())
    assert repeated['passed'] and repeated['inputs'] == reference['inputs']
    for variant in ('near', 'far', 'bank'):
        assert repeated['variants'][variant] == reference['variants'][variant]
    assert all(sha(ROOT / name) == sha(fresh / name) == digest for name, digest in sources.items())
    report = dict(passed=True, terminal_sha256=manifest['binary_sha256'], source_count=len(sources),
                  sources=sources, original_inputs=[], actual_DOS_workflows=15,
                  repeated_DOS_sha256=sha(fresh / 'build/claims-regression/result.json'),
                  terminal_memory=manifest['memory_layout'], flags=flags_for(manifest),
                  source_path_object_variations=variations,
                  limitations=['Exact public-source parent rebuild and queue/claims DOS composition; no live logger startup/events/poll or hardware claim.'],
                  artifacts={str(p.relative_to(ROOT)): sha(p) for p in out.rglob('*') if p.is_file()})
    (out / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
    print('PASS:', len(sources), 'declared sources; exact terminal and three diagnostics; 15 repeated DOS cases')


if __name__ == '__main__':
    main()
