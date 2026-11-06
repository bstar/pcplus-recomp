#!/usr/bin/env python3
"""Execute the real timing-enabled overlay; only BIOS time and the host sink are modeled."""
import argparse,json,re,struct,subprocess
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_CODE
from unicorn.x86_const import *
from build_chat_module import ROOT,build
from build_path_session import sha
DAY=1573040


class Machine:
    def __init__(self,binary,base=0x3000):
        self.u=Uc(UC_ARCH_X86,UC_MODE_16);self.u.mem_map(0,0x100000)
        raw=binary.read_bytes();h=struct.unpack_from('<14H',raw);self.base=base;self.ds=0x1000
        self.u.mem_write(base*16,raw[h[4]*16:])
        for i in range(h[3]):
            off,seg=struct.unpack_from('<2H',raw,h[12]+i*4);at=base*16+seg*16+off
            value=struct.unpack('<H',self.u.mem_read(at,2))[0];self.u.mem_write(at,struct.pack('<H',(value+base)&65535))
        self.symbols={n:base*16+int(s,16)*16+int(o,16) for s,o,n in re.findall(
            r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',binary.with_name('PCCHAT.MAP').read_text(),re.M|re.I)}
        self.state=0x200;self.request=0x1000;self.returned=False;self.units=[];self.effects=[]
        self.tick=100;self.edge_after=None;self.edge_delta=1;self.completed=0
        self.u.mem_write(0x70100,b'\xb8\x01\x00\xcb') # Declared host sink: return1, RETF.
        self.u.hook_add(UC_HOOK_CODE,self.stop,None,0x90000,0x90000)
        self.u.hook_add(UC_HOOK_CODE,self.unit,None,self.symbols['_chat_timing_one'],self.symbols['_chat_timing_one'])
        self.u.hook_add(UC_HOOK_CODE,self.complete,None,self.symbols['chat_timing_complete'],self.symbols['chat_timing_complete'])
        self.u.hook_add(UC_HOOK_CODE,self.sink,None,0x70100,0x70100)
        self.set_tick(100)
    def set_tick(self,tick):
        self.tick=tick;self.u.mem_write(0x46c,struct.pack('<I',tick))
    def stop(self,u,at,size,user):self.returned=True;u.emu_stop()
    def unit(self,u,at,size,user):
        sp=u.reg_read(UC_X86_REG_SP);ss=u.reg_read(UC_X86_REG_SS)
        self.units.append(struct.unpack('<H',u.mem_read(ss*16+sp+4,2))[0])
    def complete(self,u,at,size,user):
        self.completed+=1
        if self.edge_after and self.completed==self.edge_after:self.set_tick((self.tick+self.edge_delta)%DAY)
    def sink(self,u,at,size,user):
        ss=u.reg_read(UC_X86_REG_SS);sp=u.reg_read(UC_X86_REG_SP)
        self.effects.append(tuple(struct.unpack('<2H',u.mem_read(ss*16+sp+4,4))))
    def call(self,name,args=(),irq=True,limit=40000000):
        u=self.u;guards=((UC_X86_REG_DS,self.ds),(UC_X86_REG_SS,self.ds),
             (UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678))
        for reg,value in (*guards,(UC_X86_REG_CS,self.base),(UC_X86_REG_ES,0xb800),
            (UC_X86_REG_BX,0xa55a),(UC_X86_REG_EFLAGS,0x202 if irq else 2)):u.reg_write(reg,value)
        words=[0,0x9000,*args];sp=0xf000-2*len(words)
        u.mem_write(self.ds*16+sp,struct.pack('<'+'H'*len(words),*words));u.reg_write(UC_X86_REG_SP,sp)
        self.returned=False;u.emu_start(self.symbols[name],0,count=limit)
        assert self.returned and u.reg_read(UC_X86_REG_SP)==sp+4,name
        for reg,value in guards:assert u.reg_read(reg)==value,(name,reg)
        assert bool(u.reg_read(UC_X86_REG_EFLAGS)&512)==irq,name
        return u.reg_read(UC_X86_REG_AX)
    def timing(self):return struct.unpack('<4HI3H',self.u.mem_read(self.ds*16+self.state,18))
    def reset(self):self.call('_chat_timing_reset',[self.state,self.ds])
    def prepare(self):return self.call('_chat_timing_prepare',[self.state,self.ds])
    def effect(self,kind,value):return self.call('_chat_timing_effect',[self.state,self.ds,kind,value])
    def ready(self,chunks=55,start=100,delta=1):
        self.reset();self.set_tick(start);assert self.prepare()==0
        self.set_tick((start+1)%DAY);self.edge_after=self.completed+chunks;self.edge_delta=delta
        return self.prepare()
    def word(self,at,value):self.u.mem_write(self.ds*16+at,struct.pack('<H',value))
    def request_word(self,at,value):self.word(self.request+at,value)
    def pointer(self,at,off,seg):self.u.mem_write(self.ds*16+self.request+at,struct.pack('<2H',off,seg))
    def operation(self,op):self.request_word(2,op);return self.call('_chat_module_dispatch',[self.request,self.ds])


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir()
    module=build(out/'module',timing=True);binary=out/'module/PCCHAT.OVL';cases=[]
    native=out/'native-pace.bin'
    subprocess.run(['nasm','-fbin','-I'+str(ROOT/'reconstruction/uart')+'/',str(ROOT/'reconstruction/meta_keys/pace.asm'),'-o',str(native)],check=True)
    proof=json.loads((ROOT/'reconstruction/meta_keys/provenance.json').read_text())
    unit=next(x for x in proof['units'] if Path(x['file']).name=='pace.asm')
    assert sha(native)==unit['sha256']
    sample=Machine(binary);loop=bytes(sample.u.mem_read(sample.symbols['chat_timing_loop'],11))
    assert loop==native.read_bytes()[0x6b87-0x6b72:0x6b92-0x6b72]
    def check(name,fn):fn();cases.append(dict(case=name,passed=True));print(name,'PASS',flush=True)
    def primitive():
        m=Machine(binary);loops=[]
        m.u.hook_add(UC_HOOK_CODE,lambda *args:loops.append(1),None,m.symbols['chat_timing_loop'],m.symbols['chat_timing_loop'])
        for count in (0,1,2,512,65535):
            before=len(loops);m.call('_chat_timing_one',[count],irq=count!=2)
            assert len(loops)-before==(count or 65536)
            assert m.u.reg_read(UC_X86_REG_BX)==0xa55a and m.u.reg_read(UC_X86_REG_ES)==0xb800
        for irq in (False,True):
            m.set_tick(0x12345678);m.call('_chat_timing_ticks',irq=irq)
            assert (m.u.reg_read(UC_X86_REG_DX)<<16|m.u.reg_read(UC_X86_REG_AX))==0x12345678
    check('actual-native-unit-loop-zero-wrap-full-word-and-clock-IF-ABI',primitive)
    def calibration():
        for n,start in [(4,100),(55,100),(128,DAY-2),(7039,100)]:
            m=Machine(binary);assert m.ready(n,start)==1
            state=m.timing();assert state[:4]==(3,0,n*512//55,n)
            before=len(m.units);assert m.prepare()==1 and len(m.units)==before
        m=Machine(binary);m.reset()
        for _ in range(10):assert m.prepare()==0 and not m.units
    check('calibration-chunks-4-to7039-formula-midnight-and-yielding-alignment',calibration)
    def invalid():
        for n,delta,error in [(1,1,4),(10,2,2)]:
            m=Machine(binary);assert m.ready(n,100,delta)==0 and m.timing()[1]==error
        m=Machine(binary);m.reset();m.prepare();m.set_tick(101)
        assert m.prepare()==0 and m.timing()[:2]==(4,3) and len(m.units)==7039
        before=m.timing();assert m.prepare()==0 and m.timing()==before
        m.reset();m.set_tick(DAY);assert m.prepare()==0 and m.timing()[:2]==(4,2)
        m.reset();assert m.call('_chat_timing_prepare',[m.state,m.ds],irq=False)==0 and m.timing()[:2]==(4,1)
    check('stalled-clock-bound-invalid-time-coarse-measurement-IF-off-and-sticky-fault',invalid)
    def pauses():
        for start in (0,65530,DAY-5):
            m=Machine(binary);m.reset();m.set_tick(start);assert m.effect(5,9)==0
            for elapsed in (0,1,9):m.set_tick((start+elapsed)%DAY);assert m.effect(5,9)==0
            before=m.timing();assert m.effect(6,0)==0 and m.timing()==before
            m.set_tick((start+10)%DAY);assert m.effect(5,9)==1 and m.timing()[5:]==(0,0,0)
        for value,ticks in [(0,1),(65535,1),(65534,65535)]:
            m=Machine(binary);m.reset();m.set_tick(0);assert m.effect(5,value)==0
            m.set_tick(ticks);assert m.effect(5,value)==1
        m=Machine(binary);m.reset();m.effect(5,9);m.set_tick(20);assert m.effect(5,9)==1
    check('ten-tick-pause-low-word-midnight-missed-observation-and-native-word-wrap',pauses)
    def pacing():
        m=Machine(binary);assert m.ready()==1;before=len(m.units)
        assert m.effect(6,0)==1 and len(m.units)==before
        for at in range(7):
            assert m.effect(6,7)==(at==6) and len(m.units)==before+at+1
        assert m.units[before:]==[512]*7
        assert m.effect(6,65535)==0 and m.timing()[-1]==65534
        before=m.timing();count=len(m.units)
        for kind,value in [(5,9),(6,1),(1,65)]:assert m.effect(kind,value)==0 and m.timing()==before and len(m.units)==count
        m.reset();assert m.timing()==(0,0,0,0,0,0,0,0)
    check('zero-and-seven-native-pacing-units-full-word-pending-mismatch-and-reset',pacing)
    def composition():
        for base in (0x3000,0x4100):
            m=Machine(binary,base);m.state=0x200+430 # Timing fields inside the actual448-byte session.
            m.request_word(0,0x103);m.pointer(6,0x200,m.ds);m.pointer(10,0,0x5000)
            for at,value in [(26,4000),(28,25),(30,0x17),(32,0x71),(34,0x17),(36,1),(38,1),(40,1),(44,1)]:m.request_word(at,value)
            assert m.operation(1)==1
            m.u.mem_write(m.ds*16+0x2000,b'A~^@B\0'+bytes(46));m.pointer(22,0x2000,m.ds)
            for at,value in [(48,52),(32,126),(38,1),(46,7)]:m.request_word(at,value)
            assert m.operation(8)==1
            m.pointer(18,0x100,0x7000);m.pointer(22,0,0);m.request_word(46,32)
            assert m.operation(9)==0 and not m.effects
            m.set_tick(101);m.edge_after=m.completed+55;assert m.operation(9)>0
            assert m.effects==[(4,65),(1,65)]
            # Ordinary session RX/history/log continue while a pacing unit or
            # BIOS pause remains pending; the timed sink never sees RX effects.
            m.u.mem_write(m.ds*16+0x3000,bytes(range(256)));m.pointer(14,0x3000,m.ds)
            m.request_word(48,240);assert m.operation(3)==1
            assert m.operation(4)==2 and m.effects[-2:]==[(3,240),(2,240)]
            m.effects=m.effects[:-2]
            for _ in range(80):
                if not struct.unpack('<H',m.u.mem_read(m.ds*16+0x200+362,2))[0]:break
                if m.timing()[5]==5:m.set_tick((m.tick+1)%DAY)
                assert m.operation(9)!=65535
            else:raise AssertionError('Timed TEXT did not complete')
            assert m.effects==[(4,65),(1,65),(1,0),(4,66),(1,66)]
            assert m.operation(5)==0 and m.timing()==(0,0,0,0,0,0,0,0)
            # A BIOS-wait fault must surface even with pacing0 (no calibration
            # entry), retain the owner until abort, then reset cleanly.
            assert m.operation(1)==1;m.u.mem_write(m.ds*16+0x2000,b'~\0'+bytes(50))
            m.pointer(22,0x2000,m.ds);m.request_word(48,52);m.request_word(46,0)
            assert m.operation(8)==1;m.pointer(22,0,0);m.request_word(46,32)
            count=len(m.effects);m.set_tick(DAY)
            assert m.operation(9)==65535 and m.timing()[:2]==(4,2) and len(m.effects)==count
            assert m.operation(9)==65535 and m.operation(5)==0 and m.timing()==(0,0,0,0,0,0,0,0)
    check('two-relocations-actual-module-TEXT-native-delay-boundaries-and-background-RX',composition)
    names=list(module['sources'])+['standalone/check_chat_timing_cpu.py','standalone/build_path_session.py',
        'reconstruction/meta_keys/pace.asm','reconstruction/meta_keys/provenance.json','reconstruction/uart/encodings.inc']
    report=dict(passed=True,cases=cases,module_sha256=module['binary_sha256'],module_image_bytes=module['image_bytes'],
        state_bytes=448,timing_bytes=18,sources={n:sha(ROOT/n) for n in names},
        scope=__doc__+' All product instructions execute; synthetic time changes at completed native512-iteration chunks, host sink records TX/echo/history/log. Two module relocation bases and RX during pending timing. Raw unit loop counts0/1/2/512/65535 and full-word wait arguments verified. Full65535-unit pacing duration is not executed; first pending decrement is checked. No wall-clock calibration accuracy, original echo rendering, parent frontend, real UART/BBS or physical acceptance.')
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
