#!/usr/bin/env python3
"""Independent Python wire oracle against host C and source-built 8086 DOS C.
No terminal, file ownership, original executable or BBS interoperability claim.
"""
import binascii
import ctypes as C
import fcntl
import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import struct
import subprocess
import zlib

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/zmodem-wire'
SRC=ROOT/'src/transfer'

class Decoder(C.Structure):
    _fields_=[('buffer',C.c_void_p)]+[(n,C.c_uint) for n in
        ('capacity','count','phase','index','escape','cans','control','overflow','nibble','format','ending')]+[
        ('header',C.c_ubyte*5),('crc',C.c_uint32),('received',C.c_uint32)]

def checksum(data,fmt):
    return (zlib.crc32(data).to_bytes(4,'little') if fmt==67 else
            binascii.crc_hqx(data,0).to_bytes(2,'big'))

def quoted(data,control,previous=0):
    out=bytearray()
    for v in data:
        if v==255:out.extend(b'\x18m')
        elif v in (16,17,19,24,144,145,147,152) or (control and not v&96) or (v&127==13 and previous&127==64):
            out.extend((24,v^64))
        else:out.append(v)
        previous=v
    return bytes(out)

def header(data,fmt,control):
    crc=checksum(data,fmt)
    if fmt==66:return b'**\x18B'+(data+crc).hex().encode()+b'\r\n'+(b'' if data[0] in (3,8) else b'\x11')
    return b'*\x18'+bytes([fmt])+quoted(data+crc,control)

def packet(data,fmt,ending,control):
    # Initial CR is quoted conservatively: preceding header CRC may end in @.
    return (quoted(data,control,64)+bytes([24,ending])+
            quoted(checksum(data+bytes([ending]),fmt),control,ending)+
            (b'\x11' if ending==107 else b''))

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    lock=(OUT/'.lock').open('w')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    subprocess.run(['gcc','-std=c89','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-shared','-fPIC',str(SRC/'zmodem_wire.c'),'-o',str(OUT/'wire.so')],check=True)
    lib=C.CDLL(str(OUT/'wire.so'))
    lib.zw_init.argtypes=[C.c_void_p,C.c_void_p,C.c_uint,C.c_uint]
    lib.zw_feed.argtypes=[C.c_void_p,C.c_uint]
    lib.zw_data.argtypes=[C.c_void_p]
    lib.zw_headers.argtypes=[C.c_void_p]
    lib.zw_header_encode.argtypes=[C.c_uint,C.c_void_p,C.c_uint,C.c_void_p,C.c_uint]
    lib.zw_data_encode.argtypes=[C.c_uint,C.c_void_p,C.c_uint,C.c_uint,C.c_uint,C.c_void_p,C.c_uint]
    rng=random.Random(0x5a4d);records=[];streams=[];checks=0
    def decoder(fmt,control,kind,capacity=1024):
        s=Decoder();buf=C.create_string_buffer(b'\xa5'*(capacity+2),capacity+2)
        assert lib.zw_init(C.byref(s),C.byref(buf,1),capacity,control)==0
        s.format=fmt
        if kind:assert lib.zw_data(C.byref(s))==0
        return s,buf
    def feed(s,wire):return [(i,v) for i,b in enumerate(wire) if (v:=lib.zw_feed(C.byref(s),b))]
    def scenario(fmt,control,kind,wire,expected,capacity=1024):
        nonlocal checks
        s,buf=decoder(fmt,control,kind,capacity)
        assert [v for _,v in feed(s,wire)]==expected,(fmt,control,kind,wire,expected)
        assert buf.raw[0]==165 and buf.raw[capacity+1:]==b'\xa5'
        streams.append(struct.pack('<BBBHHH',fmt,control,kind,capacity,len(wire),len(expected))+wire+bytes(expected));checks+=1
    def case(kind,fmt,control,data,ending=107,retain=True):
        nonlocal checks
        wire=packet(data,fmt,ending,control) if kind else header(data,fmt,control)
        raw=C.create_string_buffer(data);out=C.create_string_buffer(b'\xa5'*2060,2060)
        def encode(cap):
            return (lib.zw_data_encode(fmt,raw,len(data),ending,control,out,cap) if kind else
                    lib.zw_header_encode(fmt,raw,control,out,cap))
        assert encode(2060)==len(wire) and out.raw[:len(wire)]==wire
        assert out.raw[len(wire)]==165;checks+=1
        for cap in (0,1,len(wire)-1):
            out.raw=b'\xa5'*2060;assert encode(cap)==0 and out.raw==b'\xa5'*2060;checks+=1
        s,buf=decoder(fmt,control,kind)
        events=feed(s,wire);assert len(events)==1 and events[0][1]==(2 if kind else 1),(kind,fmt,control,events)
        assert (s.count==len(data) and s.ending==ending and buf.raw[1:1+len(data)]==data) if kind else bytes(s.header)==data
        assert buf.raw[0]==165 and buf.raw[1025]==165;checks+=1
        # Every single-byte delivery already crosses all possible split points.
        if retain:records.append(struct.pack('<BBBBHH',kind,fmt,control,ending,len(data),len(wire))+data+wire)
        return wire
    for fmt in (65,66,67):
        for control in (0,1):
            for data in (bytes(5),bytes([1,0,0,0,35]),bytes([3,17,19,24,255]),bytes([8,255,127,144,152]),b'@\r\xc0\x8d\xff'):
                case(0,fmt,control,data)
            for n in (0,1,2,255,256,1023,1024):
                for end in range(104,108):case(1,fmt,control,bytes(i%256 for i in range(n)),end)
            for data in (b'\r',b'\x8d',b'\r@\r\xc0\x8d'):
                wire=case(1,fmt,control,data)
                assert wire.startswith(b'\x18');checks+=1
            for _ in range(50):
                data=rng.randbytes(rng.randrange(1025));case(1,fmt,control,data,rng.randrange(104,108))
                case(0,fmt,control,rng.randbytes(5))
    # Corruption must not release a CRC-valid payload or header.
    for fmt in (65,66,67):
        for kind in (0,1):
            data=b'HELLO' if not kind else bytes(range(256))
            wire=packet(data,fmt,107,0) if kind else header(data,fmt,0)
            start=0 if kind else (4 if fmt==66 else 3)
            for at in range(start,len(wire)-(1 if kind else (3 if fmt==66 else 0))):
                bad=bytearray(wire);bad[at]^=1
                s,buf=decoder(fmt,0,kind);events=feed(s,bad)
                assert all(event!=(2 if kind else 1) for _,event in events),(fmt,kind,at,events)
                checks+=1
    for fmt in (65,66,67):
        # Continue data frames, then return to header search after CRCE/CRCW.
        wire=b''.join(packet(b'PAYLOAD',fmt,e,0) for e in (105,106,104))+header(bytes([8,0,0,0,0]),66,0)
        scenario(fmt,0,1,wire,[2,2,2,1])
        for control in (0,1):
            scenario(fmt,control,1,packet(b'OVERFLOW',fmt,107,control),[5],capacity=3)
            # Flow controls may appear between escape and suffix, too.
            wire=packet(b'\x18\xff\x10\x11\x13@\r\xc0\x8d',fmt,107,control)
            injected=b''.join(bytes([b])+b'\x11\x93' for b in wire)
            scenario(fmt,control,1,injected,[2])
            # Five raw CAN cancel; quoted runs of CAN are ordinary payload.
            for prefix in (b'',b'*\x18A',b'abc\x18'):
                scenario(fmt,control,1,prefix+b'\x18'*5+b'ABC',[6]*(5 if prefix.endswith(b'\x18') else 4))
            case(1,fmt,control,b'\x18'*256,107)
            wire=packet(b'ABC',fmt,107,control)
            scenario(fmt,control,1,b'X'+wire[1:],[3])
            scenario(fmt,control,1,wire[:-4],[])
            scenario(fmt,control,1,b'\x18z',[4])
    for fmt in (65,67):
        for control in (0,1):
            for count in (1025,2048,4096,8192):
                body=bytes(i%256 for i in range(count))
                scenario(fmt,control,1,packet(body,fmt,107,control),[2],capacity=8192)
            scenario(fmt,control,1,packet(b'Z'*8193,fmt,107,control),[5],capacity=8192)
            scenario(fmt,control,1,packet(bytes(8192),fmt,107,control),[2],capacity=8192)
    # Historic hex headers use parity-marked LF (8a); uppercase hex accepted.
    for control in (0,1):
        wire=header(bytes([1,0,0,0,35]),66,control).upper().replace(b'\n',b'\x8a')
        scenario(66,control,0,wire,[1])
    # Rubout encodings and negotiated control filtering, with an independent CRC.
    for fmt in (65,67):
        data=b'\x7f\xff'
        wire=b'\x18l\x18m\x18k'+quoted(checksum(data+b'k',fmt),1)+b'\x11'
        s,buf=decoder(fmt,1,1)
        assert [v for _,v in feed(s,b'\x01'+wire)]==[2] and buf.raw[1:3]==data;checks+=1
        scenario(fmt,1,1,b'\x01'+wire,[2])
    # Invalid arguments must preserve supplied state/output.
    s,buf=decoder(65,0,1);before=bytes(s)
    assert lib.zw_feed(C.byref(s),256)==7 and bytes(s)==before;checks+=1
    assert lib.zw_init(C.byref(s),C.byref(s),1,0)==7 and bytes(s)==before;checks+=1
    out=C.create_string_buffer(b'Z'*2060,2060)
    assert lib.zw_data_encode(67,out,1024,107,0,out,2060)==0 and out.raw==b'Z'*2060;checks+=1
    (OUT/'VECTORS.BIN').write_bytes(b''.join(records))
    (OUT/'STREAMS.BIN').write_bytes(b''.join(streams))
    sources=[SRC/'zmodem_wire.c',SRC/'zmodem_wire.h',ROOT/'standalone/zmodem_wire_host.c',Path(__file__).resolve()]
    subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-s','-w4','-we','-k8192','-i='+str(SRC),'-fe=WIRE.EXE',str(sources[0]),str(sources[2])],cwd=OUT,check=True)
    isolated=OUT/'source-only';isolated.mkdir(exist_ok=True)
    for p in sources[:3]:shutil.copy2(p,isolated/p.name)
    subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-s','-w4','-we','-k8192','-i=.','-fe=WIRE.EXE','zmodem_wire.c','zmodem_wire_host.c'],cwd=isolated,check=True)
    assert (isolated/'WIRE.EXE').read_bytes()==(OUT/'WIRE.EXE').read_bytes()
    for name in ('PASS.TXT','FAIL.TXT','RESULT.TXT'):(OUT/name).unlink(missing_ok=True)
    conf=f'''[sdl]
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
WIRE >RESULT.TXT
if errorlevel 1 goto fail
echo PASS>PASS.TXT
goto done
:fail
echo FAIL>FAIL.TXT
:done
exit
'''
    (OUT/'dosbox.conf').write_text(conf)
    with (OUT/'dosbox.log').open('w') as log:
        subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(OUT/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=60)
    text=(OUT/'RESULT.TXT').read_text();assert (OUT/'PASS.TXT').exists() and not (OUT/'FAIL.TXT').exists(),text
    result=dict(passed=True,host_checks=checks,DOS_vectors=len(records),DOS_streams=len(streams),DOS_summary=text.strip(),
        isolated_source_build_byte_identical=True,
        tools={name:shutil.which(name) for name in ('gcc','wcl','dosbox-x')},
        vectors_sha256=hashlib.sha256((OUT/'VECTORS.BIN').read_bytes()).hexdigest(),
        streams_sha256=hashlib.sha256((OUT/'STREAMS.BIN').read_bytes()).hexdigest(),
        binary_sha256=hashlib.sha256((OUT/'WIRE.EXE').read_bytes()).hexdigest(),
        sources={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        scope='Maintained wire codec only: independent Python oracle, host C, source-built 8086 DOS vectors and near-span guards. No sender/receiver, UART, file owner, modern peer or throughput validation.')
    (OUT/'checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':main()
