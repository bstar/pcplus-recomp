#!/usr/bin/env python3
"""Actual DOS ASPECT scripts, native COM1, independent peer and ASIO parent return."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src/aspect'))
from compiler import compile_source

DRIVER = r'''
#include <dos.h>
#include <conio.h>
#include <stdio.h>
#include <process.h>
#include <io.h>
#include <fcntl.h>
#include <sys/stat.h>
#include "serial_handoff.h"
static aspect_serial_handoff lease;
static struct {unsigned before;unsigned char bytes[4096];unsigned after;} ring;
int main(void){
 int out,err,oldout,olderr,result;unsigned mask,vector_ok,mask_ok,psp,ds,guard_ok,oldmcr,mcr_ok;
 char option[32];union REGS inregs,outregs;FILE *record;
 void (__interrupt __far *vector)(void);
 inregs.h.ah=0x62;intdos(&inregs,&outregs);psp=outregs.x.bx;
 ds=FP_SEG((void __far *)&lease);
 lease.magic=ASIO_MAGIC;lease.version=ASIO_VERSION;lease.size=ASIO_SIZE;
 lease.parent_psp=psp;lease.parent_ds=ds;lease.ring=(unsigned)ring.bytes;
 lease.capacity=ASIO_CAPACITY;lease.guard=psp^ds^(unsigned)ring.bytes^ASIO_GUARD;
 ring.before=0x1234;ring.after=0x5678;
 sprintf(option,"/S1:0003:03:N:%04X:%04X",ds,(unsigned)&lease);
 /* Model the retained parent's already established modem connection. The
  * child lease deliberately refuses to raise DTR itself. */
 oldmcr=inp(0x3fc);outp(0x3fc,oldmcr|1);
 vector=_dos_getvect(12);mask=inp(0x21);
 out=open("STDOUT.BIN",O_CREAT|O_TRUNC|O_WRONLY|O_BINARY,S_IREAD|S_IWRITE);
 err=open("STDERR.BIN",O_CREAT|O_TRUNC|O_WRONLY|O_BINARY,S_IREAD|S_IWRITE);
 if(out<0||err<0)return 99;
 oldout=dup(1);olderr=dup(2);if(oldout<0||olderr<0)return 98;
 if(dup2(out,1)||dup2(err,2))return 97;close(out);close(err);
 result=spawnl(P_WAIT,"ASPECT.EXE","ASPECT","CASE.ASX",option,(char *)0);
 dup2(oldout,1);dup2(olderr,2);close(oldout);close(olderr);
 vector_ok=_dos_getvect(12)==vector;mask_ok=inp(0x21)==mask;
 mcr_ok=inp(0x3fc)==(oldmcr|1);outp(0x3fc,oldmcr);
 guard_ok=ring.before==0x1234&&ring.after==0x5678&&lease.guard==(psp^ds^(unsigned)ring.bytes^ASIO_GUARD);
 record=fopen("RETURN.BIN","wb");if(!record)return 96;
 if(lease.count<=4096)fwrite(ring.bytes,1,lease.count,record);fclose(record);
 record=fopen("LEASE.BIN","wb");if(!record)return 96;fwrite(&lease,1,sizeof(lease),record);fclose(record);
 record=fopen("STATUS.TXT","w");if(!record)return 96;
 fprintf(record,"exit=%d vector=%u mask=%u mcr=%u returned=%u count=%u lease=%u guard=%u\n",
 result,vector_ok,mask_ok,mcr_ok,lease.returned,lease.count,lease.status,guard_ok);fclose(record);
 return vector_ok&&mask_ok&&mcr_ok&&guard_ok&&lease.returned==1&&lease.count<=4096?0:95;
}
'''


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build_driver(output):
    output.mkdir(parents=True, exist_ok=True)
    (output / 'driver.c').write_text(DRIVER)
    subprocess.run(['wcl', '-q', '-bt=dos', '-0', '-ms', '-s', '-w4', '-we', '-k4096',
                    '-i=' + str(ROOT / 'src/aspect'), '-fe=SERTEST.EXE', str(output / 'driver.c')],
                   cwd=output, check=True)
    return output / 'SERTEST.EXE'


def run(case, binary, destination, driver):
    output = destination / case['name']
    output.mkdir(parents=True, exist_ok=True)
    for name in ('STATUS.TXT', 'STDOUT.BIN', 'STDERR.BIN', 'RETURN.BIN', 'LEASE.BIN', 'PASS.TXT', 'FAIL.TXT'):
        (output / name).unlink(missing_ok=True)
    shutil.copyfile(binary, output / 'ASPECT.EXE')
    shutil.copyfile(driver, output / 'SERTEST.EXE')
    compiled = compile_source(case['source'])
    assert compiled == bytes.fromhex(case['hex']), case['name']
    (output / 'CASE.ASP').write_bytes(case['source'].encode('cp437'))
    (output / 'CASE.ASX').write_bytes(compiled)
    model, expected = case['serial'], case['expected']
    outgoing = bytes.fromhex(expected['tx_hex'])
    incoming = bytes.fromhex(model.get('input_hex', ''))
    trigger = bytes.fromhex(model.get('send_after_tx_hex', ''))
    wire, errors = bytearray(), []
    stop, sent = threading.Event(), threading.Event()
    server = socket.socket()
    server.bind(('127.0.0.1', 0));server.listen(1);server.settimeout(12)

    def peer():
        try:
            connection, _ = server.accept()
            with connection:
                connection.settimeout(0.05)
                connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                while not stop.is_set():
                    if not sent.is_set() and (not trigger or trigger in wire):
                        if incoming:
                            connection.sendall(incoming)
                        sent.set()
                    try:
                        chunk = connection.recv(4096)
                        if not chunk:
                            break
                        wire.extend(chunk)
                    except socket.timeout:
                        pass
        except OSError as error:
            if not stop.is_set():
                errors.append(str(error))

    thread = threading.Thread(target=peer, daemon=True);thread.start()
    config = f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
cycles=max
[mixer]
nosound=true
[serial]
serial1=nullmodem server:127.0.0.1 port:{server.getsockname()[1]} transparent:1 rxdelay:200 txdelay:1
serial2=disabled
serial3=disabled
serial4=disabled
[autoexec]
@echo off
mount c "{output}"
c:
SERTEST
if errorlevel 1 goto failed
echo PASS>PASS.TXT
goto done
:failed
echo FAIL>FAIL.TXT
:done
exit
'''
    (output / 'dosbox.conf').write_text(config)
    started = time.monotonic()
    try:
        with (output / 'dosbox.log').open('w') as log:
            subprocess.run(['dosbox-x', '-fastlaunch', '-nogui', '-conf', str(output / 'dosbox.conf')],
                           stdout=log, stderr=log, check=True, timeout=15,
                           env=dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy'))
    finally:
        stop.set();server.close();thread.join(timeout=1)
    (output / 'transmitted.bin').write_bytes(wire)
    (output / 'received-stimulus.bin').write_bytes(incoming)
    status = (output / 'STATUS.TXT').read_text().strip()
    stdout, stderr = (output / 'STDOUT.BIN').read_bytes(), (output / 'STDERR.BIN').read_bytes()
    returned = (output / 'RETURN.BIN').read_bytes()
    # The authored trigger includes a deterministic trailing span in SWHIT.
    intended_return = b'TRAIL' if case['name'] == 'SWHIT' else b''
    code = {'operand': 7, 'unsupported': 3}.get(expected.get('error'), 0)
    checks = dict(
        dos_parent_pass=(output / 'PASS.TXT').exists() and not (output / 'FAIL.TXT').exists(),
        status_uart_asio=status == f'exit={code} vector=1 mask=1 mcr=1 returned=1 count={len(intended_return)} lease=0 guard=1',
        exact_transmit=bytes(wire) == outgoing,
        exact_stdout=stdout.hex() == expected.get('stdout_hex', ''),
        exact_returned_unread=returned == intended_return,
        stderr=(bool(stderr) if code else stderr == b''),
        peer_no_error=not errors,
        input_delivered=sent.is_set() if incoming else True,
    )
    result = dict(name=case['name'], passed=all(checks.values()), checks=checks,
                  source_sha256=sha(output / 'CASE.ASP'), asx_sha256=sha(output / 'CASE.ASX'),
                  binary_sha256=sha(output / 'ASPECT.EXE'),
                  parent_binary_sha256=sha(output / 'SERTEST.EXE'),
                  config_sha256=sha(output / 'dosbox.conf'),
                  handoff_header_sha256=sha(ROOT / 'src/aspect/serial_handoff.h'),
                  tx_hex=bytes(wire).hex(), input_hex=incoming.hex(),
                  stdout_hex=stdout.hex(), stderr_hex=stderr.hex(), status=status,
                  returned_hex=returned.hex(), descriptor_hex=(output / 'LEASE.BIN').read_bytes().hex(),
                  elapsed_seconds=round(time.monotonic() - started, 3), peer_errors=errors)
    (output / 'checks.json').write_text(json.dumps(result, indent=2) + '\n')
    print(case['name'], 'PASS' if result['passed'] else checks, flush=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runner', type=Path, default=ROOT / 'build/aspect-runner/ASPECT.EXE')
    parser.add_argument('--fixtures', type=Path, default=ROOT / 'standalone/fixtures/aspect_serial_vectors.json')
    parser.add_argument('--case', action='append')
    args = parser.parse_args()
    assert args.runner.is_file() and not args.runner.name.endswith('.analysis.exe')
    fixture = json.loads(args.fixtures.read_text())
    cases = [case for case in fixture['vectors'] if case.get('serial', {}).get('dos_peer', False)]
    if args.case:
        cases = [case for case in cases if case['name'] in args.case]
        assert {case['name'] for case in cases} == set(args.case)
    assert cases
    output = ROOT / 'build/aspect-script-serial-dos'
    driver = build_driver(output)
    binary_sha256 = sha(args.runner)
    runner_manifest = args.runner.parent / 'manifest.json'
    if runner_manifest.exists():
        assert json.loads(runner_manifest.read_text())['binary_sha256'] == binary_sha256
    results = [run(case, args.runner, output, driver) for case in cases]
    assert all(result['binary_sha256'] == binary_sha256 for result in results), 'Runner changed during validation.'
    report = dict(passed=all(result['passed'] for result in results), original_inputs=[],
                  checker_sha256=sha(Path(__file__)), runner_sha256=binary_sha256,
                  runner_manifest_sha256=sha(runner_manifest) if runner_manifest.exists() else None,
                  parent_binary_sha256=sha(driver), parent_source_sha256=sha(output / 'driver.c'),
                  fixture_sha256=sha(args.fixtures), compiler_sha256=sha(ROOT / 'src/aspect/compiler.py'),
                  handoff_header_sha256=sha(ROOT / 'src/aspect/serial_handoff.h'),
                  prior_attempts=['build/aspect-script-serial-dos/failed-parent-DTR-01/reason.json',
                                  'build/aspect-serial-validation-history/runner-6cebb4/scripts/checks.json'],
                  cases=results, scope='Actual source-built DOS ASPECT child, native COM1 and independent TCP peer; '
                  'retained-parent ASIOv1 descriptor, exact unread bytes and restored IRQ/PIC/guards. '
                  'COM1/38400/8N1/flowN only in this script integration. Flow/other ports belong to separate UART diagnostics. '
                  'No peer ASX interpreter, original executable, physical-modem or external-BBS claim.')
    (output / 'checks.json').write_text(json.dumps(report, indent=2) + '\n')
    assert report['passed'], 'Serial DOS script checks failed; per-case evidence retained.'
    print(f'{len(results)} actual DOS serial-script cases passed')


if __name__ == '__main__':
    main()
