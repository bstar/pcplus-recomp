#!/usr/bin/env python3
"""Ordinary sound-enabled terminal/ASPECT products with passive speaker sampling."""
import argparse,json,re,shutil,struct,subprocess,sys
from pathlib import Path
import test_aspect_renderer_dos as render
from test_aspect_parent_process_dos import prepare_observer
from directory_fixtures import directory,prm
ROOT=render.ROOT;sha=render.sha
sys.path.insert(0,str(ROOT/'src/aspect'))
from compiler import compile_source

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--label',required=True);parser.add_argument('--mouse',action='store_true');parser.add_argument('--input',action='store_true');parser.add_argument('--no-driver',action='store_true');parser.add_argument('--notice-help',action='store_true');args=parser.parse_args();assert re.fullmatch(r'[A-Za-z0-9_-]+',args.label)
    if args.input:assert args.mouse
    if args.no_driver:assert args.input
    if args.notice_help:assert args.input
    out=ROOT/'build/program-sound-smoke'/args.label;out.mkdir(parents=True,exist_ok=False)
    parent=ROOT/('build/terminal-mouse-notice-sound/TERMINAL.EXE' if args.mouse else 'build/terminal-notice-sound/TERMINAL.EXE');child=ROOT/'build/aspect-notice-sound-parent/ASPECT.EXE';sources={}
    if args.input:parent=ROOT/'build/terminal-mouse-notice-input/TERMINAL.EXE';child=ROOT/'build/aspect-notice-input-parent/ASPECT.EXE'
    if args.notice_help:child=ROOT/'build/aspect-notice-help-parent/ASPECT.EXE'
    for product in (parent,child):
        m=json.loads((product.parent/'manifest.json').read_text());assert m['binary_sha256']==sha(product)
        for n,h in m['sources'].items():assert n not in sources or sources[n]==h;sources[n]=h
    for n in ['standalone/test_program_sound_smoke_dos.py','standalone/test_aspect_parent_process_dos.py','standalone/test_aspect_renderer_dos.py','standalone/test_connection_dos.py','standalone/test_terminal.py','standalone/directory_fixtures.py','standalone/modem_fixtures.py','standalone/terminal_config_fixtures.py','standalone/directory_test_support.py','standalone/notice_success_child.asm','src/aspect/compiler.py']:sources[n]=sha(ROOT/n)
    if args.input:
        sources['standalone/notice_input_parent_probe.py']=sha(ROOT/'standalone/notice_input_parent_probe.py')
        sources['standalone/notice_input_no_driver_probe.py']=sha(ROOT/'standalone/notice_input_no_driver_probe.py')
        for product,mapname in [(parent,'terminal.map'),(child,'ASPECT.map')]:
            for path in [product.parent/mapname,product.parent/'manifest.json']:sources[str(path.relative_to(ROOT))]=sha(path)
    if args.mouse:
        for n in ['standalone/mouse_parent_probe.py','standalone/mouse_sound_checks.py']:sources[n]=sha(ROOT/n)
    for n,h in sources.items():
        assert sha(ROOT/n)==h;npath=out/'sources'/n;npath.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/n,npath)
    render.OUT=out;observer,size=prepare_observer(out,render.map_offsets(parent.parent/'terminal.map'),parent.parent/'terminal.map',sound_probe=True,mouse_probe=args.mouse and not args.no_driver)
    source=(out/'observer.asm').read_text();assert source.count('timer:\n save\n')==source.count('sample_end:')==1
    source=source.replace('sample_end:','audio_ticks: dw 0\nsample_end:').replace('timer:\n save\n', '''timer:
 save
 ; Passive hardware read only, while the ordinary ASPECT EXEC is live.
 cmp word [cs:exec_seen],1
 jne .audio_done
 cmp word [cs:exec_done],0
 jne .audio_done
 in al,0x61
 and al,3
 cmp al,3
 jne .audio_done
 inc word [cs:audio_ticks]
.audio_done:
''')
    (out/'observer.asm').write_text(source);subprocess.run(['nasm','-fbin',str(out/'observer.asm'),'-o',str(out/'RENDER.COM')],check=True);observer=(out/'RENDER.COM').read_bytes()
    harness=render.adapter(cpu='8086');results=[]
    script='proc main\nwaitfor "LOGIN:" 5\nset display off\nset keys off\nputenv "PATH="\nrun "ABSENT.COM"\nif success\ntransmit "BAD"\nexit\nendif\nrun "SUCCESS.COM"\nif failure\ntransmit "BAD"\nexit\nendif\nset display on\nmessage "AFTER SOUND"\ntransmit $D_PWORD\ntransmit "^M"\npause 1\nendproc\n'
    for setting,port in [(0,1),(1,1),(65535,2)]:
        name=f'sound-{setting}-com{port}';folder=out/name;folder.mkdir();shutil.copyfile(parent,folder/'TERMINAL.EXE');shutil.copyfile(child,folder/'ASPECT.EXE');harness.BINARY=folder/'TERMINAL.EXE'
        subprocess.run(['nasm','-fbin',str(out/'sources/standalone/notice_success_child.asm'),'-o',str(folder/'SUCCESS.COM')],check=True)
        event=8 if setting==1 else 2;bios=16 if setting else 0
        if args.input:
            if args.no_driver:
                from notice_input_no_driver_probe import instrument
                child_source=instrument(source,child.parent/'ASPECT.map')
            else:
                from notice_input_parent_probe import instrument
                child_source=instrument(source,child.parent/'ASPECT.map',event)
            (folder/'child-observer.asm').write_text(child_source)
            subprocess.run(['nasm','-fbin',str(folder/'child-observer.asm'),'-o',str(folder/'RENDER.COM')],check=True)
            observer=(folder/'RENDER.COM').read_bytes()
        files={'LOGIN.ASP':script.encode(),'LOGIN.ASX':compile_source(script),'SUCCESS.COM':(folder/'SUCCESS.COM').read_bytes(),'RENDER.COM':observer}
        payload=bytearray(directory(port=port));payload[302:311]=b'LOGIN\0\0\0\0';payload[325:336]=b'Synth42\0\0\0\0'
        settings=bytearray(prm(port=port,soft=0,hard=1));struct.pack_into('<H',settings,0x1bc,setting)
        scales=((9,5) if setting==1 else (999,1) if setting==65535 else (8,4)) if args.input else (8,4)
        if args.mouse:struct.pack_into('<HH',settings,0x4e4,*scales)
        harness.RENDER_POST=render.QUERY;harness.RENDER_TRIGGER=b'Synth42\r'
        result=harness.run(name,'success','p9000 space p700 '+('a-z p1500 escape ' if args.no_driver else 'a-z p1500 ' if args.mouse else '')+'r e a d y p700 a-x',directory=bytes(payload),prm=bytes(settings),com=port,arguments='@D:\\TEST.PRM /E:D:\\TEST.DIR /N:1 /A:NETWORK'+(' /B:'+('ENHANCED' if bios else 'STANDARD') if args.input else ''),files=files,banner=b'\x1b[2J\x1b[HFIRST BYTE SAFE\x1b[6n\x1b[0cLOGIN:',working_drive='d',observer='RENDER')
        capture=(folder/'RENDER.BIN').read_bytes();child_input=None
        if args.input:
            if args.no_driver:
                from notice_input_no_driver_probe import WORDS,BYTES
            else:
                from notice_input_parent_probe import WORDS,BYTES
            child_input=dict(zip(WORDS,struct.unpack_from('<'+str(len(WORDS))+'H',capture,len(capture)-BYTES)))
            capture=capture[:-BYTES]
        audio=struct.unpack('<H',capture[-2:])[0];raw=capture[:-2];head=struct.unpack_from('<7H',raw);owners=struct.unpack_from('<13H',raw,len(raw)-26-32*70-size*2)
        wire=(folder/'serial.bin').read_bytes();screen=(folder/'SCREEN.BIN').read_bytes()[::2]
        checks=result['checks'];checks.update(ordinary_ASPECT_success=head[:4]==(0x524e,1,1,1) and head[6]==0,parent_JFT=raw[14:34]==raw[34:54],parent_file_owners=raw[54:470]==raw[470:886],parent_resources=owners[2]==0 and raw[-size*2:-size]==raw[-size:],parent_lease_retired=owners[7]==0 and owners[8]==owners[9] and owners[8]>=2,
            passive_sound_policy=bool(audio)==bool(setting),real_success_child=(folder/'SUCCESS.OK').exists() and (folder/'SUCCESS.OK').read_bytes()==b'OK',continued_session=b'AFTER SOUND' in screen and b'BAD' not in wire and b'ready' in wire and wire.count(b'Synth42\r')==1)
        if args.input:
            c=child_input;cause=2 if event==8 else 1;key=27 if event==8 else 13
            if args.no_driver:
                checks.update(child_BIOS_fallback=c['seen']==c['exit_seen']==1,INT33_absent_until_child_exit=c['exit_vector_zero']==1,child_BIOS_mode=c['bios']==bios,BIOS_key_seeded=c['seed_status']==0,INT33_vector_restored=(c['old_off'],c['old_seg'])==(c['after_off'],c['after_seg']) and bool(c['old_off'] or c['old_seg']),child_notice_read=(c['notice_status'],c['notice_cause'],c['notice_key'],c['notice_service'])==(1,1,13,0))
            else:
                checks.update(child_native_input=c['seen']==c['exit_seen']==1,child_scales=(c['scale_x'],c['scale_y'])==scales,child_BIOS_mode=c['bios']==bios,child_foreign_DS=c['returned_ds']==0x40,child_native_event=(c['event'],c['queued_count'],c['queued_code'])==(event,1,5 if event==8 else 4),child_notice_read=(c['notice_status'],c['notice_cause'],c['notice_key'],c['notice_service'])==(cause,cause,key,0))
        mouse=None
        if args.mouse and not args.no_driver:
            from mouse_sound_checks import verify
            mouse_checks,mouse=verify(raw,parent.parent/'terminal.map',size,folder,expected_scales=scales);checks.update(mouse_checks)
            if args.input:checks['child_callback_retired_before_DOS_exit']=(child_input['exit_mask'],child_input['exit_off'],child_input['exit_seg'])==(mouse['suspended_mask'],mouse['suspended_off'],mouse['suspended_seg'])
        result.update(child_input=child_input,observer_sha256=sha(folder/'RENDER.COM'),mouse=mouse,passed=all(checks.values()),speaker_active_timer_samples=audio,sound=setting,port=port,passive_header=head,owner_words=owners,compared_parent_bytes=size)
        (folder/'result.json').write_text(json.dumps(result,indent=2)+'\n');results.append(result)
        print(name,'FINAL PASS' if result['passed'] else 'FINAL FAIL '+','.join(k for k,v in checks.items() if not v),flush=True)
    assert all(sha(ROOT/n)==h for n,h in sources.items())
    report=dict(mouse=args.mouse,native_notice_input=args.input,no_driver=args.no_driver,passed=all(r['passed'] for r in results),cases=results,sources=sources,parent_sha256=sha(parent),child_sha256=sha(child),observer_sha256=sha(out/'RENDER.COM'),scope=__doc__+' No diagnostic ASPECT driver or product patch. Audio sampling only reads speaker gate bits during live EXEC. '+('The separate mouse probe exchanges INT33 registration and deliberately invokes the actual native callback/menu events, then checks full driver restoration. ' if args.mouse else 'The observer does not program speaker ports or invoke product helpers. ')+'Mixer muted, so this is not acoustic or physical audio evidence.')
    if args.input:
        report['observer_variants']={r['case']:r['observer_sha256'] for r in results}
        report['scope']='Ordinary matching terminal/ASPECT products: configured sound, missing PROGRAM target, successful subsequent DOS child and continued serial input. '+('Owned test disables INT33 before terminal startup, seeds a BIOS Enter at the rendered popup, observes selected BIOS mode and notice read, checks INT33 remains absent at child exit, and restores the original vector after terminal exit. No mouse callback is invoked and no opaque driver-state comparison is claimed in this variant. ' if args.no_driver else 'Separate active INT33 probe verifies the child callback target against its map/PSP, invokes actual native Enter/Escape with foreign DS, observes configured scales/BIOS mode and final notice result, and checks the prior suspended registration before DOS child exit. The existing active parent probe then verifies resume, menu events and complete driver-state restoration. ')+'Independent speaker-gate reads; muted mixer. Physical clicks, acoustic output, contextual Alt-Z UI and full application acceptance remain open.'
    report['notice_help']=args.notice_help
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
