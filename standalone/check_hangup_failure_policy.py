#!/usr/bin/env python3
"""Linked failed-hangup recovery, successful hangup and carrier-high startup policy."""
import argparse,json
from pathlib import Path
import check_transport as transport
from check_connection import Connection
from audit_aspect_transmit_wait import ROOT,sha


def hold(m,kind,enabled):
    if kind=='XOFF':m.receive_irq(b'\x13' if enabled else b'\x11');m.poll()
    elif kind=='CTS':m.cts=not enabled
    elif kind=='THRE':m.thre=not enabled


def failed(kind,drop):
    m=Connection(drop=drop);m.put('uart_software_flow',1);m.connect();hold(m,kind,True)
    wire=bytes(m.tx);m.call('terminal_connection_cancel',ax=1);m.poll(100)
    assert m.state()==6 and m.get('connection_status')==8 and bytes(m.tx)==wire
    assert m.get('uart_tx_paused')==int(kind=='XOFF')
    assert m.controls==([10,11] if drop else [])
    m.start();m.poll(3)
    assert m.state()==6 and m.get('connection_status')==8 and bytes(m.tx)==wire
    return m,wire


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--product',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    product=a.product.resolve();transport.BINARY=product/'TERMINAL.EXE';transport.MAP=product/'terminal.map';rows=[]
    for kind in ('XOFF','CTS','THRE'):
      for drop in (0,1):
        for recovery in ('XON-hangup','carrier-loss','exit'):
            m,wire=failed(kind,drop)
            if recovery=='XON-hangup':
                hold(m,kind,False);m.call('terminal_connection_cancel',ax=1);m.poll(100)
                assert m.state()==0 and m.get('connection_status')==5 and bytes(m.tx)==wire+b'+++ATH\r'
                m.start();m.waiting();assert bytes(m.tx)==wire+b'+++ATH\rATZ\rATDLocal.Example:2323\r'
            elif recovery=='carrier-loss':
                m.carrier=False;m.poll();assert m.state()==0 and m.get('connection_status')==6 and not m.get('uart_tx_paused')
                hold(m,kind,False);m.start();m.waiting();assert bytes(m.tx)==wire+b'ATZ\rATDLocal.Example:2323\r'
            else:
                m.call('terminal_connection_exit');m.poll(100)
                assert m.state()==0 and m.get('terminal_quit')==1 and bytes(m.tx)==wire
            rows.append(dict(blocker=kind,drop_DTR=bool(drop),recovery=recovery,passed=True))
    for initialize in (0,1):
        m=Connection(initialize=initialize);m.start();m.waiting()
        assert bytes(m.tx)==(b'ATZ\r' if initialize else b'')+b'ATDLocal.Example:2323\r'
        rows.append(dict(case='initial-carrier-high',initialize=initialize,passed=True))
    for drop in (0,1):
        m=Connection(drop=drop);m.connect();wire=bytes(m.tx);m.call('terminal_connection_cancel',ax=1);m.poll(100)
        assert m.state()==0 and m.get('connection_status')==5
        m.start();m.waiting();assert bytes(m.tx)==wire+b'+++ATH\rATZ\rATDLocal.Example:2323\r'
        rows.append(dict(case='successful-always-high-carrier-hangup',drop_DTR=bool(drop),passed=True))
    m=Connection();m.put('terminal_directory_mode',1);m.start();assert m.state()==6
    m.call('terminal_connection_cancel',ax=1);assert m.state()==0 and m.get('connection_status')==5
    rows.append(dict(case='direct-line-unchanged',passed=True))
    result=dict(passed=True,parent_sha256=sha(transport.BINARY),checker_sha256=sha(Path(__file__)),cases=rows,scope=__doc__+' Actual linked controller/sender/UART IRQ with hardware registers and BIOS ticks modeled. Not actual DOS peer or physical modem acceptance.')
    assert not a.output.exists();a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,cases=len(rows))))


if __name__=='__main__':main()
