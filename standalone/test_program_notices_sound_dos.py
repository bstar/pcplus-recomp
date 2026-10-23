#!/usr/bin/env python3
"""Actual configured PROGRAM sound, attached terminal and synchronous fault recovery."""
import argparse,json,re,shutil,struct,subprocess,sys
from pathlib import Path
import test_aspect_renderer_dos as render
from test_aspect_parent_process_dos import prepare_observer
PAYLOAD=b"Q"*500+b"ENDMARK!"
from directory_fixtures import directory,prm
ROOT=render.ROOT;sha=render.sha
sys.path.insert(0,str(ROOT/'src/aspect'))
from compiler import compile_source

def scripts():
    opening='set display off\nset keys off\nset fgets_crlf off\nputenv "PATH="\n'
    for i in range(5):opening+=f'fopen {i} "SLOT{i}.BIN" "rb"\nfgetc {i} value\n'
    first='integer value\nproc main\nwaitfor "LOGIN:" 5\n'+opening+'fopen 5 "WRITE.BIN" "wb"\nfputs 5 "FIRST"\ntransmit "PAYLOAD!"\nrun "ABSENT.COM"\nendproc\n'
    second='integer value\nlong position\nproc main\nwaitfor "ENDMARK!" 5\nif waitfor\nelse\ntransmit "BAD"\nexit\nendif\n'+opening+'fopen 5 "WRITE.BIN" "ab"\nfputs 5 "SECOND"\nrun "ABSENT.COM"\n'
    for i in range(5):second+=f'ftell {i} position\nif position!=1L\ntransmit "BAD"\nexit\nendif\nfgetc {i} value\nif value!=69\ntransmit "BAD"\nexit\nendif\nfclose {i}\n'
    second+='fclose 5\nrun "SUCCESS.COM"\nif failure\ntransmit "BAD"\nexit\nendif\nset display on\nmessage "RECOVERY OK"\ntransmit $D_PWORD\ntransmit "^M"\npause 1\nendproc\n'
    return first,second

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label',required=True);parser.add_argument('--mode',action='append',choices=['1D','2D','3D','2A','2F'])
    parser.add_argument('--input',action='store_true');parser.add_argument('--mouse',action='store_true');parser.add_argument('--sound',type=int,choices=[0,1,65535],default=1)
    parser.add_argument('--notice-help',action='store_true')
    parser.add_argument('--quarantine',choices=['guard','foreign','speaker']);parser.add_argument('--port',type=int,choices=[1,2],default=1)
    args=parser.parse_args();assert re.fullmatch(r'[A-Za-z0-9_-]+',args.label)
    if args.input:assert args.mouse
    if args.notice_help:assert args.input and not args.quarantine and args.mode and all(m in ('2D','2A','2F') for m in args.mode)
    out=ROOT/'build/program-notices-sound'/args.label;out.mkdir(parents=True,exist_ok=False)
    parent=ROOT/('build/terminal-mouse-notice-sound/TERMINAL.EXE' if args.mouse else 'build/terminal-notice-sound/TERMINAL.EXE');child=ROOT/'build/aspect-notice-sound-fault/ASPECT.EXE';sources={}
    if args.input:parent=ROOT/'build/terminal-mouse-notice-input/TERMINAL.EXE';child=ROOT/'build/aspect-notice-input-fault/ASPECT.EXE'
    if args.notice_help:child=ROOT/'build/aspect-notice-help-fault/ASPECT.EXE'
    for product in (parent,child):
        manifest=json.loads((product.parent/'manifest.json').read_text());assert manifest['binary_sha256']==sha(product)
        for name,digest in manifest['sources'].items():
            assert name not in sources or sources[name]==digest,name
            sources[name]=digest
    for name in ('standalone/test_program_notices_sound_dos.py','standalone/test_program_notices_dos.py','standalone/test_aspect_parent_process_dos.py','standalone/test_aspect_renderer_dos.py','standalone/test_connection_dos.py','standalone/test_terminal.py','standalone/directory_fixtures.py','standalone/modem_fixtures.py','standalone/terminal_config_fixtures.py','standalone/directory_test_support.py','standalone/notice_success_child.asm','src/aspect/compiler.py'):sources[name]=sha(ROOT/name)
    if args.mouse:
        for name in ['standalone/mouse_parent_probe.py','standalone/mouse_sound_checks.py']:sources[name]=sha(ROOT/name)
    if args.input:
        for name in ['standalone/notice_input_fault_probe.py','standalone/notice_input_parent_probe.py']:
            sources[name]=sha(ROOT/name)
        for product,mapname in [(parent,'terminal.map'),(child,'ASPECT.map')]:
            for path in [product.parent/mapname,product.parent/'manifest.json']:sources[str(path.relative_to(ROOT))]=sha(path)
    if args.notice_help:sources['standalone/notice_help_probe.py']=sha(ROOT/'standalone/notice_help_probe.py')
    for name,digest in sources.items():
        assert sha(ROOT/name)==digest,name
        target=out/'sources'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
    render.OUT=out;observer,size=prepare_observer(out,render.map_offsets(parent.parent/'terminal.map'),parent.parent/'terminal.map',sound_probe=True,mouse_probe=args.mouse)
    if args.input:
        if args.notice_help:
            from notice_help_probe import instrument
            source=instrument((out/'observer.asm').read_text(),child.parent/'ASPECT.map',fault=True)
        else:
            from notice_input_fault_probe import instrument
            source=instrument((out/'observer.asm').read_text(),child.parent/'ASPECT.map')
        (out/'observer.asm').write_text(source)
        subprocess.run(['nasm','-fbin',str(out/'observer.asm'),'-o',str(out/'RENDER.COM')],check=True);observer=(out/'RENDER.COM').read_bytes()
    harness=render.adapter(cpu='8086',timeout_seconds=40 if args.notice_help else 20);results=[];first,second=scripts();port=args.port
    for mode in args.mode or ['1D','2D','3D','2A','2F']:
        assert not args.quarantine or mode in ('2D','2A','2F')
        name=mode;folder=out/name;folder.mkdir();shutil.copyfile(parent,folder/'TERMINAL.EXE');shutil.copyfile(child,folder/'ASPECT.EXE');harness.BINARY=folder/'TERMINAL.EXE'
        subprocess.run(['nasm','-fbin',str(out/'sources/standalone/notice_success_child.asm'),'-o',str(folder/'SUCCESS.COM')],check=True)
        files={'LOGIN.ASP':first.encode(),'LOGIN.ASX':compile_source(first),'RECOVER.ASP':second.encode(),'RECOVER.ASX':compile_source(second),'RENDER.COM':observer,'SUCCESS.COM':(folder/'SUCCESS.COM').read_bytes()}
        for i in range(5):files[f'SLOT{i}.BIN']=b'SEED0'
        payload=bytearray(directory(port=port));payload[302:311]=b'LOGIN\0\0\0\0';payload[325:336]=b'Synth42\0\0\0\0'
        harness.RENDER_POST=PAYLOAD;harness.RENDER_TRIGGER=b'PAYLOAD!'
        request=mode+str(port)+('H' if args.notice_help else 'N')+({'guard':'G','foreign':'W','speaker':'S'}.get(args.quarantine,'N'))+'P'
        settings=bytearray(prm(port=port,soft=0,hard=1));struct.pack_into('<H',settings,0x1bc,args.sound)
        if args.mouse:struct.pack_into('<HH',settings,0x4e4,8,4)
        result=harness.run(name,'success','p12000 space p700 '+('a-z p1500 ' if args.mouse else '')+'r e a d y p700 a-x',directory=bytes(payload),prm=bytes(settings),com=port,
            arguments='@D:\\TEST.PRM /E:D:\\TEST.DIR /N:1 /A:NETWORK',files=files,environment={'PCPNOTICE':request},
            banner=b'\x1b[2J\x1b[HFIRST BYTE SAFE\x1b[6n\x1b[0cLOGIN:',working_drive='d',observer='RENDER')
        raw=(folder/'RENDER.BIN').read_bytes();child_input=None;help_probe=None;help_frames=None
        if args.notice_help:
            from notice_help_probe import WORDS,BYTES
            start=len(raw)-BYTES;help_probe=dict(zip(WORDS,struct.unpack_from('<'+str(len(WORDS))+'H',raw,start)))
            help_frames=raw[start+len(WORDS)*2:];raw=raw[:start]
        if args.input:
            from notice_input_fault_probe import WORDS,BYTES
            child_input=dict(zip(WORDS,struct.unpack_from('<'+str(len(WORDS))+'H',raw,len(raw)-BYTES)));raw=raw[:-BYTES]
        head=struct.unpack_from('<7H',raw);owners=struct.unpack_from('<13H',raw,len(raw)-26-32*70-size*2)
        report=(folder/'NOTICE.BIN').read_bytes() if (folder/'NOTICE.BIN').exists() else b'';w=struct.unpack('<72H',report) if len(report)==144 else ()
        wire=(folder/'serial.bin').read_bytes();screen=(folder/'SCREEN.BIN').read_bytes()[::2];error=5 if mode[1]=='A' else 12
        enabled=int(bool(args.sound));first_enabled=enabled if mode!='1D' else 0
        checks=result['checks'];checks.update(report_present=bool(w),PRM_sound_policy=bool(w) and (w[62],w[69])==(first_enabled,enabled),
            sound_while_faulting=bool(w) and (w[63],w[64])==(first_enabled,3*first_enabled if mode.startswith('2') else 0),sound_after_recovery=bool(w) and w[65:69]==((1,3,0,0) if args.quarantine=='speaker' else (0,0,0,0)),second_normal_popup_sound=bool(w) and w[70]==enabled,outer_error=head[:4]==(0x524e,1,1,1) and head[6]==error,
            parent_JFT=raw[14:34]==raw[34:54],parent_file_owners=raw[54:470]==raw[470:886],
            parent_resources=owners[2]==0 and raw[-size*2:-size]==raw[-size:],parent_lease_retired=owners[7]==0 and owners[8]==owners[9] and owners[8]>=3,
            first_resources_and_serial=bool(w) and w[14:16]==(1,65535) and w[17]==w[27]==1,
            allocation_balance=bool(w) and w[59]==w[60],
            popup_seen=bool(w) and w[11]==int(mode!='1D'),first_result=bool(w) and w[4]==error,
            recovery_VM=bool(w) and w[18:20]==(0,2) and w[20] in (0,1,2) and w[21:23]==(0,1) and w[24:26]==(1,0) and w[61]==0,
            queued_payload=bool(w) and w[12]==(0 if mode=='1D' else 508),
            continued_serial=wire.count(b'Synth42\r')==1 and b'ready' in wire and b'BAD' not in wire,
            queued_text_exact=PAYLOAD in screen,recovery_marker=b'RECOVERY OK' in screen,actual_child=(folder/'SUCCESS.OK').exists() and (folder/'SUCCESS.OK').read_bytes()==b'OK',
            retained_stream_output=(folder/'WRITE.BIN').exists() and (folder/'WRITE.BIN').read_bytes()==b'FIRSTSECOND')
        if args.notice_help:
            h=help_probe
            checks.update(help_open_before_fault=h['stage']==5 and h['seed_failures']==0 and h['help_seen']==1 and h['held_ticks']>=90,
                help_capture=b'PCPlus // CONTEXT HELP' in help_frames[4000:8000:2],
                speaker_quiet_at_fault=bool(w) and w[64]==0)
            # The ordinary speaker completes its bounded duration while help
            # remains open. This replaces the pre-help immediate-fault sample.
            checks['sound_while_faulting']=bool(w) and w[64]==0
            checks['popup_seen']=bool(w) and w[11]==0 and b'Program not found.' in help_frames[:4000:2]
        if args.quarantine:
            guard=args.quarantine=='guard';foreign_speaker=args.quarantine=='speaker';count=1 if guard or foreign_speaker else 2
            checks.update(quarantine_held=bool(w) and w[37:44]==(3 if foreign_speaker else count,1,1,6,1,int(guard or foreign_speaker),0 if foreign_speaker else 2 if guard else 1),original_cause=bool(w) and w[44]==w[58]==9,
                retry_blocked=bool(w) and w[45:50]==(10,1,1,10,10),retry_succeeded=bool(w) and w[50:56]==(0,0,1,1,1,0),
                quarantine_storage_released=bool(w) and w[56:58]==(count,count),recovery_attempts=bool(w) and w[26]==3)
        else:checks['first_cleanup_and_view']=bool(w) and w[9:11]==(1,1)
        mouse=None
        if args.mouse:
            from mouse_sound_checks import verify
            mouse_checks,mouse=verify(raw,parent.parent/'terminal.map',size,folder);checks.update(mouse_checks)
            if args.input:
                c=child_input
                checks.update(child_notice_input_observed=c['seen']==c['exit_seen']==1 and c['event']==0,child_scales=(c['scale_x'],c['scale_y'])==(8,4),child_callback_retired_before_DOS_exit=(c['exit_mask'],c['exit_off'],c['exit_seg'])==(mouse['suspended_mask'],mouse['suspended_off'],mouse['suspended_seg']))
        result.update(help=help_probe,child_input=child_input,mouse=mouse,passed=all(checks.values()),notice_words=w,passive_header=head,owner_words=owners,compared_parent_bytes=size)
        (folder/'result.json').write_text(json.dumps(result,indent=2)+'\n');results.append(result)
        print(name,'FINAL PASS' if result['passed'] else 'FINAL FAIL '+','.join(k for k,v in checks.items() if not v),flush=True)
    for name,digest in sources.items():assert sha(ROOT/name)==digest,name
    report=dict(passed=all(r['passed'] for r in results),cases=results,sources=sources,parent_sha256=sha(parent),child_sha256=sha(child),observer_sha256=sha(out/'RENDER.COM'),quarantine=args.quarantine,port=port,sound=args.sound,mouse=args.mouse,native_notice_input=args.input,notice_help=args.notice_help,
        scope='Actual PRM-configured PROGRAM sound and DOS attached terminal, popup error, checkpoint recovery, retained streams, 508 queued printable UART bytes restored through the actual renderer and real subsequent DOS child. Mixer muted; physical audio/modem and complete PROGRAM shared UI policy remain unverified.')
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
