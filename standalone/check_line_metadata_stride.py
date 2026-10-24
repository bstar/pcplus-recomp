#!/usr/bin/env python3
"""Exercise the application's actual logical-plane kernel at 80/132 columns."""
import hashlib
import itertools
import json
from pathlib import Path
import random
import re
import struct

from unicorn import UC_HOOK_CODE, UC_HOOK_INTR, UC_HOOK_INSN
from unicorn.x86_const import *
from dos_image import DosImage

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/terminal'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def reference(data,width,row,bottom,insert,fill):
    """Construct new rows from an immutable source, without overlap copying."""
    result=bytearray(data)
    for target in range(row,bottom+1):
        source=target-1 if insert else target+1
        result[target*width:(target+1)*width]=(data[source*width:(source+1)*width]
            if row<=source<=bottom else bytes([fill])*width)
    return bytes(result)


def main():
    manifest=json.loads((OUT/'manifest.json').read_text())
    assert sha(OUT/'TERMINAL.EXE')==manifest['binary_sha256']
    for name,digest in manifest['sources'].items():assert sha(ROOT/name)==digest,name
    listing=(OUT/'terminal.map').read_text()
    segment,offset=re.search(r'^([0-9a-f]+):([0-9a-f]+)[*+ ]+\s+terminal_line_metadata_move\s*$',listing,re.M|re.I).groups()
    assert int(offset,16)<0xfffe
    randomizer=random.Random(0x13280)
    cases=0;counts={80:0,132:0}
    regions=[(1,0,0),(5,0,4),(5,2,4),(24,0,23),(24,7,13),(25,0,24),(25,24,24),(25,2,23)]
    for width,(height,top,bottom),insert,fill,backward in itertools.product((80,132),regions,(False,True),(0,7,255),(False,True)):
        for row in sorted({top,(top+bottom)//2,bottom}):
            m=DosImage(OUT/'TERMINAL.EXE',OUT/'terminal.map');u=m.uc
            code_segment=m.base_segment+int(segment,16);stop=code_segment*16+0xfffe
            stopped=[]
            def finish(uc,address,size,_):
                if address==stop and uc.reg_read(UC_X86_REG_CS)==code_segment:
                    stopped.append(True);uc.emu_stop()
            def interrupt(*args):raise AssertionError('Plane kernel entered BIOS/DOS')
            def port(*args):raise AssertionError('Plane kernel accessed hardware')
            u.hook_add(UC_HOOK_CODE,finish);u.hook_add(UC_HOOK_INTR,interrupt)
            u.hook_add(UC_HOOK_INSN,port,None,1,0,UC_X86_INS_IN)
            u.hook_add(UC_HOOK_INSN,port,None,1,0,UC_X86_INS_OUT)
            flags=randomizer.randbytes(4096);values=randomizer.randbytes(4096)
            # Distinct, nonempty receive and deferred-owner bytes must survive.
            u.mem_write(m.symbols['uart_rx_buffer'],randomizer.randbytes(4096))
            m.put('uart_rx_count',3071);m.put('terminal_deferred_count',3)
            for name,value in dict(screen_columns=80,screen_attribute_row_bytes=width,
                screen_cursor_row=row,screen_cursor_column=0,screen_attribute_offset=row*width,
                screen_first_row=top,screen_last_row=bottom,csi_last_row=height-1,
                erase_cell_count=width*height).items():m.put(name,value)
            for name,data in [('screen_attribute_cells',flags),('erase_attribute_values',values)]:
                u.mem_write(m.symbols[name],data)
            video=randomizer.randbytes(4000);u.mem_write(0xb8000,video)
            shadow=m.get('erase_shadow_segment')*16+m.get('erase_shadow_offset')
            shadow_bytes=randomizer.randbytes(8192);u.mem_write(shadow,shadow_bytes)
            stack_bottom=m.offset('terminal_stack_top')-m.stack_bytes
            before=bytes(u.mem_read(m.data_base,stack_bottom));expected=bytearray(before)
            for name,data,blank in [('screen_attribute_cells',flags,0),('erase_attribute_values',values,fill)]:
                at=m.offset(name);assert 0<=at and at+4096<=stack_bottom
                expected[at:at+4096]=reference(data,width,row,bottom,insert,blank)
            sp=m.offset('terminal_stack_top')-2
            registers={UC_X86_REG_CS:code_segment,UC_X86_REG_DS:m.ds,UC_X86_REG_SS:m.ds,
                UC_X86_REG_SP:sp,UC_X86_REG_BP:0xbabe,UC_X86_REG_BX:0x9876,
                UC_X86_REG_SI:0x1234,UC_X86_REG_DI:0x5678,UC_X86_REG_ES:0xb800,
                UC_X86_REG_AX:0 if insert else 1,UC_X86_REG_DX:0xab00|fill,
                UC_X86_REG_EFLAGS:0x602 if backward else 0x202}
            for register,value in registers.items():u.reg_write(register,value)
            u.mem_write(m.data_base+sp,struct.pack('<H',0xfffe))
            u.emu_start(m.symbols['terminal_line_metadata_move'],0,count=100000)
            identity=(width,height,top,bottom,row,insert,fill,backward)
            assert stopped and u.reg_read(UC_X86_REG_SP)==sp+2,identity
            assert bytes(u.mem_read(m.data_base,stack_bottom))==expected,(identity,'near state')
            assert bytes(u.mem_read(0xb8000,4000))==video,(identity,'video')
            assert bytes(u.mem_read(shadow,8192))==shadow_bytes,(identity,'shadow')
            for register in (UC_X86_REG_BP,UC_X86_REG_BX,UC_X86_REG_SI,UC_X86_REG_DI,UC_X86_REG_ES,UC_X86_REG_DS,UC_X86_REG_SS):
                assert u.reg_read(register)==registers[register],(identity,register)
            assert not u.reg_read(UC_X86_REG_EFLAGS)&0x400,identity
            cases+=1;counts[width]+=1
    report=dict(passed=True,binary_sha256=manifest['binary_sha256'],cases=cases,width_cases=counts,
        checker_sha256=sha(Path(__file__)),sources=manifest['sources'],original_inputs=[],
        scope='Actual linked application logical-plane kernel, immutable-row oracle at80/132 columns. Full near data/BSS excluding stack, both4096-byte planes, video/shadow canaries, nonempty RX/deferred state and register/DF checks. No service substitution or original inputs. Trusted bounded caller fixtures; this does not admit live132 geometry or exercise132 video, native field repaint, parser/UI/child/BBS workflows.')
    (OUT/'line-metadata-stride-checks.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS logical line metadata:',cases,'cases',counts)


if __name__=='__main__':main()
