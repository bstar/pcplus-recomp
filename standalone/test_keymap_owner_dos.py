#!/usr/bin/env python3
"""Real DOS owner refusal/release via BIOS keys, files and independent UART peer.

The source-owned counting child proves PROGRAM admission, not helper rendering.
No product variables, instruction bytes or modeled ownership callbacks change.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess
import test_connection_dos as lab
from modem_fixtures import fixture
from package_connection_test import terminal_companions

ROOT=Path(__file__).resolve().parents[1]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def keys(text):return ' '.join(text)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--terminal',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--case',action='append',choices=['recording','monitor','redisplay','parser'])
    args=parser.parse_args();parent=args.terminal.resolve();out=args.output.resolve()
    assert parent.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build') and not out.exists()
    manifest=json.loads(parent.with_name('manifest.json').read_text())
    assert manifest['experimental_keymap_editor'] and sha(parent)==manifest['binary_sha256']
    for name,digest in manifest['sources'].items():assert sha(ROOT/name)==digest,name
    companions,companion_sources=terminal_companions(parent,manifest)
    out.mkdir(parents=True);runtime=out/'runtime';runtime.mkdir()
    for leaf,source in {'TERMINAL.EXE':parent,**companions}.items():
        shutil.copyfile(source,runtime/leaf)
    probe=ROOT/'standalone/keymap_launch_probe.asm'
    subprocess.run(['nasm','-fobj',str(probe),'-o',str(out/'probe.obj')],check=True)
    subprocess.run(['wlink','system','dos','option','quiet','option','start=start','name',str(runtime/'PCKEYMAP.EXE'),'file',str(out/'probe.obj')],check=True)
    products={p.name:sha(p) for p in runtime.iterdir()}
    watcher=out/'RVWATCH.COM'
    subprocess.run(['nasm','-fbin',str(ROOT/'standalone/redisplay_watch.asm'),'-o',str(watcher)],check=True)
    settings=bytearray(fixture())
    for at,value in ((0x4e4,8),(0x4e6,4),(0x194,6),(0x1c2,0),(0x1c8,2),(0x1ca,25),(0x4ec,0),(0x1bc,0),(0x1be,0),(0x1e6,0),(0x3e4,7),(0x3e6,11),(0x3e8,113)):
        struct.pack_into('<H',settings,at,value)
    banner=b'\x1b[2J\x1b[HFIRST BYTE SAFE\x1b[6n\x1b[0c'
    raw_monitor=b'MONITOR-OWNED\x00\xff\x1b[6nNO-PARSER'
    results=[];lab.BINARY=runtime/'TERMINAL.EXE'
    for case in args.case or ['recording','monitor','redisplay','parser']:
        label=out.name+'-'+case;drive=ROOT/'build/connection-dos'/label
        assert not drive.exists()
        snapshots=[]
        def released(folder):
            snapshots.append(dict(at='after-owner-before-allowed-entry',launch_exists=(folder/'LAUNCH.LOG').exists(),
                files={p.name:p.stat().st_size for p in folder.glob('*') if p.suffix.upper() in ('.ASP','.TMP','.DMP')}))
        def resumed(folder):
            snapshots.append(dict(at='after-allowed-entry',launch_bytes=(folder/'LAUNCH.LOG').read_bytes().hex() if (folder/'LAUNCH.LOG').exists() else None))
        observer=None;files={'SYN.KBD':bytes(7*948)};triggers=[]
        if case=='recording':
            owned='a-r p300 enter p800 '+keys('recbefore')+' p300 a-f8 p500 '+keys('recafter')+' p500 a-r p500 escape escape p700'
        elif case=='monitor':
            owned='c-\\ p300 y p500 '+keys('monbefore')+' p800 a-f8 p500 '+keys('monafter')+' p500 escape p700'
            triggers.append((b'monbefore',raw_monitor))
        elif case=='redisplay':
            owned='c-pgup p700 home p700 a-f8 p700 escape p700'
            files['RVWATCH.COM']=watcher.read_bytes();observer='RVWATCH'
        else:
            owned=keys('parserbefore')+' p150 a-f8 p100 '+keys('held')+' p1400'
            triggers.append((b'parserbefore',((0,b'\x1b['),(.8,b'7;1HWAIT-DONE\x1b[6n'))))
        sequence='p900 enter p3000 '+owned+' '+keys('released')+' p500 a-f8 p1500 '+keys('ready')+' p600 a-x'
        triggers.append((b'ready',banner))
        r=lab.run(label,'success',sequence,prm=bytes(settings),arguments='@D:\\TEST.PRM /D:CaseTest:23 /K:D:\\SYN.KBD COM1 19200 HARD',
            files=files,cpu='8086',working_drive='d',observer=observer,online_triggers=tuple(triggers),
            online_actions=((b'released',released),(b'ready',resumed)),timeout=40)
        checks=dict(r['checks']);wire=(drive/'serial.bin').read_bytes()
        checks.update(refused_until_owner_released=bool(snapshots and not snapshots[0]['launch_exists']),
            exactly_one_postrelease_child=(drive/'LAUNCH.LOG').is_file() and (drive/'LAUNCH.LOG').read_bytes()==b'K',
            ordinary_input_resumed=b'releasedready' in wire,
            matched_products_unchanged=all(sha(runtime/name)==digest for name,digest in products.items()))
        if case=='recording':
            source=(drive/'PCPLUS.ASP').read_bytes() if (drive/'PCPLUS.ASP').exists() else b''
            recorded=b''.join(bytes.fromhex(x.decode()) for x in re.findall(rb'^transmitraw "([0-9A-F]*)"\r?$',source,re.M))
            checks.update(actual_continuous_recording=recorded==b'recbeforerecafter' and source.endswith(b'endproc\r\n'),
                recording_staging_resolved=not list(drive.glob('LPR*.TMP')) and not list(drive.glob('LPR*.BAK')))
        elif case=='monitor':
            checks.update(actual_raw_monitor=(drive/'PCPLUS.DMP').is_file() and (drive/'PCPLUS.DMP').read_bytes()==raw_monitor,
                no_parser_response_during_monitor=wire.count(b'\x1b[1;16R')==2)
        elif case=='redisplay':
            raw=(drive/'RVIEW.BIN').read_bytes();magic,count,ticks=struct.unpack_from('<3H',raw)
            footers=[raw[6+i*320+240:6+(i+1)*320] for i in range(count)]
            checks['actual_redisplay_observed']=magic==0x4452 and count>0 and ticks>0 and any(b'Frozen history' in footer for footer in footers)
        else:
            checks['split_parser_completed']=b'\x1b[7;10R' in wire and b'held' in wire
        row=dict(case=case,passed=all(checks.values()),checks=checks,snapshots=snapshots,raw_result=str((drive/'result.json').relative_to(ROOT)))
        (out/(case+'.json')).write_text(json.dumps(row,indent=2)+'\n');results.append(row)
        assert row['passed'],(case,[name for name,value in checks.items() if not value])
        print('PASS real DOS mapper owner:',case,flush=True)
    names=['standalone/test_keymap_owner_dos.py','standalone/keymap_launch_probe.asm','standalone/redisplay_watch.asm','standalone/test_connection_dos.py','standalone/modem_fixtures.py','standalone/package_connection_test.py']
    result=dict(passed=True,parent_sha256=sha(parent),counting_child_sha256=sha(runtime/'PCKEYMAP.EXE'),cases=results,cpu='8086',original_inputs=[],
        sources={**companion_sources,**{name:sha(ROOT/name) for name in names}},products=products,scope=__doc__+' Synthetic serial modem and KBD; no physical or actual mapper rendering acceptance.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':main()
