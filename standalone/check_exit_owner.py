#!/usr/bin/env python3
"""Replay linked exit admission and retain/fail-stop decisions with modeled DOS."""
import json,struct
from pathlib import Path
from unicorn import UC_HOOK_CODE,UC_HOOK_INTR
from unicorn.x86_const import *
from dos_image import DosImage
from build_exit_owner import ROOT,OUT,sha

class Machine:
    def __init__(self):
        self.image=DosImage(OUT/'EXITKID.EXE',OUT/'EXITKID.map');self.uc=self.image.uc
        self.psp=0x800;self.calls=[];self.live=0;self.stopped=None
        self.image.put('__psp',self.psp);self.image.put('__STACKTOP',0xe000)
        self.uc.mem_write(self.psp*16,b'\xcd\x20')
        self.mcb=(self.psp-1)*16
        self.uc.mem_write(self.mcb,struct.pack('<BHH',ord('M'),self.psp,0x8000))
        self.uc.hook_add(UC_HOOK_INTR,self.interrupt)
        self.uc.hook_add(UC_HOOK_CODE,self.code)
    def interrupt(self,u,number,_):
        assert number==0x21
        ax=u.reg_read(UC_X86_REG_AX);self.calls.append(ax)
        if ax>>8==0x62:u.reg_write(UC_X86_REG_BX,self.psp)
        elif ax>>8==0x50:self.psp=u.reg_read(UC_X86_REG_BX)
        elif ax>>8==0x31:
            assert ax&255==10 and self.psp==0x800
            assert u.reg_read(UC_X86_REG_DX)==0x8000
            self.stopped='retained';u.emu_stop()
        else:raise AssertionError(hex(ax))
    def code(self,u,address,size,_):
        if address==self.image.symbols['_program_exit_live']:
            ss=u.reg_read(UC_X86_REG_SS);sp=u.reg_read(UC_X86_REG_SP)
            target=int.from_bytes(u.mem_read(ss*16+sp,2),'little')
            u.reg_write(UC_X86_REG_AX,self.live);u.reg_write(UC_X86_REG_SP,sp+2)
            u.reg_write(UC_X86_REG_IP,target)
        elif address==self.image.symbols['_program_exit_stop']:
            self.stopped='held';u.emu_stop()
    def call(self,name,args=()):
        try:return self.image.call('_program_exit_'+name,args)
        except AssertionError:
            if not self.stopped or self.image.returned:raise
            return self.stopped

def main():
    manifest=json.loads((OUT/'manifest.json').read_text())
    assert manifest['products']['EXITKID.EXE']==sha(OUT/'EXITKID.EXE')
    for name,digest in manifest['sources'].items():assert sha(ROOT/name)==digest,name
    negatives=[]
    for kind in ['if0','foreign-ss','foreign-dgroup','crt-psp','signature','mcb-type','mcb-owner','mcb-size','mcb-wrap','stack-top']:
        m=Machine();u=m.uc;image=m.image
        if kind=='crt-psp':image.put('__psp',0x801)
        if kind=='signature':u.mem_write(0x8000,b'\x00\x00')
        if kind=='mcb-type':u.mem_write(m.mcb,b'B')
        if kind=='mcb-owner':u.mem_write(m.mcb+1,struct.pack('<H',0x801))
        if kind=='mcb-size':u.mem_write(m.mcb+3,struct.pack('<H',0x10))
        if kind=='mcb-wrap':u.mem_write(m.mcb+3,struct.pack('<H',0xffff))
        if kind=='stack-top':image.put('__STACKTOP',0)
        def context(uc,at,size,_):
            if at!=image.symbols['_program_exit_begin']:return
            if kind=='if0':uc.reg_write(UC_X86_REG_EFLAGS,2)
            if kind in ['foreign-ss','foreign-dgroup']:
                sp=uc.reg_read(UC_X86_REG_SP)
                uc.mem_write(0x70000+sp,bytes(uc.mem_read(image.data_base+sp,32)))
                uc.reg_write(UC_X86_REG_SS,0x7000)
                if kind=='foreign-dgroup':uc.reg_write(UC_X86_REG_DS,0x7000)
        hook=u.hook_add(UC_HOOK_CODE,context)
        before=bytes(u.mem_read(image.data_base,0xd000))
        assert m.call('begin')==10,kind
        assert bytes(u.mem_read(image.data_base,0xd000))==before,kind
        if kind in ['if0','foreign-ss','foreign-dgroup']:assert not m.calls,kind
        u.hook_del(hook);negatives.append(kind)
    m=Machine();assert m.call('begin')==0;assert m.call('begin')==10
    assert m.call('finish',(37,))==37
    m=Machine();assert m.call('begin')==0;m.psp=0x700
    assert m.call('finish',(37,))==37 and m.psp==0x800
    m=Machine();assert m.call('begin')==0;m.live=1
    assert m.call('finish',(37,))=='retained'
    m=Machine();assert m.call('begin')==0;m.live=1
    m.uc.mem_write(m.mcb+3,struct.pack('<H',1))
    assert m.call('finish',(37,))=='held'
    assert all(ax>>8!=0x31 for ax in m.calls)
    result=dict(passed=True,admission_rejections=negatives,decisions=4,
        binary_sha256=manifest['products']['EXITKID.EXE'],checker_sha256=sha(Path(__file__)),
        scope='Actual linked guard instructions; modeled DOS PSP/termination and controlled lease callback. Invalid MCB retains execution at fail-stop entry; not actual DOS-kernel corruption recovery.')
    (OUT/'model-checks.json').write_text(json.dumps(result,indent=2)+'\n')
    print('10 rejected admissions and four exit decisions passed')
if __name__=='__main__':main()
