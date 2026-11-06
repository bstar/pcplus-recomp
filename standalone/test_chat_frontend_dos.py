#!/usr/bin/env python3
"""Actual DOS experimental Chat foreground entry and keyboard/RX ownership.

The dedicated caller loads the source-built parent as a DOS overlay and uses
its real DS=SS and declared stack. Parent main/PSP initialization is not run;
normal-main ASPECT/BBS admission must be validated separately.
"""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
from build_path_session import ROOT, sha


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('terminal','output'):
        p.add_argument('--'+name,type=Path,required=True)
    a = p.parse_args()
    binary,out = a.terminal.resolve(),a.output.resolve()
    assert binary.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build') and not out.exists()
    m = json.loads(binary.with_name('manifest.json').read_text())
    assert m['experimental_chat_adapters'] and m['experimental_chat_presentation']
    presentation = m.get('experimental_chat_presentation',False)
    assert m['chat_loader']['module']['api_version']==(0x101 if presentation else 0x100)
    assert sha(binary)==m['binary_sha256']
    sources = dict(m['sources'])
    for n in ['standalone/test_chat_frontend_dos.py','standalone/chat_frontend_host.c',
              'standalone/chat_parent_invoke.asm']:
        sources[n]=sha(ROOT/n)
    for n,h in sources.items():
        assert sha(ROOT/n)==h,n
    listing=binary.with_name('terminal.map').read_text()
    symbols={n:(int(off,16),int(seg,16)) for seg,off,n in re.findall(
        r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',listing,re.M|re.I)}
    group=re.search(r'^DGROUP\s+([0-9a-f]+):0000',listing,re.M|re.I);assert group
    constants=dict(PARENT_DS=int(group[1],16),PARENT_SP=symbols['terminal_stack_top'][0],
                   PARENT_PARAS=(m['memory_layout']['minimum_allocated_module_bytes']+15)//16,
                   MODULE_IMAGE_BYTES=m['chat_loader']['module']['image_bytes'])
    entries=dict(ACQUIRE='terminal_chat_storage_acquire',RELEASE='terminal_chat_storage_release',
                 LOAD='_chat_module_load',CALL='_chat_module_call',UNLOAD='_chat_module_unload',
                 VALID='_chat_module_image_valid',KEY='terminal_redisplay_key_far',
                 BEFORE='terminal_redisplay_before_far',IDLE='terminal_redisplay_idle_far',
                 STOP='terminal_redisplay_stop_far',RESET='reset_bank_call_far',
                 OWNER='_redisplay_active',FROZEN='redisplay_snapshot',FRAME='redisplay_view',
                 SINK='_terminal_chat_sink',INIT='_capture_session_initialize_far',
                 BEGIN='_capture_session_begin_far',END='_capture_session_stop_far',
                 TXCOUNT='terminal_tx_count',TXHEAD='terminal_tx_head',TXTAIL='terminal_tx_tail',
                 TXBUFFER='terminal_tx_buffer',ORIGIN='terminal_tx_origin_bits',
                 HISTORY='terminal_history_buffer',HISTORYPTR='terminal_history_pointer',
                 PENDING='terminal_history_pending',PRINTER='terminal_sink_3988_enabled',
                 PRCOUNT='terminal_printer_count',PRTAIL='terminal_printer_tail',
                 PRBUFFER='terminal_printer_buffer',CRLF='terminal_cr_adds_lf',
                 QUIT='terminal_quit',ASPECT='terminal_aspect_active',EVENT='_chat_front_event',
                 KEYHOLD='terminal_chat_key_hold_far',RXHOLD='terminal_chat_receive_hold_far',
                 RX='terminal_chat_receive_far',KEYFRONT='terminal_chat_key_far',
                 POLL='terminal_chat_idle_far',FRONTSTOP='terminal_chat_stop_far',PSP='process_psp',
                 DEFERRED='terminal_deferred_count',MODE='modes_value_1d1a')
    for label,name in entries.items():
        constants[label+'_OFF'],constants[label+'_SEG']=symbols[name]
    assert constants['FROZEN_OFF']==0 and constants['OWNER_SEG']==constants['PARENT_DS']
    out.mkdir();drive=out/'drive';drive.mkdir()
    (drive/'parent.h').write_text('/* Exact declared source-built parent identities. */\n'+
        ''.join('#define '+k+' '+str(v)+'\n' for k,v in constants.items()))
    shutil.copyfile(binary,drive/'PARENT.EXE')
    shutil.copyfile(binary.parent/'PCCHAT.OVL',drive/'PCCHAT.OVL')
    subprocess.run(['nasm','-fobj',str(ROOT/'standalone/chat_parent_invoke.asm'),'-o','invoke.obj'],cwd=drive,check=True)
    subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-s','-w4','-we','-ecc','-k8192',
                    *(['-dCHAT_PRESENTATION'] if presentation else []),
                    '-i='+str(drive),'-fe=LEASE.EXE','-fm=LEASE.MAP',
                    str(ROOT/'standalone/chat_frontend_host.c'),'invoke.obj'],cwd=drive,check=True)
    host_map=(drive/'LEASE.MAP').read_text()
    assert '_chat_module_load' not in host_map and '_chat_module_dispatch' not in host_map
    config=out/'dosbox.conf'
    config.write_text('[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=fixed 12000\n[autoexec]\n@echo off\nmount c "'+str(drive)+'"\nc:\nLEASE >RESULT.TXT\nif errorlevel 1 goto failed\necho PASS>PASS.TXT\nexit\n:failed\necho FAIL>FAIL.TXT\nexit\n')
    with (out/'dosbox.log').open('w') as log:
        run=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(config)],cwd=drive,
            env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=60)
    text=(drive/'RESULT.TXT').read_text() if (drive/'RESULT.TXT').exists() else ''
    assert run.returncode==0 and (drive/'PASS.TXT').exists() and not (drive/'FAIL.TXT').exists(),text
    assert 'errors=0 foreground_entries=3 TX=3 RX_effects=2 pending_key_preserved=1 quarantine=1' in text,text
    for n,h in sources.items():
        assert sha(ROOT/n)==h,n
    assert sha(drive/'PARENT.EXE')==sha(binary)
    assert sha(drive/'PCCHAT.OVL')==m['chat_loader']['module']['binary_sha256']
    record=dict(passed=True,binary_sha256=sha(binary),module_sha256=sha(drive/'PCCHAT.OVL'),
                loads=3,relocation_areas=1,presentation=presentation,source_files=len(sources),sources=sources,
                constants=constants,artifacts={str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()},
                scope=__doc__+' Actual parent foreground C/assembly entry/peek/RX/idle/stop and loaded module, real queue/history. Host PSP used for actual sibling resource path; parent main and actual BIOS keyboard dequeue/UART delivery are not executed here. No Help/direct TEXT, notice/trap, BBS or physical acceptance.')
    (out/'result.json').write_text(json.dumps(record,indent=2)+'\n')
    print('PASS actual DOS foreground core: real entry, pending-key hold, RX/history and retirement')


if __name__=='__main__':
    main()
