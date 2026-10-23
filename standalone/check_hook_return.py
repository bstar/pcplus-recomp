#!/usr/bin/env python3
"""Execute linked returned-PRM validation and semantic change classification."""
import argparse
import hashlib
import json
import re
import struct
from pathlib import Path
from unicorn import UC_HOOK_INTR, UC_HOOK_INSN
from unicorn.x86_const import *
from dos_image import DosImage
from check_setup_model import image
from check_startup_import import terminal_expected
from check_modem_import import expected as modem_expected

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--hook-execute', action='store_true')
    parser.add_argument('--hook-modem', action='store_true')
    parser.add_argument('--hook-input', action='store_true')
    args = parser.parse_args()
    output = args.output.resolve()
    assert output.is_relative_to(ROOT / 'build') and not output.exists()
    output.mkdir(parents=True)
    base = ROOT / 'build/terminal-directory-keys-process-bank-session-capture-projection-bound-registers-controls-return'
    if args.hook_execute: base = base.with_name(base.name + '-execute')
    if args.hook_modem:
        assert args.hook_execute
        base = base.with_name(base.name + '-modem')
    if args.hook_input:
        assert args.hook_modem
        base=base.with_name(base.name+'-input')
    manifest = json.loads((base / 'manifest.json').read_text())
    assert manifest['experimental_hook_return'] and sha(base / 'TERMINAL.EXE') == manifest['binary_sha256']
    if args.hook_execute: assert manifest['experimental_hook_execute']
    model = DosImage(base / 'TERMINAL.EXE', base / 'terminal.map')
    u = model.uc
    seg, off = re.search(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+_hook_return_validate\s*$',
                         (base / 'terminal.map').read_text(), re.M | re.I).groups()
    cs, ip = model.base_segment + int(seg, 16), int(off, 16)
    top = model.offset('terminal_stack_top')
    # Source buffers and caller outputs occupy the upper half of the real
    # application stack. The callee's two decoded plans grow below this frame.
    before, after, dest, result = top - 1280, top - 2550, top - 3050, top - 3070
    sp = top - 3100
    def prohibited(*unused):
        raise AssertionError('returned-PRM validator attempted interrupt or port IO')
    u.hook_add(UC_HOOK_INTR, prohibited)
    for insn in [UC_X86_INS_IN, UC_X86_INS_OUT]:
        u.hook_add(UC_HOOK_INSN, prohibited, None, 1, 0, insn)
    raw = bytearray(image())
    struct.pack_into('<HH', raw, 0x4e4, 8, 4)
    raw = bytes(raw)
    cases = []
    def invoke(first=raw, second=raw, active=1, pointers=None, flags=0x202, ds=None, ss=None):
        u.mem_write(model.data_base + before, bytes(first))
        u.mem_write(model.data_base + after, bytes(second))
        u.mem_write(model.data_base + dest, b'X' * 490)
        u.mem_write(model.data_base + result, b'R' * 8)
        regs = {UC_X86_REG_CS:cs, UC_X86_REG_IP:ip, UC_X86_REG_DS:model.ds if ds is None else ds,
                UC_X86_REG_SS:model.ds if ss is None else ss, UC_X86_REG_SP:sp,
                UC_X86_REG_EFLAGS:flags, UC_X86_REG_BP:0xbabe, UC_X86_REG_SI:0x1234, UC_X86_REG_DI:0x5678}
        for register, value in regs.items():u.reg_write(register, value)
        argv = [before, after, active, dest, result] if pointers is None else pointers
        u.mem_write(regs[UC_X86_REG_SS] * 16 + sp, struct.pack('<7H', model.return_offset, model.code_segment, *argv))
        globals_before = bytes(u.mem_read(model.data_base, top - 8192))
        model.returned = False
        u.emu_start(cs * 16 + ip, 0, count=500000)
        assert model.returned and u.reg_read(UC_X86_REG_SP) == sp + 4
        for register in [UC_X86_REG_DS,UC_X86_REG_SS,UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI]:
            assert u.reg_read(register) == regs[register]
        assert bytes(u.mem_read(model.data_base, top - 8192)) == globals_before
        assert bytes(u.mem_read(model.data_base + before, 1264)) == first
        assert bytes(u.mem_read(model.data_base + after, 1264)) == second
        status = u.reg_read(UC_X86_REG_AX)
        candidate = bytes(u.mem_read(model.data_base + dest, 490))
        detail = bytes(u.mem_read(model.data_base + result, 8))
        if status:assert candidate == b'X' * 490
        return status, candidate, detail
    def done(name, count=1):
        cases.append(dict(case=name, inputs=count, passed=True))
        print(name, count, flush=True)
    status, candidate, detail = invoke()
    assert status == 0 and struct.unpack_from('<3H', candidate) == (1,0,0)
    assert candidate[6:50] == terminal_expected(raw)
    assert candidate[50:418] == modem_expected(raw)
    assert candidate[418:484] == struct.pack('<H',0) + b'.\0'.ljust(64,b'\0')
    assert candidate[484:] == struct.pack('<3H', int(struct.unpack_from('<H',raw,0x1bc)[0]!=0),8,4)
    done('unchanged-full-decoded-plan')
    # Independent field edit vectors: the expected application categories are
    # frozen here rather than read from the implementation's byte allowlist.
    edits = [(0,1,1), (2,3,2), (4,1,4), (6,2,4), (8,7,4), (0x198,1,8),
             (0x194,6,16), (0x19c,0,32), (0x19e,0,32), (0x1ae,30,32),
             (0x1b0,31,32), (0x1b2,32,32), (0x1b4,33,32), (0x1b6,0,32),
             (0x1e4,31,64|128), (0x1a4,123,512), (0x1e0,2,2048),
             (0x4ea,32,4096), (0x42c,1,8192), (0x4e4,999,16384), (0x4e6,1,16384),
             (0x1bc,0,32768), (0xa,46,128), (0xc,3,128), (0xe,0,128),
             (0x10,0,128), (0x14,1,128), (0x16,4,128)]
    for at, value, mask in edits:
        changed = bytearray(raw);struct.pack_into('<H',changed,at,value)
        status, candidate, _ = invoke(second=bytes(changed))
        assert status == 0 and struct.unpack_from('<3H',candidate) == (1,mask,1), (at,status,candidate[:6].hex())
    done('supported-word-edits-classified',len(edits))
    for at, data, mask in [(0x12,b'\x1b',128),(0x1e2,b'!',64|128),
                           (0x18,b'ATX^M\0',128),(0x31c,b'D:\\FILES\0',8192)]:
        changed=bytearray(raw);changed[at:at+len(data)]=data
        status,candidate,_=invoke(second=bytes(changed))
        assert status==0 and struct.unpack_from('<3H',candidate)==(1,mask,1),(at,status)
    done('byte-command-and-path-edits',4)
    for at in [0x1bc,0x42c]:
        first=bytearray(raw);second=bytearray(raw)
        struct.pack_into('<H',first,at,0xffff);struct.pack_into('<H',second,at,1)
        status,candidate,_=invoke(bytes(first),bytes(second))
        assert status==0 and struct.unpack_from('<3H',candidate)==(1,0,1)
    first=bytearray(raw);second=bytearray(raw);second[0x18+46]^=1
    status,candidate,_=invoke(bytes(first),bytes(second))
    assert status==0 and struct.unpack_from('<3H',candidate)==(1,0,1)
    assert candidate[50+18:50+65] == second[0x18:0x47]
    done('raw-representation-and-opaque-known-string-tail',3)
    inactive=bytearray(raw);inactive[0xa:0x174]=b'\xff'*(0x174-0xa)
    status,candidate,_=invoke(bytes(inactive),bytes(inactive),0)
    assert status==0 and struct.unpack_from('<3H',candidate)==(0,0,0)
    assert candidate[50:418]==struct.pack('<8H',0,0,0,0,0,0,30,ord('~'))+bytes(350)+raw[0x1a4:0x1a6]
    done('inactive-private-group-opaque',1)
    # Exhaust every byte outside the independently declared supported schema.
    words=[0,2,4,6,8,0x194,0x198,0x19a,0x19c,0x19e,0x1a4,0x1ae,0x1b0,0x1b2,
           0x1b4,0x1b6,0x1bc,0x1e0,0x1e4,0x42c,0x4e4,0x4e6,0x4ea,0x174,0x184]
    common={at+i for at in words for i in [0,1]}|{0x1e2}|set(range(0x31c,0x35c))
    private=set(range(0xa,0x13))|set(range(0x14,0x174))
    total=0
    for active in [0,1]:
        source=raw if active else bytes(inactive)
        for at in sorted(set(range(1264))-(common|(private if active else set()))):
            second=bytearray(source);second[at]^=1
            status,_,detail=invoke(source,bytes(second),active)
            assert status==6 and struct.unpack('<4H',detail)==(6,0,2,at),(active,at,status)
            total+=1
    done('every-unsupported-byte-refused',total)
    for at,value,want in [(0,4,2),(2,9,2),(0x198,2,2),(0xa,0,3),
                          (0x4e4,0,5),(0x4e6,1000,5),(0x4ea,256,2)]:
        changed=bytearray(raw);struct.pack_into('<H',changed,at,value)
        status,_,detail=invoke(second=bytes(changed));assert status==want,(at,status)
        assert struct.unpack('<4H',detail)[2]==1
    changed=bytearray(raw);changed[0x18:0x18+2]=b'^\0'
    assert invoke(second=bytes(changed))[0]==3
    done('malformed-known-values-and-command-expansion',8)
    # Expanded response bytes must survive the helper boundary literally and
    # be usable by the actual recovered matcher linked into this executable.
    response_cases=0
    for slot in range(11):
        at=0xc4+slot*16
        for value in range(1,256):
            changed=bytearray(raw);changed[at:at+2]=bytes([value,0])
            status,candidate,_=invoke(second=bytes(changed))
            semantic=raw[at:at+16].split(b'\0')[0]!=bytes([value])
            assert status==0 and struct.unpack_from('<3H',candidate)==(1,128 if semantic else 0,int(changed!=raw))
            assert candidate[50:418]==modem_expected(changed)
            slots=bytearray(176);slots[slot*16:slot*16+16]=candidate[50+190+slot*16:50+206+slot*16]
            u.mem_write(model.symbols['modem_response_slots'],bytes(slots))
            assert model.call('modem_responses_reset_bounded')==0
            assert model.call('modem_responses_feed_bounded',[value])==slot
            response_cases+=1
        changed=bytearray(raw);changed[at:at+3]=b'^M\0'
        status,candidate,_=invoke(second=bytes(changed));assert status==0
        slots=bytearray(176);slots[slot*16:slot*16+16]=candidate[50+190+slot*16:50+206+slot*16]
        u.mem_write(model.symbols['modem_response_slots'],bytes(slots))
        assert model.call('modem_responses_reset_bounded')==0
        assert model.call('modem_responses_feed_bounded',[ord('^')])==65535
        assert model.call('modem_responses_feed_bounded',[ord('M')])==slot
        changed[at:at+16]=b'X'*16
        assert invoke(second=bytes(changed))[0]==3
        response_cases+=2
    done('literal-expanded-response-bytes-through-actual-matcher',response_cases)
    for pointers in [[0,after,1,dest,result],[before,0,1,dest,result],
                     [before,after,1,0,result],[before,after,1,dest,0],
                     [before,before,1,dest,result],[before,after,1,before,result],
                     [before,after,1,dest,dest],[0xfff0,after,1,dest,result]]:
        assert invoke(pointers=pointers)[0]==1
    for flags,ds,ss in [(0x2,None,None),(0x602,None,None),(0x202,model.ds+1,None),(0x202,None,model.ds+1)]:
        assert invoke(flags=flags,ds=ds,ss=ss)[0]==1
    assert invoke(active=2)[0]==1
    done('argument-alias-wrap-and-CPU-context-refusal',13)
    sources=dict(manifest['sources'])
    for name in ['standalone/check_hook_return.py','standalone/dos_image.py','standalone/check_setup_model.py',
                 'standalone/check_startup_import.py','standalone/check_modem_import.py','standalone/terminal_config_fixtures.py']:
        sources[name]=sha(ROOT/name)
    for name,digest in sources.items():assert sha(ROOT/name)==digest,name
    report=dict(passed=True,inputs=sum(case['inputs'] for case in cases),cases=cases,sources=sources,
                binary_sha256=manifest['binary_sha256'],scope='Linked actual far validator/decoders/native expansion. '
                'Every unsupported byte, semantic/raw distinctions, inactive modem group, atomic refusal and calling convention. '
                'No hardware/filesystem service is allowed. No DOS helper EXEC, foreground application or full HOOK acceptance.')
    (output/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS',report['inputs'],'linked returned-PRM cases')


if __name__=='__main__':main()
