#!/usr/bin/env python3
"""Check the maintained C literal codec on the host and under8086 DOS."""
import ctypes as C
import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import subprocess

from build_aspect_literal import ROOT, OUT, VECTORS


class Result(C.Structure):
    _fields_ = [('text_length', C.c_uint), ('wire_length', C.c_uint), ('stride', C.c_uint)]


def library():
    lib = C.CDLL(str(OUT / 'literal.so'))
    lib.aspect_literal_encode.argtypes = [C.c_void_p,C.c_uint,C.c_uint32,C.c_uint32,C.c_void_p,C.c_uint,C.c_void_p]
    lib.aspect_literal_decode.argtypes = [C.c_void_p,C.c_uint,C.c_uint32,C.c_void_p,C.c_uint,C.c_void_p]
    return lib


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    compiler = Path(shutil.which('gcc')).resolve()
    assert str(compiler).startswith('/nix/store/'), 'Use the pinned Nix shell'
    subprocess.run(['gcc','-std=c89','-Wall','-Wextra','-Werror','-shared','-fPIC',
        str(ROOT / 'src/aspect/literal.c'),'-o',str(OUT / 'literal.so')], check=True)
    lib = library()
    vectors = json.loads(VECTORS.read_text())['vectors']
    checks = 0

    def pair(text, position, line, expected=None):
        nonlocal checks
        raw = C.create_string_buffer(text)
        wire = C.create_string_buffer(b'\xcc'*100,100)
        result = Result()
        assert lib.aspect_literal_encode(raw,len(text),position,line,wire,100,C.byref(result)) == 0
        actual = bytes(wire)[:len(text)+2]
        if expected is not None:
            assert actual == expected, (text,position,line,actual,expected)
        assert result.text_length == len(text) and result.wire_length == len(text)+2
        assert bytes(wire)[len(text)+2:] == b'\xcc'*(98-len(text))
        output = C.create_string_buffer(b'\xdd'*100,100)
        # Extra stream bytes are not consumed or decoded as part of the literal.
        wire[len(text)+2:len(text)+5] = b'XYZ'
        assert lib.aspect_literal_decode(wire,len(text)+5,position,output,100,C.byref(result)) == 0
        assert bytes(output) == text+b'\xdd'*(100-len(text))
        assert result.stride == ((position+line)&0xffffffff)%12+1
        checks += 1
        return actual

    for v in vectors:
        pair(bytes.fromhex(v['text_hex']),v['payload_offset'],v['source_line'],bytes.fromhex(v['wire_hex']))
    rng = random.Random(101)
    for _ in range(1200):
        text = bytes(rng.randrange(1,256) for _ in range(rng.randrange(1,81)))
        pair(text,rng.randrange(1<<32),rng.randrange(1<<32))
    original = bytes.fromhex(vectors[0]['wire_hex'])
    n = len(original)-2

    def bad_decode(raw,available,position,capacity,expected):
        nonlocal checks
        src = C.create_string_buffer(bytes(raw))
        output = C.create_string_buffer(b'\x77'*100,100)
        result = Result();C.memset(C.byref(result),0x88,C.sizeof(result))
        prior = bytes(result)
        status = lib.aspect_literal_decode(src,available,position,output,capacity,C.byref(result))
        assert status == expected,(raw,status,expected)
        assert bytes(output) == b'\x77'*100 and bytes(result) == prior
        checks += 1

    for v in vectors:
        wire = bytes.fromhex(v['wire_hex']);length=len(wire)-2;position=v['payload_offset']
        for available in range(len(wire)):
            bad_decode(wire,available,position,100,3)
        bad_decode(wire,len(wire),position,length-1,3)
        changed=bytearray(wire);changed[1]^=128
        bad_decode(changed,len(changed),position,100,4)
        changed=bytearray(wire);changed[1]=(changed[1]&128)|length
        bad_decode(changed,len(changed),position,100,4)
        changed=bytearray(wire);changed[0]=0xb3
        bad_decode(changed,len(changed),position,100,4)
        # Zero plaintext is outside this compiler's strlen-based payload.
        changed=bytearray(wire);changed[2]=(changed[2]-bytes.fromhex(v['text_hex'])[0])&255
        bad_decode(changed,len(changed),position,100,4)
    result=Result();output=C.create_string_buffer(100);raw=C.create_string_buffer(b'ABC')
    for length,status in [(0,2),(81,2)]:
        assert lib.aspect_literal_encode(raw,length,4,2,output,100,C.byref(result))==status;checks+=1
    assert lib.aspect_literal_encode(raw,3,4,2,raw,100,C.byref(result))==1;checks+=1
    assert lib.aspect_literal_encode(raw,3,4,2,output,100,raw)==1;checks+=1
    assert lib.aspect_literal_encode(raw,3,4,2,output,100,output)==1;checks+=1
    assert lib.aspect_literal_encode(None,1,4,2,output,100,C.byref(result))==1;checks+=1
    assert lib.aspect_literal_decode(None,3,4,output,100,C.byref(result))==1;checks+=1
    assert lib.aspect_literal_encode(raw,3,4,2,output,4,C.byref(result))==3;checks+=1
    zero=C.create_string_buffer(b'A\0B')
    assert lib.aspect_literal_encode(zero,3,4,2,output,100,C.byref(result))==4;checks+=1

    subprocess.run(['python3',str(ROOT / 'standalone/build_aspect_literal.py')],check=True)
    for name in ['DONE.TXT','PASS.TXT','FAIL.TXT']:
        (OUT / name).unlink(missing_ok=True)
    config=f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
cycles=max
[mixer]
nosound=true
[autoexec]
@echo off
mount c "{OUT}"
c:
LITERAL >RESULT.TXT
if errorlevel 1 goto failed
echo PASS>PASS.TXT
goto done
:failed
echo FAIL>FAIL.TXT
:done
exit
'''
    (OUT / 'dosbox.conf').write_text(config)
    with (OUT / 'dosbox.log').open('w') as log:
        subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(OUT / 'dosbox.conf')],
            env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),
            stdout=log,stderr=log,check=True,timeout=30)
    summary=(OUT / 'DONE.TXT').read_text().strip()
    assert (OUT / 'PASS.TXT').exists() and not (OUT / 'FAIL.TXT').exists(),(OUT / 'RESULT.TXT').read_text()
    assert summary.endswith('0 failures'),summary
    sources=[ROOT / 'src/aspect/literal.c',ROOT / 'src/aspect/literal.h',VECTORS,
             ROOT / 'standalone/build_aspect_literal.py',Path(__file__).resolve()]
    report=dict(passed=True,native_compiler_vectors=len(vectors),host_checks=checks,DOS_summary=summary,
        binary_sha256=hashlib.sha256((OUT/'LITERAL.EXE').read_bytes()).hexdigest(),
        sources={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        original_inputs=[],scope='Maintained nonempty literal payload codec only; frozen native compiler vectors plus negative/roundtrip tests and real8086 DOS. No VM or compiler completeness claim.')
    (OUT / 'checks.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
