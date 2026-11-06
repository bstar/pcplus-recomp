#!/usr/bin/env python3
"""DOS8086 serviced TEXT effects versus recovered48CC/4934 CPU instructions."""
import argparse,hashlib,json,os,struct,subprocess
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_CODE
from unicorn.x86_const import *
from build_path_session import ROOT,sha,object_segments


def reference(code,text,pause,echo,pacing):
    u=Uc(UC_ARCH_X86,UC_MODE_16);u.mem_map(0,0x100000)
    for at,raw in code.items():u.mem_write(0x10000+at,raw)
    u.mem_write(0x21000,text+b'\0');u.mem_write(0x21d66,bytes([pause]));u.mem_write(0x21d1a,struct.pack('<H',echo));u.mem_write(0x21d68,struct.pack('<H',pacing))
    for r,v in [(UC_X86_REG_CS,0x1000),(UC_X86_REG_DS,0x2000),(UC_X86_REG_SS,0x2000),
                (UC_X86_REG_SP,0xfe00),(UC_X86_REG_BP,0x3210),(UC_X86_REG_SI,0x4567),
                (UC_X86_REG_DI,0x6789),(UC_X86_REG_IP,0x48cc),(UC_X86_REG_EFLAGS,0x202)]:u.reg_write(r,v)
    u.mem_write(0x2fe00,struct.pack('<2H',0xfa00,0x1000));events=[];done=[]
    services={0x610:(4,0),0xab0b:(1,2),0x6b98:(5,2),0x6b72:(6,2)}
    def step(u,address,size,unused):
        if address==0x1fa00:done.append(True);u.emu_stop();return
        if address-0x10000 not in services:return
        kind,cleanup=services[address-0x10000];sp=u.reg_read(UC_X86_REG_SP)
        ip,value=struct.unpack('<2H',u.mem_read(0x20000+sp,4));events.append((kind,value))
        u.reg_write(UC_X86_REG_SP,sp+2+cleanup);u.reg_write(UC_X86_REG_IP,ip)
    u.hook_add(UC_HOOK_CODE,step);u.emu_start(0x148cc,0,count=100000)
    assert done and u.reg_read(UC_X86_REG_SP)==0xfe02
    for r,v in [(UC_X86_REG_DS,0x2000),(UC_X86_REG_SS,0x2000),(UC_X86_REG_BP,0x3210),(UC_X86_REG_SI,0x4567),(UC_X86_REG_DI,0x6789)]:assert u.reg_read(r)==v
    return events


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--original',action='store_true',help='Analyst-only genuine original byte comparison; never an application build input')
    a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir();drive=out/'drive';drive.mkdir()
    names=['src/chat/text.c','src/chat/text.h','src/chat/text_bank.asm','src/terminal/chat_owner.h',
           'standalone/chat_text_host.c','standalone/test_chat_text_dos.py','standalone/build_path_session.py',
           'reconstruction/meta_keys/text.asm','reconstruction/meta_keys/caret.asm',
           'reconstruction/meta_keys/provenance.json','reconstruction/uart/encodings.inc']
    sources={n:sha(ROOT/n) for n in names};proof=json.loads((ROOT/'reconstruction/meta_keys/provenance.json').read_text());code={}
    original=(ROOT/'analysis/pcplus-originals/PCPLUS-main-2.01.EXE').read_bytes() if a.original else None
    if original is not None:assert hashlib.sha256(original).hexdigest()==proof['source_sha256']
    for n,at in [('text',0x48cc),('caret',0x4934)]:
        target=out/(n+'.bin');subprocess.run(['nasm','-fbin','-I'+str(ROOT/'reconstruction/uart')+'/',str(ROOT/'reconstruction/meta_keys'/(n+'.asm')),'-o',str(target)],check=True)
        raw=target.read_bytes();unit=next(x for x in proof['units'] if Path(x['file']).stem==n);assert sha(target)==unit['sha256'] and len(raw)==unit['bytes']
        if original is not None:assert raw==original[0x1200+at:0x1200+at+len(raw)]
        code[at]=raw
    cases=[]
    for operand in range(1,256):
        for echo in (0,1):
            for pause in (126,255):cases.append((b'^'+bytes([operand]),pause,echo,7,65535))
    for value in range(1,256):
        for echo in (0,1):cases.append((b'^^^' if value==94 else bytes([value]),126,echo,0,65535))
    fixed=[b'',b'^@A~B',b'~',b'^^^',b'^^',b'^`LOST',b'A^MB',b'\x80\xff',b'A'*51,b'^@'*25,b'AB^`CD^@',b'NOEXEC^M']
    for text in fixed:
        for echo in (0,1,65535):
            for pause in (0,255,65,126):
                for pacing in (0,65535):cases.append((text,pause,echo,pacing,65535))
    sequence=reference(code,b'AB~^@C',126,1,7)
    for limit in range(len(sequence)+1):cases.append((b'AB~^@C',126,1,7,limit))
    cases += [(b'NOEXEC^M',126,1,7,65535)]*4
    expected=[]
    with (drive/'CASES.BIN').open('wb') as stream:
        stream.write(struct.pack('<H',len(cases)))
        for index,(text,pause,echo,pacing,limit) in enumerate(cases):
            stream.write(struct.pack('<H',index%4)+text.ljust(52,b'\0')+struct.pack('<4H',pause,echo,pacing,limit))
            effects=reference(code,text,pause,echo,pacing);expected += effects if limit==65535 else effects[:limit]
            expected.append((65535,index))
    subprocess.run(['wcc','-q','-bt=dos','-0','-ms','-s','-w4','-we','-ecc','-dCHAT_BANK','-nt=CHAT_TEXT_CODE','-nc=FARCODE','-fo=text.obj',str(ROOT/'src/chat/text.c')],cwd=drive,check=True)
    subprocess.run(['nasm','-fobj',str(ROOT/'src/chat/text_bank.asm'),'-o','bank.obj'],cwd=drive,check=True)
    segments=object_segments(drive/'text.obj');assert all(v['bytes']==0 for n,v in segments.items() if n!='CHAT_TEXT_CODE')
    subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-s','-w4','-we','-ecc','-dCHAT_BANK','-k8192','-fe=TEXT.EXE','-fm=TEXT.MAP',str(ROOT/'standalone/chat_text_host.c'),'bank.obj','text.obj'],cwd=drive,check=True)
    config=out/'dosbox.conf';config.write_text('[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=fixed 12000\n[autoexec]\n@echo off\nmount c "'+str(drive)+'"\nc:\nTEXT >RESULT.TXT\nif errorlevel 1 goto failed\necho PASS>PASS.TXT\nexit\n:failed\necho FAIL>FAIL.TXT\nexit\n')
    with (out/'dosbox.log').open('w') as log:r=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(config)],cwd=drive,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=60)
    text=(drive/'RESULT.TXT').read_text();assert r.returncode==0 and (drive/'PASS.TXT').exists() and not (drive/'FAIL.TXT').exists(),text
    actual=(drive/'EVENTS.BIN').read_bytes();want=b''.join(struct.pack('<2H',*e) for e in expected);assert actual==want,(len(actual),len(want))
    assert all(sha(ROOT/n)==h for n,h in sources.items())
    report=dict(passed=True,cases=len(cases),ordered_effects=len(expected)-len(cases),abort_points=len(sequence)+1,invalid_open_controls=10,state_bytes=68,code_bytes=segments['CHAT_TEXT_CODE']['bytes'],private_DGROUP_bytes=0,max_sink_attempts=32,genuine_original_bytes_compared=original is not None,sources=sources,artifacts={str(q.relative_to(out)):sha(q) for q in out.rglob('*') if q.is_file()},scope=__doc__+' CPU reference records exact echo/wire/wait9/pacing calls; time/UART/rendering and effects inside echo are modeled service boundaries. Production far code executes in DOS with synthetic sink backpressure/abort/reopen and invalid-open controls. No frontend/module integration, real BIOS/calibrated delay, original terminal-echo rendering, BBS or physical acceptance.')
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS',len(cases),'DOS TEXT vectors;',report['ordered_effects'],'native-ordered effects')


if __name__=='__main__':main()
