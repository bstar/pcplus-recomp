#!/usr/bin/env python3
"""Source-only linked8086 DOS/CPU checks; optional private native-byte oracle.

The native dispatcher executes unmodified. Source-owned hook models provide
service/read/handlers/file/UI behavior; they do not implement the ASPECT VM.
An explicit --original argument enables private original-input comparison.
"""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess

from unicorn import Uc, UC_ARCH_X86, UC_MODE_16, UC_HOOK_CODE, UC_HOOK_INTR
from unicorn.x86_const import (UC_X86_REG_CS, UC_X86_REG_DS, UC_X86_REG_SS,
    UC_X86_REG_ES, UC_X86_REG_IP, UC_X86_REG_SP, UC_X86_REG_BP,
    UC_X86_REG_SI, UC_X86_REG_DI, UC_X86_REG_AX)
from build_aspect_dispatch import ROOT, OUT, SHA, START, END, NATIVE, DATA, sha

CS, DS, STACK, STOP = 0x1000, 0x3000, 0xf000, 0xf800
EXPECTED_FLAT_SHA = 'd2006fe5dd53b6416aec915c9bd58b4ae1a11fc003aafef090279fa2d37520a6'


def replay(code, opcode=7, flags=1, owner=0, initial_exit=0):
    u=Uc(UC_ARCH_X86,UC_MODE_16)
    u.mem_map(0,0x100000)
    u.mem_write(CS*16+START,code)
    def put(offset,value):
        u.mem_write(DS*16+offset,struct.pack('<H',value))
    def word(offset):
        return struct.unpack('<H',u.mem_read(DS*16+offset,2))[0]
    for reg,value in [(UC_X86_REG_CS,CS),(UC_X86_REG_DS,DS),(UC_X86_REG_SS,DS),
                      (UC_X86_REG_ES,DS),(UC_X86_REG_SP,STACK),(UC_X86_REG_BP,0xabcd),
                      (UC_X86_REG_SI,0x1357),(UC_X86_REG_DI,0x2468)]:
        u.reg_write(reg,value)
    u.mem_write(DS*16+STACK,struct.pack('<HHH',STOP,owner,0x1234))
    for i in range(215):
        put(DATA['handlers']+2*i,0x2000+2*i)
    for name,value in [('stream',0x1000),('paused',int(bool(flags&8))),
                       ('seek_enabled',int(bool(flags&32))),('wait_disabled',int(bool(flags&16))),
                       ('exit_state',initial_exit),('next_script',0x5678)]:
        put(DATA[name],value)
    put(0x1006,0x10 if flags&64 else 0)
    reverse={value:name for name,value in NATIVE.items()}
    counts=Counter()
    calls=[]
    reached=False
    def on_code(cpu,address,size,_):
        nonlocal reached
        assert cpu.reg_read(UC_X86_REG_CS)==CS
        ip=address-CS*16
        if ip==STOP:
            reached=True;cpu.emu_stop();return
        if START<=ip<END:
            return
        sp=cpu.reg_read(UC_X86_REG_SP)
        args=[word(sp+i) for i in (2,4,6,8)]
        si,di=cpu.reg_read(UC_X86_REG_SI),cpu.reg_read(UC_X86_REG_DI)
        cleanup=0;ax=0
        if ip in reverse:
            name=reverse[ip]
            counts[name]+=1
            if name=='probe':
                assert args[0]==DATA['argument']
                assert si==(0x1234 if counts[name]==1 else 0x5678)
                assert di==(owner if counts[name]==1 else 0)
                put(DATA['exit_state'],initial_exit if counts[name]==1 else 0)
                ax=flags&1
            elif name=='open':
                assert args[:2]==[di,si]
                ax=flags&2;cleanup=4
            elif name=='service':
                ax=flags&4
            elif name=='read':
                ax=opcode
            elif name=='seek':
                assert args==[0x1000,0xffff,0xffff,1]
            elif name=='wait':
                assert args[0]==0
                if counts[name]==2:
                    put(DATA['paused'],0)
                cleanup=2
            elif name=='error':
                assert args[0]==107
                put(DATA['exit_state'],1);cleanup=2
            elif name=='invalid_command':
                put(DATA['exit_state'],1)
            elif name=='close':
                assert args[0]==0x1000
        else:
            assert 0x2000<=ip<0x2000+430 and not ip&1,hex(ip)
            index=(ip-0x2000)//2
            assert index==opcode and si==opcode*2
            name='handler'
            counts[name]+=1
            put(DATA['exit_state'],999 if flags&128 and counts[name]==1 else 1)
        calls.append(name)
        cpu.reg_write(UC_X86_REG_AX,ax)
        cpu.reg_write(UC_X86_REG_IP,word(sp))
        cpu.reg_write(UC_X86_REG_SP,sp+2+cleanup)
    def interrupt(cpu,number,_):
        raise AssertionError(f'Unexpected interrupt {number}')
    u.hook_add(UC_HOOK_CODE,on_code)
    u.hook_add(UC_HOOK_INTR,interrupt)
    u.emu_start(CS*16+START,0,count=20000)
    assert reached
    assert u.reg_read(UC_X86_REG_SP)==STACK+6
    assert u.reg_read(UC_X86_REG_BP)==0xabcd
    assert u.reg_read(UC_X86_REG_SI)==0x1357 and u.reg_read(UC_X86_REG_DI)==0x2468
    assert u.reg_read(UC_X86_REG_DS)==u.reg_read(UC_X86_REG_SS)==DS
    assert bytes(u.mem_read(CS*16+START,END-START))==code
    assert counts['initialize']==counts['finish']==1
    if not flags&3:
        assert calls==['initialize','probe','open','finish']
    elif flags&4 or initial_exit:
        assert counts['read']==0 and counts['handler']==0
        assert counts['service']==(0 if initial_exit else 1)
        assert counts['shutdown']==(not owner and initial_exit!=999)
    else:
        loops=2 if flags&128 else 1
        assert counts['cleanup']==counts['close']==loops
        assert counts['shutdown']==(1 if loops==2 or not owner else 0)
        if opcode<=214:
            assert counts['handler']==loops
        elif flags&64:
            assert counts['error']==loops and counts['invalid_command']==0
        else:
            assert counts['invalid_command']==loops and counts['error']==0
        waits=2 if flags&8 and not flags&16 and opcode<199 else 0
        assert counts['wait']==waits
        seeks=1 if waits and flags&32 else 0
        assert counts['seek']==seeks
        assert counts['read']==loops+seeks
    return dict(counts=sorted(counts.items()),calls=calls,exit_state=word(DATA['exit_state']))


def cases():
    # Every original handler slot and both cleanup ownership paths.
    result=[dict(opcode=i,owner=o) for i in range(215) for o in (0,1)]
    # Boundary opcodes, wait/seek gates, and both FILE EOF states.
    for opcode in (0,198,199,214,215,255,0xffff):
        for flags in (1,9,25,41,57,65,73,89,105,121):
            for owner in (0,1):
                result.append(dict(opcode=opcode,flags=flags,owner=owner))
    for flags in (0,2,4,5,6,129,130):
        for owner in (0,1):
            result.append(dict(flags=flags,owner=owner))
    for state in (1,2,998):
        for owner in (0,1):
            result.append(dict(initial_exit=state,owner=owner))
    return result


def dos_test():
    for name in ('DONE.TXT','PASS.TXT','FAIL.TXT'):
        (OUT/name).unlink(missing_ok=True)
    config=f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
cycles=max
[mixer]
nosound=true
[autoexec]
@echo off
mount c "{OUT}"
c:
DISPATCH >RESULT.TXT
if errorlevel 1 goto failed
echo PASS>PASS.TXT
goto done
:failed
echo FAIL>FAIL.TXT
:done
exit
'''
    (OUT/'dosbox.conf').write_text(config)
    with (OUT/'dosbox.log').open('w') as log:
        subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(OUT/'dosbox.conf')],
            env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),
            stdout=log,stderr=log,check=True,timeout=30)
    summary=(OUT/'DONE.TXT').read_text().strip()
    assert (OUT/'PASS.TXT').exists() and not (OUT/'FAIL.TXT').exists(),(OUT/'RESULT.TXT').read_text()
    assert summary.endswith('0 failures'),summary
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--original',type=Path,help='Explicit optional private PCPLUS.EXE oracle; never required by normal build/check')
    args=parser.parse_args()
    subprocess.run(['python3',str(ROOT/'standalone/build_aspect_dispatch.py')],check=True)
    code=(OUT/'dispatch.bin').read_bytes()
    assert sha(code)==EXPECTED_FLAT_SHA
    matrix=cases()
    actual=[replay(code,**case) for case in matrix]
    optional=None
    if args.original:
        original=args.original.read_bytes()
        assert sha(original)==SHA
        native=original[0x1200+START:0x1200+END]
        assert native==code
        baseline=[replay(native,**case) for case in matrix]
        assert baseline==actual
        optional=dict(original_sha256=SHA,native_file_start=0x1200+START,native_file_end_exclusive=0x1200+END,
                      native_sha256=sha(native),exact_bytes=len(code),paired_cpu_cases=len(matrix))
    summary=dos_test()
    report=dict(passed=True,cpu_cases=len(matrix),DOS_summary=summary,flat_sha256=sha(code),
                binary_sha256=sha((OUT/'DISPATCH.EXE').read_bytes()),
                optional_original=optional,check_sha256=sha(Path(__file__).read_bytes()),
                original_inputs=[] if optional is None else [str(args.original)],
                scope='Native dispatcher executes on CPU; linked8086 DOS callback diagnostic. All215 handler slots checked; real opcode handlers, CRT, loader, UI and file IO deliberately stubbed. Not full ASPECT VM.')
    target='checks-native.json' if args.original else 'checks.json'
    (OUT/target).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
