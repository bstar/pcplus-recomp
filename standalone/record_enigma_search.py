#!/usr/bin/env python3
"""Record exact search-route success and the separate long-name download gap."""
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'lab/bbs'))
from enigma_search_fixture import parse
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()


def main(server):
    server=server.resolve();stage='build/bbs-lab/owned-enigma-search-01';candidate=ROOT/stage/'candidate'
    setup=read(stage+'/candidate/search-instance.json');prepared=read(stage+'/report.json')
    assert prepared['passed'] and prepared['stock_client_unchanged']
    assert prepared['nix_lock_sha256']==sha('nix/flake.lock')
    for p,h in setup['source_inputs'].items():assert hashlib.sha256((server/p).read_bytes()).hexdigest()==h,p
    for p,h in setup['source_modules'].items():assert hashlib.sha256((candidate/p).read_bytes()).hexdigest()==h,p
    for p,h in setup['fixture_inputs'].items():assert hashlib.sha256((candidate/p).read_bytes()).hexdigest()==h,p
    source_config=parse(candidate,server/'config/menus/file_base.hjson')
    menus=json.loads((candidate/'config/menus/loc-main.hjson').read_text())
    for name in setup['selected_menus']:assert menus['menus'][name]==source_config['menus'][name],name
    assert menus['prompts']['fileMenuCommand']==source_config['prompts']['fileMenuCommand']
    assert 'pcplusNotesProbe' not in menus['menus']
    source_theme=parse(candidate,server/'art/themes/black_flag/theme.hjson')
    theme=parse(candidate,candidate/'art/themes/luciano_blocktronics/theme.hjson')
    for name in setup['selected_theme']:assert theme['customization']['menus'][name]==source_theme['customization']['menus'][name],name
    for name in ('FMENU','FILPMPT','LOCSEARCH'):
        assert (candidate/f'art/themes/luciano_blocktronics/{name}.ANS').read_bytes()==(server/f'art/themes/black_flag/{name}.ANS').read_bytes()
    assert len(setup['archives'])==30
    with sqlite3.connect(f'file:{candidate/"db/file.sqlite3"}?mode=ro',uri=True) as db,sqlite3.connect(f'file:{candidate/"local/catalog/notes/index.sqlite3"}?mode=ro',uri=True) as notes:
        for archive in setup['archives']:
            p=candidate/'file_base/pcplus_games'/archive['name'];assert hashlib.sha256(p.read_bytes()).hexdigest()==archive['sha256']
            assert db.execute('SELECT file_name,file_sha256,storage_tag FROM file WHERE file_id=?',(archive['file_id'],)).fetchone()==(archive['name'],archive['sha256'],'exodos_games')
            with zipfile.ZipFile(p) as z:
                docs=notes.execute('SELECT d.member,d.text FROM document d JOIN archive a ON a.id=d.archive_id WHERE a.name=?',(archive['name'],)).fetchall()
                assert len(docs)==2 and all(z.read(member)==text.encode('ascii') for member,text in docs)
    query_path=stage+'/search-query-checks.json';queries=read(query_path)
    assert queries['passed'] and queries['checks']==11 and all(c['passed'] for c in queries['cases'])
    assert queries['checker_sha256']==sha('lab/bbs/check_enigma_search.js')
    assert queries['search_sha256']==setup['source_modules']['mods/black_flag_files/search.js']
    assert queries['file_entry_sha256']==hashlib.sha256((server/'core/file_entry.js').read_bytes()).hexdigest()
    dos_path='build/bbs-lab/results/enigma/owned-search-framed-01/search-checks.json';dos=read(dos_path)
    terminal=sha('build/terminal/TERMINAL.EXE')
    assert dos['passed'] and all(dos['checks'].values()) and dos['terminal_sha256']==terminal
    assert dos['runner_sha256']==sha('lab/bbs/enigma_search_dos.py') and dos['fixture_sha256']==sha('lab/bbs/enigma_search_fixture.py')
    assert dos['pages']==dos['expected_pages'] and dos['selected']==dos['expected_selected'] and dos['ranges']==dos['expected_ranges'] and dos['route']==dos['expected_route']
    assert dos['source_inputs']==setup['source_inputs'] and dos['source_modules']==setup['source_modules']
    transfer_path='build/bbs-lab/results/enigma/owned-game-transfer-02-wrapper/characterization.json';transfer=read(transfer_path)
    assert transfer['terminal_sha256']==terminal and transfer['inputs_unchanged'] and transfer['no_post_saved']
    assert transfer['runner_sha256']==sha('lab/bbs/enigma_game_transfer_dos.py')
    assert not transfer['transfer_passed'] and not transfer['received_files']
    assert transfer['protocol_checks']['DOS_normal_exit'] and transfer['protocol_checks']['hardware_restored'] and transfer['protocol_checks']['no_leftover_staging']
    assert any(o['name']=='PCPLUS PROBE 01 (1991).ZIP' and o['size']==1301 and o['data_crc_verified'] for o in transfer['wire_offers'])
    replay_path=stage+'/wire-name-replay.json';replay=read(replay_path)
    assert replay['passed'] and replay['terminal_sha256']==terminal
    assert replay['checker_sha256']==sha('standalone/check_game_wire_name.py')
    assert replay['header_source_sha256']==sha('src/transfer/batch_header.c')
    assert replay['capture_sha256']==sha('build/bbs-lab/results/enigma/owned-game-transfer-02/display.bin')
    assert [o['status'] for o in replay['observations']]==[2,0]
    proof_path='docs/validation/application-components-source-build.json';proof=read(proof_path)
    assert proof['passed'] and proof['outputs']['terminal/TERMINAL.EXE']['sha256']==terminal
    assert hashlib.sha256((server/'core/client.js').read_bytes()).hexdigest()==prepared['stock_client_sha256']
    result=dict(passed=True,navigation_verified=True,game_download_verified=False,compatibility_complete=False,live_server_modified=False,
        terminal_sha256=terminal,owned_upstream_revision=prepared['upstream_revision'],source_modules=setup['source_modules'],source_inputs=setup['source_inputs'],
        selected_menus=setup['selected_menus'],selected_theme=setup['selected_theme'],menu_selection_sha256=setup['menu_selection_sha256'],synthetic_archives=30,
        queries=dict(path=query_path,sha256=sha(query_path),checks=queries),
        DOS=dict(path=dos_path,sha256=sha(dos_path),checks=dos['checks'],selected=dos['selected'],ranges=dos['ranges'],NFO_pages=dos['pages'],route=dos['route']),
        game_download=dict(path=transfer_path,sha256=sha(transfer_path),passed=False,wire_offers=transfer['wire_offers'],received_files=transfer['received_files'],
            checks=transfer['protocol_checks'],errors=transfer['protocol_errors'],wire_name_replay=dict(path=replay_path,sha256=sha(replay_path),checks=replay)),
        source_build_proof=dict(path=proof_path,sha256=sha(proof_path),outputs=proof['output_count']),nix_lock_sha256=sha('nix/flake.lock'),
        recorder_sha256=sha(Path(__file__).relative_to(ROOT)),whole_application_gates_closed=[],
        retained_prerequisite_failure=dict(label='owned-game-transfer-01',reason='Import selected a same-named standalone diagnostic, before any BBS connection; driver now asserts the laboratory module path.'),
        remaining=['Implement separate bounded wire names and DOS local names with deterministic collision/device/path handling; repeat exact game ZIP download and menu return.',
          'Approved live patch/restart and actual catalog retesting remain pending; selected source/menu/ANSI copies with generated data are isolated evidence.',
          'Physical modem timing/flow control,100ms key deadline and complete application gates remain open.'])
    (ROOT/'docs/validation/enigma-search.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Recorded actual owned search/index/DIZ/NFO route; long-name ZIP download remains a verified gap')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--server-root',type=Path,required=True)
    main(p.parse_args().server_root)
