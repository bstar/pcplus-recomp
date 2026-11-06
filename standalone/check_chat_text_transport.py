#!/usr/bin/env python3
"""Execute the linked parent TEXT TX sink, UART/IRQ, queue and real recorder.

Only BIOS/DOS filesystem/UART hardware boundaries are modeled. Parent main,
module scheduling, echo/delay services and physical hardware are not accepted.
"""
import argparse,json,re,struct,sys
from pathlib import Path
from unicorn.x86_const import *
import check_transport as transport
from check_recording_foreground_live import Recorder
from build_path_session import ROOT,sha


class TextTransport(Recorder):
    def receive_irq(self,data):
        # This recorder harness already injects enabled IRQs at instruction
        # boundaries. Do not also explicitly call its ISR (a second empty read).
        assert not self.rx
        self.rx.extend(data);self.call('uart_poll_flow');assert not self.rx

    def sink(self,kind=1,value=65):
        name='_terminal_chat_text_tx_sink';segment,offset=self.entries[name]
        words=[self.return_offset,self.code_segment,kind,value,0,0]
        sp=self.offset('terminal_stack_top')-len(words)*2
        self.uc.mem_write(self.data_base+sp,struct.pack('<6H',*words))
        guards=((UC_X86_REG_DS,self.ds),(UC_X86_REG_SS,self.ds),
                (UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),
                (UC_X86_REG_DI,0x5678),(UC_X86_REG_ES,0xb800))
        for register,value in (*guards,(UC_X86_REG_CS,self.base_segment+segment),
                               (UC_X86_REG_SP,sp),(UC_X86_REG_EFLAGS,0x202)):
            self.uc.reg_write(register,value)
        self.returned=False;self.uc.emu_start(self.symbols[name],0,count=300000)
        assert self.returned and self.uc.reg_read(UC_X86_REG_SP)==sp+4
        for register,value in guards:assert self.uc.reg_read(register)==value,(name,register)
        return self.uc.reg_read(UC_X86_REG_AX)

    def grant(self):
        self.call('terminal_poll_serial')
        assert self.get('terminal_macro_tx_allowed')==1

    def snapshot(self):
        names=('terminal_tx_count','terminal_tx_head','terminal_tx_tail',
               'terminal_macro_tx_allowed','terminal_macro_tx_epoch','terminal_quit')
        return ([self.get(n) for n in names],self.state(),
                bytes(self.uc.mem_read(self.symbols['terminal_tx_origin_bits'],128)),
                bytes(self.uc.mem_read(self.symbols['terminal_tx_buffer'],1024)),
                bytes(self.tx),{k:bytes(v) for k,v in self.files.items()},self.keyboard_calls)

    def refuses(self,kind=1,value=65):
        before=self.snapshot();assert self.sink(kind,value)==0
        assert self.snapshot()==before


def ready():
    m=TextTransport();m.initialize();assert m.begin_recording()==0
    # Sink's explicit lease precondition; this is not Chat entry acceptance.
    m.put('_redisplay_active',2)
    return m


def recorded(m):
    assert m.far('stop')==0
    return b''.join(bytes.fromhex(x.decode()) for x in re.findall(
        rb'^transmitraw "([0-9A-F]*)"\r?$',bytes(m.files['PCPLUS.ASP']),re.M))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--terminal',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();binary=a.terminal.resolve();out=a.output.resolve()
    assert binary.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build') and not out.exists()
    manifest=json.loads(binary.with_name('manifest.json').read_text())
    assert manifest['experimental_chat_text_transport'] and sha(binary)==manifest['binary_sha256']
    transport.BINARY=binary;transport.MAP=binary.with_name('terminal.map')
    sources=dict(manifest['sources'])
    for module in tuple(sys.modules.values()):
        path=Path(getattr(module,'__file__','') or '/').resolve()
        if path.is_relative_to(ROOT/'standalone') and path.suffix=='.py':sources[str(path.relative_to(ROOT))]=sha(path)
    for name,digest in sources.items():assert sha(ROOT/name)==digest,name
    cases=[]
    def check(name,fn):
        fn();cases.append(dict(case=name,passed=True));print(name,'PASS',flush=True)

    def octets():
        m=ready();m.put('terminal_macro_tx_epoch',65535)
        for value in range(256):
            m.grant();epoch=m.get('terminal_macro_tx_epoch')
            assert m.sink(value=value)==1 and m.tx[-1]==value
            assert m.get('terminal_macro_tx_epoch')==(epoch+1)&65535
            assert not m.get('terminal_macro_tx_allowed') and not m.get('terminal_tx_count')
            m.refuses(value=value^255)
        assert bytes(m.tx)==recorded(m)==bytes(range(256))
    check('all-octets-physical-completion-once-per-grant-epoch-wrap-and-recording',octets)

    def connected():
        m=ready();m.put('connection_state',6);m.grant()
        assert m.sink(value=90)==1 and bytes(m.tx)==recorded(m)==b'Z'
    check('connected-state-physical-grant-and-completion',connected)

    def denied():
        m=ready();m.grant()
        for kind in (0,2,3,4,5,6,65535):m.refuses(kind=kind)
        for value in (256,257,65535):m.refuses(value=value)
        for name,values in (('_redisplay_active',(0,1,3)),('terminal_quit',(1,)),
            ('terminal_aspect_active',(1,)),('terminal_macro_active',(1,)),
            ('terminal_tx_count',(1,1024)),('terminal_macro_tx_allowed',(0,2)),
            ('connection_state',(1,2,3,4,5,7,8,9,65535))):
            old=m.get(name)
            for value in values:m.put(name,value);m.refuses()
            m.put(name,old)
        assert not m.tx and recorded(m)==b''
    check('lease-child-quit-modem-queue-macro-grant-kind-and-range-refuse-atomically',denied)

    def stalls():
        for reason in ('thre','cts','xoff','break'):
            m=ready();m.grant()
            if reason=='thre':m.thre=False
            elif reason=='cts':m.put('uart_hardware_flow',1);m.cts=False
            elif reason=='xoff':m.put('uart_software_flow',1);m.receive_irq(b'\x13')
            else:m.put('uart_break_hold',1)
            for _ in range(4):m.refuses()
            if reason=='thre':m.thre=True
            elif reason=='cts':m.cts=True
            elif reason=='xoff':m.receive_irq(b'\x11')
            else:m.put('uart_break_hold',0)
            assert m.sink()==1 and bytes(m.tx)==b'A' and recorded(m)==b'A'
    check('actual-UART-THRE-CTS-XOFF-and-break-hold-no-early-acceptance',stalls)

    def queues():
        m=ready();m.grant();m.enqueue(b'REPLY')
        # A reply may be queued after a grant: both the count and grant matter.
        m.refuses(value=84)
        for _ in b'REPLY':
            m.call('terminal_poll_serial');m.refuses(value=84)
        assert bytes(m.tx)==b'REPLY'
        m.grant();assert m.sink(value=84)==1
        assert bytes(m.tx)==b'REPLYT' and recorded(m)==b'T'
        m=ready();m.record(0,b'M');assert m.start()==0
        m.call('terminal_poll_serial');m.refuses(value=84)
        assert bytes(m.tx)==b'M' and m.get('terminal_macro_active')
        m.grant();assert not m.get('terminal_macro_active') and m.sink(value=84)==1
        assert bytes(m.tx)==recorded(m)==b'MT'
    check('ordinary-report-queue-and-native-macro-priority-no-double-user-write',queues)

    def receive():
        m=ready();m.grant();m.receive_irq(b'\0\x80\xff')
        before=m.get('uart_rx_count');assert before==3
        keys=m.keyboard_calls
        assert m.sink()==1 and m.get('uart_rx_count')==before and m.keyboard_calls==keys
        assert [m.call('uart_receive_byte') for _ in range(3)]==[0,128,255]
        assert recorded(m)==b'A'
    check('direct-TX-does-not-consume-binary-RX-or-keyboard',receive)

    for name,digest in sources.items():assert sha(ROOT/name)==digest,name
    assert sha(binary)==manifest['binary_sha256']
    out.mkdir();(out/'result.json').write_text(json.dumps(dict(passed=True,cases=cases,
        binary_sha256=sha(binary),sources=sources,memory_layout=manifest['memory_layout'],
        scope=__doc__+' Actual source-built optional parent sink and native UART instructions run without patched product code. All256 bytes, single-use grant/epoch wrap, exact recorder output, atomic refusal, queued reply/native macro priority, RX preservation and register/stack ABI verified. Common owner2 is supplied as a precondition, not entered by main. Native TEXT owner/module composition, echo/delay, main-loop scheduling, BBS and physical acceptance remain separate gates.'),indent=2)+'\n')


if __name__=='__main__':main()
