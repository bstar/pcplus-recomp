#!/usr/bin/env python3
"""Prepare exact owned game-details code with only synthetic fixture data.

Run with tools/bbs-dev after check.py exports a fresh checked candidate.
This never changes the selected source board or copies its config/databases.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess

from enigma_key_stream_fixture import ROOT, STOCK, owned, setup, pid


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(candidate, server, decoder):
    candidate=owned(candidate);server=server.resolve()
    assert candidate!=server and not pid(candidate)
    assert not (candidate/'notes-instance.json').exists()
    paths=['mods/loc_game_details/loc_game_details.js','mods/black_flag_files/helpers.js']
    before={p:sha(server/p) for p in paths}
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=server,text=True).strip()
    assert revision==json.loads((candidate.parent/'report.json').read_text())['upstream_revision']
    setup(candidate)
    for rel in paths:
        target=candidate/rel;target.parent.mkdir(parents=True,exist_ok=True)
        assert not target.exists()
        shutil.copyfile(server/rel,target)
    assert before=={p:sha(server/p) for p in paths},'Source module changed while copying'
    # Parse only the isolated synthetic main menu with its existing dependency.
    menu=candidate/'config/menus/loc-main.hjson'
    parse="const fs=require('fs'),h=require(process.argv[1]+'/node_modules/hjson');process.stdout.write(JSON.stringify(h.parse(fs.readFileSync(process.argv[2],'utf8'))));"
    document=json.loads(subprocess.check_output(['node','-e',parse,str(candidate),str(menu)],text=True))
    with sqlite3.connect(f'file:{candidate/"db/file.sqlite3"}?mode=ro',uri=True) as db:
        file_id=db.execute("SELECT file_id FROM file WHERE file_name='PCXTEST.BIN' AND area_tag='pcplus_transfer'").fetchone()[0]
    document['menus']['mainMenu']['submit'].insert(0,dict(value=dict(command='NFO'),action='@menu:pcplusNotesProbe',extraArgs=dict(fileId=file_id)))
    document['menus']['pcplusNotesProbe']=dict(desc='Synthetic game notes probe',module='@userModule:loc_game_details',config=dict(interrupt='never'))
    menu.write_text(json.dumps(document,indent=2)+'\n')
    notes=candidate/'local/catalog/notes/index.sqlite3';notes.parent.mkdir(parents=True,exist_ok=True)
    assert not notes.exists()
    nfo='\n'.join(f'PCPLUS NFO LINE {i:02d} : synthetic navigation fixture' for i in range(1,23))
    diz='PCPLUS NOTES PROBE\nSynthetic FILE_ID.DIZ\nKeyboard navigation fixture\nNo game archive copied.'
    with sqlite3.connect(notes) as db:
        db.executescript('CREATE TABLE archive(id INTEGER PRIMARY KEY,name TEXT,storage TEXT,status TEXT,error TEXT);CREATE TABLE document(id INTEGER PRIMARY KEY,archive_id INTEGER,member TEXT,kind TEXT,text TEXT,sha256 TEXT,bytes INTEGER);')
        db.execute('INSERT INTO archive VALUES(1,?,?,?,NULL)',('PCXTEST.BIN','pcplus_transfer','complete'))
        for i,(kind,text) in enumerate([('diz',diz),('nfo',nfo)],1):
            db.execute('INSERT INTO document VALUES(?,1,?,?,?,?,?)',(i,'FILE_ID.DIZ' if kind=='diz' else 'PCPLUS.NFO',kind,text,hashlib.sha256(text.encode()).hexdigest(),len(text.encode())))
        assert db.execute('PRAGMA integrity_check').fetchone()==('ok',)
    if decoder=='baseline':
        shutil.copyfile(STOCK/'core/client.js',candidate/'core/client.js')
    instance=json.loads((candidate/'instance.json').read_text())
    instance['client_sha256']=sha(candidate/'core/client.js')
    instance['notes_decoder']=decoder
    (candidate/'instance.json').write_text(json.dumps(instance,indent=2)+'\n')
    metadata=dict(decoder=decoder,upstream_revision=revision,source_modules=before,
        staged_modules={p:sha(candidate/p) for p in paths},
        fixture_inputs={p:sha(candidate/p) for p in ['config/menus/loc-main.hjson','local/catalog/notes/index.sqlite3','core/client.js','core/key_stream.js']},
        synthetic_file_id=file_id,synthetic_note_sha256=dict(nfo=hashlib.sha256(nfo.encode()).hexdigest(),diz=hashlib.sha256(diz.encode()).hexdigest()),
        scope='Exact owned module/helper copies; only stock synthetic users/files and generated DIZ/NFO. No owned config, catalogs or databases copied; source board untouched.')
    assert metadata['source_modules']==metadata['staged_modules']
    (candidate/'notes-instance.json').write_text(json.dumps(metadata,indent=2)+'\n')
    print(json.dumps(metadata,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate',type=Path,required=True);p.add_argument('--server-root',type=Path,required=True)
    p.add_argument('--decoder',choices=['baseline','framed'],default='framed')
    a=p.parse_args();prepare(a.candidate,a.server_root,a.decoder)
