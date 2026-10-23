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
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--label',required=True);args=parser.parse_args();assert re.fullmatch(r'[A-Za-z0-9_-]+',args.label)
    out=ROOT/'build/program-sound-smoke'/args.label;out.mkdir(parents=True,exist_ok=False)
    parent=ROOT/'build/terminal-notice-sound/TERMINAL.EXE';child=ROOT/'build/aspect-notice-sound-parent/ASPECT.EXE';sources={}
    for product in (parent,child):
        m=json.loads((product.parent/'manifest.json').read_text());assert m['binary_sha256']==sha(product)
        for n,h in m['sources'].items():assert n not in sources or sources[n]==h;sources[n]=h
    for n in ['standalone/test_program_sound_smoke_dos.py','standalone/test_aspect_parent_process_dos.py','standalone/test_aspect_renderer_dos.py','standalone/test_connection_dos.py','standalone/test_terminal.py','standalone/directory_fixtures.py','standalone/modem_fixtures.py','standalone/terminal_config_fixtures.py','standalone/directory_test_support.py','standalone/notice_success_child.asm','src/aspect/compiler.py']:sources[n]=sha(ROOT/n)
    for n,h in sources.items():
        assert sha(ROOT/n)==h;npath=out/'sources'/n;npath.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/n,npath)
    render.OUT=out;observer,size=prepare_observer(out,render.map_offsets(parent.parent/'terminal.map'),parent.parent/'terminal.map',sound_probe=True)
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
        files={'LOGIN.ASP':script.encode(),'LOGIN.ASX':compile_source(script),'SUCCESS.COM':(folder/'SUCCESS.COM').read_bytes(),'RENDER.COM':observer}
        payload=bytearray(directory(port=port));payload[302:311]=b'LOGIN\0\0\0\0';payload[325:336]=b'Synth42\0\0\0\0'
        settings=bytearray(prm(port=port,soft=0,hard=1));struct.pack_into('<H',settings,0x1bc,setting)
        harness.RENDER_POST=render.QUERY;harness.RENDER_TRIGGER=b'Synth42\r'
        result=harness.run(name,'success','p9000 space p700 r e a d y p700 a-x',directory=bytes(payload),prm=bytes(settings),com=port,arguments='@D:\\TEST.PRM /E:D:\\TEST.DIR /N:1 /A:NETWORK',files=files,banner=b'\x1b[2J\x1b[HFIRST BYTE SAFE\x1b[6n\x1b[0cLOGIN:',working_drive='d',observer='RENDER')
        capture=(folder/'RENDER.BIN').read_bytes();audio=struct.unpack('<H',capture[-2:])[0];raw=capture[:-2];head=struct.unpack_from('<7H',raw);owners=struct.unpack_from('<13H',raw,len(raw)-26-32*70-size*2)
        wire=(folder/'serial.bin').read_bytes();screen=(folder/'SCREEN.BIN').read_bytes()[::2]
        checks=result['checks'];checks.update(ordinary_ASPECT_success=head[:4]==(0x524e,1,1,1) and head[6]==0,parent_JFT=raw[14:34]==raw[34:54],parent_file_owners=raw[54:470]==raw[470:886],parent_resources=owners[2]==0 and raw[-size*2:-size]==raw[-size:],parent_lease_retired=owners[7]==0 and owners[8]==owners[9] and owners[8]>=2,
            passive_sound_policy=bool(audio)==bool(setting),real_success_child=(folder/'SUCCESS.OK').exists() and (folder/'SUCCESS.OK').read_bytes()==b'OK',continued_session=b'AFTER SOUND' in screen and b'BAD' not in wire and b'ready' in wire and wire.count(b'Synth42\r')==1)
        result.update(passed=all(checks.values()),speaker_active_timer_samples=audio,sound=setting,port=port,passive_header=head,owner_words=owners,compared_parent_bytes=size)
        (folder/'result.json').write_text(json.dumps(result,indent=2)+'\n');results.append(result)
        print(name,'FINAL PASS' if result['passed'] else 'FINAL FAIL '+','.join(k for k,v in checks.items() if not v),flush=True)
    assert all(sha(ROOT/n)==h for n,h in sources.items())
    report=dict(passed=all(r['passed'] for r in results),cases=results,sources=sources,parent_sha256=sha(parent),child_sha256=sha(child),observer_sha256=sha(out/'RENDER.COM'),scope=__doc__+' No diagnostic ASPECT driver or product patch. Observer reads speaker gate bits during live EXEC; it does not program ports or call product helpers. Mixer muted, so this is not acoustic or physical audio evidence.')
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
