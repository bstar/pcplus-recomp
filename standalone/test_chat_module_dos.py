#!/usr/bin/env python3
"""Build and load the actual Chat overlay in DOS8086 without free paragraphs."""
import argparse
import hashlib
import json
import os
import shutil
import struct
import subprocess
import sys
from pathlib import Path
from build_chat_module import ROOT,SOURCES,build
from test_chat_session_dos import NAMES as SESSION_SOURCES
from omf_imports import records,externals

NAMES=list(dict.fromkeys(SOURCES+['src/chat/loader.c','src/chat/loader.h','src/chat/overlay_load.asm',
    'standalone/chat_overlay_storage.asm','standalone/chat_module_host.c','standalone/test_chat_module_dos.py',
    'standalone/chat_module_proxy.c','standalone/chat_session_host.c','standalone/omf_imports.py']+SESSION_SOURCES))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--optimize-loader',action='store_true',help='Use the exact resident parent loader compiler options')
    args=p.parse_args()
    out=args.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir()
    sources={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in NAMES}
    module=build(out/'module');drive=out/'drive';drive.mkdir()
    raw=(out/'module/PCCHAT.OVL').read_bytes();(drive/'PCCHAT.OVL').write_bytes(raw)
    for name,data in [('BAD.OVL',raw[:-1]+bytes([raw[-1]^1])),('SHORT.OVL',raw[:-1]),('LONG.OVL',raw+b'X'*1024),('HEAD.OVL',b'XX'+raw[2:])]:
        (drive/name).write_bytes(data)
    bad=bytearray(raw);table=struct.unpack_from('<H',raw,0x18)[0];struct.pack_into('<2H',bad,table,0xffff,0xffff);(drive/'RELOC.OVL').write_bytes(bad)
    for n,obj in [('src/chat/overlay_load.asm','load.obj'),('standalone/chat_overlay_storage.asm','storage.obj')]:
        subprocess.run(['nasm','-fobj',*(['-DCHAT_LOADER_BANK'] if obj=='load.obj' else []),str(ROOT/n),'-o',obj],cwd=drive,check=True)
    loader_flags=['-ox','-os','-oe=0'] if args.optimize_loader else []
    subprocess.run(['wcc','-q','-bt=dos','-0','-ms','-s','-w4','-we','-ecc',*loader_flags,'-nt=CHAT_LOAD_CODE','-nc=FARCODE','-i='+str(out/'module'),'-fo=loader.obj',str(ROOT/'src/chat/loader.c')],cwd=drive,check=True)
    imports=[name.decode() for kind,payload,raw_record in records((drive/'loader.obj').read_bytes()) if kind==0x8c for name,index in externals(payload)]
    assert set(imports)=={'_small_code_','_chat_file_open','_chat_file_read','_chat_file_close','_chat_dos_overlay_load','_chat_module_image_valid'},imports
    subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-s','-w4','-we','-k8192',
        '-i='+str(out/'module'),'-fe=LOADCHAT.EXE','-fm=LOADCHAT.MAP',
        str(ROOT/'standalone/chat_module_host.c'),'loader.obj','load.obj','storage.obj'],cwd=drive,check=True)
    # The host must not statically link the Chat implementation.
    listing=(drive/'LOADCHAT.MAP').read_text();assert 'CHAT_CODE' not in listing and '_chat_module_dispatch' not in listing
    config=out/'dosbox.conf';config.write_text('[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=fixed 12000\n[autoexec]\n@echo off\nmount c "'+str(drive)+'"\nc:\nLOADCHAT >RESULT.TXT\nif errorlevel 1 goto failed\necho PASS>PASS.TXT\nexit\n:failed\necho FAIL>FAIL.TXT\nexit\n')
    with (out/'dosbox.log').open('w') as log:
        result=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(config)],cwd=drive,
            env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=60)
    assert result.returncode==0 and (drive/'PASS.TXT').exists() and not (drive/'FAIL.TXT').exists(),(drive/'RESULT.TXT').read_text()
    # Reuse the unchanged full composition fixture, replacing only its six
    # imported session entries with fixture proxies to the loaded module.
    proxy=out/'composed';proxy.mkdir();(proxy/'PCCHAT.OVL').write_bytes(raw)
    aliases=['-dchat_session_'+n+'=chat_proxy_'+n for n in ('open','key','receive','step','abort')]
    subprocess.run(['wcc','-q','-bt=dos','-0','-ms','-s','-w4','-we','-ecc','-dCHAT_BANK',*aliases,'-fo=host.obj',str(ROOT/'standalone/chat_session_host.c')],cwd=proxy,check=True)
    subprocess.run(['wcc','-q','-bt=dos','-0','-ms','-s','-w4','-we','-ecc','-dCHAT_BANK','-nt=PROXY_CODE','-nc=FARCODE','-fo=proxy.obj',str(ROOT/'standalone/chat_module_proxy.c')],cwd=proxy,check=True)
    for n,obj,flags in [('src/chat/overlay_load.asm','load.obj',['-DCHAT_LOADER_BANK']),('standalone/chat_overlay_storage.asm','storage.obj',['-DCHAT_PROXY'])]:
        subprocess.run(['nasm','-fobj',*flags,str(ROOT/n),'-o',obj],cwd=proxy,check=True)
    shutil.copyfile(drive/'loader.obj',proxy/'loader.obj')
    subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-s','-w4','-we','-k8192','-i='+str(out/'module'),'-fe=COMPOSE.EXE','-fm=COMPOSE.MAP','loader.obj','host.obj','proxy.obj','load.obj','storage.obj'],cwd=proxy,check=True)
    listing=(proxy/'COMPOSE.MAP').read_text();assert 'CHAT_CODE' not in listing and '_chat_module_dispatch' not in listing
    config=out/'composed.conf';config.write_text('[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=fixed 12000\n[autoexec]\n@echo off\nmount c "'+str(proxy)+'"\nc:\nCOMPOSE >RESULT.TXT\nif errorlevel 1 goto failed\necho PASS>PASS.TXT\nexit\n:failed\necho FAIL>FAIL.TXT\nexit\n')
    with (out/'composed.log').open('w') as log:
        result=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(config)],cwd=proxy,
            env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=60)
    assert result.returncode==0 and (proxy/'PASS.TXT').exists() and not (proxy/'FAIL.TXT').exists(),(proxy/'RESULT.TXT').read_text()
    subprocess.run([sys.executable,str(ROOT/'standalone/test_chat_session_dos.py'),'--output',str(out/'reference')],cwd=ROOT,check=True)
    reference=json.loads((out/'reference/result.json').read_text());assert reference['passed']
    for leaf in ('FRAMES.BIN','EVENTS.BIN'):assert (proxy/leaf).read_bytes()==(out/'reference/drive'/leaf).read_bytes(),leaf
    assert all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h for n,h in sources.items())
    report=dict(passed=True,module_sha256=module['binary_sha256'],module_image_bytes=module['image_bytes'],
        source_files=len(sources),loader_compiler_flags=loader_flags,loads=6,relocation_areas=2,free_paragraphs_during_load=0,
        malformed_file_controls=5,loaded_image_negative_controls=['ordinary-byte','relocation-word'],
        composed_frames=reference['complete_frames'],composed_effects=reference['ordered_effects'],rx_effects_while_tx_blocked=reference['rx_effects_while_tx_blocked'],loader_imports=imports,sources=sources,
        artifacts={str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file()},
        scope='Actual DOS8086 4B03 source-built overlay in caller-owned guarded existing storage, zero free paragraphs, two relocation bases, same PSP/JFT/free memory, far callbacks/DS=SS and busy/active/unload checks. No CRT or Chat code in host. No physical DOS, parent integration, concurrent module-file mutation or arbitrary memory-corruption guarantee.')
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS source-built DOS Chat overlay: six loads, two bases, no free paragraphs')


if __name__=='__main__':main()
