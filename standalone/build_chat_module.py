#!/usr/bin/env python3
"""Build a CRT-free MZ Chat overlay from declared source, never originals."""
import argparse
import hashlib
import json
import re
import struct
import subprocess
import zlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCES=['src/chat/module_entry.asm','src/chat/module.c','src/chat/module.h',
         'src/chat/session.c','src/chat/session.h','src/chat/screen.c','src/chat/screen.h',
         'src/terminal/chat_owner.c','src/terminal/chat_owner.h','standalone/build_chat_module.py']


def build(out,presentation=False):
    out=out.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir()
    extra=['src/chat/presentation.c','src/chat/presentation.h','src/chat/presentation_bios.asm'] if presentation else []
    subprocess.run(['nasm','-fobj',*(['-DCHAT_PRESENTATION'] if presentation else []),str(ROOT/'src/chat/module_entry.asm'),'-o','entry.obj'],cwd=out,check=True)
    objects=['entry.obj']
    for name in ['src/chat/module.c','src/chat/session.c','src/chat/screen.c','src/terminal/chat_owner.c']+(['src/chat/presentation.c'] if presentation else []):
        obj=Path(name).stem+'.obj';objects.append(obj)
        subprocess.run(['wcc','-q','-bt=dos','-0','-ms','-s','-w4','-we','-ecc','-dCHAT_BANK',*(['-dCHAT_PRESENTATION'] if presentation else []),'-nt=CHAT_CODE','-nc=FARCODE','-fo='+obj,str(ROOT/name)],cwd=out,check=True)
    if presentation:
        subprocess.run(['nasm','-fobj',str(ROOT/'src/chat/presentation_bios.asm'),'-o','bios.obj'],cwd=out,check=True)
        objects.append('bios.obj')
    (out/'link.lnk').write_text('system dos\noption quiet\noption nodefaultlibs\noption start=chat_overlay_entry\noption stack=0\noption map=PCCHAT.MAP\nname PCCHAT.OVL\n'+''.join('file '+obj+'\n' for obj in objects))
    subprocess.run(['wlink','@link.lnk'],cwd=out,check=True)
    raw=(out/'PCCHAT.OVL').read_bytes();header=struct.unpack_from('<14H',raw)
    magic,last,pages,relocs,paragraphs,minalloc,maxalloc,ss,sp,checksum,ip,cs,table,overlay=header
    assert magic==0x5a4d and overlay==0 and paragraphs*16<=len(raw)
    assert (pages-1)*512+(last or 512)==len(raw)
    image=raw[paragraphs*16:];assert 0<len(image)<8192 and cs==ip==ss==sp==minalloc==0
    api,state_bytes=(0x101,362) if presentation else (0x100,358)
    assert image[0]==0xea and image[5:19]==b'LOCCHAT\0'+struct.pack('<3H',api,50,state_bytes)
    relocations=[struct.unpack_from('<2H',raw,table+i*4) for i in range(relocs)]
    assert relocs and all(seg*16+off+2<=len(image) for off,seg in relocations)
    listing=(out/'PCCHAT.MAP').read_text()
    segments=re.findall(r'^(\w+)\s+\w+\s+\w+\s+([0-9a-f]{4}):([0-9a-f]{4})\s+([0-9a-f]+)\s*$',listing,re.M|re.I)
    assert segments and all(int(size,16)==0 for name,seg,off,size in segments if name!='CHAT_CODE')
    assert sum(int(size,16) for name,seg,off,size in segments)==len(image)
    offsets=sorted(seg*16+off for off,seg in relocations);assert len(set(offsets))==len(offsets) and all(a+2<=b for a,b in zip(offsets,offsets[1:]))
    crc=zlib.crc32(raw);constants={'file_bytes':len(raw),'image_bytes':len(image),'header_bytes':paragraphs*16,'relocations':relocs,'entry_offset':ip,'entry_segment':cs,'file_crc32':crc,'image_crc32':zlib.crc32(image)}
    (out/'expected.h').write_text('/* Generated from the exact reviewed module, not read at application startup. */\n'+''.join('#define CHAT_EXPECTED_'+k.upper()+' '+(hex(v)+'UL' if k.endswith('crc32') else str(v))+'\n' for k,v in constants.items())+'static const unsigned short __based(__segname("_CODE")) chat_expected_relocations[]={'+','.join(str(v) for v in offsets)+'};\n')
    result=dict(passed=True,binary_sha256=hashlib.sha256(raw).hexdigest(),**constants,minimum_extra_paragraphs=minalloc,own_stack_bytes=sp,DGROUP_bytes=0,
                presentation=presentation,api_version=api,state_bytes=state_bytes,
                sources={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in SOURCES+extra},
                scope='Source-only DOS MZ overlay with one code group, declared far dispatch ABI and self-relocations; no CRT, private data, stack, original artifact or prior object. Runtime loading and parent integration remain separate.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--presentation',action='store_true');args=p.parse_args()
    print(json.dumps(build(args.output,args.presentation),indent=2))
