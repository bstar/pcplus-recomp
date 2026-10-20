#!/usr/bin/env python3
"""Execute linked bridge error policy with explicitly modeled owner results."""
import json,struct
from pathlib import Path
from dos_image import DosImage
from build_aspect_process import ROOT,OUT,sha
from unicorn import UC_HOOK_CODE,UC_HOOK_INTR,UC_HOOK_INSN
from unicorn.x86_const import *


class Policy(DosImage):
    def __init__(self,program,process,child,renderer=False):
        super().__init__(OUT/'ASPECT.EXE',OUT/'ASPECT.map')
        self.program=program;self.process=process;self.child=child;self.renderer=renderer;self.events=[]
        self.uc.mem_write(self.symbols['_runtime_file']+8,struct.pack('<H',0xc000))
        self.uc.mem_write(self.data_base+0xc000,bytes(64));self.uc.mem_write(self.data_base+0xc200,b'TEST.COM\0')
        names=['_aspect_render_active','_runtime_external_scope','_aspect_file_tell','ftell_',
            '_runtime_script_files_external_begin','_runtime_script_files_external_end',
            '_process_handles_begin','_process_handles_end','_native_program_execute','_runtime_external_observe']
        self.boundaries={self.symbols[name]:name for name in names}
        self.uc.hook_add(UC_HOOK_CODE,self.boundary);self.uc.hook_add(UC_HOOK_INTR,self.forbidden)
        for instruction in (UC_X86_INS_IN,UC_X86_INS_OUT):self.uc.hook_add(UC_HOOK_INSN,self.forbidden,None,1,0,instruction)
    def forbidden(self,*args):raise AssertionError('Policy model reached an undeclared DOS/BIOS/port boundary')
    def boundary(self,u,address,size,data):
        name=self.boundaries.get(address)
        if not name:return
        sp=u.reg_read(UC_X86_REG_SP);stack=self.data_base+sp
        args=struct.unpack('<6H',u.mem_read(stack+2,12));result=0
        if name=='_aspect_render_active':result=int(self.renderer)
        elif name=='_runtime_external_scope':self.events.append('scope'+str(args[0]))
        elif name=='_aspect_file_tell':result=32
        elif name=='ftell_':result=256
        elif name=='_runtime_script_files_external_begin':
            self.events.append('streams+');u.mem_write(self.data_base+args[1],b'\0\0')
        elif name=='_runtime_script_files_external_end':self.events.append('streams-')
        elif name=='_process_handles_begin':self.events.append('handles+')
        elif name=='_process_handles_end':self.events.append('handles-')
        elif name=='_native_program_execute':
            self.events.append('execute');result=self.program
            words=[self.program,0,8,0,65535,self.process,self.child,0,0,0]
            u.mem_write(self.data_base+args[5],struct.pack('<10H',*words))
        u.reg_write(UC_X86_REG_AX,result);u.reg_write(UC_X86_REG_DX,0)
        u.reg_write(UC_X86_REG_IP,int.from_bytes(u.mem_read(stack,2),'little'));u.reg_write(UC_X86_REG_SP,sp+2)


def main():
    cases=[]
    for name,program,process,child,raw,error in [
        ('child-success',0,0,37,37,0),('missing-target',5,3,65535,65535,0),
        ('allocation-failure',5,4,65535,65535,0),('process-state-fatal',5,5,37,65535,10),
        ('backend-argument-rejection',5,1,65535,65535,0),
        ('unknown-process-result-fatal',5,99,37,65535,10),
        ('contradictory-process-result-fatal',5,0,37,65535,10),
        ('process-busy-fatal',5,2,65535,65535,10),('invalid-name',1,1,65535,1,0),
        ('program-busy-fatal',2,0,37,65535,10),('display-fatal',3,0,37,65535,10),
        ('serial-fatal',4,0,37,65535,14),('unknown-program-result-fatal',99,0,37,65535,10)]:
        m=Policy(program,process,child);observed=m.call('_runtime_external_execute',[0xc200,0,0,0,1])
        expected_events=['scope1','streams+','handles+','execute','handles-','streams-','scope0']
        passed=observed==raw and m.get('_runtime_error')==error and m.events==expected_events
        if program==4:passed=passed and m.get('_runtime_serial_error')==8
        cases.append(dict(case=name,passed=passed,raw=observed,error=m.get('_runtime_error'),expected_raw=raw,expected_error=error,events=m.events))
    m=Policy(0,0,37,True);raw=m.call('_runtime_external_execute',[0xc200,0,0,0,1])
    cases.append(dict(case='attached-renderer-rejects-before-file-owners',passed=raw==65535 and m.get('_runtime_error')==10 and not m.events))
    report=dict(passed=all(c['passed'] for c in cases),cases=cases,binary_sha256=sha(OUT/'ASPECT.EXE'),
        manifest_sha256=sha(OUT/'manifest.json'),checker_sha256=sha(Path(__file__)),
        scope='Actual linked external bridge policy/cleanup ordering. Renderer, VM scope, file/JFT and PROGRAM boundaries are explicit scalar models; no EXEC/stream/renderer hardware claim.')
    (OUT/'policy.json').write_text(json.dumps(report,indent=2)+'\n')
    print('ASPECT process policy:',len(cases),'cases','PASS' if report['passed'] else [c for c in cases if not c['passed']])
    return 0 if report['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
