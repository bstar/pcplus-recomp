#!/usr/bin/env python3
"""Logged-in owned ENiGMA through actual DOS and the SynthModem candidate."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import select
import socket
import subprocess
import sys
import threading
import time

import enigma
from modem import Telnet

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'standalone'))
from modem_fixtures import fixture
from test_terminal import SAMPLER


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()


class Relay:
 """Byte-transparent loopback observer; no batching timer or protocol replies."""
 def __init__(self):
  self.server=socket.socket();self.server.bind(('127.0.0.1',0));self.server.listen(1);self.server.settimeout(12)
  self.port=self.server.getsockname()[1];self.stop=threading.Event();self.errors=[]
  self.to_bbs=bytearray();self.from_bbs=bytearray();self.trace=[]
  self.thread=threading.Thread(target=self.run,daemon=True)
 def run(self):
  start=time.monotonic()
  try:
   client,_=self.server.accept()
   with client,socket.create_connection(('127.0.0.1',enigma.PORT),timeout=3) as bbs:
    while not self.stop.is_set():
     ready,_,_=select.select([client,bbs],[],[],.1)
     for source in ready:
      data=source.recv(4096)
      if not data:return
      target,stream,direction=(bbs,self.to_bbs,'to_bbs') if source is client else (client,self.from_bbs,'from_bbs')
      self.trace.append(dict(direction=direction,offset=len(stream),count=len(data),seconds=time.monotonic()-start))
      stream.extend(data);target.sendall(data)
  except Exception as error:
   if not self.stop.is_set():self.errors.append(repr(error))
  finally:self.server.close()


def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--candidate',type=Path,required=True)
 parser.add_argument('--output',type=Path,required=True);parser.add_argument('--route',choices=['menus','editor'],default='menus');args=parser.parse_args()
 candidate,out=args.candidate.resolve(),args.output.resolve()
 assert candidate.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build')
 pin=json.loads((ROOT/'docs/validation/synthmodem-telnet.json').read_text())
 expected={**pin['candidate_sha256'],**{n:pin['upstream_sha256'][n] for n in ['config.js','src/logger.js']}}
 assert all(sha(candidate/n)==h for n,h in expected.items())
 pid=enigma.process_pid();assert pid and Path(f'/proc/{pid}/cwd').resolve()==enigma.SOURCE.resolve(),'Owned running fixture required'
 revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=enigma.SOURCE,text=True).strip()
 assert revision==enigma.COMMIT
 assert not subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],cwd=enigma.SOURCE,text=True)
 server_files=[enigma.SOURCE/'main.js',enigma.SOURCE/'core/client.js',enigma.SOURCE/'config/config.hjson',enigma.SOURCE/'package-lock.json']
 server_files+=sorted((enigma.SOURCE/'config/menus').glob('*.hjson'))
 server_hashes={str(p.relative_to(enigma.SOURCE)):sha(p) for p in server_files}
 frozen_names=['lab/bbs/synthmodem_bbs_dos.py','lab/bbs/synthmodem_serial.js','lab/bbs/enigma.py','lab/bbs/modem.py',
  'lab/bbs/editor-recipes.json','standalone/modem_fixtures.py','standalone/terminal_config_fixtures.py',
  'standalone/test_terminal.py','build/terminal/TERMINAL.EXE','build/terminal/terminal.map']
 frozen={n:sha(ROOT/n) for n in frozen_names}
 out.mkdir(parents=True,exist_ok=False)
 log=enigma.SOURCE/'logs/enigma-bbs.log';boundary=(log.stat().st_ino,log.stat().st_size)
 (out/'server-log-start.json').write_text(json.dumps(dict(inode=boundary[0],offset=boundary[1]))+'\n')
 relay=Relay();relay.thread.start()
 profile=fixture(timeout=60,autobaud=0);(out/'MODEM.PRM').write_bytes(profile)
 (out/'sampler.asm').write_text(SAMPLER);subprocess.run(['nasm','-fbin',str(out/'sampler.asm'),'-o',str(out/'SNAP.COM')],check=True)
 original=json.loads((ROOT/'lab/bbs/editor-recipes.json').read_text())['enigma_unsaved']['keyboard_input']
 if args.route=='menus':
  login=original.split(' M enter',1)[0]
  recipe=login+' M enter p5000 Q enter p5000 F enter p7000 a-x'
 else:recipe=original
 keys='p3000 '+' '.join(f'127.0.0.1:{relay.port}')+' enter '+recipe+' p2000 a-x'
 assert len('ADDKEY '+keys)<500,'DOS command-line limit'
 with (out/'node.log').open('w') as node_log:
  node=subprocess.Popen(['node',str(ROOT/'lab/bbs/synthmodem_serial.js'),str(candidate),str(out)],stdout=node_log,stderr=node_log)
  try:
   start=time.monotonic()
   while not (out/'serial-port.json').exists():
    assert node.poll() is None and time.monotonic()-start<5
    time.sleep(.02)
   port=json.loads((out/'serial-port.json').read_text())['port']
   binary=ROOT/'build/terminal/TERMINAL.EXE'
   cfg=f'''[sdl]
output=surface
[cpu]
core=normal
cputype=386
cycles=fixed 6000
[mixer]
nosound=true
[serial]
serial1=nullmodem server:127.0.0.1 port:{port} transparent:1 rxdelay:200 txdelay:1
serial2=disabled
serial3=disabled
serial4=disabled
[autoexec]
@echo off
mount c "{binary.parent}"
mount d "{out}"
d:
SNAP B
ADDKEY {keys}
C:\\TERMINAL @MODEM.PRM /D:1 COM1 38400 8N1 HARD
if errorlevel 1 goto fail
echo PASS>PASS.TXT
goto capture
:fail
echo FAIL>FAIL.TXT
:capture
SNAP S
SNAP A
exit
'''
   (out/'dosbox.conf').write_text(cfg)
   with (out/'dosbox.log').open('w') as doslog:
    code=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],stdout=doslog,stderr=doslog,
      env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),timeout=150).returncode
  finally:
   relay.stop.set();node.terminate();node.wait(timeout=5);relay.thread.join(3)
 def read(n):return (out/n).read_bytes() if (out/n).exists() else b''
 assert log.stat().st_ino==boundary[0],'Server log rotated'
 with log.open('rb') as f:f.seek(boundary[1]);all_rows=[json.loads(line) for line in f if line.strip()]
 connected={r['sessionId'] for r in all_rows if r.get('menuName')=='telnetConnected'}
 assert len(connected)==1,connected
 session=connected.pop();rows=[r for r in all_rows if r.get('sessionId')==session]
 menus=[r['menuName'] for r in rows if r.get('menuName')]
 sent,_=Telnet().feed(relay.to_bbs);display,_=Telnet().feed(relay.from_bbs)
 screen=read('SCREEN.BIN');text='\n'.join(screen[r*160:r*160+160:2].decode('cp437') for r in range(25)) if len(screen)==4000 else ''
 clean=re.sub(rb'\x1b\[[0-?]*[ -/]*[@-~]',b'',display).decode('cp437')
 node_events=json.loads((out/'node-events.json').read_text())
 checks=dict(DOS_normal_exit=code==0 and (out/'PASS.TXT').exists() and not (out/'FAIL.TXT').exists(),
  hardware_restored=len(read('BEFORE.BIN'))==42 and read('BEFORE.BIN')==read('AFTER.BIN'),
  no_relay_errors=not relay.errors,relay_stopped=not relay.thread.is_alive(),
  numeric_local_call=node_events['commands']==['ATZ','ATD1'],
  actual_DOS_DA=b'\x1b[?1;2c' in sent,actual_DOS_CPR=bool(re.search(rb'\x1b\[\d+;\d+R',sent)),
  authenticated=any(r.get('msg')=='User "loclab" successfully logged in' for r in rows),
  no_post_saved=not any('posted message to' in r.get('msg','') for r in rows),
  profile_unchanged=read('MODEM.PRM')==profile,
  inputs_unchanged=all(sha(ROOT/n)==h for n,h in frozen.items()),
  candidate_unchanged=all(sha(candidate/n)==h for n,h in expected.items()),
  server_unchanged=all(sha(enigma.SOURCE/n)==h for n,h in server_hashes.items()),
  no_unsupported_terminal='unsupported terminal' not in text.lower())
 if args.route=='menus':
  wanted=iter(['mainMenu','messageBaseMainMenu','mainMenu','fileBaseMainMenu']);next_menu=next(wanted)
  for m in menus:
   if m==next_menu:next_menu=next(wanted,None)
  checks.update(ordered_main_messages_main_files=next_menu is None,
    final_file_menu_visible='file base >>' in text.lower() and menus[-1]=='fileBaseMainMenu')
 else:
  positions=[(int(r),int(c)) for r,c in re.findall(r'(?:INS|OVR) (\d+),(\d+)',clean[clean.find('KEYTEST'):])]
  checks.update(editor_entered='messageBaseNewPost' in menus,typed_draft_sent=b'ABCDE' in sent,
    home_moves_before_marker=positions[:7]==[(1,2),(1,3),(1,4),(1,5),(1,6),(1,1),(1,2)],
    insert_toggles_overtype='OVR ' in clean)
  (out/'editor-positions.json').write_text(json.dumps(positions)+'\n')
 for n,data in [('to-bbs.bin',relay.to_bbs),('from-bbs.bin',relay.from_bbs),('sent.bin',sent),('display.bin',display)]: (out/n).write_bytes(data)
 (out/'screen.txt').write_text(text+'\n');(out/'server-session.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
 (out/'chunk-trace.json').write_text(json.dumps(relay.trace,indent=2)+'\n')
 result=dict(passed=all(checks.values()),route=args.route,checks=checks,session=session,menus=menus,
  frozen_inputs=frozen,candidate_sha256=expected,server_revision=revision,server_sha256=server_hashes,
  wire_sha256={n:sha(out/n) for n in ['to-bbs.bin','from-bbs.bin','sent.bin','display.bin','SCREEN.BIN','server-session.jsonl']},
  scope='Actual DOS and isolated SynthModem TelnetProxy against owned stock ENiGMA on loopback. Synthetic ATZ/ATD1 call; transparent immediate relay has no timed buffering or terminal replies. No SIP/audio, physical modem or full BBS compatibility claim.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2),flush=True)
 return 0 if result['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
