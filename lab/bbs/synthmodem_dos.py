#!/usr/bin/env python3
"""Actual DOS ZMODEM through the isolated SynthModem proxy, no SIP/audio."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import select
import socket
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[2]
NEGOTIATION = bytes([255,253,0,255,251,0,255,253,24,255,253,31,
                    255,251,1,255,251,3,255,253,3,255,250,24,1,255,240])
sys.path.insert(0, str(ROOT / 'standalone'))
from modem_fixtures import fixture
from test_terminal import SAMPLER
from test_terminal_zmodem_dos import ZPeer


def sha(path):
 return hashlib.sha256(path.read_bytes()).hexdigest()


class TelnetServer:
 """Independent server-side framing, only the explicitly offered options.

 Negotiations are already offered at accept; collect acknowledgments without
 re-offering. All terminal reports and file-protocol bytes come from DOS/lrzsz.
 """
 def __init__(self):
  self.state = 'data'; self.sub = bytearray(); self.commands = []; self.subs = []
 def feed(self, data):
  out = bytearray()
  for b in data:
   if self.state == 'data':
    if b == 255: self.state = 'iac'
    else: out.append(b)
   elif self.state == 'iac':
    if b == 255: out.append(b); self.state = 'data'
    elif b in (251, 252, 253, 254): self.verb = b; self.state = 'option'
    elif b == 250: self.sub.clear(); self.state = 'sub'
    else: self.state = 'data'
   elif self.state == 'option': self.commands.append([self.verb, b]); self.state = 'data'
   elif self.state == 'sub':
    if b == 255: self.state = 'subiac'
    else: self.sub.append(b)
   elif self.state == 'subiac':
    if b == 255: self.sub.append(b); self.state = 'sub'
    else:
     assert b == 240, 'Unexpected server subnegotiation control'
     self.subs.append(bytes(self.sub)); self.sub.clear(); self.state = 'data'
   assert len(self.sub) <= 1024
  return bytes(out)


class Relay:
 def __init__(self, raw_port):
  self.server = socket.socket(); self.server.bind(('127.0.0.1', 0)); self.server.listen(1)
  self.server.settimeout(12); self.port = self.server.getsockname()[1]
  self.raw_port = raw_port; self.stop = threading.Event(); self.errors = []; self.codec = TelnetServer()
  self.incoming = bytearray(); self.outgoing = bytearray(); self.plain = bytearray()
  self.thread = threading.Thread(target=self.run, daemon=True)
 def run(self):
  try:
   conn, _ = self.server.accept()
   with conn, socket.create_connection(('127.0.0.1', self.raw_port), timeout=3) as raw:
    # Server offers precede terminal data; exercise TTYPE SEND and proper NAWS.
    conn.sendall(NEGOTIATION); self.outgoing.extend(NEGOTIATION)
    while not self.stop.is_set():
     ready, _, _ = select.select([conn, raw], [], [], .1)
     for source in ready:
      data = source.recv(4096)
      if not data: return
      if source is conn:
       self.incoming.extend(data); plain = self.codec.feed(data); self.plain.extend(plain)
       if plain: raw.sendall(plain)
      else:
       escaped = data.replace(b'\xff', b'\xff\xff'); self.outgoing.extend(escaped); conn.sendall(escaped)
  except Exception as error:
   if not self.stop.is_set(): self.errors.append(repr(error))
  finally: self.server.close()


def run_case(out, candidate, direction, binary_hash, large):
 out.mkdir(parents=True, exist_ok=False)
 for n in ('RECV', 'SEND', 'PEER'): (out / n).mkdir()
 files = [('EMPTY.BIN', b''), ('ODD.BIN', b'A'), ('ALL.BIN', bytes(range(256)) * (257 if large else 4) + b'\0\x1a\xff@\r')]
 source = out / ('SEND' if direction == 'tx' else 'PEER')
 for name, data in files: (source / name).write_bytes(data)
 source_hashes = {p.name: sha(p) for p in source.iterdir()}
 recipe = dict(name=direction, direction=direction, flags=[], files=files,
               transfer_timeout=95 if large else 40, resume_timeout=95 if large else 40)
 peer = ZPeer(recipe, out); peer.thread.start()
 relay = Relay(peer.port); relay.thread.start()
 with (out / 'node.log').open('w') as log:
  node = subprocess.Popen(['node', str(ROOT / 'lab/bbs/synthmodem_serial.js'), str(candidate), str(out)], stdout=log, stderr=log)
  started = time.monotonic()
  try:
   while not (out / 'serial-port.json').exists():
    assert node.poll() is None and time.monotonic() - started < 5, 'Bridge did not start'
    time.sleep(.02)
   port = json.loads((out / 'serial-port.json').read_text())['port']
   (out / 'sampler.asm').write_text(SAMPLER)
   subprocess.run(['nasm', '-fbin', str(out / 'sampler.asm'), '-o', str(out / 'SNAP.COM')], check=True)
   profile = fixture(timeout=60, autobaud=0); (out / 'MODEM.PRM').write_bytes(profile)
   filename = 'D:\\RECV\\' if direction == 'rx' else 'D:\\SEND\\*.BIN'
   # Numeric call is automatic; the BBS address is typed at the bridge prompt.
   keys = ['p3000'] + list(f'127.0.0.1:{relay.port}') + ['enter', 'p1200',
     'a-r' if direction == 'rx' else 'a-s', 'p300', 'f2', 'p100', 'f2', 'p200'] + list(filename) + [
     'enter', 'p65000' if large else 'p16000', 'r', 'e', 'a', 'd', 'y', 'p1500', 'a-x']
   binary = ROOT / 'build/terminal/TERMINAL.EXE'
   config = f'''[sdl]
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
ADDKEY {' '.join(keys)}
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
   (out / 'dosbox.conf').write_text(config)
   with (out / 'dosbox.log').open('w') as doslog:
    code = subprocess.run(['dosbox-x', '-fastlaunch', '-nogui', '-conf', str(out / 'dosbox.conf')],
      env=dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy'),
      stdout=doslog, stderr=doslog, timeout=100 if large else 50).returncode
  finally:
   peer.stop.set(); relay.stop.set(); node.terminate(); node.wait(timeout=5)
   if peer.conn:
    try: peer.conn.shutdown(socket.SHUT_RDWR)
    except OSError: pass
   peer.thread.join(6); relay.thread.join(3)
 def read(name): return (out / name).read_bytes() if (out / name).exists() else b''
 destination = out / ('RECV' if direction == 'rx' else 'PEER')
 events = json.loads((out / 'node-events.json').read_text())
 screen = read('SCREEN.BIN')
 checks = dict(peer.checks)
 checks.update(DOS_normal_exit=code == 0 and (out / 'PASS.TXT').exists() and not (out / 'FAIL.TXT').exists(),
  hardware_restored=len(read('BEFORE.BIN')) == 42 and read('BEFORE.BIN') == read('AFTER.BIN'),
  no_peer_errors=not peer.errors, no_relay_errors=not relay.errors,
  threads_stopped=not peer.thread.is_alive() and not relay.thread.is_alive(),
  exact_destination={p.name:p.read_bytes() for p in destination.iterdir()} == dict(files),
  sources_unchanged={p.name:sha(p) for p in source.iterdir()} == source_hashes,
  numeric_local_call=events['commands'] == ['ATZ', 'ATD1'],
  BINARY_both_directions=[251,0] in relay.codec.commands and [253,0] in relay.codec.commands,
  TTYPE_ANSI=b'\x18\0ANSI' in relay.codec.subs,
  NAWS_80x25=b'\x1f\0P\0\x19' in relay.codec.subs,
  inbound_Telnet_payload_exact=relay.plain==peer.wire,
  outbound_Telnet_payload_exact=relay.outgoing==NEGOTIATION+peer.sent.replace(b'\xff',b'\xff\xff'),
  posttransfer_DSR=bool(peer.checks.get('posttransfer_DSR')),
  posttransfer_keyboard=bool(peer.checks.get('posttransfer_keyboard')),
  screen_restored=len(screen)==4000 and screen[:28:2]==b'AFTER TRANSFER',
  no_stages=not any(p.name.upper().startswith(('PCRX.', 'PCZRX.')) for p in out.rglob('*')),
  profile_unchanged=read('MODEM.PRM')==profile,
  binary_unchanged=sha(ROOT/'build/terminal/TERMINAL.EXE')==binary_hash)
 for name,data in [('telnet-in.bin',relay.incoming),('telnet-out.bin',relay.outgoing),
                   ('terminal-in.bin',peer.wire),('terminal-out.bin',peer.sent)]: (out/name).write_bytes(data)
 (out/'peer-events.json').write_text(json.dumps(peer.events,indent=2)+'\n')
 result=dict(passed=all(checks.values()),direction=direction,checks=checks,peer_errors=peer.errors,
  relay_errors=relay.errors,peer_command=getattr(peer,'command',None),peer_exit=peer.peer_exit,
  files={name:hashlib.sha256(data).hexdigest() for name,data in files},binary_sha256=binary_hash,
  trace_sha256={name:sha(out/name) for name in ['telnet-in.bin','telnet-out.bin','terminal-in.bin','terminal-out.bin']},
  literal_FF_payload_counts={'from_DOS':peer.wire.count(255),'to_DOS':peer.sent.count(255)},
  scope='Actual DOS controller, BIOS keys, UART, files and ZMODEM with independent lrzsz through actual candidate TelnetProxy and loopback TCP. Synthetic Hayes call and server framing; no SIP/audio, physical modem or real BBS.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n'); print(direction,json.dumps(result),flush=True)
 return result


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate',type=Path,required=True)
 p.add_argument('--output',type=Path,required=True);p.add_argument('--direction',choices=['rx','tx','both'],default='both');p.add_argument('--large',action='store_true');a=p.parse_args()
 candidate=a.candidate.resolve();out=a.output.resolve()
 assert candidate.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build')
 baseline=json.loads((ROOT/'docs/validation/synthmodem-telnet.json').read_text())
 expected=baseline['candidate_sha256']
 for name,h in expected.items():assert sha(candidate/name)==h,name
 for name in ['config.js','src/logger.js']:
  assert sha(candidate/name)==baseline['upstream_sha256'][name],name
 out.mkdir(parents=True,exist_ok=False)
 inputs=['lab/bbs/synthmodem_dos.py','lab/bbs/synthmodem_serial.js',
  'standalone/test_terminal_zmodem_dos.py','standalone/test_terminal_ymodem_dos.py',
  'standalone/test_terminal_transfer_dos.py','standalone/test_terminal.py','standalone/modem_fixtures.py',
  'standalone/terminal_config_fixtures.py','build/terminal/TERMINAL.EXE','build/terminal/terminal.map']
 frozen={name:sha(ROOT/name) for name in inputs}
 candidate_inputs={name:sha(candidate/name) for name in ['config.js','src/logger.js',*expected]}
 results=[run_case(out/d,candidate,d,frozen['build/terminal/TERMINAL.EXE'],a.large) for d in (['rx','tx'] if a.direction=='both' else [a.direction])]
 assert frozen=={name:sha(ROOT/name) for name in inputs},'Inputs changed during execution'
 for name,h in expected.items():assert sha(candidate/name)==h,name
 assert candidate_inputs=={name:sha(candidate/name) for name in candidate_inputs}
 result=dict(passed=all(r['passed'] for r in results),large=a.large,frozen_inputs=frozen,candidate_sha256=candidate_inputs,
  tools={name:subprocess.check_output([name,'--version'],stderr=subprocess.STDOUT,text=True).splitlines()[0] for name in ['node','sz','rz']},cases=results)
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
 return 0 if result['passed'] else 1


if __name__=='__main__': raise SystemExit(main())
