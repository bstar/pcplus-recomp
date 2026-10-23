#!/usr/bin/env python3
"""Observe retained PRM generation before and after accepted/rejected live children."""
import argparse,hashlib,json,re,shutil,struct,subprocess
from pathlib import Path
import test_setup_startup_dos as harness
from check_setup_model import image
ROOT=harness.ROOT
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def sealed(raw,generation,kind):
    h=0xb41d^generation^kind
    for value in struct.unpack('<632H',raw):h=((h<<1)|(h>>15))&65535;h^=value
    return struct.pack('<4H',0xb451,generation,kind,h)+raw
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    base=ROOT/'build/terminal-directory-keys-process-bank-session-capture-projection-bound';m=json.loads((base/'manifest.json').read_text())
    assert m['experimental_session_baseline'] and sha(base/'TERMINAL.EXE')==m['binary_sha256']
    match=re.search(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+terminal_baseline_storage\s*$',(base/'terminal.map').read_text(),re.M|re.I);assert match
    harness.OUT=out;harness.BINARY=base/'TERMINAL.EXE';cases=[]
    raw=bytearray(image());struct.pack_into('<HH',raw,0x4e4,8,4);raw=bytes(raw)
    for name,field,value in [('accepted',0x1ae,30),('rejected',0x194,7)]:
        source=f'''BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
..start:
 mov ax,[es:0x16]
 add ax,{16+int(match[1],16)}
 mov [cs:parent_segment],ax
 push cs
 pop ds
 mov dx,flag_name
 mov ax,0x3d00
 int 0x21
 jc first
 mov bx,ax
 mov ah,0x3e
 int 0x21
 jc failed
 mov byte [state_name+5],'2'
 jmp snapshot
first:
 cmp ax,2
 jne failed
 mov byte [first_call],1
 xor cx,cx
 mov ah,0x3c
 int 0x21
 jc failed
 mov bx,ax
 mov ah,0x3e
 int 0x21
 jc failed
snapshot:
 mov dx,state_name
 xor cx,cx
 mov ah,0x3c
 int 0x21
 jc failed
 mov bx,ax
 push ds
 mov ds,[parent_segment]
 mov dx,{int(match[2],16)}
 mov cx,1272
 mov ah,0x40
 int 0x21
 pop ds
 jc failed
 cmp ax,1272
 jne failed
 mov ah,0x3e
 int 0x21
 jc failed
 cmp byte [first_call],0
 je success
 mov dx,settings_name
 mov ax,0x3d00
 int 0x21
 jc failed
 mov bx,ax
 mov dx,buffer
 mov cx,1264
 mov ah,0x3f
 int 0x21
 jc failed
 cmp ax,1264
 jne failed
 mov ah,0x3e
 int 0x21
 jc failed
 mov word [buffer+{field}],{value}
 mov dx,settings_name
 xor cx,cx
 mov ah,0x3c
 int 0x21
 jc failed
 mov bx,ax
 mov dx,buffer
 mov cx,1264
 mov ah,0x40
 int 0x21
 jc failed
 cmp ax,1264
 jne failed
 mov ah,0x3e
 int 0x21
 jc failed
success:
 mov ax,0x4c00
 int 0x21
failed:
 mov ax,0x4c01
 int 0x21
parent_segment: dw 0
first_call: db 0
state_name: db 'STATE1.BIN',0
flag_name: db 'SECOND.FLG',0
settings_name: db 'TEST.PRM',0
buffer: times 1264 db 0
SEGMENT STACK stack class=STACK use16
 resb 1024
'''
        asm=out/(name+'.asm');obj=out/(name+'.obj');child=out/(name+'.EXE');asm.write_text(source)
        subprocess.run(['nasm','-fobj',str(asm),'-o',str(obj)],check=True)
        subprocess.run(['wlink','system','dos','option','quiet','name',str(child),'file',str(obj)],check=True)
        rebuild=out/(name+'-rebuild');rebuild.mkdir()
        subprocess.run(['nasm','-fobj',str(asm),'-o',str(rebuild/'child.obj')],check=True)
        subprocess.run(['wlink','system','dos','option','quiet','name',str(rebuild/'CHILD.EXE'),'file',str(rebuild/'child.obj')],check=True)
        assert sha(child)==sha(rebuild/'CHILD.EXE')
        r,actual=harness.run(name,keys='p2000 a-f10 p700 space p500 a-f10 p700 space r e a d y',arguments='@TEST.PRM',
            payload=raw,child_binary=child,post_echo=True,rate_mask=1,line_mask=1,expected_profile=4,cpu='8086')
        changed=bytearray(raw);struct.pack_into('<H',changed,field,value);assert actual==changed
        assert (out/name/'STATE1.BIN').read_bytes()==sealed(raw,1,1)
        expected_state=sealed(bytes(changed),2,2) if name=='accepted' else sealed(raw,1,1)
        assert (out/name/'STATE2.BIN').read_bytes()==expected_state
        screen=(out/name/'SCREEN.BIN').read_bytes();color=30 if name=='accepted' else 7
        assert screen[22:32:2]==b' LIVE' and screen[23:33:2]==bytes([color])*5
        assert b'ready' in (out/name/'serial.bin').read_bytes()
        r['checks']['exact_retained_image_before_first_child']=True
        r['checks']['accepted_ack_advances_or_rejected_image_retains_baseline']=True
        r['checks']['active_profile_palette_and_serial_continue']=True
        r['child_sha256']=sha(child);r['child_reproduces']=True;cases.append(r)
    sources=dict(m['sources'])
    for n in ['standalone/test_session_baseline_live_dos.py','standalone/test_setup_startup_dos.py','standalone/check_setup_model.py','standalone/check_modem_import.py','standalone/terminal_config_fixtures.py','standalone/test_terminal.py','standalone/setup_watch.asm']:sources[n]=sha(ROOT/n)
    for n,h in sources.items():
        assert sha(ROOT/n)==h,n
        dest=out/'source'/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/n,dest)
    report=dict(passed=True,cases=cases,sources=sources,binary_sha256=m['binary_sha256'],
        scope='Two actual8086 DOS sessions with two source-built children each. Suspended-parent far store observed before/after accepted color and rejected profile edits; exact seals/images, active palette/profile and post-child serial continuation. Controlled PRMEDIT fixture child, not production editor UI or native HOOK helper.')
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS two live8086 retained-baseline workflows')
if __name__=='__main__':main()
