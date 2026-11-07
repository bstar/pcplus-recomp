#!/usr/bin/env python3
"""Source-only notation checks; optional SHA-pinned original CPU comparison.

Original routines and their real memcpy execute as isolated 16-bit CPU code.
No original DOS entry point, private KBD, BIOS, UART or filesystem is executed.
"""
import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import random
import struct
import subprocess
from unicorn import Uc, UC_ARCH_X86, UC_MODE_16, UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_CS, UC_X86_REG_DS, UC_X86_REG_SS, UC_X86_REG_SP, UC_X86_REG_IP

ROOT=Path(__file__).resolve().parents[1]
ORIGINAL_SHA='f079418fca6392cde318e2eb657874a1f5ee10db83616c83054d191441fb6244'
SOURCES=['src/key_mapping/keymap_text.c','src/key_mapping/keymap_text.h','standalone/test_keymap_text.py']

def spelling(raw):
    out=bytearray()
    for c in raw:
        if c in (30,127,255):out.extend(bytes([174,{30:94,127:68,255:48}[c],175]))
        elif c<32:out.extend(bytes([94,c+64]))
        elif c==94:out.extend(b'^^')
        else:out.append(c)
    return bytes(out)

def original(module, entry, value):
    u=Uc(UC_ARCH_X86,UC_MODE_16)
    u.mem_map(0,0x100000)
    u.mem_write(0x10000,module)
    data=0x13f10
    for reg,v in ((UC_X86_REG_CS,0x1000),(UC_X86_REG_DS,0x13f1),(UC_X86_REG_SS,0x13f1),(UC_X86_REG_SP,0xf000)):
        u.reg_write(reg,v)
    u.mem_write(data+0xa000,value+b'\0')
    u.mem_write(data+0xb000,b'\xa5'*96)
    u.mem_write(data+0xf000,struct.pack('<HHH',0xf000,0xa000,0xb000))
    def stop(cpu,address,size,_):
        if address==0x1f000:cpu.emu_stop()
    u.hook_add(UC_HOOK_CODE,stop)
    u.emu_start(0x10000+entry,0x20000,count=20000)
    assert u.reg_read(UC_X86_REG_IP)==0xf000 and u.reg_read(UC_X86_REG_SP)==0xf002
    result=bytes(u.mem_read(data+0xb000,96))
    assert b'\0' in result
    n=result.index(0)
    assert result[n+1:]==b'\xa5'*(95-n)
    return result[:n]

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--original',type=Path)
    a=p.parse_args();out=a.output.resolve()
    assert out.is_relative_to(ROOT/'build') and not out.exists()
    out.mkdir(parents=True)
    module=None
    if a.original:
        image=a.original.read_bytes()
        assert hashlib.sha256(image).hexdigest()==ORIGINAL_SHA
        assert struct.unpack_from('<H',image,8)[0]*16==512
        module=image[512:]
    subprocess.run(['cc','-shared','-fPIC','-std=c89','-pedantic','-Wall','-Wextra','-Werror','-o',str(out/'text.so'),str(ROOT/SOURCES[0])],check=True)
    lib=ctypes.CDLL(str(out/'text.so'))
    for name in ('encode','decode'):
        fn=getattr(lib,'keymap_text_'+name)
        fn.argtypes=[ctypes.c_void_p,ctypes.c_uint,ctypes.c_void_p,ctypes.c_uint];fn.restype=ctypes.c_int
    def run(name,raw,capacity):
        target=ctypes.create_string_buffer(b'\xa5'*40,40)
        n=getattr(lib,'keymap_text_'+name)(raw,len(raw),target,capacity)
        if n<0:assert target.raw==b'\xa5'*40
        else:assert target.raw[n:n+1]==b'\0' and target.raw[n+1:]==b'\xa5'*(39-n)
        return n,target.raw[:n] if n>=0 else None
    rng=random.Random(201)
    alphabet=bytes(c for c in range(1,256) if c!=174)
    vectors=[b'']+[bytes([c]) for c in alphabet]+[b'\x1e'*11,b'^'*11,b'A'*11]
    vectors += [bytes(rng.choice(alphabet) for _ in range(rng.randrange(12))) for _ in range(128)]
    proof_cases=[]
    for raw in vectors:
        text=spelling(raw)
        assert run('encode',raw,len(text)+1)==(len(text),text)
        assert run('decode',text,len(raw)+1)==(len(raw),raw)
        assert run('encode',raw,len(text))[0]==-1
        assert run('decode',text,len(raw))[0]==-1
        if module is not None:
            assert original(module,0xdc4,raw)==text
            assert original(module,0xd4c,text)==raw
        proof_cases.append((raw,text))
    for c in range(97,123):
        text=bytes([94,c]);expected=bytes([c-96])
        assert run('decode',text,12)==(1,expected)
        if module is not None:assert original(module,0xd4c,text)==expected
    malformed=[b'^',b'^@',b'^ ',b'^`',b'\xae',b'\xaeD',b'\xaeDx',b'\xaeX\xaf',b'A'*12,b'A'*34,b'\0',b'\x7f',b'\xff']
    for text in malformed:assert run('decode',text,40)[0]==-1
    for raw in (b'A'*12,b'\0',b'\xae',b'\xaeD\xaf'):assert run('encode',raw,40)[0]==-1
    if module is not None:
        assert original(module,0xdc4,b'\xaeD\xaf')==b'\xaeD\xaf'
        assert original(module,0xd4c,b'\xaeD\xaf')==b'\x7f'
    def arr(v):return '{'+','.join(str(c) for c in v+b'\0')+'}'
    driver=['#include <stdio.h>','#include <string.h>','#include "keymap_text.h"','int main(void){unsigned char out[40]; unsigned i; int n;']
    for raw,text in proof_cases:
        driver.append('{static const unsigned char raw[]='+arr(raw)+';static const unsigned char text[]='+arr(text)+';')
        for action,source,expected in [('encode','raw','text'),('decode','text','raw')]:
            driver.append('memset(out,0xa5,sizeof(out));n=keymap_text_'+action+'('+source+',sizeof('+source+')-1,out,sizeof(out));if(n!=sizeof('+expected+')-1 || memcmp(out,'+expected+',sizeof('+expected+')))return 1;for(i=n+1;i<sizeof(out);++i)if(out[i]!=0xa5)return 2;')
        driver.append('}')
    for text in malformed:
        driver.append('{static const unsigned char bad[]='+arr(text)+';memset(out,0xa5,sizeof(out));if(keymap_text_decode(bad,sizeof(bad)-1,out,sizeof(out))!=-1)return 5;for(i=0;i<40;++i)if(out[i]!=0xa5)return 6;}')
    driver.extend(['memset(out,0xa5,sizeof(out));if(keymap_text_decode((const unsigned char *)"^@",2,out,40)!=-1)return 3;for(i=0;i<40;++i)if(out[i]!=0xa5)return 4;', 'puts("PASS KEYMAP NOTATION '+str(len(proof_cases)*2)+' DOS CASES");return 0;}'])
    (out/'driver.c').write_text('\n'.join(driver)+'\n')
    subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k4096','-i='+str(ROOT/'src/key_mapping'),'-fe=KMTEXT.EXE',str(out/'driver.c'),str(ROOT/SOURCES[0])],cwd=out,check=True)
    (out/'dosbox.conf').write_text('[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=fixed 6000\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "'+str(out)+'"\nc:\nKMTEXT >RESULT.TXT\nexit\n')
    with (out/'dosbox.log').open('w') as log:
        result=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=20)
    assert result.returncode==0 and ('PASS KEYMAP NOTATION '+str(len(proof_cases)*2)+' DOS CASES').encode() in (out/'RESULT.TXT').read_bytes()
    receipt={'passed':True,'source_only_build':True,'original_cpu_comparison':module is not None,'original_sha256':ORIGINAL_SHA if module else None,'original_cpu_cases':len(vectors)*2+28 if module else 0,'dos_cases':len(proof_cases)*2,'host_roundtrip_vectors':len(vectors),'host_transactional_boundary_checks':len(vectors)*2+len(malformed)+4,'literal_AE_collision_confirmed':module is not None,'sources':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in SOURCES},'dos_binary_sha256':hashlib.sha256((out/'KMTEXT.EXE').read_bytes()).hexdigest(),'limits':['No editor GUI, file IO, factory defaults or terminal integration tested.','Strict malformed/capacity/literal-AE refusal intentionally differs from unbounded original.','Original CPU checks run conversion routines, including their real memcpy, without original startup.']}
    (out/'result.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
