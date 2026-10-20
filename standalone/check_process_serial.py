#!/usr/bin/env python3
"""Linked UART handoff; only DOS vectors, UART/PIC and BIOS clock are modeled."""
import itertools,json,struct
from pathlib import Path
import check_aspect_serial as serial
import check_uart as uart
from build_process_serial import ROOT,OUT,sha
from unicorn.x86_const import UC_X86_REG_EFLAGS
uart.BINARY=OUT/'PSERIAL.EXE';uart.MAP=OUT/'process_serial.map'
BASELINE=['uart_saved_pic','uart_saved_lcr','uart_saved_mcr','uart_saved_ier',
          'uart_saved_dll','uart_saved_dlm','uart_previous_irq_offset','uart_previous_irq_segment']


class Owner(serial.Serial):
    def __init__(self):
        self.fifo=False;super().__init__();self.registers[0x21]&=~1
        self.initial=(dict(self.registers),list(self.divisor),dict(self.vectors))
    def _input(self,u,p,s,data):
        value=super()._input(u,p,s,data)
        if p==self.port_base+2 and self.fifo:value|=0xc0
        if p==self.port_base+5:self.registers[0x3fd]&=~2 #LSR read acknowledges OE.
        return value
    def _output(self,u,p,s,value,data):
        if p==self.port_base+2:self.fifo=bool(value&1)
        return super()._output(u,p,s,value,data)
    def saved(self):return {n:self.get(n,1 if n.startswith('uart_saved_') else 2) for n in BASELINE}
    def ring(self):
        return (self.get('uart_rx_read'),self.get('uart_rx_write'),self.get('uart_rx_count'),
                bytes(self.uc.mem_read(self.symbols['uart_rx_buffer'],4096)),
                self.get('serial_unread_valid'),self.get('serial_unread_slot'))
    def child(self,overrun=False,dtr=True,fifo=False,stall=False):
        self.registers[0x3fb]=0x9e;self.divisor=[0x34,0x12]
        self.registers[0x3f9]=0;self.registers[0x3fc]=int(dtr)
        self.registers[0x21]^=0x20
        self.vectors[self.get('serial_vector')]=(0x5555,0x7777)
        self.registers[0x3fd]=(0x20 if stall else 0x60)|(2 if overrun else 0)
        self.fifo=fifo


def main():
    cases=[]
    for port,flow in itertools.product(range(1,5),'NSHB'):
        m=Owner();assert m.open(f'/S{port}:0003:03:{flow}'.encode())==0
        m.call('_aspect_serial_poll');m.tx.clear();m.receive_irq(b'ABC')
        assert m.call('_aspect_serial_read')==65;ring=m.ring();saved=m.saved();ours=m.vectors[m.get('serial_vector')]
        assert m.call('_aspect_process_serial_pause')==0
        assert m.get('_aspect_serial_active')==2 and m.get('_aspect_process_serial_detached')==1
        assert m.ring()==ring and m.saved()==saved
        assert m.vectors[m.get('serial_vector')]!=ours and m.registers[0x3f9]==0
        before=len(m.physical_writes)
        for name,args,result in [('_aspect_serial_read',[],65535),('_aspect_serial_unread',[],2),
            ('_aspect_serial_available',[],0),('_aspect_serial_carrier',[],65535),
            ('_aspect_serial_poll',[],2),('_aspect_serial_close',[],2),
            ('_aspect_serial_compile_resume',[],2),('_aspect_serial_try_write',[88],2),
            ('_aspect_process_serial_pause',[],2)]:assert m.call(name,args)==result,name
        assert m.ring()==ring and len(m.physical_writes)==before
        m.child();m.rx.append(0xa5);others=m.registers[0x21]&~(16 if port in (1,3) else 8)
        assert m.call('_aspect_process_serial_resume')==0
        assert m.saved()==saved and m.ring()==ring and list(m.rx)==[0xa5]
        assert m.vectors[m.get('serial_vector')]==ours and m.registers[0x21]==others
        assert (m.registers[0x3fb],m.registers[0x3fc],m.registers[0x3f9],m.divisor)==(3,11,1,[3,0])
        assert m.call('_aspect_process_serial_resume')==0
        m.receive_irq(b'');assert m.call('_aspect_serial_unread')==0
        assert bytes(m.call('_aspect_serial_read') for _ in range(4))==b'ABC\xa5'
        assert m.tx==([0x13,0x11] if flow in 'SB' else [])
        assert m.call('_aspect_serial_close')==0;m.restored()
        cases.append(dict(case='port-flow',port=port,flow=flow,passed=True))
    for flow,count in itertools.product('SHB',(128,3072,4096)):
        m=Owner();assert m.open(f'/S1:0003:03:{flow}'.encode())==0;m.call('_aspect_serial_poll')
        m.receive_irq(b'A'*count);ring=m.ring()
        assert m.call('_aspect_process_serial_pause')==0;m.child()
        assert m.call('_aspect_process_serial_resume')==0 and m.ring()==ring
        if count>=3072:
            assert (m.get('uart_xoff_sent',1),m.get('uart_rts_lowered',1))==(int(flow in 'SB'),int(flow in 'HB'))
        for _ in range(count):assert m.call('_aspect_serial_read')==65
        m.call('_aspect_serial_poll');assert m.registers[0x3fc]&2
        assert m.call('_aspect_serial_close')==0;m.restored()
        cases.append(dict(case='ring-pressure',flow=flow,count=count,passed=True))
    for case,child,status in [('overrun',dict(overrun=True),5),('DTR-drop',dict(dtr=False),8),
            ('FIFO-change',dict(fifo=True),8),('TEMT-timeout',dict(stall=True),7),
            ('combined-fault',dict(overrun=True,dtr=False,stall=True),5)]:
        m=Owner();assert m.open(b'/S1:0003:03:B')==0;m.call('_aspect_serial_poll')
        assert m.call('_aspect_process_serial_pause')==0;m.child(**child);before=m.tick
        assert m.call('_aspect_process_serial_resume')==status,case
        assert not m.get('_aspect_process_serial_detached') and m.get('_aspect_serial_active')==1
        assert m.tick-before<=38 and not m.fifo and m.divisor==[3,0]
        if child.get('stall'):assert m.tick-before>=36
        if child.get('overrun'):assert m.get('uart_rx_dropped')==1
        assert m.call('_aspect_serial_close')==status;m.restored()
        cases.append(dict(case=case,status=status,passed=True))
    m=Owner();assert m.open()==0;before=len(m.physical_writes)
    assert m.call('_aspect_process_serial_pause',eflags=2)==4 and len(m.physical_writes)==before
    assert m.call('_aspect_process_serial_pause')==0;m.child();before=len(m.physical_writes)
    assert m.call('_aspect_process_serial_resume',eflags=2)==4 and len(m.physical_writes)==before
    assert m.get('_aspect_process_serial_detached') and m.call('_aspect_process_serial_resume')==0
    assert m.call('_aspect_serial_close')==0;m.restored();cases.append(dict(case='IF0-reject-retry',passed=True))
    m=Owner();assert m.call('_aspect_process_serial_pause')==m.call('_aspect_process_serial_resume')==0
    assert not m.physical_writes;cases.append(dict(case='closed-idempotence',passed=True))
    m=Owner();assert m.open(b'/S1:0003:03:B')==0;assert m.call('_aspect_serial_compile_pause')==0
    assert m.call('_aspect_process_serial_pause')==2 and m.call('_aspect_process_serial_resume')==0
    assert m.get('serial_compile_held')==1;assert m.call('_aspect_serial_compile_resume')==0
    assert m.call('_aspect_serial_close')==0;m.restored();cases.append(dict(case='foreign-flow-token',passed=True))
    m=Owner();assert m.open()==0;m.registers[0x21]|=1;before=len(m.physical_writes)
    assert m.call('_aspect_process_serial_pause')==4 and len(m.physical_writes)==before
    m.registers[0x21]&=~1;assert m.call('_aspect_process_serial_pause')==0;m.child(stall=True);m.registers[0x21]|=1
    before=m.tick;assert m.call('_aspect_process_serial_resume')==4 and m.tick==before
    assert not m.get('_aspect_process_serial_detached') and m.get('_aspect_serial_active')==1
    assert m.registers[0x21]&1 and m.divisor==[3,0]
    m.registers[0x21]&=~1;assert m.call('_aspect_serial_close')==4;m.restored()
    cases.append(dict(case='masked-IRQ0-bounded-restore',passed=True))
    for count,start in ((0,0),(9,4090),(4096,7)):
        m=Owner();m.parent_psp=0x8800
        m.uc.mem_write(m.child_psp*16+0x16,struct.pack('<H',m.parent_psp))
        m.uc.mem_write((m.parent_psp-1)*16,b'M'+struct.pack('<HH',m.parent_psp,0x1000))
        guard=m.parent_psp^0x9000^0x1000^0xa510^count^start
        desc=struct.pack('<I18H',0x4f495341,3,40,m.parent_psp,0x9000,0x1000,4096,count,start,guard,0,0,0,0,0,0,0,0,0)
        raw=bytes(i&255 for i in range(4096));m.uc.mem_write(0x90100,desc);m.uc.mem_write(0x91000,raw)
        assert m.open(b'/S1:0003:03:B:9000:0100')==0;m.call('_aspect_serial_poll');ring=m.ring()
        assert m.call('_aspect_process_serial_pause')==0
        # Returned flag is word at descriptor22; close while away must not publish.
        assert m.call('_aspect_serial_close')==2 and bytes(m.uc.mem_read(0x90116,2))==b'\0\0'
        m.child();assert m.call('_aspect_process_serial_resume')==0 and m.ring()==ring
        assert m.call('_aspect_serial_close')==0;m.restored()
        values=struct.unpack('<I18H',m.uc.mem_read(0x90100,40))
        assert values[7]==count and values[8]==0 and values[10]==1
        expected=bytes(raw[(start+i)&4095] for i in range(count))
        assert bytes(m.uc.mem_read(0x91000,count))==expected
        cases.append(dict(case='ASIO3-nested-owner-handback',count=count,start=start,passed=True))
    m=Owner();assert m.open()==0;m.fifo=True
    assert m.call('_aspect_process_serial_pause')==8 and not m.get('_aspect_process_serial_detached') and m.fifo
    m.fifo=False;assert m.call('_aspect_serial_close')==0;m.restored();cases.append(dict(case='preexisting-FIFO-admission',passed=True))
    m=Owner();assert m.open()==0;ours=m.vectors[12];m.vectors[12]=(0x6666,0x9999)
    assert m.call('_aspect_process_serial_pause')==4 and m.vectors[12]==(0x6666,0x9999)
    m.vectors[12]=ours;assert m.call('_aspect_serial_close')==0;m.restored();cases.append(dict(case='foreign-vector-admission',passed=True))
    m=Owner();assert m.open()==0;assert m.call('_aspect_serial_break_reserve')==0
    assert m.call('_aspect_process_serial_pause')==2 and m.get('serial_break_state')==1
    assert m.call('_aspect_serial_break_release')==0;assert m.call('_aspect_serial_close')==0;m.restored();cases.append(dict(case='foreign-BREAK-owner',passed=True))
    m=Owner();assert m.open()==0;m.registers[0x3fd]=0x20;before=m.tick
    assert m.call('_aspect_process_serial_pause')==7 and m.tick-before<=40
    assert not m.get('_aspect_process_serial_detached') and m.get('_aspect_serial_active')==1
    m.registers[0x3fd]=0x60;assert m.call('_aspect_serial_close')==0;m.restored();cases.append(dict(case='pause-TEMT-timeout',passed=True))
    report=dict(passed=True,cases=cases,case_count=len(cases),binary_sha256=sha(OUT/'PSERIAL.EXE'),
        checker_sha256=sha(Path(__file__)),reused_checkers={str(p.relative_to(ROOT)):sha(p) for p in (Path(serial.__file__),Path(uart.__file__))},
        scope='Real linked process/serial owner, native UART ISR/vector functions and bounded serial C API. UART/PIC/clock/DOS vector boundaries modeled; no child process or physical modem in this proof.')
    (OUT/'cpu.json').write_text(json.dumps(report,indent=2)+'\n');print('Process UART owner:',len(cases),'linked cases PASS')


if __name__=='__main__':main()
