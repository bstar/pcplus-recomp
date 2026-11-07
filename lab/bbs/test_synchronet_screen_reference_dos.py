#!/usr/bin/env python3
"""Capture an actual stock Synchronet editor at a real CPR boundary in DOS."""
import argparse
import fcntl
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from product_inputs import ROOT,select_product,sha,stage_companions
from terminal_geometry import terminal_geometry
from audio_synchronet import snapshot,message_bodies,statistics
from audio_synchronet_editor import editor_checks
from synchronet import LAB,PORT
sys.path.insert(0,str(ROOT/'src/aspect'))
from compiler import compile_source

def login_script():
    def wait(token,label):
        return f'waitfor "{token}" 45\nif waitfor == 0\nfopen 0 "D:\\STAGES.LOG" "ab"\nfputs 0 "FAIL-{label}|"\nfclose 0\nexit\nendif\nwaitquiet 2 30\nfopen 0 "D:\\STAGES.LOG" "ab"\nfputs 0 "{label}|"\nfclose 0\n'
    source='proc main\n'
    for token,label,data in [('CONNECT> ','BRIDGE','loc^M'),('Login:','LOGIN','LABUSER^M'),('Password:','PASSWORD','LABPASS42^M'),('[Hit a key]','WELCOME',' '),('Enter number of bulletin or [','BULLETINS','Q'),('Search all groups for new messages?','SCAN','n^M'),('Read/Post Messages','MAIN','2^M'),('General','GENERAL','P'),('Subject:','SUBJECT','KEYTEST^M')]:
        source+=wait(token,label)+f'transmit "{data}"\n'
    return source+wait('FSEditor v1.105','EDITOR')+'fopen 0 "D:\\SCRIPT.OK" "wb"\nfputs 0 "PASS"\nfclose 0\nendproc\n'

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--keymap-helper',type=Path);p.add_argument('--keymap-profiles',type=int,choices=[7,33],default=33);p.add_argument('--keymap-help',action='store_true');p.add_argument('--ignore-rts',action='store_true');p.add_argument('--runtime',required=True,type=Path);p.add_argument('--terminal',required=True,type=Path);p.add_argument('--label',required=True);p.add_argument('--runner',type=Path,default=ROOT/'build/aspect-register-parent-custom-irq/ASPECT.EXE');p.add_argument('--display-rows',type=int,choices=[25,28,43,50],default=25);p.add_argument('--status-hidden',type=int,choices=[0,1],default=0);p.add_argument('--size-probe',action='store_true');p.add_argument('--phone-log',action='store_true');p.add_argument('--gateway-overlay',action='store_true');p.add_argument('--file-directory-overlay',action='store_true');p.add_argument('--file-viewer-overlay',action='store_true');p.add_argument('--external-viewer-overlay',action='store_true');p.add_argument('--external-editor-overlay',action='store_true');p.add_argument('--meta-keys-overlay',action='store_true');p.add_argument('--admission-watch',action='store_true');a=p.parse_args()
    assert not a.ignore_rts or a.keymap_helper
    assert a.keymap_helper or not a.keymap_help
    assert a.keymap_helper or a.keymap_profiles==33
    if a.keymap_helper:
        a.keymap_helper=a.keymap_helper.resolve()
        assert not any((a.meta_keys_overlay,a.external_editor_overlay,a.external_viewer_overlay,a.file_viewer_overlay,a.file_directory_overlay,a.gateway_overlay,a.phone_log,a.admission_watch))
        assert a.size_probe and (a.display_rows,a.status_hidden)==(25,0)
    if a.meta_keys_overlay:
        assert not any((a.external_editor_overlay,a.external_viewer_overlay,a.file_viewer_overlay,a.file_directory_overlay,a.gateway_overlay,a.phone_log,a.admission_watch))
        assert a.size_probe and (a.display_rows,a.status_hidden)==(25,0)
    if a.external_editor_overlay:
        assert not a.external_viewer_overlay
        a.external_viewer_overlay=True
    external_tool='editor' if a.external_editor_overlay else 'viewer'
    if a.external_viewer_overlay:assert not any((a.file_viewer_overlay,a.file_directory_overlay,a.gateway_overlay,a.phone_log)) and a.display_rows==25 and a.status_hidden==0
    if a.file_directory_overlay:assert not a.gateway_overlay and not a.phone_log and a.display_rows==25 and a.status_hidden==0
    if a.file_viewer_overlay:assert not a.file_directory_overlay and not a.gateway_overlay and not a.phone_log and a.display_rows==25 and a.status_hidden==0
    if a.gateway_overlay:assert not a.phone_log and a.display_rows==25 and a.status_hidden==0
    assert re.fullmatch('[A-Za-z0-9_-]+',a.label)
    fixture_lock=(LAB/'.dos-integration.lock').open('a')
    try:fcntl.flock(fixture_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:raise RuntimeError('Another owned Synchronet DOS integration is active')
    server=snapshot();bodies=message_bodies();stats=statistics()
    binary,sources=select_product(a.terminal,'TERMINAL.EXE');geometry=terminal_geometry(binary);assert geometry['rows']==24
    if a.size_probe:assert json.loads((binary.parent/'manifest.json').read_text())['experimental_display_startup']
    assert a.size_probe or (a.display_rows,a.status_hidden)==(25,0)
    layout=dict(physical_rows=a.display_rows,logical_rows=a.display_rows-(not a.status_hidden),status_hidden=a.status_hidden) if a.size_probe else None
    expected_rows=layout['logical_rows'] if layout else geometry['rows']
    child,child_sources=select_product(a.runner,'ASPECT.EXE');sources+=child_sources
    names=['lab/bbs/test_synchronet_screen_reference_dos.py','lab/bbs/synthmodem_proxy_serial.js','lab/bbs/terminal_geometry.py','lab/bbs/audio_synchronet_editor_keys.asm','lab/bbs/editor_dos_probe.py','lab/bbs/test_dos.py','lab/bbs/modem.py','lab/bbs/audio_synchronet.py','lab/bbs/audio_synchronet_editor.py','src/aspect/compiler.py','standalone/display_startup_geometry.asm']
    sources += [ROOT/n for n in names]+[binary.parent/'terminal.map']
    if a.phone_log:sources += [ROOT/n for n in ('lab/bbs/phone_log_evidence.py','standalone/phone_log_events_watch.asm','standalone/test_phone_log_events_terminal.py')]
    if a.gateway_overlay:
        from gateway_bbs_support import SOURCES
        sources += [ROOT/n for n in SOURCES]
    if a.file_directory_overlay:
        from file_directory_bbs_support import SOURCES
        sources += [ROOT/n for n in SOURCES]
    if a.file_viewer_overlay:
        from file_viewer_bbs_support import SOURCES
        sources += [ROOT/n for n in SOURCES]
    if a.external_viewer_overlay:
        from external_viewer_bbs_support import SOURCES
        sources += [ROOT/n for n in SOURCES]
    if a.admission_watch:
        assert a.external_viewer_overlay
        sources += [ROOT/'lab/bbs/program_admission_support.py',ROOT/'standalone/program_admission_watch.inc']
    if a.meta_keys_overlay:
        from meta_front_bbs_support import SOURCES
        sources += [ROOT/n for n in SOURCES]
    if a.keymap_helper:
        from keymap_bbs_support import SOURCES
        sources += [ROOT/n for n in SOURCES]+[ROOT/'lab/bbs/nullmodem_control.py']
        proof=json.loads(a.keymap_helper.with_name('result.json').read_text())
        sources += [a.keymap_helper,a.keymap_helper.with_name('result.json')]+[ROOT/n for n in proof['sources']]
    frozen={str(n.relative_to(ROOT)):sha(n) for n in sources}
    base=ROOT/'build/bbs-lab';bridge=base/(a.label+'-proxy');out=base/'results/synchronet'/a.label
    assert not bridge.exists() and not out.exists();out.mkdir(parents=True)
    (out/'server-inputs.json').write_text(json.dumps(server,indent=2)+'\n')
    stage=out/'program';stage.mkdir()
    shutil.copyfile(binary,stage/'TERMINAL.EXE');shutil.copyfile(child,stage/'ASPECT.EXE')
    stage_companions(binary,stage)
    source=login_script();(stage/'SYNC.ASP').write_text(source);(stage/'SYNC.ASX').write_bytes(compile_source(source))
    helper=out/'EDITKEY.COM'
    subprocess.run(['nasm','-fbin',*(['-DKEYMAP_ROUNDTRIP','-DRECORD_KEY_SEGMENT']if a.keymap_helper else []),*(['-DKEYMAP_HELP_ROUNDTRIP'] if a.keymap_help else []),*(['-DMETA_KEYS_ROUNDTRIP']if a.meta_keys_overlay else []),*(['-DGATEWAY_ROUNDTRIP'] if a.gateway_overlay else []),*(['-DFILE_DIRECTORY_ROUNDTRIP'] if a.file_directory_overlay else []),*(['-DFILE_VIEWER_ROUNDTRIP'] if a.file_viewer_overlay else []),*(['-DEXTERNAL_VIEWER_ROUNDTRIP','-DRECORD_KEY_SEGMENT'] if a.external_viewer_overlay else []),*(['-DEXTERNAL_EDITOR_ROUNDTRIP'] if a.external_editor_overlay else []),'-DSCREEN_REFERENCE_FREEZE','-DAUDIO_SYNC_EDITOR_SCREEN_BYTES='+str((layout['physical_rows'] if layout else 25)*160),'-DAUDIO_SYNC_EDITOR_SETTLE=72','-DAUDIO_SYNC_EDITOR_KEY_WAIT=9','-DAUDIO_SYNC_EDITOR_FINAL_WAIT=54','-DAUDIO_SYNC_EDITOR_WATCHDOG_TICKS=2160',str(ROOT/'lab/bbs/audio_synchronet_editor_keys.asm'),'-o',str(helper)],check=True)
    generated_paths=[*stage.iterdir(),helper]
    observer=None;gateway_child=None
    if a.keymap_helper:
        from keymap_bbs_support import prepare
        keymap_folder=out/'keymap'
        keymap_binary,observer=prepare(keymap_folder,binary,a.keymap_helper,a.keymap_profiles,a.keymap_help)
        shutil.copyfile(a.keymap_helper,stage/'PCKEYMAP.EXE')
        generated_paths += [stage/'PCKEYMAP.EXE',observer]
    if a.meta_keys_overlay:
        from meta_front_bbs_support import prepare
        observer=prepare(out/'meta-keys',binary);generated_paths.append(observer)
    if a.gateway_overlay:
        assert json.loads((binary.parent/'manifest.json').read_text())['experimental_gateway_frontend']
        from gateway_bbs_support import prepare
        gateway_child,observer=prepare(out/'gateway')
        generated_paths += [gateway_child,observer]
    if a.file_directory_overlay:
        assert json.loads((binary.parent/'manifest.json').read_text())['experimental_file_directory']
        from file_directory_bbs_support import prepare
        observer=prepare(out/'file-directory');generated_paths.append(observer)
    if a.file_viewer_overlay:
        assert json.loads((binary.parent/'manifest.json').read_text())['experimental_file_viewer']
        from file_viewer_bbs_support import prepare
        observer=prepare(out/'file-viewer');generated_paths.append(observer)
    external_child=None
    if a.external_viewer_overlay:
        assert json.loads((binary.parent/'manifest.json').read_text())['experimental_external_viewer']
        if a.external_editor_overlay:assert json.loads((binary.parent/'manifest.json').read_text())['experimental_external_editor']
        from external_viewer_bbs_support import prepare
        external_child,observer=prepare(out/'external-viewer',binary if a.admission_watch else None);generated_paths += [external_child,observer]
    if a.phone_log:
        from phone_log_evidence import build_observer
        observer=build_observer(binary,out/'LOGWATCH.COM');generated_paths.append(observer)
    generated={str(p.relative_to(out)):sha(p) for p in generated_paths}
    proc=subprocess.Popen(['node',str(ROOT/'lab/bbs/synthmodem_proxy_serial.js'),'--runtime',str(a.runtime.resolve()),'--output',str(bridge),'--bbs-port',str(PORT),'--terminal-rows',str(expected_rows),'--framing-ms','250','--byte-delay-ms','20','--screen-reference','--screen-quiet-ms','150',*(['--probe-terminal-size'] if a.size_probe else [])],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True)
    try:
        deadline=time.monotonic()+15
        while not (bridge/'ready.json').exists():
            assert proc.poll() is None,'Proxy exited: '+proc.stderr.read()
            assert time.monotonic()<deadline,'Proxy readiness timeout';time.sleep(.05)
        ready=json.loads((bridge/'ready.json').read_text())
        cpu='386' if a.keymap_helper or a.file_viewer_overlay or a.external_viewer_overlay or a.meta_keys_overlay else '8086'
        command=[sys.executable,str(ROOT/'lab/bbs/editor_dos_probe.py'),str(stage/'TERMINAL.EXE'),'synchronet','--port',str(ready['endpoint']['port']),'--label',a.label,'--com','3','--baud','19200','--flow','HARD','--directory-fixture','--directory-script-fixture',str(stage/'SYNC.ASX'),'--keyboard-helper',str(helper),'--irq','5','--mouse-scales','8','4','--cpu',cpu,'--timeout','160','--wait','145','--raw-upstream','--keys','p900 enter']
        if a.size_probe:command+=['--display-rows',str(a.display_rows),'--status-hidden',str(a.status_hidden)]
        if a.keymap_helper:command+=['--keymap-fixture',str(keymap_folder/'BOARD.KBD'),'--keymap-expected',str(keymap_folder/'EXPECT.KBD'),'--hardware-flow-model','--video-observer',str(observer),'--video-observer-high','--keyboard-helper-high']
        if a.ignore_rts:command+=['--ignore-rts']
        if a.meta_keys_overlay:command+=['--video-observer',str(observer),'--video-observer-high']
        if a.phone_log:command+=['--phone-log','--video-observer',str(observer)]
        if a.gateway_overlay:command+=['--comspec-fixture',str(gateway_child),'--video-observer',str(observer)]
        if a.file_directory_overlay:command+=['--video-observer',str(observer)]
        if a.file_viewer_overlay:command+=['--video-observer',str(observer),'--video-observer-high']
        if a.external_viewer_overlay:command+=['--external-viewer-fixture',str(external_child),'--video-observer',str(observer),'--video-observer-high','--keyboard-helper-high']
        if external_child:command+=['--external-command-tool',external_tool]
        with (out/'harness.log').open('w') as log:code=subprocess.run(command,cwd=ROOT,stdout=log,stderr=log,timeout=175).returncode
        base_result=json.loads((out/'result.json').read_text())
        closed=json.loads((bridge/'1-closed.json').read_text());proof=json.loads((bridge/'1-screen-reference.json').read_text())
        # The bounded stream stops in the editor. The held continuation must
        # separately prove that the normal Ctrl-Q abort still reached stock
        # FSEditor and that the owned draft was not published.
        delivered=(out/'serial-sent.bin').read_bytes();held=(bridge/'1-held-output.bin').read_bytes()
        semantic=editor_checks(delivered+held)
        screen=(out/'SCREEN.BIN').read_bytes();text=screen[:expected_rows*160:2].decode('cp437')
        stages=(out/'STAGES.LOG').read_text() if (out/'STAGES.LOG').exists() else ''
        after_stats=statistics()
        checks=dict(size_probe_requested=not a.size_probe or ready['terminalSizeProbe'],harness=code==0 and base_result['passed'],runtime_unchanged=closed['source_unchanged'],
                    server_static_inputs_unchanged=snapshot()==server,message_bodies_unchanged=message_bodies()==bodies,
                    no_message_mail_or_transfer_writes=all(stats['Total'][k]==after_stats['Total'][k] for k in ('posts','email','feedback','uploads','uploadb','dnloads','dnloadb')),
                    actual_ASPECT_login=stages=='BRIDGE|LOGIN|PASSWORD|WELCOME|BULLETINS|SCAN|MAIN|GENERAL|SUBJECT|EDITOR|' and (out/'SCRIPT.OK').read_bytes()==b'PASS',
                    staged_inputs_unchanged=generated=={str(p.relative_to(out)):sha(p) for p in generated_paths},
                    frozen_editor_frame='FSEditor v1.105' in text and 'UNSAVED' in text,
                    actual_CPR_boundary=proof['armed'] and proof['frozen'] and proof['reply'] is not None,
                    fixture_CPR_consumed=proof['probeReplyConsumed'],expected_geometry_advertised=ready['terminalRows']==expected_rows,
                    source_inputs_unchanged=frozen=={str(n.relative_to(ROOT)):sha(n) for n in sources},**semantic)
        result=dict(passed=all(checks.values()),checks=checks,server='Synchronet',binary_sha256=sha(binary),interpreter_sha256=sha(child),generated_inputs=generated,stages=stages,screen_sha256=sha(out/'SCREEN.BIN'),terminal_geometry=geometry,display_layout=layout,screen_reference=proof,bridge=ready,command=command,product_inputs=frozen,
                    scope=f'Actual DOS{cpu} COM3/IRQ5 candidate and stock owned Synchronet FSEditor through the real SynthModem proxy. Viewer variant explicitly enables XMS/UMB, disables EMS and requires its passive observer in upper memory.250ms key framing/20ms input pacing. Editor bytes freeze at a real CPR; held continuation independently checks normal Ctrl-Q abort and unchanged message bodies. No application patch, unframed/SIP/DSP/analog or physical acceptance.')
        if a.keymap_helper:
            from keymap_bbs_support import audit as audit_keymap
            result['keymap']=audit_keymap(out,keymap_folder,stage/'TERMINAL.EXE',require_high=True);checks['actual_keymap_roundtrip']=result['keymap']['passed'];result['passed']=all(checks.values())
        if a.meta_keys_overlay:
            from meta_front_bbs_support import audit as audit_meta
            result['meta_front']=audit_meta(out,binary);checks['actual_Meta_Keys_editor_roundtrip']=result['meta_front']['passed']
            import struct
            observer_segment=struct.unpack('<H',(out/'METASEG.BIN').read_bytes())[0]
            result['meta_observer_segment']=observer_segment;checks['Meta_observer_in_UMB']=observer_segment>=0xa000;result['passed']=all(checks.values())
        if a.file_directory_overlay:
            from file_directory_bbs_support import audit as audit_listing
            result['file_directory']=audit_listing(out);checks['actual_File_Directory_roundtrip']=result['file_directory']['passed'];result['passed']=all(checks.values())
        if a.file_viewer_overlay:
            from file_viewer_bbs_support import audit as audit_viewer
            result['file_viewer']=audit_viewer(out,require_high=True);checks['actual_File_Viewer_roundtrip']=result['file_viewer']['passed'];result['passed']=all(checks.values())
        if a.external_viewer_overlay:
            from external_viewer_bbs_support import audit as audit_external
            import struct
            segment=struct.unpack('<H',(out/'VFSEG.BIN').read_bytes())[0]
            result['external_viewer']=audit_external(out,external_tool)
            checks['actual_external_viewer_roundtrip']=result['external_viewer']['passed']
            checks['external_observer_actually_high']=segment>=0xa000 and base_result['video_observer_high_requested']
            result['external_observer_segment']=segment
            key_segment=struct.unpack('<H',(out/'KEYSEG.BIN').read_bytes())[0]
            checks['external_key_helper_actually_high']=key_segment>=0xa000
            result['external_key_helper_segment']=key_segment;result['passed']=all(checks.values())
        if a.gateway_overlay:
            from gateway_bbs_support import audit as audit_gateway
            result['gateway']=audit_gateway(out);checks['actual_Gateway_roundtrip']=result['gateway']['passed'];result['passed']=all(checks.values())
        if a.phone_log:
            from phone_log_evidence import audit as audit_log
            result['phone_log']=audit_log(out);checks['actual_call_log']=result['phone_log']['passed'];result['passed']=all(checks.values())
        (out/'proxy-integration.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({k:v for k,v in result.items() if k not in ['product_inputs','command','bridge']},indent=2))
        assert result['passed']
    finally:
        proc.terminate()
        try:proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:proc.kill();proc.communicate()

if __name__=='__main__':main()
