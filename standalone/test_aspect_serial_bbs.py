#!/usr/bin/env python3
"""Read-only ASPECT greeting smoke against the two existing owned local BBSes.

Reuses the existing Hayes/Telnet modem model. No login, posting, account changes,
ANSI reply fabrication, or BBS reconfiguration is performed.
"""
import argparse
import asyncio
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from test_aspect_script_serial_dos import ROOT, build_driver, sha

sys.path.insert(0, str(ROOT / 'lab/bbs'))
from modem import Modem
sys.path.insert(0, str(ROOT / 'src/aspect'))
from compiler import compile_source

TARGETS = {
    'synchronet': (23231, 'Synchronet', 'SYNC GREETING', 'sbbs'),
    'enigma': (23233, 'enigma-bbs/', 'ENIGMA GREETING', 'MainThread'),
}


async def run(name, binary, driver,root=None):
    port, needle, expected, process_name = TARGETS[name]
    listener = subprocess.run(['ss', '-ltnp', f'sport = :{port}'],
                              check=True, text=True, capture_output=True).stdout
    assert f'127.0.0.1:{port}' in listener and f'"{process_name}"' in listener, listener
    output = (root or ROOT / 'build/aspect-serial-bbs') / name
    output.mkdir(parents=True, exist_ok=True)
    for item in ('STATUS.TXT', 'STDOUT.BIN', 'STDERR.BIN', 'RETURN.BIN', 'LEASE.BIN'):
        (output / item).unlink(missing_ok=True)
    shutil.copyfile(binary, output / 'ASPECT.EXE')
    shutil.copyfile(driver, output / 'SERTEST.EXE')
    source = (f'proc main\r\ntransmit "ATDLAB.LOCAL:{port}^M"\r\n'
              'waitfor "CONNECT" 5\r\nif waitfor\r\n'
              f'waitfor "{needle}" 8\r\nif waitfor\r\n'
              f'transmit "^M"\r\nmessage "{expected}"\r\n'
              'else\r\nmessage "NO GREETING"\r\nendif\r\n'
              'else\r\nmessage "NO CARRIER"\r\nendif\r\nendproc\r\n')
    (output / 'CASE.ASP').write_bytes(source.encode('cp437'))
    (output / 'CASE.ASX').write_bytes(compile_source(source))
    modem = Modem('127.0.0.1', port, output, soft=False, baud=38400)
    server = await asyncio.start_server(modem.accept, '127.0.0.1', 0)
    endpoint = server.sockets[0].getsockname()[1]
    config = f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
cycles=max
[mixer]
nosound=true
[serial]
serial1=nullmodem server:127.0.0.1 port:{endpoint} transparent:1 rxdelay:200 txdelay:1
serial2=disabled
serial3=disabled
serial4=disabled
[autoexec]
@echo off
mount c "{output}"
c:
SERTEST
exit
'''
    (output / 'dosbox.conf').write_text(config)
    try:
        with (output / 'dosbox.log').open('w') as log:
            child = await asyncio.create_subprocess_exec(
                'dosbox-x', '-fastlaunch', '-nogui', '-conf', str(output / 'dosbox.conf'),
                stdout=log, stderr=log,
                env=dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy'))
            try:
                result = await asyncio.wait_for(child.wait(), timeout=20)
            except asyncio.TimeoutError:
                child.terminate()
                await child.wait()
                raise
        assert result == 0
        await asyncio.wait_for(modem.done.wait(), timeout=3)
    finally:
        server.close()
        await server.wait_closed()
        modem.save()
    status = (output / 'STATUS.TXT').read_text().strip()
    stdout, stderr = (output / 'STDOUT.BIN').read_bytes(), (output / 'STDERR.BIN').read_bytes()
    tx = bytes(modem.keyboard)
    intended = f'ATDLAB.LOCAL:{port}\r\r'.encode()
    returned = (output / 'RETURN.BIN').read_bytes()
    marker_end = bytes(modem.serial_out).lower().find(needle.encode().lower()) + len(needle)
    remaining = bytes(modem.serial_out)[marker_end:]
    checks = dict(
        actual_child_and_uart_restoration=status == f'exit=0 vector=1 mask=1 mcr=1 returned=1 count={len(returned)} lease=0 guard=1',
        exact_unread_prefix=remaining.startswith(returned),
        greeting_status_stdout=stdout == expected.encode() + b'\r\n',
        clean_stderr=stderr == b'',
        exact_dial_and_single_newline=tx == intended,
        actual_bbs_marker=needle.encode().lower() in bytes(modem.display).lower(),
        actual_bbs_connection=any(event['kind'] == 'bbs-connected' for event in modem.events),
        telnet_negotiated=bool(modem.codec.events),
    )
    report = dict(name=name, passed=all(checks.values()), checks=checks,
                  endpoint=f'127.0.0.1:{port}', listener=listener,
                  source_sha256=sha(output / 'CASE.ASP'), asx_sha256=sha(output / 'CASE.ASX'),
                  runner_sha256=sha(output / 'ASPECT.EXE'),
                  parent_binary_sha256=sha(output / 'SERTEST.EXE'),
                  config_sha256=sha(output / 'dosbox.conf'),
                  handoff_header_sha256=sha(ROOT / 'src/aspect/serial_handoff.h'),
                  status=status, stdout_hex=stdout.hex(),
                  stderr_hex=stderr.hex(), tx_hex=tx.hex(),
                  returned_hex=returned.hex(), descriptor_hex=(output / 'LEASE.BIN').read_bytes().hex(),
                  files={item: sha(output / item) for item in ('bbs-wire.bin', 'bbs-sent.bin',
                         'display.bin', 'serial-received.bin', 'serial-sent.bin', 'modem.json')})
    (output / 'checks.json').write_text(json.dumps(report, indent=2) + '\n')
    print(name, 'PASS' if report['passed'] else checks)
    return report


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runner', type=Path, default=ROOT / 'build/aspect-runner/ASPECT.EXE')
    parser.add_argument('--bbs', choices=TARGETS, action='append')
    parser.add_argument('--output',type=Path)
    args = parser.parse_args()
    assert args.runner.is_file() and not args.runner.name.endswith('.analysis.exe')
    output = args.output.resolve() if args.output else ROOT / 'build/aspect-serial-bbs'
    assert output.is_relative_to(ROOT/'build')
    if args.output:assert not output.exists()
    output.mkdir(parents=True, exist_ok=True)
    driver = build_driver(output)
    binary_sha256 = sha(args.runner)
    runner_manifest = args.runner.parent / 'manifest.json'
    if runner_manifest.exists():
        assert json.loads(runner_manifest.read_text())['binary_sha256'] == binary_sha256
    results = [await run(name, args.runner, driver,output)
               for name in (args.bbs or TARGETS)]
    assert all(result['runner_sha256'] == binary_sha256 for result in results), 'Runner changed during validation.'
    report = dict(passed=all(result['passed'] for result in results), original_inputs=[],
                  checker_sha256=sha(Path(__file__)), driver_checker_sha256=sha(ROOT / 'standalone/test_aspect_script_serial_dos.py'),
                  modem_source_sha256=sha(ROOT / 'lab/bbs/modem.py'), runner_sha256=binary_sha256,
                  runner_manifest_sha256=sha(runner_manifest) if runner_manifest.exists() else None,
                  parent_binary_sha256=sha(driver), parent_source_sha256=sha(output / 'driver.c'),
                  handoff_header_sha256=sha(ROOT / 'src/aspect/serial_handoff.h'),
                  compiler_sha256=sha(ROOT / 'src/aspect/compiler.py'), cases=results,
                  prior_success='build/aspect-serial-validation-history/runner-6cebb4/bbs/checks.json',
                  scope='Read-only local stock BBS greetings through existing Hayes/Telnet modem, actual DOS '
                  'ASPECT.EXE native COM1/38400/8N1/flowN and source-built scripts. Exact dial and one CR only; no login/posting/menu navigation, '
                  'terminal renderer or fabricated ANSI replies, physical WiFi modem, or complete application claim.')
    (output / 'checks.json').write_text(json.dumps(report, indent=2) + '\n')
    assert report['passed'], 'Retained BBS greeting checks failed.'


if __name__ == '__main__':
    asyncio.run(main())
