#!/usr/bin/env python3
"""Replay linked owner admission and abandoned DOS-service transitions."""
import hashlib
import itertools
import json
from pathlib import Path
from unicorn import UC_HOOK_CODE, UC_HOOK_INTR, UC_HOOK_INSN
from unicorn.x86_const import *
from dos_image import DosImage

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/break-owner'

class Machine:
    def __init__(self,initial=0):
        self.image=DosImage(OUT/'BRKOWN.EXE',OUT/'BRKOWN.map')
        self.uc=self.image.uc
        self.baseline={0x1b:(0x1234,0x2345),0x23:(0x4567,0x5678)}
        self.vectors=dict(self.baseline);self.flag=initial;self.initial=initial
        self.psp=0x900;self.calls=[];self.stop_after=None;self.stopped=False
        self.seed=bytes(range(0xa0,0xa9))
        self.storage=self.image.symbols['_native_break_original_1b']
        self.uc.mem_write(self.storage,self.seed)
        self.uc.hook_add(UC_HOOK_INTR,self.interrupt)
        self.uc.hook_add(UC_HOOK_INSN,self.io,None,1,0,UC_X86_INS_IN)
        self.uc.hook_add(UC_HOOK_INSN,self.io,None,1,0,UC_X86_INS_OUT)

    def io(self,*args):
        raise AssertionError('Owner attempted port I/O')

    def interrupt(self,u,number,_):
        assert number==0x21,hex(number)
        ax=u.reg_read(UC_X86_REG_AX);dx=u.reg_read(UC_X86_REG_DX)
        self.calls.append(ax)
        if ax==0x3300:u.reg_write(UC_X86_REG_DX,(dx&0xff00)|self.flag)
        elif ax==0x3301:self.flag=dx&255
        elif ax>>8==0x62:u.reg_write(UC_X86_REG_BX,self.psp)
        elif ax>>8==0x35:
            off,seg=self.vectors[ax&255]
            u.reg_write(UC_X86_REG_BX,off);u.reg_write(UC_X86_REG_ES,seg)
        elif ax>>8==0x25:self.vectors[ax&255]=(dx,u.reg_read(UC_X86_REG_DS))
        else:raise AssertionError(hex(ax))
        u.reg_write(UC_X86_REG_EFLAGS,u.reg_read(UC_X86_REG_EFLAGS)&~1)
        if self.stop_after==len(self.calls):
            self.stopped=True;u.emu_stop()

    def call(self,operation,args=()):
        try:return self.image.call('_native_break_'+operation,args)
        except AssertionError:
            # An explicit service-boundary abandonment is expected to bypass
            # the near return. No other assertion may count as abandonment.
            if not self.stopped or self.image.returned:raise
            self.stop_after=None;self.stopped=False
            return None

    def clean(self):
        assert self.call('phase')==0
        assert self.vectors==self.baseline and self.flag==self.initial
        assert bytes(self.uc.mem_read(self.storage,9))==self.seed

def admission():
    count=0
    for operation,args in [('open',(1,)),('suspend',()),('resume',()),('close',()),('recover',()),('phase',())]:
        for context in ['foreign-ss','foreign-dgroup','if0']:
            if operation=='phase' and context=='if0':continue
            m=Machine();image=m.image;u=m.uc
            before=bytes(u.mem_read(image.data_base,0xd000))
            above=bytes(u.mem_read(image.data_base+0xe100,0x1f00))
            foreign=bytes(u.mem_read(0x70000,0xd000))
            address=image.symbols['_native_break_'+operation]
            def alter(uc,at,size,_):
                if at!=address:return
                sp=uc.reg_read(UC_X86_REG_SP)
                if context!='if0':
                    uc.mem_write(0x70000+sp,bytes(uc.mem_read(image.data_base+sp,32)))
                    uc.reg_write(UC_X86_REG_SS,0x7000)
                    if context=='foreign-dgroup':uc.reg_write(UC_X86_REG_DS,0x7000)
                else:uc.reg_write(UC_X86_REG_EFLAGS,2)
            hook=u.hook_add(UC_HOOK_CODE,alter)
            assert m.call(operation,args)==(65535 if operation=='phase' else 1)
            u.hook_del(hook)
            assert not m.calls
            assert bytes(u.mem_read(image.data_base,0xd000))==before
            assert bytes(u.mem_read(image.data_base+0xe100,0x1f00))==above
            assert bytes(u.mem_read(0x70000,0xd000))==foreign
            count+=1
    m=Machine();assert m.call('open',(2,))==1 and not m.calls;m.clean()
    return count+1

def prepared(operation,initial,policy):
    m=Machine(initial)
    if operation!='open':assert m.call('open',(policy,))==0
    if operation=='resume':
        assert m.call('suspend')==0
        m.vectors={0x1b:(1,2),0x23:(3,4)};m.flag=1-initial
    m.calls=[]
    return m

def transitions():
    count=0;boundaries=[]
    for operation,initial,policy in itertools.product(['open','suspend','resume','close'],[0,1],[0,1]):
        args=(policy,) if operation=='open' else ()
        full=prepared(operation,initial,policy)
        assert full.call(operation,args)==0
        size=len(full.calls)
        boundaries.append(dict(operation=operation,initial=initial,policy=policy,services=size))
        for cut in range(1,size+1):
            m=prepared(operation,initial,policy);m.stop_after=cut
            assert m.call(operation,args) is None
            # Model a foreground checkpoint discarding the abandoned near stack.
            # The actual linked owner then runs against retained owner metadata.
            assert m.call('recover')==0,(operation,initial,policy,cut)
            m.clean();count+=1
    return count,boundaries

def quarantines():
    m=Machine();assert m.call('open',(1,))==0
    one=m.vectors[0x1b];m.vectors[0x1b]=(1,2)
    assert m.call('close')==3 and m.call('phase')==4
    assert m.call('recover')==3 and m.vectors[0x1b]==(1,2)
    m.vectors[0x1b]=one;assert m.call('recover')==0;m.clean()
    m=Machine();assert m.call('open',(1,))==0
    m.psp+=1;assert m.call('suspend')==3
    assert m.call('recover')==3
    m.psp-=1;assert m.call('recover')==0;m.clean()
    return 2

def main():
    manifest=json.loads((OUT/'manifest.json').read_text())
    assert hashlib.sha256((OUT/'BRKOWN.EXE').read_bytes()).hexdigest()==manifest['binary_sha256']
    for name,digest in manifest['sources'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
    admissions=admission();cuts,boundaries=transitions();held=quarantines()
    result=dict(passed=True,admissions=admissions,abandoned_service_boundaries=cuts,
        quarantine_cases=held,operations=boundaries,binary_sha256=manifest['binary_sha256'],
        checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        scope='Actual linked owner instructions; explicit modeled DOS21 vectors/break/PSP. '
              'Each DOS-service cut abandons the C stack and calls recovery from a fresh '
              'DS=SS foreground stack. Not asynchronous IRQ, kernel corruption or full VM unwind proof.')
    (OUT/'owner-checks.json').write_text(json.dumps(result,indent=2)+'\n')
    print(f'{admissions} admission cases; {cuts} abandoned service boundaries; {held} quarantine cases passed')

if __name__=='__main__':main()
