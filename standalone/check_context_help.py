#!/usr/bin/env python3
"""Run the exact help producer; resolver/formatter/PROGRAM are explicit models."""
import argparse,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_CODE
from unicorn.x86_const import *
from build_context_help import ROOT,sha

class Machine:
    def __init__(self,build,original=False):
        self.u=Uc(UC_ARCH_X86,UC_MODE_16);self.u.mem_map(0,0x100000)
        proof=json.loads((build/'manifest.json').read_text())
        image=None
        if original:
            path=ROOT/'analysis/pcplus-originals/PCPLUS-main-2.01.EXE'
            assert sha(path)==json.loads((ROOT/'reconstruction/context_help/provenance.json').read_text())['original_sha256']
            image=path.read_bytes()
        for unit in proof['units']:
            flat=(build/(Path(unit['file']).stem+'.bin')).read_bytes()
            data=image[unit['file_offset']:unit['file_offset']+unit['bytes']] if original else flat
            assert data==flat
            self.u.mem_write(0x10000+unit['start'],data)
        self.u.hook_add(UC_HOOK_CODE,self.code)
    def word(self,at):return int.from_bytes(self.u.mem_read(at,2),'little')
    def string(self,offset):
        data=bytes(self.u.mem_read(self.base+offset,100))
        assert b'\0' in data
        return data.split(b'\0',1)[0]
    def code(self,u,at,size,data):
        if at==0x1ff00:self.returned=True;u.emu_stop();return
        if at not in (0x1353d,0x182b6,0x1433d):return
        sp=u.reg_read(UC_X86_REG_SP);stack=self.base+sp
        arg=lambda n:self.word(stack+2+n*2)
        if at==0x1353d:
            key=self.string(arg(0));self.keys.append(key)
            assert key==([b'PCPLUS.HLP',b'PCHELP.RTE'][len(self.keys)-1])
            value=self.path if len(self.keys)==1 else b'HELP.EXE'
            u.mem_write(self.base+0x6000,value+b'\0');result=0x6000
        elif at==0x182b6:
            assert self.string(arg(1))==b' PCHELP %lu'
            pointer=arg(2)|(arg(3)<<16)
            assert pointer==(self.ds<<16)|((self.sp-26)&65535)
            tail=b' PCHELP '+str(pointer).encode();assert len(tail)+1<=30
            u.mem_write(self.base+arg(0),tail+b'\0');result=len(tail)
        else:
            assert len(self.keys)==2 and self.string(arg(0))==b'HELP.EXE'
            tail=self.string(arg(1));pointer=int(tail[8:]);off=pointer&65535
            assert tail==b' PCHELP '+str(pointer).encode()
            assert [arg(i) for i in (2,3,4)]==[0,0,0]
            raw=bytes(u.mem_read(self.base+off,18));words=struct.unpack('<9H',raw)
            assert words==(self.sp-122,0x24b8,self.topic,*self.ui)
            assert self.string(words[0])==self.path
            assert self.string(words[1])==b'PROCOMM PLUS'
            self.record=(raw,tail,self.string(words[0]),self.string(words[1]))
            result=self.result
        u.reg_write(UC_X86_REG_AX,result)
        u.reg_write(UC_X86_REG_SP,sp+2);u.reg_write(UC_X86_REG_IP,self.word(stack))
    def run(self,ds,sp,topic,path,ui,result):
        self.ds=ds;self.base=ds*16;self.sp=sp;self.topic=topic;self.path=path;self.ui=ui;self.result=result
        self.keys=[];self.returned=False;self.record=None;u=self.u
        u.mem_write(self.base+sp-256,b'\xa5'*300)
        u.mem_write(self.base+sp-2,b'\0\xff')
        for at,value in ((0x24ac,b'PCPLUS.HLP\0'),(0x24b8,b'PROCOMM PLUS\0'),(0x24c6,b' PCHELP %lu\0'),(0x24d2,b'PCHELP.RTE\0')):u.mem_write(self.base+at,value)
        for at,value in zip((0x397a,0x1d3e,0x1d32,0x1d34,0x1d38,0x2068,0x206a),(topic,*ui)):u.mem_write(self.base+at,struct.pack('<H',value))
        for reg,value in ((UC_X86_REG_CS,0x1000),(UC_X86_REG_DS,ds),(UC_X86_REG_SS,ds),(UC_X86_REG_ES,0xbeef),(UC_X86_REG_SP,sp-2),(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678),(UC_X86_REG_EFLAGS,0x202)):u.reg_write(reg,value)
        u.emu_start(0x157ae,0x20000,count=10000)
        assert self.returned and self.record
        assert [u.reg_read(r) for r in (UC_X86_REG_AX,UC_X86_REG_SP,UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI,UC_X86_REG_DS,UC_X86_REG_SS,UC_X86_REG_ES)]==[result,sp,0xbabe,0x1234,0x5678,ds,ds,ds]
        assert u.reg_read(UC_X86_REG_EFLAGS)&0x600==0x200
        assert bytes(u.mem_read(self.base+sp,44))==b'\xa5'*44
        assert bytes(u.mem_read(self.base+sp-256,100))==b'\xa5'*100
        return self.record

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--original',action='store_true');a=p.parse_args();build=a.build.resolve()
    manifest=json.loads((build/'manifest.json').read_text())
    for name,digest in manifest['sources'].items():assert sha(ROOT/name)==digest,name
    machines=[Machine(build)]+([Machine(build,True)] if a.original else [])
    profiles=((0,0,0,0,0,0),(1,7,15,0x70,8,16),(0xffff,0x8000,0x1234,0xabcd,0,0xffff))
    count=0
    for values in itertools.product((0x2000,0x5000,0x9000),(0xf000,0xf001),(0,19,41,45,46,47,0x8000,0xffff),(b'',b'A',b'X'*63,b'Y'*65),profiles,(0,5,0xffff)):
        records=[m.run(*values) for m in machines];assert all(r==records[0] for r in records);count+=1
    report=dict(passed=True,cases=count,original_comparisons=count if a.original else 0,checker_sha256=sha(Path(__file__)),manifest_sha256=sha(build/'manifest.json'),scope='Actual132-byte producer,50-byte strcpy and3-byte getDS. Resolver, formatter and PROGRAM are modeled boundaries; no original executable or analysis image executed. Native unbounded path copy tested only through65 chars. No production help UI, UART or physical acceptance.')
    (build/('cpu-original.json' if a.original else 'cpu.json')).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))

if __name__=='__main__':main()
