#!/usr/bin/env python3
"""Exact native numeric selection/token CPU and linked8086 DOS diagnostics.

No original is read unless --original is explicitly provided. Builtins, invalid
selector handling and byte/CRT IO are labeled fixture policies. Indexed bank
and frame reads retain unchecked native offset/EOF behavior in isolated memory.
"""
import argparse
import json
import os
from pathlib import Path
import random
import struct
import subprocess
from unicorn.x86_const import (UC_X86_REG_CS,UC_X86_REG_DS,UC_X86_REG_SS,UC_X86_REG_IP,
    UC_X86_REG_SP,UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI,UC_X86_REG_AX,UC_X86_REG_DX,UC_X86_REG_EFLAGS)
from check_aspect_flow import Machine as FlowMachine,CS,DS,STACK,STOP,TOKEN,BUFFER
from build_aspect_flow import UNITS as FLOW_UNITS,FILE_BASE,STACK_START,STACK_END,COPY,COPY_END
from build_aspect_operands import (ROOT,OUT,SHA,UNITS,ENTRIES,LOOKAHEAD,BANK_A,BANK_B,LONG_BANK,SYSTEM,BACKENDS,sha)

EXPECTED={'addresses':'837dc6adc3b2ecb8bd21262a26641768d8476c96cd2f9debdc407d1a0134b2cf',
 'predicates':'cf642a67b20e39f23082ca212a63e5effcee3d2980f1b0d39f54fd88d018753b',
 'numeric':'74db7d82604bae2f46594f183d6f013f49a68b09320548654dcf9c13fedde4da',
 'token':'2aee346fac99f7af7195d428924dcdf998fb7ff2843f4d3cf9c18662d30edf55'}


class Machine(FlowMachine):
    def __init__(self,images,data=b'',buffered=0):
        super().__init__(images,data,buffered)
        self.put(LOOKAHEAD,0)
        self.numeric_reverse={v:k for k,v in BACKENDS.items()}
        self.invalid_returns=True;self.invalids=0;self.builtin_index=None
        # Source-owned patterns, not original variable values. These address
        # ranges intentionally retain their native overlap and wrap behavior.
        for start,length,salt in ((BANK_A,512,19),(BANK_B,512,37),(LONG_BANK,1024,53),(SYSTEM,2048,71)):
            self.u.mem_write(DS*16+start,bytes((i*73+salt)&255 for i in range(length)))
    def read_byte(self):
        remaining=(self.word(TOKEN+2)-1)&65535;self.put(TOKEN+2,remaining)
        if remaining<0x8000:
            address=self.word(TOKEN);value=self.u.mem_read(DS*16+address,1)[0];self.put(TOKEN,address+1);return value
        self.calls.append('refill')
        if self.head>=len(self.data):self.put(TOKEN+6,self.word(TOKEN+6)|0x10);return 65535
        value=self.data[self.head];self.head+=1;self.put(TOKEN+2,0);self.put(TOKEN,BUFFER+self.head);return value
    def on_code(self,cpu,address,size,_):
        ip=address-CS*16
        if not hasattr(self,'numeric_reverse') or ip not in self.numeric_reverse:
            return super().on_code(cpu,address,size,_)
        name=self.numeric_reverse[ip];self.calls.append(name);sp=cpu.reg_read(UC_X86_REG_SP)
        ax=dx=cleanup=0
        if name=='byte':ax=self.read_byte()
        elif name.startswith('builtin'):
            index=self.word(sp+2);self.builtin_index=index;cleanup=2
            value=(index^0x7654) if name=='builtin_integer' else (0x89abcdef^index)
            ax=value&65535;dx=value>>16
        else:
            self.invalids+=1
            if not self.invalid_returns:self.aborted=True;cpu.emu_stop();return
            ax=0xccdd;dx=0xaabb
        cpu.reg_write(UC_X86_REG_AX,ax);cpu.reg_write(UC_X86_REG_DX,dx)
        cpu.reg_write(UC_X86_REG_IP,self.word(sp));cpu.reg_write(UC_X86_REG_SP,sp+2+cleanup)
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
        assert self.u.reg_read(UC_X86_REG_CS)==CS and self.u.reg_read(UC_X86_REG_DS)==self.u.reg_read(UC_X86_REG_SS)==DS
        assert not self.u.reg_read(UC_X86_REG_EFLAGS)&0x400
        for start,end,code in self.images:assert bytes(self.u.mem_read(CS*16+start,end-start))==code
        return self.u.reg_read(UC_X86_REG_AX)|(self.u.reg_read(UC_X86_REG_DX)<<16)
    def long(self,address):
        return self.word(address)|(self.word((address+2)&65535)<<16)
    def record(self):
        result=super().record();result.update(invalids=self.invalids,builtin_index=self.builtin_index,lookahead=self.word(LOOKAHEAD));return result


def suite(images):
    records=[]
    def done(m):records.append(m.record())
    rng=random.Random(0xa5c017)
    for token in list(range(256))+[0x7fff,0x8000,0xfffe,0xffff]+[rng.randrange(65536) for _ in range(128)]:
        m=Machine(images)
        for name,remainder in [('is_integer',1),('is_long',2),('is_float',3)]:assert m.invoke(name,token)&65535==int(token%10==remainder)
        done(m)
    for token in list(range(256))+[0x8000,0xffff]:
        for buffered in (0,1):
            m=Machine(images,b'\x98',buffered);m.put(LOOKAHEAD,token);value=m.invoke('next_token')&65535
            assert value==(token if token else 0x98) and m.word(LOOKAHEAD)==0
            assert m.position()==(0 if token else 1)
            assert m.calls.count('refill')==int(not token and not buffered);done(m)
    m=Machine(images);assert m.invoke('next_token')&65535==65535;done(m)
    selectors_int=(101,111,121,141,151,161,171,181)
    selectors_long=(112,122,142,152,162,172)
    for kind,selectors in [('read_integer',selectors_int),('read_long',selectors_long)]:
        for token in range(256):
            if token in selectors:continue
            for returns in (False,True):
                m=Machine(images,bytes([token]));m.invalid_returns=returns;value=m.invoke(kind)
                assert m.invalids==1 and m.aborted==(not returns)
                if returns:assert (value&65535 if kind=='read_integer' else value)==(0xccdd if kind=='read_integer' else 0xaabbccdd)
                done(m)
        for token in (0x8000,0xffff):
            m=Machine(images);m.put(LOOKAHEAD,token);m.invoke(kind);assert m.invalids==1 and m.word(LOOKAHEAD)==0;done(m)
    for token,base,shift,kind in [(101,BANK_A,1,'read_integer'),(141,BANK_B,1,'read_integer'),
                                  (121,SYSTEM,3,'read_integer'),(142,LONG_BANK,2,'read_long'),(122,SYSTEM,3,'read_long')]:
        for index in list(range(256))+[65535]:
            # Empty operand after a cached selector makes native byteEOF become
            # an uncheckedFFFF index. No original bank-capacity claim is made.
            data=bytes([index]) if index<256 else b''
            m=Machine(images,data);m.put(LOOKAHEAD,token)
            address=(base+((index<<shift)&65535))&65535
            expected=m.word(address) if kind=='read_integer' else m.long(address)
            value=m.invoke(kind)
            assert (value&65535 if kind=='read_integer' else value)==expected and not m.invalids;done(m)
    for token,kind in [(111,'read_integer'),(112,'read_long')]:
        for index in list(range(256))+[65535]:
            m=Machine(images,bytes([index]) if index<256 else b'');m.put(LOOKAHEAD,token)
            value=m.invoke(kind);expected=index^0x7654 if kind=='read_integer' else 0x89abcdef^index
            assert (value&65535 if kind=='read_integer' else value)==expected and m.builtin_index==index;done(m)
    for frame in (0,1,0x6000,0xffff):
        for offset in (0,1,2,81,0xffff):
            for name,sign in [('frame_plus',1),('frame_minus',-1)]:
                m=Machine(images,offset.to_bytes(2,'little'));m.set('frame',frame)
                assert m.invoke(name)&65535==(frame+sign*offset)&65535;done(m)
            for token,sign,kind in [(151,-1,'read_integer'),(161,1,'read_integer'),(152,-1,'read_long'),(162,1,'read_long')]:
                m=Machine(images,offset.to_bytes(2,'little'));m.put(LOOKAHEAD,token);m.set('frame',frame)
                address=(frame+sign*offset)&65535;expected=m.word(address) if kind=='read_integer' else m.long(address)
                value=m.invoke(kind);assert (value&65535 if kind=='read_integer' else value)==expected;done(m)
    for i in range(256):
        m=Machine(images,bytes([171,i,i^255]));assert m.invoke('read_integer')&65535==i|((i^255)<<8);done(m)
        m=Machine(images,bytes([181,i]));assert m.invoke('read_integer')&65535==i;done(m)
        value=0x89abcdef^(i*0x01010101);m=Machine(images,bytes([172])+value.to_bytes(4,'little'));assert m.invoke('read_long')==value;done(m)
    for size in range(5):
        m=Machine(images,b'\x11\x22\x33\x44'[:size]);m.put(LOOKAHEAD,172)
        expected=int.from_bytes((b'\x11\x22\x33\x44'[:size]+b'\xa5'*4)[:4],'little')
        assert m.invoke('read_long')==expected;done(m)
    for token in (171,181):
        m=Machine(images);m.put(LOOKAHEAD,token);assert m.invoke('read_integer')&65535==65535;done(m)
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
OPERANDS >RESULT.TXT
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
        subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(OUT/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=30)
    summary=(OUT/'DONE.TXT').read_text().strip()
    assert (OUT/'PASS.TXT').exists() and not (OUT/'FAIL.TXT').exists(),(OUT/'RESULT.TXT').read_text()
    assert summary.endswith('0 failures'),summary
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--original',type=Path);args=parser.parse_args()
    subprocess.run(['python3',str(ROOT/'standalone/build_aspect_operands.py')],check=True)
    images=[]
    for _,name,start,end in UNITS:
        code=(OUT/(name+'.bin')).read_bytes();assert sha(code)==EXPECTED[name];images.append((start,end,code))
    for _,name,start,end in FLOW_UNITS:images.append((start,end,(OUT/('flow-'+name+'.bin')).read_bytes()))
    images.extend([(STACK_START,STACK_END,(OUT/'stack.bin').read_bytes()),(COPY,COPY_END,(OUT/'copy.bin').read_bytes())])
    records=suite(images);optional=None
    if args.original:
        original=args.original.read_bytes();assert sha(original)==SHA
        native=[]
        for start,end,code in images:
            file_start=FILE_BASE+start if start!=COPY else 0x1200+COPY
            data=original[file_start:file_start+end-start];assert data==code;native.append((start,end,data))
        assert suite(native)==records
        optional=dict(original_sha256=SHA,exact_operand_bytes=sum(end-start for _,_,start,end in UNITS),paired_cpu_scenarios=len(records))
    summary=dos_test()
    report=dict(passed=True,cpu_scenarios=len(records),DOS_summary=summary,optional_original=optional,
                binary_sha256=sha((OUT/'OPERANDS.EXE').read_bytes()),units=EXPECTED,check_sha256=sha(Path(__file__).read_bytes()),
                inherited_checker_sha256=sha((ROOT/'standalone/check_aspect_flow.py').read_bytes()),
                original_inputs=[] if optional is None else [str(args.original)],
                scope='8native operand/token/address/predicate entries with actual flow/typed stack/copy. Source-owned banks and modeled builtin/invalid/byte/CRT callbacks. Allinteger/long selector paths, invalidtokens,uncheckedEOFindex/framewrap and shortDWORD exposure tested; no real builtin, float or full VM claim.')
    (OUT/('checks-native.json' if args.original else 'checks.json')).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
