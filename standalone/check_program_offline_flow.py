#!/usr/bin/env python3
"""Linked parent PROGRAM admission after an observed MODEM carrier loss."""
import argparse,json,shutil
from pathlib import Path
from check_program_actions_live import LiveProgram,ROOT,BINARY
from audit_aspect_transmit_wait import sha


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--expect-gap',action='store_true');a=p.parse_args()
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    rows=[]
    for hard in (0,1):
      for lost in (False,True):
        m=LiveProgram(mutate_child=False);m.put('uart_software_flow',1);m.put('uart_hardware_flow',hard)
        m.put('connection_enabled',1,1);m.put('terminal_directory_mode',0);m.put('connection_state',6)
        m.call('terminal_connection_poll');assert m.get('connection_carrier_seen',1)
        if lost:
            m.carrier=False;m.poll()
            assert m.get('connection_state')==0 and m.get('connection_status')==6
        before=bytes(m.tx);assert m.queue(b'OWNED.COM')==0
        m.safe(10);m.safe(11);m.poll()
        assert len(m.children)==1 and m.get('terminal_program_status')==4 and not m.get('terminal_program_pending')
        wire=bytes(m.tx)[len(before):]
        expected=b'\x13' if lost and a.expect_gap else b'' if lost else b'\x13\x11'
        assert wire==expected,(hard,lost,wire,expected)
        assert m.vector_value()==m.parent_vector and m.ier==1 and m.mcr&1
        rows.append(dict(case=('lost' if lost else 'online')+('-both' if hard else '-soft'),passed=True,MODEM_carrier_loss=lost,child_executed=True,wire_hex=wire.hex()))
    manifest=json.loads((BINARY.parent/'manifest.json').read_text());assert manifest['binary_sha256']==sha(BINARY)
    sources={**manifest['sources'],str(Path(__file__).relative_to(ROOT)):sha(Path(__file__)),
        'standalone/check_program_actions_live.py':sha(ROOT/'standalone/check_program_actions_live.py')}
    for name,digest in sources.items():
        assert sha(ROOT/name)==digest;target=out/'inputs'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,target)
    r=dict(passed=True,gap_reproduced=a.expect_gap,compatibility_accepted=not a.expect_gap,cases=rows,parent_sha256=sha(BINARY),inputs=sources,
        scope=__doc__+' Real connection poll and PROGRAM executor run; DOS/BIOS/UART boundaries modeled. Observed high-to-low DCD changes parent state before launch. Baseline sends an isolated XOFF in command mode. No actual DOS modem or physical acceptance.')
    (out/'checks.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(passed=True,cases=len(rows),gap=a.expect_gap)))


if __name__=='__main__':main()
