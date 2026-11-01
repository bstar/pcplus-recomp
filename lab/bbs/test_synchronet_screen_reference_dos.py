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
from product_inputs import ROOT,select_product,sha
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
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--runtime',required=True,type=Path);p.add_argument('--terminal',required=True,type=Path);p.add_argument('--label',required=True);p.add_argument('--runner',type=Path,default=ROOT/'build/aspect-register-parent-custom-irq/ASPECT.EXE');p.add_argument('--phone-log',action='store_true');a=p.parse_args()
    assert re.fullmatch('[A-Za-z0-9_-]+',a.label)
    fixture_lock=(LAB/'.dos-integration.lock').open('a')
    try:fcntl.flock(fixture_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:raise RuntimeError('Another owned Synchronet DOS integration is active')
    server=snapshot();bodies=message_bodies();stats=statistics()
    binary,sources=select_product(a.terminal,'TERMINAL.EXE');geometry=terminal_geometry(binary);assert geometry['rows']==24
    child,child_sources=select_product(a.runner,'ASPECT.EXE');sources+=child_sources
    names=['lab/bbs/test_synchronet_screen_reference_dos.py','lab/bbs/synthmodem_proxy_serial.js','lab/bbs/terminal_geometry.py','lab/bbs/audio_synchronet_editor_keys.asm','lab/bbs/editor_dos_probe.py','lab/bbs/test_dos.py','lab/bbs/modem.py','lab/bbs/audio_synchronet.py','lab/bbs/audio_synchronet_editor.py','src/aspect/compiler.py']
    sources += [ROOT/n for n in names]+[binary.parent/'terminal.map']
    if a.phone_log:sources += [ROOT/n for n in ('lab/bbs/phone_log_evidence.py','standalone/phone_log_events_watch.asm','standalone/test_phone_log_events_terminal.py')]
    frozen={str(n.relative_to(ROOT)):sha(n) for n in sources}
    base=ROOT/'build/bbs-lab';bridge=base/(a.label+'-proxy');out=base/'results/synchronet'/a.label
    assert not bridge.exists() and not out.exists();out.mkdir(parents=True)
    (out/'server-inputs.json').write_text(json.dumps(server,indent=2)+'\n')
    stage=out/'program';stage.mkdir()
    shutil.copyfile(binary,stage/'TERMINAL.EXE');shutil.copyfile(child,stage/'ASPECT.EXE')
    source=login_script();(stage/'SYNC.ASP').write_text(source);(stage/'SYNC.ASX').write_bytes(compile_source(source))
    helper=out/'EDITKEY.COM'
    subprocess.run(['nasm','-fbin','-DSCREEN_REFERENCE_FREEZE','-DAUDIO_SYNC_EDITOR_SETTLE=72','-DAUDIO_SYNC_EDITOR_KEY_WAIT=9','-DAUDIO_SYNC_EDITOR_FINAL_WAIT=54','-DAUDIO_SYNC_EDITOR_WATCHDOG_TICKS=2160',str(ROOT/'lab/bbs/audio_synchronet_editor_keys.asm'),'-o',str(helper)],check=True)
    generated_paths=[*stage.iterdir(),helper]
    observer=None
    if a.phone_log:
        from phone_log_evidence import build_observer
        observer=build_observer(binary,out/'LOGWATCH.COM');generated_paths.append(observer)
    generated={str(p.relative_to(out)):sha(p) for p in generated_paths}
    proc=subprocess.Popen(['node',str(ROOT/'lab/bbs/synthmodem_proxy_serial.js'),'--runtime',str(a.runtime.resolve()),'--output',str(bridge),'--bbs-port',str(PORT),'--terminal-rows','24','--framing-ms','250','--byte-delay-ms','20','--screen-reference','--screen-quiet-ms','150'],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True)
    try:
        deadline=time.monotonic()+15
        while not (bridge/'ready.json').exists():
            assert proc.poll() is None,'Proxy exited: '+proc.stderr.read()
            assert time.monotonic()<deadline,'Proxy readiness timeout';time.sleep(.05)
        ready=json.loads((bridge/'ready.json').read_text())
        command=[sys.executable,str(ROOT/'lab/bbs/editor_dos_probe.py'),str(stage/'TERMINAL.EXE'),'synchronet','--port',str(ready['endpoint']['port']),'--label',a.label,'--com','3','--baud','19200','--flow','HARD','--directory-fixture','--directory-script-fixture',str(stage/'SYNC.ASX'),'--keyboard-helper',str(helper),'--irq','5','--mouse-scales','8','4','--cpu','8086','--timeout','160','--wait','145','--raw-upstream','--keys','p900 enter']
        if a.phone_log:command+=['--phone-log','--video-observer',str(observer)]
        with (out/'harness.log').open('w') as log:code=subprocess.run(command,cwd=ROOT,stdout=log,stderr=log,timeout=175).returncode
        base_result=json.loads((out/'result.json').read_text())
        closed=json.loads((bridge/'1-closed.json').read_text());proof=json.loads((bridge/'1-screen-reference.json').read_text())
        # The bounded stream stops in the editor. The held continuation must
        # separately prove that the normal Ctrl-Q abort still reached stock
        # FSEditor and that the owned draft was not published.
        delivered=(out/'serial-sent.bin').read_bytes();held=(bridge/'1-held-output.bin').read_bytes()
        semantic=editor_checks(delivered+held)
        screen=(out/'SCREEN.BIN').read_bytes();text=screen[:3840:2].decode('cp437')
        stages=(out/'STAGES.LOG').read_text() if (out/'STAGES.LOG').exists() else ''
        after_stats=statistics()
        checks=dict(harness=code==0 and base_result['passed'],runtime_unchanged=closed['source_unchanged'],
                    server_static_inputs_unchanged=snapshot()==server,message_bodies_unchanged=message_bodies()==bodies,
                    no_message_mail_or_transfer_writes=all(stats['Total'][k]==after_stats['Total'][k] for k in ('posts','email','feedback','uploads','uploadb','dnloads','dnloadb')),
                    actual_ASPECT_login=stages=='BRIDGE|LOGIN|PASSWORD|WELCOME|BULLETINS|SCAN|MAIN|GENERAL|SUBJECT|EDITOR|' and (out/'SCRIPT.OK').read_bytes()==b'PASS',
                    staged_inputs_unchanged=generated=={str(p.relative_to(out)):sha(p) for p in generated_paths},
                    frozen_editor_frame='FSEditor v1.105' in text and 'UNSAVED' in text,
                    actual_CPR_boundary=proof['armed'] and proof['frozen'] and proof['reply'] is not None,
                    fixture_CPR_consumed=proof['probeReplyConsumed'],compiled_geometry_advertised=ready['terminalRows']==geometry['rows'],
                    source_inputs_unchanged=frozen=={str(n.relative_to(ROOT)):sha(n) for n in sources},**semantic)
        result=dict(passed=all(checks.values()),checks=checks,server='Synchronet',binary_sha256=sha(binary),interpreter_sha256=sha(child),generated_inputs=generated,stages=stages,screen_sha256=sha(out/'SCREEN.BIN'),terminal_geometry=geometry,screen_reference=proof,bridge=ready,command=command,product_inputs=frozen,
                    scope='Actual DOS8086 COM3/IRQ5 candidate and stock owned Synchronet FSEditor through the real SynthModem proxy.250ms key framing/20ms input pacing. Editor bytes freeze at a real CPR; held continuation independently checks normal Ctrl-Q abort and unchanged message bodies. No application patch, unframed/SIP/DSP/analog or physical acceptance.')
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
