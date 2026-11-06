#!/usr/bin/env python3
"""Compare serviced Chat effects in DOS8086 with recovered native CPU traces."""
import argparse
import hashlib
import json
import os
import struct
import subprocess
from pathlib import Path
from check_chat_native import execute

ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--banked',action='store_true')
    args=p.parse_args();out=args.output.resolve()
    assert out.is_relative_to(ROOT/'build') and not out.exists()
    out.mkdir();drive=out/'drive';drive.mkdir()
    sources=['src/terminal/chat_owner.c','src/terminal/chat_owner.h','src/chat/bank.asm',
             'standalone/chat_owner_host.c','standalone/test_chat_owner_dos.py',
             'standalone/check_chat_native.py','reconstruction/chat/chat.asm',
             'reconstruction/chat/provenance.json']
    hashes={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in sources}
    subprocess.run(['nasm','-fbin','-DRECON_FLAT',str(ROOT/'reconstruction/chat/chat.asm'),'-o',str(out/'native.bin')],check=True)
    native=(out/'native.bin').read_bytes()
    assert hashlib.sha256(native).hexdigest()==json.loads((ROOT/'reconstruction/chat/provenance.json').read_text())['sha256']
    if args.banked:
        subprocess.run(['nasm','-fobj',str(ROOT/'src/chat/bank.asm'),'-o','bank.obj'],cwd=drive,check=True)
        for source,obj,flags in [('standalone/chat_owner_host.c','host.obj',[]),('src/terminal/chat_owner.c','owner.obj',['-nt=CHAT_CODE','-nc=FARCODE'])]:
            subprocess.run(['wcc','-q','-bt=dos','-0','-ms','-s','-w4','-we','-ecc','-dCHAT_BANK',*flags,'-fo='+obj,str(ROOT/source)],cwd=drive,check=True)
        inputs=['bank.obj','host.obj','owner.obj']
    else:inputs=[str(ROOT/'standalone/chat_owner_host.c'),str(ROOT/'src/terminal/chat_owner.c')]
    subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-s','-w4','-we','-k8192',
                    '-fe=CHAT.EXE','-fm=CHAT.MAP',*inputs],cwd=drive,check=True)
    cases=[]
    keys=[[27],[65,13,27],[65,0xe00d,27],[65,0xe08,66,13,27],
          [0xe08,65,13,27],[17,19,27],[0x6d00,65,27],
          [0x7800+i*256 for i in range(10)]+[27],
          [0,65,13,27],[0x80,0xff,13,27],[65,66,27],
          [0x1e61,0x3062,13,27],[0x2d00,13,27],[0x1011,13,27]]
    keys += [[65]*n+[27] for n in (297,298,299,596,597)]
    for buffered in (0,1,0xffff):
        for duplex in (0,1,0xffff):
            for newline in (0,1):
                for sequence in keys:cases.append((buffered,duplex,newline,sequence))
    data=bytearray(struct.pack('<H',len(cases)));expected=[]
    for index,(b,d,n,sequence) in enumerate(cases):
        data+=struct.pack('<4H',b,d,n,len(sequence))+struct.pack('<'+'H'*len(sequence),*sequence)
        events=execute(native,sequence,buffered=b,duplex=d,newline=n)
        expected.append((0xfffe,index))
        for event in events:
            address=event[0]
            if address==0x3d94:expected.append((4,event[1]))
            elif address==0x9b6:expected.append((2,event[1]))
            elif address==0x5832:expected.append((3,event[1]))
            elif address==0xab0b:expected.append((1,event[1]&255))
            elif address==0xa62:expected.extend((1,byte) for byte in event[1])
            elif address==0xd830:expected.append((5,0x6d00))
            elif address==0x48cc:expected.append((6,0x7800+(event[1]-0x3758)//54*256))
        expected.append((0xffff,index))
    (drive/'VECTORS.BIN').write_bytes(data)
    config=out/'dosbox.conf'
    config.write_text('[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=fixed 12000\n[autoexec]\n@echo off\nmount c "'+str(drive)+'"\nc:\nCHAT >RESULT.TXT\nif errorlevel 1 goto failed\necho PASS>PASS.TXT\nexit\n:failed\necho FAIL>FAIL.TXT\nexit\n')
    with (out/'dosbox.log').open('w') as log:
        result=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(config)],cwd=drive,
            env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=60)
    assert result.returncode==0 and (drive/'PASS.TXT').exists() and not (drive/'FAIL.TXT').exists(),(drive/'RESULT.TXT').read_text()
    actual=list(struct.iter_unpack('<2H',(drive/'EVENTS.BIN').read_bytes()))
    for i,(a,b) in enumerate(zip(actual,expected)):
        assert a==b,(i,a,b)
    assert len(actual)==len(expected),(len(actual),len(expected))
    assert all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h for n,h in hashes.items())
    report=dict(passed=True,cases=len(cases),exact_ordered_events=len(actual),cpu='8086',banked=args.banked,
                context_bytes=320,max_sink_attempts_per_turn=32,sources=hashes,
                artifacts={str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file()},
                scope='Actual DOS8086 maintained Chat controller versus recovered760-byte CPU traces. Synthetic sink refusals, no-op UI/callee boundaries and keyboard vectors; no live terminal binding, complete native callees, UART/CTS or physical acceptance.')
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS serviced Chat DOS:',len(cases),'cases',len(actual),'exact ordered effects')


if __name__=='__main__':main()
