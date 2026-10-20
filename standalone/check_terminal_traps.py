#!/usr/bin/env python3
"""Execute linked trap owner/handlers with modeled DOS PSP/version/break calls."""
import json,re,struct
from pathlib import Path
from unicorn import UC_HOOK_CODE,UC_HOOK_INTR
from unicorn.x86_const import *
from dos_image import DosImage
from build_aspect_process import ROOT,sha
OUT=ROOT/'build/terminal-traps-mouse'
class Machine:
    def __init__(self,flag=0):
        self.image=DosImage(OUT/'TERMINAL.EXE',OUT/'terminal.map');self.u=self.image.uc
        self.map={n:(self.image.base_segment+int(s,16),int(o,16)) for s,o,n in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+]?\s+(\w+)\s*$',(OUT/'terminal.map').read_text(),re.M|re.I)}
        self.psp=0xff0;self.flag=flag;self.version=5;self.calls=[];self.done=None
        self.image.put('process_psp',self.psp)
        self.baseline=[(0x111,0xf000),(0x222,0xf000),(0x333,0xf000)]
        for index,pair in zip([0x1b,0x23,0x24],self.baseline):self.vector(index,*pair)
        self.u.hook_add(UC_HOOK_INTR,self.interrupt);self.u.hook_add(UC_HOOK_CODE,self.code)
    def vector(self,index,off,seg):self.u.mem_write(index*4,struct.pack('<HH',off,seg))
    def vectors(self):return [struct.unpack('<HH',self.u.mem_read(i*4,4)) for i in [0x1b,0x23,0x24]]
    def ours(self):
        seg,off=self.map['terminal_trap_break'];cs,ip=self.map['terminal_trap_critical']
        return [(off,seg),(off,seg),(ip,cs)]
    def interrupt(self,u,n,_):
        assert n==0x21
        ax=u.reg_read(UC_X86_REG_AX);self.calls.append(ax)
        if ax>>8==0x30:u.reg_write(UC_X86_REG_AX,self.version)
        elif ax>>8==0x62:u.reg_write(UC_X86_REG_BX,self.psp)
        elif ax>>8==0x50:self.psp=u.reg_read(UC_X86_REG_BX)
        elif ax==0x3300:u.reg_write(UC_X86_REG_DX,self.flag)
        elif ax==0x3301:self.flag=u.reg_read(UC_X86_REG_DX)&255
        else:raise AssertionError(hex(ax))
    def code(self,u,at,size,_):
        if at==0x70005:self.done='returned';u.emu_stop()
        elif at==self.image.symbols['terminal_trap_hold']:self.done='held';u.emu_stop()
    def registers(self,ds=None,ss=None,flags=0x202):
        for r,v in [(UC_X86_REG_DS,self.image.ds if ds is None else ds),(UC_X86_REG_SS,self.image.ds if ss is None else ss),
                    (UC_X86_REG_EFLAGS,flags),(UC_X86_REG_AX,0x1234),(UC_X86_REG_BX,0x5678),(UC_X86_REG_CX,0x2345),
                    (UC_X86_REG_DX,0x3456),(UC_X86_REG_SI,0x4567),(UC_X86_REG_DI,0x5678),(UC_X86_REG_BP,0x6789)]:self.u.reg_write(r,v)
    def call(self,name,**kwargs):
        self.registers(**kwargs);seg,off=self.map['terminal_trap_'+name]
        self.u.mem_write(0x70000,b'\x9a'+struct.pack('<HH',off,seg)+b'\xf4');self.u.ctl_remove_cache(0x70000,0x70006)
        stack=self.image.offset('terminal_stack_top')-32
        self.u.reg_write(UC_X86_REG_CS,0x7000);self.u.reg_write(UC_X86_REG_SP,stack)
        self.done=None;self.u.emu_start(0x70000,0,count=30000);assert self.done=='returned'
        assert self.u.reg_read(UC_X86_REG_SP)==stack
        for r,v in [(UC_X86_REG_BX,0x5678),(UC_X86_REG_CX,0x2345),(UC_X86_REG_DX,0x3456),(UC_X86_REG_SI,0x4567),(UC_X86_REG_DI,0x5678),(UC_X86_REG_BP,0x6789)]:assert self.u.reg_read(r)==v,(name,r)
        return self.u.reg_read(UC_X86_REG_AX)
    def handler(self,name,ax=0x1234,di=0x5678):
        self.registers(ds=0x40,ss=0x6800);seg,off=self.map['terminal_trap_'+name]
        self.u.reg_write(UC_X86_REG_AX,ax);self.u.reg_write(UC_X86_REG_DI,di)
        sp=0xe000;self.u.mem_write(0x68000+sp,struct.pack('<3H',5,0x7000,0x202))
        self.u.reg_write(UC_X86_REG_SS,0x6800);self.u.reg_write(UC_X86_REG_SP,sp)
        self.u.reg_write(UC_X86_REG_CS,seg);self.u.reg_write(UC_X86_REG_IP,off)
        self.calls.clear();self.done=None;self.u.emu_start(seg*16+off,0,count=3000)
        assert self.done and not self.calls
        if self.done=='returned':
            assert self.u.reg_read(UC_X86_REG_SP)==sp+6 and self.u.reg_read(UC_X86_REG_DS)==0x40
            assert self.u.reg_read(UC_X86_REG_SS)==0x6800 and self.u.reg_read(UC_X86_REG_DI)==di
            assert self.u.reg_read(UC_X86_REG_BX)==0x5678 and self.u.reg_read(UC_X86_REG_EFLAGS)&0x200
        return self.done,self.u.reg_read(UC_X86_REG_AX)
def main():
    manifest=json.loads((OUT/'manifest.json').read_text());assert manifest['terminal_traps']
    assert manifest['binary_sha256']==sha(OUT/'TERMINAL.EXE')
    for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
    lifecycle=[]
    for flag in [0,1]:
        m=Machine(flag);assert m.call('open')==0 and m.vectors()==m.ours() and m.flag==0
        assert m.image.get('terminal_trap_phase')==1
        assert m.call('suspend')==0 and m.vectors()==m.baseline and m.flag==flag
        for i in [0x1b,0x23,0x24]:m.vector(i,0x1111,0x7000)
        m.flag=1-flag
        assert m.call('resume')==0 and m.vectors()==m.ours() and m.flag==0
        assert m.call('close')==0 and m.vectors()==m.baseline and m.flag==flag
        assert m.image.get('terminal_trap_phase')==0
        lifecycle.append(flag)
    invalid=[]
    for kind in ['if0','foreign-ds','foreign-ss','DOS2','foreign-psp']:
        m=Machine();kwargs={}
        if kind=='if0':kwargs['flags']=2
        if kind=='foreign-ds':kwargs['ds']=0x7100
        if kind=='foreign-ss':kwargs['ss']=0x7100
        if kind=='DOS2':m.version=2
        if kind=='foreign-psp':m.psp+=1
        assert m.call('open',**kwargs)==1 and m.vectors()==m.baseline
        if kind in ['if0','foreign-ds','foreign-ss']:assert not m.calls
        invalid.append(kind)
    events=[]
    for name,ax,di in [('break',0x1234,0x5678),('critical',0x0801,12)]:
        m=Machine(1);assert m.call('open')==0
        assert m.handler(name,ax,di)==('returned',0x0803 if name=='critical' else ax)
        assert m.image.get('terminal_trap_pending')==(2 if name=='critical' else 1)
        m.call('poll');assert m.image.get('terminal_quit')==1 and m.image.get('terminal_exit_code')==16
        assert m.call('close')==0 and m.vectors()==m.baseline and m.flag==1
        events.append(name)
    m=Machine();assert m.call('open')==0;assert m.handler('critical',0x0001,12)[0]=='held'
    quarantines=[]
    for index in [0x1b,0x23,0x24]:
        m=Machine();assert m.call('open')==0;m.vector(index,0x4444,0x7000)
        m.calls.clear()
        assert m.call('close')==1 and m.image.get('terminal_trap_phase')==4
        assert not m.calls
        assert struct.unpack('<HH',m.u.mem_read(index*4,4))==(0x4444,0x7000)
        # Explicit modeled repair, never performed by product cleanup.
        m.vector(index,*m.baseline[[0x1b,0x23,0x24].index(index)])
        assert m.call('close')==0 and m.vectors()==m.baseline
        quarantines.append(index)
    self_baselines=[]
    for index,pair in zip([0x1b,0x23,0x24],Machine().ours()):
        m=Machine();m.vector(index,*pair);before=m.vectors()
        assert m.call('open')==1 and m.image.get('terminal_trap_phase')==0 and m.vectors()==before
        self_baselines.append(index)
    m=Machine(1);assert m.call('open')==0 and m.call('suspend')==0
    m.psp=0x7100
    assert m.call('resume',flags=2)==0 and m.psp==0xff0 and m.vectors()==m.ours() and m.flag==0
    m=Machine();assert m.call('open')==0;m.handler('break');assert m.call('suspend')==1
    assert m.vectors()==m.ours() and m.image.get('terminal_trap_child')==0
    m=Machine();assert m.call('open')==0;assert m.call('open')==1
    assert m.call('close')==0 and m.vectors()==m.baseline
    report=dict(passed=True,lifecycle_flags=lifecycle,invalid_admissions=invalid,events=events,unfailable_critical='held',
        quarantine_vectors=quarantines,self_baselines_rejected=self_baselines,IF0_foreign_PSP_resume=True,cancelled_child_rejected=True,reentry_rejected=True,
        binary_sha256=sha(OUT/'TERMINAL.EXE'),checker_sha256=sha(Path(__file__)),loader_sha256=sha(ROOT/'standalone/dos_image.py'),
        scope='Actual linked trap instructions and foreign-DS interrupt frames; modeled DOS version/PSP/break services. Critical holding and explicit vector repair are modeled, not live kernel corruption recovery.')
    (OUT/'trap-model.json').write_text(json.dumps(report,indent=2)+'\n');print('Trap owner lifecycle,foreign frames,typed events,quarantine and holding checks PASS')
if __name__=='__main__':main()
