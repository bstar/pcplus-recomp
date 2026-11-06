#!/usr/bin/env python3
"""Exercise the actual parent native echo scope and IRQ-backed continuations.

DOS/BIOS/UART hardware are modeled. Chat owner2 and coherent local cursor are
supplied preconditions; frontend busy-key scheduling and main are not accepted.
"""
import argparse,json,struct,sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
import check_transport as transport
from check_chat_timing_parent import Composed
from check_chat_echo_context import FIELDS
from build_path_session import ROOT,sha


class Echo(Composed):
    def __init__(self):
        super().__init__();self.initialize()
        self.put('_redisplay_active',2);self.put('ui_window_rows',25)
        self.uc.mem_write(0x449,b'\x03\x50\x00');self.uc.mem_write(0x462,b'\0');self.uc.mem_write(0x484,b'\x18')
        self.uc.mem_write(self.symbols['screen_line_flags'],bytes(50))
        self.put('csi_terminal_id',4);self.put('screen_viewport_enabled',0);self.put('screen_viewport_offset',0)
        self.context=self.symbols['redisplay_snapshot']+14500
        self.uc.mem_write(self.context-16,b'\xa5'*16+struct.pack('<11H',20,79,79,20,79,3358,1679,0,0,0,0)+b'\x5a'*16)
        self.read_polls=0;self.intervention=None
        # Inject an external request after polling has completed, before the
        # scope checks revocation; do not let modem poll consume the fixture.
        at=self.symbols['line_poll_far']+3
        assert bytes(self.uc.mem_read(at,1))==b'\xcb'
        self.uc.hook_add(UC_HOOK_CODE,self.poll_hook,None,at,at)
    def poll_hook(self,u,at,size,user):
        self.read_polls+=1
        if self.intervention:self.intervention(self)
    def native(self):return tuple(self.get(name) for name in FIELDS[:11])
    def local(self):return struct.unpack('<11H',self.uc.mem_read(self.context,22))
    def echo(self,value,kind=4,delta=0):
        seg,off=self.entries['_terminal_chat_text_echo_sink']
        # Canonical pointer expected by the owned frozen-storage lease.
        ds_seg,ds_off=self.entries['redisplay_snapshot']
        return self.farcall(self.base_segment+seg,off,[kind,value,ds_off+14500+delta,self.base_segment+ds_seg])
    def error(self):
        seg,off=self.entries['terminal_chat_echo_error_far'];return self.farcall(self.base_segment+seg,off,[])
    def restored(self,before,cursor):
        assert self.native()==before and self.cursor==cursor
        assert not self.get('terminal_parser_active') and not self.get('terminal_ansi_wait_active')
        assert bytes(self.uc.mem_read(self.context-16,16))==b'\xa5'*16
        assert bytes(self.uc.mem_read(self.context+22,16))==b'\x5a'*16


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('terminal','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();binary=a.terminal.resolve();out=a.output.resolve()
    assert binary.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build') and not out.exists()
    manifest=json.loads(binary.with_name('manifest.json').read_text());assert manifest['experimental_chat_echo'] and sha(binary)==manifest['binary_sha256']
    transport.BINARY=binary;transport.MAP=binary.with_name('terminal.map')
    cases=[]
    def check(name,fn):fn();cases.append(dict(case=name,passed=True));print('PASS',name,flush=True)
    def plain():
        m=Echo();before=m.native();cursor=m.cursor
        assert m.echo(65)==1 and m.error()==0;m.restored(before,cursor)
        assert m.local()[7]==1 and bytes(m.uc.mem_read(0xb8000+20*160+158,2))==b'A\x07'
        m.call('terminal_receive_input',ax=ord('R'));remote=m.native();cursor=m.cursor
        assert m.echo(66)==1 and m.error()==0;m.restored(remote,cursor)
        assert bytes(m.uc.mem_read(0xb8000+21*160,2))==b'B\x07' and m.local()[:2]==(21,1)
        assert not m.tx and not m.keyboard_calls
    check('plain-echo-deferred-wrap-remote-interleave-and-full-cursor-restore',plain)
    def parser():
        m=Echo();before=m.native();cursor=m.cursor;m.receive_irq(b'[31mQ')
        assert m.echo(27)==1 and m.error()==0;m.restored(before,cursor)
        assert m.get('attributes_current')&7==4 and m.get('uart_rx_count')==1
        assert m.call('uart_receive_byte')==ord('Q')
        assert m.read_polls>=4 and not m.tx
        # C1's initial unread belongs to this local parser, not UART RX undo.
        m=Echo();before=m.native();cursor=m.cursor;m.put('terminal_input_mode_8fe8',1);m.put('terminal_c1_enabled',1)
        m.receive_irq(b'32mZ');assert m.echo(0x9b)==1 and m.error()==0;m.restored(before,cursor)
        assert m.get('attributes_current')&7==2 and m.call('uart_receive_byte')==ord('Z')
    check('actual-CSI-and-C1-initial-unread-use-IRQ-RX-leaving-next-byte-owned-by-main',parser)
    def timeout():
        for advance,want in ((True,1),(False,4)):
            m=Echo();m.advance_ticks=advance;m.put('terminal_ansi_wait_cancel',0x1234);m.put('terminal_ansi_wait_timed_out',0x5678)
            before=m.native();cursor=m.cursor
            result=m.echo(27);error=m.error();assert result==1 and error==want,(advance,result,error,want)
            m.restored(before,cursor)
            assert m.get('terminal_ansi_wait_cancel')==0x1234 and m.get('terminal_ansi_wait_timed_out')==0x5678
            # Poll cancellation/clock once before refusing the exhausted
            # no-progress budget:4096 read attempts plus this final service.
            assert (m.read_polls<=4097 if advance else m.read_polls==4097),(advance,m.read_polls)
            assert m.get('uart_rx_count')==0
            assert m.echo(65)==1 and m.error()==0;m.restored(before,cursor)
    check('whole-scope-tick-and-stopped-clock-budget-return-restore-and-retry',timeout)
    def progressing_clock():
        m=Echo();m.advance_ticks=False;m.set_tick(100);before=m.native();cursor=m.cursor
        # A real advancing clock may permit more than4096 polls within the
        # whole36-tick deadline. The no-progress guard must not shorten it.
        m.intervention=lambda e:e.set_tick(100+e.read_polls//256)
        assert m.echo(27)==1 and m.error()==1,(m.error(),m.read_polls)
        assert m.read_polls>=36*256;m.restored(before,cursor)
    check('progressing-clock-retains-whole-deadline-beyond4096-total-polls',progressing_clock)
    def aborts():
        for field,value,want in (('terminal_ansi_wait_cancel',1,2),('terminal_quit',1,2),('connection_state',7,3)):
            m=Echo();before=m.native();cursor=m.cursor
            m.intervention=lambda e,f=field,v=value:e.put(f,v)
            result=m.echo(27);error=m.error();assert result==1 and error==want,(field,result,error,want)
            m.restored(before,cursor)
            assert m.get('uart_rx_count')==0
    check('explicit-cancel-quit-and-modem-phase-revoke-scope-after-accepted-echo',aborts)
    def nested():
        m=Echo();before=m.native();cursor=m.cursor;m.advance_ticks=False;m.put('terminal_ansi_m_policy',1)
        m.receive_irq(b'[M');assert m.echo(27)==1 and m.error()==4;m.restored(before,cursor)
        # The controller polls before its read and once more before noticing
        # the cancellation latch; parser entry contributes the other edge.
        assert m.read_polls==4098 and not m.get('uart_rx_count')
    check('original-alternate-CSI-M-wait-uses-owned-nonblocking-read-and-cancels-on-budget',nested)
    def admission():
        for field,value in [('_redisplay_active',0),('terminal_aspect_active',1),('terminal_parser_active',1),('terminal_ansi_wait_active',1),('terminal_quit',1),('terminal_deferred_count',33 if manifest.get('experimental_chat_foreground_text') else 1),('terminal_macro_active',1),('terminal_program_pending',1),('screen_viewport_enabled',1),('screen_viewport_offset',1),('connection_state',2)]:
            m=Echo();m.put(field,value);before=m.native();video=bytes(m.uc.mem_read(0xb8000,4000));local=m.local()
            assert m.echo(65)==0 and m.native()==before and m.local()==local and bytes(m.uc.mem_read(0xb8000,4000))==video
        for kind,value,delta in ((1,65,0),(4,256,0),(4,65,2)):
            m=Echo();before=m.native();assert m.echo(value,kind,delta)==0 and m.native()==before
        for at,data in ((0x449,b'\x13'),(0x44a,b'\x84\x00'),(0x462,b'\x01'),(0x484,b'\x31')):
            m=Echo();m.uc.mem_write(at,data);before=m.native();local=m.local()
            video=bytes(m.uc.mem_read(0xb8000,4000))
            assert m.echo(65)==0 and m.native()==before and m.local()==local
            assert bytes(m.uc.mem_read(0xb8000,4000))==video
        m=Echo();m.uc.mem_write(m.symbols['screen_line_flags']+20,b'\x80');before=m.native()
        assert m.echo(65)==0 and m.native()==before
        for offset,value in ((0,25),(2,80),(6,19),(10,1),(14,2),(20,2)):
            m=Echo();m.uc.mem_write(m.context+offset,struct.pack('<H',value));before=m.native()
            assert m.echo(65)==0 and m.native()==before
    check('owner-pointer-byte-geometry-and-cursor-admission-refuse-before-paint',admission)
    if manifest.get('experimental_chat_foreground_text'):
        def retained():
            for count in (1,32):
                m=Echo();m.put('terminal_deferred_count',count)
                before=m.native();cursor=m.cursor
                assert m.echo(65)==1 and m.error()==0;m.restored(before,cursor)
                assert m.get('terminal_deferred_count')==count
        check('foreground-owned-bounded-typeahead-does-not-reject-or-consume-native-echo',retained)
        def legacy_overflow():
            for owner in (0,1):
                m=Echo();m.put('_redisplay_active',owner)
                m.put('terminal_deferred_count',32);m.put('terminal_macro_active',1)
                before=m.native();cursor=m.cursor
                m.call('terminal_defer_key',ax=ord('X'))
                assert (m.get('terminal_deferred_count'),m.get('terminal_macro_active'),
                        m.get('terminal_macro_status'),m.get('terminal_exit_code'),m.get('terminal_quit'))==(0,0,7,3,1)
                m.restored(before,cursor)
        check('non-Chat-full-FIFO-retains-legacy-explicit-stop-without-Chat-bell-policy',legacy_overflow)
    sources=dict(manifest['sources'])
    for mod in tuple(sys.modules.values()):
        q=Path(getattr(mod,'__file__','') or '/').resolve()
        if q.is_relative_to(ROOT/'standalone') and q.suffix=='.py':sources[str(q.relative_to(ROOT))]=sha(q)
    for n,h in sources.items():assert sha(ROOT/n)==h,n
    out.mkdir();(out/'result.json').write_text(json.dumps(dict(passed=True,binary_sha256=sha(binary),cases=cases,sources=sources,
        minimum_allocated_module_bytes=manifest['memory_layout']['minimum_allocated_module_bytes'],
        scope=__doc__+' Actual native parser/renderer, bounded live transport/keyboard polling, IRQ ring, C1 unread and nested original alternate wait run without product-code patches. Explicit cancellation/modem-phase intervention writes model an external request, not BIOS key-dispatch acceptance. Whole-echo36tick deadline and4096attempts without BIOS clock progress are maintained adaptations. Foreground TEXT keys, busy-key guard, ASPECT memory funding, actual DOS/BBS and hardware acceptance are separate gates.'),indent=2)+'\n')


if __name__=='__main__':main()
