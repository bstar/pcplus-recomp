#!/usr/bin/env python3
"""Check linked snapshot lease owners, bounds, identity and failed-retirement quarantine."""
import argparse,json,struct
from pathlib import Path
from unicorn.x86_const import *
import check_aspect_parent_process as parent_model
import check_aspect_program_client as child_model
from terminal_memory import inspect_terminal_memory
from build_path_session import ROOT,sha

class Parent(parent_model.Owner):
    def __init__(self,layout):
        super().__init__();self.root=self.base_segment-16
        self.put('process_psp',self.root)
        self.mcb=(self.root-1)*16
        self.uc.mem_write(self.mcb,b'M'+struct.pack('<HH',self.root,layout['retained_parent_paragraphs']))
        self.frame=self.symbols['redisplay_live']
        self.uc.mem_write(self.frame,b'\xa5'*8000)
    def boundary(self,u,address,size,unused):
        if address==self.symbols['terminal_script_window_close']:
            sp=u.reg_read(UC_X86_REG_SP);ip=int.from_bytes(u.mem_read(self.data_base+sp,2),'little')
            u.reg_write(UC_X86_REG_SP,sp+2);u.reg_write(UC_X86_REG_IP,ip);u.reg_write(UC_X86_REG_AX,0)
        else:super().boundary(u,address,size,unused)

class Child(child_model.Client):
    def __init__(self):
        self.pointer=(0x2000,0x6000);self.bad_byte=None
        super().__init__()
    def endpoint(self,u,address,size,unused):
        old=self.reply
        if address==0x80000 and u.reg_read(UC_X86_REG_AX)==18 and not self.reply:
            i=u.reg_read(UC_X86_REG_BX)
            self.reply=self.bad_byte if self.bad_byte is not None else struct.pack('<2H',*self.pointer)[i]
        super().endpoint(u,address,size,unused);self.reply=old

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['terminal','runner','output']:p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();binary=a.terminal.resolve();runner=a.runner.resolve();out=a.output.resolve()
    assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir()
    parent_model.OUT=binary.parent;child_model.OUT=runner.parent
    for b,flag in [(binary,'experimental_aspect_snapshot_lease'),(runner,'experimental_snapshot_lease')]:
        m=json.loads(b.with_name('manifest.json').read_text());assert m[flag] and sha(b)==m['binary_sha256']
        for n,h in m['sources'].items():assert sha(ROOT/n)==h,n
    layout=inspect_terminal_memory(binary,binary.with_name('terminal.map'));cases=[]
    def record(name):cases.append(dict(case=name,passed=True))
    def parent():
        m=Parent(layout);assert m.operation(9,1)==0;return m
    for size in [1,4000,4480,6880,8000]:
        m=parent();assert m.operation(17,size)==0 and m.get('render_snapshot_owned')==1
        pointer=bytes(m.operation(18,i) for i in range(4));off,seg=struct.unpack('<2H',pointer)
        assert seg*16+off==m.frame
        assert bytes(m.uc.mem_read(m.frame,8000))==b'\xa5'*8000
        assert m.operation(10)==10 and m.get('render_program_owned')==2
        assert m.operation(17,size)==10 and m.operation(18,4)==7
        assert m.operation(19,1)==7 and m.get('render_snapshot_owned')==1
        assert m.operation(19)==0 and m.operation(10)==0
        record('parent-size-and-retire-'+str(size))
    for size in [0,8001,65535]:
        m=parent();assert m.operation(17,size)==7 and not m.get('render_snapshot_owned');record('parent-bounds-'+str(size))
    for field,width in [('_redisplay_active',2),('_redisplay_live_ready',2),('_command_menu_active',2),
                        ('terminal_editor_screen_owned',1),('terminal_browser_screen_owned',1),
                        ('terminal_script_window_active',2),('terminal_script_confirm_active',2)]:
        m=parent();m.uc.mem_write(m.symbols[field],(1).to_bytes(width,'little'))
        assert m.operation(17,4000)==10 and not m.get('render_snapshot_owned');record('competing-'+field)
    for kind in ['owner','type','short','overflow']:
        m=parent()
        if kind=='owner':m.uc.mem_write(m.mcb+1,struct.pack('<H',m.root+1))
        elif kind=='type':m.uc.mem_write(m.mcb,b'X')
        else:m.uc.mem_write(m.mcb+3,struct.pack('<H',1 if kind=='short' else 65535))
        assert m.operation(17,4000)==10 and not m.get('render_snapshot_owned');record('mcb-'+kind)
    for field in ['render_child_psp','render_child_ds','terminal_program_kind','terminal_program_active','render_attached']:
        m=parent();m.put(field,0)
        for op,val in [(17,4000),(18,0),(19,0)]:assert m.operation(op,val)==10
        record('identity-'+field)
    m=Parent(layout);assert m.operation(9,0)==0 and m.operation(17,4000)==10;record('noclear-cannot-borrow')
    m=parent();assert m.operation(18,0)==10 and m.operation(19)==10;record('no-unowned-pointer-or-release')
    for entry,args in [('terminal_directory_choose',[]),('terminal_directory_edit',[0]),('terminal_redisplay_key',[])]:
        m=parent();assert m.operation(17,4000)==0
        m.uc.reg_write(UC_X86_REG_AX,0x8400)
        value=m.call(entry,args)
        if entry=='terminal_directory_choose':assert value==2
        elif entry=='terminal_directory_edit':assert value==0
        else:assert m.uc.reg_read(UC_X86_REG_EFLAGS)&1 and not m.get('_redisplay_active')
        assert m.get('render_snapshot_owned')==1 and bytes(m.uc.mem_read(m.frame,8000))==b'\xa5'*8000
        record('leased-frame-blocks-'+entry)
    for size in [0,8001,65535]:
        m=Child();assert m.call('_aspect_render_program_begin',[1])==0;before=list(m.requests)
        assert m.call('_aspect_render_snapshot_begin',[size])==0 and m.requests==before;record('child-bounds-'+str(size))
    m=Child();assert m.call('_aspect_render_snapshot_begin',[4000])==0;record('child-needs-program')
    for error in [1,7,10,14,65535]:
        m=Child();assert m.call('_aspect_render_program_begin',[1])==0
        assert m.call('_aspect_render_snapshot_begin',[4000])==m.pointer[0] and m.uc.reg_read(UC_X86_REG_DX)==m.pointer[1]
        before=list(m.requests);assert m.call('_aspect_render_snapshot_begin',[4000])==0 and m.requests==before
        m.reply=error;assert m.call('_aspect_render_snapshot_end')==(error if error<=14 else 10)
        before=list(m.requests);assert m.call('_aspect_render_program_end',[0])==10 and m.requests==before
        m.reply=0;assert m.call('_aspect_render_snapshot_end')==0 and m.call('_aspect_render_program_end',[0])==0
        record('failed-release-quarantine-'+str(error))
    for pointer,bad in [((0xffff,0x6000),None),((0,0),None),((0x2000,0x6000),256),((0x2000,0x6000),65535)]:
        m=Child();m.pointer=pointer;m.bad_byte=bad;assert m.call('_aspect_render_program_begin',[1])==0
        assert m.call('_aspect_render_snapshot_begin',[4000])==0 and m.requests[-1]==(19,0)
        assert m.call('_aspect_render_program_end',[0])==0;record('invalid-pointer-'+str(pointer)+'-'+str(bad))
    sources={n:sha(ROOT/n) for n in ['standalone/check_snapshot_lease.py','standalone/check_aspect_parent_process.py','standalone/check_aspect_program_client.py','standalone/dos_image.py','standalone/terminal_memory.py']}
    r=dict(passed=True,cases=cases,parent_sha256=sha(binary),child_sha256=sha(runner),sources=sources,
        scope=__doc__+' Actual linked code; caller identity, view admission, window close and child scalar endpoint are modeled. Real MCB reads use declared fixtures; no actual DOS/BIOS/UART or physical claim. Separate composed DOS tests required.')
    (out/'result.json').write_text(json.dumps(r,indent=2)+'\n');print('PASS',len(cases),'linked snapshot ownership cases')
if __name__=='__main__':main()
