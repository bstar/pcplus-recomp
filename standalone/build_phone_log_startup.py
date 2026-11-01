#!/usr/bin/env python3
"""Build DOS saved-log startup/path selection with near/far queue storage."""
import argparse
import json
import os
from pathlib import Path
import subprocess
from build_phone_log_file import stable_header
from build_phone_log_queue import ROOT, sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    assert output.is_relative_to(ROOT / 'build') and not output.exists()
    output.mkdir(parents=True)
    sources = ['src/directory/' + n + '.c' for n in ['phone_log_startup',
        'phone_log_queue', 'phone_log_format', 'phone_log_clock', 'phone_log_file', 'phone_log_fs']]
    sources += ['src/capture/capture_fs.c', 'src/config/resource_path.c']
    products = {}
    for variant in ['near', 'far']:
        folder = output / variant
        folder.mkdir()
        flags = ['-q', '-bt=dos', '-0', '-ms', '-s', '-w4', '-we', '-zld']
        if variant == 'far':
            flags += ['-dPHONE_LOG_QUEUE_FAR']
        objects = []
        for source in sources:
            name = Path(source).stem + '.obj'
            subprocess.run(['wcl', '-c', *flags, '-fo=' + name,
                os.path.relpath(ROOT / source, folder)], cwd=folder, check=True)
            stable_header(folder / name, source)
            objects.append(name)
        subprocess.run(['wcl', *flags, '-k8192', '-fm=STARTUP.map', '-fe=STARTUP.EXE',
            os.path.relpath(ROOT / 'standalone/phone_log_startup_diagnostic.c', folder),
            *objects], cwd=folder, check=True)
        products[variant] = dict(binary_sha256=sha(folder / 'STARTUP.EXE'),
            objects={name: sha(folder / name) for name in objects})
    names = sources + [name.replace('.c', '.h') for name in sources] + [
        'src/config/prm_dos.h', 'standalone/phone_log_startup_diagnostic.c',
        'standalone/build_phone_log_startup.py', 'standalone/build_phone_log_queue.py',
        'standalone/build_phone_log_file.py']
    manifest = dict(kind='DOS-log-startup-path-queue-diagnostic', original_inputs=[],
        sources={name: sha(ROOT / name) for name in names}, outputs=products,
        limitations=['Near/far queue-data component; not wired into application startup/events/polling.',
            'No file opened/created/written until subsequent explicit connection events and queue polls.',
            'Fixed reservation integration and parent code banking remain separate.'])
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print('Built near/far STARTUP.EXE from', len(names), 'public source files')


if __name__ == '__main__':
    main()
