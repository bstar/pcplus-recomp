#!/usr/bin/env python3
"""Check the real passive hook's filtering, bounded records and preserved ABI."""
import argparse,json,struct,subprocess
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_CODE
from unicorn.x86_const import *
from build_path_session import ROOT,sha

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir()
    fields=['ERROR','OPCODE','RAW','CLEANUP','CALLS','SCOPE','DISPLAY','BUSY','PROCESS','HEADER','NEAR','FAR','BACKUP','ERRNO','DOSERR']
    offsets={n:0x100+i*2 for i,n in enumerate(fields)}
    defines=dict(PARENT_DATA_SEG=0x200,PARENT_RENDER_SEG=0x100,PARENT_CHILD_DS=0x100,CHILD_RESULT=0x140,
                 **{'CHILD_'+n:o for n,o in offsets.items()})
    source=ROOT/'standalone/aspect_exit_watch.asm';wrapper=out/'hook.asm'
    wrapper.write_text(source.read_text()+'\ntest_symbols: dw hook,old21,parent_ds,data,resident_end,alloc_data,alloc_current,probe_records\n')
    binary=out/'hook.com';subprocess.run(['nasm','-fbin',*[f'-D{k}={v}' for k,v in defines.items()],str(wrapper),'-o',str(binary)],check=True)
    raw=binary.read_bytes();entry,old,parent,data,end,alloc,current,probe=struct.unpack('<8H',raw[-16:]);cases=[]
    for df in [0,0x400]:
      for cf in [0,1]:
       for scenario in ['match','other-name','other-function','foreign-stack','foreign-child','full','pointer-bound']:
        u=Uc(UC_ARCH_X86,UC_MODE_16);u.mem_map(0,0x100000);u.mem_write(0x10100,raw)
        u.mem_write(0x10000+old,struct.pack('<HH',0,0x3000));u.mem_write(0x30000,b'\xcf')
        u.mem_write(0x5f100,struct.pack('<H',0x7000))
        for i,n in enumerate(fields):u.mem_write(0x70000+offsets[n],struct.pack('<H',0x120+i))
        u.mem_write(0x70140,struct.pack('<8H',*range(0x900,0x908)))
        def invoke(ax,ds,ss,dx=0x2000,result=None):
            stub=b'\xcf'
            if result:
                ra,rb,rc=result
                stub=b'\x55\x89\xe5\xb8'+struct.pack('<H',ra)+b'\xbb'+struct.pack('<H',rb)
                stub+=b'\x36\x83'+(b'\x4e\x06\x01' if rc else b'\x66\x06\xfe')+b'\x5d\xcf'
            u.mem_write(0x30000,stub)
            regs={UC_X86_REG_AX:ax,UC_X86_REG_BX:0x3456,UC_X86_REG_CX:0x789a,
                  UC_X86_REG_DX:dx,UC_X86_REG_SI:0x4567,UC_X86_REG_DI:0x5678,
                  UC_X86_REG_BP:0x6789,UC_X86_REG_DS:ds,UC_X86_REG_ES:0xbeef,
                  UC_X86_REG_SS:ss,UC_X86_REG_SP:0x9000}
            for reg,value in regs.items():u.reg_write(reg,value)
            u.reg_write(UC_X86_REG_CS,0x1000);u.reg_write(UC_X86_REG_IP,entry)
            u.reg_write(UC_X86_REG_EFLAGS,2|df|cf)
            u.mem_write(ss*16+0x9000,struct.pack('<3H',0x100,0xf000,0x202|df|cf))
            predecessor=[];returned=[]
            def check(machine,address,size,unused):
                if address==0x30000:
                    predecessor.append(True)
                    for reg,value in regs.items():
                        if result and reg==UC_X86_REG_SP:value-=8
                        assert u.reg_read(reg)==value,(scenario,reg)
                    assert u.reg_read(UC_X86_REG_EFLAGS)&0x603==2|df|cf
                if address==0xf0100:returned.append(True);u.emu_stop()
            h=u.hook_add(UC_HOOK_CODE,check);u.emu_start(0x10000+entry,0,count=4000);u.hook_del(h)
            assert predecessor==[True] and returned==[True]
            assert u.reg_read(UC_X86_REG_SP)==0x9006
            assert u.reg_read(UC_X86_REG_EFLAGS)&0x603==0x202|df|(result[2] if result else cf)
            for reg,value in regs.items():
                if reg==UC_X86_REG_SP:continue
                if result and reg in [UC_X86_REG_AX,UC_X86_REG_BX]:value=result[0 if reg==UC_X86_REG_AX else 1]
                assert u.reg_read(reg)==value,(scenario,reg,'returned')
        name=b'D:\\ASPECT.EXE\0' if scenario!='other-name' else b'D:\\OTHER.EXE\0'
        u.mem_write(0x62000,name)
        invoke(0x4300 if scenario=='other-function' else 0x4b00,0x6000,
               0x6100 if scenario=='foreign-stack' else 0x6000,0xffb1 if scenario=='pointer-bound' else 0x2000)
        matched=scenario in ['match','foreign-child','full']
        assert struct.unpack('<H',u.mem_read(0x10000+parent,2))[0]==(0x6000 if matched else 0)
        if scenario=='full':u.mem_write(0x10000+data+4,struct.pack('<H',8))
        child=0x7100 if scenario=='foreign-child' else 0x7000
        product_before=bytes(u.mem_read(0x70000,0x10000));render_before=bytes(u.mem_read(0x5f000,0x1000))
        invoke(0x4c0a,child,child)
        count=struct.unpack('<H',u.mem_read(0x10000+data+4,2))[0]
        assert count==(8 if scenario=='full' else 1 if scenario=='match' else 0)
        if scenario=='match':
            values=struct.unpack('<13H',u.mem_read(0x10000+data+10,26))
            assert values==(10,0x7000,0x7000,*range(0x120,0x12a))
            assert struct.unpack('<8H',u.mem_read(0x10000+probe,16))==tuple(range(0x900,0x908))
        after=bytes(u.mem_read(0x70000,0x10000))
        lo=(child-0x7000)*16+0x8f00;hi=(child-0x7000)*16+0x9006
        assert after[:lo]==product_before[:lo] and after[hi:]==product_before[hi:]
        assert bytes(u.mem_read(0x5f000,0x1000))==render_before
        cases.append(dict(scenario=scenario,df=bool(df),cf=bool(cf),count=count))
        if scenario=='match':
            for index,result in enumerate([(0x4567,0x3456,0),(8,229,1)]):
                invoke(0x4800,0x7000,0x7000,result=result)
                assert struct.unpack('<H',u.mem_read(0x10000+alloc+4,2))[0]==index+1
                values=struct.unpack('<11H',u.mem_read(0x10000+alloc+6+index*22,22))
                assert values==(0x3456,*result,*(0x120+fields.index(n) for n in ['NEAR','FAR','BACKUP','DISPLAY','PROCESS','ERRNO','DOSERR']))
                assert struct.unpack('<H',u.mem_read(0x10000+current,2))[0]==0
                cases.append(dict(scenario='allocation-return',df=bool(df),cf=bool(cf),result=result))
    report=dict(passed=True,cases=cases,resident_bytes=end,sources={str(source.relative_to(ROOT)):sha(source),str(Path(__file__).relative_to(ROOT)):sha(Path(__file__))},
        scope=__doc__+' Assembled8086 hook with a modeled predecessor IRET; no DOS/kernel or physical acceptance. Product fields are read-only; the interrupt stack frame is expected execution storage.')
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS',len(cases),'passive hook ABI/filter cases')
if __name__=='__main__':main()
