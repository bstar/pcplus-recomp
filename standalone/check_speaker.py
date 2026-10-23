#!/usr/bin/env python3
"""Replay actual banked speaker code, modeled ports and instruction abandonments."""
import hashlib,json,re,struct
from pathlib import Path
from unicorn import UC_HOOK_CODE,UC_HOOK_INSN
from unicorn.x86_const import *
from dos_image import DosImage
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/speaker'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
class Machine:
    def __init__(self,port=0xa0):
        self.image=DosImage(OUT/'SPEAKER.EXE',OUT/'SPEAKER.map');self.u=self.image.uc;self.port=port;self.events=[];self.trace=[];self.cut=None
        self.entries={n:(int(s,16)+0x1000,int(o,16)) for s,o,n in re.findall(r'^\s*([0-9a-f]{4}):([0-9a-f]{4,8})[*+]?\s+(\w+)\s*$',(OUT/'SPEAKER.map').read_text(),re.I|re.M)}
        h=struct.unpack_from('<14H',self.image.image);self.sp=(self.image.base+h[7]*16+h[8])-self.image.data_base-64;assert 1024<self.sp<65536
        self.u.hook_add(UC_HOOK_CODE,self.code);self.u.hook_add(UC_HOOK_INSN,self.read,None,1,0,UC_X86_INS_IN);self.u.hook_add(UC_HOOK_INSN,self.write,None,1,0,UC_X86_INS_OUT)
        self.clock(100)
    def clock(self,value):self.u.mem_write(0x46c,struct.pack('<I',value))
    def read(self,u,port,size,user):assert port==0x61 and size==1;return self.port
    def write(self,u,port,size,value,user):
        assert port in (0x43,0x42,0x61) and size==1
        assert self.image.get('_speaker_owned')==1,'Hardware write without published cleanup owner'
        self.events.append((port,value))
        if port==0x61:self.port=value
    def code(self,u,address,size,user):
        if address==0x90100:self.returned=True;u.emu_stop();return
        if self.cut is not None and len(self.trace)==self.cut:self.abandoned=True;u.emu_stop();return
        self.trace.append(address)
    def call(self,name,args=(),cut=None,flags=0x202,foreign=False):
        seg,off=self.entries[name];u=self.u
        for reg,value in [(UC_X86_REG_CS,seg),(UC_X86_REG_DS,self.image.ds+1 if foreign else self.image.ds),(UC_X86_REG_SS,self.image.ds),(UC_X86_REG_SP,self.sp),(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678),(UC_X86_REG_EFLAGS,flags)]:u.reg_write(reg,value)
        u.mem_write(self.image.data_base+self.sp,struct.pack('<'+'H'*(2+len(args)),0x100,0x9000,*args))
        self.trace=[];self.cut=cut;self.returned=self.abandoned=False;u.emu_start(seg*16+off,0,count=10000)
        assert self.returned or self.abandoned,name
        if self.returned:assert u.reg_read(UC_X86_REG_SP)==self.sp+4
        return u.reg_read(UC_X86_REG_AX)
    def start(self,cut=None):return self.call('_speaker_start',(220,3,1000,0),cut)
def main():
    checks=0;rows=[]
    def ck(value):
        nonlocal checks
        checks+=1;assert value,checks
    m=Machine();ck(m.start()==1 and m.port==0xa3);ck(m.image.get('_speaker_generation_word')==1);ck(m.call('_speaker_start',(440,4,1000,0))==3)
    ck(m.call('_speaker_poll')==1);m.clock(103);ck(m.call('_speaker_poll')==0 and m.port==0xa0 and not m.image.get('_speaker_owned'))
    ck(m.events==[(0x43,0xb6),(0x42,47),(0x42,21),(0x61,0xa3),(0x61,0xa0)])
    for hz in (0,1,18):
        m=Machine();ck(m.call('_speaker_start',(hz,3,1000,0))==2 and not m.events)
    for flags,foreign in [(2,False),(0x202,True)]:
        m=Machine();ck(m.call('_speaker_start',(220,3,1000,0),flags=flags,foreign=foreign)==4 and not m.events)
    m=Machine(0xa3);ck(m.start()==3 and not m.events);ck(m.call('_speaker_stop')==0 and m.port==0xa3 and not m.events)
    m=Machine();m.image.put('_speaker_generation_word',65535);ck(m.start()==1 and m.image.get('_speaker_generation_word')==1);ck(m.call('_speaker_stop')==0)
    for operation in ('_speaker_start','_speaker_poll','_speaker_stop'):
        full=Machine()
        if operation!='_speaker_start':ck(full.start()==1);full.clock(103)
        full.call(operation,(220,3,1000,0) if operation=='_speaker_start' else ())
        count=len(full.trace)
        for cut in range(count):
            m=Machine()
            if operation!='_speaker_start':ck(m.start()==1);m.clock(103)
            m.call(operation,(220,3,1000,0) if operation=='_speaker_start' else (),cut=cut);ck(m.abandoned)
            before=m.image.get('_speaker_owned');ck(m.call('_speaker_stop')==0 and m.port==0xa0 and m.image.get('_speaker_owned')==0)
            rows.append(dict(operation=operation,cut=cut,published_owner_before_cleanup=before,writes=m.events))
    r=dict(passed=True,checks=checks,abandonment_cases=len(rows),cases=rows,binary_sha256=sha(OUT/'SPEAKER.EXE'),checker_sha256=sha(Path(__file__)),loader_sha256=sha(ROOT/'standalone/dos_image.py'),scope=__doc__+' All product code executes, including actual port instructions and BIOS tick reads. Cuts model a caller already repairing DS=SS/IF and abandoning the frame, not actual asynchronous CPU/DOS/hardware faults.')
    (OUT/'checks.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(passed=True,checks=checks,abandonment_cases=len(rows))))
if __name__=='__main__':main()
