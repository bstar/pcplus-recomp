#!/usr/bin/env python3
"""Actual DOS keys through an isolated exact owned game-details module.

Use tools/dev. The candidate must be prepared by enigma_notes_fixture.py and
started with enigma_key_stream_fixture.py through tools/bbs-dev.
"""
import argparse
import asyncio
import contextlib
import hashlib
import json
from pathlib import Path
import re
import shutil
import sqlite3

import test_dos
from enigma_key_stream_fixture import ROOT,PORT,owned,verify_running


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def messages(candidate):
    with sqlite3.connect(f'file:{candidate/"db/message.sqlite3"}?mode=ro',uri=True) as db:
        return db.execute('SELECT COUNT(*) FROM message').fetchone()[0]


async def run(args):
    assert re.fullmatch(r'[A-Za-z0-9_-]+',args.label)
    candidate=owned(args.candidate);server=args.server_root.resolve()
    log=verify_running(candidate);metadata=json.loads((candidate/'notes-instance.json').read_text())
    for p,h in metadata['fixture_inputs'].items():assert sha(candidate/p)==h,p
    for p,h in metadata['source_modules'].items():
        assert sha(server/p)==sha(candidate/p)==h,p
    out=ROOT/'build/bbs-lab/results/enigma'/args.label
    out.mkdir(parents=True,exist_ok=False);stage=out/'program';stage.mkdir()
    binary=ROOT/'build/terminal/TERMINAL.EXE';shutil.copyfile(binary,stage/'TERMINAL.EXE')
    sources={f'candidate/{p}':candidate/p for p in [*metadata['fixture_inputs'],*metadata['source_modules'],'config/config.hjson']}
    sources.update({f'source_board/{p}':server/p for p in [*metadata['source_modules'],'core/client.js']})
    sources.update({'terminal':binary,'staged_terminal':stage/'TERMINAL.EXE','runner':Path(__file__),'harness':Path(test_dos.__file__)})
    before={p:sha(f) for p,f in sources.items()};count=messages(candidate)
    log_inode,log_offset=log.stat().st_ino,log.stat().st_size
    canonical=json.loads((ROOT/'lab/bbs/editor-recipes.json').read_text())['enigma_unsaved']['keyboard_input']
    prefix=canonical[:canonical.index('M enter')].replace('n p6000 n p3000 enter','n p6000 enter')
    body=('c-y N F O enter p2000 i p600 n p600 down p600 pgdown p600 up p600 '
          'pgup p600 end p600 home p600 o p600 q p1500 N F O enter p1500 '
          'n p600 pgdown p600 q p1500')
    keys=prefix+body
    assert len('ADDKEY p1000 '+keys+' p2000 a-x')<500
    options=argparse.Namespace(name='enigma',label=args.label,port=PORT,
        com=2,baud=19200,flow='HARD',packet_delay_ms=0,dial_fixture=True,
        directory_fixture=False,directory_browser=False,entry=3,binary=stage/'TERMINAL.EXE',
        config_fixture=False,keymap_fixture=ROOT/'build/keyboard-profiles/NETWORK.KBD',
        server_log=log,keys=keys,wait=2,timeout=190)
    with (out/'harness.log').open('w') as capture,contextlib.redirect_stdout(capture):
        code=await test_dos.run(options)
    harness=json.loads((out/'result.json').read_text());display=(out/'display.bin').read_bytes()
    clean=re.sub(rb'\x1b\[[0-?]*[ -/]*[@-~]',b'',display).decode('cp437',errors='replace')
    (out/'display-clean.txt').write_text(clean)
    pages=[tuple(map(int,p)) for p in re.findall(r'NFO \| lines (\d+)-(\d+)/(\d+)',clean)]
    expected=[(1,15,24),(2,16,24),(10,24,24),(9,23,24),(1,15,24),(10,24,24),(1,15,24),(1,15,24),(10,24,24)]
    assert log.stat().st_ino==log_inode,'Server log rotated; retain run'
    with log.open('rb') as f:
        f.seek(log_offset);rows=[json.loads(line) for line in f if line.strip()]
    sessions={r['sessionId'] for r in rows if r.get('msg')=='User "loclab" successfully logged in'}
    own=[r for r in rows if r.get('sessionId') in sessions]
    menus=[r['menuName'] for r in own if r.get('menuName')]
    (out/'server-session.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in own))
    wire=(out/'bbs-sent.bin').read_bytes()
    checks=dict(DOS_harness=code==0 and harness['passed'],unique_authenticated_session=len(sessions)==1,
        exact_owned_module=all(sha(candidate/p)==h for p,h in metadata['source_modules'].items()),
        inputs_unchanged=before=={p:sha(f) for p,f in sources.items()},
        no_post_saved=count==messages(candidate) and not any('posted message to' in r.get('msg','') for r in own),
        overview=clean.count('OVERVIEW | lines')>=3,
        diz_page='FILE_ID.DIZ | lines 1-6/6' in clean and 'Synthetic FILE_ID.DIZ' in clean,
        nfo_page=bool(pages) and 'PCPLUS NFO LINE 01' in clean,
        exact_navigation=pages==expected,
        bottom_content='PCPLUS NFO LINE 22' in clean,
        menu_leave_reenter=menus.count('pcplusNotesProbe')==2,
        actual_profile_key_bytes=all(wire.count(seq)>=n for seq,n in [(b'\x1b[B',1),(b'\x1b[A',1),(b'\x1b[6~',2),(b'\x1b[5~',1),(b'\x1b[H',1),(b'\x1b[F',1)]))
    result=dict(passed=all(checks.values()),checks=checks,decoder=metadata['decoder'],terminal_sha256=sha(binary),
        source_modules=metadata['source_modules'],input_hashes=before,upstream_revision=metadata['upstream_revision'],
        pages=pages,expected_pages=expected,menus=menus,modem_packet_delay_ms=0,
        runner_sha256=sha(Path(__file__)),fixture_sha256=sha(ROOT/'lab/bbs/enigma_notes_fixture.py'),
        artifacts={p.name:sha(p) for p in out.iterdir() if p.is_file()},
        scope='Actual DOSBox-X19200/HARD/immediate modeled modem against exact owned game-details/helper code and real ENiGMA Client/MenuModule/FileEntry/SQLite. Synthetic account,file,DIZ,NFO and added NFO menu route; not the live custom search/list flow or physical RS-232 modem.')
    (out/'notes-checks.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(passed=result['passed'],checks=checks,pages=pages),indent=2))
    return 0 if result['passed'] else 1


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate',type=Path,required=True)
    p.add_argument('--server-root',type=Path,required=True);p.add_argument('--label',required=True)
    a=p.parse_args();raise SystemExit(asyncio.run(run(a)))
