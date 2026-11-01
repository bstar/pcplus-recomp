#!/usr/bin/env python3
"""Compare actual DOS video cells/cursor replies with an independent pyte screen."""
import argparse
import hashlib
import importlib.metadata
import inspect
import json
import os
from pathlib import Path
import re
import socket
import struct
import subprocess
import threading
import time
import pyte
import wcwidth
from directory_fixtures import prm
from test_terminal import SAMPLER

ROOT = Path(__file__).resolve().parents[1]
RESET = b'\x1b[0m\x1b[2J\x1b[H'
CASES = {
    'CP437-panel': b'\x1b[2;3H\xda' + b'\xc4'*30 + b'\xbf\x1b[3;3H\xb3 LoSs oF CoNtRoL / NODE 01    \xb3\x1b[4;3H\xc0' + b'\xc4'*30 + b'\xd9\x1b[6;5H' + bytes(range(128,256)),
    'cursor-controls': b'ONE\tTWO\r\nTHREE\b!\x1b[5;11HX\x1b[2AY\x1b[3CZ\x1b[2DW\x1b[4BQ',
    'erase-line': b'\x1b[3;1H'+b'A'*60+b'\x1b[3;21H\x1b[K\x1b[5;1H'+b'B'*60+b'\x1b[5;21H\x1b[1K',
    'erase-display': b'\x1b[2;2HABOVE\x1b[15;20HBELOW\x1b[8;12H\x1b[JEND',
    'insert-delete-characters': b'\x1b[4;10HABCDEFGHIJKLM\x1b[4;13H\x1b[3@xyz\x1b[4;20H\x1b[2P',
    'insert-delete-lines': b''.join(f'\x1b[{i};1HLINE {i:02}'.encode() for i in range(1,24))+b'\x1b[6;1H\x1b[2LNEW\x1b[14;1H\x1b[3M',
    'scroll-region': b'\x1b[1;1HTOP\x1b[24;1HBOTTOM\x1b[3;20r\x1b[20;1HINSIDE\r\nNEXT\x1b[3;1H\x1bMUP',
    'deferred-wrap': b'\x1b[7;78HABCDE\x1b[10;80HX\rY\x1b[13;80HZ\bQ',
    'bottom-scroll': b''.join(f'ROW {i:02}\r\n'.encode() for i in range(1,29)),
    'colors': b''.join(f'\x1b[{2+i};4H\x1b[{30+i}mCOLOR {i}'.encode() for i in range(8))+b'\x1b[0m\x1b[12;4H\x1b[1mBRIGHT\x1b[0m\x1b[14;4H\x1b[5mBLINK\x1b[0m\x1b[16;4H\x1b[7mREVERSE\x1b[0m',
    'save-restore-cursor': b'\x1b[5;9H\x1b7\x1b[12;30HELSEWHERE\x1b8BACK',
    'origin-mode': b'\x1b[4;21r\x1b[?6h\x1b[1;1HORIGIN\x1b[18;1HLAST\x1b[?6l\x1b[2;3HABSOLUTE',
    'status-boundary': b'\x1b[25;1HCLAMPED\x1b[999;999H*',
    'RIS-status-boundary': b'\x1b[5;9r\x1b[?6h\x1b[31;1mDIRTY\x1bc\x1b[25;1HRESET\x1b[999;999H!',
}
COLORS = dict(black=0, red=4, green=2, brown=6, blue=1, magenta=5, cyan=3, white=7)

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def reference(payload):
    screen = pyte.Screen(80,24)
    pyte.Stream(screen).feed(payload.decode('cp437'))
    cells = bytearray()
    for row in range(24):
        for col in range(80):
            c = screen.buffer[row][col]
            assert not c.italics and not c.underscore and not c.strikethrough
            fg = COLORS[c.fg] if c.fg != 'default' else 7
            bg = COLORS[c.bg] if c.bg != 'default' else 0
            if c.reverse:
                fg,bg = bg,fg
            attr = fg | (bg<<4) | (8 if c.bold else 0) | (128 if c.blink else 0)
            glyph = c.data.encode('cp437')
            assert len(glyph)==1
            cells.extend(glyph+bytes([attr]))
    return bytes(cells),(screen.cursor.y+1,min(screen.cursor.x,79)+1)

def run(binary,out,label,payload,fragment):
    out.mkdir()
    expected,cursor = reference(payload)
    (out/'input.bin').write_bytes(payload)
    (out/'expected.bin').write_bytes(expected)
    (out/'sampler.asm').write_text(SAMPLER)
    subprocess.run(['nasm','-fbin',str(out/'sampler.asm'),'-o',str(out/'SNAP.COM')],check=True)
    settings=bytearray(prm(port=1,baud=6))
    struct.pack_into('<HH',settings,0x4e4,8,4)
    for off,val in [(0x1ae,7),(0x1b0,15),(0x1b4,0x70),(0x194,6)]:
        struct.pack_into('<H',settings,off,val)
    (out/'TEST.PRM').write_bytes(settings)
    server=socket.socket();server.bind(('127.0.0.1',0));server.listen(1);server.settimeout(12)
    stop=threading.Event();wire=bytearray();checks=dict(actual_DSR_ready=False,reference_cursor_reply=False);errors=[]
    def peer():
        try:
            conn,_=server.accept()
            with conn:
                conn.settimeout(.05);conn.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,1)
                def until(token,seconds):
                    end=time.monotonic()+seconds
                    while time.monotonic()<end and not stop.is_set():
                        if token in wire:return True
                        try:
                            block=conn.recv(4096)
                            if not block:return False
                            wire.extend(block)
                        except socket.timeout:pass
                    return token in wire
                # Splash acknowledgement is keyboard-driven; actual DSR is
                # the readiness boundary. No fake reply or product RAM hook.
                ready=False
                for _ in range(16):
                    conn.sendall(b'\x1b[5n')
                    if until(b'\x1b[0n',.2):ready=True;break
                checks['actual_DSR_ready']=ready
                if not ready:return
                for at in range(0,len(payload),fragment):
                    conn.sendall(payload[at:at+fragment]);time.sleep(.001)
                conn.sendall(b'\x1b[6n')
                checks['reference_cursor_reply']=until(f'\x1b[{cursor[0]};{cursor[1]}R'.encode(),2)
                while not stop.wait(.05):pass
        except OSError as error:
            if not stop.is_set():errors.append(str(error))
    thread=threading.Thread(target=peer,daemon=True);thread.start()
    config=f'''[sdl]
output=surface
[dosbox]
quit warning=false
memsize=16
[cpu]
core=normal
cputype=8086
cycles=fixed 12000
[mixer]
nosound=true
[serial]
serial1=nullmodem server:127.0.0.1 port:{server.getsockname()[1]} transparent:1 rxdelay:200 txdelay:1
serial2=disabled
serial3=disabled
serial4=disabled
[autoexec]
@echo off
mount c "{binary.parent}"
mount d "{out}"
d:
SNAP B
ADDKEY p900 enter p6500 a-x
C:\\TERMINAL.EXE @D:\\TEST.PRM
if errorlevel 1 goto failed
echo PASS>PASS.TXT
goto capture
:failed
echo FAIL>FAIL.TXT
:capture
SNAP S
SNAP A
exit
'''
    (out/'dosbox.conf').write_text(config)
    try:
        with (out/'dosbox.log').open('w') as log:
            proc=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],stdout=log,stderr=log,timeout=15,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'))
    finally:
        stop.set();server.close();thread.join(1)
    actual=(out/'SCREEN.BIN').read_bytes()
    checks.update(DOS_exit=proc.returncode==0 and (out/'PASS.TXT').exists() and not (out/'FAIL.TXT').exists(),
                  hardware_restored=(out/'BEFORE.BIN').read_bytes()==(out/'AFTER.BIN').read_bytes(),
                  PRM_unchanged=(out/'TEST.PRM').read_bytes()==settings,no_peer_errors=not errors,
                  exact_1920_cells=len(actual)==4000 and actual[:3840]==expected,
                  status_help_visible=b'Alt-Z FOR HELP' in actual[3840::2])
    differences=[dict(row=i//80+1,column=i%80+1,actual=list(actual[2*i:2*i+2]),expected=list(expected[2*i:2*i+2])) for i in range(1920) if actual[2*i:2*i+2]!=expected[2*i:2*i+2]]
    result=dict(case=label,passed=all(checks.values()),checks=checks,expected_cursor=cursor,actual_cursor_replies=re.findall(rb'\x1b\[(\d+);(\d+)R',bytes(wire)),different_cells=len(differences),first_differences=differences[:24],peer_errors=errors)
    result['actual_cursor_replies']=[[int(a),int(b)] for a,b in result['actual_cursor_replies']]
    (out/'serial.bin').write_bytes(wire)
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(label,'PASS' if result['passed'] else 'FAIL',len(differences),'different cells',flush=True)
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--package',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    p.add_argument('--case',action='append',choices=list(CASES));p.add_argument('--fragment',type=int,default=7)
    a=p.parse_args();package=a.package.resolve();out=a.output.resolve()
    assert out.is_relative_to(ROOT/'build') and not out.exists() and 0<a.fragment<=4096
    m=json.loads((package/'manifest.json').read_text());binary=package/'PCPLUSSE/TERMINAL.EXE'
    assert sha(binary)==m['files']['TERMINAL.EXE']
    out.mkdir(parents=True)
    reports=[run(binary,out/n,n,RESET+CASES[n],a.fragment) for n in (a.case or CASES)]
    result=dict(passed=all(r['passed'] for r in reports),cases=reports,binary_sha256=sha(binary),pyte_version=importlib.metadata.version('pyte'),fragment_bytes=a.fragment,original_inputs=[],
                sources={n:sha(ROOT/n) for n in ['standalone/test_ansi_reference_dos.py','standalone/test_terminal.py','standalone/directory_fixtures.py','standalone/modem_fixtures.py','standalone/terminal_config_fixtures.py','nix/flake.nix']},
                scope=__doc__+' Real DOS8086 UART stream, 80x24 CP437 cell/attribute comparison and real CPR. pyte is a Linux/VT-style reference, not an authoritative specification for every PCPlus emulation. Status row, font pixels, physical transport and complete stock BBS screens are not covered.')
    result['reference_modules']={name:sha(inspect.getfile(__import__(name,fromlist=['_']))) for name in ['pyte.screens','pyte.streams','pyte.graphics','pyte.charsets','pyte.modes','pyte.control','pyte.escape','wcwidth.wcwidth']}
    result['nix_lock_sha256']=sha(ROOT/'nix/flake.lock')
    result['wcwidth_version']=importlib.metadata.version('wcwidth')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    assert result['passed'],'Independent reference differences retained in '+str(out)

if __name__=='__main__':main()
