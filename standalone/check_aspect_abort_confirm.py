#!/usr/bin/env python3
"""Execute native confirmation/yes-no instructions with modeled UI services.

Optional original comparison executes genuine file ranges, never an analysis EXE.
This is a component proof, not production DOS/serial or modal UI acceptance.
"""
import argparse,hashlib,json,struct,subprocess
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_CODE
from unicorn.x86_const import *

ROOT=Path(__file__).resolve().parents[1]
CODE,DATA,STOP=0x10000,0x30000,0x1f000
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def build(out):
    out.mkdir(parents=True,exist_ok=True)
    source=ROOT/'reconstruction/script_abort/confirm.asm'
    proof=json.loads(source.with_name('provenance.json').read_text());regions=[]
    for row in proof['ranges']:
        target=out/f"unit-{row['unit']}.bin"
        subprocess.run(['nasm','-fbin','-Ireconstruction/uart/',
            f"-DABORT_CONFIRM_UNIT={row['unit']}",str(source.relative_to(ROOT)),'-o',str(target)],cwd=ROOT,check=True)
        assert target.stat().st_size==row['bytes'] and sha(target)==row['sha256']
        regions.append((int(row['start'],16),target.read_bytes()))
    for far in (False,True):
        subprocess.run(['nasm','-fobj','-Ireconstruction/uart/',
            '-DABORT_CONFIRM_OMF',*(['-DABORT_CONFIRM_FAR'] if far else []),
            str(source.relative_to(ROOT)),'-o',str(out/('confirm-far.obj' if far else 'confirm.obj'))],cwd=ROOT,check=True)
    return proof,regions

def exercise(regions,low,high,default,cursor_mode,wrapper=False):
    u=Uc(UC_ARCH_X86,UC_MODE_16);u.mem_map(0,0x100000)
    for at,blob in regions:u.mem_write(CODE+at,blob)
    for register,value in [(UC_X86_REG_CS,0x1000),(UC_X86_REG_DS,0x3000),
        (UC_X86_REG_SS,0x3000),(UC_X86_REG_SP,0x8800),(UC_X86_REG_BP,0xbabe),
        (UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678),(UC_X86_REG_ES,0x4444),
        (UC_X86_REG_EFLAGS,0x202)]:u.reg_write(register,value)
    put=lambda at,value:u.mem_write(DATA+at,struct.pack('<H',value))
    word=lambda at:struct.unpack('<H',u.mem_read(DATA+at,2))[0]
    put(0x1f7e,0x2468);put(0x1f7c,0x1357);put(0x7a6c,cursor_mode);put(0x7a9e,0xdead)
    stack=[STOP-CODE] if wrapper else [STOP-CODE,default,0x1357,0x031a]
    u.mem_write(DATA+0x8800,struct.pack('<'+'H'*len(stack),*stack))
    frame=bytes((i*37+low+high)&255 for i in range(4000));u.mem_write(0xb8000,frame)
    # Prediction is derived from the input key, before executing either body.
    accepted=low in (13,27,ord('Y'),ord('y'),ord('N'),ord('n'))
    answer=1 if low in (ord('Y'),ord('y')) else 0 if low in (27,ord('N'),ord('n')) else default
    keys=[(high<<8)|low]+([] if accepted else [0x1c0d]);pending=keys[:]
    cursor=0x1122;cursor_stack=[];events=[];done=[];instructions=set()
    calls={0x3fc7:('save',0,1),0x4015:('restore',0,3),0x6bf0:('write',6,3),
        0x6b5a:('cursor-push',0,0),0x6b42:('cursor-pop',0,0),0x6e78:('cursor-set',2,1),
        0x6dca:('cursor-enable',0,0),0x6e5a:('cursor-disable',0,0),
        0x64fe:('read',0,0),0x376d:('bell',0,0)}
    def boundary(machine,address,size,_):
        nonlocal cursor
        if address==STOP:done.append(True);machine.emu_stop();return
        at=address-CODE;instructions.add(at)
        if at not in calls:return
        name,clean,count=calls[at];sp=machine.reg_read(UC_X86_REG_SP)
        args=struct.unpack('<'+'H'*(count+1),machine.mem_read(DATA+sp,2*(count+1)))
        events.append([name,list(args[1:])])
        for reg,value in [(UC_X86_REG_AX,0xe123),(UC_X86_REG_BX,0xe456),
            (UC_X86_REG_CX,0xe789),(UC_X86_REG_DX,0xeabc)]:machine.reg_write(reg,value)
        if name=='save':
            assert wrapper and args[1:]==(0x329e,)
            assert bytes(machine.mem_read(0xb8000,4000))==frame
            machine.mem_write(0xb8000,b'\x58\x17'*2000)
            machine.reg_write(UC_X86_REG_AX,0x3456);machine.reg_write(UC_X86_REG_DX,0x4567)
        elif name=='restore':
            assert wrapper and args[1:]==(0x329e,0x3456,0x4567)
            machine.mem_write(0xb8000,frame)
        elif name=='cursor-push':cursor_stack.append(cursor)
        elif name=='cursor-pop':cursor=cursor_stack.pop()
        elif name=='cursor-set':assert args[1:]==(0x031a,);cursor=0x031a
        elif name=='cursor-enable':put(0x7a6c,1)
        elif name=='cursor-disable':put(0x7a6c,0)
        elif name=='read':assert pending;machine.reg_write(UC_X86_REG_AX,pending.pop(0))
        machine.reg_write(UC_X86_REG_SP,sp+2+clean);machine.reg_write(UC_X86_REG_IP,args[0])
    u.hook_add(UC_HOOK_CODE,boundary)
    u.emu_start(CODE+(0x4e6b if wrapper else 0x6dde),0,count=2000)
    assert done and not pending and not cursor_stack
    assert u.reg_read(UC_X86_REG_AX)==answer
    assert word(0x7a9e)==keys[-1] and word(0x7a6c)==cursor_mode and cursor==0x1122
    assert bytes(u.mem_read(0xb8000,4000))==frame
    expected=[]
    if wrapper:expected+=[['save',[0x329e]],['write',[0x4948,0x2468,0x0307]]]
    expected+=[['cursor-push',[]],['write',[0x7a96 if default==0 else 0x7a9a,0x1357,0x031a]],['cursor-set',[0x031a]]]
    if cursor_mode==0:expected.append(['cursor-enable',[]])
    expected.append(['read',[]])
    if not accepted:expected+=[['bell',[]],['read',[]]]
    if accepted and low!=13:expected.append(['write',[0x7a9a if answer else 0x7a96,0x1357,0x031a]])
    if cursor_mode==0:expected.append(['cursor-disable',[]])
    expected.append(['cursor-pop',[]])
    if wrapper:expected.append(['restore',[0x329e,0x3456,0x4567]])
    assert events==expected,(low,high,default,cursor_mode,wrapper,events,expected)
    registers=[u.reg_read(r) for r in (UC_X86_REG_SP,UC_X86_REG_BP,UC_X86_REG_SI,
        UC_X86_REG_DI,UC_X86_REG_DS,UC_X86_REG_SS,UC_X86_REG_ES)]
    assert registers==[0x8802 if wrapper else 0x8808,0xbabe,0x1234,0x5678,0x3000,0x3000,0x4444]
    assert u.reg_read(UC_X86_REG_EFLAGS)&0x200
    return dict(low=low,high=high,default=default,cursor_mode=cursor_mode,wrapper=wrapper,
        answer=answer,reads=keys,events=events,registers=registers),instructions

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--original',action='store_true');a=p.parse_args()
    out=ROOT/'build/aspect-abort-confirm';proof,regions=build(out);original=None
    if a.original:
        blob=(ROOT/'analysis/pcplus-originals/PCPLUS-main-2.01.EXE').read_bytes()
        assert hashlib.sha256(blob).hexdigest()==proof['source_sha256']
        original=[(int(row['start'],16),blob[row['file_offset']:row['file_offset']+row['bytes']]) for row in proof['ranges']]
        assert original==regions
    cases=[];instructions=set();comparisons=0
    for wrapper,default in [(False,0),(False,1),(True,0)]:
        for mode in (0,1,2):
            for high in (0,0xab):
                for low in range(256):
                    result,seen=exercise(regions,low,high,default,mode,wrapper);instructions|=seen
                    if original is not None:
                        reference,_=exercise(original,low,high,default,mode,wrapper)
                        assert reference==result;comparisons+=1
                    cases.append(result)
    # The generic native helper preserves a non-Boolean default on Enter.
    for mode in (0,0xffff):
        result,seen=exercise(regions,13,0x1c,0xffff,mode);instructions|=seen
        if original is not None:
            assert exercise(original,13,0x1c,0xffff,mode)[0]==result;comparisons+=1
        cases.append(result)
    report=dict(passed=True,cases=len(cases),original_comparisons=comparisons,
        instruction_addresses=sorted(instructions),source_sha256=sha(ROOT/'reconstruction/script_abort/confirm.asm'),
        checker_sha256=sha(Path(__file__)),case_results_sha256=hashlib.sha256(json.dumps(cases,sort_keys=True).encode()).hexdigest(),
        products={p.name:sha(p) for p in out.iterdir() if p.suffix in ('.bin','.obj')},scope=__doc__)
    name='original-checks.json' if a.original else 'checks.json'
    (out/name).write_text(json.dumps(report,indent=2)+'\n')
    print('Abort confirmation',len(cases),'component cases;',comparisons,'original comparisons PASS')

if __name__=='__main__':main()
