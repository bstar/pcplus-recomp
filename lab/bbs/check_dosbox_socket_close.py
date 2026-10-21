#!/usr/bin/env python3
"""Pair normal emulated UART exits with drained versus unread TCP payload."""
import argparse
import errno
import json
import os
from pathlib import Path
import re
import shutil
import socket
import struct
import subprocess
import threading
import time
from synthmodem_vm_control import ROOT, sha


def case(out, name, payload_size, read_count):
    out = out/name; out.mkdir()
    payload = bytes(range(256))*(payload_size//256)
    server = socket.socket(); server.bind(('127.0.0.1',0)); server.listen(1); server.settimeout(10)
    port = server.getsockname()[1]; observed = {'bytes_sent':0,'received_hex':'','close':None,'errno':None}
    def peer():
        try:
            conn,_ = server.accept()
            with conn:
                conn.settimeout(10)
                first = conn.recv(1); assert first == b'R', first
                conn.sendall(payload); observed['bytes_sent'] = len(payload)
                wire = bytearray(first)
                try:
                    while True:
                        b = conn.recv(4096)
                        if not b: observed['close'] = 'EOF'; break
                        wire.extend(b)
                except ConnectionResetError as e:
                    observed['close'] = 'RST'; observed['errno'] = e.errno
                observed['received_hex'] = wire.hex()
        except Exception as e: observed['exception'] = repr(e)
        finally: server.close()
    thread = threading.Thread(target=peer,daemon=True); thread.start()
    subprocess.run(['nasm','-fbin',f'-DREAD_COUNT={read_count}',str(ROOT/'lab/bbs/dosbox_socket_close_probe.asm'),'-o',str(out/'PROBE.COM')],check=True)
    (out/'dosbox.conf').write_text(f'''[sdl]
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
mount c "{out}"
c:
PROBE
if errorlevel 1 goto fail
echo PASS>PASS.TXT
goto done
:fail
echo FAIL>FAIL.TXT
:done
exit
''')
    with (out/'dosbox.log').open('w') as log:
        run = subprocess.run(['strace','-f','-ttt','-yy','-e','trace=network,close','-o',str(out/'syscalls.log'),
                              'dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],
                             stdout=log,stderr=log,timeout=15,
                             env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'))
    thread.join(2); assert not thread.is_alive()
    witness = (out/'COUNT.BIN').read_bytes()
    lines = (out/'syscalls.log').read_text().splitlines()
    relevant = [line for line in lines if f'127.0.0.1:{port}' in line]
    received = sum(int(m.group(1)) for line in relevant if 'recvfrom(' in line
                   for m in [re.search(r'\)\s+=\s+(\d+)',line)] if m)
    checks = {'normal_DOS_return':run.returncode==0 and (out/'PASS.TXT').is_file() and not (out/'FAIL.TXT').exists(),
              'UART_read_witness':len(witness)==3 and struct.unpack('<H',witness[:2])[0]==read_count and witness[2]==payload[read_count-1],
              'peer_ready_only':observed['received_hex']==b'R'.hex(),
              'peer_payload_sent':observed['bytes_sent']==len(payload),
              'no_peer_exception':'exception' not in observed}
    result = {'name':name,'checks':checks,'passed':all(checks.values()),'payload_bytes':len(payload),
              'UART_bytes_read':read_count,'observed':observed,'traced_TCP_bytes_received':received,
              'socket_syscalls':relevant,'artifacts_sha256':{p.name:sha(p) for p in out.iterdir() if p.is_file()}}
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n'); return result


def main():
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--output',type=Path,required=True)
    out = p.parse_args().output.resolve(); assert out.is_relative_to(ROOT/'build'); out.mkdir(parents=True,exist_ok=False)
    cases = [case(out,'drained',256,256),case(out,'unread',65536,1)]
    comparison = {'both_normal_exits':all(c['passed'] for c in cases),
                  'drained_has_FIN_EOF':cases[0]['observed']['close']=='EOF',
                  'unread_has_connection_reset':cases[1]['observed']['close']=='RST' and cases[1]['observed']['errno']==errno.ECONNRESET,
                  'drained_TCP_payload_consumed':cases[0]['traced_TCP_bytes_received']==256,
                  'unread_TCP_payload_remains':0<cases[1]['traced_TCP_bytes_received']<65536}
    inputs = [Path(__file__).resolve(),ROOT/'lab/bbs/dosbox_socket_close_probe.asm',ROOT/'nix/flake.nix',ROOT/'nix/flake.lock']
    result = {'passed':all(comparison.values()),'comparison':comparison,'cases':cases,
              'inputs':{str(n.relative_to(ROOT)):sha(n) for n in inputs},
              'tools':{name:{'path':str(Path(shutil.which(name)).resolve()),'sha256':sha(Path(shutil.which(name)))} for name in ['dosbox-x','strace','nasm']},
              'scope':'Controlled actual DOS UART reads and normal emulator exits, real loopback TCP peer and owned-child syscall traces. Only read count/payload size differ. Proves an emulator unread-data reset mechanism, not the exact cause of historical untraced DOS exits, application completeness or physical modem behavior.'}
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'passed':result['passed'],'comparison':comparison,'cases':[{k:c[k] for k in ['name','passed','observed','traced_TCP_bytes_received']} for c in cases]},indent=2)); assert result['passed']


if __name__=='__main__': main()
