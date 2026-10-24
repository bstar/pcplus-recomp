#!/usr/bin/env python3
"""Check real pane copies, native foreign-DS counterexample and maintained repair."""
import argparse,hashlib,itertools,json,struct
from pathlib import Path
from unicorn import UC_HOOK_CODE,UC_HOOK_INSN
from unicorn.x86_const import *
from dos_image import DosImage

ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


class Viewport(DosImage):
    def __init__(self,fixed,original=None):
        kind='VIEWPORT'if fixed else'CONTROL'
        super().__init__(ROOT/f'build/viewport/{kind}.EXE',ROOT/f'build/viewport/{kind}.map')
        if original is not None:
            proof=json.loads((ROOT/'reconstruction/viewport/provenance.json').read_text())
            self.ds=0x3000;self.data_base=self.ds*16;self.code_segment=0x1000;self.code_base=0x10000;self.return_offset=0xf000
            self.symbols={name:self.data_base+int(at,16)for at,name in proof['state'].items()}
            self.symbols.update(text_cga_status_port=self.data_base+0x7a8e,viewport_flags=self.data_base+0xd600,
                                terminal_stack_top=self.data_base+0xff00)
            for start,end in [(0x4816,0x4861),(0x644c,0x64b8),(0x77ae,0x77bd),(0x77be,0x77d2)]:
                self.uc.mem_write(self.code_base+start,original[0x1200+start:0x1200+end])
            for name,offset in [('viewport_save_left',0x4816),('viewport_enter',0x482a),('viewport_save_right',0x483b),
                                ('viewport_leave',0x4850),('viewport_copy',0x644c),('ui_cga_unblank',0x77ae)]:
                self.symbols[name]=self.code_base+offset
            self.symbols['viewport_invoke']=self.code_base+0xe800
            self.uc.mem_write(self.symbols['viewport_invoke'],b'\xff\x36\x00\xd6\xe8'+struct.pack('<H',(0x644c-0xe807)&65535)+b'\xc3')
        self.outputs=[];self.foreign=[]
        self.uc.hook_add(UC_HOOK_CODE,self.observe)
        self.uc.hook_add(UC_HOOK_INSN,self.input,None,1,0,UC_X86_INS_IN)
        self.uc.hook_add(UC_HOOK_INSN,self.output,None,1,0,UC_X86_INS_OUT)
    def observe(self,u,address,size,_):
        if address==self.symbols['ui_cga_unblank']and u.reg_read(UC_X86_REG_DS)!=self.ds:
            self.foreign.append(u.reg_read(UC_X86_REG_DS))
    def input(self,u,port,size,_):return 8
    def output(self,u,port,size,value,_):self.outputs.append((port,value))


def exercise(fixed,geometry,active,operation,port,original=None):
    columns,rows,extra,offset=geometry;m=Viewport(fixed,original)
    m.put('viewport_physical_columns',columns);m.put('viewport_rows',rows);m.put('screen_viewport_left',extra)
    m.put('text_video_segment',0x8000);m.put('erase_shadow_segment',0x6000);m.put('erase_shadow_offset',offset)
    m.put('screen_viewport_active',active);m.put('text_cga_status_port',port)
    video=bytearray((i*37+91)&255 for i in range(columns*rows*2))
    shadow=bytearray((i*19+7)&255 for i in range((columns+extra)*rows*2))
    before_video=bytes(video);before_shadow=bytes(shadow)
    guard=bytes([0xa5])*32
    m.uc.mem_write(0x80000-32,guard+bytes(video)+guard)
    m.uc.mem_write(0x60000+offset-32,guard+bytes(shadow)+guard)
    # Distinct nonzero decoys expose the native callback's foreign DS read.
    port_offset=m.offset('text_cga_status_port')
    m.uc.mem_write(0x80000+port_offset,b'\x34\x12');m.uc.mem_write(0x60000+port_offset,b'\x34\x12')
    if isinstance(operation,int):
        ops=[(bool(operation&0x8000),operation&1)];m.put('viewport_flags',operation);entry='viewport_invoke'
    else:
        entry='viewport_'+operation
        ops=({'save_left':[(False,0)]if active else[],
              'save_right':[]if active else[(False,1)],
              'enter':([]if active else[(False,1)])+[(True,0)],
              'leave':([(False,0)]if active else[])+[(True,1)]})[operation]
    for restore,right in ops:
        for row in range(rows):
            v=row*columns*2;s=(row*(columns+extra)+right*extra)*2
            if restore:video[v:v+columns*2]=shadow[s:s+columns*2]
            else:shadow[s:s+columns*2]=video[v:v+columns*2]
    m.call(entry,limit=1000000)
    assert bytes(m.uc.mem_read(0x80000-32,len(video)+64))==guard+video+guard
    assert bytes(m.uc.mem_read(0x60000+offset-32,len(shadow)+64))==guard+shadow+guard
    assert m.get('screen_viewport_active')==active
    assert m.uc.reg_read(UC_X86_REG_DS)==m.uc.reg_read(UC_X86_REG_SS)==m.ds
    assert [m.uc.reg_read(r)for r in(UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI)]==[0xbabe,0x1234,0x5678]
    assert len(m.foreign)==(0 if fixed else len(ops))
    assert len([event for event in m.outputs if event==(0x12d8,0x2d)])==(0 if fixed else len(ops))
    return dict(video_sha256=hashlib.sha256(video).hexdigest(),shadow_sha256=hashlib.sha256(shadow).hexdigest(),
                foreign_unblank_calls=len(m.foreign),outputs=m.outputs,copy_operations=len(ops))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--original',type=Path);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();manifest=json.loads((ROOT/'build/viewport/manifest.json').read_text())
    for name,digest in manifest['sources'].items():assert sha(ROOT/name)==digest
    for name,digest in manifest['products'].items():assert sha(ROOT/'build/viewport'/name)==digest
    original=None
    if args.original:
        proof=json.loads((ROOT/'reconstruction/viewport/provenance.json').read_text())
        assert sha(args.original)==proof['original_sha256'];original=args.original.read_bytes()
    cases=[]
    geometries=[(2,2,1,32),(80,24,52,32),(80,25,52,0x123),(40,3,10,35)]
    for geometry,active,operation,port in itertools.product(geometries,(0,1),(0,1,0x8000,0x8001,0x42,0xfffe,'save_left','save_right','enter','leave'),(0,0x3da)):
        native=exercise(False,geometry,active,operation,port)
        fixed=exercise(True,geometry,active,operation,port)
        assert native['video_sha256']==fixed['video_sha256']and native['shadow_sha256']==fixed['shadow_sha256']
        if original is not None:assert exercise(False,geometry,active,operation,port,original)==native
        cases.append(dict(geometry=geometry,active=active,operation=operation,port=port,passed=True,
                          native_foreign_calls=native['foreign_unblank_calls'],maintained_foreign_calls=fixed['foreign_unblank_calls']))
    sources=dict(manifest['sources']);sources[str(Path(__file__).relative_to(ROOT))]=sha(Path(__file__))
    sources['standalone/dos_image.py']=sha(ROOT/'standalone/dos_image.py')
    result=dict(passed=True,cases=cases,paired_original=original is not None,products=manifest['products'],sources=sources,
                scope='160 native and maintained pane-copy/switch cases with exact guarded far/video buffers, real CGA instructions and modeled retrace. Optional original instruction replay. Native foreign-DS callback reproduced; maintained DS restoration verified. Caller must admit geometry/extents/DF; no live width integration.')
    args.output.write_text(json.dumps(result,indent=2)+'\n');print('PASS',len(cases),'viewport cases; paired original:',original is not None)


if __name__=='__main__':main()
