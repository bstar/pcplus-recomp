#!/usr/bin/env python3
"""Fault-test the Help parent admission core with a bounded memory backend."""
import argparse,ctypes as C,json,struct,subprocess
from pathlib import Path
from build_context_help import ROOT,sha

class Context(C.Structure):
    _fields_=[('path_offset',C.c_uint),('title_offset',C.c_uint),('topic',C.c_uint),('ui_words',C.c_uint*6)]
class Parent(C.Structure):
    _fields_=[('parent_psp',C.c_uint),('parent_ds',C.c_uint),('descriptor_offset',C.c_uint),('context',Context),('path',C.c_char*81),('title',C.c_char*31)]
COPY=C.CFUNCTYPE(C.c_uint,C.c_void_p,C.c_ulong,C.POINTER(C.c_ubyte),C.c_uint)
class Source(C.Structure):
    _fields_=[('child_psp',C.c_uint),('cookie',C.c_void_p),('copy',COPY)]

class Fixture:
    def __init__(self,lib,parent=0x1000,child=0x6000):
        self.lib=lib;self.mem=bytearray(0xa0000);self.parent=parent;self.child=child
        self.ds=parent+0x20;self.off=0x100;self.path=0x200;self.title=0x300
        self.mcb=(parent-1)*16;self.at=self.ds*16+self.off
        self.log=[];self.by_address={};self.fail_at=None;self.change_at=None
        self.mem[child*16:child*16+2]=b'\xcd\x20';self.word(child*16+22,parent)
        self.mem[parent*16:parent*16+2]=b'\xcd\x20'
        self.mem[self.mcb]=ord('M');self.word(self.mcb+1,parent);self.word(self.mcb+3,0x2000)
        self.raw=[self.path,self.title,41,0xffff,7,15,0x70,8,16];self.descriptor()
        self.mem[self.ds*16+self.path:self.ds*16+self.path+9]=b'HELP.HLP\0'
        self.mem[self.ds*16+self.title:self.ds*16+self.title+13]=b'PCPlus Help!\0'
        self.callback=COPY(self.copy);self.source=Source(child,None,self.callback)
    def word(self,at,value):self.mem[at:at+2]=struct.pack('<H',value)
    def descriptor(self):self.mem[self.at:self.at+18]=struct.pack('<9H',*self.raw)
    def copy(self,cookie,at,out,n):
        self.log.append((at,n));self.by_address[at]=self.by_address.get(at,0)+1
        if self.fail_at==len(self.log):return 1
        if at<0 or at+n>len(self.mem):return 1
        if self.change_at==at and self.by_address[at]==2:self.mem[at]^=1
        C.memmove(out,bytes(self.mem[at:at+n]),n)
        return 0
    def run(self,expected=0,text=None):
        out=Parent();C.memset(C.addressof(out),0xa5,C.sizeof(out))
        before=bytes(out);pointer=(self.ds<<16)|self.off
        result=self.lib.help_parent_read(C.byref(self.source),str(pointer).encode() if text is None else text,C.byref(out))
        assert result==expected,(result,expected,self.log)
        assert all(at>=0 and at+n<=0xa0000 for at,n in self.log)
        if result:assert bytes(out)==before,'failed admission published output'
        else:
            assert (out.parent_psp,out.parent_ds,out.descriptor_offset)==(self.parent,self.ds,self.off)
            assert (out.context.path_offset,out.context.title_offset,out.context.topic,*out.context.ui_words)==tuple(self.raw)
        return out

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    names=['src/help/parent.c','src/help/parent.h','src/help/format.c','src/help/format.h','standalone/test_help_parent.py']
    sources={name:sha(ROOT/name) for name in names}
    import shutil
    for name in names:
        dest=out/'source'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,dest)
    library=out/'parent.so'
    subprocess.run(['cc','-std=c89','-Wall','-Wextra','-Werror','-pedantic','-fPIC','-shared','-o',str(library),str(out/'source/src/help/parent.c'),str(out/'source/src/help/format.c')],check=True)
    lib=C.CDLL(str(library));lib.help_parent_read.argtypes=[C.POINTER(Source),C.c_char_p,C.POINTER(Parent)];lib.help_parent_read.restype=C.c_uint
    cases=0
    for parent,child in ((0x1000,0x6000),(0x6000,0x1000),(0x50,0x9ffe)):
        for topic in (0,41,46,47,0x8000,0xffff):
            f=Fixture(lib,parent,child);f.raw[2]=topic;f.descriptor();v=f.run();assert v.path==b'HELP.HLP' and v.title==b'PCPlus Help!';cases+=1
    for length in (0,1,65,80,81):
        f=Fixture(lib);at=f.ds*16+f.path;f.mem[at:at+length+1]=b'X'*length+b'\0'
        v=f.run(6 if length in (0,81) else 0)
        if length not in (0,81):assert v.path==b'X'*length
        cases+=1
    for length in (0,1,30,31):
        f=Fixture(lib);at=f.ds*16+f.title;f.mem[at:at+length+1]=b'T'*length+b'\0';v=f.run(6 if length==31 else 0)
        if length<31:assert v.title==b'T'*length
        cases+=1
    # Signed/raw context values are preserved; fallback belongs to the consumer.
    for value in range(256):
        f=Fixture(lib);f.raw[3:]=[value*257]*6;f.descriptor();f.run();cases+=1
    for text in (b'',b'0',b'65535',b'-1',b'+1',b' 65536',b'65536 ',b'4294967296',b'4294967295',b'99999999999'):
        f=Fixture(lib);f.run(2,text);assert not f.log;cases+=1
    # Each metadata rejection is before reading any descriptor/string.
    mutations=[(lambda f:setattr(f.source,'child_psp',0x4f),3),
        (lambda f:setattr(f.source,'child_psp',0x9fff),3),
        (lambda f:f.word(f.child*16,0),3),
        (lambda f:f.word(f.child*16+22,0x4f),3),
        (lambda f:f.word(f.child*16+22,0xffff),3),
        (lambda f:f.word(f.child*16+22,f.child),3),
        (lambda f:f.mem.__setitem__(f.mcb,ord('Q')),4),
        (lambda f:f.word(f.mcb+1,8),4),
        (lambda f:f.word(f.mcb+3,15),4),
        (lambda f:f.word(f.mcb+3,0xffff),4),
        (lambda f:f.word(f.mcb+3,0x5001),4),
        (lambda f:f.word(f.parent*16,0),3)]
    for mutate,status in mutations:
        f=Fixture(lib);mutate(f);f.run(status);assert not any(at==f.at for at,n in f.log);cases+=1
    f=Fixture(lib);f.mem[f.mcb]=ord('Z');f.run();cases+=1
    # A descriptor may fit exactly through segment FFFF; no offset wrap.
    f=Fixture(lib);f.off=0xffee;f.at=f.ds*16+f.off;f.descriptor();f.run();cases+=1
    f=Fixture(lib);f.off=0xffef;f.at=f.ds*16+f.off;f.run(2);assert not f.log;cases+=1
    for field in (0,1):
        f=Fixture(lib);f.raw[field]=0;f.descriptor();f.run(6);cases+=1
        f=Fixture(lib);f.raw[field]=0xffff;f.descriptor();f.mem[f.ds*16+0xffff]=ord('X');f.run(5);cases+=1
    # Parent PSP bytes and separately owned/foreign conventional memory are excluded.
    for ds,off in ((0x1000,0x16),(0x4000,0x100),(0xa000,0x100),(0x50,0x100)):
        f=Fixture(lib);f.ds=ds;f.off=off;f.run(5);cases+=1
    for field in (0,1):
        f=Fixture(lib);f.ds=0x2f00;f.at=f.ds*16+f.off
        f.mem[f.ds*16+f.path:f.ds*16+f.path+9]=b'HELP.HLP\0'
        f.mem[f.ds*16+f.title:f.ds*16+f.title+13]=b'PCPlus Help!\0'
        f.raw[field]=0x2000;f.descriptor();f.run(5);cases+=1
    # Inject failure at every actual read, including final consistency reads.
    f=Fixture(lib);f.run();reads=len(f.log)
    for failure in range(1,reads+1):
        f=Fixture(lib);f.fail_at=failure;f.run(7);assert len(f.log)==failure;cases+=1
    for address in (0x60000,0x0fff0,0x10300):
        f=Fixture(lib);f.change_at=address;f.run(8);cases+=1
    # Null arguments fail before invoking the memory callback.
    f=Fixture(lib);value=Parent()
    for source,text,target in ((None,b'65536',C.byref(value)),(C.byref(f.source),None,C.byref(value)),(C.byref(f.source),b'65536',None)):
        assert lib.help_parent_read(source,text,target)==1;assert not f.log;cases+=1
    report=dict(passed=True,cases=cases,read_failures=reads,sources=sources,library_sha256=sha(library),scope='Host-compiled admission core with explicit conventional-memory callback. Includes output nonpublication on all failures, ownership/bounds, parent above/below child, raw UI/context preservation, every read failure and changed identity/MCB/descriptor. Actual DOS backend is tested separately through EXEC; no full help UI or physical acceptance.')
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))

if __name__=='__main__':main()
