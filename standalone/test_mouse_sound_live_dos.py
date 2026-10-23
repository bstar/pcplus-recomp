#!/usr/bin/env python3
"""Actual Alt-F10 combined editor followed by attached PROGRAM and serial input."""
import argparse,json,re,shutil,struct,subprocess,sys
import test_aspect_renderer_dos as render
from test_aspect_parent_process_dos import prepare_observer
from directory_fixtures import prm
from mouse_sound_checks import verify
ROOT=render.ROOT;sha=render.sha
sys.path.insert(0,str(ROOT/'src/aspect'))
from compiler import compile_source


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--label',required=True)
    a=p.parse_args();assert re.fullmatch(r'[A-Za-z0-9_-]+',a.label)
    out=ROOT/'build/mouse-sound-live'/a.label;out.mkdir(parents=True,exist_ok=False)
    parent=ROOT/'build/terminal-mouse-notice-sound/TERMINAL.EXE'
    child=ROOT/'build/aspect-notice-sound-parent/ASPECT.EXE'
    editor=ROOT/'build/setup-mouse-notice-sound/PRMEDIT.EXE';sources={}
    for product in (parent,child,editor):
        m=json.loads((product.parent/'manifest.json').read_text());assert sha(product)==m['binary_sha256']
        for n,h in m['sources'].items():assert n not in sources or sources[n]==h;sources[n]=h
    support=['standalone/test_mouse_sound_live_dos.py','standalone/test_aspect_parent_process_dos.py',
        'standalone/test_aspect_renderer_dos.py','standalone/test_connection_dos.py','standalone/test_terminal.py',
        'standalone/directory_fixtures.py','standalone/modem_fixtures.py','standalone/terminal_config_fixtures.py',
        'standalone/directory_test_support.py','standalone/notice_success_child.asm',
        'standalone/mouse_parent_probe.py','standalone/mouse_sound_checks.py','src/aspect/compiler.py']
    for n in support:sources[n]=sha(ROOT/n)
    for n,h in sources.items():
        assert sha(ROOT/n)==h;target=out/'sources'/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/n,target)
    render.OUT=out
    observer,size=prepare_observer(out,render.map_offsets(parent.parent/'terminal.map'),parent.parent/'terminal.map',sound_probe=True,mouse_probe=True)
    source=(out/'observer.asm').read_text()
    assert source.count('timer:\n save\n')==source.count('sample_end:')==1
    source=source.replace('sample_end:','audio_ticks: dw 0\nsample_end:').replace('timer:\n save\n','''timer:
 save
 ; Read speaker gate only during the observed ordinary ASPECT child.
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
    (out/'observer.asm').write_text(source)
    subprocess.run(['nasm','-fbin',str(out/'observer.asm'),'-o',str(out/'RENDER.COM')],check=True)
    observer=(out/'RENDER.COM').read_bytes();harness=render.adapter(cpu='8086');rows=[]
    script='proc main\nputenv "PATH="\nrun "ABSENT.COM"\nif success\ntransmit "BAD"\nexit\nendif\nrun "SUCCESS.COM"\nif failure\ntransmit "BAD"\nexit\nendif\ntransmit "AFTERSETUP"\nendproc\n'
    cases=[('enable',0,1,(9,5),'save'),('disable',1,0,(9,5),'save'),
        ('nonzero',0,65535,(999,1),'save'),('discard',1,0,(9,5),'discard'),
        ('invalid',1,65536,(9,5),'invalid')]
    for name,initial,requested,scales,action in cases:
        folder=out/name;folder.mkdir();shutil.copyfile(parent,folder/'TERMINAL.EXE');harness.BINARY=folder/'TERMINAL.EXE'
        subprocess.run(['nasm','-fbin',str(out/'sources/standalone/notice_success_child.asm'),'-o',str(folder/'SUCCESS.COM')],check=True)
        settings=bytearray(prm(port=1,soft=0,hard=1));struct.pack_into('<HH',settings,0x4e4,8,4);struct.pack_into('<H',settings,0x1bc,initial)
        expected=bytearray(settings)
        if action=='save':struct.pack_into('<HH',expected,0x4e4,*scales);struct.pack_into('<H',expected,0x1bc,requested)
        want=requested if action=='save' else initial;want_scales=scales if action=='save' else (8,4)
        edit='pgdown '+'tab '*12+'home del del del '+' '.join(str(scales[0]))+' tab home del del del '+' '.join(str(scales[1]))+' tab home del '+' '.join(str(requested))
        finish='f10 escape' if action=='save' else 'escape y' if action=='discard' else 'f10 escape y'
        keys='p1800 a-f10 p700 '+' p60 '.join((edit+' '+finish).split())+' p500 space p500 a-z p300 a p300 t e s t . a s x enter p5500 a-z p1500 r e a d y p500 a-x'
        assert len('ADDKEY '+keys)<500
        files={'PRMEDIT.EXE':editor.read_bytes(),'ASPECT.EXE':child.read_bytes(),'TEST.ASX':compile_source(script),
            'TEST.ASP':script.encode(),'SUCCESS.COM':(folder/'SUCCESS.COM').read_bytes(),'RENDER.COM':observer}
        harness.RENDER_TRIGGER=b'AFTERSETUP';harness.RENDER_POST=render.QUERY
        result=harness.run(name,'success',keys,prm=bytes(settings),prm_expected=bytes(expected),
            arguments='@TEST.PRM /D:CaseTest:23 /I:3',files=files,working_drive='d',observer='RENDER')
        capture=(folder/'RENDER.BIN').read_bytes();ticks=struct.unpack_from('<H',capture,len(capture)-2)[0];raw=capture[:-2]
        header=struct.unpack_from('<7H',raw);owners=struct.unpack_from('<13H',raw,len(raw)-26-32*70-size*2)
        wire=(folder/'serial.bin').read_bytes();checks=result['checks']
        checks.update(ordinary_ASPECT_success=header[:4]==(0x524e,1,1,1) and header[6]==0,
            passive_sound_after_live_setup=bool(ticks)==bool(want),
            real_DOS_child=(folder/'SUCCESS.OK').exists() and (folder/'SUCCESS.OK').read_bytes()==b'OK',
            continued_session=b'BAD' not in wire and wire.count(b'AFTERSETUP')==1 and b'ready' in wire,
            parent_JFT=raw[14:34]==raw[34:54],parent_file_owners=raw[54:470]==raw[470:886],
            parent_resources=owners[2]==0 and raw[-size*2:-size]==raw[-size:],
            parent_lease_retired=owners[7]==0 and owners[8]==owners[9] and owners[8]>=2,
            no_editor_recovery_files=not (folder/'PRMEDIT.BAK').exists() and not (folder/'PRMEDIT.$$$').exists())
        mouse_checks,mouse=verify(raw,parent.parent/'terminal.map',size,folder,expected_scales=want_scales);checks.update(mouse_checks)
        result.update(passed=all(checks.values()),initial_sound=initial,requested_sound=requested,expected_sound=want,
            expected_mouse_scales=want_scales,speaker_active_timer_samples=ticks,mouse=mouse,passive_header=header,
            owner_words=owners,compared_parent_bytes=size,keys=keys)
        (folder/'BEFORE.PRM').write_bytes(settings);(folder/'EXPECTED.PRM').write_bytes(expected)
        result['artifacts']={x.name:sha(x) for x in folder.iterdir() if x.is_file() and x.name!='result.json'}
        (folder/'result.json').write_text(json.dumps(result,indent=2)+'\n');rows.append(result)
        print(name,'FINAL PASS' if result['passed'] else [k for k,v in checks.items() if not v],flush=True)
    assert all(sha(ROOT/n)==h for n,h in sources.items())
    report=dict(passed=all(r['passed'] for r in rows),cases=rows,sources=sources,
        products={str(x.relative_to(ROOT)):sha(x) for x in (parent,child,editor)},observer_sha256=sha(out/'RENDER.COM'),
        scope=__doc__+' Ordinary matching products, no renamed main or product patches. Exact full PRM comparisons. Passive speaker-gate reads during ASPECT; separate active INT33 callback/menu probe and full driver-state restoration. Synthetic Hayes peer; muted mixer. Physical modem/audio, mouse input inside notices, broader views and full application acceptance remain open.')
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');return 0 if report['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
