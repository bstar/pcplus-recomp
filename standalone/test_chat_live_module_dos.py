#!/usr/bin/env python3
"""Actual DOS8086 API0104 binding, scheduling, fault retirement and two-address loading."""
import argparse,json,os,shutil,subprocess
from pathlib import Path
from build_chat_module import ROOT,build
from build_path_session import sha


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir()
    module=build(out/'module',foreground=True);old=build(out/'old-module',timing=True)
    names=list(module['sources'])+['src/chat/loader.c','src/chat/loader.h','src/chat/overlay_load.asm',
        'standalone/chat_overlay_storage.asm','standalone/chat_live_module_host.c',
        'standalone/test_chat_live_module_dos.py','standalone/build_path_session.py']
    sources={n:sha(ROOT/n) for n in names};drive=out/'drive';drive.mkdir()
    shutil.copyfile(out/'module/PCCHAT.OVL',drive/'PCCHAT.OVL');shutil.copyfile(out/'old-module/PCCHAT.OVL',drive/'OLD.OVL')
    for n,obj,flags in [('src/chat/overlay_load.asm','load.obj',['-DCHAT_LOADER_BANK']),('standalone/chat_overlay_storage.asm','storage.obj',[])]:
        subprocess.run(['nasm','-fobj',*flags,str(ROOT/n),'-o',obj],cwd=drive,check=True)
    flags=['-q','-bt=dos','-0','-ms','-s','-w4','-we','-ecc','-dCHAT_TEXT','-dCHAT_PRESENTATION','-dCHAT_TIMING','-dCHAT_FOREGROUND_TEXT']
    subprocess.run(['wcc',*flags,'-ox','-os','-oe=0','-nt=CHAT_LOAD_CODE','-nc=FARCODE','-i='+str(out/'module'),'-fo=loader.obj',str(ROOT/'src/chat/loader.c')],cwd=drive,check=True)
    subprocess.run(['wcl',*flags,'-k8192','-fe=LIVEMOD.EXE','-fm=LIVEMOD.MAP',str(ROOT/'standalone/chat_live_module_host.c'),'loader.obj','load.obj','storage.obj'],cwd=drive,check=True)
    listing=(drive/'LIVEMOD.MAP').read_text();assert 'CHAT_CODE ' not in listing and '_chat_timing_effect' not in listing
    config=out/'dosbox.conf';config.write_text('[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=fixed 12000\n[autoexec]\n@echo off\nmount c "'+str(drive)+'"\nc:\nLIVEMOD >RESULT.TXT\nif errorlevel 1 goto failed\necho PASS>PASS.TXT\nexit\n:failed\necho FAIL>FAIL.TXT\nexit\n')
    with (out/'dosbox.log').open('w') as log:r=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(config)],cwd=drive,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=60)
    text=(drive/'RESULT.TXT').read_text();assert r.returncode==0 and (drive/'PASS.TXT').exists() and not (drive/'FAIL.TXT').exists(),text
    assert 'errors=0 ' in text and 'loads=2 binding_bounds=8 echo_faults=4' in text,text
    assert old['binary_sha256']=='5b6892e71dfb6054cc5e1ff04b9cfac380af1a5e530da11dc2780325a8d45622'
    assert all(sha(ROOT/n)==h for n,h in sources.items())
    report=dict(passed=True,api_version=module['api_version'],state_bytes=476,binding_bytes=24,module_sha256=module['binary_sha256'],
        image_bytes=module['image_bytes'],loads=2,relocation_bases=2,free_DOS_paragraphs=0,binding_bounds=True,
        old_timing_module_unchanged=True,sources=sources,artifacts={str(q.relative_to(out)):sha(q) for q in out.rglob('*') if q.is_file()},
        scope=__doc__+' Real4B03 at two addresses with all remaining DOS paragraphs reserved. Explicit binding refuses null KEY and cursor aliases into state/code/backup, then refuses rebind/generic TEXT bypass. Real ten-tick pause, concurrent RX/history/log, copied KEY text, TX refusal without duplicate echo, preserved local input, cursor initialization, stale API/file, reentry/unload refusal, automatic constructor binding, accepted partial-echo fault and echo refusal each retire without TX/retry. Exact VGA restore, canaries/CRC/same PSP/JFT/free memory. TX/echo are host recorders; this is separate from normal-main physical-UART/native-echo fixtures, BBS and physical acceptance.')
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS DOS API0104: two bases, zero free paragraphs, binding bounds, pause/RX/TX refusal and echo fault retirement')


if __name__=='__main__':main()
