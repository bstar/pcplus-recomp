#!/usr/bin/env python3
"""Check source-owned global-string lifecycle; optional private original oracle.

All execution counts are within the compiler's valid0..128 table capacity.
Malformed counts are documented from native instructions, never executed here.
Error101 is tested with explicitly separate returning and stop-at-error models;
no original error UI, heap manager, or longjmp code executes.
"""
import argparse
import json
import os
from pathlib import Path
import struct
import subprocess
from unicorn import Uc, UC_ARCH_X86, UC_MODE_16, UC_HOOK_CODE, UC_HOOK_INTR
from unicorn.x86_const import (UC_X86_REG_CS, UC_X86_REG_DS, UC_X86_REG_SS,
    UC_X86_REG_ES, UC_X86_REG_IP, UC_X86_REG_SP, UC_X86_REG_BP,
    UC_X86_REG_SI, UC_X86_REG_DI, UC_X86_REG_AX, UC_X86_REG_DX)
from build_aspect_globals import (ROOT,OUT,START,RELEASE,END,SOURCE_FILE_START,SHA,HOOKS,COUNT,TABLE,sha)

CS,DS,STACK,STOP = 0x1000,0x3000,0xf000,0xf800
EXPECTED_FLAT_SHA = '2375d3d0436ed254d52c441682ae07983dcb967c9fe9792bab208c4092890fad'


def pointer(index,style):
    if style=='offset-zero':return (0,0x5005+index*16)
    if style=='segment-zero':return (0x5000+index*0x100,0)
    if style=='high-offset':return (0xff80,0x5000+index*16)
    assert style=='ordinary'
    return (0x50,0x5000+index*16)


def replay(code,count,style='ordinary',failed=None,error_returns=False,clear_slots=()):
    assert 0<=count<=128
    assert failed is None or 0<=failed<count
    u=Uc(UC_ARCH_X86,UC_MODE_16);u.mem_map(0,0x100000)
    u.mem_write(CS*16+START,code)
    def put(offset,value):u.mem_write(DS*16+offset,struct.pack('<H',value))
    def word(offset):return struct.unpack('<H',u.mem_read(DS*16+offset,2))[0]
    for reg,value in [(UC_X86_REG_CS,CS),(UC_X86_REG_DS,DS),(UC_X86_REG_SS,DS),
                      (UC_X86_REG_ES,0x2468),(UC_X86_REG_BP,0xabcd),
                      (UC_X86_REG_SI,0x1357),(UC_X86_REG_DI,0x2468)]:u.reg_write(reg,value)
    put(COUNT,0x8888)
    u.mem_write(DS*16+TABLE-2,b'\xcc'*(130*4+4))
    for i in range(count):
        offset,segment=pointer(i,style)
        u.mem_write(segment*16+offset-1,b'\xa5'*83)
    calls={'read':0,'alloc':0,'error':0,'free':0};frees=[];aborted=False;reached=False
    reverse={ip:name for name,ip in HOOKS.items()}
    def on_code(cpu,address,size,_):
        nonlocal reached,aborted
        assert cpu.reg_read(UC_X86_REG_CS)==CS
        ip=address-CS*16
        if ip==STOP:reached=True;cpu.emu_stop();return
        if START<=ip<END:return
        assert ip in reverse,hex(ip)
        name=reverse[ip];calls[name]+=1
        sp=cpu.reg_read(UC_X86_REG_SP)
        ax,dx,cleanup=0,0,0
        if name=='read':ax=count
        elif name=='alloc':
            index=calls[name]-1
            assert word(sp+2)==81 and index<count
            if index!=failed:ax,dx=pointer(index,style)
        elif name=='error':
            assert word(sp+2)==101 and failed is not None
            # Native pointer assignment precedes notification, no rollback.
            assert word(TABLE+failed*4)==word(TABLE+failed*4+2)==0
            if not error_returns:
                aborted=True;cpu.emu_stop();return
            cleanup=2
        elif name=='free':
            frees.append((word(sp+2),word(sp+4)))
        cpu.reg_write(UC_X86_REG_AX,ax);cpu.reg_write(UC_X86_REG_DX,dx)
        cpu.reg_write(UC_X86_REG_IP,word(sp));cpu.reg_write(UC_X86_REG_SP,sp+2+cleanup)
    def intr(cpu,number,_):raise AssertionError(f'Unexpected interrupt {number}')
    u.hook_add(UC_HOOK_CODE,on_code);u.hook_add(UC_HOOK_INTR,intr)
    def invoke(ip):
        nonlocal reached
        reached=False
        u.reg_write(UC_X86_REG_SP,STACK);put(STACK,STOP)
        u.reg_write(UC_X86_REG_SI,0x1357);u.reg_write(UC_X86_REG_DI,0x2468)
        u.emu_start(CS*16+ip,0,count=100000)
        if not aborted:
            assert reached and u.reg_read(UC_X86_REG_SP)==STACK+2
            assert u.reg_read(UC_X86_REG_SI)==0x1357 and u.reg_read(UC_X86_REG_DI)==0x2468
            assert u.reg_read(UC_X86_REG_BP)==0xabcd
        assert u.reg_read(UC_X86_REG_DS)==u.reg_read(UC_X86_REG_SS)==DS
    invoke(START)
    attempts=failed+1 if aborted else count
    assert word(COUNT)==count
    assert calls['read']==1 and calls['alloc']==attempts and calls['error']==int(failed is not None)
    expected_table=[]
    for i in range(count):
        expected=(0,0) if i==failed else pointer(i,style)
        if i>=attempts:expected=(0xcccc,0xcccc)
        assert (word(TABLE+i*4),word(TABLE+i*4+2))==expected
        expected_table.append(expected)
        offset,segment=pointer(i,style)
        data=bytes(u.mem_read(segment*16+offset-1,83))
        assert data==b'\xa5'+(b'\0' if i<attempts and i!=failed else b'\xa5')+b'\xa5'*81
    assert bytes(u.mem_read(DS*16+TABLE-2,2))==b'\xcc'*2
    assert bytes(u.mem_read(DS*16+TABLE+count*4,(130-count)*4))==b'\xcc'*((130-count)*4)
    before_release=bytes(u.mem_read(DS*16+TABLE,128*4))
    if not aborted:
        for i in clear_slots:
            assert 0<=i<count
            put(TABLE+i*4,0);put(TABLE+i*4+2,0);expected_table[i]=(0,0)
        before_release=bytes(u.mem_read(DS*16+TABLE,128*4))
        invoke(RELEASE)
        assert frees==[p for p in expected_table if p!=(0,0)]
        assert word(COUNT)==count
        assert bytes(u.mem_read(DS*16+TABLE,128*4))==before_release
    else:
        assert not frees
    assert bytes(u.mem_read(CS*16+START,END-START))==code
    return dict(count=count,style=style,failed=failed,error_model='return' if error_returns else 'stop-at-error',
                calls=calls,aborted=aborted,table_sha256=sha(before_release),frees=frees)


def cases():
    matrix=[]
    for style in ('ordinary','offset-zero','segment-zero','high-offset'):
        for count in range(129):matrix.append(dict(count=count,style=style))
        for count in (1,2,3,64,128):
            for failed in sorted({0,count//2,count-1}):
                for error_returns in (False,True):
                    matrix.append(dict(count=count,style=style,failed=failed,error_returns=error_returns))
        matrix.append(dict(count=128,style=style,clear_slots=(0,63,127)))
    return matrix


def dos_test():
    for name in ('DONE.TXT','PASS.TXT','FAIL.TXT'):(OUT/name).unlink(missing_ok=True)
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
GLOBALS >RESULT.TXT
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
            env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,
            check=True,timeout=30)
    summary=(OUT/'DONE.TXT').read_text().strip()
    assert (OUT/'PASS.TXT').exists() and not (OUT/'FAIL.TXT').exists(),(OUT/'RESULT.TXT').read_text()
    assert summary.endswith('0 failures'),summary
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--original',type=Path,help='Explicit optional private original PCPLUS.EXE comparison')
    args=parser.parse_args()
    subprocess.run(['python3',str(ROOT/'standalone/build_aspect_globals.py')],check=True)
    code=(OUT/'globals.bin').read_bytes();assert sha(code)==EXPECTED_FLAT_SHA
    matrix=cases();actual=[replay(code,**case) for case in matrix]
    optional=None
    if args.original:
        original=args.original.read_bytes();assert sha(original)==SHA
        native=original[SOURCE_FILE_START:SOURCE_FILE_START+END-START]
        assert native==code
        assert [replay(native,**case) for case in matrix]==actual
        optional=dict(original_sha256=SHA,file_start=SOURCE_FILE_START,file_end_exclusive=SOURCE_FILE_START+END-START,
                      native_sha256=sha(native),exact_bytes=len(code),paired_cpu_cases=len(matrix))
    summary=dos_test()
    report=dict(passed=True,cpu_cases=len(matrix),DOS_summary=summary,
                binary_sha256=sha((OUT/'GLOBALS.EXE').read_bytes()),flat_sha256=sha(code),
                optional_original=optional,original_inputs=[] if optional is None else [str(args.original)],
                check_sha256=sha(Path(__file__).read_bytes()),
                tested_counts='0..128 only; malformed values deliberately not executed',
                native_malformed_behavior='Stores complete read AX and signed JG; FFFF is negative and skips loops; byte255 exceeds128-slot table. No bounds check or rollback. Release retains pointers/count; repeated release is unsafe.',
                scope='Recovered routines execute unmodified with source-owned read/farheap/error callbacks. Error-return and stop-at-error are separate diagnostic models, not real error101/longjmp recovery. Real heap, loader and VM remain outside scope.')
    path=OUT/('checks-native.json' if args.original else 'checks.json')
    path.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
