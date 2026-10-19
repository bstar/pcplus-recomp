#!/usr/bin/env python3
"""Native ASPECT flow/operand CPU and linked8086 DOS callback diagnostics.

Optional private original ranges are compared only with explicit --original.
The typed stack and72-byte copy execute maintained native instructions. CRT IO,
error-return/stop and exit are explicitly source-owned fixture policies; real
DOS files, application abort/longjmp and the complete VM are outside this test.
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
from build_aspect_flow import (ROOT,OUT,SHA,UNITS,ENTRIES,FILE_BASE,BACKENDS,DATA,
    STACK_START,STACK_END,COPY,COPY_END,BASE,LENGTH,sha)

CS,DS,STACK,STOP,TOKEN,BUFFER=0x1000,0x3000,0xf000,0xf800,0x2000,0x3000
EXPECTED={
 'locals':'e2079db7562728ef7c528d663e2a86a40aa4456a63a490a89741e2053b68db86',
 'seek':'0a34c077a9ccca36a1dd58183f0ee5fdd969af8dd7cc393142dd05f3811dd962',
 'calls':'68223941e1d0a5a7bfb1a9c50acc41d3bc02ee812807bdbfd6b6b043644415c2',
 'readers':'dfa7447160db051ea69b4c0e0387a279b539fd0b5854622c9d0c01e236b6a628'}


class Machine:
    def __init__(self,images,data=b'',buffered=0):
        self.u=Uc(UC_ARCH_X86,UC_MODE_16);self.u.mem_map(0,0x100000)
        self.images=images
        self.u.mem_write(DS*16,b'\xa5'*65536)
        for start,end,code in images:
            assert len(code)==end-start
            self.u.mem_write(CS*16+start,code)
        for reg,value in [(UC_X86_REG_CS,CS),(UC_X86_REG_DS,DS),(UC_X86_REG_SS,DS),(UC_X86_REG_ES,0x4321),
                          (UC_X86_REG_SP,STACK),(UC_X86_REG_BP,0xabcd),(UC_X86_REG_SI,0x1357),
                          (UC_X86_REG_DI,0x2468),(UC_X86_REG_EFLAGS,2)]:self.u.reg_write(reg,value)
        for name,value in [('stream',TOKEN),('depth',0),('frame',0x2468),('local_count',0),('wait_gate',0),('stack_pointer',BASE)]:self.put(DATA[name],value)
        self.u.mem_write(DS*16+DATA['locals'],bytes(36))
        self.data=bytearray(data);assert 0<=buffered<=len(data)
        if data:self.u.mem_write(DS*16+BUFFER,bytes(data))
        self.head=buffered;self.put(TOKEN,BUFFER);self.put(TOKEN+2,buffered);self.put(TOKEN+6,0)
        self.seek_failure=False;self.tell_failure=False;self.error_returns=False
        self.calls=[];self.last_seek=None;self.exits=0;self.errors=0
        self.reached=False;self.aborted=False
        self.reverse={v:k for k,v in BACKENDS.items()}
        self.u.hook_add(UC_HOOK_CODE,self.on_code);self.u.hook_add(UC_HOOK_INTR,self.interrupt)

    def put(self,offset,value):self.u.mem_write(DS*16+offset,struct.pack('<H',value&65535))
    def word(self,offset):return struct.unpack('<H',self.u.mem_read(DS*16+offset,2))[0]
    def get(self,name):return self.word(DATA[name])
    def set(self,name,value):self.put(DATA[name],value)
    def position(self):
        remaining=self.word(TOKEN+2);remaining=remaining if remaining<0x8000 else remaining-65536
        return self.head-max(0,remaining)
    def set_position(self,position):
        self.head=position;self.put(TOKEN,BUFFER+position);self.put(TOKEN+2,0)
    def on_code(self,cpu,address,size,_):
        ip=address-CS*16;assert cpu.reg_read(UC_X86_REG_CS)==CS
        if ip==STOP:self.reached=True;cpu.emu_stop();return
        if any(start<=ip<end for start,end,_ in self.images):return
        assert ip in self.reverse,hex(ip)
        name=self.reverse[ip];sp=cpu.reg_read(UC_X86_REG_SP)
        args=[self.word(sp+i) for i in (2,4,6,8)]
        self.calls.append(name);ax=dx=cleanup=0
        if name=='refill':
            assert args[0]==TOKEN
            if self.head>=len(self.data):
                ax=65535;self.put(TOKEN+6,self.word(TOKEN+6)|0x10)
            else:
                ax=self.data[self.head];self.head+=1;self.put(TOKEN+2,0);self.put(TOKEN,BUFFER+self.head)
        elif name=='fread':
            dest,size_,count,token=args;assert (size_,count,token)==(4,1,TOKEN)
            position=self.position();data=self.data[position:position+4]
            if data:self.u.mem_write(DS*16+dest,bytes(data))
            self.set_position(position+len(data));ax=len(data)//4
            if len(data)<4:self.put(TOKEN+6,self.word(TOKEN+6)|0x10)
        elif name=='fseek':
            token,low,high,origin=args;assert token==TOKEN and origin==0
            offset=low|(high<<16);self.last_seek=offset
            if self.seek_failure or offset>len(self.data):ax=65535
            else:self.set_position(offset);self.put(TOKEN+6,0)
        elif name=='ftell':
            assert args[0]==TOKEN
            value=0xffffffff if self.tell_failure else self.position();ax=value&65535;dx=value>>16
        elif name=='exit':self.exits+=1
        elif name=='error':
            assert args[0]==105;self.errors+=1
            if not self.error_returns:self.aborted=True;cpu.emu_stop();return
            cleanup=2
        cpu.reg_write(UC_X86_REG_AX,ax);cpu.reg_write(UC_X86_REG_DX,dx)
        cpu.reg_write(UC_X86_REG_IP,self.word(sp));cpu.reg_write(UC_X86_REG_SP,sp+2+cleanup)
    def interrupt(self,cpu,number,_):raise AssertionError(f'Unexpected interrupt {number}')
    def invoke(self,name,*args):
        self.reached=self.aborted=False
        self.u.mem_write(DS*16+STACK-128,b'\xa5'*144)
        self.u.mem_write(DS*16+STACK,struct.pack('<'+'H'*(len(args)+1),STOP,*args))
        for reg,value in [(UC_X86_REG_SP,STACK),(UC_X86_REG_BP,0xabcd),(UC_X86_REG_SI,0x1357),(UC_X86_REG_DI,0x2468)]:self.u.reg_write(reg,value)
        self.u.emu_start(CS*16+ENTRIES[name],0,count=100000)
        if not self.aborted:
            assert self.reached and self.u.reg_read(UC_X86_REG_SP)==STACK+2+len(args)*2
            assert self.u.reg_read(UC_X86_REG_BP)==0xabcd
            assert self.u.reg_read(UC_X86_REG_SI)==0x1357 and self.u.reg_read(UC_X86_REG_DI)==0x2468
        assert self.u.reg_read(UC_X86_REG_DS)==self.u.reg_read(UC_X86_REG_SS)==DS
        assert not self.u.reg_read(UC_X86_REG_EFLAGS)&0x400
        for start,end,code in self.images:assert bytes(self.u.mem_read(CS*16+start,end-start))==code
        return self.u.reg_read(UC_X86_REG_AX)|(self.u.reg_read(UC_X86_REG_DX)<<16)
    def record(self):
        return dict(calls=self.calls,position=self.position(),last_seek=self.last_seek,
                    depth=self.get('depth'),frame=self.get('frame'),pointer=self.get('stack_pointer'),
                    local_count=self.get('local_count'),exits=self.exits,errors=self.errors,aborted=self.aborted,
                    values_sha256=sha(bytes(self.u.mem_read(DS*16+BASE,LENGTH+128))))


def suite(images):
    records=[]
    def done(m):records.append(m.record())
    for initial in (0,1,0x7fff,0x8000,0xffff):
        m=Machine(images);m.set('wait_gate',initial);m.invoke('gate_decrement');assert m.get('wait_gate')==(initial-1)&65535
        m.invoke('gate_increment');assert m.get('wait_gate')==initial
        m.set('wait_gate',65535);m.invoke('gate_increment');assert m.get('wait_gate')==0;done(m)
    for length in range(7):
        data=bytes((i*73+19)&255 for i in range(length))
        for buffered in range(min(length,2)+1):
            m=Machine(images,data,buffered);value=m.invoke('read_word')&65535
            expected=(data[0] if length else 65535)|((data[1] if length>1 else 255)<<8)
            assert value==expected
            assert m.calls.count('refill')==max(0,2-buffered);done(m)
    for length in range(9):
        data=bytes((i*73+19)&255 for i in range(length))
        for buffered in range(min(length,4)+1):
            m=Machine(images,data,buffered);value=m.invoke('read_dword')
            expected=int.from_bytes((data[:4]+b'\xa5'*4)[:4],'little')
            assert value==expected and m.calls==['fread'];assert m.position()==min(length,4);done(m)
    for offset in (0,1,7,127,128,0x80000000,0xffffffff):
        for fail in (False,True):
            m=Machine(images,bytes(128));m.set_position(3);m.seek_failure=fail
            value=m.invoke('seek',offset&65535,offset>>16)&65535
            assert m.last_seek==offset and m.position()==(3 if fail or offset>128 else offset)
            assert value==(65535 if fail or offset>128 else 0) and m.get('depth')==0;done(m)
    for target in range(64):
        for seek_failure,tell_failure in ((False,False),(True,False),(False,True)):
            m=Machine(images,bytes(128));m.set_position(7);m.seek_failure=seek_failure;m.tell_failure=tell_failure
            m.invoke('call',target,0);assert m.get('depth')==1 and m.get('stack_pointer')==BASE+4
            expected=0xffffffff if tell_failure else 7
            assert bytes(m.u.mem_read(DS*16+BASE,4))==expected.to_bytes(4,'little')
            assert m.position()==(7 if seek_failure else target)
            m.invoke('return');assert m.get('depth')==0 and m.get('stack_pointer')==BASE
            assert m.last_seek==expected
            assert m.position()==(7 if seek_failure else target if tell_failure else 7)
            m.invoke('return');assert m.exits==1;done(m)
        m=Machine(images,target.to_bytes(4,'little')+bytes(124));m.invoke('call_operand')
        assert m.position()==target and m.get('depth')==1
        assert bytes(m.u.mem_read(DS*16+BASE,4))==b'\4\0\0\0'
        m.invoke('return');assert m.position()==4;done(m)
    for levels in range(1,9):
        m=Machine(images,bytes(128));m.set_position(7)
        for level in range(levels):m.invoke('call',20+level,0)
        assert m.get('depth')==levels and m.get('stack_pointer')==BASE+levels*4
        for level in range(levels-1,-1,-1):
            m.invoke('return');assert m.position()==(7 if level==0 else 19+level)
        assert m.get('stack_pointer')==BASE;done(m)
    for target in range(12,32):
        data=bytearray(128);data[:4]=target.to_bytes(4,'little');data[target:target+2]=b'\x11\0'
        m=Machine(images,data);m.invoke('call_framed')
        assert m.get('depth')==1 and m.get('frame')==BASE+6 and m.get('stack_pointer')==BASE+6
        assert bytes(m.u.mem_read(DS*16+BASE,6))==b'\4\0\0\0\x68\x24'
        m.invoke('reserve_locals');assert m.get('stack_pointer')==BASE+23
        m.invoke('return_framed');assert (m.get('frame'),m.get('depth'),m.get('stack_pointer'),m.position())==(0x2468,0,BASE,4)
        done(m)
        m=Machine(images,data);m.invoke('jump');assert m.position()==target and m.get('depth')==0 and m.get('stack_pointer')==BASE;done(m)
    for frame in (0,1,0x8000,0xffff):
        m=Machine(images);m.set('frame',frame);m.invoke('push_frame')
        assert m.get('frame')==BASE+2 and m.get('stack_pointer')==BASE+2 and m.word(BASE)==frame;done(m)
    for pointer in (BASE,BASE+LENGTH-1,BASE+LENGTH,0xfffe):
        for size in (0,1,2,81,0xffff):
            for returns in (False,True):
                m=Machine(images,size.to_bytes(2,'little'));m.set('stack_pointer',pointer);m.error_returns=returns
                m.invoke('reserve_locals');next_pointer=(pointer+size)&65535
                assert m.get('stack_pointer')==next_pointer
                assert m.errors==int(next_pointer>BASE+LENGTH)
                assert m.aborted==(bool(m.errors) and not returns);done(m)
    for depth in (0,1,2,0xffff):
        for flags in range(8):
            m=Machine(images);m.set('depth',depth);m.set('local_count',3)
            depths=(1,2,0xffff)
            for i,d in enumerate(depths):m.put(DATA['locals']+i*12,int(bool(flags&(1<<i))));m.put(DATA['locals']+i*12+4,d)
            count=3-sum(depth<d for d in depths);m.invoke('cleanup_locals')
            assert m.get('local_count')==count&65535
            for i,d in enumerate(depths):
                assert m.word(DATA['locals']+i*12)==(0 if depth<d else int(bool(flags&(1<<i))))
                assert m.word(DATA['locals']+i*12+4)==d
            m.invoke('cleanup_locals');assert m.get('local_count')==(2*count-3)&65535;done(m)
    for depth in (0,1,2,0xffff):
        m=Machine(images,bytes(128));m.set('depth',depth);m.set('stack_pointer',BASE+4)
        m.u.mem_write(DS*16+BASE,(17).to_bytes(4,'little'));m.set('local_count',3)
        for i in range(3):m.put(DATA['locals']+i*12,1);m.put(DATA['locals']+i*12+4,i+1)
        m.invoke('return')
        if depth==0:assert m.exits==1 and m.get('stack_pointer')==BASE+4
        else:
            assert m.get('depth')==depth-1 and m.get('stack_pointer')==BASE and m.position()==17
            assert m.get('local_count')==3-sum(depth-1<d for d in (1,2,3))
        done(m)
    m=Machine(images,bytes(128));m.set('depth',65535);m.invoke('call',4,0)
    assert m.get('depth')==0;m.invoke('return');assert m.exits==1 and m.get('stack_pointer')==BASE+4;done(m)
    return records


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
FLOW >RESULT.TXT
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
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--original',type=Path)
    args=parser.parse_args()
    subprocess.run(['python3',str(ROOT/'standalone/build_aspect_flow.py')],check=True)
    images=[]
    for _,name,start,end in UNITS:
        code=(OUT/(name+'.bin')).read_bytes();assert sha(code)==EXPECTED[name];images.append((start,end,code))
    images.extend([(STACK_START,STACK_END,(OUT/'stack.bin').read_bytes()),(COPY,COPY_END,(OUT/'copy.bin').read_bytes())])
    records=suite(images);optional=None
    if args.original:
        original=args.original.read_bytes();assert sha(original)==SHA
        native=[]
        for start,end,code in images:
            file_start=FILE_BASE+start if start!=COPY else 0x1200+COPY
            data=original[file_start:file_start+end-start];assert data==code
            native.append((start,end,data))
        assert suite(native)==records
        optional=dict(original_sha256=SHA,exact_flow_bytes=sum(end-start for _,_,start,end in UNITS),
                      exact_stack_bytes=STACK_END-STACK_START,exact_copy_bytes=COPY_END-COPY,paired_cpu_scenarios=len(records))
    summary=dos_test()
    report=dict(passed=True,cpu_scenarios=len(records),DOS_summary=summary,optional_original=optional,
                binary_sha256=sha((OUT/'FLOW.EXE').read_bytes()),units=EXPECTED,check_sha256=sha(Path(__file__).read_bytes()),
                original_inputs=[] if optional is None else [str(args.original)],
                scope='14native flow/read entries plus actual typed stack/copy. Modeled CRT/error/exit only; short reads retain stack bytes, failed IO is unchecked, gate/depth/pointer/local-count wrap preserved. No full VM or realfile/longjmp claim.')
    (OUT/('checks-native.json' if args.original else 'checks.json')).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
