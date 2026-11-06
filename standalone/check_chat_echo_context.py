#!/usr/bin/env python3
"""Chat-style cursor assignment versus repaired0610 rendering; optional genuine resident comparison."""
import argparse,json,struct,subprocess,sys
from pathlib import Path
from unicorn import UC_HOOK_INTR
from unicorn.x86_const import *
from dos_image import DosImage
from check_input_dispatch import Input
from compare_input_dispatch_original import OriginalInput
from compare_render_original import EXPECTED
from build_path_session import ROOT,sha


class Source(Input):
    def __init__(self,binary):
        DosImage.__init__(self,binary,binary.with_name('input_dispatch.map'))
        self.positions=[];self.calls=[];self.video=0xb8000
        self.uc.mem_write(self.video,b'\xa5'*4000);self.uc.hook_add(UC_HOOK_INTR,self.interrupt)
        self.call('csi_clear_tabs',(1,))


def bios_cursor(c,row,column,original=False):
    u=c.uc;segment=0x1000 if original else c.code_segment
    ds=c.data_base//16 if original else c.ds;ret=0xf000 if original else c.return_offset
    entry=c.base+0x6e66 if original else c.symbols['screen_cursor_pack']
    sp=0xe000-6;u.mem_write(ds*16+sp,struct.pack('<3H',ret,column,row))
    for reg,value in [(UC_X86_REG_CS,segment),(UC_X86_REG_DS,ds),(UC_X86_REG_SS,ds),
        (UC_X86_REG_SP,sp),(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678),(UC_X86_REG_EFLAGS,0x202)]:u.reg_write(reg,value)
    c.returned=False;u.emu_start(entry,0,count=100000)
    assert c.returned and u.reg_read(UC_X86_REG_SP)==sp+6


FIELDS=['screen_cursor_row','screen_cursor_column','screen_visible_column',
        'screen_previous_row','screen_previous_column','screen_video_offset',
        'screen_attribute_offset','csi_wrap_pending','render_deferred_row',
        'render_deferred_column','scroll_suppress_next_linefeed',
        'terminal_history_pending','terminal_history_wrapped']


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('input','output'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--original',action='store_true',help='Analyst-only unmodified original resident instruction comparison')
    a=p.parse_args();binary=a.input.resolve();out=a.output.resolve()
    assert binary.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build') and not out.exists()
    manifest=json.loads(binary.with_name('manifest.json').read_text());assert sha(binary)==manifest['binary_sha256']
    out.mkdir();chat=out/'chat.bin'
    subprocess.run(['nasm','-fbin','-DRECON_FLAT','-I'+str(ROOT/'reconstruction/uart')+'/',str(ROOT/'reconstruction/chat/chat.asm'),'-o',str(chat)],check=True)
    chat_proof=json.loads((ROOT/'reconstruction/chat/provenance.json').read_text())
    assert sha(chat)==chat_proof['sha256'] and chat.stat().st_size==chat_proof['bytes']
    sources=dict(manifest['sources']);image=None
    if a.original:
        path=ROOT/'analysis/pcplus-originals/PCPLUS-main-2.01.EXE';assert sha(path)==EXPECTED;image=path.read_bytes()
        at=chat_proof['source_file_offset'];assert image[at:at+chat_proof['bytes']]==chat.read_bytes()
    cases=[];operations=0;misplaced=0
    streams=[b'AB',b'A\tB\r\nC\x08D\0\x7f\x80\xff',b'A'*81+b'B']
    for profile in (4,6):
        for old in ((0,0),(2,7),(18,79),(24,79)):
            for target in ((20,0),(21,10),(23,79)):
                for repair in (False,True):
                    for data in streams:
                        s=Source(binary);s.put('csi_terminal_id',profile);s.position(*old)
                        native=OriginalInput(image,s) if image is not None else None
                        if native:native.position(*old)
                        for c in (s,native):
                            if c is None:continue
                            # Exact logical-coordinate writes from native Chat's
                            # pre-key path, followed by its BIOS-only6E66 call.
                            c.put('screen_cursor_row',target[0]);c.put('screen_cursor_column',target[1])
                            bios_cursor(c,*target,original=c is native)
                            if repair:c.position(*target)
                        for index,value in enumerate(data):
                            s.call('terminal_receive_character',(value,))
                            if native:
                                native.character(value)
                                assert bytes(s.uc.mem_read(s.video,4000))==bytes(native.uc.mem_read(native.video,4000)),(profile,old,target,repair,index,'frame')
                                for field in FIELDS:
                                    width=1 if field=='terminal_history_pending' else 2
                                    assert s.get(field,width)==native.get(field,width),(field,s.get(field,width),native.get(field,width))
                                assert s.history()==native.history() and s.positions==native.positions and s.calls==native.calls
                            if index==0:
                                at=s.video+(target[0]*80+target[1])*2
                                if repair:assert bytes(s.uc.mem_read(at,2))==b'A\x07'
                                else:
                                    prior=s.video+(old[0]*80+old[1])*2
                                    assert bytes(s.uc.mem_read(prior,2))==b'A\x07' and bytes(s.uc.mem_read(at,2))!=b'A\x07'
                                    misplaced+=1
                            if repair:
                                row,col=s.get('screen_cursor_row'),s.get('screen_cursor_column')
                                assert s.get('screen_video_offset')==(row*80+col)*2
                                assert s.get('screen_attribute_offset')==row*80+col
                            operations+=1
                        cases.append(dict(profile=profile,prior=list(old),target=list(target),repair=repair,bytes=len(data),passed=True))
    # Moving a cursor back is not a full echo-context restore: native deferred
    # wrap state survives. The next integration must explicitly own it too.
    s=Source(binary);s.position(20,79);s.call('terminal_receive_character',(65,))
    assert s.get('csi_wrap_pending')==1;s.position(2,7);assert s.get('csi_wrap_pending')==1
    for mod in tuple(sys.modules.values()):
        q=Path(getattr(mod,'__file__','') or '/').resolve()
        if q.is_relative_to(ROOT/'standalone') and q.suffix=='.py':sources[str(q.relative_to(ROOT))]=sha(q)
    for group in ('render','screen','text','erase','scroll','input_dispatch'):
        name='reconstruction/'+group+'/provenance.json';sources[name]=sha(ROOT/name)
    for name in ('reconstruction/chat/chat.asm','reconstruction/chat/provenance.json'):
        sources[name]=sha(ROOT/name)
    for n,h in sources.items():assert sha(ROOT/n)==h,n
    (out/'result.json').write_text(json.dumps(dict(passed=True,binary_sha256=sha(binary),original_sha256=EXPECTED if image else None,
        Chat_controller_bytes=chat_proof['bytes'],Chat_controller_original_bytes_matched=image is not None,Chat_controller_executed=False,
        original_resident_executed=image is not None,cases=cases,character_operations=operations,misplaced_first_echo_cases=misplaced,
        cursor_restore_alone_clears_deferred_wrap=False,sources=sources,
        scope=__doc__+' Real source-linked0610/control/render/cursor/history with BIOS model; logical Chat pre-key writes and BIOS cursor calls are applied explicitly, not full Chat controller execution. Optional unmodified original resident instructions match full4000-byte frame, cursor/cache/deferred/history fields, history bytes and BIOS calls per byte. Repair is an intentional coherent-cursor adaptation, not claimed original Chat behavior. ESC/overlay emulations, original full Chat entry/exit and parent echo/foreground integration remain unverified.'),indent=2)+'\n')
    print('PASS',len(cases),'cursor/echo vectors;',operations,'characters;',misplaced,'raw first-echo misplacements; genuine comparison',image is not None)


if __name__=='__main__':main()
