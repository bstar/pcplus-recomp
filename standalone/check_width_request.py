#!/usr/bin/env python3
"""Compare linked width-request ABI with optional original bytes at the reset boundary."""
import argparse,hashlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_CODE
from unicorn.x86_const import *
from dos_image import DosImage

ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
REGS=[UC_X86_REG_AX,UC_X86_REG_BX,UC_X86_REG_CX,UC_X86_REG_DX,UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI]


def linked(old,argument,replacement):
    m=DosImage(ROOT/'build/width-request/WIDTH.EXE',ROOT/'build/width-request/width.map')
    m.put('reset_configured_wide',old);m.put('width_request_argument',argument);m.put('width_reset_replacement',replacement)
    m.call('width_request_invoke')
    assert m.uc.reg_read(UC_X86_REG_DS)==m.uc.reg_read(UC_X86_REG_SS)==m.ds
    state=[m.get(n)for n in ['reset_configured_wide','width_observed_configuration','width_observed_mode','width_reset_calls']]
    return state+[m.uc.reg_read(reg)for reg in REGS]


def original(blob,old,argument,replacement):
    uc=Uc(UC_ARCH_X86,UC_MODE_16);uc.mem_map(0,0x100000)
    uc.mem_write(0x12a6e,blob);uc.mem_write(0x120a4,b'\xc3');uc.mem_write(0x1f000,b'\x90')
    base=0x30000;uc.mem_write(base+0x1d2e,struct.pack('<H',old))
    uc.mem_write(base+0xdffc,struct.pack('<HH',0xf000,argument))
    for reg,value in [(UC_X86_REG_CS,0x1000),(UC_X86_REG_DS,0x3000),(UC_X86_REG_SS,0x3000),
                      (UC_X86_REG_SP,0xdffc),(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),
                      (UC_X86_REG_DI,0x5678),(UC_X86_REG_EFLAGS,0x202)]:uc.reg_write(reg,value)
    seen=[];returned=[]
    def observe(u,address,size,_):
        if address==0x120a4:
            sp=u.reg_read(UC_X86_REG_SP)
            ret,mode=struct.unpack('<HH',u.mem_read(base+sp,4))
            seen.append((struct.unpack('<H',u.mem_read(base+0x1d2e,2))[0],mode))
            u.mem_write(base+0x1d2e,struct.pack('<H',replacement))
            for reg,value in zip(REGS[:4],[0xaaaa,0xbbbb,0xcccc,0xdddd]):u.reg_write(reg,value)
            u.reg_write(UC_X86_REG_SP,sp+2);u.reg_write(UC_X86_REG_IP,ret)
        elif address==0x1f000:returned.append(True);u.emu_stop()
    uc.hook_add(UC_HOOK_CODE,observe);uc.emu_start(0x12a6e,0,count=200)
    assert returned and len(seen)==1 and uc.reg_read(UC_X86_REG_SP)==0xe000
    assert uc.reg_read(UC_X86_REG_DS)==uc.reg_read(UC_X86_REG_SS)==0x3000
    return [struct.unpack('<H',uc.mem_read(base+0x1d2e,2))[0],*seen[0],1]+[uc.reg_read(reg)for reg in REGS]


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--original',type=Path);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();manifest=json.loads((ROOT/'build/width-request/manifest.json').read_text())
    for name,digest in manifest['sources'].items():assert sha(ROOT/name)==digest
    assert sha(ROOT/'build/width-request/WIDTH.EXE')==manifest['binary_sha256']
    proof=json.loads((ROOT/'reconstruction/modes/width_request_provenance.json').read_text());blob=None
    if args.original:
        assert sha(args.original)==proof['original_sha256']
        data=args.original.read_bytes();blob=data[proof['file_offset']:proof['file_offset']+proof['bytes']]
        assert hashlib.sha256(blob).hexdigest()==proof['sha256']
    cases=[]
    for old,argument,replacement in itertools.product((0,1,0x1234,0xffff),(0,1,2,0x8000,0xffff),(0,0x9999,0xffff)):
        actual=linked(old,argument,replacement)
        assert actual==[old,argument,0,1,0xaaaa,0xbbbb,0xcccc,0xdddd,0xbabe,0x1234,0x5678]
        if blob is not None:assert original(blob,old,argument,replacement)==actual
        cases.append(dict(configuration=old,argument=argument,reset_replacement=replacement,passed=True))
    sources=dict(manifest['sources']);sources[str(Path(__file__).relative_to(ROOT))]=sha(Path(__file__))
    sources['standalone/dos_image.py']=sha(ROOT/'standalone/dos_image.py')
    result=dict(passed=True,cases=cases,paired_original=blob is not None,binary_sha256=manifest['binary_sha256'],sources=sources,
                scope='60 linked adapter invocations with explicit reset boundary; optional original instruction replay. No real reset/132-column display or application integration claim.')
    args.output.write_text(json.dumps(result,indent=2)+'\n');print('PASS',len(cases),'width adapter cases; paired original:',blob is not None)


if __name__=='__main__':main()
