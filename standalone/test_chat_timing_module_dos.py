#!/usr/bin/env python3
"""Actual DOS8086 loaded timing module, BIOS pause/calibration, RX and physical frame return."""
import argparse,json,os,shutil,subprocess
from pathlib import Path
from build_chat_module import ROOT,build
from build_path_session import sha


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir()
    module=build(out/'module',timing=True);old=build(out/'old-module',text=True)
    names=list(module['sources'])+['src/chat/loader.c','src/chat/loader.h','src/chat/overlay_load.asm',
        'standalone/chat_overlay_storage.asm','standalone/chat_timing_module_host.c',
        'standalone/test_chat_timing_module_dos.py','standalone/build_path_session.py']
    sources={n:sha(ROOT/n) for n in names};drive=out/'drive';drive.mkdir()
    shutil.copyfile(out/'module/PCCHAT.OVL',drive/'PCCHAT.OVL');shutil.copyfile(out/'old-module/PCCHAT.OVL',drive/'OLD.OVL')
    for n,obj,flags in [('src/chat/overlay_load.asm','load.obj',['-DCHAT_LOADER_BANK']),('standalone/chat_overlay_storage.asm','storage.obj',[])]:
        subprocess.run(['nasm','-fobj',*flags,str(ROOT/n),'-o',obj],cwd=drive,check=True)
    flags=['-q','-bt=dos','-0','-ms','-s','-w4','-we','-ecc','-dCHAT_TEXT','-dCHAT_PRESENTATION','-dCHAT_TIMING']
    subprocess.run(['wcc',*flags,'-ox','-os','-oe=0','-nt=CHAT_LOAD_CODE','-nc=FARCODE','-i='+str(out/'module'),'-fo=loader.obj',str(ROOT/'src/chat/loader.c')],cwd=drive,check=True)
    subprocess.run(['wcl',*flags,'-k8192','-fe=TIMEMOD.EXE','-fm=TIMEMOD.MAP',str(ROOT/'standalone/chat_timing_module_host.c'),'loader.obj','load.obj','storage.obj'],cwd=drive,check=True)
    listing=(drive/'TIMEMOD.MAP').read_text();assert 'CHAT_CODE ' not in listing and '_chat_timing_effect' not in listing
    config=out/'dosbox.conf';config.write_text('[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=fixed 12000\n[autoexec]\n@echo off\nmount c "'+str(drive)+'"\nc:\nTIMEMOD >RESULT.TXT\nif errorlevel 1 goto failed\necho PASS>PASS.TXT\nexit\n:failed\necho FAIL>FAIL.TXT\nexit\n')
    with (out/'dosbox.log').open('w') as log:r=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(config)],cwd=drive,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=60)
    text=(drive/'RESULT.TXT').read_text();assert r.returncode==0 and (drive/'PASS.TXT').exists() and not (drive/'FAIL.TXT').exists(),text
    assert 'errors=0 ' in text and 'loads=2 real_BIOS_pause=2 pacing_calibration=1 RX_during_pause=2' in text,text
    assert old['binary_sha256']=='5ee67785e2efa4f630c6d17b391a99226fce9569af69070130cd5b53c87c0b72'
    assert all(sha(ROOT/n)==h for n,h in sources.items())
    report=dict(passed=True,api_version=module['api_version'],state_bytes=448,timing_bytes=18,module_sha256=module['binary_sha256'],
        image_bytes=module['image_bytes'],loads=2,relocation_bases=2,free_DOS_paragraphs=0,geometry_quarantine=True,
        old_TEXT_module_unchanged=True,sources=sources,artifacts={str(q.relative_to(out)):sha(q) for q in out.rglob('*') if q.is_file()},
        scope=__doc__+' Real4B03 at two addresses with all remaining DOS paragraphs reserved, real ten-tick pauses, calibration and paced units, physical VGA frame restore, RX/history/log during pending pause, copied source, TX refusal, local buffered line, stale API/file and reentry/unload refusal, abort/canaries/CRC/same PSP/JFT/free memory. TX/echo remain recorders, not real UART/original echo. No live parent frontend, BBS or physical acceptance.')
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS DOS timing module: two bases, zero free paragraphs, real BIOS waits/calibration and RX/frame return')


if __name__=='__main__':main()
