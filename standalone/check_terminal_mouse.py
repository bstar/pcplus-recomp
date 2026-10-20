#!/usr/bin/env python3
"""Execute the production foreground policy with explicit DOS/driver boundaries."""
import json
from pathlib import Path
import re
import struct
from check_mouse_keyboard import Owner
from build_native_mouse import ROOT, sha
from unicorn.x86_const import *

OUT = ROOT / 'build/terminal-mouse'


class TerminalOwner(Owner):
    def __init__(self):
        super().__init__(OUT / 'TERMINAL.EXE', OUT / 'terminal.map', bank=True, dos_memory=True)
        self.resize_fail = False
        self.retained = False
        self.keep = json.loads((OUT / 'manifest.json').read_text())['memory_layout']['retained_parent_paragraphs']
        self.put('process_psp', self.base_segment - 0x10)
        self.put('process_keep_paragraphs', self.keep)
        self.put('process_minimum_paragraphs', self.keep)
        self.put('process_memory_released', 0)
        listing = (OUT / 'terminal.map').read_text()
        bss = re.search(r'^_BSS\s+BSS\s+DGROUP\s+([0-9a-f]+):([0-9a-f]+)\s+([0-9a-f]+)', listing, re.M|re.I)
        self.uc.mem_write(self.base+int(bss[1],16)*16+int(bss[2],16), bytes([0xa5])*int(bss[3],16))
        self.invoke('_terminal_mouse_bootstrap')

    def boundary(self,uc,address,size,data):
        if address==self.symbols.get('capture_fs_canonical_'):
            destination=uc.reg_read(UC_X86_REG_DX)
            uc.mem_write(self.data_base+destination,b'D:\\TEST.PRM\0'.ljust(128,b'\0'))
            self.events.append(('canonical',))
            uc.reg_write(UC_X86_REG_AX,0)
            sp=uc.reg_read(UC_X86_REG_SP);ss=uc.reg_read(UC_X86_REG_SS)
            uc.reg_write(UC_X86_REG_IP,int.from_bytes(uc.mem_read(ss*16+sp,2),'little'))
            uc.reg_write(UC_X86_REG_SP,sp+2)
            return
        super().boundary(uc,address,size,data)

    def interrupt(self, uc, number, data):
        ax = uc.reg_read(UC_X86_REG_AX)
        if number == 0x21 and ax >> 8 == 0x4a:
            assert uc.reg_read(UC_X86_REG_ES) == self.get('process_psp')
            assert uc.reg_read(UC_X86_REG_BX) == self.keep
            self.events.append(('DOS-resize', self.keep))
            flags = uc.reg_read(UC_X86_REG_EFLAGS)
            uc.reg_write(UC_X86_REG_EFLAGS, flags | 1 if self.resize_fail else flags & ~1)
            if self.resize_fail:uc.reg_write(UC_X86_REG_AX, 8)
        elif number == 0x21 and ax >> 8 == 9:
            assert uc.reg_read(UC_X86_REG_DS) != self.ds
            self.events.append(('DOS-retention-message',))
        elif number == 0x21 and ax >> 8 == 0x31:
            assert ax == 0x310e and uc.reg_read(UC_X86_REG_DX) == self.keep
            self.events.append(('DOS-retain', 14, self.keep))
            self.retained = True
            uc.emu_stop()
        else:
            super().interrupt(uc, number, data)

    def far(self, name, args=(), retain=False):
        uc = self.uc
        bank = next(c for c in json.loads((OUT/'manifest.json').read_text())['memory_layout']['code_segments'] if c['name']=='MOUSE_CODE')
        for reg,value in [(UC_X86_REG_CS,self.base_segment+bank['relative_segment']),
                          (UC_X86_REG_DS,self.ds),(UC_X86_REG_SS,self.ds),(UC_X86_REG_EFLAGS,0x202),
                          (UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678)]:
            uc.reg_write(reg,value)
        words = [self.return_offset,self.base_segment,*args]
        sp = 0xe000-2*len(words)
        uc.mem_write(self.data_base+sp,struct.pack('<'+'H'*len(words),*words))
        uc.reg_write(UC_X86_REG_SP,sp)
        self.returned = False
        uc.emu_start(self.symbols[name],0,count=500000)
        if retain:
            assert self.retained and not self.returned and self.allocations
        else:
            assert self.returned and not self.retained and uc.reg_read(UC_X86_REG_SP)==sp+4
            assert uc.reg_read(UC_X86_REG_DS)==self.ds and uc.reg_read(UC_X86_REG_SS)==self.ds
            assert bytes(uc.mem_read(self.data_base+sp+4,len(args)*2))==struct.pack('<'+'H'*len(args),*args)
            for reg,value in [(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678)]:
                assert uc.reg_read(reg)==value
        return uc.reg_read(UC_X86_REG_AX)

    def stage(self, x, y, size=0x4f0):
        image = bytearray(0x4f0)
        struct.pack_into('<HH',image,0x4e4,x,y)
        self.uc.mem_write(self.data_base+0x5000,bytes(image))
        return self.far('_terminal_mouse_stage_far',[0x5000,size])

    def offer(self, x, y, size=0x4f0):
        image=bytearray(0x4f0);struct.pack_into('<HH',image,0x4e4,x,y)
        self.uc.mem_write(self.data_base+0x5000,bytes(image))
        return self.far('_terminal_mouse_offer_far',[0x5000,size])

    def finish(self):
        self.far('terminal_mouse_exit')
        assert not self.allocations and self.driver==self.original_driver


def main():
    manifest = json.loads((OUT/'manifest.json').read_text())
    assert manifest['experimental_mouse'] and manifest['binary_sha256']==sha(OUT/'TERMINAL.EXE')
    assert all(sha(ROOT/p)==h for p,h in manifest['sources'].items())
    cases = []
    def passed(name, **values):cases.append(dict(case=name,passed=True,**values))
    m = TerminalOwner()
    assert m.invoke('_terminal_mouse_start')==0
    assert m.get('mouse_scale_x')==8 and m.get('mouse_scale_y')==8
    assert m.stage(3,7)==15
    assert m.invoke('_terminal_mouse_pause')==0 and m.invoke('_terminal_mouse_resume')==0
    assert m.get('mouse_scale_x')==8 and m.get('mouse_scale_y')==8
    m.finish();passed('poisoned-BSS-bootstrap-defaults-lifecycle-and-live-stage-refusal')
    for x,y,size in [(0,4,0x4f0),(8,0,0x4f0),(1000,4,0x4f0),(8,1000,0x4f0),(8,4,0x4ef)]:
        m = TerminalOwner()
        assert m.stage(8,4)==0 and m.stage(x,y,size)==15
        assert m.invoke('_terminal_mouse_start')==0
        assert m.get('mouse_scale_x')==8 and m.get('mouse_scale_y')==4
        m.finish();passed('transactional-PRM-rejection',x=x,y=y,size=size)
    for name,value in [('process_psp',0),('process_keep_paragraphs',0x0f),
                        ('process_minimum_paragraphs',0),('process_minimum_paragraphs',0xffff)]:
        m = TerminalOwner();m.put(name,value)
        assert m.invoke('_terminal_mouse_start')==15 and not m.events and not m.allocations
        m.finish();passed('invalid-parent-bound-rejects-before-DOS',field=name)
    m = TerminalOwner();m.resize_fail = True
    assert m.invoke('_terminal_mouse_start')==15 and m.get('process_memory_released')==0
    assert m.events==[('DOS-resize',m.keep)]
    m.finish();passed('DOS-resize-failure-precedes-driver-mutation')
    m = TerminalOwner();m.put('process_memory_released',1)
    assert m.invoke('_terminal_mouse_start')==0 and not any(e[0]=='DOS-resize' for e in m.events)
    m.finish();passed('already-released-parent-is-not-resized-again')
    for missing in ('vector','storage'):
        m = TerminalOwner()
        if missing=='vector':m.vector=(0,0)
        else:m.size=0
        assert m.invoke('_terminal_mouse_start')==0 and not m.allocations
        assert m.invoke('_terminal_mouse_pause')==0 and m.invoke('_terminal_mouse_resume')==0
        m.finish();passed('BIOS-fallback-without-acquisition',missing=missing)
    m = TerminalOwner();m.alloc_fail = True
    assert m.invoke('_terminal_mouse_start')==15 and not m.allocations
    assert not any(e==('driver',0x21) for e in m.events)
    m.finish();passed('DOS-allocation-failure-has-no-driver-reset')
    for boundary in ('ready','suspended'):
        m = TerminalOwner();assert m.invoke('_terminal_mouse_start')==0
        if boundary=='suspended':assert m.invoke('_terminal_mouse_pause')==0
        m.vector=(0,0)
        assert m.invoke('_terminal_mouse_resume' if boundary=='suspended' else '_terminal_mouse_pause')==2
        mark=len(m.events);m.far('terminal_mouse_exit',retain=True)
        assert not any(e[0]=='driver' for e in m.events[mark:])
        assert m.events[-1]==('DOS-retain',14,m.keep)
        passed('quarantine-keeps-callback-allocation-without-unknown-driver-call',boundary=boundary)
    m=TerminalOwner();assert m.stage(8,4)==0 and m.invoke('_terminal_mouse_start')==0
    assert m.invoke('_terminal_mouse_pause')==0
    native=m.native();storage=m.storage();events=len(m.events)
    assert m.offer(16,8)==16384 and m.native()==native and len(m.events)==events
    assert m.far('_terminal_mouse_commit_far')==0 and m.native()==native and m.storage()==storage
    assert m.invoke('_terminal_mouse_resume')==0 and m.get('mouse_scale_x')==16 and m.get('mouse_scale_y')==8
    m.finish();passed('live-settings-commit-retains-original-snapshot-and-allocation')
    for x,y,size in [(0,8,0x4f0),(16,0,0x4f0),(1000,8,0x4f0),(16,1000,0x4f0),(16,8,0x4ef)]:
        m=TerminalOwner();assert m.stage(8,4)==0 and m.invoke('_terminal_mouse_start')==0
        assert m.invoke('_terminal_mouse_pause')==0 and m.offer(16,8)==16384
        assert m.offer(x,y,size)==15 and m.far('_terminal_mouse_commit_far')==0
        assert m.invoke('_terminal_mouse_resume')==0 and (m.get('mouse_scale_x'),m.get('mouse_scale_y'))==(8,4)
        m.finish();passed('failed-offer-discards-previous-candidate',x=x,y=y,size=size)
    m=TerminalOwner();assert m.stage(8,4)==0 and m.invoke('_terminal_mouse_start')==0
    assert m.offer(16,8)==15
    assert m.invoke('_terminal_mouse_pause')==0 and m.offer(16,8)==16384
    m.far('_terminal_mouse_discard_far');assert m.far('_terminal_mouse_commit_far')==0
    assert m.invoke('_terminal_mouse_resume')==0 and m.get('mouse_scale_y')==4
    m.finish();passed('live-stage-needs-suspension-and-abort-does-not-adopt')
    for fault in ('vector','size','guard','callback'):
        m=TerminalOwner();assert m.stage(8,4)==0 and m.invoke('_terminal_mouse_start')==0
        assert m.invoke('_terminal_mouse_pause')==0 and m.offer(16,8)==16384
        if fault=='vector':m.vector=(0,0)
        elif fault=='size':m.size+=1
        elif fault=='guard':m.uc.mem_write(m.storage(),b'\0')
        else:m.put('mouse_depth',0)
        mark=len(m.events);assert m.far('_terminal_mouse_commit_far')==2
        assert not any(e[0]=='driver' and e[1] in (0,0x21,0x0c,0x17) for e in m.events[mark:])
        m.vector=(0x7000,0x40);m.size=256;m.uc.mem_write(m.storage(),b'\xa5');m.put('mouse_depth',0xffff)
        m.finish();passed('live-commit-quarantines-without-reinitializing-untrusted-state',fault=fault)
    m=TerminalOwner();assert m.stage(8,4)==0 and m.invoke('_terminal_mouse_start')==0
    assert m.invoke('_terminal_mouse_pause')==0;mark=len(m.events)
    assert m.offer(8,4)==0 and m.far('_terminal_mouse_commit_far')==0 and len(m.events)==mark
    assert m.invoke('_terminal_mouse_resume')==0;m.finish();passed('unchanged-file-offer-needs-no-reconfigure-or-driver-call')
    m=TerminalOwner();assert m.stage(8,4)==0 and m.invoke('_terminal_mouse_start')==0
    storage=m.storage()
    for x,y in [(16,8),(32,16),(8,4)]:
        assert m.invoke('_terminal_mouse_pause')==0 and m.offer(x,y)==16384
        assert m.far('_terminal_mouse_commit_far')==0 and m.invoke('_terminal_mouse_resume')==0
        assert (m.get('mouse_scale_x'),m.get('mouse_scale_y'))==(x,y) and m.storage()==storage
    assert m.events.count(('driver',0x16))==1
    m.finish();passed('repeated-edits-and-revert-retain-one-original-driver-snapshot')
    m=TerminalOwner();assert m.stage(8,4)==0 and m.invoke('_terminal_mouse_start')==0
    assert m.invoke('_terminal_mouse_pause')==0 and m.offer(16,8)==16384
    m.uc.mem_write(m.data_base+0x5000,b'TEST.PRM\0'.ljust(64,b'\0'))
    source=bytearray(44);struct.pack_into('<H',source,42,13)
    m.uc.mem_write(m.data_base+0x6000,bytes(source))
    assert m.invoke('_live_setup_bind',[0x5000,0,0x6000])==0
    assert m.invoke('_live_setup_acknowledge',[0])==0
    assert m.invoke('_terminal_mouse_resume')==0 and (m.get('mouse_scale_x'),m.get('mouse_scale_y'))==(8,4)
    m.finish();passed('setup-rebind-cannot-publish-a-previous-mouse-offer')
    report=dict(passed=True,cases=cases,binary_sha256=sha(OUT/'TERMINAL.EXE'),
        checker_sha256=sha(Path(__file__)),owner_boundary_checker_sha256=sha(ROOT/'standalone/check_mouse_keyboard.py'),
        scope='Linked actual terminal foreground policy with poisoned C BSS, cdecl/far staging frames, parent extent/resize/allocation errors, BIOS fallback and retained-memory boundaries. DOS and driver errors are explicit modeled boundaries; actual TSR/menu/child observations are separate.')
    (OUT/'mouse-policy.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Terminal mouse foreground:',len(cases),'linked cases PASS')


if __name__=='__main__':main()
