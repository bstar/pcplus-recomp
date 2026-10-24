#!/usr/bin/env python3
"""Link recovered native reset with a separate DS=SS bank and real root UART."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import struct

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/reset-bank'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    native=[]
    for module in ['screen','erase','scroll','text','cursor_shape','terminal_services','terminal_reset','viewport']:
        native+=sorted((ROOT/'reconstruction'/module).glob('*.asm'))
    native += [ROOT/'reconstruction/attributes/reset.asm',ROOT/'reconstruction/ui_windows/cga_blank.asm',
        ROOT/'reconstruction/ui_windows/cga_unblank.asm',ROOT/'reconstruction/modes/width_request.asm',ROOT/'standalone/terminal_reset_host.asm']
    root=[ROOT/'reconstruction/uart/core.asm',ROOT/'src/uart/api.asm',ROOT/'standalone/data.asm',
        ROOT/'standalone/services.asm',ROOT/'src/ui/reset_bank_context.asm',ROOT/'standalone/reset_bank_body.asm',ROOT/'standalone/reset_bank_driver.asm']
    objects=[]
    for number,source in enumerate(native+root):
        obj=OUT/f'unit-{number}.obj';objects.append(obj)
        flags=[]
        if source in native:
            flags=['-D'+source.parent.name.upper()+'_OMF','-DRESET_VIEWPORT','-DRESET_BANK','-DVIEWPORT_PRESERVE_DS',
                '-DWIDTH_REQUEST_OMF','-D_TEXT=RESET_CODE','-DCODE=FARCODE','-D_DATA=RESET_DATA',
                '-DSTACK=RESET_STACK','-DDGROUP=RESET_GROUP','-Dstack_top=reset_stack_top']
        if source==ROOT/'reconstruction/uart/core.asm':flags=['-DUART_OMF']
        subprocess.run(['nasm','-fobj',*flags,'-I',str(ROOT/'reconstruction/uart')+'/',str(source.relative_to(ROOT)),'-o',str(obj)],cwd=ROOT,check=True)
    subprocess.run(['wlink','system','dos','option','quiet','option','map='+str(OUT/'bank.map'),'name',str(OUT/'BANK.EXE'),'file',','.join(map(str,objects))],check=True)
    listing=(OUT/'bank.map').read_text();groups={name:(int(seg,16),int(size,16))for name,seg,off,size in re.findall(r'^(DGROUP|RESET_GROUP)\s+([0-9a-f]+):([0-9a-f]+)\s+([0-9a-f]+)',listing,re.M|re.I)}
    assert set(groups)=={'DGROUP','RESET_GROUP'} and all(size<65536 for _,size in groups.values())
    a,n=groups['DGROUP'];b,m=groups['RESET_GROUP'];assert a*16+n<=b*16 or b*16+m<=a*16
    symbols={name:(int(seg,16),int(off,16))for seg,off,name in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',listing,re.M|re.I)}
    def bank_offset(name):
        seg,off=symbols[name];return seg*16+off-b*16
    image=bank_offset('reset_data_image');top=bank_offset('reset_stack_top')
    assert top-image==0xd600+4096 and top<=m
    header=struct.unpack_from('<14H',(OUT/'BANK.EXE').read_bytes())
    root_top=symbols['stack_top'][0]*16+symbols['stack_top'][1]
    assert header[7]*16+header[8]==root_top,'DOS loader stack must start in the owned root stack'
    sources=native+root+sorted((ROOT/'reconstruction/uart').glob('*.inc'))+[Path(__file__)]
    manifest=dict(kind='native-reset-private-context-real-uart-diagnostic',binary_sha256=sha(OUT/'BANK.EXE'),
        groups={name:dict(relative_segment=seg,bytes=size)for name,(seg,size)in groups.items()},
        context_layout=dict(image_offset=image,image_bytes=0xd600,stack_bottom_offset=top-4096,stack_top_offset=top,stack_bytes=4096,root_stack_top_offset=root_top-a*16),
        sources={str(path.relative_to(ROOT)):sha(path)for path in sources},original_inputs=[],
        scope='Actual native width/soft-reset in a distinct DS=SS data/stack bank while the source UART ISR owns root data. Static diagnostic shadow and selected native24-row hidden-status path; not live projection, normal application width ownership, dynamic allocation/rollback, arbitrary asynchronous recovery or physical acceptance.')
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Built private reset bank',manifest['binary_sha256'],manifest['groups'])


if __name__=='__main__':main()
