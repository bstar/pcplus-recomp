#!/usr/bin/env python3
"""8086 DOS session engine: far callback ABI, independent wire scripts, real files."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
from check_zmodem import h,meta,offer,payload
from check_zmodem_wire import packet
from zmodem_window_vectors import vectors
from check_zmodem_names import alias

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/zmodem-dos'
def main():
    OUT.mkdir(parents=True,exist_ok=True);lock=(OUT/'.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    src=ROOT/'src/transfer';sources=[src/n for n in ('zmodem.c','zmodem_wire.c','zmodem_name.c','batch_header.c','download_file.c','download_fs.c')]+[ROOT/'standalone/zmodem_host.c']
    subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-s','-w4','-we','-k8192','-i='+str(src),'-fe=SESSION.EXE',*map(str,sources)],cwd=OUT,check=True)
    isolated=OUT/'source-only';isolated.mkdir(exist_ok=True)
    headers=[src/n for n in ('zmodem.h','zmodem_wire.h','zmodem_name.h','batch_header.h','download_file.h','download_fs.h')]
    for p in sources+headers:shutil.copy2(p,isolated/p.name)
    subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-s','-w4','-we','-k8192','-i=.','-fe=SESSION.EXE',*[p.name for p in sources]],cwd=isolated,check=True)
    assert (isolated/'SESSION.EXE').read_bytes()==(OUT/'SESSION.EXE').read_bytes()
    run=OUT/'run'
    if run.exists():shutil.rmtree(run)
    run.mkdir();shutil.copy2(OUT/'SESSION.EXE',run/'SESSION.EXE')
    cases=[];commands=[];body=bytes(range(256))*257+b'\x1a\0\xff@\r'
    def case(label,sending,wire,expected_files,expected_status=0,expected_wire=None,source_files=None,preexisting=None,fault=0,checks=None):
        name=f'T{len(cases):03}';path=run/name;path.mkdir()
        (path/'IN.BIN').write_bytes(b''.join(struct.pack('<H',v) for v in wire))
        for filename,data in (preexisting or {}).items():(path/filename).write_bytes(data)
        for filename,data in (source_files or {}).items():(path/filename).write_bytes(data)
        (path/'LIST.TXT').write_text(''.join(n+'\n' for n in (source_files or {})))
        commands.extend([f'cd \\{name}',f'..\\SESSION {"S" if sending else "R"} {fault} >RESULT.TXT'])
        cases.append(dict(label=label,path=path,status=expected_status,files=expected_files,wire=expected_wire,source=source_files or {},preexisting=preexisting or {},extra=checks or {}))
    for fmt in (65,67):
        for n in (0,1,1023,1024,1025,len(body)):
            data=body[:n];wire=offer('TEST.BIN',n,fmt);expected=h(1,0x23002000)+h(9)
            for off in range(0,n,1024):
                wire+=payload(data[off:off+1024],off,fmt);expected+=h(3,min(off+1024,n))
            wire+=h(11,n,fmt)+h(8)+b'OO';expected+=h(1,0x23002000)+h(8)
            case(f'receive-{fmt}-{n}',False,wire,{'TEST.BIN':data},expected_wire=expected)
            rx=h(1,0x22000000 if fmt==67 else 0x02000000)+h(9)
            tx=h(0)+h(4,0x01000000,fmt)+packet(meta('TEST.BIN',n).ljust(128,b'\0'),fmt,107,0)
            for off in range(0,n,1024):rx+=h(3,min(off+1024,n));tx+=payload(data[off:off+1024],off,fmt)
            rx+=h(1,0x22000000 if fmt==67 else 0x02000000)+h(8);tx+=h(11,n,fmt)+h(8)+b'OO'
            case(f'send-{fmt}-{n}',True,rx,{},expected_wire=tx,source_files={'TEST.BIN':data},checks={'closes':1,'uncertain':0})
    for fmt in (65,67):
        name='PCPLUS PROBE 01 (1991).ZIP';local=alias(name.encode()).decode()
        wire=offer(name,6,fmt)+payload(b'ABC',0,fmt)+offer(name,6,fmt)+payload(b'DEF',3,fmt)+h(11,6,fmt)+h(8)+b'OO'
        case(f'long-name-retry-{fmt}',False,wire,{local:b'ABCDEF'})
    name='PCPLUS PROBE 01 (1991).ZIP';local=alias(name.encode()).decode()
    case('long-name-existing-alias-skipped',False,offer(name,3)+h(8)+b'OO',{},preexisting={local:b'ORIGINAL'},expected_wire=h(1,0x23002000)+h(5)+h(8))
    a='Game 9P4Ppbwljq4gg3.ZIP';b='Game o6dYr6fHK42eTT.ZIP'
    case('long-active-alias-collision',False,offer(a,6)+payload(b'ABC')+offer(b,6),{},expected_status=6)
    case('long-committed-alias-collision',False,offer(a,3)+payload(b'ABC')+h(11,3)+offer(b,3)+h(8)+b'OO',{'4F09E7D3.ZIP':b'ABC'},expected_wire=h(1,0x23002000)+h(9)+h(3,3)+h(1,0x23002000)+h(5)+h(8))
    long='A'*251+'.ZIP';local=alias(long.encode()).decode()
    case('wire-name-255',False,offer(long,3)+payload(b'ABC')+h(11,3)+h(8)+b'OO',{local:b'ABC'})
    case('wire-name-256-rejected',False,offer('A'*252+'.ZIP',3),{},expected_status=6)
    for end in (104,105,106,107):
        wire=offer('TEST.BIN',999)+h(10,0,67)+packet(b'ABC',67,end,0)
        wire+=(h(10,3,67) if end in (104,107) else b'')+packet(b'DEF',67,107,0)+h(11,6)+h(8)+b'OO'
        case(f'receive-ending-estimate-{end}',False,wire,{'TEST.BIN':b'ABCDEF'})
    bad=bytearray(packet(b'BAD',67,107,0));bad[0]^=1
    wire=offer('TEST.BIN',0)+payload(b'ABC')+offer('TEST.BIN',0)+h(10,3,67)+bad+payload(b'DEF',3)+h(11,6)+h(8)+b'OO'
    case('CRC-duplicate-offer-zero-size-estimate',False,wire,{'TEST.BIN':b'ABCDEF'})
    for offset in (0,3,6):
        rx=h(1,0x22000000)+h(9,offset)+(h(3,6) if offset<6 else b'')+h(1,0x22000000)+h(8)
        tx=h(0)+h(4,0x01000000,67)+packet(meta('TEST.BIN',6).ljust(128,b'\0'),67,107,0)
        if offset<6:tx+=payload(b'ABCDEF'[offset:],offset)
        tx+=h(11,6,67)+h(8)+b'OO'
        case(f'send-resume-{offset}',True,rx,{},source_files={'TEST.BIN':b'ABCDEF'},expected_wire=tx)
    case('cancel-owned-stage',False,offer('TEST.BIN',3)+payload(b'ABC')+b'\x18'*5,{},expected_status=5)
    case('lost-final-OO',False,offer('TEST.BIN',3)+payload(b'ABC')+h(11,3)+h(8),{'TEST.BIN':b'ABC'},expected_status=8)
    case('existing-target-skipped',False,offer('TEST.BIN',3)+h(8)+b'OO',{},preexisting={'TEST.BIN':b'ORIGINAL'},expected_wire=h(1,0x23002000)+h(5)+h(8))
    # An existing foreign stage is a conflict, not an owned file to remove.
    case('foreign-stage-preserved',False,offer('TEST.BIN',3)+h(8)+b'OO',{},preexisting={'PCZRX.$$$':b'FOREIGN'},expected_status=7)
    case('write-failure',False,offer('TEST.BIN',3)+payload(b'ABC'),{},fault=4,expected_status=7,
        expected_wire=h(1,0x23002000)+h(9)+b'\x18'*8+b'\x08'*10)
    case('commit-failure-no-acknowledgement',False,offer('TEST.BIN',3)+payload(b'ABC')+h(11,3),{},fault=5,expected_status=7,
        expected_wire=h(1,0x23002000)+h(9)+h(3,3)+b'\x18'*8+b'\x08'*10)
    for fault in (1,2,3):
        case(f'source-fault-{fault}',True,h(1,0x22000000)+h(9)+h(3,3)+h(1,0x22000000)+h(8),{},source_files={'TEST.BIN':b'ABC'},fault=fault,expected_status=7,
            checks={'closes':1,'uncertain':1 if fault==3 else 0})
    for name,data in (('missing-filename-NUL',b'TEST.BIN'),('missing-metadata-NUL',b'TEST.BIN\x00123'),('unsafe-filename',meta('../X',3))):
        case(name,False,h(4,0,67)+packet(data,67,107,0),{},expected_status=6)
    data=bytes(range(17));rx=h(1,0x23000007)+h(9)
    tx=h(0)+h(4,0x01000000,67)+packet(meta('TEST.BIN',17).ljust(128,b'\0'),67,107,0)
    for off in range(0,17,7):rx+=h(3,min(off+7,17));tx+=payload(data[off:off+7],off)
    rx+=h(1,0x23000007)+h(8);tx+=h(11,17,67)+h(8)+b'OO'
    case('finite-receiver-buffer-seven',True,rx,{},source_files={'TEST.BIN':data},expected_wire=tx)
    for fmt in (65,67):
        for n in (2048,4096,8192):
            data=bytes(i&255 for i in range(n))
            case(f'ZedZap-receive-{fmt}-{n}',False,offer('TEST.BIN',n,fmt)+payload(data,0,fmt)+h(11,n,fmt)+h(8)+b'OO',{'TEST.BIN':data})
        data=bytes(8192)+bytes(range(256))*32
        case(f'ZedZap-continued-ACK-buffer-reuse-{fmt}',False,offer('TEST.BIN',len(data),fmt)+h(10,0,fmt)+packet(data[:8192],fmt,106,0)+packet(data[8192:],fmt,107,0)+h(11,len(data),fmt)+h(8)+b'OO',{'TEST.BIN':data})
    for fmt in (65,67):
        for v in vectors(fmt,include_long=True):
            case(f'window-{fmt}-'+v['label'],True,v['rx'],{},expected_wire=v['tx'],source_files={'TEST.BIN':v['body']},checks={'closes':1,'uncertain':0})
    conf=f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
cycles=max
[mixer]
nosound=true
[autoexec]
@echo off
mount c "{run}"
c:
'''+ '\n'.join(commands)+'\nexit\n'
    (OUT/'dosbox.conf').write_text(conf)
    with (OUT/'dosbox.log').open('w') as log:
        subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(OUT/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=60)
    results=[]
    for item in cases:
        path=item['path'];text=(path/'RESULT.TXT').read_text();fields={k:int(v) for k,v in re.findall(r'(\w+)=(\d+)',text)}
        assert fields['status']==item['status'],(item['label'],text)
        for key,value in item['extra'].items():assert fields[key]==value,(item['label'],key,text)
        for name,data in {**item['preexisting'],**item['source'],**item['files']}.items():assert (path/name).read_bytes()==data,(item['label'],name)
        owned_stage=path/'PCZRX.$$$'
        if 'PCZRX.$$$' not in item['preexisting']:assert not owned_stage.exists(),item['label']
        expected_names={'IN.BIN','OUT.BIN','LIST.TXT','RESULT.TXT',*item['preexisting'],*item['source'],*item['files']}
        assert {p.name for p in path.iterdir()}==expected_names,item['label']
        if item['wire'] is not None:assert (path/'OUT.BIN').read_bytes()==item['wire'],item['label']
        results.append(dict(label=item['label'],passed=True,result=fields,input_sha256=hashlib.sha256((path/'IN.BIN').read_bytes()).hexdigest(),output_sha256=hashlib.sha256((path/'OUT.BIN').read_bytes()).hexdigest()))
    inputs=sources+headers+[Path(__file__).resolve(),ROOT/'standalone/check_zmodem.py',ROOT/'standalone/check_zmodem_names.py',ROOT/'standalone/zmodem_window_vectors.py',ROOT/'standalone/check_zmodem_wire.py',ROOT/'nix/flake.nix',ROOT/'nix/flake.lock',ROOT/'tools/dev']
    result=dict(passed=True,DOS_cases=len(results),cases=results,binary_sha256=hashlib.sha256((OUT/'SESSION.EXE').read_bytes()).hexdigest(),isolated_source_build_byte_identical=True,
        tools={name:shutil.which(name) for name in ('wcl','dosbox-x')},
        sources={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
        scope='Actual source-built 8086 DOS session engine with far callbacks and real checked receive filesystem owner. Wire input is scripted, source callbacks diagnostic stdio; not the terminal source/transport/UI adapter or a live DOS UART/BBS session.')
    (OUT/'checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,DOS_cases=len(results),binary_sha256=result['binary_sha256'])))

if __name__=='__main__':main()
