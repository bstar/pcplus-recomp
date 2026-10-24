#!/usr/bin/env python3
"""Compose a delayed-start width shell in a fresh private Synchronet runtime."""
import argparse
import json
from pathlib import Path
import shutil

import synchronet_peer_width_fixture as base

ROOT = base.ROOT


def setup(candidate):
    base.setup(candidate)
    target = candidate / 'mods/default.js'
    module = ROOT / 'lab/bbs/synchronet_aspect_width_module.js'
    shutil.copyfile(module, target)
    manifest = candidate / 'peer-width-instance.json'
    metadata = json.loads(manifest.read_text())
    metadata['fixture_inputs']['mods/default.js'] = base.sha(target)
    metadata['ASPECT_delayed_start'] = True
    metadata['composition_sources'] = {str(p.relative_to(ROOT)): base.sha(p) for p in
                                       [Path(__file__).resolve(), module]}
    metadata['scope'] += '; width requests wait for A from the real ASPECT child'
    manifest.write_text(json.dumps(metadata, indent=2) + '\n')
    verify(candidate)


def verify(candidate):
    base.verify(candidate)
    metadata = json.loads((candidate / 'peer-width-instance.json').read_text())
    assert metadata['ASPECT_delayed_start']
    for name, digest in metadata['composition_sources'].items():
        assert base.sha(ROOT / name) == digest, name


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['setup', 'start', 'stop', 'verify'])
    parser.add_argument('--candidate', type=Path, required=True)
    args = parser.parse_args()
    candidate = base.owned(args.candidate)
    if args.action in ('setup', 'verify'):
        globals()[args.action](candidate)
    else:
        verify(candidate)
        getattr(base, args.action)(candidate)
