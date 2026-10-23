#!/usr/bin/env python3
"""Ordinary terminal/ASPECT help composition, queued receive and real next EXEC."""
import argparse,json,re,shutil,struct,subprocess,sys
from pathlib import Path
import test_aspect_renderer_dos as render
from test_aspect_parent_process_dos import prepare_observer
from directory_fixtures import directory,prm
from notice_help_probe import instrument,WORDS,BYTES
from notice_input_fault_probe import WORDS as INPUT_WORDS,BYTES as INPUT_BYTES
ROOT=render.ROOT;sys.path.insert(0,str(ROOT/'src/aspect'))
from compiler import compile_source
PAYLOAD=b'Q'*500+b'ENDMARK!'
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--label',required=True);p.add_argument('--port',type=int,choices=[1,2],default=1);p.add_argument('--no-driver',action='store_true');p.add_argument('--bios',choices=['STANDARD','ENHANCED'],default='ENHANCED');p.add_argument('--help-resource',action='store_true');p.add_argument('--resource-case',choices=['normal','missing','bad'],default='normal');a=p.parse_args();assert re.fullmatch(r'[A-Za-z0-9_-]+',a.label)
    out=ROOT/'build/notice-help'/a.label;out.mkdir(parents=True,exist_ok=False)
    parent=ROOT/'build/terminal-mouse-notice-input/TERMINAL.EXE';child=ROOT/'build/aspect-notice-help-parent/ASPECT.EXE';sources={}
    if a.help_resource:child=ROOT/'build/aspect-help-resource-parent/ASPECT.EXE'
    for product in (parent,child):
        m=json.loads((product.parent/'manifest.json').read_text());assert m['binary_sha256']==render.sha(product)
        for n,h in m['sources'].items():
            assert n not in sources or sources[n]==h,n
            sources[n]=h
        for path in [product.parent/'manifest.json',product.parent/('terminal.map' if product==parent else 'ASPECT.map')]:sources[str(path.relative_to(ROOT))]=render.sha(path)
    for name in ['standalone/test_notice_help_dos.py','standalone/notice_help_probe.py','standalone/notice_input_fault_probe.py','standalone/notice_input_parent_probe.py','standalone/notice_input_no_driver_probe.py','standalone/mouse_parent_probe.py','standalone/mouse_sound_checks.py','standalone/test_aspect_parent_process_dos.py','standalone/test_aspect_renderer_dos.py','standalone/test_connection_dos.py','standalone/test_terminal.py','standalone/directory_fixtures.py','standalone/directory_test_support.py','standalone/terminal_config_fixtures.py','standalone/modem_fixtures.py','standalone/notice_success_child.asm','src/aspect/compiler.py']:sources[name]=render.sha(ROOT/name)
    if a.help_resource:
        for path in [ROOT/'standalone/notice_resource_probe.py',child.parent/'LOCHELP.HLP',child.parent/'help-resource.json']:sources[str(path.relative_to(ROOT))]=render.sha(path)
    for name,h in sources.items():
        assert render.sha(ROOT/name)==h,name
        target=out/'sources'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
    render.OUT=out;_,size=prepare_observer(out,render.map_offsets(parent.parent/'terminal.map'),parent.parent/'terminal.map',sound_probe=True,mouse_probe=not a.no_driver)
    if a.no_driver:
        from mouse_parent_probe import compact_collector
        (out/'observer.asm').write_text(compact_collector((out/'observer.asm').read_text()))
    if a.help_resource and a.resource_case!='missing':
        from notice_resource_probe import instrument as resource_probe
        source=resource_probe((out/'observer.asm').read_text(),child.parent/'ASPECT.map',no_driver=a.no_driver,bad=a.resource_case=='bad')
    else:source=instrument((out/'observer.asm').read_text(),child.parent/'ASPECT.map',no_driver=a.no_driver)
    (out/'observer.asm').write_text(source)
    subprocess.run(['nasm','-fbin',str(out/'observer.asm'),'-o',str(out/'RENDER.COM')],check=True)
    assert (out/'RENDER.COM').stat().st_size<=0xff00
    folder=out/'ordinary';folder.mkdir()
    for product in (parent,child):shutil.copyfile(product,folder/product.name)
    subprocess.run(['nasm','-fbin',str(ROOT/'standalone/notice_success_child.asm'),'-o',str(folder/'SUCCESS.COM')],check=True)
    script='proc main\nwaitfor "LOGIN:" 5\nset keys off\nputenv "PATH="\ntransmit "PAYLOAD!"\nrun "ABSENT.COM"\nwaitfor "ENDMARK!" 5\nif waitfor\nelse\ntransmit "BAD"\nexit\nendif\nrun "SUCCESS.COM"\nif failure\ntransmit "BAD"\nexit\nendif\nmessage "AFTER HELP"\ntransmit $D_PWORD\ntransmit "^M"\npause 1\nendproc\n'
    payload=bytearray(directory(port=a.port));payload[302:311]=b'LOGIN\0\0\0\0';payload[325:336]=b'Synth42\0\0\0\0'
    settings=bytearray(prm(port=a.port,soft=0,hard=1));struct.pack_into('<H',settings,0x1bc,1);struct.pack_into('<HH',settings,0x4e4,8,4)
    harness=render.adapter(cpu='8086',timeout_seconds=40);harness.BINARY=folder/'TERMINAL.EXE';harness.RENDER_POST=PAYLOAD;harness.RENDER_TRIGGER=b'PAYLOAD!'
    files={'LOGIN.ASP':script.encode(),'LOGIN.ASX':compile_source(script),'RENDER.COM':(out/'RENDER.COM').read_bytes(),'SUCCESS.COM':(folder/'SUCCESS.COM').read_bytes()}
    if a.help_resource and a.resource_case!='missing':files['LOCHELP.HLP']=(child.parent/'LOCHELP.HLP').read_bytes() if a.resource_case=='normal' else b'bad'
    keys='p16000 space p700 a-z p1500 '+('escape ' if a.no_driver else '')+'r e a d y p700 a-x'
    result=harness.run('ordinary','success',keys,directory=bytes(payload),prm=bytes(settings),com=a.port,
        arguments='@D:\\TEST.PRM /E:D:\\TEST.DIR /N:1 /A:NETWORK /B:'+a.bios,files=files,banner=b'\x1b[2J\x1b[HFIRST BYTE SAFE\x1b[6n\x1b[0cLOGIN:',working_drive='d',observer='RENDER')
    raw=(folder/'RENDER.BIN').read_bytes();resource=None;resource_frames=None
    if a.help_resource and a.resource_case=='normal':
        from notice_resource_probe import WORDS as RESOURCE_WORDS,BYTES as RESOURCE_BYTES
        at=len(raw)-RESOURCE_BYTES;resource=dict(zip(RESOURCE_WORDS,struct.unpack_from('<'+str(len(RESOURCE_WORDS))+'H',raw,at)));resource_frames=raw[at+len(RESOURCE_WORDS)*2:];raw=raw[:at]
    start=len(raw)-BYTES;w=dict(zip(WORDS,struct.unpack_from('<'+str(len(WORDS))+'H',raw,start)))
    frames=raw[start+len(WORDS)*2:];raw=raw[:start]
    if a.no_driver:
        from notice_input_no_driver_probe import WORDS as input_words,BYTES as input_bytes
    else:input_words,input_bytes=INPUT_WORDS,INPUT_BYTES
    c=dict(zip(input_words,struct.unpack_from('<'+str(len(input_words))+'H',raw,len(raw)-input_bytes)));raw=raw[:-input_bytes]
    head=struct.unpack_from('<7H',raw);owners=struct.unpack_from('<13H',raw,len(raw)-26-32*70-size*2)
    from mouse_sound_checks import verify
    mouse_checks,mouse=verify(raw,parent.parent/'terminal.map',size,folder) if not a.no_driver else ({},None)
    wire=(folder/'serial.bin').read_bytes();screen=(folder/'SCREEN.BIN').read_bytes()[::2]
    result['checks'].update(mouse_checks);result['checks'].update(ordinary_child=head[:4]==(0x524e,1,1,1) and head[6]==0,
        help_lifetime=w['stage']==4 and w['seed_failures']==0 and w['help_seen']==w['serial_seen']==1 and w['held_ticks']>=90,
        exact_notice_restore=w['frame_equal']==w['cursor_equal']==1,
        captured_help=b'PCPlus // CONTEXT HELP' in frames[4000:8000:2] and b'EXTERNAL PROGRAM / ERROR NOTICE' in frames[4000:8000:2],
        captured_serial_topic=b'SERIAL SESSION / LOCAL INPUT' in frames[8000:12000:2],
        help_key_not_notice_key=(c['notice_status'],c['notice_cause'],c['notice_key'],c['notice_service'])==(1,1,13,0),
        parent_resources=owners[2]==0 and raw[-size*2:-size]==raw[-size:],parent_lease=owners[7]==0 and owners[8]==owners[9] and owners[8]>=2,
        parent_JFT=raw[14:34]==raw[34:54],parent_files=raw[54:470]==raw[470:886],
        queued_text=PAYLOAD in screen,continued_session=b'AFTER HELP' in screen and wire.count(b'Synth42\r')==1 and b'ready' in wire and b'BAD' not in wire,
        real_next_EXEC=(folder/'SUCCESS.OK').exists() and (folder/'SUCCESS.OK').read_bytes()==b'OK')
    if a.help_resource and a.resource_case=='normal':
        result['checks'].update(resource_search=all(v==1 for v in resource.values()),resource_match_capture=b'Receive files' in resource_frames[:4000:2] and b'XMODEM' in resource_frames[:4000:2],resource_next_capture=b'Send files' in resource_frames[4000:8000:2])
    if a.help_resource and a.resource_case=='bad':
        result['checks']['help_lifetime']=w['stage']==4 and w['seed_failures']==0 and w['help_seen']==1 and w['held_ticks']>=90
        result['checks']['captured_help']=b'HELP RESOURCE ERROR' in frames[4000:8000:2]
        result['checks']['captured_serial_topic']=w['serial_seen']==0
    result['checks']['BIOS_mode']=c['bios']==(16 if a.bios=='ENHANCED' else 0)
    if a.no_driver:
        result['checks'].update(INT33_absent_at_exit=c['exit_vector_zero']==1,INT33_restored=(c['old_off'],c['old_seg'])==(c['after_off'],c['after_seg']) and bool(c['old_off'] or c['old_seg']))
    else:result['checks']['callback_retired']=(c['exit_mask'],c['exit_off'],c['exit_seg'])==(mouse['suspended_mask'],mouse['suspended_off'],mouse['suspended_seg'])
    assert all(render.sha(ROOT/n)==h for n,h in sources.items())
    result.update(passed=all(result['checks'].values()),help=w,resource=resource,help_resource=a.help_resource,resource_case=a.resource_case,child_input=c,sources=sources,parent_sha256=render.sha(parent),child_sha256=render.sha(child),observer_sha256=render.sha(out/'RENDER.COM'),port=a.port,no_driver=a.no_driver,bios=a.bios,
        scope=__doc__+' Owned timer seeds BIOS Alt-Z/navigation/Escape/Enter after callback/PSP admission; holds help90ticks beyond74tick notice timeout, compares exact4000-byte popup/cursor restoration and actual help captures. Direct authored child view replaces native external helper; no original UI/search parity, arbitrary faults or physical hardware acceptance.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('FINAL',result['passed'],w,c,[k for k,v in result['checks'].items() if not v]);return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
