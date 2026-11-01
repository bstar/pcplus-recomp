#!/usr/bin/env python3
"""Rebuild the startup-linked parent from a public commit and repeat native tests."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from build_phone_log_queue import ROOT, sha


def flags(manifest, startup, event_hooks=True, disk=True, controls=True):
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
        'experimental_status_geometry': 'status-geometry',
        'experimental_original_keys': 'original-keys', 'experimental_original_reference': 'original-reference',
        'experimental_native_reset_bank': 'native-reset-bank', 'native_reset_transaction': 'native-reset-transaction'}
    result = ['--' + flag for field, flag in fields.items() if manifest.get(field)]
    if manifest.get('experimental_notice_input'):
        result += ['--notice-sound']
    if manifest.get('experimental_native_reset_bank') and not manifest.get('native_reset_overlay'):
        result += ['--native-reset-static']
    if not startup:
        return result + ['--phone-log-bank']
    if manifest.get('experimental_phone_log_controls') and event_hooks and disk and controls:
        return result + ['--phone-log-controls']
    if manifest.get('experimental_phone_log_disk') and event_hooks and disk:
        return result + ['--phone-log-disk']
    if manifest.get('experimental_phone_log_events') and event_hooks:
        return result + ['--phone-log-events']
    return result + ['--phone-log-lifecycle' if manifest.get('experimental_phone_log_lifecycle') else '--phone-log-startup']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--terminal', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--commit', required=True)
    parser.add_argument('--baseline-commit', required=True)
    args = parser.parse_args()
    parent, output = args.terminal.resolve(), args.output.resolve()
    assert parent.is_relative_to(ROOT / 'build') and output.is_relative_to(ROOT / 'build') and not output.exists()
    manifest = json.loads((parent / 'manifest.json').read_text())
    assert manifest['experimental_phone_log_startup']
    assert sha(parent / 'TERMINAL.EXE') == manifest['binary_sha256']
    commit = subprocess.check_output(['git', 'rev-parse', args.commit + '^{commit}'], text=True).strip()
    baseline = subprocess.check_output(['git', 'rev-parse', args.baseline_commit + '^{commit}'], text=True).strip()
    tracked = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', commit], text=True).splitlines()
    names = set(manifest['sources']) | {name for name in tracked if name.startswith('standalone/') and name.endswith('.py')}
    names |= {'standalone/phone_log_startup_watch.asm', 'nix/flake.nix', 'nix/flake.lock', 'tools/dev'}
    reservations=bool(manifest.get('experimental_phone_log_reservations'))
    if reservations:
        names |= {'standalone/phone_log_claim_watch.asm', 'standalone/phone_log_reservation_diagnostic.c',
                  'standalone/phone_log_bank_client.asm'}
    controls=bool(manifest.get('experimental_phone_log_controls'))
    if controls:names |= {'standalone/phone_log_close_fault.asm'}
    disk=bool(manifest.get('experimental_phone_log_disk'))
    events=bool(manifest.get('experimental_phone_log_events'))
    if events:names |= {'standalone/phone_log_events_watch.asm'}
    if disk:names |= {'standalone/program_handoff_child.asm'}
    lifecycle=bool(manifest.get('experimental_phone_log_lifecycle'))
    if lifecycle:
        names |= {'standalone/phone_log_lifecycle_diagnostic.c', 'standalone/phone_log_lifecycle_client.asm'}
    output.mkdir(parents=True)
    sources, differences = {}, {}
    allowed = {'src/directory/phone_log_queue.c', 'src/directory/phone_log_queue.h',
        'standalone/build_phone_log_bank.py', 'standalone/build_terminal.py', 'standalone/terminal_memory.py'}
    for label, revision in [('source', commit), ('baseline', baseline)]:
        fresh = output / label
        available = set(subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', revision], text=True).splitlines())
        for name in sorted(names):
            assert not Path(name).is_absolute() and '..' not in Path(name).parts
            assert Path(name).parts[0] not in ('build', 'analysis', 'install', 'original', 'originals', '.git')
            assert Path(name).suffix.lower() not in ('.exe', '.obj', '.img', '.com', '.db', '.prm', '.fon')
            if label == 'baseline' and name not in available:
                continue
            data = subprocess.check_output(['git', 'show', revision + ':' + name])
            target = fresh / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            stamp = (ROOT / name).stat()
            os.utime(target, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
            if label == 'source':
                sources[name] = sha(target)
                if sha(ROOT / name) != sources[name]:
                    assert name in allowed, name
                    differences[name] = dict(worktree_sha256=sha(ROOT / name), public_sha256=sources[name])
    fresh = output / 'source'
    with (output / 'build.log').open('w') as log:
        subprocess.run([sys.executable, 'standalone/build_terminal.py', *flags(manifest, True)], cwd=fresh, stdout=log, stderr=log, check=True)
        rebuilt = fresh / 'build' / parent.name
        assert sha(rebuilt / 'TERMINAL.EXE') == manifest['binary_sha256']
        startup_target=rebuilt
        event_control={}
        if events:
            subprocess.run([sys.executable, 'standalone/test_phone_log_events_terminal.py',
                '--terminal', str(rebuilt), '--label', 'public-events'], cwd=fresh, stdout=log, stderr=log, check=True)
            if controls:
                for folder in (fresh,output/'baseline'):
                    subprocess.run([sys.executable, 'standalone/build_terminal.py', *flags(manifest, True, True, True, False)],
                        cwd=folder, stdout=log, stderr=log, check=True)
                def disk_control(folder):
                    products=[p for p in (folder/'build').glob('terminal-phone-log-bank-*/manifest.json')
                        if json.loads(p.read_text()).get('experimental_phone_log_disk') and
                        not json.loads(p.read_text()).get('experimental_phone_log_controls')]
                    assert len(products)==1
                    return products[0].parent
                disk_target=disk_control(fresh)
                assert sha(disk_target/'TERMINAL.EXE')==sha(disk_control(output/'baseline')/'TERMINAL.EXE')
                subprocess.run([sys.executable, 'standalone/test_phone_log_events_terminal.py',
                    '--terminal', str(disk_target), '--label', 'public-disk-controls-off'],
                    cwd=fresh, stdout=log, stderr=log, check=True)
            if disk:
                for folder in (fresh,output/'baseline'):
                    subprocess.run([sys.executable, 'standalone/build_terminal.py', *flags(manifest, True, True, False)],
                        cwd=folder, stdout=log, stderr=log, check=True)
                def ram_control(folder):
                    products=[p for p in (folder/'build').glob('terminal-phone-log-bank-*/manifest.json')
                        if json.loads(p.read_text()).get('experimental_phone_log_events') and
                        not json.loads(p.read_text()).get('experimental_phone_log_disk')]
                    assert len(products)==1
                    return products[0].parent
                ram_target=ram_control(fresh)
                assert sha(ram_target/'TERMINAL.EXE')==sha(ram_control(output/'baseline')/'TERMINAL.EXE')
                subprocess.run([sys.executable, 'standalone/test_phone_log_events_terminal.py',
                    '--terminal', str(ram_target), '--label', 'public-ram-events'],
                    cwd=fresh, stdout=log, stderr=log, check=True)
            for folder in (fresh,output/'baseline'):
                subprocess.run([sys.executable, 'standalone/build_terminal.py', *flags(manifest, True, False)],
                    cwd=folder, stdout=log, stderr=log, check=True)
            def lifecycle_control(folder):
                products=[p for p in (folder/'build').glob('terminal-phone-log-bank-*/manifest.json')
                    if json.loads(p.read_text()).get('experimental_phone_log_lifecycle') and
                    not json.loads(p.read_text()).get('experimental_phone_log_events')]
                assert len(products)==1
                return products[0].parent
            startup_target=lifecycle_control(fresh)
            baseline_lifecycle=lifecycle_control(output/'baseline')
            assert sha(startup_target/'TERMINAL.EXE')==sha(baseline_lifecycle/'TERMINAL.EXE')
            event_control=dict(unchanged_event_off_control_sha256=sha(startup_target/'TERMINAL.EXE'))
            if disk:event_control['unchanged_disk_off_control_sha256']=sha(ram_target/'TERMINAL.EXE')
            if controls:event_control['unchanged_controls_off_control_sha256']=sha(disk_target/'TERMINAL.EXE')
        subprocess.run([sys.executable, 'standalone/test_phone_log_startup_terminal.py',
            '--terminal', str(startup_target), '--label', 'public-startup'], cwd=fresh, stdout=log, stderr=log, check=True)
        if reservations:
            subprocess.run([sys.executable, 'standalone/test_phone_log_claim_terminal.py',
                '--terminal', str(startup_target), '--label', 'public-claims'], cwd=fresh, stdout=log, stderr=log, check=True)
            subprocess.run([sys.executable, 'standalone/test_phone_log_reservation_dos.py',
                '--output', 'build/public-queue-claims'], cwd=fresh, stdout=log, stderr=log, check=True)
        if lifecycle:
            subprocess.run([sys.executable, 'standalone/test_phone_log_lifecycle_dos.py',
                '--bank', '--output', 'build/public-lifecycle'], cwd=fresh, stdout=log, stderr=log, check=True)
        subprocess.run([sys.executable, 'standalone/build_terminal.py', *flags(manifest, False)], cwd=fresh, stdout=log, stderr=log, check=True)
        subprocess.run([sys.executable, 'standalone/build_terminal.py', *flags(manifest, False)], cwd=output / 'baseline', stdout=log, stderr=log, check=True)
    def control(folder):
        products = [p for p in (folder / 'build').glob('terminal-phone-log-bank-*/manifest.json')
            if not json.loads(p.read_text()).get('experimental_phone_log_startup')]
        assert len(products) == 1
        return products[0].parent / 'TERMINAL.EXE'
    assert sha(control(fresh)) == sha(control(output / 'baseline'))
    native_path = fresh / 'build/phone-log-startup-terminal/public-startup/result.json'
    native = json.loads(native_path.read_text())
    assert native['passed'] and len(native['cases']) == 7
    composition=dict(startup_capture_target_sha256=sha(startup_target/'TERMINAL.EXE'),**event_control)
    if reservations:
        capture_path=fresh/'build/phone-log-claim-terminal/public-claims/result.json'
        queue_path=fresh/'build/public-queue-claims/result.json'
        capture=json.loads(capture_path.read_text());queue=json.loads(queue_path.read_text())
        assert capture['passed'] and len(capture['cases'])==3 and all(capture['checks'].values())
        assert queue['passed'] and all(queue['checks'].values())
        assert sum(len(v['cases']) for v in queue['variants'].values())==15
        composition.update(repeated_capture_cases=3,repeated_queue_claim_cases=15,
            repeated_capture_sha256=sha(capture_path),repeated_queue_claim_sha256=sha(queue_path))
    if lifecycle:
        lifecycle_path=fresh/'build/public-lifecycle/result.json'
        life=json.loads(lifecycle_path.read_text())
        assert life['passed'] and all(life['checks'].values())
        assert sum(len(v['cases']) for v in life['variants'].values())==21
        assertions=sum(row['assertions'] for v in life['variants'].values() for row in v['cases'].values())
        composition.update(repeated_lifecycle_cases=21,repeated_lifecycle_assertions=assertions,
            repeated_lifecycle_sha256=sha(lifecycle_path))
    if events:
        events_path=fresh/'build/phone-log-events-terminal/public-events/result.json'
        event_report=json.loads(events_path.read_text())
        assert event_report['passed'] and all(event_report['checks'].values()) and len(event_report['cases'])==(19 if controls else 13 if disk else 8)
        assert event_report['terminal_sha256']==manifest['binary_sha256']
        if disk:
            ram_path=fresh/'build/phone-log-events-terminal/public-ram-events/result.json'
            ram_report=json.loads(ram_path.read_text())
            assert ram_report['passed'] and len(ram_report['cases'])==8 and all(ram_report['checks'].values())
            assert ram_report['terminal_sha256']==event_control['unchanged_disk_off_control_sha256']
            if controls:
                controls_off=fresh/'build/phone-log-events-terminal/public-disk-controls-off/result.json'
                off_report=json.loads(controls_off.read_text())
                assert off_report['passed'] and len(off_report['cases'])==13 and all(off_report['checks'].values())
                assert off_report['terminal_sha256']==event_control['unchanged_controls_off_control_sha256']
                composition.update(repeated_controls_cases=19,repeated_controls_sha256=sha(events_path),
                    repeated_disk_cases=13,repeated_disk_sha256=sha(controls_off))
            else:
                composition.update(repeated_disk_cases=13,repeated_disk_sha256=sha(events_path))
            composition.update(repeated_event_cases=8,repeated_event_sha256=sha(ram_path))
        else:
            composition.update(repeated_event_cases=8,repeated_event_sha256=sha(events_path))
    assert all(sha(fresh / name) == digest for name, digest in sources.items())
    result = dict(passed=True, source_commit=commit, baseline_commit=baseline, source_count=len(sources), sources=sources,
        declared_uncommitted_reservation_source_differences=differences, original_inputs=[],
        terminal_sha256=sha(rebuilt / 'TERMINAL.EXE'), repeated_native_cases=7,
        repeated_native_sha256=sha(native_path), unchanged_bank_control_sha256=sha(control(fresh)),
        build_log_sha256=sha(output / 'build.log'),**composition,
        scope=__doc__ + ' Public Git source only; no Git metadata, originals, previous objects or installed files copied. '
            'Require exact full executable despite declared pending-source differences. Compare disabled-feature '
            'control against the pre-feature public commit. Optional RAM-event hooks when selected; startup/capture regressions use the independently compared event-off control. Guarded disk polling only when selected; no complete transport, recovery UI, physical or deployment acceptance.')
    (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print('PASS public parent:', len(sources), 'sources; seven native startup cases; exact disabled-feature control')


if __name__ == '__main__':
    main()
