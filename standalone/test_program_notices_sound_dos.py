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
    parser.add_argument('--sound',type=int,choices=[0,1,65535],default=1)
    parser.add_argument('--quarantine',choices=['guard','foreign','speaker']);parser.add_argument('--port',type=int,choices=[1,2],default=1)
    args=parser.parse_args();assert re.fullmatch(r'[A-Za-z0-9_-]+',args.label)
    out=ROOT/'build/program-notices-sound'/args.label;out.mkdir(parents=True,exist_ok=False)
    parent=ROOT/'build/terminal-notice-sound/TERMINAL.EXE';child=ROOT/'build/aspect-notice-sound-fault/ASPECT.EXE';sources={}
    for product in (parent,child):
        manifest=json.loads((product.parent/'manifest.json').read_text());assert manifest['binary_sha256']==sha(product)
        for name,digest in manifest['sources'].items():
            assert name not in sources or sources[name]==digest,name
            sources[name]=digest
    for name in ('standalone/test_program_notices_sound_dos.py','standalone/test_program_notices_dos.py','standalone/test_aspect_parent_process_dos.py','standalone/test_aspect_renderer_dos.py','standalone/test_connection_dos.py','standalone/test_terminal.py','standalone/directory_fixtures.py','standalone/modem_fixtures.py','standalone/terminal_config_fixtures.py','standalone/directory_test_support.py','standalone/notice_success_child.asm','src/aspect/compiler.py'):sources[name]=sha(ROOT/name)
    for name,digest in sources.items():
        assert sha(ROOT/name)==digest,name
        target=out/'sources'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
    render.OUT=out;observer,size=prepare_observer(out,render.map_offsets(parent.parent/'terminal.map'),parent.parent/'terminal.map',sound_probe=True)
    harness=render.adapter(cpu='8086');results=[];first,second=scripts();port=args.port
    for mode in args.mode or ['1D','2D','3D','2A','2F']:
        assert not args.quarantine or mode in ('2D','2A','2F')
        name=mode;folder=out/name;folder.mkdir();shutil.copyfile(parent,folder/'TERMINAL.EXE');shutil.copyfile(child,folder/'ASPECT.EXE');harness.BINARY=folder/'TERMINAL.EXE'
        subprocess.run(['nasm','-fbin',str(out/'sources/standalone/notice_success_child.asm'),'-o',str(folder/'SUCCESS.COM')],check=True)
        files={'LOGIN.ASP':first.encode(),'LOGIN.ASX':compile_source(first),'RECOVER.ASP':second.encode(),'RECOVER.ASX':compile_source(second),'RENDER.COM':observer,'SUCCESS.COM':(folder/'SUCCESS.COM').read_bytes()}
        for i in range(5):files[f'SLOT{i}.BIN']=b'SEED0'
        payload=bytearray(directory(port=port));payload[302:311]=b'LOGIN\0\0\0\0';payload[325:336]=b'Synth42\0\0\0\0'
        harness.RENDER_POST=PAYLOAD;harness.RENDER_TRIGGER=b'PAYLOAD!'
        request=mode+str(port)+'N'+({'guard':'G','foreign':'W','speaker':'S'}.get(args.quarantine,'N'))+'P'
        settings=bytearray(prm(port=port,soft=0,hard=1));struct.pack_into('<H',settings,0x1bc,args.sound)
        result=harness.run(name,'success','p12000 space p700 r e a d y p700 a-x',directory=bytes(payload),prm=bytes(settings),com=port,
            arguments='@D:\\TEST.PRM /E:D:\\TEST.DIR /N:1 /A:NETWORK',files=files,environment={'PCPNOTICE':request},
            banner=b'\x1b[2J\x1b[HFIRST BYTE SAFE\x1b[6n\x1b[0cLOGIN:',working_drive='d',observer='RENDER')
        raw=(folder/'RENDER.BIN').read_bytes();head=struct.unpack_from('<7H',raw);owners=struct.unpack_from('<13H',raw,len(raw)-26-32*70-size*2)
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
        if args.quarantine:
            guard=args.quarantine=='guard';foreign_speaker=args.quarantine=='speaker';count=1 if guard or foreign_speaker else 2
            checks.update(quarantine_held=bool(w) and w[37:44]==(3 if foreign_speaker else count,1,1,6,1,int(guard or foreign_speaker),0 if foreign_speaker else 2 if guard else 1),original_cause=bool(w) and w[44]==w[58]==9,
                retry_blocked=bool(w) and w[45:50]==(10,1,1,10,10),retry_succeeded=bool(w) and w[50:56]==(0,0,1,1,1,0),
                quarantine_storage_released=bool(w) and w[56:58]==(count,count),recovery_attempts=bool(w) and w[26]==3)
        else:checks['first_cleanup_and_view']=bool(w) and w[9:11]==(1,1)
        result.update(passed=all(checks.values()),notice_words=w,passive_header=head,owner_words=owners,compared_parent_bytes=size)
        (folder/'result.json').write_text(json.dumps(result,indent=2)+'\n');results.append(result)
        print(name,'FINAL PASS' if result['passed'] else 'FINAL FAIL '+','.join(k for k,v in checks.items() if not v),flush=True)
    for name,digest in sources.items():assert sha(ROOT/name)==digest,name
    report=dict(passed=all(r['passed'] for r in results),cases=results,sources=sources,parent_sha256=sha(parent),child_sha256=sha(child),observer_sha256=sha(out/'RENDER.COM'),quarantine=args.quarantine,port=port,sound=args.sound,
        scope='Actual PRM-configured PROGRAM sound and DOS attached terminal, popup error, checkpoint recovery, retained streams, 508 queued printable UART bytes restored through the actual renderer and real subsequent DOS child. Mixer muted; physical audio/modem and complete PROGRAM shared UI policy remain unverified.')
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
