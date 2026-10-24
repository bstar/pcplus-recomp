#!/usr/bin/env python3
"""Reproduce composed IRQ parent/editor/child and unchanged controls from source."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

from build_guarded_helper import ROOT, LOOKUP, FLAGS
from prove_custom_irq_source import sha

PRODUCTS = {LOOKUP: 'TERMINAL.EXE', LOOKUP + '-custom-irq': 'TERMINAL.EXE',
            'setup-mouse-notice-sound': 'PRMEDIT.EXE', 'setup-mouse-notice-sound-custom-irq': 'PRMEDIT.EXE',
            'aspect-register-parent': 'ASPECT.EXE', 'aspect-register-parent-custom-irq': 'ASPECT.EXE',
            'aspect-runner': 'ASPECT.EXE', 'aspect-compiler-dos': 'ASPCOMP.EXE'}
CONTROLS = {LOOKUP: '9dc1a1797710c35806224b40367fbc071cc20ee8fda0accd25c72aa446acda52',
            'setup-mouse-notice-sound': '79c3c09ca4699073f06bfc85c69e5bf967c7d13b361754f40495e21455a4144e',
            'aspect-register-parent': 'efb4083976464eff2ad1c00ae3a0d0fd1b5f4037c6e281d49f66a98e0d659d3b',
            'aspect-runner': '183f852dfe0a992faa29515e124eb3b6570e44578bdc25880a8a792a2bf7da3f',
            'aspect-compiler-dos': '18789792ad9e1be92057386d4405e4091e488d9bd8368490f414477e3dd5c8a2'}


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
        m = json.loads((base / 'manifest.json').read_text())
        assert not m.get('original_inputs') and sha(base / leaf) == m['binary_sha256']
        products[folder] = m['binary_sha256']
        if folder in CONTROLS:
            assert products[folder] == CONTROLS[folder]
        for name, digest in m['sources'].items():
            assert sha(ROOT / name) == digest and (name not in sources or sources[name] == digest), name
            sources[name] = digest
    for name in ['standalone/build_guarded_helper.py', 'standalone/prove_parent_custom_irq_source.py']:
        sources[name] = sha(ROOT / name)
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
    terminal = ['standalone/build_terminal.py', *FLAGS, '--hook-lookup', '--exit-guard', '--traps']
    editor = ['standalone/build_setup.py', '--mouse', '--notice-sound']
    child = ['standalone/build_aspect_process.py', '--notice-bank', '--notice-sound', '--notice-input',
             '--notice-help', '--help-resource', '--serial-bank', '--register-handoff']
    commands = [terminal, terminal + ['--custom-irq'], editor, editor + ['--custom-irq'],
                child, child + ['--custom-irq'], ['standalone/build_aspect_runner.py'],
                ['standalone/build_aspect_compiler_dos.py']]
    assert not (fresh / 'build').exists()
    with (out / 'build.log').open('w') as log:
        for command in commands:
            subprocess.run([sys.executable, *command], cwd=fresh, stdout=log, stderr=log, check=True, timeout=240)
    actual = {folder: sha(fresh / 'build' / folder / leaf) for folder, leaf in PRODUCTS.items()}
    assert actual == products
    for name, digest in sources.items():
        assert sha(ROOT / name) == digest
    result = dict(passed=True, products=products, controls=CONTROLS, sources=sources,
                  source_files=len(sources), commands=commands, original_inputs=[],
                  checker_sha256=sha(Path(__file__)), build_log_sha256=sha(out / 'build.log'), scope=__doc__)
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print('PASS parent IRQ reproduction:', len(sources), 'sources, eight products, five exact controls')


if __name__ == '__main__':
    main()
