#!/usr/bin/env python3
"""Build the retained queue in a dedicated code bank with actual DOS callbacks."""
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


def build_bank(out):
    OUT = Path(out)
    OUT.mkdir(parents=True, exist_ok=True)
    flags = ['-q', '-bt=dos', '-0', '-ms', '-s', '-w4', '-we', '-zld']
    sources = ['src/directory/' + name + '.c' for name in
               ['phone_log_queue', 'phone_log_format', 'phone_log_clock', 'phone_log_file', 'phone_log_fs']]
    objects = []
    adapters = {}
    for source in sources:
        obj = OUT / (Path(source).stem + '.obj')
        subprocess.run(['wcl', '-c', *flags, '-dPHONE_LOG_QUEUE_FAR', '-dPHONE_LOG_QUEUE_EXTERNAL', '-nt=PHONE_LOG_CODE', '-nc=FARCODE',
                        *['-d' + name + '=' + value for name, value in ALIASES.items()],
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
    for source in asm_sources:
        obj = OUT / (Path(source).stem + '.obj')
        subprocess.run(['nasm', '-fobj', '-I' + str(ROOT / 'src/terminal') + '/',
                        source, '-o', str(obj)], cwd=ROOT, check=True)
        objects.append(obj.name)
    names = sources + asm_sources + [
        *['src/directory/' + name + '.h' for name in
          ['phone_log_queue', 'phone_log_format', 'phone_log_clock', 'phone_log_file', 'phone_log_fs']],
        'src/capture/capture_fs.h', 'src/config/prm_dos.h', 'src/terminal/phone_log_abi.inc',
        'src/terminal/far_bridge.inc', 'standalone/build_phone_log_bank.py',
        'standalone/build_phone_log_file.py', 'standalone/omf_imports.py']
    objects.remove('phone_log_bank.obj')
    objects.insert(0, 'phone_log_bank.obj')
    return dict(objects=[OUT / name for name in objects], sources=[ROOT / name for name in names],
                adapters=adapters)


def main():
    flags = ['-q', '-bt=dos', '-0', '-ms', '-s', '-w4', '-we', '-zld']
    result = build_bank(OUT)
    objects = [path.name for path in result['objects']]
    client = 'standalone/phone_log_bank_client.asm'
    subprocess.run(['nasm', '-fobj', '-I' + str(ROOT / 'src/terminal') + '/',
                    client, '-o', str(OUT / 'phone_log_bank_client.obj')], cwd=ROOT, check=True)
    objects.append('phone_log_bank_client.obj')
    # Existing real capture backend remains resident, with the same diagnostic
    # prefix-write/ambiguous-close interception as the near/far-data tests.
    source = 'src/capture/capture_fs.c'
    subprocess.run(['wcl', '-c', *flags, '-dcapture_fs_write=phone_real_write',
                    '-dcapture_fs_close=phone_real_close', '-fo=capture_fs.obj',
                    os.path.relpath(ROOT / source, OUT)], cwd=OUT, check=True)
    stable_header(OUT / 'capture_fs.obj', source)
    objects.append('capture_fs.obj')
    subprocess.run(['wcl', *flags, '-dPHONE_LOG_QUEUE_FAR', '-k8192', '-fm=QUEUE.map', '-fe=QUEUE.EXE',
                    os.path.relpath(ROOT / 'standalone/phone_log_queue_diagnostic.c', OUT), *objects],
                   cwd=OUT, check=True)
    names = [str(path.relative_to(ROOT)) for path in result['sources']] + [source, client,
             'standalone/phone_log_queue_diagnostic.c']
    manifest = dict(original_inputs=[], sources={name: sha(ROOT / name) for name in names},
                    entries=ENTRIES, adapters=result['adapters'], outputs=dict(bank=dict(binary_sha256=sha(OUT / 'QUEUE.EXE'),
                    objects={name: sha(OUT / name) for name in objects})),
                    limitations=['Dedicated code/far-data diagnostic with actual DOS callbacks; not yet linked into terminal.',
                                 'Diagnostic-only near client/CONFIG callback substitutes must not enter the application.'])
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print('Built dedicated phone-log code bank and eight resident callback adapters')


if __name__ == '__main__':
    main()
