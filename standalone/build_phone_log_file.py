#!/usr/bin/env python3
"""Source-only checked append objects, host failure model and DOS diagnostic."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/phone-log-file'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable_header(path, source):
    raw = path.read_bytes()
    position = 0
    headers = []
    while position < len(raw):
        length = int.from_bytes(raw[position + 1:position + 3], 'little')
        end = position + 3 + length
        assert length and end <= len(raw) and sum(raw[position:end]) & 255 == 0
        if raw[position] == 0x80:
            headers.append((position, end))
        position = end
    assert position == len(raw) and len(headers) == 1 and headers[0][0] == 0
    end = headers[0][1]
    assert raw[3] == end - 5 and raw[4:end - 1].decode('ascii') == str(ROOT / source)
    name = source.encode('ascii')
    assert len(name) < 256
    prefix = b'\x80' + (len(name) + 2).to_bytes(2, 'little') + bytes([len(name)]) + name
    normalized = prefix + bytes([-sum(prefix) & 255]) + raw[end:]
    path.with_suffix('.raw.obj').write_bytes(raw)
    path.write_bytes(normalized)
    assert normalized[len(prefix) + 1:] == raw[end:]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    # OMF dependency records contain source paths/mtimes. The explicit manifest
    # binds every source/header instead. -zld removes volatile dependency
    # records; the checked THEADR rewrite retains a logical source identity.
    flags = ['-q', '-bt=dos', '-0', '-ms', '-s', '-w4', '-we', '-zld']
    def compile(name, source, defines=()):
        subprocess.run(['wcl', '-c', *flags, *['-d' + value for value in defines],
                        '-fo=' + name + '.obj', os.path.relpath(ROOT / source, OUT)], cwd=OUT, check=True)
        stable_header(OUT / (name + '.obj'), source)
    compile('file', 'src/directory/phone_log_file.c')
    compile('capture', 'src/capture/capture_fs.c')
    compile('rollback', 'src/directory/phone_log_fs.c')
    compile('capture_real', 'src/capture/capture_fs.c', ['capture_fs_write=phone_real_write', 'capture_fs_close=phone_real_close'])
    compile('rollback_real', 'src/directory/phone_log_fs.c', ['phone_log_fs_seek=phone_real_seek',
            'phone_log_fs_truncate=phone_real_truncate', 'phone_log_fs_commit=phone_real_commit'])
    subprocess.run(['wcl', *flags, '-k8192', '-fm=PHONEAPP.map', '-fe=PHONEAPP.EXE',
                    os.path.relpath(ROOT / 'standalone/phone_log_file_diagnostic.c', OUT), 'file.obj',
                    'capture_real.obj', 'rollback_real.obj'], cwd=OUT, check=True)
    subprocess.run(['cc', '-std=c99', '-Wall', '-Wextra', '-Werror', '-Wno-misleading-indentation',
                    '-O2', str(ROOT / 'standalone/phone_log_file_model.c'), '-o', str(OUT / 'model')], check=True)
    model = subprocess.check_output([str(OUT / 'model')], text=True)
    assert model == 'PASS 138 append cases, 7239 assertions\n', model
    (OUT / 'model.txt').write_text(model)
    names = ['standalone/build_phone_log_file.py', 'standalone/phone_log_file_diagnostic.c',
             'standalone/phone_log_file_model.c', 'src/directory/phone_log_file.c',
             'src/directory/phone_log_file.h', 'src/directory/phone_log_fs.c',
             'src/directory/phone_log_fs.h', 'src/capture/capture_fs.c', 'src/capture/capture_fs.h']
    manifest = dict(kind='source-only-checked-phone-log-append', binary_sha256=sha(OUT / 'PHONEAPP.EXE'),
                    model_cases=138, model_assertions=7239, original_inputs=[],
                    sources={name: sha(ROOT / name) for name in names},
                    objects={name: sha(OUT / name) for name in ['file.obj', 'capture.obj', 'rollback.obj']},
                    object_metadata='Only the checked THEADR filename is rewritten to its logical source path; all later records are byte-identical. Raw objects retained. Compiler -zld omits volatile dependency records, replaced by explicit source/header hashes.',
                    limitations=['Maintained append backend, not the exact recovered native controller.',
                                 'Host filesystem boundaries modeled; DOS diagnostic injects selected failure results around actual kernel IO.',
                                 'Foreground-only; cross-application file reservations and terminal lifecycle/banking integration remain open.'])
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print('Built checked append objects and DOS diagnostic;', model.strip())


if __name__ == '__main__':
    main()
