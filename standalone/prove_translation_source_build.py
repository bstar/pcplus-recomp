#!/usr/bin/env python3
"""Rebuild/retest this XLT checkpoint in an explicit source-only tree."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    files = ['reconstruction/translation/files.asm', 'reconstruction/translation/receive.asm',
             'reconstruction/translation/provenance.json', 'reconstruction/uart/encodings.inc',
             'src/translation/xlt_dos.c', 'src/translation/xlt_dos.h',
             'src/translation/xlt_dos_fs.c', 'src/translation/xlt_dos_fs.h',
             'standalone/build_translation.py', 'standalone/check_translation.py',
             'standalone/check_xlt_dos.py']
    outputs = ['build/translation/files.bin', 'build/translation/receive.bin',
               'build/translation/files.obj', 'build/translation/receive.obj',
               'build/translation-dos/REAL.EXE', 'build/translation-dos/FAULT.EXE']
    hashes = {name: digest(ROOT / name) for name in files}
    with tempfile.TemporaryDirectory(prefix='pcplus-xlt-source-') as temporary:
        tree = Path(temporary)
        for name in files:
            destination = tree / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, destination)
        assert not (tree / 'analysis').exists()
        for script in ('build_translation.py', 'check_translation.py', 'check_xlt_dos.py'):
            subprocess.run([sys.executable, str(tree / 'standalone' / script)], cwd=tree, check=True)
        for name in files:
            assert digest(tree / name) == hashes[name] == digest(ROOT / name)
        rebuilt = {name: digest(tree / name) for name in outputs}
        for name, value in rebuilt.items():
            assert digest(ROOT / name) == value, name
        result = {'passed': True, 'byte_identical_outputs': rebuilt,
                  'sources': hashes,
                  'proof_script_sha256': digest(Path(__file__)),
                  'toolchain_inputs': {name: digest(ROOT / name) for name in
                                       ('nix/flake.nix', 'nix/flake.lock')},
                  'tool_paths': {name: shutil.which(name) for name in
                                 ('nasm', 'wcl', 'wlink', 'dosbox-x')},
                  'original_inputs': [],
                  'scope': 'Only recovered XLT flat/OMF units and checked-loader DOS diagnostics; isolated CPU and DOS tests pass. Not the full interactive application.'}
    destination = ROOT / 'docs/validation/translation-source-build.json'
    destination.write_text(json.dumps(result, indent=2) + '\n')
    print('XLT isolated source build: six byte-identical outputs; CPU/DOS tests pass')


if __name__ == '__main__':
    main()
