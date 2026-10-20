#!/usr/bin/env python3
"""Copy owned DOS door code/menu and private writable game-image clones."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

from enigma_key_stream_fixture import ROOT, owned, setup, pid, sha, reuse_stopped_base
from enigma_search_fixture import parse


def state(path):
    value = path.stat()
    return dict(inode=value.st_ino, bytes=value.st_size, mtime_ns=value.st_mtime_ns, sha256=sha(path))


def prepare(candidate, server, *, base_ready=False):
    candidate, server = owned(candidate), server.resolve()
    assert not pid(candidate)
    assert not (candidate / 'v86-door-instance.json').exists()
    if base_ready:
        reuse_stopped_base(candidate)
    else:
        setup(candidate)
    modules = ['core/v86_door/' + name for name in ('v86_door.js', 'v86_worker.js', 'isolated_worker.js',
        'isolated_worker_child.js', 'fat_image.js')]
    modules += ['core/dropfile.js', 'core/door_util.js', 'mods/loc_main_menu/loc_main_menu.js',
        'mods/loc_main_menu/classic-pillars.json', 'mods/loc_main_menu/dos-doors.json']
    sources = [*modules, 'misc/v86_bios/seabios.bin', 'misc/v86_bios/vgabios.bin',
        'config/menus/doors.hjson', 'config/menus/black-flag.hjson']
    original = {name: sha(server / name) for name in sources}
    for name in sources:
        if name.startswith('config/'):
            continue
        target = candidate / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(server / name, target)
    source_images = {}
    images = candidate / 'local/doors/images'
    images.mkdir(parents=True)
    for name in ('gwar', 'bre'):
        source = server / ('local/doors/images/' + name + '.img')
        before = state(source)
        target = images / source.name
        shutil.copyfile(source, target)
        assert state(source) == before and sha(target) == before['sha256']
        source_images[str(source.relative_to(server))] = before
    doors = parse(candidate, server / 'config/menus/doors.hjson')
    main = parse(candidate, server / 'config/menus/black-flag.hjson')
    menu_path = candidate / 'config/menus/loc-main.hjson'
    config = parse(candidate, menu_path)
    selected = ['doorsMainMenu', 'locGlobalWar', 'locBarrenRealms']
    for name in selected:
        config['menus'][name] = doors['menus'][name]
    # Only the selected two games are staged; remove unstaged library actions.
    config['menus']['doorsMainMenu']['submit'] = [entry for entry in config['menus']['doorsMainMenu']['submit']
        if entry['action'] != '@menu:locInfocomLibrary']
    for name, image in [('locGlobalWar', 'gwar'), ('locBarrenRealms', 'bre')]:
        settings = config['menus'][name]['config']
        assert settings['nodeMax'] == 1 and settings['isolateProcess'] is True
        settings['image'] = str(images / (image + '.img'))
        settings['biosPath'] = str(candidate / 'misc/v86_bios/seabios.bin')
        settings['vgaBiosPath'] = str(candidate / 'misc/v86_bios/vgabios.bin')
    config['prompts']['locMainCommand'] = main['prompts']['locMainCommand']
    config['menus']['mainMenu']['submit'] = [entry for entry in config['menus']['mainMenu']['submit']
        if entry.get('value', {}).get('command') != 'D']
    config['menus']['mainMenu']['submit'].insert(0, dict(value=dict(command='D'), action='@menu:doorsMainMenu'))
    menu_path.write_text(json.dumps(config, indent=2) + '\n')
    code = r'''const c=require('./core/oputil/oputil_common');c.initConfigAndDatabases(e=>{
if(e)throw e;const U=require('./core/user'),P=require('./core/user_property');
U.getUserIdAndName('loclab',(e,id)=>{if(e)throw e;
U.persistPropertyByUserId(id,P.RealName,'PCPlus Door Lab01',e=>{if(e)throw e;process.exit(0);});});});'''
    subprocess.run(['node', '-e', code], cwd=candidate, check=True)
    assert original == {name: sha(server / name) for name in sources}
    # Resolve the actual pinned package entry, rather than guessing its layout.
    entry = Path(subprocess.check_output(['node', '-p', 'require.resolve("v86")'], cwd=candidate, text=True).strip())
    dependency_inputs = {str(path.relative_to((candidate / 'node_modules').resolve())): sha(path) for path in (entry, entry.with_name('v86.wasm'))}
    staged = [*modules, 'misc/v86_bios/seabios.bin', 'misc/v86_bios/vgabios.bin',
        'config/menus/loc-main.hjson', 'config/config.hjson', 'core/client.js', 'core/key_stream.js']
    record = dict(source_inputs=original, source_images=source_images,
        fixture_inputs={name: sha(candidate / name) for name in staged}, dependency_inputs=dependency_inputs,
        initial_images={str(path.relative_to(candidate)): sha(path) for path in images.iterdir()},
        selected_menus=selected, synthetic_real_name='PCPlus Door Lab01', setup_sha256=sha(Path(__file__)),
        scope='Actual owned v86 modules/door menu/layout and BIOS, private writable clones of installed game images, synthetic BBS DB and player. Main D -> owned Doors -> two selected games; Infocom actions omitted. No live image writes or live custom Main Menu assertion.')
    (candidate / 'v86-door-instance.json').write_text(json.dumps(record, indent=2) + '\n')
    print('Prepared private GWAR/BRE image copies and owned door routes')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--server-root', type=Path, required=True)
    args = parser.parse_args()
    prepare(args.candidate, args.server_root)
