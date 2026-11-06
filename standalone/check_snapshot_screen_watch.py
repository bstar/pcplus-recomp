#!/usr/bin/env python3
"""Exercise the passive screen witness and reject damaged capture controls."""
import argparse,json,struct,subprocess
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_CODE,UC_HOOK_INTR
from unicorn.x86_const import *
from build_path_session import ROOT,sha
from snapshot_screen_watch import verify

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir()
    source=ROOT/'standalone/snapshot_screen_watch.asm';wrapper=out/'watch.asm'
    wrapper.write_text(source.read_text()+'\ntest_symbols: dw hook,old21,data,resident_end\n')
    values=dict(IRQ_VECTOR=52,PARENT_ISR_OFFSET=0x1111,CHILD_ISR_OFFSET=0x2222,
        PARENT_ISR_SEG=0x100,PARENT_RENDER_SEG=0x200,PARENT_CHILD_DS=0x100,
        CHILD_ISR_SEG=0x100,CHILD_DATA_SEG=0x300)
    binary=out/'watch.com';subprocess.run(['nasm','-fbin',*[f'-D{k}={v}' for k,v in values.items()],str(wrapper),'-o',str(binary)],check=True)
    raw=binary.read_bytes();entry,old,data,end=struct.unpack('<4H',raw[-8:]);cases=[];valid=None
    for df in [0,0x400]:
     for cf in [0,1]:
      for scenario in ['child','parent','wrong-irq','wrong-ds','wrong-ss','wrong-path','wrong-function','wrong-page','wrong-mode']:
       u=Uc(UC_ARCH_X86,UC_MODE_16);u.mem_map(0,0x100000);u.mem_write(0x10100,raw)
       u.mem_write(0x10000+old,struct.pack('<HH',0,0x3000));u.mem_write(0x30000,b'\xcf')
       u.mem_write(0x10000+data+6,struct.pack('<H',0xa000))
       vector=(0x1111,0x5f00) if scenario=='parent' else (0x9999,0x6e00) if scenario=='wrong-irq' else (0x2222,0x6e00)
       u.mem_write(52,struct.pack('<2H',*vector));u.mem_write(0x60100,struct.pack('<H',0x7000))
       u.mem_write(0x449,bytes([0x13 if scenario=='wrong-mode' else 3]));u.mem_write(0x44a,struct.pack('<H',80))
       u.mem_write(0x484,b'\x18');u.mem_write(0x485,struct.pack('<H',16));u.mem_write(0x450,struct.pack('<H',0x0312))
       u.mem_write(0x460,struct.pack('<H',0x0607));u.mem_write(0x462,bytes([1 if scenario=='wrong-page' else 0]))
       video=bytes((i*17+3)&255 for i in range(4000));u.mem_write(0xb8000,video)
       u.hook_add(UC_HOOK_INTR,lambda *args:(_ for _ in ()).throw(AssertionError('Unexpected interrupt request')))
       def call(name,function=0x3c00):
        ds=0x7100 if scenario=='wrong-ds' else 0x7000;ss=0x7100 if scenario=='wrong-ss' else ds
        u.mem_write(ds*16+0x2000,name)
        registers={UC_X86_REG_AX:function,UC_X86_REG_BX:0x3456,UC_X86_REG_CX:0x5678,
          UC_X86_REG_DX:0x2000,UC_X86_REG_SI:0x2000 if function==0x6c00 else 0x2345,
          UC_X86_REG_DI:0x4567,UC_X86_REG_BP:0x6789,UC_X86_REG_DS:ds,UC_X86_REG_ES:0xbeef,
          UC_X86_REG_SS:ss,UC_X86_REG_SP:0x9000}
        for reg,value in registers.items():u.reg_write(reg,value)
        u.reg_write(UC_X86_REG_CS,0x1000);u.reg_write(UC_X86_REG_IP,entry);u.reg_write(UC_X86_REG_EFLAGS,2|df|cf)
        u.mem_write(ss*16+0x9000,struct.pack('<3H',0x100,0xf000,0x202|df|cf));predecessor=[];returned=[]
        def step(machine,address,size,unused):
         if address==0x30000:
          predecessor.append(True)
          for reg,value in registers.items():assert u.reg_read(reg)==value,(scenario,reg)
          assert u.reg_read(UC_X86_REG_EFLAGS)&0x603==2|df|cf
         if address==0xf0100:returned.append(True);u.emu_stop()
        h=u.hook_add(UC_HOOK_CODE,step);u.emu_start(0x10000+entry,0,count=30000);u.hook_del(h)
        assert predecessor==[True] and returned==[True] and u.reg_read(UC_X86_REG_SP)==0x9006
        assert u.reg_read(UC_X86_REG_EFLAGS)&0x603==0x202|df|cf
        for reg,value in registers.items():
         if reg!=UC_X86_REG_SP:assert u.reg_read(reg)==value,(scenario,reg,'returned')
        assert bytes(u.mem_read(0xb8000,4000))==video
       accepted=scenario in ['child','parent']
       name=b'D:\\OTHER.TXT\0' if scenario=='wrong-path' else b'D:\\FPRE.TXT\0'
       call(name,0x4300 if scenario=='wrong-function' else 0x3c00)
       assert struct.unpack('<H',u.mem_read(0x10000+data+4,2))[0]==int(accepted)
       if accepted:
        call(b'D:\\FPRE.TXT\0') # Duplicate open/create must not create another PRE.
        assert struct.unpack('<H',u.mem_read(0x10000+data+4,2))[0]==1
        call(b'D:\\FPST.TXT\0',0x3d00);call(b'D:\\FPRE.TXT\0',0x6c00);call(b'D:\\FPST.TXT\0')
        before=bytes(u.mem_read(0x10000+data,8+4*4016));call(b'D:\\FPRE.TXT\0')
        assert bytes(u.mem_read(0x10000+data,len(before)))==before
        for i in range(4):
         record=before[8+i*4016:8+(i+1)*4016]
         assert struct.unpack('<8H',record[:16])==(i,3,80,25,16,0x0312,0x0607,0)
         assert record[16:]==video
        valid=before
       cases.append(dict(scenario=scenario,df=bool(df),cf=bool(cf),passed=True))
    original=out/'valid.bin';original.write_bytes(valid);assert verify(original)['passed']
    rejected=[]
    for name,offset in [('count',4),('mode',8+4016+2),('cursor',8+4016+10),('shape',8+4016+12),('character',8+4016+16),('attribute',8+4016+17)]:
     damaged=bytearray(valid);damaged[offset]^=1;p=out/(name+'.bin');p.write_bytes(damaged)
     try:verify(p)
     except AssertionError:rejected.append(name)
     else:raise AssertionError('Accepted damaged '+name)
    p=out/'truncated.bin';p.write_bytes(valid[:-1])
    try:verify(p)
    except AssertionError:rejected.append('truncated')
    else:raise AssertionError('Accepted truncated capture')
    r=dict(passed=True,cases=cases,rejected_artifacts=rejected,resident_bytes=end,
      sources={str(source.relative_to(ROOT)):sha(source),'standalone/snapshot_screen_watch.py':sha(ROOT/'standalone/snapshot_screen_watch.py'),'standalone/check_snapshot_screen_watch.py':sha(Path(__file__))},
      scope=__doc__+' Real assembled8086 hook with modeled predecessor IRET/IRQ/BDA/video. No actual DOS or hardware claim; separate captured DOS run required.')
    (out/'result.json').write_text(json.dumps(r,indent=2)+'\n');print('PASS',len(cases),'hook cases and',len(rejected),'damaged capture rejections')
if __name__=='__main__':main()
