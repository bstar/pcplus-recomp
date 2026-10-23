#!/usr/bin/env python3
"""Linked input offer admission, unchanged resources and atomic refusal."""
import argparse
import hashlib
import json
import re
import struct
from pathlib import Path
from unicorn import UC_HOOK_INTR,UC_HOOK_INSN
from unicorn.x86_const import *
from dos_image import DosImage

ROOT=Path(__file__).resolve().parents[1]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--hook-apply',action='store_true');args=parser.parse_args()
    out=args.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    base=ROOT/'build/terminal-directory-keys-process-bank-session-capture-projection-bound-registers-controls-return-execute-modem-input'
    if args.hook_apply:base=base.with_name(base.name+'-apply')
    manifest=json.loads((base/'manifest.json').read_text());assert manifest['experimental_hook_input']
    assert sha(base/'TERMINAL.EXE')==manifest['binary_sha256']
    listing=(base/'terminal.map').read_text();model=DosImage(base/'TERMINAL.EXE',base/'terminal.map');u=model.uc
    top=model.offset('terminal_stack_top');result,sp=top-64,top-128
    def forbidden(*unused):raise AssertionError('Input admission attempted interrupt or port IO')
    u.hook_add(UC_HOOK_INTR,forbidden)
    for insn in [UC_X86_INS_IN,UC_X86_INS_OUT]:u.hook_add(UC_HOOK_INSN,forbidden,None,1,0,insn)
    keys=b''.join(bytes([65+i%26,0])+bytes([128+i])*10 for i in range(79))
    table=bytes((i*73+19)&255 for i in range(256))
    blocks=['terminal_parser_active','terminal_transfer_pending','terminal_transfer_active',
            'terminal_monitor_active','terminal_controller_active']
    cases=[]
    def call(profile=4,mode=0,current_profile=4,current_mode=0,phase=3,bound=1,fixed=False,
             blocked=None,owner_phase=0,owner_segment=0,register_phase=0,pointer=None,flags=0x202,foreign=False,
             name='_terminal_hook_prepare_input'):
        model.put('csi_terminal_id',current_profile);model.put('terminal_translation_mode',current_mode)
        model.put('terminal_option_mask',16384 if fixed else 0)
        model.put('_terminal_hook_phase',phase);model.put('_terminal_hook_input_bound',bound)
        for field in blocks:model.put(field,int(field==blocked))
        u.mem_write(model.symbols['_terminal_hook_owner']+2,struct.pack('<3H',owner_phase,0,owner_segment))
        u.mem_write(model.symbols['_terminal_register_owner'],struct.pack('<H',register_phase))
        proposal=model.symbols['_terminal_hook_proposal']
        u.mem_write(proposal,b'P'*2584)
        u.mem_write(proposal+2094+6+16,struct.pack('<H',profile))
        u.mem_write(proposal+2094+6+40,struct.pack('<H',mode))
        u.mem_write(model.symbols['terminal_keymap'],keys);u.mem_write(model.symbols['terminal_translation_table'],table)
        offer=model.symbols['_terminal_hook_input_offer'];u.mem_write(offer,b'X'*1212)
        u.mem_write(model.data_base+result,b'R'*12)
        seg,off=re.search(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+'+name+r'\s*$',listing,re.M|re.I).groups()
        regs={UC_X86_REG_CS:model.base_segment+int(seg,16),UC_X86_REG_IP:int(off,16),UC_X86_REG_DS:model.ds+int(foreign),
              UC_X86_REG_SS:model.ds,UC_X86_REG_SP:sp,UC_X86_REG_EFLAGS:flags,UC_X86_REG_BP:0xbabe,UC_X86_REG_SI:0x1234,UC_X86_REG_DI:0x5678}
        for reg,value in regs.items():u.reg_write(reg,value)
        argv=[] if name.endswith('cancel') else [result if pointer is None else pointer]
        u.mem_write(model.data_base+sp,struct.pack('<'+'H'*(2+len(argv)),model.return_offset,model.code_segment,*argv))
        prior=bytes(u.mem_read(proposal,2584));model.returned=False
        u.emu_start(model.symbols[name],0,count=1000000)
        assert model.returned and u.reg_read(UC_X86_REG_SP)==sp+4
        for reg in [UC_X86_REG_DS,UC_X86_REG_SS,UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI]:assert u.reg_read(reg)==regs[reg]
        assert bytes(u.mem_read(proposal,2584))==prior
        assert bytes(u.mem_read(model.symbols['terminal_keymap'],948))==keys
        assert bytes(u.mem_read(model.symbols['terminal_translation_table'],256))==table
        assert model.get('csi_terminal_id')==current_profile and model.get('terminal_translation_mode')==current_mode
        status=u.reg_read(UC_X86_REG_AX);actual=bytes(u.mem_read(offer,1212))
        if not name.endswith('cancel'):
            if status:assert actual==b'X'*1212 and model.get('_terminal_hook_phase')==phase
            else:assert actual==struct.pack('<4H',profile,mode,0,0)+keys+table and model.get('_terminal_hook_phase')==4
        return status,bytes(u.mem_read(model.data_base+result,12))
    def record(name,count):cases.append(dict(case=name,inputs=count,passed=True));print(name,count,flush=True)
    for profile in [4,6]:
        for mode in [0,1,2]:assert call(profile=profile,mode=mode,current_profile=profile,current_mode=mode)[0]==0
    record('unchanged-resource-exact-offer-for-both-profiles-and-all-modes',6)
    for profile in [0,3,5,7,65535]:assert call(profile=profile)[0]==3
    for mode in [3,65535]:assert call(mode=mode)[0]==3
    for mode in [0,2]:assert call(mode=mode,current_mode=1,fixed=True)[0]==3
    record('invalid-and-explicit-fixed-policy-refusal',9)
    for phase in [0,1,2,4,65535]:assert call(phase=phase)[0]==2
    for bound in [0,2]:assert call(bound=bound)[0]==2
    for field in blocks:assert call(blocked=field)[0]==2
    for kwargs in [dict(owner_phase=1),dict(owner_segment=1),dict(register_phase=1)]:assert call(**kwargs)[0]==2
    record('phase-binding-and-competing-owner-refusal',15)
    for pointer in [0,65530]:assert call(pointer=pointer)==(1,b'R'*12)
    for flags,foreign in [(2,False),(0x602,False),(0x202,True)]:assert call(flags=flags,foreign=foreign)==(1,b'R'*12)
    record('pointer-and-CPU-context-admission',5)
    status,detail=call(mode=1);assert status==5 and struct.unpack('<6H',detail)[:3]==(5,7,7)
    record('missing-private-translation-stage-retains-offer',1)
    for phase in [0,3,4]:
        call(phase=phase,name='_terminal_hook_input_cancel')
        assert model.get('_terminal_hook_input_bound')==0
    record('cancel-releases-private-binding-without-adoption',3)
    sources=dict(manifest['sources'])
    for name in ['standalone/check_hook_input.py','standalone/dos_image.py']:sources[name]=sha(ROOT/name)
    for name,digest in sources.items():assert sha(ROOT/name)==digest,name
    report=dict(passed=True,inputs=sum(c['inputs']for c in cases),cases=cases,sources=sources,binary_sha256=manifest['binary_sha256'],
                scope='Actual linked input offer admission, unchanged resources and refusal. Interrupt/port IO prohibited. '
                'Real keyboard/XLT IO and helper CWD mutation checked separately in DOS. No accepted settings adoption.')
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS',report['inputs'],'linked input cases')


if __name__=='__main__':main()
