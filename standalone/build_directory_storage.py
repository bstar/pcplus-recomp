#!/usr/bin/env python3
"""Source-only DOS shared directory owner with real-kernel fault witnesses."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
from build_phone_log_file import stable_header

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'build/directory-storage'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    units = [
        ('storage', 'src/directory/directory_storage.c', ['capture_file_release=storage_test_release']),
        ('replace', 'src/directory/directory_replace.c', ['_dos_close=storage_test_close']),
        ('replace_fs', 'src/directory/directory_replace_fs.c',
         ['directory_replace_rename=storage_real_rename', 'directory_replace_delete=storage_real_delete']),
        ('capture', 'src/capture/capture_file.c', []),
        ('reservations', 'src/capture/capture_reservation.c', []),
        ('capture_fs', 'src/capture/capture_fs.c',
         ['capture_fs_canonical=storage_real_canonical', 'capture_fs_close=storage_real_capture_close']),
        ('diagnostic', 'standalone/directory_storage_diagnostic.c', [])]
    flags = ['-q', '-bt=dos', '-0', '-ms', '-s', '-w4', '-we', '-zld']
    for name, source, aliases in units:
        subprocess.run(['wcl', '-c', *flags, *['-d'+a for a in aliases], '-fo='+name+'.obj',
                        os.path.relpath(ROOT/source, OUT)], cwd=OUT, check=True)
        stable_header(OUT/(name+'.obj'), source)
    asm = 'reconstruction/directory_accounting/patch.asm'
    subprocess.run(['nasm', '-fobj', asm, '-o', str(OUT/'patch.obj')], cwd=ROOT, check=True)
    objects = [n+'.obj' for n, _, _ in units]+['patch.obj']
    subprocess.run(['wcl', *flags, '-k8192', '-fm=STORAGE.map', '-fe=STORAGE.EXE', *objects], cwd=OUT, check=True)
    names = [s for _, s, _ in units]+[asm, 'src/directory/directory_storage.h',
        'src/directory/directory_replace.h', 'src/directory/directory_replace_fs.h',
        'src/directory/directory_dos.h', 'src/capture/capture_file.h',
        'src/capture/capture_fs.h', 'src/capture/capture_reservation.h',
        'standalone/build_directory_storage.py', 'standalone/build_phone_log_file.py']
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    report = dict(kind='source-only-shared-directory-storage-owner', original_inputs=[],
        binary_sha256=sha(OUT/'STORAGE.EXE'), sources={n: sha(ROOT/n) for n in sorted(set(names))},
        objects={n: sha(OUT/n) for n in objects}, snapshot_bytes=222,
        limitations=['Component only; application selection adoption and UART handoff remain open.',
                     'DOS canonical identities exclude same-process owners, not external writers or host aliases.',
                     'Uncertain handles/recovery files retain claims until process exit.'])
    (OUT/'manifest.json').write_text(json.dumps(report, indent=2)+'\n')
    print('Built STORAGE.EXE', report['binary_sha256'])


if __name__ == '__main__':
    main()
