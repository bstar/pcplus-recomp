#!/usr/bin/env python3
"""Build the retained queue in a dedicated code bank with actual DOS callbacks."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

from build_phone_log_file import stable_header
from omf_imports import rename_imports, records, externals

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/phone-log-bank'
ENTRIES = dict(phone_log_queue_initialize=0, phone_log_queue_configure=2,
               phone_log_queue_start=5, phone_log_queue_end=3, phone_log_queue_poll=0,
               phone_log_queue_retry=0, phone_log_queue_inspect=1,
               phone_log_decode_enabled=3, phone_log_read_stamp=1, phone_log_stamp_seconds=2)
LIFECYCLE_ENTRIES = dict(phone_log_lifecycle_ready=0, phone_log_lifecycle_begin=3,
                         phone_log_lifecycle_end=1, phone_log_lifecycle_service=0,
                         phone_log_lifecycle_inspect=1)
ALIASES = {name: name + '_impl' for name in ENTRIES}
ALIASES.update({name: 'phone_' + name + '_service' for name in
                ['memcpy', 'memset', 'memcmp', 'strchr', 'strcmp', 'strcpy', 'memmove']})
ALIASES.update(capture_fs_canonical='phone_canonical_service',
               capture_fs_attributes='phone_capture_attributes_service',
               capture_fs_create='phone_capture_create_service',
               capture_fs_open_append='phone_capture_open_service',
               capture_fs_seek_end='phone_capture_seek_service',
               capture_fs_write='phone_capture_write_service',
               capture_fs_close='phone_capture_close_service',
               intdos='phone_intdos_service', _dos_write='phone_dos_write_service')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_bank(out, reservations=False, startup=False, lifecycle=False, events=False, disk=False, controls=False, gateway=False, shared_paths=False):
    OUT = Path(out)
    OUT.mkdir(parents=True, exist_ok=True)
    flags = ['-q', '-bt=dos', '-0', '-ms', '-s', '-w4', '-we', '-zld']
    if reservations:
        flags += ['-dPHONE_LOG_QUEUE_RESERVATION', '-dCAPTURE_FIXED_RESERVATION']
    if disk:flags += ['-dPHONE_LOG_DISK']
    if controls:flags += ['-dPHONE_LOG_CONTROLS']
    if gateway:flags += ['-dTERMINAL_GATEWAY_FILES']
    sources = ['src/directory/' + name + '.c' for name in
               ['phone_log_queue', 'phone_log_format', 'phone_log_clock', 'phone_log_file', 'phone_log_fs']]
    aliases = dict(ALIASES)
    resource_source='src/config/'+('resource_path_shared.c' if shared_paths else 'resource_path.c')
    if lifecycle:
        sources += ['src/directory/phone_log_lifecycle.c']
        aliases.update({name: name + '_impl' for name in LIFECYCLE_ENTRIES})
    if events:
        assert lifecycle and startup and reservations
        sources += ['src/directory/phone_log_events.c']
        aliases.update({name: name + '_impl' for name in ('terminal_phone_log_events_ready',
            'terminal_phone_log_events_connected', 'terminal_phone_log_events_disconnected',
            'terminal_phone_log_events_shutdown')})
    if disk:
        assert events
        sources += ['src/directory/phone_log_disk.c']
        aliases['terminal_phone_log_disk_poll']='terminal_phone_log_disk_poll_impl'
        aliases['phone_log_disk_before_program']='phone_log_disk_before_program_impl'
    if controls:
        assert disk
        sources += ['src/directory/phone_log_controls.c']
        aliases['phone_log_controls_event']='phone_log_controls_event_impl'
    if startup:
        sources += ['src/directory/phone_log_startup.c', 'src/directory/phone_log_startup_owner.c', resource_source]
        aliases.update(phone_log_startup_owner='phone_log_startup_owner_impl',
            resource_pcplus_path='phone_resource_pcplus_path', resource_program_path='phone_resource_program_path')
    objects = []
    adapters = {}
    for source in sources:
        obj = OUT / (('phone_resource_path' if source == resource_source else Path(source).stem) + '.obj')
        includes = ['-i=' + str(ROOT / 'src/config')] if source.endswith('/phone_log_events.c') else []
        subprocess.run(['wcl', '-c', *flags, *includes, '-dPHONE_LOG_QUEUE_FAR', '-dPHONE_LOG_QUEUE_EXTERNAL', '-nt=PHONE_LOG_CODE', '-nc=FARCODE',
                        *['-d' + name + '=' + value for name, value in aliases.items()],
                        '-fo=' + obj.name, os.path.relpath(ROOT / source, OUT)], cwd=OUT, check=True)
        stable_header(obj, source)
        before = obj.read_bytes()
        imports = {name.decode('ascii') for kind, payload, raw in records(before) if kind == 0x8c
                   for name, index in externals(payload)}
        helpers = {name: value for name, value in {'__U4D': 'phone_u4div_service_',
                   '__U4M': 'phone_u4mul_service_'}.items() if name in imports}
        after, counts = rename_imports(before, helpers) if helpers else (before, {})
        obj.with_suffix('.compiler.obj').write_bytes(before)
        obj.write_bytes(after)
        adapters[obj.name] = dict(import_counts=counts, compiler_sha256=sha(obj.with_suffix('.compiler.obj')),
                                  normalized_sha256=sha(obj))
        objects.append(obj.name)
    asm_sources = ['src/terminal/phone_log_bank.asm', 'src/terminal/phone_log_resident.asm',
                   'src/terminal/phone_log_storage.asm', 'src/terminal/phone_log_end.asm']
    if lifecycle:asm_sources.insert(-1, 'src/terminal/phone_log_lifecycle_bank.asm')
    if events:asm_sources.insert(-1, 'src/terminal/phone_log_events_bank.asm')
    if disk:asm_sources.insert(-1, 'src/terminal/phone_log_disk_bank.asm')
    if controls:asm_sources.insert(-1, 'src/terminal/phone_log_controls_bank.asm')
    if startup:asm_sources.insert(-1, 'src/terminal/phone_log_startup_bank.asm')
    for source in asm_sources:
        obj = OUT / (('phone_resource_path' if source == 'src/config/resource_path.c' else Path(source).stem) + '.obj')
        subprocess.run(['nasm', '-fobj', '-I' + str(ROOT / 'src/terminal') + '/',
                        source, '-o', str(obj)], cwd=ROOT, check=True)
        objects.append(obj.name)
    names = sources + asm_sources + [
        *['src/directory/' + name + '.h' for name in
          ['phone_log_queue', 'phone_log_format', 'phone_log_clock', 'phone_log_file', 'phone_log_fs']],
        'src/capture/capture_fs.h', 'src/config/prm_dos.h', 'src/terminal/phone_log_abi.inc',
        'src/terminal/far_bridge.inc', 'standalone/build_phone_log_bank.py',
        'standalone/build_phone_log_file.py', 'standalone/omf_imports.py']
    if controls:names += ['src/directory/phone_log_controls.h']
    if disk:names += ['src/directory/phone_log_disk.h']
    if events:
        names += ['src/directory/phone_log_events.h']
    if lifecycle:
        names += ['src/directory/phone_log_lifecycle.h', 'src/terminal/phone_log_lifecycle_abi.inc']
    if reservations:
        names += ['src/capture/capture_file.h']
    if startup:
        names += ['src/directory/phone_log_startup.h', 'src/config/resource_path.h',
                  'src/terminal/session_baseline.h']
    objects.remove('phone_log_bank.obj')
    objects.insert(0, 'phone_log_bank.obj')
    return dict(objects=[OUT / name for name in objects], sources=[ROOT / name for name in names],
                adapters=adapters)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=OUT)
    parser.add_argument('--reservations', action='store_true')
    parser.add_argument('--lifecycle', action='store_true')
    args = parser.parse_args()
    out = args.output.resolve()
    flags = ['-q', '-bt=dos', '-0', '-ms', '-s', '-w4', '-we', '-zld']
    if args.reservations:
        flags += ['-dPHONE_LOG_QUEUE_RESERVATION', '-dCAPTURE_FIXED_RESERVATION']
    result = build_bank(out, reservations=args.reservations, lifecycle=args.lifecycle)
    objects = [path.name for path in result['objects']]
    client = 'standalone/phone_log_bank_client.asm'
    subprocess.run(['nasm', '-fobj', '-I' + str(ROOT / 'src/terminal') + '/',
                    client, '-o', str(out / 'phone_log_bank_client.obj')], cwd=ROOT, check=True)
    objects.append('phone_log_bank_client.obj')
    lifecycle_sources = []
    fault_adapter = None
    if args.lifecycle:
        # Diagnostic-only END-refusal callback; production build_bank never
        # rewrites this import. Actual near/stack/far ABI is retained.
        obj = out / 'phone_log_lifecycle.obj'
        original = obj.read_bytes()
        changed, counts = rename_imports(original, {'_phone_log_queue_end_impl': '_lifecycle_queue_end_service'})
        assert counts == {'_phone_log_queue_end_impl': 1}, counts
        obj.with_suffix('.production.obj').write_bytes(original)
        obj.write_bytes(changed)
        fault_adapter = dict(import_counts=counts, production_sha256=hashlib.sha256(original).hexdigest(),
                             diagnostic_sha256=sha(obj))
        client_lifecycle = 'standalone/phone_log_lifecycle_client.asm'
        subprocess.run(['nasm', '-fobj', '-I' + str(ROOT / 'src/terminal') + '/',
                        client_lifecycle, '-o', str(out / 'phone_log_lifecycle_client.obj')], cwd=ROOT, check=True)
        objects.append('phone_log_lifecycle_client.obj')
        lifecycle_sources.append(client_lifecycle)
    # Existing real capture backend remains resident, with the same diagnostic
    # prefix-write/ambiguous-close interception as the near/far-data tests.
    source = 'src/capture/capture_fs.c'
    subprocess.run(['wcl', '-c', *flags, '-dcapture_fs_write=phone_real_write',
                    '-dcapture_fs_close=phone_real_close', '-fo=capture_fs.obj',
                    os.path.relpath(ROOT / source, out)], cwd=out, check=True)
    stable_header(out / 'capture_fs.obj', source)
    objects.append('capture_fs.obj')
    extra_sources = []
    if args.reservations:
        extra_sources = ['src/capture/capture_file.c', 'src/capture/capture_reservation.c']
        for extra in extra_sources:
            name = Path(extra).stem + '.obj'
            subprocess.run(['wcl', '-c', *flags, '-fo=' + name,
                            os.path.relpath(ROOT / extra, out)], cwd=out, check=True)
            stable_header(out / name, extra)
            objects.append(name)
    diagnostic = ('standalone/phone_log_lifecycle_diagnostic.c' if args.lifecycle else
                  'standalone/phone_log_reservation_diagnostic.c' if args.reservations else 'standalone/phone_log_queue_diagnostic.c')
    if args.lifecycle:flags += ['-dPHONE_LOG_LIFECYCLE_BANK']
    subprocess.run(['wcl', *flags, '-dPHONE_LOG_QUEUE_FAR', '-k8192', '-fm=QUEUE.map', '-fe=QUEUE.EXE',
                    os.path.relpath(ROOT / diagnostic, out), *objects], cwd=out, check=True)
    names = [str(path.relative_to(ROOT)) for path in result['sources']] + [source, client,
             diagnostic] + extra_sources + lifecycle_sources
    if args.reservations:
        names += ['src/capture/capture_reservation.h']
    manifest = dict(original_inputs=[], sources={name: sha(ROOT / name) for name in names},
                    entries=ENTRIES, adapters=result['adapters'], outputs=dict(bank=dict(binary_sha256=sha(out / 'QUEUE.EXE'),
                    objects={name: sha(out / name) for name in objects})),
                    limitations=['Dedicated code/far-data diagnostic with actual DOS callbacks; not yet linked into terminal.',
                                 'Diagnostic-only near client/CONFIG callback substitutes must not enter the application.'])
    if args.lifecycle:
        manifest['lifecycle_entries'] = LIFECYCLE_ENTRIES
        manifest['diagnostic_end_refusal_adapter'] = fault_adapter
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print('Built dedicated phone-log code bank and eight resident callback adapters')


if __name__ == '__main__':
    main()
