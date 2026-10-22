#!/usr/bin/env python3
"""Reproduce retry into a retained carrier after a blocked manual hangup."""
import argparse,json,shutil
from pathlib import Path
from check_connection import Connection,ROOT
from audit_aspect_transmit_wait import sha


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    rows=[]
    for drop in (0,1):
      for hard in (0,1):
        m=Connection(drop=drop);m.put('uart_software_flow',1);m.put('uart_hardware_flow',hard)
        m.connect();assert m.state()==6 and m.get('connection_carrier_seen',1)==128
        m.receive_irq(b'\x13');m.poll();assert m.get('uart_tx_paused')==1
        initial=bytes(m.tx);m.call('terminal_connection_cancel',ax=1)
        assert m.state()==9
        for _ in range(150):
            m.poll()
            if m.state()==0:break
        # The hardware boundary deliberately retains DCD despite DTR policy.
        # No product state is repaired or UART/controller callback replaced.
        assert m.carrier and m.state()==0 and m.get('connection_status')==3
        assert bytes(m.tx)==initial and not m.get('uart_tx_paused')
        assert m.controls==([10,11] if drop else [])
        m.start();m.waiting();retry=bytes(m.tx)[len(initial):]
        assert m.carrier and retry==b'ATZ\rATDLocal.Example:2323\r'
        rows.append(dict(drop_DTR=bool(drop),hardware_flow=bool(hard),gap_reproduced=True,DCD_still_high=True,post_hangup_state=0,post_hangup_status=3,post_hangup_pause=0,DTR_control_writes=m.controls,retry_modem_bytes_while_carrier_high=retry.hex()))
    binary=ROOT/'build/terminal/TERMINAL.EXE';manifest=json.loads((binary.parent/'manifest.json').read_text());assert sha(binary)==manifest['binary_sha256']
    inputs=dict(manifest['sources'])
    for path in (Path(__file__),ROOT/'standalone/check_connection.py',ROOT/'standalone/check_transport.py',ROOT/'standalone/dos_image.py'):
        inputs[str(path.relative_to(ROOT))]=sha(path)
    for name,digest in inputs.items():
        assert sha(ROOT/name)==digest;dest=out/'inputs'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,dest)
    shutil.copy2(binary,out/'admitted.EXE');shutil.copy2(binary.parent/'terminal.map',out/'admitted.map')
    result=dict(passed=True,gap_reproduced=True,compatibility_accepted=False,parent_sha256=sha(binary),cases=rows,inputs=inputs,checker_sha256=sha(Path(__file__)),scope=__doc__+' Four linked actual controller/sender/UART IRQ cases. Hardware model holds DCD high, including across a configured DTR pulse. Blocked hangup retires flow and returns idle, then retry emits AT commands while carrier remains high. This does not establish physical command/data mode or Boca behavior. Actual DOS and policy correction remain required.')
    (out/'checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,gap_reproduced=True,cases=len(rows))))


if __name__=='__main__':main()
