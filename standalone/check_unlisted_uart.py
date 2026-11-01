#!/usr/bin/env python3
"""Run linked UART ownership with an omitted or conflicting BIOS table entry."""
import argparse,json,struct
from pathlib import Path
import check_parent_custom_irq as parent
import check_transport as transport
import check_aspect_custom_irq as child

ROOT=Path(__file__).resolve().parents[1]

def terminal_cases(binary,accept_empty):
    transport.BINARY=binary;transport.MAP=binary.parent/'terminal.map'
    count=0
    for port in (2,3,4):
        for irq in (3,4,5,7):
            for entry in (0,0x1234):
                m=parent.IRQPorts();m.quiet()
                m.uc.mem_write(0x400+2*(port-1),struct.pack('<H',entry))
                before=(m.hardware(),m.saved(),m.pic,len(m.writes),len(m.reads))
                wanted=0 if entry==0 and accept_empty else 1
                assert m.move(port,irq)==wanted
                if wanted:
                    assert (m.hardware(),m.saved(),m.pic,len(m.writes),len(m.reads))==before
                else:
                    assert m.get('uart_port_rbr')==parent.BASES[port-1]
                    assert m.get('terminal_irq_vector')==irq+8
                m.resume();m.shutdown();count+=1
    return count

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--terminal',type=Path,required=True)
    p.add_argument('--baseline',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    old=terminal_cases(a.baseline.resolve(),False)
    current=terminal_cases(a.terminal.resolve(),True)
    count=0
    for port in range(1,5):
        for irq in (3,4,5,7):
            for entry in (0,0x1234):
                m=child.machine();m.uc.mem_write(0x400+2*(port-1),struct.pack('<H',entry))
                status=m.open(f'/S{port}:0003:03:N:I{irq}'.encode())
                if entry:
                    assert status!=0 and not m.physical_writes
                else:
                    assert status==0
                    m.receive_irq(b'RAW\x80\xff')
                    assert bytes(m.call('_aspect_serial_read') for _ in range(5))==b'RAW\x80\xff'
                    assert m.call('_aspect_serial_close')==0
                m.restored();count+=1
    result=dict(passed=True,old_terminal_cases=old,terminal_cases=current,child_cases=count,
        terminal_sha256=child.sha(a.terminal),baseline_sha256=child.sha(a.baseline),
        child_diagnostic_sha256=child.sha(child.base.uart.BINARY),
        sources={n:child.sha(ROOT/n) for n in ('standalone/check_unlisted_uart.py',
            'src/terminal/main.asm','src/terminal/port_handoff.asm','src/aspect/serial_backend.asm')},
        scope=__doc__+' Actual linked code; modeled hardware. Old control rejects omitted entries; new custom-IRQ code acquires/restores them and rejects nonzero conflicts before writes. Startup and actual child process need separate DOS evidence.')
    (a.output/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS',old,'old control,',current,'terminal and',count,'child cases')

if __name__=='__main__':main()
