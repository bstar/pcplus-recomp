#!/usr/bin/env python3
"""Build near/far-data DOS queue diagnostics without original inputs."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

from build_phone_log_file import stable_header

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/phone-log-queue'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    sources = ['src/directory/phone_log_queue.c', 'src/directory/phone_log_format.c',
               'src/directory/phone_log_clock.c', 'src/directory/phone_log_file.c',
               'src/directory/phone_log_fs.c', 'src/capture/capture_fs.c']
    outputs = {}
    for variant in ['near', 'far']:
        out = OUT / variant
        out.mkdir(exist_ok=True)
        flags = ['-q', '-bt=dos', '-0', '-ms', '-s', '-w4', '-we', '-zld']
        if variant == 'far':
            flags += ['-dPHONE_LOG_QUEUE_FAR']
        objects = []
        for source in sources:
            name = Path(source).stem + '.obj'
            options = ['-dcapture_fs_write=phone_real_write', '-dcapture_fs_close=phone_real_close'] if source.endswith('/capture_fs.c') else []
            subprocess.run(['wcl', '-c', *flags, *options, '-fo=' + name,
                            os.path.relpath(ROOT / source, out)], cwd=out, check=True)
            stable_header(out / name, source)
            objects.append(name)
        subprocess.run(['wcl', *flags, '-k8192', '-fm=QUEUE.map', '-fe=QUEUE.EXE',
                        os.path.relpath(ROOT / 'standalone/phone_log_queue_diagnostic.c', out),
                        *objects], cwd=out, check=True)
        outputs[variant] = dict(binary_sha256=sha(out / 'QUEUE.EXE'),
                               objects={name: sha(out / name) for name in objects})
    names = sources + [
        'src/directory/phone_log_queue.h', 'src/directory/phone_log_format.h',
        'src/directory/phone_log_clock.h', 'src/directory/phone_log_file.h',
        'src/directory/phone_log_fs.h', 'src/capture/capture_fs.h', 'src/config/prm_dos.h',
        'standalone/phone_log_queue_diagnostic.c', 'standalone/build_phone_log_queue.py',
        'standalone/build_phone_log_file.py']
    result = dict(kind='source-only-phone-log-queue-format-clock', outputs=outputs,
                  sources={name: sha(ROOT / name) for name in names}, original_inputs=[],
                  limitations=['Actual DOS queue/file integration with selected failure injection, not the terminal/modem scheduler.',
                               'Four bounded event records; explicit queue-full/retry/recovery outcomes require caller handling.',
                               'Native PRM flag offset and text layout, maintained bounded formatting and calendar/generation policy.'])
    (OUT / 'manifest.json').write_text(json.dumps(result, indent=2) + '\n')
    print('Built near/far-data QUEUE.EXE diagnostics from', len(names), 'source files')


if __name__ == '__main__':
    main()
