#!/usr/bin/env python3
"""Stage bounded immutable save reads only in an isolated stopped door fixture."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from enigma_key_stream_fixture import ROOT, owned, pid, sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--server-root', type=Path, required=True)
    args = parser.parse_args()
    candidate = owned(args.candidate)
    assert not pid(candidate)
    meta_path = candidate / 'infocom-save-instance.json'
    meta = json.loads(meta_path.read_text())
    names = ['core/zmachine_door/' + name for name in ('save_dialog.js', 'zmachine_worker.js')]
    original = {name: sha(candidate / name) for name in names}
    assert all(digest == meta['source_inputs'][name] == sha(args.server_root / name) for name, digest in original.items())
    marker = candidate / 'save-read-experiment.json'
    target = candidate / 'core/zmachine_door/save_read.js'
    assert not marker.exists() and not target.exists()
    here = Path(__file__).resolve().parent
    patch, helper = here / 'save-read.patch', here / 'save_read.js'
    subprocess.run(['git', 'apply', '--check', str(patch)], cwd=candidate, check=True)
    shutil.copyfile(helper, target)
    subprocess.run(['git', 'apply', str(patch)], cwd=candidate, check=True)
    staged = {name: sha(candidate / name) for name in [*names, str(target.relative_to(candidate))]}
    record = dict(original_core=original, staged_core=staged,
        inputs={str(path.relative_to(ROOT)): sha(path) for path in (Path(__file__).resolve(), patch, helper)},
        authored_core={str(target.relative_to(candidate)): dict(source=str(helper.relative_to(ROOT)), sha256=sha(helper))},
        scope='Separate candidate: bounded structural/story validation and immutable read snapshot before VM restore; write/overwrite path remains upstream.')
    marker.write_text(json.dumps(record, indent=2) + '\n')
    meta['fixture_inputs'].update(staged)
    meta['fixture_inputs']['save-read-experiment.json'] = sha(marker)
    meta['save_read_experiment'] = True
    meta['scope'] += ' Explicit save-read experiment changes the dialog/worker and adds one authored helper.'
    meta_path.write_text(json.dumps(meta, indent=2) + '\n')
    print('Staged save-read candidate; live board unchanged')


if __name__ == '__main__':
    main()
