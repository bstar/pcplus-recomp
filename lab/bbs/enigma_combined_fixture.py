#!/usr/bin/env python3
"""Compose current compatibility candidates without live source/data writes."""
import argparse
import json
from pathlib import Path
import subprocess

from enigma_key_stream_fixture import ROOT, owned, pid, sha
from enigma_search_fixture import setup_search
from enigma_v86_fixture import prepare as v86
from enigma_infocom_save_fixture import prepare as infocom


def prepare(candidate, server):
    candidate, server = owned(candidate), server.resolve()
    assert not pid(candidate) and not (candidate / 'instance.json').exists()
    setup_search(candidate, server, transfer_bytes=0, uploads=True)
    v86(candidate, server, base_ready=True)
    infocom(candidate, server, base_ready=True)
    stages = [('enigma-transfer-owner', True), ('enigma-save-read', True),
              ('enigma-v86-input', False), ('enigma-v86-shutdown', False)]
    for name, needs_server in stages:
        command = ['python3', str(ROOT / 'lab/bbs/patches' / name / 'stage.py'), '--candidate', str(candidate)]
        if needs_server:
            command += ['--server-root', str(server)]
        subprocess.run(command, check=True)
    names = ['notes-instance.json', 'search-instance.json', 'v86-door-instance.json', 'infocom-save-instance.json']
    fixtures = {name: json.loads((candidate / name).read_text()) for name in names}
    paths = {path for meta in fixtures.values() for path in meta['fixture_inputs']}
    paths.update(['v86-input-bridge.json', 'v86-input-shutdown.json'])
    final_inputs = {name: sha(candidate / name) for name in sorted(paths)}
    source_inputs = {}
    for meta in fixtures.values():
        for name, digest in meta.get('source_inputs', meta.get('source_modules', {})).items():
            assert source_inputs.get(name, digest) == digest
            assert sha(server / name) == digest
            source_inputs[name] = digest
    marker = candidate / 'combined-instance.json'
    record = dict(stager_sha256=sha(Path(__file__)), patches=['keyboard-stream', *[name for name, _ in stages]],
        final_inputs=final_inputs, source_inputs=source_inputs,
        source_images=fixtures['v86-door-instance.json']['source_images'],
        metadata_before_composition={name: sha(candidate / name) for name in names},
        scope='One synthetic instance with owned search/index/NFO/upload, direct ZORK save probe and owned DOS Doors. Current four staged patch families plus keyboard stream. Final shared config/module hashes rebound explicitly before runtime. No live deployment or whole custom board assertion.')
    marker.write_text(json.dumps(record, indent=2) + '\n')
    final_inputs['combined-instance.json'] = sha(marker)
    for name, meta in fixtures.items():
        meta['fixture_inputs'] = final_inputs
        meta['combined_fixture'] = True
        meta['scope'] += ' Explicit composed fixture; all final shared runtime inputs are frozen together.'
        (candidate / name).write_text(json.dumps(meta, indent=2) + '\n')
    instance = json.loads((candidate / 'instance.json').read_text())
    instance['config_sha256'] = sha(candidate / 'config/config.hjson')
    (candidate / 'instance.json').write_text(json.dumps(instance, indent=2) + '\n')
    print('Composed five patch families:', len(final_inputs), 'shared frozen runtime inputs')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--server-root', type=Path, required=True)
    args = parser.parse_args()
    prepare(args.candidate, args.server_root)
