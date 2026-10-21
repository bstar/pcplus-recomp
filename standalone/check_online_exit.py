#!/usr/bin/env python3
"""Actual linked Alt-X must hang up online, while dialing still uses abort."""
import argparse
import hashlib
import json
import time
from pathlib import Path
from check_connection import Connection, ROOT


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--output',type=Path,default=ROOT/'build/terminal/online-exit'/str(time.time_ns()))
    out=p.parse_args().output.resolve(); assert out.is_relative_to(ROOT/'build'); out.mkdir(parents=True,exist_ok=False)
    cases=[]
    for name in ['online-configured','online-empty','dialing','hangup-in-progress','online-CTS-stall']:
        m=Connection()
        if name=='online-empty':
            m.uc.mem_write(m.symbols['terminal_modem_settings']+115,bytes(25))
            assert m.call('terminal_connection_prepare')==0
        if name=='dialing': m.start(); m.waiting()
        else: m.connect()
        if name=='hangup-in-progress':
            m.keys.append(0x2300); m.poll(); assert m.state()==9
        if name=='online-CTS-stall': m.cts=False
        before=len(m.tx); m.keys.append(0x2d00)
        if name=='online-CTS-stall':
            m.poll(60); m.cts=True; m.poll(40) # Recover after the3s hangup deadline.
        else: m.poll(100)
        wanted=b'\x1b' if name=='dialing' else b'' if name in ['online-empty','online-CTS-stall'] else b'+++ATH\r'
        wire=bytes(m.tx[before:])
        checks={'exact_selected_modem_operation':wire==wanted,
                'bounded_completion':m.state()==0 and m.get('terminal_quit')==1,
                'DTR_restored':m.controls==[10,11],
                'typed_completion_status':m.get('connection_status')==(4 if name=='dialing' else 3 if name=='online-CTS-stall' else 5)}
        cases.append({'name':name,'passed':all(checks.values()),'checks':checks,
                      'expected_wire_hex':wanted.hex(),'actual_wire_hex':wire.hex(),
                      'final_state':m.state(),'final_status':m.get('connection_status'),'modem_control_writes':m.controls})
    inputs=[Path(__file__),ROOT/'standalone/check_connection.py',ROOT/'standalone/check_transport.py',
            ROOT/'standalone/modem_fixtures.py',ROOT/'build/terminal/TERMINAL.EXE',ROOT/'build/terminal/terminal.map']
    r={'passed':all(c['passed'] for c in cases),'cases':cases,'inputs':{str(n.resolve().relative_to(ROOT)):sha(n) for n in inputs},
       'scope':'Actual linked keyboard/connection/sender/UART instructions. Hardware-only BIOS tick, keyboard, CTS/DCD and port models. Online Alt-X selects configured hangup (or DTR-only empty string), retains an in-progress hangup, and never turns a hangup timeout into a dial-abort byte. Dialing keeps the configured abort character. No exact-original-UI or physical modem claim.'}
    (out/'result.json').write_text(json.dumps(r,indent=2)+'\n')
    print(json.dumps(r,indent=2)); assert r['passed']


if __name__=='__main__': main()
