#!/usr/bin/env python3
"""Execute linked modem staging, native expansion and reply-framing checks."""
import argparse
import hashlib
import json
import re
import struct
import sys
from pathlib import Path
from unicorn import UC_HOOK_INTR,UC_HOOK_INSN
from unicorn.x86_const import *
from dos_image import DosImage
from check_setup_model import image
from check_startup_import import terminal_expected
from check_modem_import import expected as modem_expected
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src/config'))
from prm import expand_modem_command


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--hook-input',action='store_true')
    parser.add_argument('--hook-apply',action='store_true')
    args=parser.parse_args();out=args.output.resolve()
    assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    base=ROOT/'build/terminal-directory-keys-process-bank-session-capture-projection-bound-registers-controls-return-execute-modem'
    if args.hook_input:base=base.with_name(base.name+'-input')
    if args.hook_apply:
        assert args.hook_input
        base=base.with_name(base.name+'-apply')
    manifest=json.loads((base/'manifest.json').read_text());assert manifest['experimental_hook_modem']
    assert sha(base/'TERMINAL.EXE')==manifest['binary_sha256']
    model=DosImage(base/'TERMINAL.EXE',base/'terminal.map');u=model.uc
    listing=(base/'terminal.map').read_text()
    segment,offset=re.search(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+_hook_modem_prepare\s*$',listing,re.M|re.I).groups()
    cs,ip=model.base_segment+int(segment,16),int(offset,16)
    top=model.offset('terminal_stack_top');settings,target,dest,result,sp=top-512,top-592,top-1700,top-1710,top-1750
    def forbidden(*unused):raise AssertionError('Modem stager attempted interrupt or port IO')
    u.hook_add(UC_HOOK_INTR,forbidden)
    for insn in [UC_X86_INS_IN,UC_X86_INS_OUT]:u.hook_add(UC_HOOK_INSN,forbidden,None,1,0,insn)
    raw=bytearray(image());struct.pack_into('<HH',raw,0x4e4,8,4)
    seed=struct.pack('<3H',1,0,0)+terminal_expected(raw)+modem_expected(raw)+struct.pack('<H',0)+b'.\0'.ljust(64,b'\0')+struct.pack('<3H',1,8,4)
    command_offsets=[18,65,90,115,140,165];caps=[47,25,25,25,25,25]
    default_target=b'5551234\0'.ljust(64,b'\0');cases=[]
    def invoke(source=seed,text=default_target,wait=1,pointers=None,flags=0x202,foreign=False):
        u.mem_write(model.data_base+settings,bytes(source));u.mem_write(model.data_base+target,bytes(text))
        u.mem_write(model.data_base+dest,b'X'*1086);u.mem_write(model.data_base+result,b'R'*4)
        regs={UC_X86_REG_CS:cs,UC_X86_REG_IP:ip,UC_X86_REG_DS:model.ds+int(foreign),UC_X86_REG_SS:model.ds,
              UC_X86_REG_SP:sp,UC_X86_REG_EFLAGS:flags,UC_X86_REG_BP:0xbabe,UC_X86_REG_SI:0x1234,UC_X86_REG_DI:0x5678}
        for reg,value in regs.items():u.reg_write(reg,value)
        argv=[settings,target,wait,dest,result] if pointers is None else pointers
        u.mem_write(model.data_base+sp,struct.pack('<7H',model.return_offset,model.code_segment,*argv))
        globals_before=bytes(u.mem_read(model.data_base,top-8192))
        model.returned=False;u.emu_start(cs*16+ip,0,count=1000000)
        assert model.returned and u.reg_read(UC_X86_REG_SP)==sp+4
        for reg in [UC_X86_REG_DS,UC_X86_REG_SS,UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI]:assert u.reg_read(reg)==regs[reg]
        assert bytes(u.mem_read(model.data_base,top-8192))==globals_before
        assert bytes(u.mem_read(model.data_base+settings,490))==source
        assert bytes(u.mem_read(model.data_base+target,64))==text
        status=u.reg_read(UC_X86_REG_AX);actual=bytes(u.mem_read(model.data_base+dest,1086))
        if status:assert actual==b'X'*1086
        return status,actual,struct.unpack('<2H',u.mem_read(model.data_base+result,4))
    def record(name,count):cases.append(dict(case=name,inputs=count,passed=True));print(name,count,flush=True)
    def expected(source=seed,text=default_target):
        active=struct.unpack_from('<H',source)[0]
        rate=struct.unpack_from('<I',source,8)[0]
        baud=[300,1200,2400,4800,9600,19200,38400,57600,115200].index(rate)
        pause=struct.unpack_from('<H',source,64)[0] if active else 0
        if not active:return struct.pack('<3H',0,baud,0)+bytes(1080)
        commands=[expand_modem_command(source[50+at:50+at+cap].split(b'\0')[0]) for at,cap in zip(command_offsets,caps)]
        dial=commands[1].split(b'\0')[0]+expand_modem_command(text.split(b'\0')[0]).split(b'\0')[0]+commands[2].split(b'\0')[0]
        return struct.pack('<3H',1,baud,pause)+b''.join(x.ljust(129,b'\0')for x in commands)+dial.ljust(129,b'\0')+source[240:416]+b'\0'
    status,actual,detail=invoke();assert status==0 and actual==expected() and detail==(0,65535)
    record('complete-staged-plan-and-native-command-concatenation',1)
    for rate in [300,1200,2400,4800,9600,19200,38400,57600,115200]:
        changed=bytearray(seed);struct.pack_into('<I',changed,8,rate)
        status,actual,_=invoke(bytes(changed));assert status==0 and actual==expected(bytes(changed))
    record('all-nine-effective-DTE-rates',9)
    count=0
    for slot,at,cap in zip(range(6),command_offsets,caps):
        for value in range(1,256):
            text=b'^'+bytes([value])
            try:expand_modem_command(text)
            except ValueError:continue
            changed=bytearray(seed);changed[50+at:50+at+cap]=(text+b'\0').ljust(cap,b'\0')
            status,actual,_=invoke(bytes(changed),wait=0)
            assert status==0 and actual==expected(bytes(changed)),(slot,value,status)
            count+=1
    record('six-command-slots-all-valid-caret-bytes',count)
    count=0
    for slot in range(11):
        changed=bytearray(seed);changed[240+slot*16:240+(slot+1)*16]=b'^M\0'+bytes([0xff])*13
        status,actual,_=invoke(bytes(changed));assert status==0 and actual==expected(bytes(changed))
        count+=1
    record('already-expanded-responses-and-opaque-tails',count)
    count=0
    strings=[b'ATZ^M',b'ATZ',b'',b'^M^J',b'ATZ^J^M',b'~ATZ^M~',b'A^MB^M']
    for pause in range(256):
        for text in strings:
            changed=bytearray(seed);struct.pack_into('<H',changed,64,pause)
            changed[68:115]=(text+b'\0').ljust(47,b'\0')
            pending=False;valid=True
            for value in expand_modem_command(text):
                if value==pause:continue
                if value==13:pending=False
                elif value==10:
                    if pending:valid=False;break
                else:pending=True
            valid=valid and not pending
            status,actual,detail=invoke(bytes(changed))
            assert status==(0 if valid else 5),(pause,text,status,valid)
            if valid:assert actual==expected(bytes(changed))
            else:assert detail==(5,19)
            count+=1
    record('native-init-reply-framing-all-pause-bytes',count)
    count=0
    for slot,at,cap in zip(range(6),command_offsets,caps):
        for bad in [b'X'*cap,b'^\0'.ljust(cap,b'\0')]:
            changed=bytearray(seed);changed[50+at:50+at+cap]=bad
            status,_,detail=invoke(bytes(changed));assert (status,detail)==(3,(3,slot));count+=1
    for slot in range(11):
        changed=bytearray(seed);changed[240+slot*16:240+(slot+1)*16]=b'X'*16
        assert invoke(bytes(changed))[2]==(4,6+slot);count+=1
    for text in [b'X'*64,b'^\0'.ljust(64,b'\0')]:
        assert invoke(text=text)[2]==(3,17);count+=1
    for at,value,want in [(0,2,1),(8,123,2),(64,256,1)]:
        changed=bytearray(seed);struct.pack_into('<H',changed,at,value)
        assert invoke(bytes(changed))[0]==want;count+=1
    assert invoke(wait=2)[0]==1;count+=1
    record('malformed-command-response-rate-target-and-policy-atomic-refusal',count)
    inactive=bytearray(seed);struct.pack_into('<H',inactive,0,0);inactive[50:418]=b'\xff'*368
    status,actual,_=invoke(bytes(inactive),text=b'X'*64);assert status==0 and actual==expected(bytes(inactive),b'X'*64)
    record('inactive-modem-private-settings-and-target-unconsumed',1)
    count=0
    for argv in [[0,target,1,dest,result],[settings,0,1,dest,result],[settings,target,1,0,result],
                 [settings,target,1,dest,0],[settings,settings,1,dest,result],[settings,target,1,settings,result],
                 [settings,target,1,dest,dest],[65530,target,1,dest,result]]:
        assert invoke(pointers=argv)[0]==1;count+=1
    for flags,foreign in [(2,False),(0x602,False),(0x202,True)]:
        assert invoke(flags=flags,foreign=foreign)[0]==1;count+=1
    record('pointer-and-CPU-context-admission',count)
    # Exercise the terminal's proposal -> staged-offer transition using its
    # actual far storage and current target/init-reply policy.
    offer=model.symbols['_terminal_hook_modem_offer']
    proposal=model.symbols['_terminal_hook_proposal']
    wrapper_seg,wrapper_off=re.search(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+_terminal_hook_prepare_modem\s*$',listing,re.M|re.I).groups()
    def stage(source=seed,phase=2,owner_phase=0,flags=0x202,wait_seconds=1):
        u.mem_write(proposal+2094,bytes(source))
        u.mem_write(offer,b'X'*1086);u.mem_write(model.data_base+result,b'R'*4)
        model.put('_terminal_hook_phase',phase)
        u.mem_write(model.symbols['_terminal_hook_owner']+2,struct.pack('<H',owner_phase))
        model.put('terminal_modem_init_wait',wait_seconds)
        u.mem_write(model.symbols['terminal_dial_target'],default_target)
        for reg,value in [(UC_X86_REG_CS,model.base_segment+int(wrapper_seg,16)),(UC_X86_REG_IP,int(wrapper_off,16)),
                          (UC_X86_REG_DS,model.ds),(UC_X86_REG_SS,model.ds),(UC_X86_REG_SP,sp),(UC_X86_REG_EFLAGS,flags),
                          (UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678)]:u.reg_write(reg,value)
        u.mem_write(model.data_base+sp,struct.pack('<3H',model.return_offset,model.code_segment,result))
        prior=bytes(u.mem_read(model.data_base,top-8192))
        model.returned=False;u.emu_start(model.symbols['_terminal_hook_prepare_modem'],0,count=1000000)
        assert model.returned and u.reg_read(UC_X86_REG_SP)==sp+4
        assert bytes(u.mem_read(model.data_base,top-8192))==prior
        assert bytes(u.mem_read(proposal+2094,490))==source
        status=u.reg_read(UC_X86_REG_AX)
        actual=bytes(u.mem_read(offer,1086))
        if status:assert actual==b'X'*1086 and model.get('_terminal_hook_phase')==phase
        else:assert actual==expected(source) and model.get('_terminal_hook_phase')==3
        return status
    assert stage()==0
    for seconds in [3,32767]:assert stage(wait_seconds=seconds)==0
    broken=bytearray(seed);broken[68:115]=b'ATZ\0'.ljust(47,b'\0')
    assert stage(bytes(broken))==5
    broken[68:115]=b'^\0'.ljust(47,b'\0');assert stage(bytes(broken))==3
    for phase in [0,1,3]:assert stage(phase=phase)==7
    assert stage(owner_phase=1)==7
    assert stage(flags=2)==1
    record('terminal-proposal-offer-publication-and-failure-retention',10)
    sources=dict(manifest['sources'])
    for name in ['standalone/check_hook_modem.py','standalone/dos_image.py','standalone/check_setup_model.py',
                 'standalone/check_startup_import.py','standalone/check_modem_import.py','src/config/prm.py']:
        sources[name]=sha(ROOT/name)
    for name,digest in sources.items():assert sha(ROOT/name)==digest,name
    report=dict(passed=True,inputs=sum(c['inputs']for c in cases),cases=cases,sources=sources,binary_sha256=manifest['binary_sha256'],
                scope='Actual linked pure modem staging, recovered command expansion and production init validator with explicit proposed pause. '
                'Exact full plans, literal responses/tails, inactive policy, refusal atomicity. Interrupt/port IO prohibited. No application commit.')
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS',report['inputs'],'linked modem preparation cases')


if __name__=='__main__':main()
