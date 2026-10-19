#!/usr/bin/env python3
"""Independent actual-DOS receive command tests with timed raw UART peer input.

Expectations below are authored before execution from native contracts and the
explicit maintained81-byte RGET guard; no original executable is a build input.
"""
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
from test_aspect_script_serial_dos import ROOT, build_driver, sha

sys.path.insert(0, str(ROOT / 'src/aspect'))
from compiler import compile_source


def definitions():
    result = []

    def add(name, declarations, body, output, data=b'', *, delay=0.1, tail=b'',
            error=0, escape=False, helper='', minimum=0, policy=False):
        source = declarations + '\nproc main\n' + body + '\nendproc\n' + helper
        result.append(dict(name=name, source=source.replace('\n', '\r\n'),
                           stdout=output, input=data, delay=delay, returned=tail,
                           exit=error, escape=escape, minimum_seconds=minimum,
                           maintained_guard=policy))

    scalar = 'integer value\nstring displaybuf'
    show = '\nitoa value displaybuf\nmessage displaybuf'
    add('GCEMPTY', scalar, 'comgetc value' + show, b'-1\r\n')
    add('GDLATE', scalar, 'transmit "READY^M"\ncomgetcd value' + show,
        b'255\r\n', b'\xff', delay=0.2)
    add('GDEMPTY', scalar, 'transmit "READY^M"\ncomgetcd value' + show,
        b'-1\r\n', minimum=1.0)
    add('GCBINARY', scalar, 'transmit "READY^M"\npause 1\ncomgetc value' + show +
        '\ncomgetc value' + show + '\ncomgetc value' + show,
        b'0\r\n128\r\n255\r\n', bytes.fromhex('0080ff'))
    add('RGBINARY', 'integer value\nstring buffer,displaybuf',
        'transmit "READY^M"\nrget buffer 5 3\npause 1\nmessage buffer\n'
        'strpeek buffer 1 value' + show + '\nstrpeek buffer 2 value' + show +
        '\nvalue = COMDATA' + show,
        b'A\r\n0\r\n255\r\n5\r\n', bytes.fromhex('4100ff0d') + b'TRAIL', tail=b'TRAIL')
    add('RGPARM', '', 'call worker with "OLD"', b'NEW\r\n', b'NEW\r',
        helper='proc worker\nstrparm buffer\ntransmit "READY^M"\nrget buffer 5 3\nmessage buffer\nendproc\n')
    for name, timeout in [('RGTIME', 1), ('RGZERO', 0)]:
        add(name, 'integer value\nstring buffer,displaybuf',
            f'transmit "READY^M"\nbuffer = "OLD"\nrget buffer 5 {timeout}\nmessage buffer\n'
            'value = failure' + show, b'\r\n1\r\n')
    for name, command, value in [('WQQUIET', 'waitquiet 1 3', 0),
                                 ('WQSHORT', 'waitquiet 2 1', 1),
                                 ('WQFOREV', 'waitquiet 2 FOREVER', 0)]:
        add(name, scalar, 'transmit "READY^M"\n' + command + '\nvalue = failure' + show,
            str(value).encode() + b'\r\n', b'A')
    add('RGCANCEL', 'string buffer', 'transmit "READY^M"\nrget buffer 80 30\nmessage "UNREACHABLE"',
        b'', error=13, escape=True)
    add('RGZERO80', 'string buffer', 'transmit "READY^M"\nrget buffer 0 3\nmessage buffer',
        b'A' * 80 + b'\r\n', b'A' * 80 + b'\r')
    add('RGGUARD', 'string buffer', 'transmit "READY^M"\nrget buffer 0 3\nmessage "UNREACHABLE"',
        b'', b'A' * 81, error=7, policy=True)
    add('RGRANGE', 'string buffer', 'transmit "READY^M"\nrget buffer 81 1\nmessage "UNREACHABLE"',
        b'', error=7)
    return result


def run(case, binary, driver, output):
    folder = output / case['name']
    folder.mkdir(parents=True, exist_ok=True)
    for name in ('STATUS.TXT', 'STDOUT.BIN', 'STDERR.BIN', 'RETURN.BIN', 'LEASE.BIN'):
        (folder / name).unlink(missing_ok=True)
    shutil.copyfile(binary, folder / 'ASPECT.EXE')
    shutil.copyfile(driver, folder / 'SERTEST.EXE')
    (folder / 'CASE.ASP').write_bytes(case['source'].encode('cp437'))
    (folder / 'CASE.ASX').write_bytes(compile_source(case['source']))
    tx, errors = bytearray(), []
    stop, sent = threading.Event(), threading.Event()
    server = socket.socket();server.bind(('127.0.0.1', 0));server.listen(1);server.settimeout(12)
    intended_tx = b'READY\r' if 'transmit' in case['source'] else b''

    def peer():
        ready_at = None
        try:
            connection, _ = server.accept()
            with connection:
                connection.settimeout(0.02)
                connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                while not stop.is_set():
                    if ready_at is None and intended_tx and intended_tx in tx:
                        ready_at = time.monotonic()
                    if (case['input'] and not sent.is_set() and ready_at is not None and
                            time.monotonic() - ready_at >= case['delay']):
                        connection.sendall(case['input']);sent.set()
                    try:
                        chunk = connection.recv(4096)
                        if not chunk:
                            break
                        tx.extend(chunk)
                    except socket.timeout:
                        pass
        except OSError as error:
            if not stop.is_set():
                errors.append(str(error))

    thread = threading.Thread(target=peer, daemon=True);thread.start()
    cancel = 'ADDKEY p600 escape\n' if case['escape'] else ''
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
mount c "{folder}"
c:
{cancel}SERTEST
exit
'''
    (folder / 'dosbox.conf').write_text(config)
    started = time.monotonic()
    try:
        with (folder / 'dosbox.log').open('w') as log:
            subprocess.run(['dosbox-x', '-fastlaunch', '-nogui', '-conf', str(folder / 'dosbox.conf')],
                           stdout=log, stderr=log, check=True, timeout=15,
                           env=dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy'))
    finally:
        stop.set();server.close();thread.join(timeout=1)
    elapsed = time.monotonic() - started
    returned = (folder / 'RETURN.BIN').read_bytes()
    stdout, stderr = (folder / 'STDOUT.BIN').read_bytes(), (folder / 'STDERR.BIN').read_bytes()
    status = (folder / 'STATUS.TXT').read_text().strip()
    checks = dict(
        exact_child_status_asio_and_uart=status == f'exit={case["exit"]} vector=1 mask=1 mcr=1 returned=1 count={len(case["returned"])} lease=0 guard=1',
        exact_stdout=stdout == case['stdout'],
        exact_tx=bytes(tx) == intended_tx,
        exact_unread=returned == case['returned'],
        stderr=bool(stderr) if case['exit'] else stderr == b'',
        native_error_contract=(b'native 1' in stderr if case['name'] == 'RGRANGE'
                               else b'native ' not in stderr if case['maintained_guard'] else True),
        input_sent=sent.is_set() if case['input'] else True,
        no_peer_error=not errors,
        minimum_delay=elapsed >= case['minimum_seconds'],
    )
    (folder / 'transmitted.bin').write_bytes(tx)
    (folder / 'input.bin').write_bytes(case['input'])
    report = dict(name=case['name'], passed=all(checks.values()), checks=checks,
                  source_sha256=sha(folder / 'CASE.ASP'), asx_sha256=sha(folder / 'CASE.ASX'),
                  runner_sha256=sha(folder / 'ASPECT.EXE'), parent_sha256=sha(folder / 'SERTEST.EXE'),
                  config_sha256=sha(folder / 'dosbox.conf'), status=status, stdout_hex=stdout.hex(),
                  stderr_hex=stderr.hex(), tx_hex=bytes(tx).hex(), input_hex=case['input'].hex(),
                  returned_hex=returned.hex(), descriptor_hex=(folder / 'LEASE.BIN').read_bytes().hex(),
                  maintained_guard=case['maintained_guard'], elapsed_seconds=round(elapsed, 3), peer_errors=errors)
    (folder / 'checks.json').write_text(json.dumps(report, indent=2) + '\n')
    print(case['name'], 'PASS' if report['passed'] else checks, flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runner', type=Path, default=ROOT / 'build/aspect-runner/ASPECT.EXE')
    parser.add_argument('--case', action='append')
    args = parser.parse_args()
    assert args.runner.is_file() and not args.runner.name.lower().endswith('.analysis.exe')
    cases = definitions()
    if args.case:
        cases = [case for case in cases if case['name'] in args.case]
        assert {case['name'] for case in cases} == set(args.case)
    output = ROOT / 'build/aspect-script-receive-dos'
    driver = build_driver(output)
    binary_hash = sha(args.runner)
    manifest = args.runner.parent / 'manifest.json'
    assert json.loads(manifest.read_text())['binary_sha256'] == binary_hash
    results = [run(case, args.runner, driver, output) for case in cases]
    assert all(case['runner_sha256'] == binary_hash for case in results)
    report = dict(passed=all(case['passed'] for case in results), original_inputs=[],
                  checker_sha256=sha(Path(__file__)), compiler_sha256=sha(ROOT / 'src/aspect/compiler.py'),
                  shared_parent_checker_sha256=sha(ROOT / 'standalone/test_aspect_script_serial_dos.py'),
                  parent_source_sha256=sha(output / 'driver.c'), parent_binary_sha256=sha(driver),
                  handoff_header_sha256=sha(ROOT / 'src/aspect/serial_handoff.h'),
                  runner_sha256=binary_hash, runner_manifest_sha256=sha(manifest), cases=results,
                  scope='Actual DOS ASPECT child with independent timed raw UART peer on COM1/38400/8N1/flowN. '
                  'Default suppressed COMbyte echo, late RX/FFFF, binary/string parameters, timeout/quiet/FOREVER, '
                  'Escape, raw ASIO tail and explicit maintained81-byte guard. Native max0 short-input quirk retained; '
                  'guard failure is a maintained safety boundary, not original native range semantics. '
                  'No originals, terminal renderer/XLT/capture/event dispatch, BBS or physical modem claim.')
    (output / 'checks.json').write_text(json.dumps(report, indent=2) + '\n')
    assert report['passed'], 'Receive DOS checks failed; every attempted case retained.'
    print(f'{len(results)} actual DOS receive cases passed')


if __name__ == '__main__':
    main()
