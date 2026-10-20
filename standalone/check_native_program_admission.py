#!/usr/bin/env python3
"""Execute linked rejection paths; forbid BIOS/DOS/port IO and unexpected data writes."""
import json,struct
from pathlib import Path
from dos_image import DosImage
from build_native_program import ROOT,OUT,sha
from unicorn import UC_HOOK_INTR,UC_HOOK_INSN
from unicorn.x86_const import *


def main():
    cases=[]
    for name,owner,wrong_stack,flags,args,want in [
        ('foreign-SS',None,True,0x202,None,1),
        *[(n,n,False,0x202,None,2) for n in ('_native_program_busy','_native_program_waiting',
            '_native_process_busy','_native_display_owned','_aspect_process_serial_detached')],
        ('suspended-UART','_aspect_serial_active',False,0x202,None,2),
        ('IF0',None,False,2,None,1),('null-program',None,False,0x202,[0,0,0,0,1,0xa100],1),
        ('null-result',None,False,0x202,[0xa000,0,0,0,1,0],1),
        ('processor-flag',None,False,0x202,[0xa000,0,2,0,1,0xa100],1),
        ('wait-flag',None,False,0x202,[0xa000,0,0,2,1,0xa100],1),
        ('save-flag',None,False,0x202,[0xa000,0,0,0,2,0xa100],1)]:
        m=DosImage(OUT/'PROGRAM.EXE',OUT/'PROGRAM.map');u=m.uc
        def forbidden(*unused):raise AssertionError('Rejected request reached BIOS/DOS/port IO')
        u.hook_add(UC_HOOK_INTR,forbidden)
        for instruction in (UC_X86_INS_IN,UC_X86_INS_OUT):u.hook_add(UC_HOOK_INSN,forbidden,None,1,0,instruction)
        if owner:m.put(owner,2 if owner=='_aspect_serial_active' else 1)
        u.mem_write(m.data_base+0xa000,b'OWN1\0');u.mem_write(m.data_base+0xa0f0,b'\xa5'*64)
        arguments=args or [0xa000,0,0,0,1,0xa100]
        stack_segment=0x9000 if wrong_stack else m.ds
        sp=0xe000-14;u.mem_write(stack_segment*16+sp,struct.pack('<7H',m.return_offset,*arguments))
        for reg,value in [(UC_X86_REG_CS,m.base_segment),(UC_X86_REG_DS,m.ds),
            (UC_X86_REG_SS,stack_segment),(UC_X86_REG_SP,sp),(UC_X86_REG_ES,0xbeef),
            (UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678),(UC_X86_REG_EFLAGS,flags)]:u.reg_write(reg,value)
        length=65536 if wrong_stack else 0xd000
        before=bytes(u.mem_read(m.data_base,length))
        u.emu_start(m.symbols['_native_program_execute'],0,count=20000)
        assert m.returned and u.reg_read(UC_X86_REG_AX)==want,name
        assert u.reg_read(UC_X86_REG_SP)==sp+2 and u.reg_read(UC_X86_REG_SS)==stack_segment
        # ES is volatile across the outer Watcom C/CRT ABI; the UI assembly
        # adapters separately preserve it around native display instructions.
        assert [u.reg_read(r) for r in (UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI,UC_X86_REG_DS)]==[0xbabe,0x1234,0x5678,m.ds],name
        after=bytes(u.mem_read(m.data_base,length))
        if owner or wrong_stack or not arguments[-1]:assert after==before,name
        else:
            at=arguments[-1];assert after[:at]==before[:at] and after[at+20:]==before[at+20:],name
            assert struct.unpack_from('<H',after,at)[0]==1
        cases.append(dict(case=name,passed=True))
    report=dict(passed=True,cases=cases,checker_sha256=sha(Path(__file__)),
        binary_sha256=sha(OUT/'PROGRAM.EXE'),manifest_sha256=sha(OUT/'manifest.json'),
        scope='Actual linked C admission with complete non-stack data comparison, wrong-SS isolation and forbidden BIOS/DOS/port IO. Not an EXEC or physical hardware model.')
    (OUT/'admission.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PROGRAM linked admission:',len(cases),'cases PASS')


if __name__=='__main__':main()
