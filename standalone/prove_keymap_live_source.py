#!/usr/bin/env python3
"""Reproduce the Alt-F8 parent and its overlays from public manifest inputs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--parent', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    parent = args.parent.resolve()
    assert parent.is_relative_to(ROOT / 'build')
    manifest = json.loads(parent.with_name('manifest.json').read_text())
    assert manifest['experimental_keymap_editor']
    assert sha(parent) == manifest['binary_sha256']
    out = args.output.resolve()
    assert out.is_relative_to(ROOT / 'build') and not out.exists()
    fresh = out / 'source'
    fresh.mkdir(parents=True)
    sources = dict(manifest['sources'])
    recipe = 'standalone/meta_shared_connection_candidate_recipe.json'
    for name in (recipe, 'standalone/prove_keymap_live_source.py'):
        sources[name] = sha(ROOT / name)
    for name, digest in sources.items():
        relative = Path(name)
        assert not relative.is_absolute() and '..' not in relative.parts
        assert relative.parts[0] in ('src', 'reconstruction', 'standalone', 'tools', 'nix')
        assert relative.suffix.lower() not in ('.exe', '.com', '.obj', '.img', '.prm', '.kbd', '.db')
        assert sha(ROOT / relative) == digest, name
        target = fresh / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    env = dict(os.environ, GIT_CEILING_DIRECTORIES=str(out))
    assert subprocess.run(['git', 'rev-parse', '--show-toplevel'], cwd=fresh,
                          env=env, capture_output=True).returncode
    flags = json.loads((fresh / recipe).read_text())['terminal_flags']
    with (out / 'rebuild.log').open('w') as log:
        subprocess.run([sys.executable, 'standalone/build_terminal.py', *flags,
                        '--keymap-editor', '--output-dir', 'build/reproduced'],
                       cwd=fresh, env=env, stdout=log, stderr=log, check=True)
    products = {}
    for leaf in ('TERMINAL.EXE', 'PCLINE.OVL', 'PCMETA.OVL'):
        expected = sha(parent.with_name(leaf))
        assert sha(fresh / 'build/reproduced' / leaf) == expected, leaf
        products[leaf] = expected
    for name, digest in sources.items():
        assert sha(ROOT / name) == sha(fresh / name) == digest, name
    result = dict(passed=True, products=products, sources=sources,
                  original_inputs=[], ancestor_git_unavailable=True,
                  scope='Exact parent and matched overlays; outer pinned Nix supplies tools. No helper, BBS or physical acceptance.')
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print('PASS public-source Alt-F8 rebuild:', len(sources), 'inputs; three exact products')


if __name__ == '__main__':
    main()
