#!/usr/bin/env python3
"""Check actual linked transaction admission and discard without DOS or port IO."""
import argparse
import hashlib
import json
import re
import struct
from pathlib import Path
from unicorn import UC_HOOK_INTR, UC_HOOK_INSN
from unicorn.x86_const import *
from dos_image import DosImage

ROOT = Path(__file__).resolve().parents[1]


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--hook-modem', action='store_true')
    args = parser.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT / 'build') and not out.exists()
    out.mkdir(parents=True)
    base = ROOT / 'build/terminal-directory-keys-process-bank-session-capture-projection-bound-registers-controls-return-execute'
    if args.hook_modem:base=base.with_name(base.name+'-modem')
    manifest = json.loads((base / 'manifest.json').read_text())
    assert manifest['experimental_hook_execute'] and sha(base / 'TERMINAL.EXE') == manifest['binary_sha256']
    model = DosImage(base / 'TERMINAL.EXE', base / 'terminal.map')
    listing = (base / 'terminal.map').read_text()
    u = model.uc
    def prohibited(*unused): raise AssertionError('Admission/discard attempted interrupt or port IO')
    u.hook_add(UC_HOOK_INTR, prohibited)
    for insn in [UC_X86_INS_IN, UC_X86_INS_OUT]: u.hook_add(UC_HOOK_INSN, prohibited, None, 1, 0, insn)
    top = model.offset('terminal_stack_top')
    path, result, sp = top - 128, top - 180, top - 300
    proposal = model.symbols['_terminal_hook_proposal']
    private = model.symbols['_terminal_hook_before']
    cases = []
    def call(name='_terminal_hook_execute', text=b'HOOKCH.EXE\0', context=3,
             pointers=None, flags=0x202, foreign=False, phase=0, owner_phase=0,
             owner_segment=0, register_phase=0):
        u.mem_write(model.data_base + path, text.ljust(64, b'X'))
        u.mem_write(model.data_base + result, b'R' * 20)
        u.mem_write(proposal, b'X' * 2584)
        u.mem_write(private, b'B' * 1264)
        model.put('_terminal_hook_phase', phase)
        owner = model.symbols['_terminal_hook_owner']
        u.mem_write(owner + 2, struct.pack('<3H', owner_phase, 0, owner_segment))
        u.mem_write(model.symbols['_terminal_register_owner'], struct.pack('<H', register_phase))
        address = model.symbols[name]
        segment, offset = re.search(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+'+name+r'\s*$',listing,re.M|re.I).groups()
        cs, ip = model.base_segment + int(segment,16), int(offset,16)
        argv = [] if name.endswith('discard') else [path, context & 65535, (context >> 16) & 65535, result]
        if pointers is not None: argv = pointers
        u.mem_write(model.data_base + sp, struct.pack('<' + 'H' * (2 + len(argv)), model.return_offset, model.code_segment, *argv))
        regs = {UC_X86_REG_CS:cs, UC_X86_REG_IP:ip, UC_X86_REG_DS:model.ds + int(foreign),
                UC_X86_REG_SS:model.ds, UC_X86_REG_SP:sp, UC_X86_REG_EFLAGS:flags,
                UC_X86_REG_BP:0xbabe, UC_X86_REG_SI:0x1234, UC_X86_REG_DI:0x5678}
        for reg, value in regs.items(): u.reg_write(reg, value)
        model.returned = False
        u.emu_start(address, 0, count=1000000)
        assert model.returned and u.reg_read(UC_X86_REG_SP) == sp + 4
        for reg in [UC_X86_REG_DS,UC_X86_REG_SS,UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI]:
            assert u.reg_read(reg) == regs[reg]
        assert bytes(u.mem_read(proposal,2584)) == b'X' * 2584
        assert bytes(u.mem_read(private,1264)) == b'B' * 1264
        return u.reg_read(UC_X86_REG_AX), bytes(u.mem_read(model.data_base + result,20))
    for pointers in [[0,3,0,result],[path,3,0,0],[65530,3,0,result],[path,3,0,65530],[path,3,0,path]]:
        assert call(pointers=pointers) == (1,b'R'*20)
        cases.append('pointer geometry')
    for flags, foreign in [(2,False),(0x602,False),(0x202,True)]:
        assert call(flags=flags,foreign=foreign) == (1,b'R'*20)
        cases.append('CPU context')
    for context in [-32769,32768]:
        assert call(context=context)[0] == 1
        cases.append('context range')
    for at in range(64):
        for control in [b'\r',b'\n']:
            assert call(text=b'A'*at+control+b'\0'*(63-at))[0] == 1
            cases.append('path control')
    for text in [b'\0',b'A'*64]:
        assert call(text=text)[0] == 1
        cases.append('path empty/unterminated')
    for kwargs in [dict(phase=1),dict(phase=2),dict(owner_phase=1),dict(owner_segment=1),dict(register_phase=1)]:
        assert call(**kwargs)[0] == 2
        cases.append('owner conflict')
    assert call()[0] == 3  # No retained startup baseline in this linked fixture.
    assert model.get('_terminal_hook_phase') == 0
    cases.append('unbound projection')
    for phase in [0,2]:
        assert call(name='_terminal_hook_discard',phase=phase)[0] == 0
        assert model.get('_terminal_hook_phase') == 0
        cases.append('discard')
    for kwargs in [dict(phase=1),dict(owner_phase=1),dict(owner_segment=1)]:
        assert call(name='_terminal_hook_discard',**kwargs)[0] == 2
        cases.append('discard owned')
    assert call(name='_terminal_hook_discard',flags=2)[0] == 1
    cases.append('discard CPU context')
    sources = dict(manifest['sources'])
    for name in ['standalone/check_hook_transaction.py','standalone/dos_image.py']: sources[name] = sha(ROOT / name)
    for name,digest in sources.items(): assert sha(ROOT / name) == digest,name
    report = dict(passed=True, inputs=len(cases), cases=cases, sources=sources, binary_sha256=manifest['binary_sha256'],
                  scope='Actual linked far transaction entry/discard admission. Pointer/CPU/path/context/owner/projection '
                  'refusal with unchanged proposal/private image. Interrupts and port IO prohibited. Real EXEC covered separately in DOS.')
    (out / 'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS',len(cases),'linked transaction admission/discard cases')


if __name__ == '__main__': main()
