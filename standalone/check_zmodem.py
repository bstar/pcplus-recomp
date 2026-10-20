#!/usr/bin/env python3
"""Maintained session engine, independent scripted oracle and real lrzsz peer.
Host transport/file callbacks here are fixtures, not the terminal integration.
"""
import argparse
import ctypes as C
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import select
import shutil
import subprocess
from check_zmodem_wire import Decoder,header,packet

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/zmodem-session'
U=C.c_uint;P=C.c_void_p;D=C.c_uint32
READ=C.CFUNCTYPE(U,P,U);WRITE=C.CFUNCTYPE(U,P,P,U)
NEXT=C.CFUNCTYPE(U,P,P,P);SEEK=C.CFUNCTYPE(U,P,D)
FILE_READ=C.CFUNCTYPE(U,P,P,U,P);CLOSE=C.CFUNCTYPE(U,P,U)
OPEN=C.CFUNCTYPE(U,P,P);SIMPLE=C.CFUNCTYPE(U,P)
class Ops(C.Structure):
    _fields_=list(zip(('read_byte','write_wire','next','seek','read_file','close_source','open_received','write_received','commit_received','abort_received'),
        (READ,WRITE,NEXT,SEEK,FILE_READ,CLOSE,OPEN,WRITE,SIMPLE,SIMPLE)))
class PacketIO(C.Union):
    _fields_=[('rx',C.c_ubyte*8192),('wire',C.c_ubyte*8192)]
class Session(C.Structure):
    _fields_=[('ops',P),('context',P)]+[(n,U) for n in ('status','cleanup_status','sending','owned','format','control','block','retries','phase','skipped','window','capacity')]+[
        (n,D) for n in ('position','size','files','bytes')]+[('name',C.c_char*256),('decoder',Decoder),('data',C.c_ubyte*1024),('io',PacketIO)]

def h(t,pos=0,fmt=66):return header(bytes([t])+pos.to_bytes(4,'little'),fmt,0)
def meta(name,size):return name.encode()+b'\0'+str(size).encode()+b'\0'
def send_meta(name,size):return name.encode()+b'\0'+str(size).encode()+b' 0\0'
def offer(name,size,fmt=67):return h(4,0,fmt)+packet(meta(name,size),fmt,107,0)
def payload(data,offset=0,fmt=67,end=107):return h(10,offset,fmt)+packet(data,fmt,end,0)

class Fixture:
    def __init__(self,lib,rx=b'',sources=(),fault=None,peer=None,corrupt=False,corrupt_at=64,corrupt_packet=1):
        self.lib=lib;self.rx=list(rx);self.tx=bytearray();self.sources=list(sources);self.source=None;self.offset=0
        self.received={};self.stage=None;self.target=None;self.events=[];self.fault=fault;self.peer=peer;self.errors=[]
        self.corrupt=corrupt;self.corrupt_at=corrupt_at;self.corrupt_packet=corrupt_packet;self.out_packets=0;self.corruptions=0;self.peer_wire=bytearray();self.engine_wire=bytearray()
        def guarded(fn,typ):
            def call(*args):
                try:return fn(*args)
                except BaseException as exc:self.errors.append(repr(exc));return 65534
            return typ(call)
        self.ops=Ops(*[guarded(fn,typ) for fn,typ in zip((self.read,self.write,self.next,self.seek,self.file_read,self.close,self.open,self.append,self.commit,self.abort),
            (READ,WRITE,NEXT,SEEK,FILE_READ,CLOSE,OPEN,WRITE,SIMPLE,SIMPLE))])
    def read(self,_,seconds):
        if self.fault=='cancel':return 65533
        if self.peer:
            ready,_,_=select.select([self.peer.stdout],[],[],seconds)
            if not ready:return 65535
            b=os.read(self.peer.stdout.fileno(),1)
            if not b:return 65534
            value=b[0];self.peer_wire.append(value)
            if self.corrupt and not self.corruptions and self.session.phase==2 and self.session.decoder.phase==10 and self.session.decoder.count==self.corrupt_at and not self.session.decoder.escape and value==64:
                self.corruptions+=1;value=65
            self.engine_wire.append(value);return value
        return self.rx.pop(0) if self.rx else 65535
    def write(self,_,data,n):
        if self.fault=='transport':return 1
        data=C.string_at(data,n)
        if self.session.phase==3 and b'@A' in data and not data.startswith(b'*\x18'):
            self.out_packets+=1
            if self.corrupt and not self.corruptions and self.out_packets==self.corrupt_packet and b'@A' in data:
                at=data.index(b'@A');data=data[:at]+b'BA'+data[at+2:];self.corruptions+=1
        self.tx.extend(data)
        if self.peer:
            self.peer.stdin.write(data);self.peer.stdin.flush()
        return 0
    def next(self,_,name,size):
        if not self.sources:return 1
        self.target,self.source=self.sources.pop(0);self.offset=0
        C.memmove(name,self.target.encode()+b'\0',len(self.target)+1);C.cast(size,C.POINTER(D))[0]=len(self.source)
        self.events.append(('next',self.target));return 2 if self.fault=='next' else 0
    def seek(self,_,offset):
        self.events.append(('seek',offset))
        if self.fault=='seek' or offset>len(self.source):return 1
        self.offset=offset;return 0
    def file_read(self,_,data,n,got):
        self.events.append(('read',n))
        if self.fault=='read':return 1
        content=self.source[self.offset:self.offset+n];C.memmove(data,content,len(content));C.cast(got,C.POINTER(U))[0]=len(content);self.offset+=len(content);return 0
    def close(self,_,complete):
        self.events.append(('close',complete))
        if self.fault=='close':return 1
        self.source=None;return 0
    def open(self,_,metadata):
        name=C.string_at(metadata).decode();self.events.append(('open',name))
        if self.fault=='open':return 2
        if name in self.received:return 1 # ZM_DONE = skip existing
        self.target=name;self.stage=bytearray();return 0
    def append(self,_,data,n):
        self.events.append(('append',n))
        if self.fault=='write':return 1
        self.stage.extend(C.string_at(data,n));return 0
    def commit(self,_):
        self.events.append(('commit',self.target))
        if self.fault=='commit':return 1
        assert self.target not in self.received
        self.received[self.target]=bytes(self.stage);self.stage=None;return 0
    def abort(self,_):
        self.events.append(('abort',self.target))
        if self.fault=='cleanup':return 1
        self.stage=None;return 0
    def run(self,sending=False):
        self.session=Session();r=self.lib.zm_run(C.byref(self.session),C.byref(self.ops),None,sending)
        assert not self.errors,self.errors
        return r

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--sexyz',type=Path,help='Optional explicitly selected stock Synchronet protocol helper (stdio only).')
    args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    lock=(OUT/'.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    runroot=OUT/'runs'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    runroot.mkdir(parents=True)
    sources=[ROOT/'src/transfer'/n for n in ('zmodem.c','zmodem.h','zmodem_wire.c','zmodem_wire.h','zmodem_name.c','zmodem_name.h','batch_header.c','batch_header.h')]
    subprocess.run(['gcc','-std=c89','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-shared','-fPIC',*[str(p) for p in sources if p.suffix=='.c'],'-o',str(OUT/'session.so')],check=True)
    lib=C.CDLL(str(OUT/'session.so'));lib.zm_run.argtypes=[P,P,P,U];cases=[]
    def check(label,good):assert good,label;cases.append(label)
    content=bytes(range(256))*4+b'\0\x1a\xff@\r'
    for fmt in (65,67):
        for n in (0,1,1023,1024,1025,len(content)):
            body=content[:n];wire=offer('TEST.BIN',n,fmt)
            for off in range(0,n,1024):wire+=payload(body[off:off+1024],off,fmt)
            wire+=h(11,n,fmt)+h(8)+b'OO'
            f=Fixture(lib,wire);check(f'receive-{fmt}-{n}',f.run()==0 and f.received=={'TEST.BIN':body} and f.session.files==1 and f.session.bytes==n)
            expected=h(1,0x23002000)+h(9)
            for off in range(0,n,1024):expected+=h(3,min(off+1024,n))
            expected+=h(1,0x23002000)+h(8)
            check(f'receive-wire-{fmt}-{n}',bytes(f.tx)==expected)
            rx=h(1,0x22000000 if fmt==67 else 0x02000000)+h(9)
            for off in range(0,n,1024):rx+=h(3,min(off+1024,n))
            rx+=h(1,0x22000000 if fmt==67 else 0x02000000)+h(8)
            f=Fixture(lib,rx,[('TEST.BIN',body)]);check(f'send-{fmt}-{n}',f.run(True)==0 and f.session.files==1 and f.session.bytes==n and f.source is None)
            expected=h(0)+h(4,0x01000000,fmt)+packet(send_meta('TEST.BIN',n).ljust(128,b'\0'),fmt,107,0)
            for off in range(0,n,1024):expected+=payload(body[off:off+1024],off,fmt)
            expected+=h(11,n,fmt)+h(8)+b'OO'
            check(f'send-wire-{fmt}-{n}',bytes(f.tx)==expected)
    # CRC failure and duplicate offer resume verified committed bytes only.
    bad=bytearray(packet(b'BAD',67,107,0));bad[0]^=1
    rx=offer('TEST.BIN',999)+payload(b'ABC')+offer('TEST.BIN',999)+h(10,3,67)+bad+payload(b'DEF',3)+h(11,6)+h(8)+b'OO'
    f=Fixture(lib,rx);check('receive-CRC-duplicate-offer-estimate',f.run()==0 and f.received=={'TEST.BIN':b'ABCDEF'} and sum(e[0]=='open' for e in f.events)==1 and h(9,3) in f.tx)
    for end in (104,105,106,107):
        wire=offer('TEST.BIN',6)+h(10,0,67)+packet(b'ABC',67,end,0)
        wire+=(h(10,3,67) if end in (104,107) else b'')+packet(b'DEF',67,107,0)+h(11,6)+h(8)+b'OO'
        f=Fixture(lib,wire);check(f'receive-ending-{end}',f.run()==0 and f.received['TEST.BIN']==b'ABCDEF')
    for off in (0,3,6):
        rx=h(1,0x22000000)+h(9,off)+(h(3,6) if off<6 else b'')+h(1,0x22000000)+h(8)
        f=Fixture(lib,rx,[('TEST.BIN',b'ABCDEF')]);check(f'send-resume-{off}',f.run(True)==0 and ('seek',off) in f.events)
    rx=h(1,0x22000000)+h(9,7)
    f=Fixture(lib,rx,[('TEST.BIN',b'ABCDEF')]);check('sender-rejects-beyond-EOF',f.run(True)==6 and ('close',0) in f.events)
    rx=h(1,0x22000000)+h(13,3)+h(9)+h(3,6)+h(1,0x22000000)+h(8)
    f=Fixture(lib,rx,[('TEST.BIN',b'ABCDEF')]);check('sender-prefix-CRC',f.run(True)==0 and h(13,__import__('zlib').crc32(b'ABC')) in f.tx)
    for fault in ('cancel','transport','open','write','commit'):
        f=Fixture(lib,offer('TEST.BIN',3)+payload(b'ABC')+h(11,3)+h(8)+b'OO',fault=fault)
        result=f.run();check('receive-fault-'+fault,result!=0 and not f.received and f.stage is None)
    for fault in ('next','seek','read','close'):
        f=Fixture(lib,h(1,0x22000000)+h(9)+h(3,3)+h(1,0x22000000)+h(8),[('TEST.BIN',b'ABC')],fault=fault)
        check('send-fault-'+fault,f.run(True)==7)
        if fault=='close':check('failed-source-close-never-repeated',sum(e[0]=='close' for e in f.events)==1 and f.session.owned==2 and f.session.cleanup_status)
    f=Fixture(lib,offer('TEST.BIN',3)+payload(b'ABC')+h(11,3)+h(8));check('lost-final-OO',f.run()==8 and f.received['TEST.BIN']==b'ABC')
    f=Fixture(lib,offer('TEST.BIN',3)+h(10,0,67),fault='cleanup');check('failed-cleanup-retained',f.run()==4 and f.session.cleanup_status and f.session.owned and f.stage is not None)
    f=Fixture(lib);check('bounded-idle-timeout',f.run()==4)
    for name,data in (('missing-filename-NUL',b'TEST.BIN'),('missing-metadata-NUL',b'TEST.BIN\x00123'),('unsafe-filename',meta('../X',3))):
        f=Fixture(lib,h(4,0,67)+packet(data,67,107,0));check(name,f.run()==6 and not any(e[0]=='open' for e in f.events))
    names={f'F{i}.BIN':b'original' for i in range(12)}
    f=Fixture(lib,b''.join(offer(name,1) for name in names)+h(8)+b'OO');f.received=dict(names)
    check('many-existing-files-skipped',f.run()==0 and f.session.skipped==12 and f.received==names)
    f=Fixture(lib,h(1,0x22000000)+h(13,7),[('TEST.BIN',b'ABCDEF')]);check('reject-CRC-prefix-beyond-EOF',f.run(True)==6)
    for capacity in (1,7,128):
        data=bytes(range(17));rx=h(1,0x22000000|capacity)+h(9)
        expected=h(0)+h(4,0x01000000,67)+packet(send_meta('TEST.BIN',17).ljust(128,b'\0'),67,107,0)
        for off in range(0,len(data),capacity):
            rx+=h(3,min(off+capacity,len(data)));expected+=payload(data[off:off+capacity],off)
        rx+=h(1,0x22000000|capacity)+h(8);expected+=h(11,17,67)+h(8)+b'OO'
        f=Fixture(lib,rx,[('TEST.BIN',data)])
        check(f'finite-receiver-buffer-{capacity}',f.run(True)==0 and f.session.block==capacity and bytes(f.tx)==expected)
    f=Fixture(lib,h(1,0x22000000)+h(9)+h(3,0)+h(3,3)+h(1,0x22000000)+h(8),[('TEST.BIN',b'ABC')])
    check('stale-ACK-before-valid-ACK',f.run(True)==0 and sum(e[0]=='read' for e in f.events)==1)
    f=Fixture(lib,list(h(1,0x22000000)+h(9))+[65535]+list(h(9,3)+h(1,0x22000000)+h(8)),[('TEST.BIN',b'ABC')])
    check('lost-ACK-resend-and-verified-reposition',f.run(True)==0 and sum(e[0]=='read' for e in f.events)==2)
    f=Fixture(lib,h(1,0x22000000)+h(9)*20,[('TEST.BIN',b'ABC')])
    check('repeated-same-position-bounded',f.run(True)==4 and sum(e[0]=='close' for e in f.events)==1)
    for fmt in (65,67):
        for n in (2048,4096,8192):
            body=bytes(i&255 for i in range(n))
            f=Fixture(lib,offer('TEST.BIN',n,fmt)+payload(body,0,fmt)+h(11,n,fmt)+h(8)+b'OO')
            check(f'ZedZap-receive-{fmt}-{n}',f.run()==0 and f.received=={'TEST.BIN':body})
        wire=offer('TEST.BIN',16384,fmt)+h(10,0,fmt)+packet(bytes(8192),fmt,106,0)+packet(bytes(range(256))*32,fmt,107,0)+h(11,16384,fmt)+h(8)+b'OO'
        f=Fixture(lib,wire);check(f'ZedZap-ACK-buffer-reuse-{fmt}',f.run()==0 and f.received['TEST.BIN']==bytes(8192)+bytes(range(256))*32)
    f=Fixture(lib,offer('TEST.BIN',3)+payload(b'ABC')+h(11,2)+h(10,3,67)+packet(b'D',67,107,0)+h(11,4)+h(8)+b'OO')
    check('wrong-EOF-offset-never-commits',f.run()==0 and f.received['TEST.BIN']==b'ABCD')
    f=Fixture(lib,offer('TEST.BIN',3)+h(10,99)+payload(b'ABC')+h(11,3)+h(8)+b'OO')
    check('wrong-DATA-offset-resynchronizes',f.run()==0 and f.received['TEST.BIN']==b'ABC')
    # Exercise an independently packaged real peer, not a second hand-written state machine.
    peer_cases=[]
    for peer_kind in (('lrzsz','sexyz') if args.sexyz else ('lrzsz',)):
      for sending in (False,True):
        variants=[([],False),(['-e'],False),((['-w','256'] if sending and peer_kind=='lrzsz' else ['-o']),False),([],True)]
        if peer_kind=='sexyz':variants += [(['-8'],False),(['-8'],True)]
        elif not sending:variants += [(['-8','-L','8192'],False),(['-8','-L','8192'],True)]
        variants=[(flags,corrupt,1) for flags,corrupt in variants]
        if sending:variants.append(([],True,3))
        for flags,corrupt,corrupt_packet in variants:
            label=peer_kind+'-'+('upload' if sending else 'download')+('-'+'-'.join(flags) if flags else '-default')+('-corrupt' if corrupt else '')+('-packet'+str(corrupt_packet) if corrupt_packet>1 else '')
            directory=runroot/label
            directory.mkdir();data=bytes(range(256))*257+b'\x1a\0\xff@\r'
            files=([('EMPTY.BIN',b'')] if peer_kind=='lrzsz' else [])+[('ODD.BIN',b'A'),('ALL.BIN',data)]
            command=([str(args.sexyz.resolve()),'-raw']+flags+['rz' if sending else 'sz'] if peer_kind=='sexyz' else
                     [shutil.which('rz' if sending else 'sz'),'-b','-q']+flags)
            if not sending:
                for name,body in files:(directory/name).write_bytes(body)
                command+=(['-L','1024'] if peer_kind=='lrzsz' and '-L' not in flags else [])+[name for name,_ in files]
            with (directory/'stderr.log').open('wb') as log:
                peer=subprocess.Popen(command,cwd=directory,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=log,bufsize=0)
                try:
                    corrupt_at=4160 if '-8' in flags and not sending else 64
                    fixture=Fixture(lib,sources=files if sending else (),peer=peer,corrupt=corrupt,corrupt_at=corrupt_at,corrupt_packet=corrupt_packet);result=fixture.run(sending)
                    for name,raw in (('peer-consumed.bin',fixture.peer_wire),('engine-delivered.bin',fixture.engine_wire),('engine-output.bin',fixture.tx)):
                        (directory/name).write_bytes(raw)
                    (directory/'engine-result.json').write_text(json.dumps(dict(status=result,files=fixture.session.files,bytes=fixture.session.bytes,events=fixture.events))+'\n')
                    assert result==0,(label,result,(directory/'stderr.log').read_text(errors='replace'),fixture.events[-10:])
                    peer.wait(timeout=10)
                    actual={name:(directory/name).read_bytes() for name,_ in files} if sending else fixture.received
                    assert peer.returncode==0 and actual==dict(files),(label,result,peer.returncode,(directory/'stderr.log').read_text(errors='replace'),fixture.events[-10:])
                    assert fixture.corruptions==int(corrupt)
                    peer_cases.append(dict(label=label,passed=True,bytes=len(data)+1,files=len(files),command=command,peer_exit=peer.returncode,corruptions=fixture.corruptions,corrupt_at=corrupt_at if corrupt else None,corrupt_packet=corrupt_packet if sending and corrupt else None,
                        peer_sha256=hashlib.sha256(Path(command[0]).read_bytes()).hexdigest(),
                        retained_wire_sha256={str((directory/name).relative_to(ROOT)):hashlib.sha256((directory/name).read_bytes()).hexdigest() for name in ('peer-consumed.bin','engine-delivered.bin','engine-output.bin')},
                        file_sha256={name:hashlib.sha256(body).hexdigest() for name,body in files}))
                finally:
                    if peer.poll() is None:peer.kill();peer.wait()
                    peer.stdin.close();peer.stdout.close()
            print('PASS',label,flush=True)
    result=dict(passed=True,scripted_checks=len(cases),cases=cases,independent_peers=peer_cases,
        tools={name:shutil.which(name) for name in ('gcc','sz','rz')},
        sources={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources+[Path(__file__).resolve(),ROOT/'standalone/check_zmodem_wire.py',ROOT/'nix/flake.nix',ROOT/'nix/flake.lock',ROOT/'tools/dev']},
        scope='Maintained session engine with host transport/storage callbacks and independent pinned lrzsz pipes; optional selected stock Synchronet sexyz stdio helper uses two nonempty files only. No DOS filesystem/16-bit callback ABI, terminal UART/UI, physical modem or BBS session claim.')
    (OUT/'checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':main()
