#!/usr/bin/env python3
"""Run the branded DOS terminal through an actual proxy against stock lab ENiGMA.

Run inside tools/dev, with the separate tools/bbs-dev stock ENiGMA already up.
All credentials and posts belong to that synthetic fixture. No live service
configuration is imported, changed or restarted.
"""
import argparse
import fcntl
import json
from pathlib import Path
import re
import subprocess
import sys
import time
import struct

from enigma import process_pid, SOURCE
from product_inputs import ROOT, select_product, sha
from check_editor_dos import audit


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runtime', type=Path, required=True)
    p.add_argument('--terminal', type=Path, required=True)
    p.add_argument('--label', required=True)
    p.add_argument('--framing-ms', type=int, choices=[0,250], default=0)
    p.add_argument('--byte-delay-ms', type=int, choices=range(21), default=2)
    p.add_argument('--reference-overlay', action='store_true', help='Observe Alt-Z/refusal during the stock BBS editor workflow')
    p.add_argument('--directory-overlay', action='store_true', help='Observe read-only Alt-D loading/pages during the stock editor workflow')
    p.add_argument('--directory-preview-overlay', action='store_true', help='Observe validated Alt-D preview inside the stock editor workflow')
    p.add_argument('--screen-reference', action='store_true', help='Match compiled geometry and freeze incoming bytes after a real final CPR probe')
    p.add_argument('--multiline-editor', choices=['page-up','page-down'], help='Native BIOS input enters24 lines and exercises actual editor page navigation')
    p.add_argument('--phone-log', action='store_true', help='Enable and passively audit the call log during the real BBS workflow')
    args = p.parse_args()
    if args.directory_preview_overlay:args.directory_overlay=True
    assert re.fullmatch('[A-Za-z0-9_-]+', args.label)
    assert not (args.reference_overlay and args.directory_overlay)
    if args.multiline_editor:
        assert args.screen_reference and not args.reference_overlay and not args.directory_overlay
    if args.phone_log:assert not args.reference_overlay and not args.directory_overlay
    assert process_pid(), 'Start the owned stock ENiGMA fixture first'
    # One synthetic account/server log is shared by these runs. Keep its
    # authentication/menu audit unambiguous; independent DOS fixtures may run
    # concurrently, but two sessions against this fixture may not.
    fixture_lock=(ROOT/'build/bbs-lab/enigma/.dos-integration.lock').open('a')
    try:fcntl.flock(fixture_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:raise RuntimeError('Another owned ENiGMA DOS integration is active; wait for it to finish')
    binary, sources = select_product(args.terminal, 'TERMINAL.EXE')
    from terminal_geometry import terminal_geometry
    geometry=terminal_geometry(binary)
    sources += [binary.parent/'terminal.map',ROOT/'lab/bbs/terminal_geometry.py']
    if args.phone_log:
        sources += [ROOT/n for n in ('lab/bbs/phone_log_evidence.py','standalone/phone_log_events_watch.asm','standalone/test_phone_log_events_terminal.py')]
    if args.multiline_editor:
        sources += [ROOT/'lab/bbs/test_synthmodem_proxy_dos.py',ROOT/'lab/bbs/audio_synchronet_editor_keys.asm',ROOT/'lab/bbs/test_dos.py',ROOT/'lab/bbs/editor-recipes.json',ROOT/'lab/bbs/check_editor_dos.py',ROOT/'lab/bbs/enigma_multiline.py']
    reference_args=['--terminal-rows',str(geometry['rows'])]+(['--screen-reference'] if args.screen_reference else [])
    before = {str(f.relative_to(ROOT)): sha(f) for f in sources}
    base = ROOT/'build/bbs-lab'
    bridge = base/(args.label+'-proxy')
    output = base/'results/enigma'/args.label
    assert not bridge.exists() and not output.exists(), 'Use a new result label'
    log_path = base/(args.label+'-harness.log')
    assert not log_path.exists()
    proc = subprocess.Popen(['node', str(ROOT/'lab/bbs/synthmodem_proxy_serial.js'),
        '--runtime', str(args.runtime.resolve()), '--output', str(bridge),
        '--framing-ms', str(args.framing_ms), '--byte-delay-ms', str(args.byte_delay_ms),*reference_args],
        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    try:
        deadline = time.monotonic()+15
        while not (bridge/'ready.json').exists():
            assert proc.poll() is None, 'Proxy exited: '+proc.stderr.read()
            assert time.monotonic() < deadline, 'Proxy readiness timeout'
            time.sleep(.05)
        ready = json.loads((bridge/'ready.json').read_text())
        keys = 'p900 enter p2500 l o c enter '+json.loads(
            (ROOT/'lab/bbs/editor-recipes.json').read_text())['enigma_unsaved']['keyboard_input']
        observer=None
        if args.phone_log:
            from phone_log_evidence import build_observer
            observer=build_observer(binary,base/(args.label+'-logwatch.COM'))
        if args.reference_overlay:
            assert json.loads((binary.parent/'manifest.json').read_text())['experimental_original_reference']
            marker='K E Y T E S T enter p1800 '
            assert keys.count(marker)==1
            keys=keys.replace(marker,marker+'a-z p600 a-d p600 escape p500 ')
            observer=base/(args.label+'-observer.COM')
            assert not observer.exists()
            subprocess.run(['nasm','-fbin',str(ROOT/'standalone/reference_watch.asm'),'-o',str(observer)],check=True)
        if args.directory_overlay:
            assert json.loads((binary.parent/'manifest.json').read_text())['experimental_directory_view']
            marker='K E Y T E S T enter p1800 '
            assert keys.count(marker)==1
            resource_owner=bool(json.loads((binary.parent/'manifest.json').read_text()).get('experimental_directory_resource_owner'))
            compile_owner=bool(json.loads((binary.parent/'manifest.json').read_text()).get('experimental_directory_compile'))
            adopt_owner=bool(json.loads((binary.parent/'manifest.json').read_text()).get('experimental_directory_adopt'))
            keys=keys.replace(marker,marker+('a-d p600 enter p3500 enter p1800 '+(('a p700 ' if adopt_owner else 'c p700 ' if compile_owner else 'r p700 ') if resource_owner else '')+'escape p500 end p3500 escape p500 ' if args.directory_preview_overlay else 'a-d p600 enter p3500 end p3500 escape p500 '))
            observer=base/(args.label+'-observer.COM')
            assert not observer.exists()
            subprocess.run(['nasm','-fbin',*(['-DDIRECTORY_ADOPT']if adopt_owner else[]),*(['-DDIRECTORY_PREVIEW']if args.directory_preview_overlay else[]),*(['-DDIRECTORY_RESOURCE_OWNER']if resource_owner and args.directory_preview_overlay else[]),str(ROOT/'standalone/directory_view_watch.asm'),'-o',str(observer)],check=True)
        exit_wait='2'
        keyboard_helper=None
        if args.multiline_editor:
            # Keep the measured owned login/subject recipe, then wait for both
            # actual editor markers before a separate native BIOS key producer.
            marker='K E Y T E S T enter p1800 '
            assert keys.count(marker)==1
            keys=keys[:keys.index(marker)+len(marker)]
            folder=base/(args.label+'-keys');folder.mkdir()
            scans=dict(R=0x13,U=0x16,P=0x19,M=0x32,A=0x1e,K=0x25,N=0x31,
                       S=0x1f,V=0x2f,E=0x12,D=0x20)
            scans.update({str(n):n+1 if n else 11 for n in range(10)})
            def words(text):return [(scans[c]<<8)|ord(c) for c in text]
            sequence=[0x1519]
            for n in range(1,25):sequence+=words(f'R{n:02}')+[0x1c0d]
            sequence += [0x4900]+words('UPMARK')
            if args.multiline_editor=='page-down':sequence += [0x5100]
            sequence += words('UNSAVED')+[0x2d00,0]
            (folder/'multiline_keys.inc').write_text('dw '+','.join(hex(word) for word in sequence)+'\n')
            keyboard_helper=folder/'MULTKEY.COM'
            subprocess.run(['nasm','-fbin','-DENIGMA_MULTILINE','-DSCREEN_REFERENCE_FREEZE',
                '-DAUDIO_SYNC_EDITOR_SETTLE=72','-DAUDIO_SYNC_EDITOR_KEY_WAIT=6',
                '-DAUDIO_SYNC_EDITOR_FINAL_WAIT=90','-DAUDIO_SYNC_EDITOR_WATCHDOG_TICKS=2520',
                '-I'+str(folder)+'/',str(ROOT/'lab/bbs/audio_synchronet_editor_keys.asm'),
                '-o',str(keyboard_helper)],check=True)
            exit_wait='65'
        if args.directory_preview_overlay and resource_owner:
            # Preserve the recipe's3-second final pause and one ordinary Alt-X,
            # supplied by the adapter. Its redundant second exit would push
            # this expanded preflight recipe past the DOS500-character bound.
            assert keys.endswith(' p3000 a-x')
            keys=keys[:-len(' p3000 a-x')]
            exit_wait='3'
        command = [sys.executable, str(ROOT/'lab/bbs/editor_dos_probe.py'), str(binary),
            'enigma', '--port', str(ready['endpoint']['port']),
            '--server-log', str(SOURCE/'logs/enigma-bbs.log'), '--label', args.label,
            '--com', '3', '--baud', '19200', '--flow', 'HARD', '--dial-fixture',
            '--irq', '5', '--mouse-scales', '8', '4', '--cpu', '8086',
            '--timeout', '160', '--wait', exit_wait, '--raw-upstream', '--keys', keys]
        if observer:command+=['--video-observer',str(observer)]
        if args.phone_log:command+=['--phone-log']
        if keyboard_helper:command+=['--keyboard-helper',str(keyboard_helper)]
        if args.directory_overlay:command+=['--directory-view-fixture']
        with log_path.open('w') as log:
            run = subprocess.run(command, cwd=ROOT, stdout=log, stderr=log, timeout=175)
        # Audit even a failed harness when artifacts exist. A normal DOS return
        # cannot substitute for actual authentication and editor semantics.
        semantic = audit('enigma', args.label, disconnect=True,keyboard_profile='enigma-multiline' if args.multiline_editor else 'network',multiline_mode=args.multiline_editor)
        closed = json.loads((bridge/'1-closed.json').read_text())
        video = (output/'SCREEN.BIN').read_bytes()
        text = '\n'.join(video[i:i+160:2].decode('cp437') for i in range(0,4000,160))
        checks = dict(harness=run.returncode == 0, semantic_audit=semantic,
            exact_screen=len(video)==4000 and 'UNSAVED' in text and 'OVR 01,08' in text,
            proxy_source_unchanged=closed['source_unchanged'],
            product_source_unchanged=all(sha(ROOT/n)==h for n,h in before.items()))
        multiline={}
        if args.multiline_editor:
            report=json.loads((output/'semantic-audit.json').read_text())
            checks['exact_screen']=len(video)==4000 and 'UNSAVED' in text
            multiline=report['authority']['multiline']
            multiline.update(helper_sha256=sha(keyboard_helper),key_source_sha256=sha(keyboard_helper.parent/'multiline_keys.inc'))
        observed={}
        if args.reference_overlay:
            capture=(output/'REFVIEW.BIN').read_bytes();assert len(capture)==12006
            magic,flags,ticks=struct.unpack_from('<3H',capture)
            names=json.loads((ROOT/'reconstruction/command_reference/provenance.json').read_text())['labels']
            checks['actual_reference_observed']=magic==0x5246 and flags&1!=0 and ticks>20
            checks['all_39_reference_commands']=all(r['name'].encode() in capture[6:4006:2] for r in names)
            checks['unavailable_AltD_observed']=flags&2!=0 and b'Not available in this build:' in capture[4006:8006:2]
            observed=dict(flags=flags,ticks=ticks,capture_sha256=sha(output/'REFVIEW.BIN'),font_sha256=sha(output/'VGA16.BIN'),observer_sha256=sha(observer))
        if args.directory_overlay:
            capture=(output/'DIRVIEW.BIN').read_bytes();assert len(capture)==(20006 if args.directory_preview_overlay and resource_owner else 16006 if args.directory_preview_overlay else 12006)
            magic,flags,ticks=struct.unpack_from('<3H',capture)
            first,last,loading=(capture[6+i*4000:4006+i*4000:2] for i in range(3))
            checks['directory_prompt_and_loading']=magic==0x4456 and flags&12==12 and b'Reading directory...' in loading
            checks['directory_first_and_last_pages']=flags&3==3 and b'LoSs oF CoNtRoL' in first and b'FINAL 200' in last
            checks['no_private_directory_fields']=all(b'HIDDENPASS' not in frame and b'SECRETA' not in frame for frame in (first,last,loading))
            if args.directory_preview_overlay:
                proposed=capture[12006:16006:2]
                checks['directory_preview_observed']=flags&16!=0 and b'SELECTED ENTRY // PROPOSED SETTINGS' in proposed
                checks['preview_target_and_DTE']=b'555' in proposed and b'19200' in proposed
                checks['preview_privacy']=b'HIDDENPASS' not in proposed and b'SECRETA' not in proposed
                if resource_owner:
                    blocked=capture[16006:20006:2]
                    checks['online_resource_check_refused']=flags&32!=0 and b'Resource check unavailable.' in blocked
                    wire=(output/'serial-received.bin').read_bytes()
                    if compile_owner:
                        assert wire.count(b'KEYTEST\r')==1
                        checks['online_compile_request_refused']=checks['online_resource_check_refused']
                        checks['resource_check_key_stayed_local']=(b'a' if adopt_owner else b'c') not in wire.split(b'KEYTEST\r',1)[1]
                        if adopt_owner:checks['online_selection_adoption_refused']=checks['online_resource_check_refused']
                    else:checks['resource_check_key_stayed_local']=b'r' not in wire
            observed=dict(flags=flags,ticks=ticks,capture_sha256=sha(output/'DIRVIEW.BIN'),font_sha256=sha(output/'VGA16.BIN'),observer_sha256=sha(observer))
        result = dict(passed=all(checks.values()), checks=checks,
            terminal_geometry=geometry,
            bridge=ready, command=command, binary_sha256=sha(binary),
            screen_sha256=sha(output/'SCREEN.BIN'), product_inputs=before,
            reference_observer=observed,
            scope='Actual DOS8086 COM3/IRQ5 terminal, synthetic Hayes/nullmodem, '
                  'actual SynthModem proxy and stock loopback ENiGMA. '
                  'Explicit paced serial delivery; no SIP/DSP, physical CTS or analog acceptance.')
        if args.phone_log:
            from phone_log_evidence import audit as audit_log
            result['phone_log']=audit_log(output)
            checks['actual_call_log']=result['phone_log']['passed']
            result['passed']=all(checks.values())
        if args.multiline_editor:result['multiline_editor']=multiline
        if args.screen_reference:
            proof=json.loads((bridge/'1-screen-reference.json').read_text())
            checks.update(reference_freeze_completed=proof['armed'] and proof['frozen'] and proof['reply'] is not None,
                          compiled_geometry_advertised=ready['terminalRows']==geometry['rows'])
            result.update(passed=all(checks.values()),terminal_geometry=geometry,screen_reference=proof)
        (output/'proxy-integration.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result,indent=2))
        return 0 if result['passed'] else 1
    finally:
        proc.terminate()
        try: proc.communicate(timeout=5)
        except subprocess.TimeoutExpired: proc.kill(); proc.communicate()


if __name__ == '__main__':
    raise SystemExit(main())
