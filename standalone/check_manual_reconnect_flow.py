#!/usr/bin/env python3
"""Execute real manual hangup/cancel and retry with native UART XOFF state."""
import argparse,json,shutil
from pathlib import Path
from check_connection import Connection,ROOT
from audit_aspect_transmit_wait import sha


class Modem(Connection):
    def output_port(self,u,port,size,value,data):
        if port==self.get('uart_port_mcr') and self.mcr&1 and not value&1:self.carrier=False
        return super().output_port(u,port,size,value,data)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--expect-gap',action='store_true');a=p.parse_args()
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True);cases=[]
    for hard in (0,1):
      for kind in ('hangup','cancel-init'):
        m=Modem();m.put('uart_software_flow',1);m.put('uart_hardware_flow',hard)
        if kind=='hangup':m.connect();assert m.get('connection_carrier_seen',1)
        else:m.carrier=False;m.start();assert not m.get('connection_carrier_seen',1)
        m.receive_irq(b'\x13');m.poll();assert m.get('uart_tx_paused')==1
        before=bytes(m.tx);m.keys.append(0x2300 if kind=='hangup' else 0x011b)
        for _ in range(150):
            m.poll()
            if m.state()==0:break
        assert m.state()==0 and m.get('connection_status')==(3 if kind=='hangup' else 4) and not m.get('terminal_quit'),(kind,m.state(),m.get('connection_status'))
        assert bytes(m.tx)==before and m.get('uart_tx_paused')==int(a.expect_gap)
        assert m.controls[-2:]==[10,11] and not m.carrier
        m.keys.append(0x2000);m.poll();assert m.state()==1
        for _ in range(150):
            m.poll()
            if m.state() in (0,5):break
        wire=bytes(m.tx)[len(before):]
        assert m.state()==(0 if a.expect_gap else 5)
        prefix=b'\r' if kind=='cancel-init' else b''
        assert wire==(b'' if a.expect_gap else prefix+b'ATZ\rATDLocal.Example:2323\r')
        cases.append(dict(case=kind+('-both' if hard else '-soft'),passed=True,first_status=3 if kind=='hangup' else 4,retry_state=m.state(),retry_wire_hex=wire.hex()))
    binary=ROOT/'build/terminal/TERMINAL.EXE';manifest=json.loads((binary.parent/'manifest.json').read_text());assert manifest['binary_sha256']==sha(binary)
    inputs={**manifest['sources']}
    for path in (Path(__file__),ROOT/'standalone/check_connection.py',ROOT/'standalone/check_transport.py',ROOT/'standalone/dos_image.py'):
        inputs[str(path.relative_to(ROOT))]=sha(path)
    for name,digest in inputs.items():
        assert sha(ROOT/name)==digest;target=out/'inputs'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,target)
    result=dict(passed=True,gap_reproduced=a.expect_gap,compatibility_accepted=not a.expect_gap,cases=cases,parent_sha256=sha(binary),inputs=inputs,
        scope=__doc__+' Four linked SOFT/BOTH cases. BIOS Alt-H/Escape/Alt-D and native receive IRQ execute. Explicit hardware model lowers DCD on DTR fall. Baseline keeps old peer pause after completion, so retry times out without sending init. No product state/code callbacks substituted, but UART/BIOS hardware boundaries are modeled; actual DOS/physical acceptance separate.')
    (out/'checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,cases=len(cases),gap=a.expect_gap)))


if __name__=='__main__':main()
