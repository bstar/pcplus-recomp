#!/usr/bin/env python3
"""Drive the exact owned file-search/index/details route from real DOS."""
import argparse
import asyncio
import contextlib
import json
from pathlib import Path
import re
import shutil

import test_dos
from enigma_notes_dos import sha,messages
from enigma_key_stream_fixture import ROOT,PORT,owned,verify_running


async def run(args):
    assert re.fullmatch(r'[A-Za-z0-9_-]+',args.label)
    candidate=owned(args.candidate);server=args.server_root.resolve();log=verify_running(candidate)
    metadata=json.loads((candidate/'search-instance.json').read_text())
    assert metadata['route']=='owned-search-index-details'
    for p,h in metadata['fixture_inputs'].items():assert sha(candidate/p)==h,p
    for p,h in metadata['source_inputs'].items():assert sha(server/p)==h,p
    for p,h in metadata['source_modules'].items():assert sha(candidate/p)==h,p
    out=ROOT/'build/bbs-lab/results/enigma'/args.label;out.mkdir(parents=True,exist_ok=False)
    stage=out/'program';stage.mkdir();binary=ROOT/'build/terminal/TERMINAL.EXE'
    shutil.copyfile(binary,stage/'TERMINAL.EXE')
    sources={f'candidate/{p}':candidate/p for p in [*metadata['fixture_inputs'],*metadata['source_modules']]}
    sources.update({f'source_board/{p}':server/p for p in [*metadata['source_inputs'],'core/client.js']})
    sources.update({'terminal':binary,'staged_terminal':stage/'TERMINAL.EXE','runner':Path(__file__),'harness':Path(test_dos.__file__),
                    'fixture':ROOT/'lab/bbs/enigma_search_fixture.py','notes_fixture':ROOT/'lab/bbs/enigma_notes_fixture.py'})
    before={p:sha(f) for p,f in sources.items()};count=messages(candidate)
    log_inode,log_offset=log.stat().st_ino,log.stat().st_size
    canonical=json.loads((ROOT/'lab/bbs/editor-recipes.json').read_text())['enigma_unsaved']['keyboard_input']
    prefix=canonical[:canonical.index('M enter')].replace('n p6000 n p3000 enter','n p6000 enter')
    body=('c-y F enter p1400 S enter p1400 P C P L U S space P R O B E enter p1800 '
          'down p400 pgdown p400 up p400 pgup p400 end p400 home p400 down p400 '
          'enter p1400 i p400 n p400 down p400 pgdown p400 up p400 pgup p400 '
          'end p400 home p400 q p1000 q p1000 c-y Z Z Z N O M A T C H enter '
          'p1400 q p1000 escape p800 Q enter p1000')
    keys=prefix+body
    assert len('ADDKEY p1000 '+keys+' p2000 a-x')<500
    options=argparse.Namespace(name='enigma',label=args.label,port=PORT,com=2,baud=19200,flow='HARD',packet_delay_ms=0,
        dial_fixture=True,directory_fixture=False,directory_browser=False,entry=3,binary=stage/'TERMINAL.EXE',
        config_fixture=False,keymap_fixture=ROOT/'build/keyboard-profiles/NETWORK.KBD',server_log=log,keys=keys,wait=2,timeout=190)
    with (out/'harness.log').open('w') as capture,contextlib.redirect_stdout(capture):code=await test_dos.run(options)
    harness=json.loads((out/'result.json').read_text())
    display=re.sub(rb'\x1b\[[0-?]*[ -/]*[@-~]',b'',(out/'display.bin').read_bytes()).decode('cp437',errors='replace')
    (out/'display-clean.txt').write_text(display)
    pages=[tuple(map(int,p)) for p in re.findall(r'NFO \| lines (\d+)-(\d+)/(\d+)',display)]
    selected=list(map(int,re.findall(r'>PCPLUS PROBE (\d\d) \(1991\)[.]ZIP',display)))
    ranges=[tuple(map(int,p)) for p in re.findall(r'30 matches \| (\d+)-(\d+) displayed',display)]
    expected_pages=[(1,15,24),(2,16,24),(10,24,24),(9,23,24),(1,15,24),(10,24,24),(1,15,24)]
    expected_selected=[0,1,15,14,0,29,0,1,0]
    expected_ranges=[(1,14),(1,14),(15,28),(15,28),(1,14),(29,30),(1,14),(1,14),(1,14)]
    assert log.stat().st_ino==log_inode,'Log rotated; retain this run'
    with log.open('rb') as f:
        f.seek(log_offset);rows=[json.loads(line) for line in f if line.strip()]
    sessions={r['sessionId'] for r in rows if r.get('msg')=='User "loclab" successfully logged in'}
    own=[r for r in rows if r.get('sessionId') in sessions];menus=[r['menuName'] for r in own if r.get('menuName')]
    (out/'server-session.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in own))
    # Compare the actual route, including the normal return stack, not only
    # isolated page strings or a direct test-only game-details entry.
    first=menus.index('fileBaseMainMenu') if 'fileBaseMainMenu' in menus else len(menus)
    route=menus[first:]
    expected_route=['fileBaseMainMenu','fileBaseSearch','blackFlagZipResults','locGameDetails',
                    'blackFlagZipResults','fileBaseSearch','blackFlagZipResults','fileBaseSearch','fileBaseMainMenu','mainMenu']
    checks=dict(DOS_harness=code==0 and harness['passed'],unique_authenticated_session=len(sessions)==1,
        exact_owned_modules=all(sha(candidate/p)==h for p,h in metadata['source_modules'].items()),
        inputs_unchanged=before=={p:sha(f) for p,f in sources.items()},no_post_saved=count==messages(candidate),
        real_search_route=route==expected_route,
        title_search='Titles / filenames: PCPLUS PROBE' in display,
        index_selection=selected==expected_selected,index_paging=ranges==expected_ranges,
        selected_game_details='GAME DETAILS' in display and 'PCPLUS PROBE 01 (1991).ZIP' in display,
        diz_page='FILE_ID.DIZ | lines 1-6/6' in display and 'Synthetic FILE_ID.DIZ' in display,
        nfo_navigation=pages==expected_pages,bottom_content='PCPLUS NFO LINE 22 : synthetic game 01' in display,
        empty_search='Titles / filenames: ZZZNOMATCH' in display and '0 matches | 0 displayed' in display and 'No matching files.' in display)
    result=dict(passed=all(checks.values()),checks=checks,terminal_sha256=sha(binary),source_modules=metadata['source_modules'],
        source_inputs={k:before['source_board/'+k] for k in metadata['source_inputs']},input_hashes=before,
        pages=pages,expected_pages=expected_pages,selected=selected,expected_selected=expected_selected,
        ranges=ranges,expected_ranges=expected_ranges,route=route,expected_route=expected_route,
        menu_selection_sha256=metadata['menu_selection_sha256'],modem_packet_delay_ms=0,
        runner_sha256=sha(Path(__file__)),fixture_sha256=sha(ROOT/'lab/bbs/enigma_search_fixture.py'),
        scope='Actual DOS and immediate19200/HARD modeled modem through exact owned F/S menu, ANSI search art, search/index/details modules and selected theme settings. Real SQLite search over30 generated ZIPs with synthetic notes; list navigation, detail selection, NFO scroll, no-result search and return stack. Isolated patched server, not live-board installation or physical RS-232 validation.')
    (out/'search-checks.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(passed=result['passed'],checks=checks,selected=selected,ranges=ranges,pages=pages,route=route),indent=2))
    return 0 if result['passed'] else 1


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--server-root',type=Path,required=True);p.add_argument('--label',required=True)
    a=p.parse_args();raise SystemExit(asyncio.run(run(a)))
