#!/usr/bin/env python3
"""Native status visibility and actual keyboard Ctrl-]/Ctrl-- selector paths.
Scroll/cursor/status drawing, rectangle rendering and DISPLAY are modeled boundaries.
"""
import argparse,hashlib,itertools,json,struct,subprocess
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
UNITS=[('toggle','reconstruction/local_controls/status_toggle.asm',0x46ba,123,'cf297698247fc782264cfbfd3c5133d2af81dfd229a2a3538d5a179e13fb4198'),
       ('clear','reconstruction/local_controls/status_clear.asm',0x4795,33,'0701086fdef896102811dfcb3006c25fad78e7b004b39b0708cfa21c7c458aec'),
       ('keyboard','reconstruction/keyboard_mapping/dispatch.asm',0x138a,1771,'61af5884e3ca080b2fb221d74b63e0ae2a8be06fc35b77c777cc2e1b6024ae18')]

def signed(v):return v if v<32768 else v-65536

class Native:
    def __init__(self,code):
        self.u=u=Uc(UC_ARCH_X86,UC_MODE_16);u.mem_map(0,0x100000)
        for entry,data in code.items():u.mem_write(0x10000+entry,data)
        for entry,cleanup in [(0x1fc4,0),(0x1bbe,0),(0x2fb8,0),(0x2530,8),(0x2eaa,0)]:
            u.mem_write(0x10000+entry,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3')
        u.hook_add(UC_HOOK_CODE,self.observe)
    def word(self,offset):return struct.unpack('<H',self.u.mem_read(0x50000+offset,2))[0]
    def put(self,offset,value):self.u.mem_write(0x50000+offset,struct.pack('<H',value&65535))
    def observe(self,u,at,size,_):
        sp=u.reg_read(UC_X86_REG_SP)
        def arg(index):return self.word(sp+2+2*index)
        if at==0x11fc4:self.events.append(('scroll',))
        elif at==0x11bbe:self.events.append(('cursor',u.reg_read(UC_X86_REG_AX),u.reg_read(UC_X86_REG_DX)))
        elif at==0x12fb8:self.events.append(('status',))
        elif at==0x12530:self.events.append(('rectangle',*(arg(i) for i in range(4))))
        elif at==0x12eaa:
            self.events.append(('display',*(arg(i) for i in range(3))))
            self.put(0x3252,arg(0) if self.accepted is None else self.accepted)
        elif at==0x1f000:self.returned=True;u.emu_stop()
        if at in (0x11fc4,0x11bbe,0x12fb8,0x12530,0x12eaa):
            for r,v in [(UC_X86_REG_AX,0xbeef),(UC_X86_REG_BX,0x1234),(UC_X86_REG_CX,0x5678),(UC_X86_REG_DX,0x9abc)]:u.reg_write(r,v)
    def execute(self,entry):
        self.events=[];self.returned=False;u=self.u
        self.put(0xdffe,0xf000);u.mem_write(0x5df30,b'GUARD!')
        for r,v in [(UC_X86_REG_CS,0x1000),(UC_X86_REG_DS,0x5000),(UC_X86_REG_SS,0x5000),
                    (UC_X86_REG_SP,0xdffe),(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0xcafe),
                    (UC_X86_REG_DI,0xabcd),(UC_X86_REG_EFLAGS,0x202)]:u.reg_write(r,v)
        u.emu_start(0x10000+entry,0,count=3000)
        assert self.returned and u.reg_read(UC_X86_REG_SP)==0xe000
        assert u.reg_read(UC_X86_REG_DS)==u.reg_read(UC_X86_REG_SS)==0x5000
        for r,v in [(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0xcafe),(UC_X86_REG_DI,0xabcd)]:assert u.reg_read(r)==v
        assert bytes(u.mem_read(0x5df30,6))==b'GUARD!'
    def status(self,hidden=0,physical=25,shown=24,oldlast=23,last=None,bottom=None,cursor=12,column=17,width=80,coordinate=0x1800,attribute=31,keyboard=False):
        last=oldlast if last is None else last;bottom=oldlast if bottom is None else bottom
        fields={0x1d46:hidden,0x7a74:physical,0x7a80:shown,0x334a:oldlast,0x334c:oldlast+1,
                0xce3a:last,0xcee4:bottom,0x399c:cursor,0x399e:column,0xceae:width,0x7a84:coordinate,
                0x1d6e:0,0x1d70:0,0x373c:0,0xcffa:29}
        for at,value in fields.items():self.put(at,value)
        self.u.mem_write(0x5d008,bytes([attribute]));self.execute(0x1604 if keyboard else 0x46ba)
        hide=int(hidden==0);rows=physical if hide else shown;newlast=(rows-1)&65535
        assert self.word(0x1d46)==hide and self.word(0x334c)==rows and self.word(0x334a)==newlast
        assert self.word(0xce3a)==(newlast if last==oldlast else last)
        assert self.word(0xcee4)==(newlast if bottom==oldlast else bottom)
        for at,value in fields.items():
            if at not in (0x1d46,0x334a,0x334c,0xce3a,0xcee4):assert self.word(at)==value&65535,hex(at)
        assert self.u.mem_read(0x5d008,1)==bytes([attribute])
        if hide:expected=[('rectangle',attribute,(coordinate+width-1)&65535,coordinate,0)]
        else:
            expected=[]
            if signed(shown)<=signed(cursor):expected=[('scroll',),('cursor',newlast,column)]
            expected.append(('status',))
        assert self.events==expected,(fields,self.events,expected)
    def lines(self,current,adapter,font=50,accepted=None):
        self.accepted=accepted
        fields={0xcffa:31,0x1d6e:0,0x1d70:0,0x373c:0,0xcee6:current,0x2070:adapter,0x1d4e:font,0x3252:0xffff}
        for at,value in fields.items():self.put(at,value)
        self.execute(0x1604)
        value=signed(current);choices=2 if adapter==0 else 4
        remainder=abs(value)%choices
        if value<0:remainder=-remainder
        request=(remainder+1)&65535
        assert self.events==[('display',request,font,0)],(current,adapter,self.events,request)
        result=request if accepted is None else accepted
        assert self.word(0xcee6)==self.word(0x3252)==result
        for at,value in fields.items():
            if at not in (0xcee6,0x3252):assert self.word(at)==value


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--original',type=Path);a=p.parse_args()
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
    original=a.original.read_bytes() if a.original else None
    if original:assert hashlib.sha256(original).hexdigest()=='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
    code={}
    for name,source,entry,size,digest in UNITS:
        target=out/(name+'.bin');subprocess.run(['nasm','-fbin','-I'+str(ROOT/'reconstruction/uart')+'/',str(ROOT/source),'-o',str(target)],check=True)
        data=target.read_bytes();assert len(data)==size and hashlib.sha256(data).hexdigest()==digest
        if original:assert data==original[0x1200+entry:0x1200+entry+size]
        code[entry]=data
        if name!='keyboard':subprocess.run(['nasm','-fobj','-DSTATUS_TOGGLE_OMF','-I'+str(ROOT/'reconstruction/uart')+'/',str(ROOT/source),'-o',str(out/(name+'.obj'))],check=True)
    m=Native(code)
    for hidden in range(65536):m.status(hidden=hidden)
    print('PASS all65536 status WORDs, geometry/margins/clear/draw',flush=True)
    count=0
    for hidden,physical,last_follows,bottom_follows,cursor in itertools.product((0,1,0x8000,0xffff),(25,43,50),(False,True),(False,True),(0,23,24,25,49,50,0x8000,0xffff)):
        shown=physical-1;oldlast=shown-1 if hidden==0 else physical-1
        m.status(hidden,physical,shown,oldlast,last=oldlast if last_follows else 7,bottom=oldlast if bottom_follows else 11,cursor=cursor,keyboard=True);count+=1
    print('PASS real normalized Ctrl-] keyboard path:',count,'inputs',flush=True)
    clears=0
    for width,coordinate,attribute in itertools.product((1,40,80,132),(0,0x1800,0xfffe),(0,7,31,255)):
        m.status(width=width,coordinate=coordinate,attribute=attribute);clears+=1
    print('PASS native status rectangle arguments:',clears,flush=True)
    for hidden in (0,1,2,0x7fff,0x8000,0xffff):
        for at,value in [(0x1d46,hidden),(0x7a84,0x1800),(0xceae,80)]:m.put(at,value)
        m.u.mem_write(0x5d008,b'\x1f');m.execute(0x4795)
        assert m.events==([('rectangle',31,0x184f,0x1800,0)] if hidden else [])
        assert m.word(0x1d46)==hidden and m.word(0x7a84)==0x1800 and m.word(0xceae)==80
    print('PASS direct clear zero/nonzero policy:6 inputs',flush=True)
    for adapter in range(65536):m.lines(adapter%4,adapter)
    print('PASS all65536 adapter WORDs through Ctrl--',flush=True)
    for adapter in (0,1):
        for current in range(65536):m.lines(current,adapter)
    print('PASS all65536 signed current-mode WORDs for both cycle lengths',flush=True)
    fallback=0
    for adapter,current,font,accepted in itertools.product((0,1,2,0xffff),(0,1,2,3,4,0x8000,0xffff),(0,14,50,0xffff),(0,1,4,0x55aa)):
        m.lines(current,adapter,font,accepted);fallback+=1
    print('PASS display accepted/fallback state:',fallback,flush=True)
    files=[Path(__file__).resolve(),ROOT/'reconstruction/uart/encodings.inc']+[ROOT/u[1] for u in UNITS]
    result=dict(passed=True,new_native_status_bytes=156,keyboard_native_bytes=1771,original_compared=bool(original),
                cases=dict(all_status_words=65536,status_keyboard=count,status_rectangle=clears,direct_clear=6,all_adapter_words=65536,all_current_words=131072,display_result=fallback),
                sources={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
                scope=__doc__+'156 exact new native bytes composed with1771 existing keyboard bytes. Real key selection and geometry/margin/clear/signed cycle/result commit instructions execute. All normalized keys, not raw BIOS normalization, are input. No actual DISPLAY implementation/BIOS changes, rendered pixels, maintained owner/geometry/ANSI/NAWS integration, DOS/BBS/SIP/physical acceptance or deployment.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS status and line-selector recovery')

if __name__=='__main__':main()
