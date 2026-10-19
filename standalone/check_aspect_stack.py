#!/usr/bin/env python3
"""Source-only native value-stack/copy CPU and linked8086 DOS checks.

Optional --original verifies private original ranges. Error105 executes only
source-owned return/stop callbacks, not the original UI/longjmp implementation.
Unsafe native arithmetic and pop semantics are retained and observed in isolated
mapped CPU memory or dedicated DOS fixture padding, never advertised as safe.
"""
import argparse
import json
import os
from pathlib import Path
import random
import struct
import subprocess
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_CODE,UC_HOOK_INTR
from unicorn.x86_const import (UC_X86_REG_CS,UC_X86_REG_DS,UC_X86_REG_SS,UC_X86_REG_ES,
    UC_X86_REG_IP,UC_X86_REG_SP,UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI,
    UC_X86_REG_AX,UC_X86_REG_DX,UC_X86_REG_EFLAGS)
from build_aspect_stack import (ROOT,OUT,START,END,SOURCE_FILE_START,SHA,ENTRIES,
    POINTER,BASE,LENGTH,ERROR,COPY,COPY_END,sha)

CS,DS,STACK,STOP=0x1000,0x3000,0xf000,0xf800
EXPECTED_FLAT_SHA='1aab9bd8ea8c0879214142073ea95bd8d2e5fc8abf1760663fbd607f6e19ea4a'
SIZES={'reserve':None,'push_word':2,'push_dword':4,'push_eight':8,'push_string':81,'pop_word':-2,'pop_dword':-4}


def replay(code,copy,operation,pointer=BASE,value=0x76543210,size=0,source=0x1000,error_returns=False):
    u=Uc(UC_ARCH_X86,UC_MODE_16);u.mem_map(0,0x100000)
    u.mem_write(CS*16+START,code);u.mem_write(CS*16+COPY,copy)
    u.mem_write(DS*16,b'\xa5'*65536)
    def put(offset,value):u.mem_write(DS*16+offset,struct.pack('<H',value))
    def word(offset):return struct.unpack('<H',u.mem_read(DS*16+offset,2))[0]
    for reg,value_ in [(UC_X86_REG_CS,CS),(UC_X86_REG_DS,DS),(UC_X86_REG_SS,DS),
                       (UC_X86_REG_ES,0x4321),(UC_X86_REG_SP,STACK),(UC_X86_REG_BP,0xabcd),
                       (UC_X86_REG_SI,0x1357),(UC_X86_REG_DI,0x2468),
                       (UC_X86_REG_EFLAGS,2)]:u.reg_write(reg,value_)
    put(POINTER,pointer)
    n=SIZES[operation]
    if operation=='reserve':args=[size];request=size
    elif operation=='push_word':args=[value&65535];request=n
    elif operation=='push_dword':args=[value&65535,value>>16];request=n
    elif n>0:args=[source];request=n
    else:args=[];request=0
    payload=bytes((i*73+19)&255 for i in range(128))
    if operation in ('push_eight','push_string'):
        for i,byte in enumerate(payload):u.mem_write(DS*16+((source+i)&65535),bytes([byte]))
    u.mem_write(DS*16+STACK,struct.pack('<'+'H'*(len(args)+1),STOP,*args))
    before=bytes(u.mem_read(DS*16,65536));expected=bytearray(before)
    # Each word operand can cross the segment's final byte; a separate
    # [BX+2] effective address wraps16-bit before its own word fetch.
    before_words=before+bytes(u.mem_read(DS*16+65536,2))
    reached=False;aborted=False;errors=0;copies=0
    def on_code(cpu,address,instruction_size,_):
        nonlocal reached,aborted,errors,copies
        assert cpu.reg_read(UC_X86_REG_CS)==CS
        ip=address-CS*16
        if ip==STOP:reached=True;cpu.emu_stop();return
        if START<=ip<END:return
        if COPY<=ip<COPY_END:
            if ip==COPY:copies+=1
            return
        assert ip==ERROR,hex(ip)
        errors+=1;sp=cpu.reg_read(UC_X86_REG_SP)
        assert word(sp+2)==105
        assert word(POINTER)==pointer
        if not error_returns:aborted=True;cpu.emu_stop();return
        cpu.reg_write(UC_X86_REG_IP,word(sp));cpu.reg_write(UC_X86_REG_SP,sp+4)
    def intr(cpu,number,_):raise AssertionError(f'Unexpected interrupt {number}')
    u.hook_add(UC_HOOK_CODE,on_code);u.hook_add(UC_HOOK_INTR,intr)
    u.emu_start(CS*16+ENTRIES[operation],0,count=100000)
    should_error=operation.startswith(('reserve','push')) and ((pointer+request)&65535)>BASE+LENGTH
    assert errors==int(should_error)
    assert aborted==(should_error and not error_returns)
    if aborted:
        expected_pointer=pointer
    elif operation=='reserve':expected_pointer=pointer
    else:expected_pointer=(pointer+n)&65535
    assert word(POINTER)==expected_pointer
    returned=None
    if not aborted:
        assert reached and u.reg_read(UC_X86_REG_SP)==STACK+2+len(args)*2
        assert u.reg_read(UC_X86_REG_BP)==0xabcd
        assert u.reg_read(UC_X86_REG_SI)==0x1357 and u.reg_read(UC_X86_REG_DI)==0x2468
        if operation.startswith('push'):
            if n==2:data=struct.pack('<H',value&65535)
            elif n==4:data=struct.pack('<I',value)
            else:data=bytes(before[(source+i)&65535] for i in range(n))
            for i,byte in enumerate(data):expected[(pointer+i)&65535]=byte
            assert copies==int(n in (8,81))
        elif operation.startswith('pop'):
            low=struct.unpack('<H',before_words[expected_pointer:expected_pointer+2])[0]
            high_offset=(expected_pointer+2)&65535
            high=struct.unpack('<H',before_words[high_offset:high_offset+2])[0]
            assert u.reg_read(UC_X86_REG_AX)==low
            if n==-4:assert u.reg_read(UC_X86_REG_DX)==high
            returned=low if n==-2 else low|(high<<16)
    else:assert copies==0
    expected[POINTER:POINTER+2]=struct.pack('<H',expected_pointer)
    actual=bytearray(u.mem_read(DS*16,65536))
    # Only the real CPU call stack's scratch bytes are outside the value domain.
    expected[STACK-128:STACK+16]=actual[STACK-128:STACK+16]
    assert expected==actual,(operation,hex(pointer),size,error_returns)
    assert u.reg_read(UC_X86_REG_DS)==u.reg_read(UC_X86_REG_SS)==DS
    assert not u.reg_read(UC_X86_REG_EFLAGS)&0x400, 'Native copy must restore DF=0'
    assert bytes(u.mem_read(CS*16+START,END-START))==code
    assert bytes(u.mem_read(CS*16+COPY,COPY_END-COPY))==copy
    return dict(operation=operation,pointer=pointer,errors=errors,aborted=aborted,
                next_pointer=expected_pointer,returned=returned,copies=copies,data_sha256=sha(actual))


def cases():
    result=[]
    for operation in ENTRIES:
        n=SIZES[operation]
        if operation=='reserve':
            for pointer in (0,BASE-1,BASE,BASE+LENGTH-1,BASE+LENGTH,BASE+LENGTH+1,0xff00,0xfffe,0xffff):
                for size in (0,1,2,4,8,81,128,0x3aca,0x8000,0xfffe,0xffff):
                    for returns in (False,True):
                        result.append(dict(operation=operation,pointer=pointer,size=size,error_returns=returns))
        elif n>0:
            for pointer in (0,BASE-1,BASE,BASE+1,BASE+LENGTH-n,BASE+LENGTH-n+1,BASE+LENGTH,0xffac,0xfffc,0xfffe):
                for returns in (False,True):
                    for value in (0,0xffff,0x80008000,0xffffffff,0x76543210):
                        result.append(dict(operation=operation,pointer=pointer,value=value,error_returns=returns))
            if n in (8,81):
                for delta in (-1,0,1):
                    result.append(dict(operation=operation,pointer=BASE+100,source=BASE+100+delta))
        else:
            for pointer in (0,1,2,3,4,BASE-1,BASE,BASE+1,BASE+LENGTH,0xfffe,0xffff):
                result.append(dict(operation=operation,pointer=pointer))
    rng=random.Random(0xa5c)
    for _ in range(160):
        operation=rng.choice(list(ENTRIES));n=SIZES[operation]
        pointer=BASE+rng.randrange(LENGTH-100)
        result.append(dict(operation=operation,pointer=pointer,value=rng.randrange(1<<32),size=rng.randrange(300),error_returns=bool(rng.randrange(2))))
    return result


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
STACK >RESULT.TXT
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
            env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=30)
    summary=(OUT/'DONE.TXT').read_text().strip()
    assert (OUT/'PASS.TXT').exists() and not (OUT/'FAIL.TXT').exists(),(OUT/'RESULT.TXT').read_text()
    assert summary.endswith('0 failures'),summary
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--original',type=Path,help='Explicit private original-byte and pairedCPU oracle')
    args=parser.parse_args()
    subprocess.run(['python3',str(ROOT/'standalone/build_aspect_stack.py')],check=True)
    code=(OUT/'stack.bin').read_bytes();copy=(OUT/'copy.bin').read_bytes()
    assert sha(code)==EXPECTED_FLAT_SHA
    matrix=cases();actual=[replay(code,copy,**case) for case in matrix]
    optional=None
    if args.original:
        original=args.original.read_bytes();assert sha(original)==SHA
        native=original[SOURCE_FILE_START:SOURCE_FILE_START+END-START]
        native_copy=original[0x1200+COPY:0x1200+COPY_END]
        assert native==code and native_copy==copy
        assert [replay(native,native_copy,**case) for case in matrix]==actual
        optional=dict(original_sha256=SHA,file_start=SOURCE_FILE_START,file_end_exclusive=SOURCE_FILE_START+END-START,
                      exact_stack_bytes=len(code),exact_copy_bytes=len(copy),paired_cpu_cases=len(matrix))
    summary=dos_test()
    report=dict(passed=True,cpu_cases=len(matrix),DOS_summary=summary,optional_original=optional,
                binary_sha256=sha((OUT/'STACK.EXE').read_bytes()),flat_sha256=sha(code),copy_sha256=sha(copy),
                check_sha256=sha(Path(__file__).read_bytes()),original_inputs=[] if optional is None else [str(args.original)],
                scope='Seven native typed-stack primitives and real85B4copy execute unchanged. Native unchecked underflow,16-bit reserve/pointer wrap and error105-return continuation verified in isolated memory; error-stop is a callback policy, not original longjmp. No safe stack or full VM claim.')
    path=OUT/('checks-native.json' if args.original else 'checks.json')
    path.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
