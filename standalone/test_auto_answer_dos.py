#!/usr/bin/env python3
"""Actual DOS8086 configured Alt-Y, quiet/echo+sound, reference and continued ANSI RX."""
import argparse,hashlib,json,re,struct
from pathlib import Path
import test_connection_dos as harness
from answer_notice_watch import build as build_watcher
from modem_fixtures import fixture
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);p.add_argument('--label',required=True);p.add_argument('--rows',type=int,choices=[25,28,43,50],default=25);a=p.parse_args()
assert re.fullmatch('[a-z0-9-]+',a.label)
binary=a.terminal.resolve();manifest=json.loads((binary.parent/'manifest.json').read_text());assert manifest['experimental_auto_answer']
assert (manifest.get('diagnostic_session_rows_probe') or 25)==a.rows and hashlib.sha256(binary.read_bytes()).hexdigest()==manifest['binary_sha256']
for n,h in manifest['sources'].items():assert hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h,n
out=ROOT/'build/auto-answer-dos'/a.label;out.mkdir(parents=True,exist_ok=False);harness.BINARY=binary;cases=[]
# Reuse the passive timer observer, selecting this notice at the first status
# text cell (after its native leading blank) and two complete captures one BIOS
# tick apart. No product hooks/writes.
build_watcher(out,a.rows)
banner=b'\x1b[2J\x1b[HFIRST BYTE SAFE\x1b[6n\x1b[0c'+b'\x1b'+f'[{a.rows-1};1HLOWER-{a.rows}'.encode()+b'\x1b[6n\x1b[1;16H'
for mode,enabled in [('direct-quiet',0),('reference-echo-sound',1)]:
    raw=bytearray(fixture(timeout=5));struct.pack_into('<HH',raw,0,2,5)
    struct.pack_into('<H',raw,0x178,0x3e8);struct.pack_into('<H',raw,0x188,5)
    struct.pack_into('<HH',raw,0x4e4,8,4);struct.pack_into('<HH',raw,0x1bc,enabled,0)
    struct.pack_into('<H',raw,0x196,0);struct.pack_into('<H',raw,0x1e6,0)
    # Real configured pauses give the passive timer time to capture two frames;
    # the pause markers never become serial data or local echo.
    raw[0x92:0xab]=b'ATS0=1~~^M^J\0'.ljust(25,b'\0')
    name=a.label+'-'+mode
    # Duplex is the live Alt-E setting; the partial PRM importer does not adopt it.
    keys='p900 enter p5000 '+('a-e p100 a-z p200 ' if enabled else '')+'a-y x p1800 r e a d y enter p1000 a-x'
    result=harness.run(name,'success',keys,prm=bytes(raw),com=3,irq=5,cpu='8086',working_drive='d',
        arguments='@D:\\TEST.PRM /D:CaseTest:23 /I:3',timeout=30,banner=banner,
        files={'ANSWERW.COM':(out/'ANSWERW.COM').read_bytes()},observer='ANSWERW',
        online_triggers=((b'ATS0=1\r\n',b'\x1b[2;1HANSWER-RX\x1b[6n'),))
    assert result['passed'],result
    folder=ROOT/'build/connection-dos'/name;wire=(folder/'serial.bin').read_bytes();screen=(folder/'SCREEN.BIN').read_bytes()
    assert wire.count(b'ATZ\r')==wire.count(b'ATDCaseTest:23\r')==wire.count(b'ATS0=1\r\n')==1
    start=wire.index(b'ATS0=1\r\n');assert wire.index(b'x',start+8)>=start+8
    assert b'\x1b[2;10R' in wire and wire.count(b'ready\r')==1
    assert screen[160:178:2]==b'ANSWER-RX' and b'AUTO ANSWER...' not in screen[::2]
    assert (b'ATS0=1' in screen[::2])==bool(enabled)
    frames=(folder/'PAUSE.BIN').read_bytes();size=a.rows*160;assert len(frames)==size*2
    for at in (0,size):
        assert frames[at+size-158:at+size-158+28:2]==b'AUTO ANSWER...'
        assert f'LOWER-{a.rows}'.encode() in frames[at+(a.rows-2)*160:at+(a.rows-1)*160:2]
    assert b'\x1b'+f'[{a.rows-1};9R'.encode() in wire
    cases.append(dict(case=mode,passed=True,result=str((folder/'result.json').relative_to(ROOT)),wire_sha256=hashlib.sha256(wire).hexdigest()))
for n,h in manifest['sources'].items():assert hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h,n
report=dict(passed=True,terminal_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),rows=a.rows,cases=cases,
    sources={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__),ROOT/'standalone/pause_watch.asm',ROOT/'standalone/test_connection_dos.py',ROOT/'standalone/answer_notice_watch.py')},
    scope=__doc__+' Actual COM3/3E8 IRQ5 UART/keyboard/native echo/ANSI and DOS owner. Synthetic Hayes serial peer, no original pixels/native calibrated timing or physical/SIP/analog/modem acknowledgement acceptance. Sound-enabled startup/cleanup executes; exact PIT/tone ownership has separate modeled-boundary evidence.')
(out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS actual DOS Auto Answer:',len(cases),'workflows')
