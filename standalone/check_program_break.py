#!/usr/bin/env python3
"""Execute recovered break routines with explicit modeled DOS vector services."""
import argparse
import hashlib
import itertools
import json
import struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_16, UC_HOOK_INTR
from unicorn.x86_const import *

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/program-break'
PROOF=json.loads((ROOT/'reconstruction/program_break/provenance.json').read_text())


class Machine:
    def __init__(self, original, flag):
        self.uc=Uc(UC_ARCH_X86,UC_MODE_16)
        self.uc.mem_map(0,0x100000)
        source=None
        if original:
            source=(ROOT/'analysis/pcplus-originals/PCPLUS-main-2.01.EXE').read_bytes()
            assert hashlib.sha256(source).hexdigest()==PROOF['source_sha256']
        for unit in PROOF['units']:
            data=source[unit['file_offset']:unit['file_offset']+unit['bytes']] if original else (OUT/(Path(unit['file']).stem+'.bin')).read_bytes()
            self.uc.mem_write(0x10000+unit['start'],data)
        self.uc.mem_write(0x30000,bytes((i*37+19)&255 for i in range(65536)))
        self.vectors={0x1b:(0x1234,0x2345),0x23:(0x4567,0x5678)}
        self.flag=flag
        self.calls=[]
        self.uc.hook_add(UC_HOOK_INTR,self.interrupt)

    def interrupt(self, u, number, _):
        assert number==0x21
        ax=u.reg_read(UC_X86_REG_AX);al=ax&255;ah=ax>>8
        dx=u.reg_read(UC_X86_REG_DX);ds=u.reg_read(UC_X86_REG_DS)
        self.calls.append([ax,ds,dx])
        if ax==0x3300:u.reg_write(UC_X86_REG_DX,(dx&0xff00)|self.flag)
        elif ax==0x3301:self.flag=dx&255
        elif ah==0x35:
            off,seg=self.vectors[al];u.reg_write(UC_X86_REG_BX,off);u.reg_write(UC_X86_REG_ES,seg)
        elif ah==0x25:self.vectors[al]=(dx,ds)
        else:raise AssertionError(hex(ax))

    def call(self, entry, argument=None):
        u=self.uc
        for register,value in [(UC_X86_REG_CS,0x1000),(UC_X86_REG_DS,0x3000),(UC_X86_REG_SS,0x3000),
            (UC_X86_REG_SP,0xf000),(UC_X86_REG_BP,0x9876),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678),
            (UC_X86_REG_ES,0x2222),(UC_X86_REG_EFLAGS,0x602)]:u.reg_write(register,value)
        u.mem_write(0x3f000,struct.pack('<H',0x200)+(struct.pack('<H',argument) if argument is not None else b''))
        before=bytes(u.mem_read(0x30000,65536))
        u.emu_start(0x10000+entry,0x10200,count=300)
        assert u.reg_read(UC_X86_REG_IP)==0x200
        assert u.reg_read(UC_X86_REG_SP)==0xf002+(2 if argument is not None else 0)
        assert [u.reg_read(r) for r in (UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI,UC_X86_REG_DS,UC_X86_REG_SS)]==[0x9876,0x1234,0x5678,0x3000,0x3000]
        assert u.reg_read(UC_X86_REG_EFLAGS)&0x400
        after=bytes(u.mem_read(0x30000,65536))
        assert before[:0x7ab6]==after[:0x7ab6] and before[0x7abf:0xefe0]==after[0x7abf:0xefe0] and before[0xf020:]==after[0xf020:]
        return after


def case(original, options, initial, child):
    m=Machine(original,initial)
    saved=dict(m.vectors)
    after=m.call(0x7508,options)
    expected=initial if options&255 else 255
    assert after[0x7ab6:0x7abf]==struct.pack('<HHHHB',*saved[0x1b],*saved[0x23],expected)
    assert m.vectors=={0x1b:(0x7f90,0x1000),0x23:(0x7f90,0x1000)}
    assert m.flag==(0 if options&255 else initial)
    m.vectors={0x1b:(1,2),0x23:(3,4)};m.flag=child
    restored=m.call(0x758a)
    assert m.vectors==saved and m.flag==(1 if expected==1 else child)
    assert after[:0xefe0]==restored[:0xefe0]
    return dict(vectors=m.vectors,flag=m.flag,state=restored[0x7ab6:0x7abf].hex(),calls=m.calls)


def main(args):
    cases=[]
    for option,initial,child in itertools.product([0,1,2,0x100,0x101,0xffff],[0,1,2,255],[0,1]):
        result=case(False,option,initial,child)
        if args.original:assert result==case(True,option,initial,child)
        cases.append(dict(option=option,initial=initial,child=child))
    # Interrupt return must restore the CPU-provided IP/CS/flags and six bytes.
    for flags in [0x2,0x3,0x202,0x203,0x402,0x403,0x602,0x603]:
        m=Machine(False,0);u=m.uc
        u.reg_write(UC_X86_REG_CS,0x1000);u.reg_write(UC_X86_REG_SS,0x3000);u.reg_write(UC_X86_REG_SP,0xf000)
        u.mem_write(0x3f000,struct.pack('<HHH',0x200,0x1000,flags))
        u.emu_start(0x17f90,0x10200,count=2)
        assert u.reg_read(UC_X86_REG_SP)==0xf006 and u.reg_read(UC_X86_REG_EFLAGS)&0x603==flags
    result=dict(passed=True,cases=cases,interrupt_frames=8,original_comparisons=len(cases) if args.original else 0,
        scope='Exact recovered instruction execution, complete nonstack DS guards, native ABI and explicit modeled DOS21 vector/Ctrl-Break services. Raw nonboolean DOS query values are model boundaries, not actual DOS claims.')
    (OUT/('original-checks.json' if args.original else 'component-checks.json')).write_text(json.dumps(result,indent=2)+'\n')
    print(len(cases),'native install/restore cases; 8 interrupt frames;',result['original_comparisons'],'original comparisons')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--original',action='store_true')
    main(parser.parse_args())
