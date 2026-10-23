#!/usr/bin/env python3
"""Linked PRM sound staging/commit, with only existing file boundaries modeled."""
import hashlib,json
from pathlib import Path
import check_startup_import as startup
import check_directory_live as directory
from check_directory_context import Context
import check_live_setup_owner as setup
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/terminal-notice-sound'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    startup.BINARY=directory.BINARY=OUT/'TERMINAL.EXE';startup.MAP=directory.MAP=OUT/'terminal.map';setup.OUT=OUT
    rows=[]
    for enabled in [0,1,65535]:
        for modem in [False,True]:
            m=startup.Startup();m.payload=directory.word(m.payload,0x1bc,enabled);m.put('_terminal_sound_enabled',7)
            prefs=m.offset('_terminal_transfer_preferences')
            assert m.call('_terminal_preferences_read',[m.path,m.serial,m.modem if modem else 0,prefs,m.result],limit=2000000)==0
            assert m.get('_terminal_sound_enabled')==int(bool(enabled)) and len(m.calls)==1
            assert m.plans()[0]==startup.terminal_expected(m.payload)
            rows.append(dict(case='startup',sound=enabled,modem=modem))
        for failure in ['file','serial','transfer']:
            m=startup.Startup();m.payload=directory.word(m.payload,0x1bc,enabled);m.put('_terminal_sound_enabled',7);m.poison();before=m.plans()
            if failure=='file':m.load_status=2
            elif failure=='serial':m.payload=directory.word(m.payload,0,4)
            else:m.payload=directory.text(m.payload,0x31c,64,b'CON')
            assert m.call('_terminal_preferences_read',[m.path,m.serial,m.modem,m.offset('_terminal_transfer_preferences'),m.result],limit=2000000)!=0
            assert m.get('_terminal_sound_enabled')==7 and m.plans()==before
            rows.append(dict(case='startup-reject',failure=failure,sound=enabled))
        m=Context();m.prm=directory.word(m.prm,0x1bc,enabled);m.put('_terminal_sound_enabled',7)
        assert m.call('_terminal_directory_preferences_read',m.arguments()+[m.context,m.offset('_terminal_transfer_preferences')],limit=3000000)==0
        assert m.get('_terminal_sound_enabled')==int(bool(enabled)) and m.context_bytes()==m.expected_context()
        rows.append(dict(case='directory-startup',sound=enabled))
        m=Context();m.prm=directory.word(m.prm,0x1bc,enabled);m.directory_status=2;m.put('_terminal_sound_enabled',7)
        assert m.call('_terminal_directory_preferences_read',m.arguments()+[m.context,m.offset('_terminal_transfer_preferences')],limit=3000000)!=0
        assert m.get('_terminal_sound_enabled')==7
        rows.append(dict(case='directory-reject',sound=enabled))
        for selected in [False,True]:
            for action in ['commit','abort','invalid','deferred-baud']:
                m=setup.Owner(selected).ready();m.put('_terminal_sound_enabled',7);m.raw=directory.word(m.raw,0x1bc,enabled)
                if action=='invalid':m.raw=directory.word(m.raw,0,4)
                if action=='deferred-baud':m.raw=directory.word(m.raw,2,8)
                status,_=m.finish();assert bool(status)==(action=='invalid')
                assert m.get('_terminal_sound_enabled')==7,'Staging mutated active sound'
                if action=='abort':assert m.invoke('_live_setup_abort',[0])==0
                assert m.invoke('_live_setup_acknowledge',[0])==0
                assert m.get('_terminal_sound_enabled')==(int(bool(enabled)) if action in ('commit','deferred-baud') else 7)
                # The offer is consumed; another acknowledgement cannot reread/commit it.
                m.put('_terminal_sound_enabled',9);assert m.invoke('_live_setup_acknowledge',[0])==0 and m.get('_terminal_sound_enabled')==9
                rows.append(dict(case='live-offer',sound=enabled,selected=selected,action=action))
    manifest=json.loads((OUT/'manifest.json').read_text());assert sha(OUT/'TERMINAL.EXE')==manifest['binary_sha256']
    sources={**manifest['sources'],**{n:sha(ROOT/n) for n in ['standalone/check_program_sound_settings.py','standalone/check_startup_import.py','standalone/check_directory_live.py','standalone/check_directory_context.py','standalone/check_live_setup_owner.py','standalone/check_setup_model.py','standalone/dos_image.py']}}
    assert all(sha(ROOT/n)==h for n,h in sources.items())
    report=dict(passed=True,cases=rows,binary_sha256=manifest['binary_sha256'],sources=sources,scope=__doc__+' Actual linked configuration bank and native ABI; synthetic file failures/PRM images. No actual Setup child or PRM write is executed by this checker.')
    (OUT/'sound-settings-checks.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,cases=len(rows))))
if __name__=='__main__':main()
