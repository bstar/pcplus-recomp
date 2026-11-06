#!/usr/bin/env python3
"""Actual DOS8086 loadable Chat screen/cursor lifecycle with no free paragraphs."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from build_chat_module import ROOT,build
from build_path_session import sha
sys.path.insert(0,str(ROOT/'src'))
from process.display_rows_link import build_display_rows_bank


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir()
    module=build(out/'module',presentation=True)
    rows=build_display_rows_bank(ROOT,out)
    names=list(module['sources'])+[str(p.relative_to(ROOT)) for p in rows['inputs']]+[
        'src/chat/loader.c','src/chat/loader.h','src/chat/overlay_load.asm',
        'standalone/chat_overlay_storage.asm','standalone/chat_presentation_host.c',
        'standalone/test_chat_presentation_dos.py','standalone/build_path_session.py']
    sources={n:sha(ROOT/n) for n in names}
    drive=out/'drive';drive.mkdir();shutil.copyfile(out/'module/PCCHAT.OVL',drive/'PCCHAT.OVL')
    for n,obj,extra in [('src/chat/overlay_load.asm','load.obj',['-DCHAT_LOADER_BANK']),
                        ('standalone/chat_overlay_storage.asm','storage.obj',[])]:
        subprocess.run(['nasm','-fobj',*extra,str(ROOT/n),'-o',obj],cwd=drive,check=True)
    subprocess.run(['wcc','-q','-bt=dos','-0','-ms','-s','-w4','-we','-ecc','-dCHAT_PRESENTATION',
                    '-ox','-os','-oe=0','-nt=CHAT_LOAD_CODE','-nc=FARCODE',
                    '-i='+str(out/'module'),'-fo=loader.obj',str(ROOT/'src/chat/loader.c')],cwd=drive,check=True)
    subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-s','-w4','-we','-ecc','-dCHAT_PRESENTATION','-k8192',
                    '-i='+str(out/'module'),'-fe=PRESENT.EXE','-fm=PRESENT.MAP',
                    str(ROOT/'standalone/chat_presentation_host.c'),'loader.obj','load.obj','storage.obj',
                    *map(str,rows['objects'])],cwd=drive,check=True)
    listing=(drive/'PRESENT.MAP').read_text()
    assert 'CHAT_CODE ' not in listing and '_chat_present_open' not in listing and '_chat_session_key' not in listing
    config=out/'dosbox.conf';config.write_text('[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=fixed 12000\n[autoexec]\n@echo off\nmount c "'+str(drive)+'"\nc:\nPRESENT >RESULT.TXT\nif errorlevel 1 goto failed\necho PASS>PASS.TXT\nexit\n:failed\necho FAIL>FAIL.TXT\nexit\n')
    with (out/'dosbox.log').open('w') as log:
        result=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(config)],cwd=drive,
            env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=60)
    text=(drive/'RESULT.TXT').read_text() if (drive/'RESULT.TXT').exists() else ''
    assert result.returncode==0 and (drive/'PASS.TXT').exists() and not (drive/'FAIL.TXT').exists(),text
    assert 'errors=0 presentations=8 rows=25,28,43,50 quarantine=4 negatives=9' in text,text
    for n,h in sources.items():assert sha(ROOT/n)==h,n
    report=dict(passed=True,module_sha256=module['binary_sha256'],module_image_bytes=module['image_bytes'],
                api_version=module['api_version'],state_bytes=module['state_bytes'],source_files=len(sources),
                presentations=8,geometries=[25,28,43,50],relocation_areas=2,free_paragraphs=0,
                geometry_retirement_quarantines=4,invalid_open_controls=9,
                sources=sources,artifacts={str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()},
                scope=__doc__+' Production module only loaded at runtime, no static Chat implementation in host. Full cells and cursor position/shape restore, visible/hidden cursor, local/RX paint and history/log callbacks, active-unload refusal and page-change retirement quarantine; unchanged PSP/JFT/largest block and canaries. Recovered source-built row helper in fixture. No parent frontend/serial/notice/trap, physical or full-native hardware-cursor-timing acceptance.')
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS loaded Chat presentation: eight screens/cursors, four geometries, retirement quarantine')


if __name__=='__main__':main()
