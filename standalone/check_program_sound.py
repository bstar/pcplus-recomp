#!/usr/bin/env python3
"""Execute recovered sound instructions with modeled PIT/speaker ports only."""
import argparse,hashlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_INSN,UC_HOOK_INTR
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/program-sound'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def case(entry,enabled,port,calibration,frequency=440,duration=20,original=False):
    u=Uc(UC_ARCH_X86,UC_MODE_16);u.mem_map(0,0x100000)
    source=(ROOT/'analysis/pcplus-originals/PCPLUS-main-2.01.EXE').read_bytes() if original else None
    proof=json.loads((ROOT/'reconstruction/program_sound/provenance.json').read_text())
    if source:assert hashlib.sha256(source).hexdigest()==proof['original_sha256']
    units=proof['units']+[dict(name='delay',start=0x6b72,bytes=38)]
    for unit in units:
        body=source[0x1200+unit['start']:0x1200+unit['start']+unit['bytes']] if source else (OUT/(unit['name']+'.bin')).read_bytes()
        assert len(body)==unit['bytes'];u.mem_write(0x10000+unit['start'],body)
    for reg,value in [(UC_X86_REG_CS,0x1000),(UC_X86_REG_DS,0x3000),(UC_X86_REG_SS,0x3000),(UC_X86_REG_ES,0x4000),(UC_X86_REG_SP,0xf000),(UC_X86_REG_BP,0x5678),(UC_X86_REG_SI,0x1357),(UC_X86_REG_DI,0x2468),(UC_X86_REG_EFLAGS,0x202)]:u.reg_write(reg,value)
    u.mem_write(0x31d40,struct.pack('<H',enabled));u.mem_write(0x37a4e,b'\0\0');u.mem_write(0x37ac4,struct.pack('<H',calibration))
    args=[duration,frequency] if entry==0x7722 else []
    u.mem_write(0x3f000,struct.pack('<'+'H'*(len(args)+1),0x200,*args))
    events=[];current=port;traps=[]
    def read(cpu,number,size,user):
        assert number==0x61 and size==1;events.append(('in',number,current));return current
    def write(cpu,number,size,value,user):
        nonlocal current
        assert number in (0x43,0x42,0x61) and size==1;events.append(('out',number,value))
        if number==0x61:current=value
    def interrupt(cpu,number,user):traps.append(number);cpu.emu_stop()
    u.hook_add(UC_HOOK_INSN,read,None,1,0,UC_X86_INS_IN);u.hook_add(UC_HOOK_INSN,write,None,1,0,UC_X86_INS_OUT);u.hook_add(UC_HOOK_INTR,interrupt)
    u.emu_start(0x10000+entry,0x10200,count=3000000)
    returned=u.reg_read(UC_X86_REG_IP)==0x200
    active=entry==0x7722 or bool(enabled);hz=frequency if entry==0x7722 else 220 if entry==0x376d else 440
    fault=active and (hz==0 or 1193182//hz>65535)
    assert traps==([0] if fault else []) and returned!=fault
    writes=[(p,v) for action,p,v in events if action=='out']
    expected=[]
    if active:
        expected=[(0x43,0xb6)]
        if not fault:
            divisor=1193182//hz;expected += [(0x42,divisor&255),(0x42,divisor>>8),(0x61,port|3),(0x61,port&252)]
    assert writes==expected
    if returned:assert u.reg_read(UC_X86_REG_SP)==0xf002+2*len(args)
    assert [u.reg_read(r) for r in (UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI,UC_X86_REG_DS,UC_X86_REG_SS)]==[0x5678,0x1357,0x2468,0x3000,0x3000]
    return dict(returned=returned,traps=traps,events=events,speaker=current,registers=[u.reg_read(r) for r in (UC_X86_REG_AX,UC_X86_REG_BX,UC_X86_REG_CX,UC_X86_REG_DX,UC_X86_REG_ES,UC_X86_REG_SP,UC_X86_REG_EFLAGS)])
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--original',action='store_true');args=parser.parse_args();rows=[]
    cases=[(entry,on,port,cal,440,20) for entry,on,port,cal in itertools.product([0x376d,0x3778],[0,1,65535],[0,3,0xa0,0xff],[1,3,100])]
    cases += [(0x7722,1,0xa3,3,hz,duration) for hz,duration in itertools.product([0,1,18,19,220,440,65535],[0,1,15,6554])]
    for values in cases:
        result=case(*values)
        if args.original:assert result==case(*values,original=True)
        rows.append(dict(entry=hex(values[0]),enabled=values[1],port=values[2],calibration=values[3],frequency=values[4],duration=values[5],**result))
    result=dict(passed=True,cases=rows,original_comparisons=len(rows) if args.original else 0,checker_sha256=sha(Path(__file__)),manifest_sha256=sha(OUT/'manifest.json'),scope=__doc__+' Actual recovered calibrated delay executes. Frequencies0/1/18 preserve native DIV0/quotient overflow and prior PIT control write as counterexamples. Port values are modeled, not physical audio/timing/ownership evidence.')
    (OUT/('original-checks.json' if args.original else 'checks.json')).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,cases=len(rows),original_comparisons=result['original_comparisons'])))
if __name__=='__main__':main()
