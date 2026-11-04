#!/usr/bin/env python3
"""Execute recovered display modes against modeled BIOS/BDA and terminal UI boundaries."""
import argparse, hashlib, itertools, json, struct, subprocess
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_16, UC_HOOK_CODE, UC_HOOK_INTR
from unicorn.x86_const import *
ROOT = Path(__file__).resolve().parents[1]
PROVENANCE = ROOT/'reconstruction/display_modes/provenance.json'

def signed(n): return n if n < 32768 else n-65536

class Native:
    def __init__(self, code):
        self.u = u = Uc(UC_ARCH_X86, UC_MODE_16)
        u.mem_map(0, 0x100000)
        for at, data in code.items(): u.mem_write(0x10000+at, data)
        for at, cleanup in [(0x1bbe,0),(0x1fc4,0),(0x2fb8,0),(0x2530,8),(0x20a4,0)]:
            u.mem_write(0x10000+at, b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3')
        u.hook_add(UC_HOOK_CODE,self.observe)
        u.hook_add(UC_HOOK_INTR,self.interrupt)
    def word(self, at): return struct.unpack('<H',self.u.mem_read(0x50000+at,2))[0]
    def put(self, at, n): self.u.mem_write(0x50000+at,struct.pack('<H',n&65535))
    def bda(self, at, n): self.u.mem_write(at,bytes([n&255]))
    def observe(self,u,at,size,_):
        if at == 0x1f000: self.returned=True;u.emu_stop();return
        sp=u.reg_read(UC_X86_REG_SP)
        if at == 0x11bbe:self.events.append(('cursor',u.reg_read(UC_X86_REG_AX),u.reg_read(UC_X86_REG_DX)))
        elif at == 0x120a4:self.events.append(('reset',self.word(sp+2),self.word(0x1d2e)))
        elif at == 0x12fb8:self.events.append(('status',))
        elif at == 0x11fc4:self.events.append(('scroll',))
        elif at == 0x12530:self.events.append(('rectangle',))
        else:return
        for reg,n in [(UC_X86_REG_AX,0xbeef),(UC_X86_REG_BX,0x1234),(UC_X86_REG_CX,0x5678),(UC_X86_REG_DX,0x9abc)]:u.reg_write(reg,n)
    def interrupt(self,u,intno,_):
        assert intno==0x10
        ax=u.reg_read(UC_X86_REG_AX);bx=u.reg_read(UC_X86_REG_BX);cx=u.reg_read(UC_X86_REG_CX)
        ah=ax>>8;al=ax&255
        if ah==15:
            self.events.append(('probe',self.mode,self.rows))
            u.reg_write(UC_X86_REG_AX,self.mode|(80<<8));u.reg_write(UC_X86_REG_BX,0)
        elif ah==0:
            self.events.append(('mode',al))
            if not self.reject:
                self.mode=al&127;self.rows=self.scanlines//(14 if not self.vga else 16)
                # BIOS baseline text modes have25 rows at350/400 scanlines.
                self.bda(0x484,self.rows-1)
                self.u.mem_write(0x463,struct.pack('<H',0x3b4 if self.mode==7 else 0x3d4))
        elif ah==0x12:
            assert bx&255==0x30
            self.events.append(('scanlines',al))
            if not self.reject:self.scanlines={0:200,1:350,2:400}[al]
        elif ah==0x11:
            assert al in (0x11,0x12) and bx&255==0
            self.events.append(('font',al))
            flags=self.u.mem_read(0x487,1)[0]
            assert flags&1 == int(not self.vga and al!=0x11)
            if not self.reject:self.rows=self.scanlines//(14 if al==0x11 else 8);self.bda(0x484,self.rows-1)
        elif ah==1:
            self.events.append(('cursor_shape',cx));self.bda(0x460,cx);self.bda(0x461,cx>>8)
        elif ax==0x6f05:
            self.events.append(('vendor_mode',bx))
            if not self.reject:self.mode=bx&127;self.rows=25;self.bda(0x484,24)
        else:raise AssertionError(('unexpected BIOS',hex(ax),hex(bx)))
    def setup(self,cap=1,vga=1,preferred=3,hidden=0,reject=False,extended=0,mono=0):
        self.events=[];self.returned=False;self.vga=bool(vga);self.reject=reject
        self.mode=7 if mono else 3;self.rows=25;self.scanlines=400 if vga else 350
        for at,n in {0x7a6e:cap,0x7a70:vga,0x2070:preferred,0x1d46:hidden,0x7a74:25,
                     0x7a80:24,0x7a76:self.mode,0x7a86:mono,0x7a68:extended,0x7a66:0,0x7a92:0,
                     0x3252:0xa55a,0x1d2e:0x1234,0x3254:0x5678,0x334a:23,0x334c:24,
                     0xce3a:23,0xcee4:23,0x399c:0,0x399e:7,0x7a84:0x1800,0xceae:80}.items():self.put(at,n)
        self.bda(0x484,24);self.bda(0x487,0xa4);self.bda(0x489,0x90)
        self.u.mem_write(0x463,struct.pack('<H',0x3b4 if mono else 0x3d4));self.bda(0x460,7);self.bda(0x461,6)
    def execute(self,entry,args=(),callee_cleanup=0):
        u=self.u;sp=0xdfe0
        self.put(sp,0xf000)
        for i,n in enumerate(args):self.put(sp+2+2*i,n)
        u.mem_write(0x5df20,b'GUARD!')
        for r,n in [(UC_X86_REG_CS,0x1000),(UC_X86_REG_DS,0x5000),(UC_X86_REG_SS,0x5000),
                    (UC_X86_REG_ES,0x6000),(UC_X86_REG_SP,sp),(UC_X86_REG_BP,0xbabe),
                    (UC_X86_REG_SI,0xcafe),(UC_X86_REG_DI,0xabcd),(UC_X86_REG_EFLAGS,0x202)]:u.reg_write(r,n)
        u.emu_start(0x10000+entry,0,count=5000)
        assert self.returned and u.reg_read(UC_X86_REG_SP)==sp+2+callee_cleanup
        assert u.reg_read(UC_X86_REG_DS)==u.reg_read(UC_X86_REG_SS)==0x5000
        for r,n in [(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0xcafe),(UC_X86_REG_DI,0xabcd)]:assert u.reg_read(r)==n
        assert bytes(u.mem_read(0x5df20,6))==b'GUARD!'
    def display(self,selector,font=50,policy=0,**kw):
        self.setup(**kw);self.execute(0x2eaa,(selector,font,policy))
        assert self.events[0]==('cursor',0,0)
        if selector>4:
            assert self.events==[('cursor',0,0)] and self.word(0x3252)==0xa55a;return
        accepted=1 if selector in (3,4) and (signed(kw.get('preferred',3))<=0 or kw.get('cap',1)==0) else selector
        assert self.word(0x3252)==accepted,(selector,kw,self.events,self.word(0x3252))
        assert self.word(0x1d2e)==0x1234
        resets=[x for x in self.events if x[0]=='reset']
        assert resets==([] if policy else [('reset',1,0x5678)])
        if not policy:
            assert self.word(0x1d46)==int(kw.get('hidden',0)!=0)
            rows=self.rows if kw.get('hidden',0) else self.rows-1
            assert self.word(0x334c)==rows and self.word(0x334a)==rows-1
            assert self.word(0xce3a)==self.word(0xcee4)==rows-1
        if any(x[0]=='probe' for x in self.events):
            assert self.word(0x7a74)==self.rows and self.word(0x7a80)==self.rows-1
            assert self.word(0x7a7a)==160 and self.word(0x7a7c)==160*self.rows
        # Independently derive each expected hardware request. BIOS effects are a model.
        hardware=[]
        vga=bool(kw.get('vga',1));cap=bool(kw.get('cap',1))
        if selector in (1,2) or accepted!=selector:
            if vga:hardware.append(('scanlines',2))
            hardware.append(('mode',7 if kw.get('mono',0) else 3))
            if cap:hardware.append(('cursor_shape',0x607))
        elif selector in (3,4):
            preferred=kw.get('preferred',3)
            hardware.append(('vendor_mode',preferred) if kw.get('extended',0) and preferred&255>=0x12 else ('mode',preferred&255))
        # Commit chooses current rows for0,1,3; only2,4 use caller font.
        if accepted in (2,4) and font!=25 and cap:
            low=font&255
            if vga:
                hardware += [('scanlines',1 if low==43 else 2),('mode',self.mode|0x80)]
                if low in (28,43,50):hardware.append(('font',0x11 if low==28 else 0x12))
                else:hardware.append(('cursor_shape',0x607))
            else:hardware += [('font',0x12 if low==43 else 0x11),('cursor_shape',0x607)]
        actual=[x for x in self.events if x[0] in ('mode','vendor_mode','scanlines','font','cursor_shape')]
        assert actual==hardware,(selector,font,policy,kw,actual,hardware)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--original',type=Path);a=p.parse_args()
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
    manifest=json.loads(PROVENANCE.read_text());units=list(manifest['units'])
    for group,names in [('program_ui',('mode','scanlines','cursor_eight')),('program_display',('geometry',)),('local_controls',('status_toggle','status_clear'))]:
        file=ROOT/'reconstruction'/group/('status-lines-provenance.json' if group=='local_controls' else 'provenance.json')
        data=json.loads(file.read_text())
        for unit in data['units']:
            name=unit.get('name',Path(unit.get('file','')).stem)
            if name in names:units.append(dict(unit,name=name,source=unit.get('source',unit.get('file')),entry=unit.get('entry',unit.get('start'))))
    code={};sources=[Path(__file__).resolve(),PROVENANCE,ROOT/'reconstruction/uart/encodings.inc']
    original=a.original.read_bytes() if a.original else None
    if original:assert hashlib.sha256(original).hexdigest()==manifest['original_sha256']
    for unit in units:
        source=ROOT/unit['source'];entry=int(str(unit['entry']),0);target=out/(unit['name']+'.bin')
        subprocess.run(['nasm','-fbin','-I'+str(ROOT/'reconstruction/uart')+'/',str(source),'-o',str(target)],check=True)
        raw=target.read_bytes();assert len(raw)==unit['bytes'] and hashlib.sha256(raw).hexdigest()==unit['sha256'],unit['name']
        if original:assert raw==original[0x1200+entry:0x1200+entry+len(raw)]
        code[entry]=raw;sources.append(source)
        if source.parent.name=='display_modes':subprocess.run(['nasm','-fobj','-DDISPLAY_MODES_OMF','-I'+str(ROOT/'reconstruction/uart')+'/',str(source),'-o',str(out/(unit['name']+'.obj'))],check=True)
    m=Native(code);count=0
    for selector,font,policy,cap,vga,preferred,hidden in itertools.product(range(5),(25,28,43,50,0x12b,0xffff),(0,1),(0,1),(0,1),(0,3,0x8000),(0,1)):
        m.display(selector,font,policy,cap=cap,vga=vga,preferred=preferred,hidden=hidden);count+=1
    print('PASS composed dispatch/fallback/font/reflow:',count,flush=True)
    for selector in range(5,65536):m.display(selector)
    print('PASS all65531 invalid selectors home cursor without committing',flush=True)
    words=0
    for preferred in (1,3,0x7fff,0x8000,0xffff):
        m.display(3,preferred=preferred);words+=1
    for hidden in (2,0x7fff,0x8000,0xffff):m.display(0,hidden=hidden)
    for font in range(256):
        m.display(2,font=font);m.display(2,font=0xff00|font)
    print('PASS low-byte row aliases and signed preferred-mode boundaries',flush=True)
    for selector,font,policy,vga in itertools.product(range(5),(28,43,50),(0,1),(0,1)):
        m.display(selector,font,policy,vga=vga,reject=True)
    for preferred in (0x12,0x13):m.display(3,preferred=preferred,extended=1)
    print('PASS modeled BIOS refusal and vendor mode branch',flush=True)
    direct=0
    for cap,vga,requested in itertools.product((0,1,0x8000,0xffff),(0,1,0x8000,0xffff),(25,28,43,50,0x12b,0xff2b)):
        m.setup(cap=cap,vga=vga);m.execute(0x6ef6,(requested,),callee_cleanup=2);direct+=1
        if not cap:
            assert not m.events and m.word(0x7a74)==25
        else:
            expected=(28 if requested&255==28 else 43 if requested&255==43 else 50 if requested&255==50 else 25) if vga else (43 if requested&255==43 else 25)
            assert m.word(0x7a74)==expected,(cap,vga,requested,m.events,m.word(0x7a74))
    print('PASS direct row service, noncanonical capability WORDs:',direct,flush=True)
    for flags,selector in itertools.product(range(256),range(3)):
        m.setup();m.bda(0x489,flags);m.u.reg_write(UC_X86_REG_BX,selector);m.execute(0x7ee8)
        masked=flags&0x90
        allowed=not ((masked==0 and selector==1) or (masked==0x10 and selector==2))
        assert m.events==([('scanlines',selector)] if allowed else []),(flags,selector,m.events)
    print('PASS all256 BDA scanline capability bytes for3 selections',flush=True)
    for selector,mono,cap,vga,policy in itertools.product((1,2),(1,0x8000,0xffff),(0,1),(0,1),(0,1)):
        m.display(selector,50,policy,mono=mono,cap=cap,vga=vga)
    print('PASS monochrome baseline and noncanonical mono WORDs:48',flush=True)
    result=dict(passed=True,original_compared=bool(original),new_native_bytes=sum(x['bytes'] for x in manifest['units']),
                cases=dict(composed=count,invalid_selectors=65531,row_lowbyte_aliases=512,mode_boundaries=words,noncanonical_hidden=4,bios_refusal=60,vendor_mode=2,direct_rows=direct,bda_scanline_combinations=768,monochrome_baseline=48),
                sources={str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sources},
                scope=__doc__+' Actual recovered dispatcher, mode/font/scanline/geometry/status services execute; BIOS INT10 effects, terminal reset, cursor/scroll/status/rectangle rendering are modeled. No maintained-terminal integration, raw key normalization, pixels, BBS/NAWS or physical hardware acceptance; no deployed payload change.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
