#!/usr/bin/env python3
"""Real KEY kind2 -> PROGRAM safe point -> atomic returned settings/registers."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import socket
import struct
import subprocess
from check_setup_model import image
from test_terminal import SAMPLER
from test_directory_key_bindings_dos import actions
from modem_fixtures import fixture as modem_fixture
import test_connection_dos as connection

ROOT=Path(__file__).resolve().parents[1]
FIELDS=[('_terminal_register_owner',1734),('terminal_baseline_storage',1272),('terminal_configuration_values',44),
        ('terminal_modem_settings',368),('_terminal_transfer_preferences',66),('terminal_keymap',948),
        ('terminal_translation_table',256),('_terminal_sound_enabled',2),('_terminal_hook_completed_status',2),
        ('terminal_translation_mode',2),('terminal_translation_enabled',2),('uart_rx_mask',2),('csi_terminal_id',2),
        ('uart_previous_irq_offset',2),('uart_previous_irq_segment',2)]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--mode',type=int,choices=range(13),default=0);parser.add_argument('--port',type=int,choices=[1,2],default=1)
    parser.add_argument('--online',action='store_true')
    parser.add_argument('--irq',type=int,choices=[3,4,5,7])
    parser.add_argument('--lookup-case',choices=['exact-before-pcplus','pcplus-file','pcplus-stem','path-file','path-stem','com-priority','batch-collision','long-pcplus'])
    parser.add_argument('--terminal',type=Path,default=ROOT/'build/terminal-directory-keys-process-bank-session-capture-projection-bound-registers-controls-return-execute-modem-input-apply/TERMINAL.EXE')
    args=parser.parse_args();out=args.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    binary=args.terminal.resolve();base=binary.parent
    assert binary.name=='TERMINAL.EXE'
    manifest=json.loads((base/'manifest.json').read_text());assert manifest['experimental_hook_apply']
    assert sha(base/'TERMINAL.EXE')==manifest['binary_sha256']
    symbols={name:(int(seg,16),int(off,16))for seg,off,name in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',(base/'terminal.map').read_text(),re.M|re.I)}
    (out/'parent_layout.h').write_text('static const struct {unsigned segment,offset,bytes;} parent_spans[]={\n'+
        ''.join('{%d,%d,%d},\n'%(*symbols[name],size)for name,size in FIELDS)+'};\n')
    subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192',*(['-dHOOK_CUSTOM_IRQ']if args.irq is not None else[]),*(['-dHOOK_LOOKUP_BATCH']if args.lookup_case=='batch-collision'else[]),'-i='+str(out),
                    '-fm=APPLYCH.map','-fe=APPLYCH.EXE',str(ROOT/'standalone/hook_apply_child.c'),str(base/'hook_exchange.obj')],cwd=out,check=True)
    shutil.copyfile(base/'TERMINAL.EXE',out/'TERMINAL.EXE')
    raw=bytearray(image());struct.pack_into('<HH',raw,0x4e4,8,4);struct.pack_into('<H',raw,0x194,6)
    if args.online:raw[10:0x174]=modem_fixture(timeout=5)[10:0x174]
    struct.pack_into('<H',raw,0,args.port-1);struct.pack_into('<H',raw,2,6)
    if args.irq is not None:struct.pack_into('<H',raw,0x184+(args.port-1)*2,args.irq)
    struct.pack_into('<HH',raw,0x198,0,0);(out/'TEST.PRM').write_bytes(raw)
    helper=(out/'APPLYCH.EXE').read_bytes();launch_name=b'APPLYCH.EXE';launch_files={'APPLYCH.EXE':helper};launch_env={}
    if args.lookup_case:
        from hook_lookup_fixtures import fixture as lookup_fixture
        assert manifest.get('experimental_hook_lookup')
        launch_name,launch_files,launch_env=lookup_fixture(args.lookup_case,helper)
        (out/'BUILD').mkdir();shutil.move(out/'APPLYCH.EXE',out/'BUILD/APPLYCH.EXE')
        for name,data in launch_files.items():
            target=out/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    environment_lines='\n'.join('set '+key+'='+value for key,value in launch_env.items())
    (out/'MODE.BIN').write_bytes(struct.pack('<H',args.mode));(out/'ACTIONS.KEY').write_bytes(actions(launch_name,2))
    if args.mode==4:(out/'PCPLUS.XLT').write_bytes(bytes(range(256)))
    for port in [1,2]:
        sampler=SAMPLER
        for offset in [0,1,3,4]:sampler=sampler.replace(hex(0x3f8+offset),hex((0x3f8 if port==1 else 0x2f8)+offset))
        if port==2:sampler=sampler.replace('BEFORE.BIN','BEFORE2.BIN').replace('AFTER.BIN','AFTER2.BIN').replace('SCREEN.BIN','SCREEN2.BIN')
        (out/f'sample{port}.asm').write_text(sampler)
        subprocess.run(['nasm','-fbin',str(out/f'sample{port}.asm'),'-o',str(out/f'SNAP{port}.COM')],check=True)
    serial='serial1=dummy\nserial2=dummy'
    if args.mode==7:
        ports=[]
        for _ in range(2):
            with socket.socket() as reserve:
                reserve.bind(('127.0.0.1',0));ports.append(reserve.getsockname()[1])
        serial='\n'.join(f'serial{i+1}=nullmodem port:{port} transparent:1 nonlocal:0 rxdelay:200 txdelay:1'for i,port in enumerate(ports))
    (out/'dosbox.conf').write_text(fr'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
cycles=fixed 6000
[serial]
{serial}
[mixer]
nosound=true
[autoexec]
@echo off
mount d "{out}"
d:
set PCPLUS=
{environment_lines}
SNAP1 B
SNAP2 B
ADDKEY p700 a-1 p700 space p400 a-1 p700 space p400 a-1 p700 space p500 a-x
TERMINAL @TEST.PRM /T:ACTIONS.KEY
if errorlevel 1 goto fail
echo PASS>PASS.TXT
goto done
:fail
echo FAIL>FAIL.TXT
:done
SNAP1 S
SNAP1 A
SNAP2 A
exit
''')
    peer_result=None
    if args.online:
        assert args.mode in [0,1,2,3,5,6,9,10]
        connection.BINARY=out/'TERMINAL.EXE'
        files={name:(out/name).read_bytes()for name in ['ACTIONS.KEY','MODE.BIN']};files.update(launch_files)
        label='hookapply-'+out.parent.name+'-'+out.name
        peer_result=connection.run(label,'success','p2000 a-1 p1000 a-1 p1000 a-1 p1000 o b s e r v e enter p800 r e a d y p700 a-x',
            prm=bytes(raw),com=args.port,working_drive='d',files=files,cpu='8086',environment=launch_env,
            arguments='@D:\\TEST.PRM /D:CaseTest:23 /T:D:\\ACTIONS.KEY',
            online_triggers=[(b'observe\r',b'\x1b[5n')],irq=args.irq)
        folder=ROOT/'build/connection-dos'/label
        for artifact in folder.iterdir():
            if artifact.is_file():shutil.copyfile(artifact,out/artifact.name)
        assert peer_result['passed'],peer_result
        wire=(out/'serial.bin').read_bytes();assert wire.index(b'observe\r')<wire.rindex(b'\x1b[0n')
        dos_pass=True
    else:
        with (out/'dosbox.log').open('w') as log:
            run=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],cwd=out,
                               env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=30)
        dos_pass=run.returncode==0
    assert dos_pass and (out/'PASS.TXT').exists() and not (out/'FAIL.TXT').exists(),args.mode
    assert (out/'COUNT.BIN').read_bytes()==struct.pack('<H',3)
    for a,b in ([('BEFORE.BIN','AFTER.BIN')] if args.online else [('BEFORE.BIN','AFTER.BIN'),('BEFORE2.BIN','AFTER2.BIN')]):assert (out/a).read_bytes()==(out/b).read_bytes(),(args.mode,a)
    assert (out/'TEST.PRM').read_bytes()==raw
    before=[(out/f'B{i}.BIN').read_bytes()for i in range(3)];after=[(out/f'A{i}.BIN').read_bytes()for i in range(3)]
    snapshots=[]
    for index in range(3):
        data=(out/f'S{index}.BIN').read_bytes();assert len(data)==sum(size for _,size in FIELDS)
        offset=0;fields={}
        for name,size in FIELDS:fields[name]=data[offset:offset+size];offset+=size
        snapshots.append(fields)
    wanted_status={1:107,2:105,3:106,8:408,9:107,10:305}.get(args.mode,0)
    observed=struct.unpack('<H',snapshots[1]['_terminal_hook_completed_status'])[0]
    assert observed==wanted_status,(args.mode,'completed',observed,wanted_status)
    committed=wanted_status==0
    assert before[1]==(after[0] if committed else before[0]),(args.mode,'whole returned frame')
    assert before[2]==after[1]==before[1]
    for i in [1,2]:
        owner=snapshots[i]['_terminal_register_owner'];bank=before[i][:830]
        assert owner[904:]==bank and struct.unpack_from('<H',owner)[0]==0
        epoch=struct.unpack_from('<H',owner,4)[0];assert epoch==(i if committed else i-1),(args.mode,epoch)
        baseline=snapshots[i]['terminal_baseline_storage']
        assert baseline[8:]==(before[i][830:] if committed or i==2 else raw)
        assert struct.unpack_from('<H',baseline,4)[0]==(3 if committed or i==2 else 1)
    for i in range(3):
        hardware=struct.unpack('<17H' if args.irq is not None else '<13H',(out/f'H{i}.BIN').read_bytes());p=before[i][830:]
        selected=struct.unpack_from('<H',p)[0];baud=struct.unpack_from('<H',p,2)[0]
        parity,stop,bits=struct.unpack_from('<3H',p,4)
        line=([0,8,0x18,0x28,0x38][parity])|(2 if bits==7 else 3)|(0 if stop==1 else 4)
        assert hardware[selected*4]==[384,96,48,24,12,6,3,2,1][baud],(args.mode,i,'divisor',hardware)
        assert hardware[selected*4+1]==line and hardware[selected*4+3]==0 and not hardware[selected*4+2]&2
        irq=struct.unpack_from('<H',p,0x184+selected*2)[0];assert hardware[8]&(1<<irq)
        vector_at={4:9,3:11,5:13,7:15}[irq]
        vector=hardware[vector_at:vector_at+2]
        assert vector==tuple(struct.unpack('<H',snapshots[i][field])[0] for field in ['uart_previous_irq_offset','uart_previous_irq_segment'])
    if not committed:
        for name,_ in FIELDS:
            if name not in ['_terminal_register_owner','_terminal_hook_completed_status']:
                assert snapshots[0][name]==snapshots[1][name],(args.mode,'partial mutation',name)
    else:
        current=snapshots[1]
        assert struct.unpack('<H',current['_terminal_sound_enabled'])[0]==0
        assert struct.unpack_from('<H',current['_terminal_transfer_preferences'])[0]==1
        if args.mode==4:
            assert struct.unpack('<H',current['csi_terminal_id'])[0]==4
            assert struct.unpack('<H',current['terminal_translation_mode'])[0]==1
            assert struct.unpack('<H',current['terminal_translation_enabled'])[0]==1
            assert current['terminal_translation_table']==bytes(range(256))
    sources=dict(manifest['sources'])
    for name in ['standalone/test_hook_apply_dos.py','standalone/hook_apply_child.c','standalone/check_setup_model.py',
                 'standalone/test_terminal.py','standalone/test_directory_key_bindings_dos.py','standalone/test_connection_dos.py']:
        sources[name]=sha(ROOT/name)
    for name,digest in sources.items():assert sha(ROOT/name)==digest,name
    if args.lookup_case:sources['standalone/hook_lookup_fixtures.py']=sha(ROOT/'standalone/hook_lookup_fixtures.py')
    result=dict(passed=True,mode=args.mode,port=args.port,online=args.online,restored_uart_count=1 if args.online else 2,peer=peer_result,committed=committed,status=observed,sources=sources,binary_sha256=manifest['binary_sha256'],
                helper_sha256=hashlib.sha256(helper).hexdigest(),lookup_case=args.lookup_case,lookup_environment=launch_env,launch_name=launch_name.decode('ascii'),
                snapshots=[sha(out/f'S{i}.BIN')for i in range(3)],
                scope='Actual8086 KEY kind2/PROGRAM/UART+mouse handoff, source-built helper and application. Three real helper '
                'invocations observe accepted bank/PRM/resources, including first-child failure retention in rejection cases. Offline checks both UART snapshots; online checks the selected UART. '
                'Optional synthetic modem peer proves post-helper RX/parser/TX; no live BBS or physical hardware acceptance.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS8086',args.mode,args.port,'committed',committed,'status',observed)


if __name__=='__main__':main()
