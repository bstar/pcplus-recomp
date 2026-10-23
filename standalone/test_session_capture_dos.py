#!/usr/bin/env python3
"""Exercise the shared capture from real live-setup handoff in8086 DOS."""
import argparse,hashlib,json,re,shutil,struct,subprocess
from pathlib import Path
import test_setup_startup_dos as harness
from check_setup_model import image
from check_startup_import import terminal_expected
ROOT=harness.ROOT
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    base=ROOT/'build/terminal-directory-keys-process-bank-session-capture'
    harness.OUT=out;harness.BINARY=base/'TERMINAL.EXE';harness.EDITOR=ROOT/'build/setup-mouse-notice-sound/PRMEDIT.EXE'
    m=json.loads((base/'manifest.json').read_text());assert m['experimental_session_capture'] and sha(harness.BINARY)==m['binary_sha256']
    listing=(base/'terminal.map').read_text();group=re.search(r'^DGROUP\s+([0-9a-f]+):',listing,re.M|re.I);assert group
    match=re.search(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+terminal_setup_plan\s*$',listing,re.M|re.I);assert match
    assert int(group[1],16)==int(match[1],16)
    # The child observes its suspended parent's captured plan. DOS MZ entry ES
    # identifies the child's PSP; PSP16h identifies the direct parent. No vendor
    # executable or guessed runtime address is used.
    source=f'''BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
..start:
 push es
 mov ax,seg name
 mov ds,ax
 mov dx,name
 xor cx,cx
 mov ah,0x3c
 int 0x21
 pop es
 jc failed
 mov bx,ax
 mov ax,[es:0x16]
 add ax,{16+int(group[1],16)}
 push ds
 mov ds,ax
 mov dx,{int(match[2],16)}
 mov cx,628
 mov ah,0x40
 int 0x21
 pop ds
 jc failed
 cmp ax,628
 jne failed
 mov ah,0x3e
 int 0x21
 jc failed
 mov ax,0x4c00
 int 0x21
failed:
 mov ax,0x4c01
 int 0x21
SEGMENT _DATA public class=DATA use16
name: db 'D:\\PLANCAP.BIN',0
SEGMENT STACK stack class=STACK use16
 resb 1024
'''
    (out/'observer.asm').write_text(source)
    subprocess.run(['nasm','-fobj',str(out/'observer.asm'),'-o',str(out/'observer.obj')],check=True)
    subprocess.run(['wlink','system','dos','option','quiet','name',str(out/'OBSERVER.EXE'),'file',str(out/'observer.obj')],check=True)
    payload=bytearray(image());struct.pack_into('<HH',payload,0x4e4,8,4);payload=bytes(payload)
    cases=[]
    r,actual=harness.run('observe',keys='p2000 a-f10 p500 space r e a d y',arguments='@TEST.PRM 19200',rate=19200,
        rate_mask=4,line_mask=1,post_echo=True,payload=payload,child_binary=out/'OBSERVER.EXE',cpu='8086')
    expected=bytearray(terminal_expected(payload)+bytes(368+214+2));struct.pack_into('<HH',expected,2,19200,0)
    struct.pack_into('<H',expected,44+366,350) # Serial-only startup keeps the default BREAK policy.
    assert (out/'observe/PLANCAP.BIN').read_bytes()==expected and actual==payload
    r['checks']['exact_captured_plan_with_CLI_rate_and_inactive_modem']=True;cases.append(r)
    for name,keys,color in [('cancel','p2000 a-f10 p500 escape space r e a d y',7),
        ('color','p2000 a-f10 p500 pgdown tab tab tab home del del 1 e f10 escape space r e a d y',30)]:
        r,actual=harness.run(name,keys=keys,arguments='@TEST.PRM',post_echo=True,rate_mask=1,line_mask=1,payload=payload,cpu='8086')
        expected=bytearray(payload);struct.pack_into('<H',expected,0x1ae,color)
        assert actual==expected
        screen=(out/name/'SCREEN.BIN').read_bytes()
        assert screen[22:32:2]==b' LIVE' and screen[23:33:2]==bytes([color])*5
        assert b'ready' in (out/name/'serial.bin').read_bytes()
        r['checks']['exact_saved_image_and_resumed_palette']=True;cases.append(r)
    sources=dict(m['sources'])
    editor=json.loads((harness.EDITOR.parent/'manifest.json').read_text());assert sha(harness.EDITOR)==editor['binary_sha256']
    for n,h in editor['sources'].items():assert n not in sources or sources[n]==h,n;sources[n]=h
    for n in ['standalone/test_session_capture_dos.py','standalone/test_setup_startup_dos.py','standalone/check_setup_model.py','standalone/check_startup_import.py','standalone/check_modem_import.py','standalone/terminal_config_fixtures.py','standalone/test_terminal.py','standalone/setup_watch.asm']:sources[n]=sha(ROOT/n)
    for n,h in sources.items():
        assert sha(ROOT/n)==h,n
        dest=out/'source'/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/n,dest)
    report=dict(passed=True,cases=cases,sources=sources,binary_sha256=m['binary_sha256'],editor_sha256=editor['binary_sha256'],
        scope='Three actual8086 DOS live setup workflows using shared capture: source child reads exact628-byte suspended-parent plan with CLI19200; real editor cancel/color save resumes serial/palette. Serial-only startup has no active modem plan. Actual-session policy1 separately linked-tested; no terminal HOOK or returned helper commit.')
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS three8086 DOS capture/setup workflows')
if __name__=='__main__':main()
