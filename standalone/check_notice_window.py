#!/usr/bin/env python3
"""Execute complete recovered window expansion/collapse against guarded video."""
import argparse,hashlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_CODE,UC_HOOK_INTR,UC_HOOK_INSN
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/notice-window'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def case(rect,animate,legacy,speed,sound,fail=False,original=False):
    u=Uc(UC_ARCH_X86,UC_MODE_16);u.mem_map(0,0x100000);m=json.loads((OUT/'manifest.json').read_text());source=None
    if original:
        source=(ROOT/'analysis/pcplus-originals/PCPLUS-main-2.01.EXE').read_bytes();assert hashlib.sha256(source).hexdigest()=='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
    for row in m['units']:
        data=source[row['file_offset']:row['file_offset']+row['bytes']] if source else (OUT/(row['name']+'.bin')).read_bytes();u.mem_write(0x10000+row['start'],data)
    u.mem_write(0x30000,bytes((i*17+31)&255 for i in range(65536)))
    def word(at,value):u.mem_write(0x30000+at,struct.pack('<H',value))
    for at,value in {0x1d3e:sound,0x3350:0x70,0x3352:0x6000,0x7a36:0x7a3a,0x7a38:0x7a3a,0x7a4e:0,0x7a66:legacy,0x7a6a:8,0x7a72:80,0x7a74:25,0x7a78:0xb800,0x7a7a:160,0x7a7c:4000,0x7a8c:2000,0x7a8e:0,0x7a94:animate,0x7ab2:0x6000,0x7ab4:0x6000,0x7ac4:speed}.items():word(at,value)
    u.mem_write(0x36000,bytes([218,196,191,179,217,196,192,179]))
    u.mem_write(0x3330c,struct.pack('<5H',*rect,0x3350));u.mem_write(0x450,struct.pack('<H',0x0405));u.mem_write(0x463,struct.pack('<H',0x3d4))
    video=bytes((i*19+23)&255 for i in range(8192));u.mem_write(0xb8000,video)
    u.mem_write(0x50000,b'G'*16+b'X'*4000+b'H'*16);calls=[];ports=[];allocations=[]
    def args(n):return struct.unpack('<'+'H'*n,bytes(u.mem_read(0x30000+u.reg_read(UC_X86_REG_SP)+2,n*2)))
    def ret():
        sp=u.reg_read(UC_X86_REG_SP);ip=struct.unpack('<H',bytes(u.mem_read(0x30000+sp,2)))[0];u.reg_write(UC_X86_REG_SP,sp+2);u.reg_write(UC_X86_REG_IP,ip)
    def boundary(cpu,addr,size,_):
        at=addr-0x10000
        if at==0x860f:
            assert args(1)==(4000,);calls.append('allocate');allocations.append(not fail);cpu.reg_write(UC_X86_REG_AX,0 if fail else 16);cpu.reg_write(UC_X86_REG_DX,0 if fail else 0x5000);ret()
        elif at==0x85fc:assert args(2)==(16,0x5000);calls.append('free');ret()
        elif at in (0x488f,0x775a,0x7764):calls.append(hex(at));ret()
    def interrupt(cpu,number,_):
        assert number==0x10;ax=cpu.reg_read(UC_X86_REG_AX);ah=ax>>8
        if ah==2:u.mem_write(0x450,struct.pack('<H',cpu.reg_read(UC_X86_REG_DX)))
        elif ah==3:cpu.reg_write(UC_X86_REG_DX,struct.unpack('<H',bytes(u.mem_read(0x450,2)))[0])
        elif ah==6:
            assert ax&255==0;cx=cpu.reg_read(UC_X86_REG_CX);dx=cpu.reg_read(UC_X86_REG_DX);attr=cpu.reg_read(UC_X86_REG_BX)>>8
            top,left=cx>>8,cx&255;bottom,right=dx>>8,dx&255;assert 0<=top<=bottom<25 and 0<=left<=right<80,(rect,cx,dx)
            for y in range(top,bottom+1):u.mem_write(0xb8000+160*y+2*left,bytes([32,attr])*(right-left+1))
        else:raise AssertionError(hex(ax))
    def output(cpu,port,size,value,_):assert size==1 and port in (0x3d4,0x3d5);ports.append((port,value))
    u.hook_add(UC_HOOK_CODE,boundary);u.hook_add(UC_HOOK_INTR,interrupt);u.hook_add(UC_HOOK_INSN,output,None,1,0,UC_X86_INS_OUT)
    def call(at,values):
        for reg,value in [(UC_X86_REG_CS,0x1000),(UC_X86_REG_DS,0x3000),(UC_X86_REG_SS,0x3000),(UC_X86_REG_SP,0xf000),(UC_X86_REG_BP,0x9876),(UC_X86_REG_SI,0x1357),(UC_X86_REG_DI,0x2468),(UC_X86_REG_EFLAGS,0x202)]:u.reg_write(reg,value)
        u.mem_write(0x3f000,struct.pack('<'+'H'*(len(values)+1),0x200,*values));u.emu_start(0x10000+at,0x10200,count=2000000)
        assert u.reg_read(UC_X86_REG_IP)==0x200 and u.reg_read(UC_X86_REG_SP)==0xf002
        assert [u.reg_read(r) for r in [UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI,UC_X86_REG_DS,UC_X86_REG_SS]]==[0x9876,0x1357,0x2468,0x3000,0x3000]
        return u.reg_read(UC_X86_REG_AX),u.reg_read(UC_X86_REG_DX)
    token=call(0x3fc7,[0x330c]);opened=bytes(u.mem_read(0xb8000,8192));assert opened!=video and opened[4000:]==video[4000:]
    assert token==((0,0) if fail else (16,0x5000));assert calls.count('allocate')==1
    if not fail:assert bytes(u.mem_read(0x50010,4000))==video[:4000]
    call(0x4015,[0x330c,*token]);closed=bytes(u.mem_read(0xb8000,8192))
    assert (closed==video)==(not fail)
    assert calls.count('free')==(not fail) and calls.count('0x488f')==(2 if fail else 0)
    assert struct.unpack('<H',bytes(u.mem_read(0x450,2)))[0]==0x0405
    assert bytes(u.mem_read(0x50000,16))==b'G'*16 and bytes(u.mem_read(0x50fb0,16))==b'H'*16
    return dict(opened_sha256=hashlib.sha256(opened).hexdigest(),closed_sha256=hashlib.sha256(closed).hexdigest(),calls=calls,ports=ports)
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--original',action='store_true');a=p.parse_args();rows=[]
    rectangles=[(9,34,11,45),(2,2,8,30),(0,0,24,79),(1,1,22,76),(10,0,12,4),(20,60,24,79)]
    for rect,animate,legacy,speed,sound in itertools.product(rectangles,[0,1],[0,1],[1,100],[0,1]):
        result=case(rect,animate,legacy,speed,sound)
        if a.original:assert result==case(rect,animate,legacy,speed,sound,original=True)
        rows.append(dict(rect=rect,animate=animate,legacy=legacy,speed=speed,sound=sound,**result))
    for animate in (0,1):
        result=case(rectangles[0],animate,0,100,0,fail=True)
        if a.original:assert result==case(rectangles[0],animate,0,100,0,fail=True,original=True)
        rows.append(dict(allocation_failure=True,animate=animate,**result))
    result=dict(passed=True,cases=rows,original_comparisons=len(rows) if a.original else 0,inputs={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),OUT/'manifest.json']},scope=__doc__+' Native snapshot/frame/shadow/expansion/collapse/cell copy and cursor code execute; DOS heap, BIOS scrolling/cursor, sound and CRTC ports are explicit models. Null-allocation screen destruction is a reproduced defect. No physical timing or application acceptance.')
    (OUT/('original-checks.json' if a.original else 'checks.json')).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,cases=len(rows),original_comparisons=result['original_comparisons'])))
if __name__=='__main__':main()
