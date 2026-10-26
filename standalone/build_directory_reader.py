#!/usr/bin/env python3
"""Build the incremental DOS directory owner and real-kernel diagnostic."""
import argparse
import hashlib
import json
import os
import re
from pathlib import Path
import subprocess
from build_phone_log_file import stable_header

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--bank', action='store_true')
    args = parser.parse_args()
    out = (args.output or ROOT / ('build/directory-reader-bank' if args.bank else 'build/directory-reader')).resolve()
    assert out.is_relative_to(ROOT / 'build')
    out.mkdir(parents=True, exist_ok=True)
    flags = ['-q', '-bt=dos', '-0', '-ms', '-s', '-w4', '-we', '-zld']
    units = [('reader', 'src/directory/directory_reader.c', []),
             ('filesystem', 'src/directory/directory_reader_fs.c', []),
             ('filesystem_real', 'src/directory/directory_reader_fs.c',
              ['-ddirectory_reader_fs_' + n + '=directory_reader_real_' + n for n in ('open', 'read', 'close')]),
             ('diagnostic', 'standalone/directory_reader_diagnostic.c', []),
             ('child', 'standalone/directory_reader_child.c', [])]
    for name, source, extra in units:
        extra = list(extra)
        if args.bank and name in ('reader', 'diagnostic'):
            extra += ['-dDIRECTORY_READER_FAR']
        if args.bank and name == 'reader':
            extra += ['-nt=DIRECTORY_CODE', '-nc=FARCODE'] + [
                '-ddirectory_reader_fs_' + n + '=directory_reader_bank_' + n + '_service'
                for n in ('open', 'read', 'close')]
        subprocess.run(['wcl', '-c', *flags, *extra, '-fo=' + name + '.obj',
                        os.path.relpath(ROOT / source, out)], cwd=out, check=True)
        stable_header(out / (name + '.obj'), source)
    objects = ['reader.obj', 'filesystem_real.obj', 'diagnostic.obj']
    if args.bank:
        subprocess.run(['nasm', '-fobj', '-I' + str(ROOT / 'src/terminal') + '/',
            'src/terminal/directory_reader_bank.asm', '-o', str(out / 'bank.obj')], cwd=ROOT, check=True)
        objects.append('bank.obj')
    subprocess.run(['wcl', *flags, '-k8192', '-fm=READER.map', '-fe=READER.EXE', *objects], cwd=out, check=True)
    subprocess.run(['wcl',*flags,'-k2048','-fm=INHERIT.map','-fe=INHERIT.EXE','child.obj'],cwd=out,check=True)
    names = [source for _, source, _ in units] + ['src/directory/directory_reader.h',
             'src/directory/directory_reader_fs.h', 'src/directory/directory_dos.h',
             'standalone/build_directory_reader.py', 'standalone/build_phone_log_file.py']
    if args.bank:
        names += ['src/terminal/directory_reader_bank.asm', 'src/terminal/far_bridge.inc']
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    result = dict(kind='source-only-incremental-directory-reader', original_inputs=[],
        sources={n: sha(ROOT / n) for n in sorted(set(names))},
        objects={n: sha(out / n) for n in ['reader.obj', 'filesystem.obj', 'filesystem_real.obj', 'diagnostic.obj','child.obj'] + (['bank.obj'] if args.bank else [])},
        binary_sha256=sha(out / 'READER.EXE'),
        child_binary_sha256=sha(out/'INHERIT.EXE'),
        bank=args.bank,
        limitations=['Foreground component; terminal UI/serial polling integration remains open.',
                     'Driver call duration and concurrent external file writers are not bounded.'])
    if args.bank:
        listing = (out / 'READER.map').read_text()
        symbols = {n: (int(s, 16), int(o, 16)) for s, o, n in re.findall(
            r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$', listing, re.M | re.I)}
        code = re.search(r'^DIRECTORY_CODE\s+FARCODE\s+\S+\s+([0-9a-f]+):([0-9a-f]+)\s+([0-9a-f]+)', listing, re.M | re.I)
        assert code and int(code[2], 16) == 0 and int(code[3], 16) < 65536
        bank = int(code[1], 16)
        for name in ('initialize', 'begin', 'step', 'cancel'):
            assert symbols['_directory_reader_' + name][0] == bank
        for name in ('open', 'read', 'close'):
            assert symbols['_directory_reader_bank_' + name + '_service'][0] == bank
            assert symbols['_directory_reader_bank_' + name + '_resident'][0] == symbols['_directory_reader_fs_' + name][0] != bank
        result['bank_layout'] = dict(relative_segment=bank, code_bytes=int(code[3], 16),
            public_far_entries=4, explicit_resident_FS_callbacks=3)
    (out / 'manifest.json').write_text(json.dumps(result, indent=2) + '\n')
    print('Built', out / 'READER.EXE', result['binary_sha256'])


if __name__ == '__main__':
    main()
