#!/usr/bin/env python3
"""Reactive receive-pressure peer against linked IRQ/ring/flow instructions."""
import argparse,hashlib,json,shutil
from pathlib import Path
import check_transport as transport
from check_connection import Connection
from audit_aspect_transmit_wait import ROOT,sha


def stream(soft,length):
    alphabet=bytes(v for v in range(256) if not soft or v not in (17,19))
    return (alphabet*((length+len(alphabet)-1)//len(alphabet)))[:length]


def pressure(soft,hard,late,thre_stall):
    m=Connection();m.connect();m.put('uart_software_flow',soft);m.put('uart_hardware_flow',hard)
    # Reset host observations only; no product ring, flow or controller repairs.
    m.tx.clear();m.controls.clear();m.cts=False if hard else True
    payload=stream(soft,65536);sent=0;received=bytearray();paused=False;pause_count=0;resume_count=0;peak=0;wire_at=0;late_sent=False;stall=0;stall_done=False;steps=0
    marks=[]
    while sent<len(payload) or m.get('uart_rx_count'):
        steps+=1;assert steps<10000
        if not paused and sent<len(payload):
            block=payload[sent:sent+128];m.receive_irq(block);sent+=len(block)
        elif paused and late and not late_sent and sent<len(payload):
            block=payload[sent:sent+512];m.receive_irq(block);sent+=len(block);late_sent=True
        peak=max(peak,m.get('uart_rx_count'));assert peak<=4096 and m.get('uart_rx_dropped')==0
        pending=m.get('uart_flow_pending',1)
        if thre_stall and soft and pending==19 and not stall_done:stall=3;stall_done=True
        m.thre=not stall
        m.call('uart_poll_flow')
        if stall:stall-=1
        hints=bytes(m.tx[wire_at:]);wire_at=len(m.tx)
        if soft:
            for value in hints:
                assert value in (17,19)
                if value==19:
                    assert not paused;paused=True;pause_count+=1;late_sent=False
                    marks.append(dict(event='XOFF',queued=m.get('uart_rx_count'),sent=sent,received=len(received)))
                else:
                    assert paused;paused=False;resume_count+=1
                    marks.append(dict(event='XON',queued=m.get('uart_rx_count'),sent=sent,received=len(received)))
        else:
            assert not hints
            now=not bool(m.mcr&2)
            if now!=paused:
                paused=now
                if paused:pause_count+=1;late_sent=False
                else:resume_count+=1
                marks.append(dict(event='RTS-low' if paused else 'RTS-high',queued=m.get('uart_rx_count'),sent=sent,received=len(received)))
        # The deliberately slow foreground lets the IRQ queue reach high water;
        # after the peer pauses, it drains quickly enough to reach low water.
        for _ in range(min(256 if paused else 32,m.get('uart_rx_count'))):received.append(m.call('uart_receive_byte'))
        assert received==payload[:len(received)]
    m.thre=True;m.call('uart_poll_flow')
    if soft:
        tail=bytes(m.tx[wire_at:])
        if tail:
            assert tail==b'\x11' and paused;paused=False;resume_count+=1
            marks.append(dict(event='XON',queued=0,sent=sent,received=len(received)))
        assert bytes(m.tx)==b'\x13\x11'*pause_count and not m.controls
    else:
        if paused and m.mcr&2:paused=False;resume_count+=1
        transitions=[v for i,v in enumerate(m.controls) if i==0 or v!=m.controls[i-1]]
        assert transitions==[9,11]*pause_count
    assert received==payload and pause_count==resume_count and pause_count>=10 and not paused
    assert not m.get('uart_xoff_sent',1) and not m.get('uart_rts_lowered',1) and not m.get('uart_flow_pending',1)
    assert m.get('uart_rx_read')==m.get('uart_rx_write') and not m.get('uart_rx_count') and not m.get('uart_rx_dropped')
    return dict(soft=soft,hard=hard,in_flight_tail_bytes=512 if late else 0,THRE_stall=thre_stall,passed=True,bytes=len(payload),sha256=hashlib.sha256(payload).hexdigest(),peak_queued=peak,pause_cycles=pause_count,steps=steps,flow_wire_hex=bytes(m.tx).hex(),MCR_write_count=len(m.controls),MCR_transitions=[v for i,v in enumerate(m.controls) if i==0 or v!=m.controls[i-1]],watermark_events=marks)


def overflow(soft,hard):
    m=Connection();m.connect();m.put('uart_software_flow',soft);m.put('uart_hardware_flow',hard)
    payload=stream(soft,5000);m.receive_irq(payload)
    assert m.get('uart_rx_count')==4096 and m.get('uart_rx_dropped')==904
    received=bytes(m.call('uart_receive_byte') for _ in range(4096))
    assert received==payload[:4096] and not m.get('uart_rx_count')
    return dict(case='peer-ignores-pause',soft=soft,hard=hard,passed=True,offered=5000,retained=4096,dropped=904,retained_sha256=hashlib.sha256(received).hexdigest())


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--product',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    product=a.product.resolve();transport.BINARY=product/'TERMINAL.EXE';transport.MAP=product/'terminal.map'
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    manifest=json.loads((product/'manifest.json').read_text());assert manifest['binary_sha256']==sha(transport.BINARY)
    inputs=dict(manifest['sources'])
    for path in (Path(__file__),ROOT/'standalone/check_connection.py',ROOT/'standalone/check_transport.py',ROOT/'standalone/dos_image.py'):
        inputs[str(path.relative_to(ROOT))]=sha(path)
    for name,digest in inputs.items():
        assert sha(ROOT/name)==digest;dest=out/'inputs'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,dest)
    shutil.copy2(transport.BINARY,out/'admitted.EXE');shutil.copy2(transport.MAP,out/'admitted.map')
    rows=[]
    for soft,hard in ((0,1),(1,0),(1,1)):
      for late in (False,True):
        for stalled in ((False,True) if soft else (False,)):
            row=pressure(soft,hard,late,stalled);rows.append(row);print(json.dumps({k:row[k] for k in ('soft','hard','in_flight_tail_bytes','THRE_stall','peak_queued','pause_cycles')}),flush=True)
      rows.append(overflow(soft,hard))
    r=dict(passed=True,cases=rows,parent_sha256=sha(transport.BINARY),inputs=inputs,checker_sha256=sha(Path(__file__)),scope=__doc__+' Hardware registers, timing and reactive peer are modeled; actual linked RX interrupt, ring reads, XOFF/XON scheduling and RTS instructions execute.65,536-byte exact streams per pressure case, optional512-byte peer tail and deferred THRE. BOTH preserves recovered receive-software precedence while outbound hardware CTS stays low. Overflow negative peer checks first4096 bytes are preserved and904 discarded. Not actual DOS, physical timing, full sustained application reception or full modem acceptance.')
    (out/'checks.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(passed=True,cases=len(rows))))


if __name__=='__main__':main()
