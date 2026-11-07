#!/usr/bin/env python3
"""Execute the linked Alt-F8 admission branches with modeled service returns."""
import argparse
import json
from pathlib import Path
import re
import struct
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_CS,UC_X86_REG_IP,UC_X86_REG_DS,UC_X86_REG_SS,UC_X86_REG_SP,UC_X86_REG_AX
from build_path_session import ROOT,sha


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--terminal',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args();binary=args.terminal.resolve();out=args.output.resolve()
    assert binary.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build') and not out.exists()
    manifest=json.loads(binary.with_name('manifest.json').read_text())
    assert manifest['experimental_keymap_editor'] and sha(binary)==manifest['binary_sha256']
    for name,digest in manifest['sources'].items():assert sha(ROOT/name)==digest,name
    symbols={name:(int(seg,16),int(off,16)) for seg,off,name in re.findall(r'^\s*([0-9a-f]{4}):([0-9a-f]{4,8})[*+]?\s+(\w+)\s*$',binary.with_name('terminal.map').read_text(),re.M|re.I)}
    data=binary.read_bytes();header=struct.unpack_from('<H',data,8)[0]*16;image=bytearray(data[header:]);load=0x1000
    count,table=struct.unpack_from('<H',data,6)[0],struct.unpack_from('<H',data,0x18)[0]
    for index in range(count):
        off,seg=struct.unpack_from('<HH',data,table+4*index);at=16*seg+off
        struct.pack_into('<H',image,at,(struct.unpack_from('<H',image,at)[0]+load)&65535)
    near=load+manifest['memory_layout']['near_relative_segment']
    address=lambda name:(load+symbols[name][0])*16+symbols[name][1]
    flags=['terminal_parser_active','terminal_macro_active','terminal_transfer_pending','terminal_transfer_active',
           'terminal_monitor_active','terminal_controller_active','terminal_snapshot_active','terminal_ansi_wait_active','_redisplay_active']
    cases=[('ready',None,0,0),('common-owner-busy',None,0,1)]
    cases += [(name+'-'+str(value),name,value,0) for name in flags+['recording'] for value in (1,0x8000,0xffff)]
    rows=[]
    for label,active,value,busy in cases:
        cpu=Uc(UC_ARCH_X86,UC_MODE_16);cpu.mem_map(0,0x100000);cpu.mem_write(load*16,bytes(image))
        for name in flags:
            assert symbols[name][0]==manifest['memory_layout']['near_relative_segment']
            cpu.mem_write(address(name),struct.pack('<H',value if active==name else 0))
        cpu.mem_write(address('terminal_program_kind'),struct.pack('<H',0x1234))
        start=symbols['terminal_keymap_edit_start'];sp=0xfe00
        for register,initial in ((UC_X86_REG_CS,load+start[0]),(UC_X86_REG_IP,start[1]),(UC_X86_REG_DS,near),(UC_X86_REG_SS,near),(UC_X86_REG_SP,sp)):
            cpu.reg_write(register,initial)
        cpu.mem_write(near*16+sp,struct.pack('<HH',0x100,0xf000))
        calls=[];returned=[]
        def return_to_caller(far):
            stack=cpu.reg_read(UC_X86_REG_SS)*16+cpu.reg_read(UC_X86_REG_SP)
            ip=struct.unpack('<H',bytes(cpu.mem_read(stack,2)))[0]
            if far:cpu.reg_write(UC_X86_REG_CS,struct.unpack('<H',bytes(cpu.mem_read(stack+2,2)))[0])
            cpu.reg_write(UC_X86_REG_SP,cpu.reg_read(UC_X86_REG_SP)+(4 if far else 2));cpu.reg_write(UC_X86_REG_IP,ip)
        def observe(machine,at,size,unused):
            if at==0xf0100:returned.append(True);machine.emu_stop()
            elif at==address('terminal_recording_owned_far'):
                machine.reg_write(UC_X86_REG_AX,value if active=='recording' else 0);return_to_caller(True)
            elif at==address('terminal_program_start'):
                calls.append(True);machine.reg_write(UC_X86_REG_AX,busy);return_to_caller(False)
        cpu.hook_add(UC_HOOK_CODE,observe);cpu.emu_start(address('terminal_keymap_edit_start'),0,count=10000)
        kind=struct.unpack('<H',bytes(cpu.mem_read(address('terminal_program_kind'),2)))[0]
        expected_queue=active is None
        assert returned and bool(calls)==expected_queue and len(calls)<=1,label
        assert kind==(13 if expected_queue and not busy else 0x1234),label
        assert cpu.reg_read(UC_X86_REG_DS)==cpu.reg_read(UC_X86_REG_SS)==near and cpu.reg_read(UC_X86_REG_SP)==sp+4,label
        rows.append(dict(case=label,queue_called=bool(calls),kind=kind,passed=True))
    out.mkdir(parents=True)
    names=['standalone/check_keymap_admission.py','src/terminal/keymap_editor.asm','standalone/build_path_session.py']
    result=dict(passed=True,parent_sha256=sha(binary),cases=rows,sources={name:sha(ROOT/name) for name in names},
                scope='Actual relocated linked Alt-F8 start/queue instructions under16-bit CPU emulation. Recording query and common PROGRAM admission are modeled services; no DOS/device execution or proof of reaching these owner states through real UI. Every nonzero gate refuses without changing kind; common busy return and DS=SS/stack return checked.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS linked Alt-F8 admission:',len(rows),'CPU cases')


if __name__=='__main__':main()
