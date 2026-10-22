#!/usr/bin/env python3
"""Actual linked confirmation-frame owner; BIOS/admission endpoints are modeled."""
import argparse,json,struct
from pathlib import Path
from unicorn.x86_const import *
import check_terminal_cooperative_window as cooperative

ROOT=cooperative.ROOT

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--mouse',action='store_true');a=parser.parse_args()
    if a.mouse:cooperative.legacy.PRODUCT='terminal-mouse'
    cases=[]
    for mode in (0,16):
        w=cooperative.Window();w.put('keyboard_bios_mode',mode,1)
        assert w.parent(12,0)==0 and w.get('terminal_script_confirm_active')==1
        assert b'PCPLUS  //  STOP SCRIPT?' in bytes(w.uc.mem_read(0xb8000,4000))[::2]
        copies=w.copies[:]
        for _ in range(100):assert w.parent(12,4)==0
        assert w.copies==copies and not w.reads and not w.callbacks
        w.near('terminal_script_window_hide')
        updated=bytes((i*19+mode)&255 for i in range(4000));w.uc.mem_write(0xb8000,updated);w.cursor=0x0516
        assert w.parent(12,1)==0
        assert b' No ' in bytes(w.uc.mem_read(0xb8000,4000))[::2]
        assert w.parent(12,2)==0
        assert b' Yes ' in bytes(w.uc.mem_read(0xb8000,4000))[::2]
        assert w.parent(12,3)==0 and not w.get('terminal_script_confirm_active')
        w.closed(updated,0x0516)
        copies=w.copies[:];assert w.parent(12,3)==0 and w.copies==copies
        assert w.get('terminal_aspect_active')==0
        cases.append(dict(name='updated-frame-cursor-idle-budget-choice-retirement',mode=mode,passed=True))
    for field in ('_redisplay_active','_command_menu_active'):
        w=cooperative.Window();w.put(field,1)
        assert w.parent(12,0)==10 and w.copies==[0,0]
        cases.append(dict(name='reject-conflicting-'+field,passed=True))
    w=cooperative.Window();assert w.near('terminal_script_confirm',bx=0,interrupts=False)==10 and w.copies==[0,0]
    cases.append(dict(name='reject-disabled-interrupts-before-frame-copy',passed=True))
    w=cooperative.Window();w.open();before=bytes(w.uc.mem_read(0xb8000,4000))
    assert w.parent(12,0)==10 and bytes(w.uc.mem_read(0xb8000,4000))==before
    assert not w.get('terminal_script_confirm_active')
    cases.append(dict(name='reference-window-cannot-be-replaced-by-confirmation',passed=True))
    w=cooperative.Window();assert w.parent(12,0)==0;before=bytes(w.uc.mem_read(0xb8000,4000))
    for operation,value in [(12,0),(11,1),(8,0x2c00)]:
        assert w.parent(operation,value)==10 and bytes(w.uc.mem_read(0xb8000,4000))==before
    assert not w.reads and not w.callbacks and w.get('terminal_script_confirm_active')==1
    assert w.parent(12,5)==7
    cases.append(dict(name='confirmation-rejects-reference-service-KEY-nesting-and-invalid-scalars',passed=True))
    w.uc.mem_write(w.symbols['_script_handoff']+22,struct.pack('<H',1))
    assert w.parent(12,4)==14 and bytes(w.uc.mem_read(0xb8000,4000))==before
    assert w.parent(12,3)==0 and not w.get('terminal_script_confirm_active');w.closed()
    cases.append(dict(name='returned-UART-rejects-draw-but-allows-frame-retirement',passed=True))
    for disposition in ('END','revoke'):
        w=cooperative.Window();assert w.parent(12,0)==0
        if disposition=='END':assert w.parent(2)==0
        else:w.near('terminal_render_revoke',far=True)
        assert not w.get('terminal_script_confirm_active') and not w.get('render_attached')
        w.closed();cases.append(dict(name='retire-on-'+disposition,passed=True))
    product=cooperative.legacy.PRODUCT
    out=ROOT/'build'/('terminal-abort-confirm-mouse' if a.mouse else 'terminal-abort-confirm');out.mkdir(exist_ok=True)
    report=dict(passed=True,cases=cases,terminal_sha256=cooperative.legacy.sha(ROOT/'build'/product/'TERMINAL.EXE'),
        checker_sha256=cooperative.legacy.sha(Path(__file__)),scope=__doc__)
    (out/'checks.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Terminal confirmation',product,len(cases),'linked groups PASS')

if __name__=='__main__':main()
