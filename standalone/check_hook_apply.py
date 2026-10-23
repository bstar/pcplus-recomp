#!/usr/bin/env python3
"""Actual linked apply checks, stale/corrupt refusal and publication without IO."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
from unicorn import UC_HOOK_INTR,UC_HOOK_INSN,UC_HOOK_CODE
from unicorn.x86_const import *
from dos_image import DosImage
from check_setup_model import image
from check_startup_import import terminal_expected
from check_modem_import import expected as modem_expected

ROOT=Path(__file__).resolve().parents[1]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    out=args.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    base=ROOT/'build/terminal-directory-keys-process-bank-session-capture-projection-bound-registers-controls-return-execute-modem-input-apply'
    manifest=json.loads((base/'manifest.json').read_text());assert manifest['experimental_hook_apply']
    assert sha(base/'TERMINAL.EXE')==manifest['binary_sha256']
    model=DosImage(base/'TERMINAL.EXE',base/'terminal.map');u=model.uc;listing=(base/'terminal.map').read_text()
    symbols={name:(int(seg,16),int(off,16))for seg,off,name in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',listing,re.M|re.I)}
    top=model.offset('terminal_stack_top');publishing=False;reads=[]
    ports={0x21:255,0x3fb:3,0x3f9:0,0x3fc:1,0x3fd:0x60}
    def interrupt(*unused):raise AssertionError('Apply attempted DOS/BIOS interrupt')
    def inp(uc,port,size,unused):
        assert not publishing,'IO after publication began'
        assert size==1 and port in ports,hex(port)
        reads.append(port);return ports[port]
    def outp(*unused):raise AssertionError('Apply attempted port write in no-transport fixture')
    def code(uc,address,size,unused):
        nonlocal publishing
        if address==model.symbols['_terminal_mouse_publish_far']:publishing=True
    u.hook_add(UC_HOOK_INTR,interrupt);u.hook_add(UC_HOOK_INSN,inp,None,1,0,UC_X86_INS_IN)
    u.hook_add(UC_HOOK_INSN,outp,None,1,0,UC_X86_INS_OUT);u.hook_add(UC_HOOK_CODE,code)
    def far(name,argv=(),sp=None,flags=0x202,foreign=False):
        seg,off=symbols[name];cs=model.base_segment+seg;stack=top-128 if sp is None else sp
        regs={UC_X86_REG_CS:cs,UC_X86_REG_IP:off,UC_X86_REG_DS:model.ds+int(foreign),UC_X86_REG_SS:model.ds,
              UC_X86_REG_SP:stack,UC_X86_REG_EFLAGS:flags,UC_X86_REG_BP:0xbabe,UC_X86_REG_SI:0x1234,UC_X86_REG_DI:0x5678}
        for reg,value in regs.items():u.reg_write(reg,value)
        u.mem_write(model.data_base+stack,struct.pack('<'+'H'*(2+len(argv)),model.return_offset,model.code_segment,*argv))
        model.returned=False;u.emu_start(cs*16+off,0,count=4000000)
        assert model.returned and u.reg_read(UC_X86_REG_SP)==stack+4,name
        for reg in [UC_X86_REG_DS,UC_X86_REG_SS,UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI]:assert u.reg_read(reg)==regs[reg],name
        return u.reg_read(UC_X86_REG_AX)
    raw=bytearray(image());struct.pack_into('<HH',raw,0x4e4,8,4);struct.pack_into('<H',raw,0x194,6)
    u.mem_write(model.symbols['terminal_configuration_values'],terminal_expected(raw))
    u.mem_write(model.symbols['terminal_modem_settings'],modem_expected(raw))
    u.mem_write(model.symbols['_terminal_transfer_preferences'],struct.pack('<H',0)+b'.\0'.ljust(64,b'\0'))
    model.put('terminal_option_mask',16);model.put('_terminal_sound_enabled',int(struct.unpack_from('<H',raw,0x1bc)[0]!=0))
    model.call('terminal_apply_configuration')
    # This register-ABI native constructor takes AX, so call through its existing
    # startup public wrapper which supplies the owned keymap destination.
    assert model.call('terminal_initialize_keymap')==0
    assert model.call('terminal_reset_capture')==0
    a,b,c,r=top-1280,top-2550,top-3060,top-3070
    u.mem_write(model.data_base+a,bytes(raw))
    far('_terminal_mouse_bootstrap_far')
    assert far('_terminal_mouse_stage_far',[a,1264],sp=top-1400)==0
    assert far('_hook_baseline_publish',[a,1],sp=top-1400)==0
    assert far('_terminal_session_project_bound',[a],sp=top-1400)==0
    before=bytes(u.mem_read(model.data_base+a,1264));after=bytearray(before)
    for at,value in [(0x1ae,30),(0x1bc,0),(0x4e4,321),(0x4e6,654),(0x42c,1)]:struct.pack_into('<H',after,at,value)
    u.mem_write(model.data_base+b,bytes(after))
    assert far('_hook_return_validate',[a,b,0,c,r],sp=top-3100)==0
    settings=bytes(u.mem_read(model.data_base+c,490))
    proposed=bytearray(830);proposed[0]=0x3c;proposed[20:25]=b'HOOK\0'
    u.mem_write(model.symbols['_terminal_hook_before'],before)
    u.mem_write(model.symbols['_terminal_hook_proposal'],bytes(proposed)+bytes(after)+settings)
    model.put('_terminal_hook_phase',2);model.put('_terminal_hook_input_bound',1)
    assert far('_terminal_hook_prepare_modem',[top-32])==0
    assert far('_terminal_hook_prepare_input',[top-32])==0
    for name,value in [('terminal_program_active',1),('terminal_program_kind',5),('terminal_program_status',4)]:model.put(name,value)
    model.put('hardware_active',1,1);model.put('vector_active',1,1)
    model.put('uart_previous_irq_offset',0x1234);model.put('uart_previous_irq_segment',0xf000)
    u.mem_write(0x400,struct.pack('<2H',0x3f8,0x2f8));u.mem_write(0x30,struct.pack('<2H',0x1234,0xf000))
    frozen=bytes(u.mem_read(0,0x100000));result=top-32;cases=[]
    def reset():
        nonlocal publishing
        u.mem_write(0,frozen);publishing=False;reads.clear()
        ports.update({0x21:255,0x3fb:3,0x3f9:0,0x3fc:1,0x3fd:0x60})
        u.mem_write(model.data_base+result,b'R'*6)
    protected=[('terminal_configuration_values',44),('terminal_modem_settings',368),('_terminal_transfer_preferences',66),
               ('terminal_keymap',948),('terminal_translation_table',256),('_terminal_sound_enabled',2),
               ('_terminal_register_owner',1734),('terminal_baseline_storage',1272)]
    def stable():return [bytes(u.mem_read(model.symbols[name],size))for name,size in protected]
    def reject(want,change=lambda:None,flags=0x202,foreign=False,pointer=None):
        reset();change();original=stable()
        status=far('_terminal_hook_apply_check',[result if pointer is None else pointer],flags=flags,foreign=foreign)
        assert status==want,(status,want)
        assert stable()==original and not publishing
        return status
    reset();original=stable();assert far('_terminal_hook_apply_check',[result])==0
    assert model.get('_terminal_hook_phase')==5 and stable()==original and not publishing
    assert far('_terminal_hook_apply',[result])==0 and publishing and model.get('_terminal_hook_phase')==6
    assert bytes(u.mem_read(model.symbols['_terminal_register_owner']+904,830))==proposed
    assert model.get('_terminal_register_owner')==0
    assert model.get('_terminal_sound_enabled')==0
    assert bytes(u.mem_read(model.symbols['terminal_configuration_values'],44))==settings[6:50]
    state=bytes(u.mem_read(model.symbols['terminal_baseline_storage'],1272));assert state[8:]==after
    assert struct.unpack_from('<3H',state)==(0xb451,2,3)
    cases.append(dict(case='validated-publication-with-no-interrupt-or-port-IO-after-first-store',inputs=1,passed=True))
    count=0
    for flags,foreign in [(2,False),(0x602,False),(0x202,True)]:reject(1,flags=flags,foreign=foreign);count+=1
    for pointer in [0,65534]:reject(1,pointer=pointer);count+=1
    for name,value in [('_terminal_hook_phase',3),('_terminal_hook_input_bound',0),('terminal_program_kind',1),
                       ('terminal_program_active',0),('terminal_program_status',5),('terminal_parser_active',1),
                       ('terminal_transfer_active',1),('terminal_transfer_pending',1),('terminal_controller_active',1),('terminal_monitor_active',1)]:
        reject(2,lambda name=name,value=value:model.put(name,value));count+=1
    cases.append(dict(case='caller-and-foreground-owner-admission',inputs=count,passed=True))
    count=0
    for name,value in [('_terminal_sound_enabled',0),('terminal_baud_low',9600),('terminal_translation_mode',2)]:
        reject(3,lambda name=name,value=value:model.put(name,value));count+=1
    for offset in [4,6]:
        reject(3,lambda offset=offset:u.mem_write(model.symbols['_terminal_register_owner']+offset,b'\x01\0'));count+=1
    for symbol,offset,want in [('_terminal_hook_proposal',830+0x200,4),('_terminal_hook_proposal',2094+6,4),
                               ('_terminal_hook_modem_offer',10,6),('_terminal_hook_input_offer',8,5)]:
        reject(want,lambda symbol=symbol,offset=offset:u.mem_write(model.symbols[symbol]+offset,b'!'));count+=1
    reject(4,lambda:u.mem_write(model.symbols['_terminal_hook_proposal']+20,b'X'*81));count+=1
    cases.append(dict(case='stale-accepted-session-and-damaged-offer-refusal',inputs=count,passed=True))
    count=0
    for port,value in [(0x21,0),(0x3fb,0x83),(0x3f9,1),(0x3fc,3),(0x3fd,0x20),(0x3fd,0x62)]:
        reject(8,lambda port=port,value=value:ports.update({port:value}));count+=1
    reject(8,lambda:u.mem_write(0x30,b'\x35\x12'));count+=1
    reject(8,lambda:model.put('hardware_active',0,1));count+=1
    reject(8,lambda:u.mem_write(0x400,b'\xf8\x02'));count+=1
    cases.append(dict(case='quiet-UART-mask-vector-register-and-overrun-refusal',inputs=count,passed=True))
    # Locate the pinned compiler's simple private phase getter rather than
    # guessing a private data address. READY must reject without driver IO.
    getter=bytes(u.mem_read(model.symbols['_mouse_owner_phase_impl'],4));assert getter[0]==0xa1 and getter[3]==0xc3
    held_phase=struct.unpack_from('<H',getter,1)[0]
    reject(7,lambda:u.mem_write(model.data_base+held_phase,b'\x01\0'))
    cases.append(dict(case='mouse-owner-must-be-closed-or-suspended',inputs=1,passed=True))
    count=0
    for change,want in [(lambda:model.put('_terminal_sound_enabled',0),3),
                        (lambda:model.put('_terminal_hook_input_bound',0),2),
                        (lambda:u.mem_write(model.symbols['_terminal_hook_proposal']+830+0x200,b'!'),4),
                        (lambda:ports.update({0x3f9:1}),8)]:
        reset();assert far('_terminal_hook_apply_check',[result])==0
        change();original=stable()
        assert far('_terminal_hook_apply',[result])==want
        assert stable()==original and not publishing;count+=1
    cases.append(dict(case='commit-rechecks-prepared-state-before-publication',inputs=count,passed=True))
    sources=dict(manifest['sources'])
    for name in ['standalone/check_hook_apply.py','standalone/dos_image.py','standalone/check_setup_model.py',
                 'standalone/check_startup_import.py','standalone/check_modem_import.py']:sources[name]=sha(ROOT/name)
    for name,digest in sources.items():assert sha(ROOT/name)==digest,name
    report=dict(passed=True,inputs=sum(c['inputs']for c in cases),cases=cases,sources=sources,binary_sha256=manifest['binary_sha256'],
                private_phase_getter_hex=getter.hex(),scope='Actual linked stage/check/publish using real parser/configuration/mouse code. '
                'UART IN values are explicit unit fixtures; interrupts and port writes prohibited, all IO prohibited after publication begins. '
                'Actual acquired UART/mouse/KEY workflows checked separately in DOS. No physical/BBS acceptance.')
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS',report['inputs'],'linked application cases')


if __name__=='__main__':main()
