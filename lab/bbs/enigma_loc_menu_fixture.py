#!/usr/bin/env python3
"""Own an isolated stock ENiGMA instance with copied LoC main-menu code/form.

No private board DB/config is copied. Only selected main-menu objects and three
explicit module/layout files are staged; navigation is limited to stock M/F/G.
"""
import argparse
import json
import shutil
from pathlib import Path

from enigma_key_stream_fixture import ROOT, owned, pid
from enigma_peer_width_fixture import setup as base_setup, start as base_start, stop, verify as base_verify
from enigma_search_fixture import parse
from product_inputs import sha


def setup(candidate, server):
    candidate, server = owned(candidate), server.resolve()
    base_setup(candidate)
    names = ['mods/loc_main_menu/loc_main_menu.js', 'mods/loc_main_menu/classic-pillars.json',
             'mods/loc_main_menu/dos-doors.json', 'config/menus/black-flag.hjson']
    before = {name: sha(server / name) for name in names}
    for name in names[:3]:
        target = candidate / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(server / name, target)
    actual = parse(candidate, server / names[-1])
    path = candidate / 'config/menus/loc-main.hjson'
    menu = parse(candidate, path)
    main = actual['menus']['mainMenu']
    assert main['module'] == '@userModule:loc_main_menu' and main['prompt'] == 'locMainCommand'
    main['submit'] = [item for item in main['submit'] if item.get('value', {}).get('command') in ('M', 'F', 'G')]
    assert {item['value']['command'] for item in main['submit']} == {'M', 'F', 'G'}
    assert next(item['action'] for item in main['submit'] if item['value']['command'] == 'M') == '@menu:messageBaseMainMenu'
    menu['menus']['mainMenu'] = main
    menu['prompts']['locMainCommand'] = actual['prompts']['locMainCommand']
    path.write_text(json.dumps(menu, indent=2) + '\n')
    config_path = candidate / 'config/config.hjson'
    config = json.loads(config_path.read_text())
    config['general']['boardName'] = config['general']['prettyBoardName'] = 'LoSs oF CoNtRoL'
    config_path.write_text(json.dumps(config, indent=2) + '\n')
    # The base verifier still checks every copied upstream file; declare the
    # explicit menu/config overlay and additionally bind all custom inputs.
    base_path = candidate / 'peer-width-instance.json'
    base = json.loads(base_path.read_text())
    base['menu_sha256'], base['config_sha256'] = sha(path), sha(config_path)
    base_path.write_text(json.dumps(base, indent=2) + '\n')
    assert before == {name: sha(server / name) for name in names}
    record = dict(passed=True, source_root=str(server), source_inputs=before,
                  fixture_inputs={name: sha(candidate / name) for name in names[:3] +
                                  ['config/menus/loc-main.hjson', 'config/config.hjson']},
                  setup_sha256=sha(Path(__file__)),
                  scope=__doc__ + ' Synthetic stock user/database snapshots and independent writable paths. Copied current LoC art/form/module; selected M/F/G actions only, not whole live-board acceptance.')
    (candidate / 'loc-menu-instance.json').write_text(json.dumps(record, indent=2) + '\n')
    print('Prepared owned LoC menu fixture; source board unchanged')


def verify(candidate):
    base_verify(candidate)
    record = json.loads((candidate / 'loc-menu-instance.json').read_text())
    for name, digest in record['fixture_inputs'].items():
        assert sha(candidate / name) == digest, name
    for name, digest in record['source_inputs'].items():
        assert sha(Path(record['source_root']) / name) == digest, name
    return record


def start(candidate):
    verify(candidate)
    base_start(candidate)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=['setup', 'start', 'stop', 'verify'])
    p.add_argument('--candidate', type=Path, required=True)
    p.add_argument('--server-root', type=Path)
    a = p.parse_args()
    candidate = owned(a.candidate)
    if a.action == 'setup':
        assert a.server_root
        setup(candidate, a.server_root)
    else:
        globals()[a.action](candidate)
