#!/usr/bin/env python3
"""Actual DOS8086 API0102 TEXT overlay, lifetime guards and background RX."""
import argparse,json,os,shutil,subprocess
from pathlib import Path
from build_chat_module import ROOT,build
from build_path_session import sha
from test_chat_text_dos import reference


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir()
    module=build(out/'module',text=True);old=build(out/'old-module',presentation=True)
    names=list(module['sources'])+['src/chat/loader.c','src/chat/loader.h','src/chat/overlay_load.asm',
        'standalone/chat_overlay_storage.asm','standalone/chat_text_module_host.c',
        'standalone/test_chat_text_module_dos.py','standalone/test_chat_text_dos.py','standalone/build_path_session.py',
        'reconstruction/meta_keys/text.asm','reconstruction/meta_keys/caret.asm','reconstruction/meta_keys/provenance.json','reconstruction/uart/encodings.inc']
    sources={n:sha(ROOT/n) for n in names};drive=out/'drive';drive.mkdir()
    shutil.copyfile(out/'module/PCCHAT.OVL',drive/'PCCHAT.OVL');shutil.copyfile(out/'old-module/PCCHAT.OVL',drive/'OLD.OVL')
    for n,obj,flags in [('src/chat/overlay_load.asm','load.obj',['-DCHAT_LOADER_BANK']),('standalone/chat_overlay_storage.asm','storage.obj',[])]:
        subprocess.run(['nasm','-fobj',*flags,str(ROOT/n),'-o',obj],cwd=drive,check=True)
    flags=['-q','-bt=dos','-0','-ms','-s','-w4','-we','-ecc','-dCHAT_TEXT','-dCHAT_PRESENTATION']
    subprocess.run(['wcc',*flags,'-ox','-os','-oe=0','-nt=CHAT_LOAD_CODE','-nc=FARCODE','-i='+str(out/'module'),'-fo=loader.obj',str(ROOT/'src/chat/loader.c')],cwd=drive,check=True)
    subprocess.run(['wcl',*flags,'-k8192','-fe=TEXTMOD.EXE','-fm=TEXTMOD.MAP',str(ROOT/'standalone/chat_text_module_host.c'),'loader.obj','load.obj','storage.obj'],cwd=drive,check=True)
    listing=(drive/'TEXTMOD.MAP').read_text();assert 'CHAT_CODE ' not in listing and '_chat_text_step' not in listing
    config=out/'dosbox.conf';config.write_text('[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=fixed 12000\n[autoexec]\n@echo off\nmount c "'+str(drive)+'"\nc:\nTEXTMOD >RESULT.TXT\nif errorlevel 1 goto failed\necho PASS>PASS.TXT\nexit\n:failed\necho FAIL>FAIL.TXT\nexit\n')
    with (out/'dosbox.log').open('w') as log:r=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(config)],cwd=drive,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=60)
    text=(drive/'RESULT.TXT').read_text();assert r.returncode==0 and (drive/'PASS.TXT').exists() and not (drive/'FAIL.TXT').exists(),text
    code={}
    for name,at in [('text',0x48cc),('caret',0x4934)]:
        target=out/(name+'.bin');subprocess.run(['nasm','-fbin','-I'+str(ROOT/'reconstruction/uart')+'/',str(ROOT/'reconstruction/meta_keys'/(name+'.asm')),'-o',str(target)],check=True);code[at]=target.read_bytes()
    import struct
    expected=reference(code,b'^@A~B^M',126,1,7)*8
    assert (drive/'EVENTS.BIN').read_bytes()==b''.join(struct.pack('<2H',*e) for e in expected)
    assert all(sha(ROOT/n)==h for n,h in sources.items())
    report=dict(passed=True,api_version=module['api_version'],state_bytes=module['state_bytes'],module_sha256=module['binary_sha256'],module_image_bytes=module['image_bytes'],old_module_sha256=old['binary_sha256'],loads=2,relocation_bases=2,free_DOS_paragraphs=0,record_kinds=4,exact_ordered_effects=len(expected),background_RX_cases=2,sources=sources,artifacts={str(q.relative_to(out)):sha(q) for q in out.rglob('*') if q.is_file()},scope=__doc__+' Module is loaded only at runtime; no static Chat implementation. Two bases, no free DOS paragraphs, stale ABI/file identity refusal, all four record kinds as direct TEXT data, copied expansion, key/open/unload/busy/reentrant guards, abort and real module RX/render/history/log service while TEXT TX is refused, exact source-CPU effect records. Sink services remain recorders, no original echo rendering, physical UART/delay, frontend/BBS or physical acceptance.')
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS real DOS TEXT module: two bases/zero free paragraphs, direct-record effects and concurrent RX')


if __name__=='__main__':main()
