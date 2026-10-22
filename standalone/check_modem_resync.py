#!/usr/bin/env python3
"""Execute linked retry synchronization through actual controller/sender/UART instructions."""
import argparse, json, struct
from pathlib import Path
import check_transport as transport
from check_connection import Connection
from audit_aspect_transmit_wait import ROOT, sha


def block(m,kind,held):
    if kind=='CTS': m.cts=not held
    elif kind=='THRE': m.thre=not held
    else:
        m.put('uart_software_flow',1)
        m.receive_irq(b'\x13' if held else b'\x11'); m.poll()


def cancel(m,kind):
    block(m,kind,True); m.call('terminal_connection_cancel',ax=0); m.poll(40)
    assert m.state()==0 and m.get('connection_status')==4


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--product',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    product=a.product.resolve(); transport.BINARY=product/'TERMINAL.EXE';transport.MAP=product/'terminal.map'
    assert not a.output.exists(); rows=[]
    for kind in ('CTS','THRE','XOFF'):
        for initialize in (0,1):
            for repeat in (False,True):
                m=Connection(initialize=initialize);m.carrier=False;m.start();m.poll()
                assert bytes(m.tx)==b'A';cancel(m,kind); before=bytes(m.tx)
                assert before==b'A'
                m.start();block(m,kind,True);m.poll(5);assert bytes(m.tx)==before
                if repeat:
                    cancel(m,kind);m.start();block(m,kind,True);m.poll(5);assert bytes(m.tx)==before
                block(m,kind,False)
                for _ in range(300):
                    n=len(m.tx);m.poll();assert len(m.tx)-n<=1
                    if m.state()==5:break
                assert m.state()==5 and bytes(m.tx)==b'A\rATZ\rATDLocal.Example:2323\r'
                rows.append(dict(case='blocked-prefix',blocker=kind,initialize=initialize,repeat_cancel=repeat,passed=True))
    for raw,expanded,pause in ((b'AT&F^M',b'AT&F\r',ord('~')),(b'',b'',ord('~')),(b'ATZ^M',b'ATZ\r',13),(b'AT~Z^M',b'ATZ\r',ord('~'))):
        m=Connection();m.carrier=False;m.start();m.poll();cancel(m,'CTS');m.cts=True
        m.uc.mem_write(m.symbols['terminal_modem_settings']+18,raw+b'\0')
        m.uc.mem_write(m.symbols['terminal_modem_settings']+14,struct.pack('<H',pause))
        assert m.call('terminal_connection_prepare')==0
        before=bytes(m.tx);m.start();m.waiting()
        # Configured CR-as-pause suppresses its own expanded terminator; the
        # synchronization separator remains a physical CR, independently paced.
        if pause==13:expanded=b'ATZ'
        assert bytes(m.tx)==before+b'\r'+expanded+b'ATDLocal.Example:2323'+(b'' if pause==13 else b'\r')
        rows.append(dict(case='configured-initialization',source_hex=raw.hex(),pause=pause,passed=True))
    m=Connection(initialize=0);m.carrier=False;m.start();m.poll();cancel(m,'CTS');m.cts=True
    before=bytes(m.tx);m.carrier=True;m.start();m.waiting()
    assert bytes(m.tx)==before+b'ATDLocal.Example:2323\r'
    rows.append(dict(case='skip-initialization-when-carrier-high',passed=True))
    r=dict(passed=True,cases=rows,parent_sha256=sha(transport.BINARY),checker_sha256=sha(Path(__file__)),scope=__doc__+' Modeled CTS/THRE/BIOS clock; real linked IRQ/XOFF and cancellation/retry. No physical or whole-application acceptance.')
    a.output.write_text(json.dumps(r,indent=2)+'\n'); print(json.dumps(dict(passed=True,cases=len(rows))))


if __name__=='__main__':main()
