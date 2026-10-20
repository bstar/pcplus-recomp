#!/usr/bin/env python3
"""Stage the owned Z-Machine door with an isolated save namespace and test menu.

Run with tools/bbs-dev against a fresh keyboard-stream checked candidate.
Story bytes remain ignored; no live user database or saved game is copied.
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

from enigma_key_stream_fixture import owned, setup, pid, reuse_stopped_base
from enigma_search_fixture import parse
from enigma_notes_fixture import sha


def prepare(candidate, server, *, base_ready=False):
    candidate, server = owned(candidate), server.resolve()
    assert candidate != server and not pid(candidate)
    catalog = server / 'local/infocom/catalog.json'
    game = next(g for g in json.loads(catalog.read_text())['games'] if g['id'] == 1)
    story = Path(game['path']).resolve()
    assert story.is_relative_to(server / 'local/infocom/games')
    assert game['title'] == 'Zork I: The Great Underground Empire'
    assert sha(story) == game['sha256'] and story.read_bytes()[0] == game['version']
    modules = ['core/zmachine_door/' + name for name in (
        'zmachine_door.js', 'zmachine_worker.js', 'save_dialog.js')]
    # Hash exact source inputs before copying; writable runtime state is synthetic.
    inputs = {p: sha(server / p) for p in modules}
    inputs['local/infocom/catalog.json'] = sha(catalog)
    inputs[str(story.relative_to(server))] = sha(story)
    assert not (candidate / 'infocom-save-instance.json').exists()
    if base_ready:
        reuse_stopped_base(candidate)
    else:
        setup(candidate)
    for name in modules:
        target = candidate / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(server / name, target)
    target_story = candidate / 'local/infocom' / story.name
    target_story.parent.mkdir(parents=True)
    shutil.copyfile(story, target_story)
    save_root = candidate / 'local/infocom/saves'
    save_root.mkdir(mode=0o700)
    menu_path = candidate / 'config/menus/loc-main.hjson'
    document = parse(candidate, menu_path)
    document['menus']['mainMenu']['submit'].insert(0, dict(
        value=dict(command='ZORK'), action='@menu:pcplusZorkSaveProbe'))
    document['menus']['pcplusZorkSaveProbe'] = dict(
        desc='Isolated Zork save/restore validation', module='zmachine_door',
        config=dict(name='PCPlus-Zork-Save-Probe', game_path=str(target_story),
                    nodeMax=0, interrupt='never', saveDirectory=str(save_root),
                    saveKey=game['sha256']))
    menu_path.write_text(json.dumps(document, indent=2) + '\n')
    assert inputs == {p: sha(server / p) for p in inputs}, 'Source changed during setup'
    staged = [*modules, str(target_story.relative_to(candidate)),
              'config/menus/loc-main.hjson', 'config/config.hjson',
              'core/client.js', 'core/key_stream.js']
    metadata = dict(source_inputs=inputs,
        fixture_inputs={p: sha(candidate / p) for p in staged},
        source_revision=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=server, text=True).strip(),
        story_sha256=game['sha256'], story_version=game['version'],
        save_root=str(save_root.relative_to(candidate)),
        scope='Exact owned door/worker/dialog, local story copy, synthetic account and direct ZORK menu. No live writes or saved games copied; not live custom menu acceptance.')
    (candidate / 'infocom-save-instance.json').write_text(json.dumps(metadata, indent=2) + '\n')
    print('Prepared isolated exact owned Z-Machine door; saves remain inside candidate.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--server-root', type=Path, required=True)
    args = parser.parse_args()
    prepare(args.candidate, args.server_root)
