#!/usr/bin/env python3
"""Replay linked terminal exit code with modeled DOS PSP/termination services."""
import json,re,struct
from pathlib import Path
from unicorn import UC_HOOK_CODE,UC_HOOK_INTR
from unicorn.x86_const import *
from dos_image import DosImage
from build_aspect_process import ROOT,sha
OUT=ROOT/'build/terminal-exit-mouse'

class Machine:
    def __init__(self):
        self.image=DosImage(OUT/'TERMINAL.EXE',OUT/'terminal.map');self.u=self.image.uc
        self.layout=json.loads((OUT/'manifest.json').read_text())['memory_layout']
        self.psp=0xff0;self.current=self.psp;self.count=self.layout['retained_parent_paragraphs']+32
        self.calls=[];self.decision=None;self.returned=False
        self.image.put('process_psp',self.psp);self.image.put('process_keep_paragraphs',self.count-32)
        self.u.mem_write(self.psp*16,b'\xcd\x20')
        self.mcb=(self.psp-1)*16
        self.u.mem_write(self.mcb,struct.pack('<BHH',ord('M'),self.psp,self.count))
        self.map={n:(self.image.base_segment+int(s,16),int(o,16)) for s,o,n in re.findall(
            r'^([0-9a-f]{4}):([0-9a-f]{4})[*+]?\s+(\w+)\s*$',(OUT/'terminal.map').read_text(),re.M|re.I)}
        self.u.hook_add(UC_HOOK_INTR,self.interrupt);self.u.hook_add(UC_HOOK_CODE,self.code)
    def interrupt(self,u,n,_):
        assert n==0x21
        ax=u.reg_read(UC_X86_REG_AX);self.calls.append(ax)
        if ax>>8==0x62:u.reg_write(UC_X86_REG_BX,self.current)
        elif ax>>8==0x50:self.current=u.reg_read(UC_X86_REG_BX)
        elif ax>>8==0x31:
            assert ax==0x310f and self.current==self.psp
            assert u.reg_read(UC_X86_REG_DX)==self.count
            self.decision='retained';u.emu_stop()
        else:raise AssertionError(hex(ax))
    def code(self,u,at,size,_):
        if at==0x70005:self.returned=True;u.emu_stop()
        elif at==self.image.symbols['terminal_exit_guard_hold']:self.decision='held';u.emu_stop()
    def call(self,name,ds=None,ss=None,flags=0x202):
        u=self.u;cs,ip=self.map['terminal_exit_guard_'+name]
        u.mem_write(0x70000,b'\x9a'+struct.pack('<HH',ip,cs)+b'\xf4')
        u.ctl_remove_cache(0x70000,0x70006)
        stack=self.image.offset('terminal_stack_top')-32
        for r,v in [(UC_X86_REG_CS,0x7000),(UC_X86_REG_IP,0),(UC_X86_REG_DS,self.image.ds if ds is None else ds),
                    (UC_X86_REG_SS,self.image.ds if ss is None else ss),(UC_X86_REG_SP,stack),(UC_X86_REG_EFLAGS,flags),
                    (UC_X86_REG_AX,0xbabe),(UC_X86_REG_BX,0x1234),(UC_X86_REG_SI,0x5678),(UC_X86_REG_DI,0x4321)]:u.reg_write(r,v)
        self.decision=None;self.returned=False
        u.emu_start(0x70000,0,count=30000)
        assert self.returned or self.decision,'No exit decision'
        if self.returned:
            assert u.reg_read(UC_X86_REG_SP)==stack and u.reg_read(UC_X86_REG_AX)==0xbabe
            assert u.reg_read(UC_X86_REG_SI)==0x5678 and u.reg_read(UC_X86_REG_DI)==0x4321
        return self.decision or ('rejected' if u.reg_read(UC_X86_REG_EFLAGS)&1 else 'returned')
    def begin(self):assert self.call('begin')=='returned'
    def vector(self,index,seg,off):self.u.mem_write(index*4,struct.pack('<HH',off,seg))

def main():
    manifest=json.loads((OUT/'manifest.json').read_text());assert manifest['binary_sha256']==sha(OUT/'TERMINAL.EXE')
    for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
    invalid=[]
    for kind in ['if0','foreign-ds','foreign-ss','psp-mismatch','signature','mcb-type','mcb-owner','mcb-short','mcb-wrap','floor-small']:
        m=Machine();kwargs={}
        if kind=='if0':kwargs['flags']=2
        if kind=='foreign-ds':kwargs['ds']=0x7100
        if kind=='foreign-ss':kwargs['ss']=0x7100
        if kind=='psp-mismatch':m.current+=1
        if kind=='signature':m.u.mem_write(m.psp*16,b'\x00\x00')
        if kind=='mcb-type':m.u.mem_write(m.mcb,b'B')
        if kind=='mcb-owner':m.u.mem_write(m.mcb+1,struct.pack('<H',m.psp+1))
        if kind=='mcb-short':m.u.mem_write(m.mcb+3,struct.pack('<H',m.count-33))
        if kind=='mcb-wrap':m.u.mem_write(m.mcb+3,b'\xff\xff')
        if kind=='floor-small':m.image.put('process_keep_paragraphs',15)
        before=bytes(m.u.mem_read(0x71000,0x10000))
        assert m.call('begin',**kwargs)=='rejected',kind
        assert m.image.get('terminal_exit_guard_valid')==0
        assert bytes(m.u.mem_read(0x71000,0x10000))==before or kind=='foreign-ss'
        if kind in ['if0','foreign-ds','foreign-ss']:assert not m.calls
        invalid.append(kind)
    for index in range(256):
        m=Machine();m.begin();m.vector(index,m.psp+16,0)
        if index in [0x22,0x23,0x24]:m.u.mem_write(m.psp*16+10+(index-0x22)*4,struct.pack('<HH',0,m.psp+16))
        assert m.call('finish')=='retained',index
        assert m.image.get('terminal_exit_guard_reason')==1 and m.image.get('terminal_exit_guard_vector')==index
    boundaries=[]
    for kind,inside in [('first',True),('last',True),('before',False),('after',False),('noncanonical',True),('wrapped-20bit',True)]:
        m=Machine();m.begin();end=m.psp+m.count
        seg,off={'first':(m.psp,0),'last':(end-1,15),'before':(m.psp-1,15),'after':(end,0),
                 'noncanonical':(m.psp-1,16),'wrapped-20bit':(0xffff,0xfff0)}[kind]
        m.vector(0x60,seg,off)
        assert m.call('finish')==('retained' if inside else 'returned'),kind
        boundaries.append(kind)
    leases=['process_busy','terminal_program_active','terminal_program_pending','terminal_aspect_active','hardware_active']
    for name in leases:
        m=Machine();m.begin();m.image.put(name,1,1 if name=='hardware_active' else 2)
        assert m.call('finish')=='retained' and m.image.get('terminal_exit_guard_reason')==2,name
    holds=[]
    for kind in ['missing-begin','if0','foreign-ds','foreign-ss','signature','mcb-type','mcb-owner','mcb-short','mcb-wrap']:
        m=Machine();kwargs={}
        if kind!='missing-begin':m.begin()
        if kind=='if0':kwargs['flags']=2
        if kind=='foreign-ds':kwargs['ds']=0x7100
        if kind=='foreign-ss':kwargs['ss']=0x7100
        if kind=='signature':m.u.mem_write(m.psp*16,b'\x00\x00')
        if kind=='mcb-type':m.u.mem_write(m.mcb,b'B')
        if kind=='mcb-owner':m.u.mem_write(m.mcb+1,struct.pack('<H',m.psp+1))
        if kind=='mcb-short':m.u.mem_write(m.mcb+3,struct.pack('<H',m.count-33))
        if kind=='mcb-wrap':m.u.mem_write(m.mcb+3,b'\xff\xff')
        assert m.call('finish',**kwargs)=='held',kind
        assert 0x310f not in m.calls
        holds.append(kind)
    m=Machine();m.begin();m.current=0x7100;assert m.call('finish')=='returned' and m.current==m.psp
    m=Machine();m.begin();m.vector(0x60,0x7000,0x100);assert m.call('finish')=='returned'
    gateways=[]
    for kind in ['unchanged-kernel','unchanged-owned','changed-owned','changed-vector30','changed-vector31']:
        m=Machine();gate=b'\xea'+struct.pack('<HH',0xffff,0xf000)
        if kind=='unchanged-kernel':
            off,seg=struct.unpack('<HH',gate[:4]);pseudo=(seg+(off>>4))&65535
            assert m.psp<=pseudo<m.psp+m.count
        if kind=='unchanged-owned':gate=b'\xea'+struct.pack('<HH',0,m.psp+16)
        m.u.mem_write(0xc0,gate);m.begin()
        if kind=='changed-owned':m.u.mem_write(0xc0,b'\xea'+struct.pack('<HH',0,m.psp+16))
        if kind=='changed-vector30':m.vector(0x30,m.psp+16,0)
        if kind=='changed-vector31':m.vector(0x31,m.psp+16,0)
        assert m.call('finish')==('returned' if kind=='unchanged-kernel' else 'retained'),kind
        gateways.append(kind)
    restored=[]
    for index in [0x22,0x23,0x24]:
        for kind in ['temporary-self','saved-self']:
            m=Machine();m.begin()
            if kind=='temporary-self':m.vector(index,m.psp+16,0)
            else:m.u.mem_write(m.psp*16+10+(index-0x22)*4,struct.pack('<HH',0,m.psp+16))
            assert m.call('finish')==('returned' if kind=='temporary-self' else 'retained')
            restored.append(dict(index=index,kind=kind))
    result=dict(passed=True,rejected_admissions=invalid,IVT_slots=256,boundaries=boundaries,leases=leases,held_decisions=holds,
        normal_decisions=2,gateways=gateways,restored_vectors=restored,binary_sha256=sha(OUT/'TERMINAL.EXE'),checker_sha256=sha(Path(__file__)),loader_sha256=sha(ROOT/'standalone/dos_image.py'),
        scope='Actual linked far guard with modeled DOS PSP/retention. Invalid MCB/fail-stop is modeled, not live DOS corruption. Wrapped pointers use conservative20-bit normalization.')
    (OUT/'model-checks.json').write_text(json.dumps(result,indent=2)+'\n')
    print('10 rejected admissions,256 slots,6 boundaries,5 leases,9 held,2 normal,5 gateway and6 restored-vector cases passed')
if __name__=='__main__':main()
