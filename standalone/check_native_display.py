#!/usr/bin/env python3
"""Execute exact display instructions with explicit BIOS/heap/port boundaries."""
import argparse,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_CODE,UC_HOOK_INTR,UC_HOOK_INSN
from unicorn.x86_const import *
from build_native_display import ROOT,OUT,CORE,sha


class Machine:
    def __init__(self,original=False):
        self.uc=Uc(UC_ARCH_X86,UC_MODE_16);self.uc.mem_map(0,0x100000)
        self.proof=json.loads((CORE/'provenance.json').read_text())
        image=None
        if original:
            path=ROOT/'analysis/pcplus-originals/PCPLUS-main-2.01.EXE';assert sha(path)==self.proof['original_sha256'];image=path.read_bytes()
        self.entries={}
        for unit in self.proof['units']:
            p=OUT/(Path(unit['file']).stem+'.bin')
            data=image[unit['file_offset']:unit['file_offset']+unit['bytes']] if original else p.read_bytes()
            self.uc.mem_write(0x10000+unit['start'],data);self.entries[Path(unit['file']).stem]=unit['start']
        self.uc.hook_add(UC_HOOK_CODE,self.code);self.uc.hook_add(UC_HOOK_INTR,self.interrupt)
        self.uc.hook_add(UC_HOOK_INSN,self.input,None,1,0,UC_X86_INS_IN)
        self.uc.hook_add(UC_HOOK_INSN,self.output,None,1,0,UC_X86_INS_OUT)
        self.reset()
    def reset(self):
        self.uc.mem_write(0x20000+0x7a66,bytes(46));self.events=[];self.fail=False;self.stuck=False;self.reads=0
    def put(self,at,value,size=2):self.uc.mem_write(0x20000+at,value.to_bytes(size,'little'))
    def get(self,at,size=2):return int.from_bytes(self.uc.mem_read(0x20000+at,size),'little')
    def word(self,at):return int.from_bytes(self.uc.mem_read(at,2),'little')
    def code(self,u,at,size,data):
        if at==0x1ff00:self.returned=True;u.emu_stop();return
        if at not in (0x1860f,0x185fc):return
        sp=u.reg_read(UC_X86_REG_SP);stack=0x20000+sp
        if at==0x1860f:
            self.events.append(('allocate',self.word(stack+2)))
            u.reg_write(UC_X86_REG_AX,0 if self.fail else 0x20);u.reg_write(UC_X86_REG_DX,0 if self.fail else 0x9000)
        else:self.events.append(('free',self.word(stack+2),self.word(stack+4)))
        u.reg_write(UC_X86_REG_SP,sp+2);u.reg_write(UC_X86_REG_IP,self.word(stack))
    def interrupt(self,u,number,data):
        assert number==0x10 and u.reg_read(UC_X86_REG_AH)==15
        u.reg_write(UC_X86_REG_AX,(self.columns<<8)|self.mode);u.reg_write(UC_X86_REG_BX,0)
    def input(self,u,port,size,data):
        assert port==0x3da and size==1
        self.reads+=1;self.events.append(('in',port))
        return 0 if self.stuck or self.reads%2 else 8
    def output(self,u,port,size,value,data):
        assert port==0x3d8 and size==1;self.events.append(('out',port,value))
    def call(self,name,args=(),limit=100000):
        u=self.uc;sp=0xf000
        for value in reversed(args):sp-=2;u.mem_write(0x20000+sp,struct.pack('<H',value))
        sp-=2;u.mem_write(0x20000+sp,b'\0\xff')
        for reg,value in [(UC_X86_REG_CS,0x1000),(UC_X86_REG_DS,0x2000),(UC_X86_REG_SS,0x2000),
                (UC_X86_REG_ES,0xbeef),(UC_X86_REG_SP,sp),(UC_X86_REG_BP,0xbabe),
                (UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678),(UC_X86_REG_EFLAGS,0x202)]:u.reg_write(reg,value)
        self.returned=False
        u.emu_start(0x10000+self.entries[name],0x20000,count=limit)
        if self.returned:
            assert u.reg_read(UC_X86_REG_SP)==0xf000
            assert [u.reg_read(r) for r in (UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI)]==[0xbabe,0x1234,0x5678]
            assert u.reg_read(UC_X86_REG_DS)==u.reg_read(UC_X86_REG_SS)==0x2000
            assert not u.reg_read(UC_X86_REG_EFLAGS)&0x400
        return u.reg_read(UC_X86_REG_AX),u.reg_read(UC_X86_REG_DX)
    def geometry(self,columns,rows,crt,legacy,snow,mode=3):
        self.reset();self.columns=columns;self.mode=mode
        self.put(0x7a66,legacy);self.put(0x7a78,0xa000);self.put(0x7a92,snow);self.put(0x7a72,0xabcd)
        self.uc.mem_write(0x460,bytes([7,6]));self.uc.mem_write(0x463,struct.pack('<H',crt));self.uc.mem_write(0x484,bytes([rows]))
        self.call('geometry');assert self.returned
        last=24 if rows<24 or (rows==29 and legacy) else rows
        total=(last+1)*columns*2&65535
        assert self.get(0x7a72)==0xab00|columns # Native low-byte-only column store.
        assert self.get(0x7a74)==last+1 and self.get(0x7a76,1)==mode
        assert self.get(0x7a7a)==columns*2 and self.get(0x7a7c)==total
        assert self.get(0x7a7e)==(columns-1)&65535 and self.get(0x7a80)==last
        assert self.get(0x7a82)==(total-columns*2)&65535
        assert self.get(0x7a85,1)==last and self.get(0x7a8c)==total//2
        assert self.get(0x7a88)==6 and self.get(0x7a8a)==7 # BDA CH start, CL end.
        assert self.get(0x7a86)==int(crt&255==0xb4)
        assert self.get(0x7a78)==(0xa000 if legacy else 0xb000 if crt&255==0xb4 else 0xb800)
        assert self.get(0x7a8e)==(0x3da if snow and not legacy and crt&255!=0xb4 else 0)
        return bytes(self.uc.mem_read(0x27a66,46))
    def copy(self,length,port,fail=False):
        self.reset();self.put(0x7a7c,length);self.put(0x7a8c,length//2);self.put(0x7a78,0xb800);self.put(0x7a8e,port)
        video=bytes((i*17+3)&255 for i in range(length));self.uc.mem_write(0xb8000,video)
        self.uc.mem_write(0x90020,b'\xa5'*(length+4));self.fail=fail
        pointer=self.call('snapshot');assert self.returned
        if fail:
            assert pointer==(0,0) and self.events==[('allocate',length)]
            assert bytes(self.uc.mem_read(0x90020,length+4))==b'\xa5'*(length+4)
        else:
            assert pointer==(0x20,0x9000)
            copied=length&~1
            assert bytes(self.uc.mem_read(0x90020,copied))==video[:copied]
            assert bytes(self.uc.mem_read(0x90020+copied,length+4-copied))==b'\xa5'*(length+4-copied)
            self.uc.mem_write(0xb8000,b'\x5a'*(length+4));self.call('restore',[0x20,0x9000]);assert self.returned
            assert bytes(self.uc.mem_read(0xb8000,copied))==video[:copied]
            assert bytes(self.uc.mem_read(0xb8000+copied,length+4-copied))==b'\x5a'*(length+4-copied)
            assert self.events[-1]==('free',0x20,0x9000)
            assert [e for e in self.events if e[0]=='out']==([('out',0x3d8,0x25),('out',0x3d8,0x2d)]*2 if port else [])
        return pointer,self.events


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--original',action='store_true');args=parser.parse_args()
    machines=[Machine()]+([Machine(True)] if args.original else []);count=0
    rows=set(itertools.product((0,1,40,80,132,255),(0,23,24,25,29,42,49,59,255),(0x3b4,0x3d4),(0,1),(0,1),(3,)))
    rows.update((80,row,0x3d4,0,0,3) for row in range(256))
    rows.update((80,24,0x3d4,0,0,mode) for mode in range(256))
    for values in sorted(rows):
        results=[m.geometry(*values) for m in machines];assert all(v==results[0] for v in results);count+=1
    for values in itertools.product((0,2,1999,2000,4000,8000,16000),(0,0x3da),(False,True)):
        results=[m.copy(*values) for m in machines];assert all(v==results[0] for v in results);count+=1
    for m in machines:
        m.reset();m.put(0x7a8e,0x3da);m.stuck=True;m.call('snow_disable',limit=2000)
        assert not m.returned and not any(e[0]=='out' for e in m.events)
    count+=1
    report=dict(passed=True,cases=count,original_comparisons=count if args.original else 0,
        checker_sha256=sha(Path(__file__)),manifest_sha256=sha(OUT/'manifest.json'),
        scope='Actual native geometry/copy/snow instructions. BIOS/heap/port are declared scalar recorders. No actual DOS or physical CGA claim.')
    (OUT/('cpu-original.json' if args.original else 'cpu.json')).write_text(json.dumps(report,indent=2)+'\n')
    print('Native display CPU:',count,'source cases;',report['original_comparisons'],'original comparisons PASS')


if __name__=='__main__':main()
