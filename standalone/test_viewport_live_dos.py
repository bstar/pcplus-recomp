#!/usr/bin/env python3
"""Run the unmodified DOS application with an explicit test-only wide-view fixture."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess

import test_connection_dos as harness
ROOT=harness.ROOT


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--label',required=True)
    parser.add_argument('--fields',action='store_true',help='Seed a deleted field boundary and verify native region repair in wide mode')
    args=parser.parse_args();assert re.fullmatch('[A-Za-z0-9_-]+',args.label)
    out=ROOT/'build/viewport-live-dos'/args.label;out.mkdir(parents=True,exist_ok=False)
    binary=ROOT/'build/terminal/TERMINAL.EXE';listing=(ROOT/'build/terminal/terminal.map').read_text()
    group=re.search(r'^DGROUP\s+([0-9a-f]+):([0-9a-f]+)',listing,re.M|re.I)
    base=int(group[1],16)*16+int(group[2],16)
    symbols={name:int(seg,16)*16+int(off,16)-base for seg,off,name in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',listing,re.M|re.I)}
    names=['screen_columns','screen_attributes_base','screen_attribute_cells','erase_attribute_values_base',
        'erase_attribute_values','screen_cursor_wrap','attributes_normal_value','erase_cell_count',
        'screen_cursor_row','screen_cursor_column','screen_attribute_row_bytes','screen_last_column',
        'csi_row_count','csi_last_row','screen_last_row','screen_first_row','screen_viewport_enabled',
        'screen_viewport_active','screen_viewport_offset','screen_viewport_left','screen_viewport_right',
        'screen_attribute_offset','erase_shadow_segment','erase_shadow_offset']
    (out/'line_attributes_offsets.inc').write_text(''.join('%define '+name.upper()+' '+str(symbols[name])+'\n'for name in names))
    observer=ROOT/'standalone/line_attributes_watch.asm';text=observer.read_text()
    start=text.index(' push ds\n pop es\n mov di,SCREEN_ATTRIBUTE_CELLS')
    end=text.index(' inc word [cs:staged]',start)
    stage=''' mov word [SCREEN_ATTRIBUTE_ROW_BYTES],132
 mov word [SCREEN_LAST_COLUMN],131
 mov word [CSI_ROW_COUNT],24
 mov word [CSI_LAST_ROW],23
 mov word [SCREEN_LAST_ROW],23
 mov word [SCREEN_FIRST_ROW],0
 mov word [ERASE_CELL_COUNT],3168
 mov word [SCREEN_VIEWPORT_ENABLED],1
 mov word [SCREEN_VIEWPORT_ACTIVE],1
 mov word [SCREEN_VIEWPORT_OFFSET],0
 mov word [SCREEN_VIEWPORT_LEFT],52
 mov word [SCREEN_VIEWPORT_RIGHT],79
 mov word [SCREEN_ATTRIBUTE_OFFSET],677
 mov es,[ERASE_SHADOW_SEGMENT]
 mov di,[ERASE_SHADOW_OFFSET]
 mov ax,0xa55a
 mov cx,4096
 rep stosw
 mov di,[ERASE_SHADOW_OFFSET]
 mov ax,0x0720
 mov cx,3168
 rep stosw
 mov di,[ERASE_SHADOW_OFFSET]
 push ds
 mov ax,0xb800
 mov ds,ax
 xor si,si
 mov bx,24
.seed_row:
 mov cx,80
 rep movsw
 add di,104
 dec bx
 jnz .seed_row
 pop ds
'''
    text=text[:start]+stage+text[end:]
    if args.fields:
        seed=''' push ds
 pop es
 mov di,SCREEN_ATTRIBUTE_CELLS
 mov al,0x55
 mov cx,4096
 rep stosb
 mov di,SCREEN_ATTRIBUTE_CELLS
 xor ax,ax
 mov cx,3168
 rep stosb
 mov di,ERASE_ATTRIBUTE_VALUES
 mov al,0x66
 mov cx,4096
 rep stosb
 mov di,ERASE_ATTRIBUTE_VALUES
 mov al,7
 mov cx,3168
 rep stosb
 mov byte [SCREEN_ATTRIBUTE_CELLS+3*132+50],0x80
 mov byte [SCREEN_ATTRIBUTE_CELLS+10*132],0x81
 mov byte [ERASE_ATTRIBUTE_VALUES+3*132-1],0x1e
 mov word [SCREEN_CURSOR_WRAP],1
'''
        text=text.replace(' inc word [cs:staged]',seed+' inc word [cs:staged]')
        text=text.replace('sample_end:','plane_flags: times 4096 db 0\nplane_values: times 4096 db 0\nsample_end:')
    text=text.replace('cmp dx,0x184f','cmp dx,0x174f')
    text=text.replace('mov ax,[SCREEN_CURSOR_WRAP]','mov ax,[SCREEN_VIEWPORT_ACTIVE]')
    assert text.count(' inc word [cs:exits]')==1
    text=text.replace(' inc word [cs:exits]',' call snapshot\n inc word [cs:exits]')
    start=text.index(' mov si,SCREEN_ATTRIBUTE_CELLS\n mov di,flags',text.index('snapshot:'))
    end=text.index(' push ds\n mov ax,0xb800',start)
    text=text[:start]+''' mov bx,[ERASE_SHADOW_OFFSET]
 push ds
 mov ds,[ERASE_SHADOW_SEGMENT]
 mov si,bx
 mov di,flags
 mov cx,8192
 rep movsb
 pop ds
'''+text[end:]
    if args.fields:
        at=text.index(' push ds\n mov ax,0xb800',text.index('snapshot:'))
        text=text[:at]+''' mov si,SCREEN_ATTRIBUTE_CELLS
 mov di,plane_flags
 mov cx,4096
 rep movsb
 mov si,ERASE_ATTRIBUTE_VALUES
 mov di,plane_values
 mov cx,4096
 rep movsb
'''+text[at:]
    (out/'observer.asm').write_text(text)
    subprocess.run(['nasm','-fbin','-I',str(out)+'/',str(out/'observer.asm'),'-o',str(out/'VPWATCH.COM')],check=True)
    esc=b'\x1b';payload=esc+b'[2J'+esc+b'[HFIRST BYTE SAFE'+esc+b'[6n'+esc+b'[0c'+esc+b'[6;18H'
    expected=[0x0720]*(132*24)
    for col,char in enumerate(b'FIRST BYTE SAFE'):expected[col]=0x700|char
    if args.fields:
        payload+=esc+b'[3;6r'+esc+b'[4;18H'+esc+b'[M'+esc+b'[r'
        expected[3*132:6*132]=[0x1e20]*(3*132)
    text_row=7 if args.fields else 5
    edits=[(0,131,b'R'),(text_row,0,b'LEFT'),(23,80,b'HIDDEN'),(text_row,79,b'E'),(text_row,80,b'F')]
    for row,col,data in edits:
        payload+=esc+b'['+str(row+1).encode()+b';'+str(col+1).encode()+b'H'+data
        for i,char in enumerate(data):expected[row*132+col+i]=0x700|char
    payload+=esc+b'[24;1H'+esc+b'[2K'+esc+b'[24;132HZ'+esc+b'[6n'+esc+b'[1;16H'+esc+b'[6n'
    expected[23*132:24*132]=[0x0720]*132;expected[24*132-1]=0x75a
    inputs={str(path.relative_to(ROOT)):sha(path)for path in [binary,observer,Path(__file__),ROOT/'standalone/test_connection_dos.py',ROOT/'standalone/test_terminal.py']}
    (out/'expectations.json').write_text(json.dumps(dict(inputs=inputs,payload_hex=payload.hex(),
        expected_logical_sha256=hashlib.sha256(struct.pack('<3168H',*expected)).hexdigest(),
        fixture='One BIOS cursor boundary stages owned132x24 geometry/shadow; subsequent UART/parser/cursor/output/erase uses the unchanged application. No width escape request is enabled.'),indent=2)+'\n')
    source=Path(harness.__file__).read_text();old="out=ROOT/'build/connection-dos'/name";assert source.count(old)==1
    scope=dict(harness.__dict__);scope['LABEL_ROOT']=out
    exec(compile(source.replace(old,'out=LABEL_ROOT/name'),str(Path(harness.__file__)),'exec'),scope)
    result=scope['run']('product','success','p6000 a-x',arguments='@D:\\TEST.PRM /D:CaseTest:23 /A:NETWORK',
        banner=payload,files={'VPWATCH.COM':(out/'VPWATCH.COM').read_bytes()},observer='VPWATCH',cpu='8086')
    raw=(out/'product/LINEATTR.BIN').read_bytes();assert len(raw)==(20408 if args.fields else 12216)
    state=struct.unpack_from('<12H',raw);shadow=bytearray(raw[24:8216]);video=raw[8216:12216]
    # Final cursor has returned to the left pane. Overlay its real video;
    # the shadow's visible portion may be stale until the next pan saves it.
    for row in range(24):shadow[row*264:row*264+160]=video[row*160:row*160+160]
    wire=(out/'product/serial.bin').read_bytes()
    checks=dict(canonical_DOS_harness=result['passed'],fixture_and_exit=state[:4]==(0x4c41,1,1,0),
        DS_equals_SS=state[4]==state[5],final_owned_geometry=state[6:11]==(1,7,3168,0,15),
        pane_cursor_seen=state[11]>=1,logical_screen_exact=shadow[:6336]==struct.pack('<3168H',*expected),
        shadow_tail_guard=shadow[6336:]==b'\x5a\xa5'*928,
        wide_cursor_report=esc+b'[24;132R' in wire,returned_cursor_report=esc+b'[1;16R' in wire,
        inputs_unchanged=inputs=={name:sha(ROOT/name)for name in inputs})
    if args.fields:
        flags=bytearray(3168);flags[10*132]=0x81
        values=bytearray(b'\x07'*3168);values[3*132-1:6*132]=b'\x1e'*(3*132+1)
        checks.update(field_flags_and_guard=raw[12216:16312]==flags+b'\x55'*928,
            field_values_and_guard=raw[16312:]==values+b'\x66'*928,
            repaired_region_video=all(struct.unpack_from('<H',shadow,i*2)[0]==0x1e20 for i in range(3*132,6*132)))
    report=dict(passed=all(checks.values()),checks=checks,binary_sha256=sha(binary),inputs=inputs,
        state=list(state),observer_sha256=sha(out/'VPWATCH.COM'),capture_sha256=sha(out/'product/LINEATTR.BIN'),
        expected_logical_sha256=hashlib.sha256(struct.pack('<3168H',*expected)).hexdigest(),cpu='8086',fields=args.fields,
        scope='Actual unchanged DOS terminal, real UART/parser/output/erase and native BIOS viewport copies at132x24 over80 physical columns. Declared test-only geometry fixture, far-shadow tail guard, real132-column CPR, restored left pane and hardware restoration. No peer width mode, general field repair/UI/child/BBS or physical acceptance.')
    (out/'checks.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(passed=report['passed'],checks=checks),indent=2))
    return 0 if report['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
