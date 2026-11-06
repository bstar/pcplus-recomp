#!/usr/bin/env python3
"""Check passive WAIT keyboard observer identity, bounded records and BIOS ABI."""
import argparse,json,struct,subprocess
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_CODE
from unicorn.x86_const import *
from build_path_session import ROOT,sha

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir()
    names=['ERROR','OPCODE','RAW','CLEANUP','CALLS','SCOPE','DISPLAY','BUSY','PROCESS','HEADER','NEAR','FAR','BACKUP','ERRNO','DOSERR','WAITING','SERIAL','DETACHED']
    offsets={n:0x100+i*2 for i,n in enumerate(names)}
    defines=dict(WAIT_WATCH=1,PARENT_DATA_SEG=0x200,PARENT_RENDER_SEG=0x100,
                 PARENT_CHILD_DS=0x100,PARENT_PROGRAM=0x102,PARENT_SNAPSHOT=0x104,
                 **{'CHILD_'+n:o for n,o in offsets.items()})
    source=ROOT/'standalone/aspect_exit_watch.asm';wrapper=out/'hook.asm'
    wrapper.write_text(source.read_text()+'\ntest_symbols: dw hook16,old16,parent_ds,wait_data,wait_records\n')
    binary=out/'hook.com'
    subprocess.run(['nasm','-fbin',*[f'-D{k}={v}' for k,v in defines.items()],str(wrapper),'-o',str(binary)],check=True)
    raw=binary.read_bytes();entry,old,parent,data,records=struct.unpack('<5H',raw[-10:]);cases=[]
    for df in [0,0x400]:
      for cf in [0,1]:
       for scenario in ['match','other-function','unattached','foreign-child','foreign-stack','not-waiting','full']:
        u=Uc(UC_ARCH_X86,UC_MODE_16);u.mem_map(0,0x100000);u.mem_write(0x10100,raw)
        u.mem_write(0x10000+old,struct.pack('<HH',0,0x3000))
        u.mem_write(0x30000,b'\xb8\x20\x39\xcf') # modeled predecessor returns actual key AX
        u.mem_write(0x10000+parent,struct.pack('<H',0 if scenario=='unattached' else 0x6000))
        u.mem_write(0x5f100,struct.pack('<3H',0x7000,2,1))
        for n in ['DISPLAY','BUSY','SERIAL','WAITING']:u.mem_write(0x70000+offsets[n],struct.pack('<H',0 if scenario=='not-waiting' and n=='WAITING' else 1))
        if scenario=='full':u.mem_write(0x10000+data+4,struct.pack('<H',8))
        ds=0x7100 if scenario=='foreign-child' else 0x7000
        ss=0x7200 if scenario=='foreign-stack' else ds
        regs={UC_X86_REG_AX:0x0100 if scenario=='other-function' else 0,
              UC_X86_REG_BX:0x3456,UC_X86_REG_CX:0x789a,UC_X86_REG_DX:0x2345,
              UC_X86_REG_SI:0x4567,UC_X86_REG_DI:0x5678,UC_X86_REG_BP:0x6789,
              UC_X86_REG_DS:ds,UC_X86_REG_ES:0xbeef,UC_X86_REG_SS:ss,UC_X86_REG_SP:0x9000}
        u.mem_write(ss*16+0x9000,struct.pack('<3H',0x100,0xf000,0x202|df|cf))
        before=bytes(u.mem_read(0x70000,0x4000));render=bytes(u.mem_read(0x5f000,0x1000))
        for r,v in regs.items():u.reg_write(r,v)
        u.reg_write(UC_X86_REG_CS,0x1000);u.reg_write(UC_X86_REG_IP,entry);u.reg_write(UC_X86_REG_EFLAGS,2|df|cf)
        seen=[];returned=[];matched=scenario=='match'
        def witness(machine,address,size,unused):
            if address==0x30000:
                seen.append(True)
                for r,v in regs.items():
                    if r==UC_X86_REG_SP and matched:v-=6
                    assert u.reg_read(r)==v,(scenario,r,'predecessor')
                assert u.reg_read(UC_X86_REG_EFLAGS)&0x603==2|df|cf
            if address==0xf0100:returned.append(True);u.emu_stop()
        u.hook_add(UC_HOOK_CODE,witness);u.emu_start(0x10000+entry,0,count=4000)
        assert seen==returned==[True]
        for r,v in regs.items():
            if r==UC_X86_REG_AX:v=0x3920
            if r==UC_X86_REG_SP:v+=6
            assert u.reg_read(r)==v,(scenario,r,'returned')
        assert u.reg_read(UC_X86_REG_EFLAGS)&0x603==0x202|df|cf
        count=struct.unpack('<H',u.mem_read(0x10000+data+4,2))[0]
        assert count==(8 if scenario=='full' else int(matched))
        payload=bytes(u.mem_read(0x10000+records,160))
        assert payload==(struct.pack('<10H',ds,ss,2,1,1,1,1,1,0,0x3920)+bytes(140) if matched else bytes(160))
        assert bytes(u.mem_read(0x70000,0x4000))==before
        assert bytes(u.mem_read(0x5f000,0x1000))==render
        cases.append(dict(scenario=scenario,df=bool(df),cf=bool(cf),count=count))
    result=dict(passed=True,cases=cases,sources={str(source.relative_to(ROOT)):sha(source),str(Path(__file__).relative_to(ROOT)):sha(Path(__file__))},
                scope=__doc__+' Assembled8086 observer with modeled BIOS predecessor; actual DOS keyboard/WAIT evidence is separate. Owned product and renderer fields are read-only.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS',len(cases),'WAIT observer ABI/filter cases')
if __name__=='__main__':main()
