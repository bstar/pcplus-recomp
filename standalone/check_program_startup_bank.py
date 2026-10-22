#!/usr/bin/env python3
"""Linked startup retention/ABI check before and after pure-code relocation."""
import argparse,json,shutil,struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
import check_transport as transport
from audit_aspect_transmit_wait import sha
ROOT=transport.ROOT


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--expect-banked',action='store_true');a=p.parse_args()
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True);rows=[];products={}
    for product in ('terminal','terminal-mouse'):
        transport.BINARY=ROOT/'build'/product/'TERMINAL.EXE';transport.MAP=transport.BINARY.parent/'terminal.map'
        manifest=json.loads((transport.BINARY.parent/'manifest.json').read_text());assert manifest['binary_sha256']==sha(transport.BINARY)
        products[product]=sha(transport.BINARY)
        for flags in (2,0x202,0x402,0x602):
            m=transport.Transport();u=m.uc;psp=m.base_segment-0x10;top=m.offset('terminal_stack_top');sp=top-2
            names=['terminal_stack_top','terminal_far_storage_end','redisplay_snapshot_end','redisplay_view_end','terminal_snapshot_image_end','browser_screen_end','ed_screen_end','program_screen_end']
            retained=(max(m.symbols[n] for n in names)+15)//16-psp
            kept=dict(BX=0xfff1,CX=0x2345,DX=0x3456,SI=0x4567,DI=0x5678,BP=0x6789,ES=0x9000,DS=m.ds,SS=m.ds)
            for name,value in dict(CS=m.base_segment,SP=sp,AX=psp,EFLAGS=flags,**kept).items():u.reg_write(globals()['UC_X86_REG_'+name],value)
            canary=bytes((i*19+7)&255 for i in range(128));u.mem_write(m.data_base+top-256,canary);u.mem_write(m.data_base+sp,struct.pack('<H',m.return_offset))
            seen=set();bad=[]
            def trace(uc,address,size,data):
                seen.add(uc.reg_read(UC_X86_REG_CS))
                if uc.reg_read(UC_X86_REG_EFLAGS)&0x200 and uc.reg_read(UC_X86_REG_DS)!=uc.reg_read(UC_X86_REG_SS):bad.append(address)
            hook=u.hook_add(UC_HOOK_CODE,trace);m.returned=False;u.emu_start(m.symbols['terminal_program_initialize'],0,count=10000);u.hook_del(hook)
            assert m.returned and not bad and u.reg_read(UC_X86_REG_SP)==top and u.reg_read(UC_X86_REG_AX)==psp
            assert u.reg_read(UC_X86_REG_EFLAGS)&0x600==flags&0x600
            for name,value in kept.items():assert u.reg_read(globals()['UC_X86_REG_'+name])==value,name
            assert bytes(u.mem_read(m.data_base+top-256,128))==canary
            assert m.get('process_psp')==psp and m.get('process_keep_paragraphs')==m.get('process_minimum_paragraphs')==retained
            assert not m.tx and not m.keyboard_calls
            assert (len(seen)>1)==a.expect_banked,(product,seen)
            if a.expect_banked:
                assert 'terminal_program_initialize_far' in m.symbols
                bank=next(s for s in manifest['memory_layout']['code_segments'] if s['name']=='CONFIG_CODE')
                bank_cs=m.base_segment+bank['relative_segment']
                assert seen=={m.base_segment,bank_cs}
            rows.append(dict(product=product,flags=flags,passed=True,retained_paragraphs=retained,executed_CS=sorted(seen)))
        for name,digest in manifest['sources'].items():
            assert sha(ROOT/name)==digest;target=out/'inputs'/name;target.parent.mkdir(parents=True,exist_ok=True)
            if target.exists():assert sha(target)==digest
            else:shutil.copy2(ROOT/name,target)
        shutil.copy2(transport.BINARY,out/(product+'.EXE'));shutil.copy2(transport.MAP,out/(product+'.map'))
    for path in (Path(__file__),ROOT/'standalone/check_transport.py',ROOT/'standalone/dos_image.py'):
        target=out/'inputs'/path.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,target)
    r=dict(passed=True,banked=a.expect_banked,cases=rows,products=products,checker_sha256=sha(Path(__file__)),
        scope=__doc__+' Eight normal/mouse linked cases execute actual instructions. Retained size is independently computed from static end symbols; AX/PSP, registers, stack canary, IF/DF and DS=SS checked. DOS/BIOS/hardware boundaries modeled; startup routine must not call them. Broader source/process/DOS/BBS and physical acceptance remain separate.')
    (out/'checks.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(passed=True,cases=len(rows),banked=a.expect_banked)))


if __name__=='__main__':main()
