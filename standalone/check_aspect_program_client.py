#!/usr/bin/env python3
"""Linked child owner checks with an explicit scalar far-parent boundary."""
import json,struct
from pathlib import Path
from dos_image import DosImage
from build_aspect_process import ROOT,sha
from unicorn import UC_HOOK_CODE,UC_HOOK_INTR,UC_HOOK_INSN
from unicorn.x86_const import *
OUT=ROOT/'build/aspect-process-parent'


class Client(DosImage):
    def __init__(self):
        super().__init__(OUT/'ASPECT.EXE',OUT/'ASPECT.map')
        self.requests=[];self.reply=0
        self.uc.mem_write(0x80000,b'\xb8\0\0\xcb')
        self.uc.hook_add(UC_HOOK_CODE,self.endpoint)
        self.uc.hook_add(UC_HOOK_INTR,self.forbidden)
        for instruction in (UC_X86_INS_IN,UC_X86_INS_OUT):self.uc.hook_add(UC_HOOK_INSN,self.forbidden,None,1,0,instruction)
        for name,value in [('__STACKLOW',0x9700),('__STACKTOP',0xb700),('_aspect_serial_active',1)]:self.put(name,value)
        assert self.call('_aspect_render_prepare',[0,0x8000,0x1234])==0
        assert self.call('_aspect_render_attach')==0 and self.requests==[(0,self.offset('_aspect_render_client_record'))]
    def put(self,name,value):self.uc.mem_write(self.symbols[name],struct.pack('<H',value))
    def endpoint(self,u,address,size,unused):
        if address==0x80000:
            self.requests.append((u.reg_read(UC_X86_REG_AX),u.reg_read(UC_X86_REG_BX)))
            sp=u.reg_read(UC_X86_REG_SP);ip,cs=struct.unpack('<2H',u.mem_read(self.data_base+sp,4))
            u.reg_write(UC_X86_REG_AX,self.reply);u.reg_write(UC_X86_REG_SP,sp+4)
            u.reg_write(UC_X86_REG_CS,cs);u.reg_write(UC_X86_REG_IP,ip)
    def forbidden(self,*unused):raise AssertionError('Client owner reached an undeclared device boundary')


def main():
    cases=[]
    def record(name):cases.append(dict(case=name,passed=True))
    for save in (0,1):
        m=Client();assert m.call('_aspect_render_program_begin',[save])==0
        before=list(m.requests)
        for name,args in [('_aspect_render_program_begin',[save]),('_aspect_render_emit',[65]),('_aspect_render_finish',[]),
            ('_aspect_render_status',[65535]),('_aspect_render_key',[65]),('_aspect_render_break_notice',[0]),
            ('_aspect_render_policy_inherit',[]),('_aspect_render_keyboard_inherit',[]),('_aspect_render_script_label',[0,0])]:
            assert m.call(name,args)==10 and m.requests==before;record('owned-rejects-'+str(save)+'-'+name)
        assert m.call('_aspect_render_callback_dispatch',[0,0])==65535
        assert m.call('_aspect_render_callback_dispatch',[4,0])==10 and m.requests==before;record('owned-rejects-callback-'+str(save))
        assert m.call('_aspect_render_program_end',[0])==0 and m.requests[-1]==(10,0)
        assert m.call('_aspect_render_emit',[65])==0 and m.requests[-1]==(1,65)
        assert m.call('_aspect_render_finish')==0;record('normal-retirement-'+str(save))
    for active in (0,2):
        m=Client();m.put('_aspect_serial_active',active);before=list(m.requests)
        assert m.call('_aspect_render_program_begin',[0])==14 and m.requests==before;record('requires-live-UART-'+str(active))
    for reply in (3,10,14,65534):
        m=Client();m.reply=reply;assert m.call('_aspect_render_program_begin',[0])==(reply if reply<=14 else 10)
        m.reply=0;assert m.call('_aspect_render_emit',[65])==0;record('failed-begin-'+str(reply))
    for reply in (0,3,14):
        m=Client();assert m.call('_aspect_render_program_begin',[0])==0;m.reply=reply
        assert m.call('_aspect_render_program_end',[0])==reply;m.reply=0
        assert m.call('_aspect_render_emit',[65])==0;record('typed-end-retires-'+str(reply))
    for reply in (1,2,4,5,6,7,8,9,10,11,12,13,65531,65532,65533,65534,65535):
        m=Client();assert m.call('_aspect_render_program_begin',[0])==0;m.reply=reply
        assert m.call('_aspect_render_program_end',[0])==(reply if reply<=14 else 10);before=list(m.requests)
        assert m.call('_aspect_render_emit',[65])==10 and m.requests==before
        m.reply=0;assert m.call('_aspect_render_program_end',[0])==0;record('rejected-end-retains-for-retry-'+str(reply))
    report=dict(passed=True,cases=cases,child_sha256=sha(OUT/'ASPECT.EXE'),checker_sha256=sha(Path(__file__)),
        scope='Linked child stack guards and local PROGRAM ownership; scalar far-parent result boundary, no DOS/BIOS/UART or parent renderer execution claim.')
    (OUT/'program-client-checks.json').write_text(json.dumps(report,indent=2)+'\n');print('Child PROGRAM policy:',len(cases),'linked cases PASS')


if __name__=='__main__':main()
