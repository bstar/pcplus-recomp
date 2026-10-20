#!/usr/bin/env python3
"""Execute linked parent owner policy; caller identity/admission are modeled.

No EXEC, BIOS or UART is supplied here. Actual product execution is checked by
test_aspect_parent_process_dos.py, separately from these rejection cases.
"""
import hashlib,json,re,struct
from pathlib import Path
from dos_image import DosImage
from unicorn import UC_HOOK_CODE,UC_HOOK_INTR,UC_HOOK_INSN
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/terminal-process'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


class Owner(DosImage):
    def __init__(self):
        super().__init__(OUT/'TERMINAL.EXE',OUT/'terminal.map')
        self.child_psp=0x9000;self.child_ds=0x9100;self.admission=0;self.admits=0
        for name,value in [('terminal_program_active',1),('terminal_program_kind',4),
            ('render_attached',1),('render_child_ds',self.child_ds),('render_child_psp',self.child_psp)]:self.put(name,value)
        self.put('_script_handoff',0,22)
        self.uc.hook_add(UC_HOOK_CODE,self.boundary)
        self.uc.hook_add(UC_HOOK_INTR,self.interrupt)
        for instruction in (UC_X86_INS_IN,UC_X86_INS_OUT):self.uc.hook_add(UC_HOOK_INSN,self.forbidden,None,1,0,instruction)
    def put(self,name,value,offset=0):self.uc.mem_write(self.symbols[name]+offset,struct.pack('<H',value))
    def get(self,name):return int.from_bytes(self.uc.mem_read(self.symbols[name],2),'little')
    def forbidden(self,*unused):raise AssertionError('Owner policy touched an undeclared device/callback boundary')
    def interrupt(self,u,number,unused):
        assert number==0x21 and u.reg_read(UC_X86_REG_AX)>>8==0x62
        u.reg_write(UC_X86_REG_BX,self.child_psp)
    def boundary(self,u,address,size,unused):
        if address==self.symbols['resident_bridge_caller_ds']:result=self.child_ds
        elif address==self.symbols['_aspect_render_admit']:self.admits+=1;result=self.admission
        elif address==self.sentinel:self.stopped=True;u.emu_stop();return
        elif address in [self.symbols[n] for n in ('resident_bridge_callback','terminal_aspect_emit_resident')]:self.forbidden()
        else:return
        sp=u.reg_read(UC_X86_REG_SP);stack=self.data_base+sp
        u.reg_write(UC_X86_REG_AX,result);u.reg_write(UC_X86_REG_IP,int.from_bytes(u.mem_read(stack,2),'little'));u.reg_write(UC_X86_REG_SP,sp+2)
    def operation(self,operation,value=0):
        u=self.uc;entry=self.symbols['render_body']
        # Select the segment from the actual Watcom map, not a linear alias.
        seg,off=re.search(r'^\s*([0-9a-f]+):([0-9a-f]+)[*+]?\s+render_body\s*$',(OUT/'terminal.map').read_text(),re.M|re.I).groups()
        code_segment=self.base_segment+int(seg,16);self.sentinel=code_segment*16+0xfffe
        sp=self.offset('terminal_stack_top')-2
        for reg,value_ in [(UC_X86_REG_CS,code_segment),(UC_X86_REG_DS,self.ds),(UC_X86_REG_SS,self.ds),
            (UC_X86_REG_ES,self.ds),(UC_X86_REG_SP,sp),(UC_X86_REG_EFLAGS,0x202),
            (UC_X86_REG_AX,operation),(UC_X86_REG_BX,value)]:u.reg_write(reg,value_)
        u.mem_write(self.data_base+sp,b'\xfe\xff');self.stopped=False
        u.emu_start(entry,0,count=100000)
        assert self.stopped and u.reg_read(UC_X86_REG_SP)==sp+2
        return u.reg_read(UC_X86_REG_AX)


def main():
    cases=[]
    def record(name,m):
        cases.append(dict(case=name,passed=True,admission_calls=m.admits,
            begins=m.get('render_program_begins'),ends=m.get('render_program_ends'),refreshes=m.get('render_program_refreshes')))
    for save in (0,1):
        m=Owner();assert m.operation(9,save)==0 and m.get('render_program_owned')==save+1
        assert m.operation(10)==0 and m.get('render_program_owned')==0
        assert (m.get('render_program_begins'),m.get('render_program_ends'))==(1,1);record('begin-end-'+str(save),m)
    m=Owner();assert m.operation(9)==0 and m.operation(10,1)==0 and m.get('render_program_refreshes')==1;record('NOCLEAR-refresh',m)
    for operation in (0,1,2,3,4,5,6,7,8,9,11,65535):
        m=Owner();assert m.operation(9)==0;before=m.admits
        assert m.operation(operation)==10 and m.get('render_program_owned')==1 and m.admits==before
        assert m.operation(10)==0;record('owned-rejects-'+str(operation),m)
    for name,field,value,op,argument,expected in [
        ('unattached','render_attached',0,9,0,10),('wrong-program','terminal_program_kind',3,9,0,10),
        ('inactive-program','terminal_program_active',0,9,0,10),('wrong-child-PSP','render_child_psp',0x9200,9,0,10),
        ('wrong-child-DS','render_child_ds',0x9200,9,0,10),('bad-save',None,0,9,2,7),
        ('returned-UART','_script_handoff',1,9,0,14),('end-without-begin',None,0,10,0,10)]:
        m=Owner()
        if field:m.put(field,value,22 if field=='_script_handoff' else 0)
        assert m.operation(op,argument)==expected and m.get('render_program_owned')==0 and m.admits==0;record(name,m)
    m=Owner();m.admission=3;assert m.operation(9)==3 and m.get('render_program_owned')==0;record('rejected-view-before-acquisition',m)
    for name,value,expected in [('bad-end-value',2,7),('saved-view-cannot-refresh',1,10)]:
        m=Owner();assert m.operation(9,1)==0 and m.operation(10,value)==expected
        assert m.get('render_program_owned')==2 and m.operation(10)==0;record(name,m)
    m=Owner();assert m.operation(9)==0;m.admission=3
    assert m.operation(10)==3 and m.get('render_program_owned')==0 and m.get('render_program_ends')==1;record('bad-returned-view-retires',m)
    m=Owner();assert m.operation(9)==0;m.put('_script_handoff',1,22)
    assert m.operation(10)==14 and m.get('render_program_owned')==0;record('returned-UART-end-retires',m)
    m=Owner();assert m.operation(9)==0;m.child_psp+=1
    assert m.operation(10)==10 and m.get('render_program_owned')==1;m.child_psp-=1
    assert m.operation(10)==0;record('foreign-end-cannot-retire',m)
    report=dict(passed=True,cases=cases,parent_sha256=sha(OUT/'TERMINAL.EXE'),checker_sha256=sha(Path(__file__)),
        scope='Linked parent policy with modeled caller identity and view admission; no EXEC/BIOS/UART or mechanical bridge substitution claim.')
    (OUT/'process-owner-checks.json').write_text(json.dumps(report,indent=2)+'\n');print('Parent PROGRAM policy:',len(cases),'linked cases PASS')


if __name__=='__main__':main()
