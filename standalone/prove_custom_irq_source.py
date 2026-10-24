#!/usr/bin/env python3
"""Reproduce optional IRQ children and unchanged controls from declared sources."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PRODUCTS = {'aspect-serial': 'SERIAL.EXE', 'aspect-serial-custom-irq': 'SERIAL.EXE',
            'aspect-register-parent': 'ASPECT.EXE', 'aspect-register-parent-custom-irq': 'ASPECT.EXE',
            'aspect-runner': 'ASPECT.EXE'}
CONTROLS = {'aspect-serial': 'd2839c96f86574fd17a8d6e206b1f26fc16f9f3dd3510cea29488e12d6b6f6c5',
            'aspect-register-parent': 'efb4083976464eff2ad1c00ae3a0d0fd1b5f4037c6e281d49f66a98e0d659d3b',
            'aspect-runner': '183f852dfe0a992faa29515e124eb3b6570e44578bdc25880a8a792a2bf7da3f'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT / 'build') and not out.exists()
    sources = {}
    products = {}
    for folder, leaf in PRODUCTS.items():
        base = ROOT / 'build' / folder
        manifest = json.loads((base / 'manifest.json').read_text())
        assert not manifest.get('original_inputs')
        products[folder] = sha(base / leaf)
        assert products[folder] == manifest['binary_sha256']
        if folder in CONTROLS:
            assert products[folder] == CONTROLS[folder]
        for name, digest in manifest['sources'].items():
            assert sha(ROOT / name) == digest and (name not in sources or sources[name] == digest), name
            sources[name] = digest
    out.mkdir(parents=True)
    fresh = out / 'source'
    for name, digest in sources.items():
        path = Path(name)
        assert not path.is_absolute() and '..' not in path.parts and path.parts[0] not in ('build', 'analysis')
        assert path.suffix.lower() not in ('.exe', '.com', '.obj', '.o', '.img', '.prm', '.dir', '.xlt')
        target = fresh / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / path, target)
        assert sha(target) == digest
    assert not (fresh / 'build').exists()
    register = ['standalone/build_aspect_process.py', '--notice-bank', '--notice-sound', '--notice-input',
                '--notice-help', '--help-resource', '--serial-bank', '--register-handoff']
    commands = [['standalone/build_aspect_serial.py'], ['standalone/build_aspect_serial.py', '--custom-irq'],
                register, register + ['--custom-irq'], ['standalone/build_aspect_runner.py']]
    with (out / 'build.log').open('w') as log:
        for command in commands:
            subprocess.run([sys.executable, *command], cwd=fresh, stdout=log, stderr=log, check=True, timeout=240)
    actual = {folder: sha(fresh / 'build' / folder / leaf) for folder, leaf in PRODUCTS.items()}
    assert actual == products
    for name, digest in sources.items():
        assert sha(ROOT / name) == digest
    result = dict(passed=True, products=products, controls=CONTROLS, sources=sources,
                  source_files=len(sources), original_inputs=[], commands=commands,
                  checker_sha256=sha(Path(__file__)), build_log_sha256=sha(out / 'build.log'), scope=__doc__)
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print('PASS custom IRQ reproduction:', len(sources), 'sources, five products, three exact controls')


if __name__ == '__main__':
    main()
