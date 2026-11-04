#!/usr/bin/env python3
"""Actual DOS8086 manual Init through direct/reference keys and continued ANSI RX."""
import argparse,hashlib,json,re,struct
from pathlib import Path
import test_connection_dos as harness
from modem_fixtures import fixture
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True)
p.add_argument('--label',required=True);a=p.parse_args();assert re.fullmatch('[a-z0-9-]+',a.label)
binary=a.terminal.resolve();assert json.loads((binary.parent/'manifest.json').read_text())['experimental_manual_init']
out=ROOT/'build/manual-init-dos'/a.label;out.mkdir(parents=True,exist_ok=False);harness.BINARY=binary
raw=bytearray(fixture(timeout=5));struct.pack_into('<HH',raw,0,2,5)
struct.pack_into('<H',raw,0x178,0x3e8);struct.pack_into('<H',raw,0x188,5)
struct.pack_into('<HH',raw,0x4e4,8,4);struct.pack_into('<HH',raw,0x1bc,0,0);struct.pack_into('<H',raw,0x1e6,0)
cases=[]
for mode in ('direct','reference'):
    name=a.label+'-'+mode
    keys='p900 enter p5000 '+('a-z p200 ' if mode=='reference' else '')+'a-j x p1800 r e a d y enter p1000 a-x'
    result=harness.run(name,'success',keys,prm=bytes(raw),com=3,irq=5,cpu='8086',working_drive='d',
        arguments='@D:\\TEST.PRM /D:CaseTest:23 /I:3',timeout=30,
        online_triggers=((b'ATZ\r',b'\x1b[2;1HMANUAL-INIT-RX\x1b[6n'),))
    assert result['passed'],result
    folder=ROOT/'build/connection-dos'/name;wire=(folder/'serial.bin').read_bytes();screen=(folder/'SCREEN.BIN').read_bytes()
    dial=wire.index(b'ATDCaseTest:23\r')+len(b'ATDCaseTest:23\r')
    manual=wire.index(b'ATZ\r',dial)
    assert wire.count(b'ATZ\r')==2 and wire.count(b'ATDCaseTest:23\r')==1
    assert wire.index(b'x',manual+4)>=manual+4 and wire.count(b'ready\r')==1
    assert b'\x1b[2;15R' in wire
    assert screen[160:160+28:2]==b'MANUAL-INIT-RX'
    assert b'ATZ' not in screen[::2]
    cases.append(dict(case=mode,passed=True,result=str((folder/'result.json').relative_to(ROOT)),
                      wire_sha256=hashlib.sha256(wire).hexdigest()))
report=dict(passed=True,terminal_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),cases=cases,
            scope=__doc__+' Real DOS/UART/keyboard, native expander/parser and synthetic serial Hayes peer; COM3/3E8 IRQ5. Exact manual bytes, no extra dial, retained typeahead, normal CPR and restored hardware/configuration. No physical/SIP/analog timing or modem acknowledgement proof.')
(out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS actual DOS manual Init:',len(cases),'workflows')
