#!/usr/bin/env python3
"""Linked optional initialization transactions and atomic /I invocation policy."""
import argparse,json,shutil,struct
from pathlib import Path
import check_transport as transport
from check_connection import Connection
from check_terminal_options import Options
from audit_aspect_transmit_wait import ROOT,sha


def model(raw=b'ATZ^M',seconds=3,**settings):
    m=Connection(**settings);m.put('terminal_modem_init_wait',seconds)
    assert len(raw)<47;m.uc.mem_write(m.symbols['terminal_modem_settings']+18,raw.ljust(47,b'\0'))
    assert m.call('terminal_connection_prepare')==0 and not m.flags()
    return m


def until(m,predicate,count=600):
    for _ in range(count):
        if predicate():return
        m.poll()
    raise AssertionError(('condition not reached',m.state(),bytes(m.tx),m.get('modem_init_phase',1)))


def command(m,expected):
    until(m,lambda:bytes(m.tx)==expected)
    assert m.state()==1 and not m.get('modem_init_reply',1)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--product',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    product=a.product.resolve();transport.BINARY=product/'TERMINAL.EXE';transport.MAP=product/'terminal.map'
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True);rows=[]
    def done(case,**data):rows.append(dict(case=case,passed=True,**data));print(case,'PASS',flush=True)
    o=Options(transport.BINARY,transport.MAP)
    for text,value in [(b'',0),(b'/I:0',0),(b'/i:0003',3),(b'/I:1',1),(b'/I:32767',32767),(b'/I:60 /Z:512',60)]:
        assert o.parse(text)==(0,0) and o.get('terminal_modem_init_wait')==value
    assert o.parse(b'/I:3 /D:CaseTest:23 @KEEP.PRM COM2 HARD /Z:128')==(0,0)
    baseline=(o.snapshot(),o.get('terminal_modem_init_wait'))
    bad=[b'/I:',b'/I:32768',b'/I:65535',b'/I:999999999',b'/I:-1',b'/I:+1',b'/I:1x',b'/I: 1',b'/I:0 /I:0',b'/I:3 /I:4',b'/I:2 /Z:0',b'/I:2 /A:BAD']
    for text in bad:
        assert o.parse(text)==(2,1) and (o.snapshot(),o.get('terminal_modem_init_wait'))==baseline
    assert o.parse(b'')==(0,0) and o.get('terminal_modem_init_wait')==0
    done('CLI-range-duplicate-mask-independence-atomicity-default-reset',inputs=20)
    dial=b'ATDLocal.Example:2323\r'
    for answer in (b'OK\r',b'0\r',b'\r\n ok \r\n'):
        m=model();m.start();command(m,b'ATZ\r');m.receive(answer);assert m.get('modem_init_reply',1)==1
        m.waiting();assert bytes(m.tx)==b'ATZ\r'+dial
        done('early-result-before-final-pacing',answer_hex=answer.hex())
    for answer in (b'ERROR\r',b'4\r',b' error \n'):
        m=model();m.start();command(m,b'ATZ\r');m.receive(answer);m.poll(100)
        assert m.state()==0 and m.get('connection_status')==2 and bytes(m.tx)==b'ATZ\r\x1b'
        done('explicit-initialization-error-no-dial',answer_hex=answer.hex())
    for unknown in (b'ATZ\rBOOK\rOKAY\rERRORS\r',b'O K\r',b'X'*128+b'\r'):
        m=model();m.start();command(m,b'ATZ\r');m.poll(2);m.receive(unknown);assert not m.get('modem_init_reply',1)
        assert m.state()==10 and bytes(m.tx)==b'ATZ\r'
        for byte in b'O K\r':m.receive(bytes([byte]))
        assert not m.get('modem_init_reply',1)
        for byte in b'OK\r\n':m.receive(bytes([byte]))
        m.waiting();assert bytes(m.tx)==b'ATZ\r'+dial
        done('echo-unknown-lines-fragmentation-and-bounded-overflow',unknown_hex=unknown.hex())
    for raw,first,second in [(b'ATZ^MATE0^M',b'ATZ\r',b'ATE0\r'),(b'ATZ^M^JATE0^M^J',b'ATZ\r\n',b'ATE0\r\n')]:
        m=model(raw);m.start();until(m,lambda:bytes(m.tx).startswith(b'ATZ\r'))
        # CRLF's result can precede its optional LF and final pacing poll.
        m.receive(b'OK\r');until(m,lambda:bytes(m.tx)==first+second)
        assert b'ATD' not in bytes(m.tx);m.receive(b'0\r');m.waiting();assert bytes(m.tx)==first+second+dial
        done('multiple-command-ACKs-before-dial-and-CRLF',source_hex=raw.hex())
    m=model(b'ATZ^MATE0^M');m.start();command(m,b'ATZ\r');m.receive(b'OK\r');until(m,lambda:bytes(m.tx)==b'ATZ\rATE0\r');m.receive(b'ERROR\r');m.poll(100)
    assert m.state()==0 and bytes(m.tx)==b'ATZ\rATE0\r\x1b';done('second-command-error-prevents-dial')
    for raw,wire in [(b'',b''),(b'~',b''),(b'AT~Z^M~',b'ATZ\r')]:
        m=model(raw);m.start()
        if wire:command(m,wire);m.receive(b'OK\r')
        m.waiting();assert bytes(m.tx)==wire+dial
        done('empty-and-pause-only-trailer',source_hex=raw.hex())
    for raw in (b'ATZ',b'ATZ^MATE0',b'AT^JZ^M'):
        m=Connection();m.put('terminal_modem_init_wait',3);m.uc.mem_write(m.symbols['terminal_modem_settings']+18,raw+b'\0')
        assert m.call('terminal_connection_prepare')!=0 and m.flags() and not m.tx and not m.controls
        done('incomplete-or-embedded-LF-rejected-before-UART',source_hex=raw.hex())
    for kind in ('CTS','THRE','XOFF'):
        m=model(seconds=1,timeout=1);m.put('uart_software_flow',1)
        if kind=='CTS':m.cts=False
        elif kind=='THRE':m.thre=False
        else:m.receive_irq(b'\x13')
        m.start();m.poll(100);assert m.state()==0 and m.get('connection_status')==3 and b'ATD' not in bytes(m.tx)
        done('bounded-initialization-transmit-stall',blocker=kind)
    m=model(seconds=1);m.start();command(m,b'ATZ\r');m.poll(100)
    assert m.state()==0 and m.get('connection_status')==3 and bytes(m.tx)==b'ATZ\r\x1b';done('strict-silent-response-timeout-no-dial')
    for action in ('Escape','AltX'):
        m=model();m.start();command(m,b'ATZ\r');m.poll(2);assert m.state()==10
        m.keys.append(0x011b if action=='Escape' else 0x2d00);m.poll(100)
        assert m.state()==0 and bool(m.get('terminal_quit'))==(action=='AltX') and b'ATD' not in bytes(m.tx)
        done('response-wait-keyboard-cancellation',action=action)
    for reply in (b'',b'ERROR\r',b'OK\r',b'ERR'):
        m=model();m.start();until(m,lambda:bytes(m.tx)==b'A');m.cts=False;m.call('terminal_connection_cancel',ax=0);m.poll(40);assert m.state()==0
        m.start();m.cts=True;until(m,lambda:bytes(m.tx)==b'A\r')
        if reply:m.receive(reply)
        m.poll(45);assert bytes(m.tx)==b'A\r'
        if reply==b'ERR':m.receive(b'OR\r')
        until(m,lambda:bytes(m.tx)==b'A\rATZ\r');m.receive(b'OK\r');m.waiting();assert bytes(m.tx)==b'A\rATZ\r'+dial
        done('retry-separator-result-drain-before-new-init',reply_hex=reply.hex())
    m=model(b'^MATZ^M');m.start();command(m,b'\r');m.receive(b'ERROR\r');m.poll(45);assert bytes(m.tx)==b'\r'
    until(m,lambda:bytes(m.tx)==b'\rATZ\r');m.receive(b'OK\r');m.waiting();assert bytes(m.tx)==b'\rATZ\r'+dial;done('empty-command-bounded-drain')
    for raw in (b'OK^M',b'ERROR^M',b'0^M',b'4^M'):
        m=model(raw,seconds=1);m.start();expected=raw.replace(b'^M',b'\r');command(m,expected);m.receive(expected);m.poll(100)
        assert m.state()==0 and m.get('connection_status')==3 and b'ATD' not in bytes(m.tx)
        done('short-command-echo-cannot-be-own-result',source_hex=raw.hex())
    m=model(initialize=0);m.start();m.waiting();assert bytes(m.tx)==dial;done('initial-high-carrier-skip-preserved')
    m=model();m.put('terminal_directory_mode',1);m.start();assert m.state()==6 and not m.tx;done('direct-line-preserved')
    m=model(seconds=0);m.start();m.waiting();assert bytes(m.tx)==b'ATZ\r'+dial;done('default-quiet-no-wait-preserved')
    manifest=json.loads((product/'manifest.json').read_text());inputs=dict(manifest['sources'])
    for path in (Path(__file__),ROOT/'standalone/check_connection.py',ROOT/'standalone/check_transport.py',ROOT/'standalone/check_terminal_options.py',ROOT/'standalone/dos_image.py'):inputs[str(path.relative_to(ROOT))]=sha(path)
    for name,digest in inputs.items():
        assert sha(ROOT/name)==digest;dest=out/'inputs'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,dest)
    r=dict(passed=True,cases=rows,parent_sha256=sha(transport.BINARY),inputs=inputs,checker_sha256=sha(Path(__file__)),scope=__doc__+' Actual linked parser/controller/sender/UART IRQ with modeled ports/BIOS ticks. Not actual DOS peer, physical modem or full F03 acceptance.')
    (out/'checks.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(passed=True,cases=len(rows))))


if __name__=='__main__':main()
