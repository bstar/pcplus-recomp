#!/usr/bin/env python3
"""Stage selected owned search/index menus with generated archive fixtures.

Use tools/bbs-dev and a new checked candidate. No live board changes; only
selected menu/theme objects, six modules and three ANSI assets are copied.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import zipfile

from enigma_key_stream_fixture import ROOT,owned,pid
from enigma_notes_fixture import prepare,sha


def parse(candidate,path):
    code="const fs=require('fs'),h=require(process.argv[1]+'/node_modules/hjson');process.stdout.write(JSON.stringify(h.parse(fs.readFileSync(process.argv[2],'utf8'))));"
    return json.loads(subprocess.check_output(['node','-e',code,str(candidate),str(path)],text=True))


def setup_search(candidate,server):
    candidate=owned(candidate);server=server.resolve();assert not pid(candidate)
    prepare(candidate,server,'framed')
    metadata=json.loads((candidate/'notes-instance.json').read_text())
    modules=['mods/black_flag_files/black_flag_files.js','mods/black_flag_files/search.js',
             'mods/loc_transfer_protocol_select/loc_transfer_protocol_select.js',
             'mods/loc_download_ready/loc_download_ready.js']
    sources=[*modules,
             'config/menus/file_base.hjson','art/themes/black_flag/theme.hjson',
             *['art/themes/black_flag/'+f+'.ANS' for f in ('FMENU','FILPMPT','LOCSEARCH')]]
    before={p:sha(server/p) for p in sources}
    for p in modules:
        dest=candidate/p;dest.parent.mkdir(parents=True,exist_ok=True)
        assert not dest.exists();shutil.copyfile(server/p,dest)
        metadata['source_modules'][p]=before[p];metadata['staged_modules'][p]=sha(dest)
    menus=parse(candidate,server/'config/menus/file_base.hjson')
    menu_path=candidate/'config/menus/loc-main.hjson';config=json.loads(menu_path.read_text())
    selected=['fileBaseMainMenu','fileBaseSearch','blackFlagZipResults','locGameDetails',
              'fileTransferProtocolSelection','locDownloadReady']
    selected_menus={p:menus['menus'][p] for p in selected}
    selected_prompts={'fileMenuCommand':menus['prompts']['fileMenuCommand']}
    config['menus'].update(selected_menus);config['prompts'].update(selected_prompts)
    # The actual F -> search route must be used; remove the direct notes probe.
    config['menus']['mainMenu']['submit']=[c for c in config['menus']['mainMenu']['submit'] if c.get('action')!='@menu:pcplusNotesProbe']
    del config['menus']['pcplusNotesProbe']
    menu_path.write_text(json.dumps(config,indent=2)+'\n')
    theme_path=candidate/'art/themes/luciano_blocktronics/theme.hjson'
    theme=parse(candidate,theme_path);source_theme=parse(candidate,server/'art/themes/black_flag/theme.hjson')
    selected_theme={p:source_theme['customization']['menus'][p] for p in selected if p in source_theme['customization']['menus']}
    theme.setdefault('customization',{}).setdefault('menus',{}).update(selected_theme)
    theme_path.write_text(json.dumps(theme,indent=2)+'\n')
    asset_hashes={}
    for name in ('FMENU','FILPMPT','LOCSEARCH'):
        dest=candidate/f'art/themes/luciano_blocktronics/{name}.ANS'
        shutil.copyfile(server/f'art/themes/black_flag/{name}.ANS',dest)
        asset_hashes[str(dest.relative_to(candidate))]=sha(dest)
    storage=candidate/'file_base/pcplus_games';storage.mkdir()
    runtime_path=candidate/'config/config.hjson';runtime=json.loads(runtime_path.read_text())
    runtime['fileBase']['storageTags']['exodos_games']=str(storage)
    runtime['fileBase']['areas']['pcplus_games']=dict(name='Synthetic PCPlus Games',desc='Generated archive navigation fixtures',storageTags=['exodos_games'],acs=dict(read='GM[users]',write='GM[users]',download='GM[users]'))
    runtime_path.write_text(json.dumps(runtime,indent=2)+'\n')
    notes_path=candidate/'local/catalog/notes/index.sqlite3';archives=[]
    with sqlite3.connect(candidate/'db/file.sqlite3') as db,sqlite3.connect(notes_path) as notes:
        for i in range(30):
            name=f'PCPLUS PROBE {i:02d} (1991).ZIP';path=storage/name
            nfo='\n'.join(f'PCPLUS NFO LINE {n:02d} : synthetic game {i:02d}' for n in range(1,23))
            diz=f'PCPLUS PROBE {i:02d}\nSynthetic FILE_ID.DIZ\nKeyboard navigation fixture\nGenerated archive; no game copied.'
            with zipfile.ZipFile(path,'x') as z:
                for member,text in [('FILE_ID.DIZ',diz),('PCPLUS.NFO',nfo),('README.TXT',f'Synthetic navigation archive {i:02d}.')]:
                    entry=zipfile.ZipInfo(member,date_time=(1991,1,1,0,0,0));z.writestr(entry,text.encode('ascii'))
            digest=sha(path)
            row=db.execute('INSERT INTO file(area_tag,file_sha256,file_name,storage_tag,desc,desc_long,upload_timestamp) VALUES(?,?,?,?,?,?,?)',('pcplus_games',digest,name,'exodos_games',f'Synthetic PCPlus Probe {i:02d}','Generated menu navigation fixture.','2026-01-01T00:00:00.000Z'))
            file_id=row.lastrowid
            db.execute('INSERT INTO file_meta VALUES(?,?,?)',(file_id,'byte_size',str(path.stat().st_size)))
            row=notes.execute('INSERT INTO archive(name,storage,status) VALUES(?,?,?)',(name,'exodos_games','complete'));archive_id=row.lastrowid
            for kind,member,text in [('diz','FILE_ID.DIZ',diz),('nfo','PCPLUS.NFO',nfo)]:
                notes.execute('INSERT INTO document(archive_id,member,kind,text,sha256,bytes) VALUES(?,?,?,?,?,?)',(archive_id,member,kind,text,hashlib.sha256(text.encode()).hexdigest(),len(text)))
            archives.append(dict(name=name,file_id=file_id,sha256=digest,bytes=path.stat().st_size))
        assert db.execute('PRAGMA integrity_check').fetchone()==notes.execute('PRAGMA integrity_check').fetchone()==('ok',)
        assert db.execute("SELECT COUNT(*) FROM file_fts WHERE file_fts MATCH 'PCPLUS PROBE'").fetchone()[0]>=30
    assert before=={p:sha(server/p) for p in sources},'Source changed during setup'
    inputs=['config/menus/loc-main.hjson','config/config.hjson','local/catalog/notes/index.sqlite3',str(theme_path.relative_to(candidate)),*asset_hashes,'core/client.js','core/key_stream.js']
    metadata.update(source_inputs={**metadata['source_modules'],**before},fixture_inputs={p:sha(candidate/p) for p in inputs},
        selected_menus=selected,selected_theme=list(selected_theme),
        menu_selection_sha256=hashlib.sha256(json.dumps(dict(menus=selected_menus,prompts=selected_prompts,theme=selected_theme),sort_keys=True).encode()).hexdigest(),
        archives=archives,route='owned-search-index-details',
        scope='Exact owned search/index/details modules and selected menu/theme/ANSI inputs; synthetic users,30 generated archives and DIZ/NFO database. Main F -> S search route; no live board changes or real catalog copied.')
    (candidate/'search-instance.json').write_text(json.dumps(metadata,indent=2)+'\n')
    instance=json.loads((candidate/'instance.json').read_text());instance['config_sha256']=sha(runtime_path)
    (candidate/'instance.json').write_text(json.dumps(instance,indent=2)+'\n')
    print(json.dumps(dict(source_inputs=metadata['source_inputs'],archives=len(archives),selected_menus=selected,selected_theme=list(selected_theme)),indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--server-root',type=Path,required=True)
    a=p.parse_args();setup_search(a.candidate,a.server_root)
