#!/usr/bin/env python3
"""Clock string getter CPU replay, aliasing and optional original CRT comparison."""
import argparse, json, struct, subprocess
from pathlib import Path
from check_aspect_clock import Clock, DATA
from build_context_help import ROOT, sha
from unicorn.x86_const import (UC_X86_REG_AX, UC_X86_REG_BP, UC_X86_REG_SI,
    UC_X86_REG_DI, UC_X86_REG_SP, UC_X86_REG_IP, UC_X86_REG_DS, UC_X86_REG_SS,
    UC_X86_REG_EFLAGS)

GETTERS = [('date',8,0xdac2,bytes.fromhex('e90f5c'),0xbfd3),
           ('time0',20,0xdaff,bytes.fromhex('2bc050e8866e5bc3'),0xc327),
           ('time1',21,0xdb07,bytes.fromhex('b8010050e87d6e5bc3'),0xc36f)]


class BuiltinClock(Clock):
    def read_builtin(self, name, year=2026, month=11, day=17,
                     hour=0, minute=0, second=0):
        self.year,self.month,self.day=year,month,day
        self.hour,self.minute,self.second=hour,minute,second
        self.kind='date' if name=='date' else 'time'
        self.mode=int(name=='time1');self.events=[];self.seen=set()
        start=next(g[2] for g in GETTERS if g[0]==name)
        self.u.mem_write(DATA+0xd000,struct.pack('<H',0xf800))
        for reg,value in [(UC_X86_REG_SP,0xd000),(UC_X86_REG_BP,0xc000),
                          (UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678),
                          (UC_X86_REG_EFLAGS,0x202)]:self.u.reg_write(reg,value)
        self.u.emu_start(0x10000+start,0x20000,count=100000)
        assert self.u.reg_read(UC_X86_REG_IP)==0xf800
        assert self.u.reg_read(UC_X86_REG_SP)==0xd002
        assert self.u.reg_read(UC_X86_REG_BP)==0xc000
        assert self.u.reg_read(UC_X86_REG_SI)==0x1234 and self.u.reg_read(UC_X86_REG_DI)==0x5678
        assert self.u.reg_read(UC_X86_REG_DS)==self.u.reg_read(UC_X86_REG_SS)==DATA>>4
        assert self.u.reg_read(UC_X86_REG_EFLAGS)&0x600==0x200
        expected_event='DOS0x2a' if name=='date' else 'DOS0x2c'
        assert self.events==[expected_event],self.events
        pointer=self.u.reg_read(UC_X86_REG_AX);text=self.string(pointer)
        expected=(f'{month:02}/{day:02}/{year-1900:02}' if name=='date' else
            f'{hour if self.mode else hour%12 or 12:02}:{minute:02}:{second:02}'+
            ('' if self.mode else 'PM' if hour>=12 else 'AM')).encode()
        assert text==expected,(name,text,expected)
        return pointer,text


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--helpers',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--original',type=Path)
    a=p.parse_args();out=a.output.resolve()
    assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    helper_path=a.helpers/'result.json';helpers=json.loads(helper_path.read_text())
    assert helpers['passed']
    for n,h in helpers['sources'].items():assert sha(ROOT/n)==h,n
    units=list(helpers['units']);original=a.original.read_bytes() if a.original else None
    if original is not None:assert sha(a.original)=='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
    getter_units=[]
    for i,(name,selector,start,code,thunk) in enumerate(GETTERS,1):
        binary=out/(name+'.bin')
        subprocess.run(['nasm','-fbin','-I'+str(ROOT/'reconstruction/uart')+'/',
            '-DASPECT_CLOCK_BUILTINS_FLAT','-DASPECT_CLOCK_BUILTINS_UNIT='+str(i),
            str(ROOT/'src/aspect/clock_builtins.asm'),'-o',str(binary)],check=True)
        assert binary.read_bytes()==code,name
        offset=109184-0xd0d0+start
        if original is not None:
            assert original[offset:offset+len(code)]==code
            assert struct.unpack_from('<H',original,0x25950+0x4cf8+selector*2)[0]==thunk
            assert original[0x1200+thunk:0x1200+thunk+12]==bytes.fromhex('9aec02ec0a1000ea')+struct.pack('<HH',start,0)
        getter_units.append(dict(name=name,selector=selector,start=start,bytes=len(code),
            file_start=offset,output=str(binary.relative_to(ROOT)),sha256=sha(binary)))
    units+=getter_units;source=BuiltinClock(units)
    native=BuiltinClock(helpers['units'],original) if original is not None else None
    if native:
        # Original resident helpers/CRT, plus exact original overlay16 bodies.
        for r in getter_units:native.u.mem_write(0x10000+r['start'],original[r['file_start']:r['file_start']+r['bytes']])
    cases=[dict(name='date',year=y,month=m,day=d)
           for y in (1980,1999,2000,2026,2099) for m in (1,6,12) for d in (1,15,28)]
    cases += [dict(name=name,hour=h,minute=m,second=s)
              for name in ('time0','time1') for h in range(24)
              for m in (0,29,59) for s in (0,29,59)]
    for case in cases:
        result=source.read_builtin(**case)
        if native:assert native.read_builtin(**case)==result
    alias_checks=0
    for model in [source]+([native] if native else []):
        date,date_text=model.read_builtin('date')
        for first,second in [('time0','time1'),('time1','time0')]:
            before,text=model.read_builtin(first,hour=1,minute=2,second=3)
            after,new=model.read_builtin(second,hour=23,minute=59,second=59)
            assert before==after and model.string(before)==new and text!=new
            assert date!=before and model.string(date)==date_text
            alias_checks+=2
        again,new=model.read_builtin('date',year=2027,month=2,day=3)
        assert again==date and model.string(date)==new and new!=date_text;alias_checks+=1
    result=dict(passed=True,cpu_cases=len(cases),original_comparisons=len(cases) if native else 0,
        exact_native_bytes=sum(r['bytes'] for r in getter_units),alias_checks=alias_checks,
        getters=getter_units,helper_receipt_sha256=sha(helper_path),
        sources={n:sha(ROOT/n) for n in ['src/aspect/clock_builtins.asm',
            'reconstruction/uart/encodings.inc','standalone/check_aspect_clock_builtins.py',
            'standalone/check_aspect_clock.py']},original_inputs=[str(a.original)] if a.original else [],
        scope='477 getter outcomes with real recovered helpers; modeled DOS2A/2C and source sprintf. Optional original executes original resident CRT. Every read issues one DOS query, no destination/flush, near ABI and shared DATE/TIME aliases checked; no full DOS VM or physical observation.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS clock getters:',len(cases),'CPU cases;',result['original_comparisons'],'original comparisons;',alias_checks,'alias checks')


if __name__=='__main__':main()
