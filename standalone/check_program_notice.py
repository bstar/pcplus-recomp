#!/usr/bin/env python3
"""Exercise original notice instructions with explicit screen/key/time boundaries."""
import argparse,hashlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_CODE,UC_HOOK_INTR
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/program-notice'
REGS=[UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI,UC_X86_REG_DS,UC_X86_REG_SS]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def case(entry,length,kind,key,seconds,original=False):
    u=Uc(UC_ARCH_X86,UC_MODE_16);u.mem_map(0,0x100000)
    source=None
    if original:
        source=(ROOT/'analysis/pcplus-originals/PCPLUS-main-2.01.EXE').read_bytes();assert hashlib.sha256(source).hexdigest()==json.loads((ROOT/'reconstruction/program_notice/provenance.json').read_text())['original_sha256']
    for name,at,size in [('core',0x427f,190),('strlen',0x8d18,27),('seconds',0x3323,11),('clock',0x778c,33)]:
        body=source[0x1200+at:0x1200+at+size] if source else (OUT/(name+'.bin')).read_bytes();assert len(body)==size;u.mem_write(0x10000+at,body)
    u.mem_write(0x30000,bytes((i*13+7)&255 for i in range(65536)))
    u.mem_write(0x34000,b'A'*length+b'\0');u.mem_write(0x31f76,struct.pack('<H',0x70))
    for reg,value in [(UC_X86_REG_CS,0x1000),(UC_X86_REG_DS,0x3000),(UC_X86_REG_SS,0x3000),(UC_X86_REG_SP,0xf000),(UC_X86_REG_BP,0x9876),(UC_X86_REG_SI,0x1357),(UC_X86_REG_DI,0x2468),(UC_X86_REG_BX,0x4000),(UC_X86_REG_EFLAGS,0x202)]:u.reg_write(reg,value)
    args=[kind,0x4000] if entry==0x429a else [0x4000] if entry==0x4288 else []
    u.mem_write(0x3f000,struct.pack('<'+'H'*(1+len(args)),0x200,*args))
    before=bytes(u.mem_read(0x30000,65536));events=[];times=iter(seconds);last=seconds[-1];polls=iter(key);clock_count=0
    def words(n):return struct.unpack('<'+'H'*n,bytes(u.mem_read(0x30000+u.reg_read(UC_X86_REG_SP)+2,n*2)))
    def ret(pop=0):
        sp=u.reg_read(UC_X86_REG_SP);ip=struct.unpack('<H',bytes(u.mem_read(0x30000+sp,2)))[0];u.reg_write(UC_X86_REG_SP,sp+2+pop);u.reg_write(UC_X86_REG_IP,ip)
    def interrupt(cpu,number,_):
        nonlocal last,clock_count
        assert number==0x21 and cpu.reg_read(UC_X86_REG_AX)>>8==0x2c
        last=next(times,last);clock_count+=1;cpu.reg_write(UC_X86_REG_CX,0x1234);cpu.reg_write(UC_X86_REG_DX,last<<8|99)
    def boundary(cpu,address,size,_):
        at=address-0x10000
        if at in (0x376d,0x3778):events.append(('bell' if at==0x376d else 'tone',));ret()
        elif at==0x3fc7:
            events.append(('save',*words(1)));cpu.reg_write(UC_X86_REG_AX,0x1234);cpu.reg_write(UC_X86_REG_DX,0x5678);ret()
        elif at==0x6bf0:events.append(('write',*words(3)));ret(6)
        elif at==0x4015:events.append(('restore',*words(3)));ret()
        elif at==0x6530:cpu.reg_write(UC_X86_REG_AX,next(polls,0));ret()
        elif at==0x64fe:events.append(('read',));cpu.reg_write(UC_X86_REG_AX,0x1c0d);ret()
    u.hook_add(UC_HOOK_INTR,interrupt);u.hook_add(UC_HOOK_CODE,boundary)
    u.emu_start(0x10000+entry,0x10200,count=20000)
    returned=u.reg_read(UC_X86_REG_IP)==0x200
    if returned:assert [u.reg_read(r) for r in REGS]==[0x9876,0x1357,0x2468,0x3000,0x3000]
    after=bytes(u.mem_read(0x30000,65536))
    for lo,hi in [(0,0x330e),(0x3310,0x3312),(0x3314,0x8f02),(0x8f0a,0xef00),(0xf020,65536)]:assert before[lo:hi]==after[lo:hi]
    center=(40-length//2)&65535
    assert struct.unpack_from('<H',after,0x330e)[0]==(center-3)&65535
    assert struct.unpack_from('<H',after,0x3312)[0]==(center+length+2)&65535
    assert events[:3]==[('tone' if entry==0x4288 or entry==0x429a and kind==0 else 'bell',),('save',0x330c),('write',0x4000,0x70,center|0xa00)]
    if returned:
        assert events[-1]==('restore',0x330c,0x1234,0x5678)
        assert u.reg_read(UC_X86_REG_SP)==0xf002+len(args)*2
    else:assert not any(e[0]=='restore' for e in events)
    return dict(returned=returned,events=events,clock_calls=clock_count,descriptor=after[0x330c:0x3316].hex())
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--original',action='store_true');a=p.parse_args();rows=[]
    policies=[('immediate',[1,1],[0]),('transient',[1,0],[0]),('timeout',[],[58,58,59,59,0,0,1,1]),('backwards',[],[3,2,2,1,1,0,0]),('stopped-clock',[],[12])]
    for entry,length,kind,(policy,keys,seconds) in itertools.product([0x427f,0x4288,0x429a],[0,1,2,31,73,74,75,80,81,160,511],[0,1,0x100],policies):
        result=case(entry,length,kind,keys,seconds)
        assert result['returned']==(policy!='stopped-clock')
        assert sum(e[0]=='read' for e in result['events'])==(policy=='immediate')
        if a.original:assert result==case(entry,length,kind,keys,seconds,True)
        rows.append(dict(entry=hex(entry),length=length,kind=kind,policy=policy,**result))
    report=dict(passed=True,cases=rows,original_comparisons=len(rows) if a.original else 0,inputs={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),ROOT/'reconstruction/program_notice/provenance.json',ROOT/'reconstruction/program_notice/core.asm',ROOT/'build/program-notice/manifest.json']},scope=__doc__+' Real recovered strlen and DOS-time conversion execute. DOS21 time samples, screen save/draw/restore, sound and keyboard are modeled boundaries. Stopped-clock cases intentionally retain the native unbounded wait. No live UI/UART or whole PROGRAM acceptance.')
    (OUT/('original-checks.json' if a.original else 'checks.json')).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,cases=len(rows),original_comparisons=report['original_comparisons'])))
if __name__=='__main__':main()
