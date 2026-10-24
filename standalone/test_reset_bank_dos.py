#!/usr/bin/env python3
"""Receive actual binary UART IRQ traffic while native reset owns a private stack."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import struct
import subprocess
import threading
import time

from test_terminal import SAMPLER
ROOT=Path(__file__).resolve().parents[1]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();out=args.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
    out.mkdir(parents=True);base=ROOT/'build/reset-bank';manifest=json.loads((base/'manifest.json').read_text())
    assert sha(base/'BANK.EXE')==manifest['binary_sha256']
    inputs={**manifest['sources'],'standalone/test_reset_bank_dos.py':sha(Path(__file__)),
        'standalone/test_terminal.py':sha(ROOT/'standalone/test_terminal.py')}
    for name,digest in inputs.items():
        assert sha(ROOT/name)==digest,name
        target=out/'inputs'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
    shutil.copyfile(base/'BANK.EXE',out/'BANK.EXE')
    (out/'sampler.asm').write_text(SAMPLER)
    subprocess.run(['nasm','-fbin',str(out/'sampler.asm'),'-o',str(out/'SNAP.COM')],check=True)
    server=socket.socket();server.bind(('127.0.0.1',0));server.listen(1);server.settimeout(15)
    checks={};events=[];done=threading.Event();payload=bytes(range(256))*2
    def peer():
        try:
            connection,_=server.accept()
            with connection:
                connection.settimeout(.1);pending=bytearray()
                def receive(count):
                    deadline=time.monotonic()+10
                    while len(pending)<count and not done.is_set() and time.monotonic()<deadline:
                        try:data=connection.recv(4096)
                        except socket.timeout:continue
                        if not data:break
                        pending.extend(data)
                    result=bytes(pending[:count]);del pending[:count];return result
                ready=receive(11);checks['root_ready']=ready==b'BANK-READY\r'
                marker=receive(1);checks['private_bank_marker']=marker==b'B'
                if not all(checks.values()):events.append(dict(ready_hex=ready.hex(),marker_hex=marker.hex()));return
                connection.sendall(payload);echo=receive(len(payload))
                (out/'echo.bin').write_bytes(echo)
                checks['every_binary_byte_received_and_echoed']=echo==payload
        except Exception as problem:events.append(dict(error=repr(problem)))
    thread=threading.Thread(target=peer,daemon=True);thread.start()
    config=f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
cycles=fixed 6000
[mixer]
nosound=true
[serial]
serial1=nullmodem server:127.0.0.1 port:{server.getsockname()[1]} transparent:1 rxdelay:1 txdelay:1
serial2=disabled
serial3=disabled
serial4=disabled
[autoexec]
@echo off
mount c "{out}"
mount d "{out}"
c:
SNAP B
BANK
if errorlevel 1 goto failed
echo PASS>PASS.TXT
goto capture
:failed
echo FAIL>FAIL.TXT
:capture
SNAP A
exit
'''
    (out/'dosbox.conf').write_text(config);timed_out=False
    try:
        with(out/'dosbox.log').open('w')as log:
            try:
                result=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],cwd=out,
                    env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=25)
                code=result.returncode
            except subprocess.TimeoutExpired:timed_out=True;code=-1
    finally:
        done.set();server.close();thread.join(2)
    raw=(out/'BANK.BIN').read_bytes()if(out/'BANK.BIN').exists()else b''
    observation=list(struct.unpack('<16H',raw))if len(raw)==32 else []
    checks.update(DOS_normal_exit=code==0 and(out/'PASS.TXT').exists()and not(out/'FAIL.TXT').exists(),
        no_timeout=not timed_out,no_peer_errors=not events,observation_complete=len(raw)==32,
        hardware_restored=(out/'BEFORE.BIN').exists()and(out/'AFTER.BIN').exists()and
            len((out/'BEFORE.BIN').read_bytes())==42 and(out/'BEFORE.BIN').read_bytes()==(out/'AFTER.BIN').read_bytes(),
        frozen_binary_unchanged=sha(out/'BANK.EXE')==manifest['binary_sha256'],
        inputs_unchanged=all(sha(ROOT/name)==sha(out/'inputs'/name)==digest for name,digest in inputs.items()))
    if observation:
        n_ds,n_ss,n_sp,n_flags,columns,configured,row,col,rx_before,rx_after,r_ds,r_ss,r_sp,r_flags,calls,refusals=observation
        delta=(manifest['groups']['RESET_GROUP']['relative_segment']-manifest['groups']['DGROUP']['relative_segment'])&65535
        checks.update(separate_DS_equals_SS=n_ds==n_ss and r_ds==r_ss and n_ds!=r_ds and(n_ds-r_ds)&65535==delta,
            private_stack_bounded=manifest['context_layout']['stack_bottom_offset']<=n_sp<manifest['context_layout']['stack_top_offset'],
            root_stack_bounded=r_sp==manifest['context_layout']['root_stack_top_offset'],
            interrupt_flags=n_flags&0x600==r_flags&0x600==0x200,
            native_width_result=(columns,configured,row,col)==(132,0,0,0),
            actual_RX_growth_on_private_stack=(rx_before,rx_after)==(0,512),
            repeated_and_unwind_calls=calls==20,IF_DF_foreign_DS_refusals=refusals==7)
    report=dict(passed=all(checks.values()),checks=checks,events=events,observation=observation,
        binary_sha256=manifest['binary_sha256'],sources=inputs,groups=manifest['groups'],timed_out=timed_out,
        scope='ActualDOS8086 dualDS=SS context, native soft reset/width and real UART IRQ while the private stack owns execution. All256 binary bytes twice are independently echoed; repeated entry, typed frame abandonment, IF/DF refusal, root canary and hardware/vector restoration are driver-checked. Static diagnostic shadow and body, not application state projection/commit, general allocator/rollback, arbitrary async faults or physical acceptance.')
    (out/'checks.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(passed=report['passed'],checks=checks,events=events,observation=observation),indent=2))
    return 0 if report['passed']else 1


if __name__=='__main__':raise SystemExit(main())
