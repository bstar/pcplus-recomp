#!/usr/bin/env python3
"""Execute passive observer handlers and verify transparent chaining."""
import argparse
import json
import struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_CODE,UC_HOOK_INTR
from unicorn.x86_const import *
from carrier_key_observer import build,FIELDS
from product_inputs import ROOT,sha


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('terminal','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir()
    source,meta=build(a.terminal,out/'observer');raw=(out/'observer/observer.com').read_bytes()
    cases=[]
    def exercise(label,ax=0x1000,enabled=1,foreign=False,empty=False,bad_irq=False,full=False,timer=False):
        u=Uc(UC_ARCH_X86,UC_MODE_16);u.mem_map(0,0x100000)
        own=0x8000;parent=0x1000+meta['parent_ds'];ss=parent;sp=0xff00
        u.mem_write(own*16+0x100,raw)
        sym={k:own*16+v for k,v in meta['offsets'].items()}
        for name in ('old_vector','old_keyboard_vector'):u.mem_write(sym[name],struct.pack('<2H',0,0xe000))
        u.mem_write(0x34,struct.pack('<2H',meta['uart_entry_offset']+(1 if bad_irq else 0),0x1000))
        u.mem_write(0x10000+meta['uart_entry_offset'],bytes.fromhex(meta['uart_signature']))
        u.mem_write(0x41a,struct.pack('<2H',0x1e,0x1e if empty else 0x20))
        u.mem_write(0x41e,struct.pack('<H',0x2960));u.mem_write(0x46c,struct.pack('<H',12345))
        values={n:i+3 for i,n in enumerate(FIELDS[6:])}
        for n,v in values.items():u.mem_write(parent*16+meta['field_offsets'][n],struct.pack('<H',v))
        u.mem_write(sym['trace_meta']+2,struct.pack('<3H',16 if full else 0,enabled,0))
        if timer:
            u.mem_write(0xb8000+3840,b''.join(bytes([c,0x1f]) for c in b' RX carrier lost'.ljust(80,b' ')))
        registers={UC_X86_REG_AX:ax,UC_X86_REG_BX:0x9876,UC_X86_REG_CX:0x3456,
                   UC_X86_REG_DX:0xabcd,UC_X86_REG_SI:0x1234,UC_X86_REG_DI:0x5678,
                   UC_X86_REG_BP:0xbabe,UC_X86_REG_DS:parent+(1 if foreign else 0),
                   UC_X86_REG_ES:0x2468,UC_X86_REG_SS:ss,UC_X86_REG_SP:sp}
        frame=struct.pack('<3H',0x4567,0x1000,0x202);u.mem_write(ss*16+sp,frame)
        for reg,v in registers.items():u.reg_write(reg,v)
        u.reg_write(UC_X86_REG_CS,own);u.reg_write(UC_X86_REG_IP,meta['offsets']['handler' if timer else 'key_handler'])
        u.reg_write(UC_X86_REG_EFLAGS,0x46) # Real interrupt entry has IF cleared.
        before=bytes(u.mem_read(parent*16,0xfe00));bda=bytes(u.mem_read(0x400,0x100));done=[]
        def stop(u,address,size,unused):
            if address==0xe0000:done.append(True);u.emu_stop()
        def forbidden(*args):raise AssertionError('Observer callback invoked an interrupt')
        u.hook_add(UC_HOOK_CODE,stop);u.hook_add(UC_HOOK_INTR,forbidden)
        u.emu_start(own*16+meta['offsets']['handler' if timer else 'key_handler'],0,count=10000)
        assert done,label
        for reg,v in registers.items():assert u.reg_read(reg)==v,(label,reg)
        assert u.reg_read(UC_X86_REG_EFLAGS)&0xffff==0x46,label
        assert bytes(u.mem_read(parent*16,0xfe00))==before
        assert bytes(u.mem_read(ss*16+sp,6))==frame and bytes(u.mem_read(0x400,0x100))==bda
        count,now_enabled,overflow=struct.unpack('<3H',u.mem_read(sym['trace_meta']+2,6))
        if timer:
            assert now_enabled==1 and count==0
        elif enabled and not foreign and not empty and not bad_irq and not full and ax>>8 in (0,16):
            assert count==1
            row=dict(zip(FIELDS,struct.unpack('<16H',u.mem_read(sym['trace_records'],32))))
            assert row==dict(tick=12345,key=0x2960,caller_ip=0x4567,caller_cs=0x1000,
                             read_ax=ax,parent_ds=parent,**values),row
        else:
            assert count==(16 if full else 0)
        if full:assert overflow==1
        cases.append(dict(case=label,passed=True))
    exercise('standard-read',ax=0x0088)
    exercise('enhanced-read')
    exercise('peek-chains',ax=0x0100)
    exercise('producer-chains',ax=0x0500)
    exercise('disabled',enabled=0)
    exercise('foreign-caller',foreign=True)
    exercise('empty-keyboard',empty=True)
    exercise('foreign-IRQ',bad_irq=True)
    exercise('full-buffer',full=True)
    exercise('carrier-notice-enables',enabled=0,timer=True)
    result=dict(passed=True,cases=cases,observer=meta,sources={n:sha(ROOT/n) for n in
        ['lab/bbs/check_carrier_key_observer.py','lab/bbs/carrier_key_observer.py',
         'lab/bbs/carrier_notice_watch.py','lab/bbs/zmodem_label_watch.py','standalone/test_terminal.py']},
        scope=__doc__+' Actual assembled 8086 handlers; all registers, FLAGS, original interrupt frame, parent non-stack memory and BIOS data unchanged. No callback DOS/BIOS interrupts. Modeled old vector endpoint; real installation/restoration and live observations require separate DOS run.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS',len(cases),'transparent observer cases; same201 retained paragraphs')


if __name__=='__main__':main()
