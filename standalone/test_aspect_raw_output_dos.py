#!/usr/bin/env python3
"""DOS-compile TRANSMITRAW and run the production CLI through a real UART ISR.

Owned loopback fixtures only. No device/VM callbacks are replaced; DOSBox-X
provides the UART. This does not implement or accept a recorder/UI owner.
"""
import argparse
import hashlib
import json
import os
import shutil
import socket
import subprocess
import sys
import threading
from pathlib import Path
from test_terminal import ROOT, SAMPLER

sys.path.insert(0, str(ROOT / 'src/aspect'))
from compiler import compile_source


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    assert output.is_relative_to(ROOT / 'build') and not output.exists()
    output.mkdir(parents=True)
    frozen = {}
    for directory, binary in [('aspect-runner', 'ASPECT.EXE'), ('aspect-compiler-dos', 'ASPCOMP.EXE')]:
        base = ROOT / 'build' / directory
        manifest = json.loads((base / 'manifest.json').read_text())
        assert not manifest['original_inputs'] and sha(base / binary) == manifest['binary_sha256']
        for name, digest in manifest['sources'].items():
            assert sha(ROOT / name) == digest, name
            assert name not in frozen or frozen[name] == digest, name
            frozen[name] = digest
        frozen[str((base / binary).relative_to(ROOT))] = sha(base / binary)
        frozen[str((base / 'manifest.json').relative_to(ROOT))] = sha(base / 'manifest.json')
        shutil.copy2(base / binary, output / binary)
    for path in [Path(__file__).resolve(), ROOT / 'standalone/test_terminal.py', ROOT / 'src/aspect/compiler.py']:
        frozen[str(path.relative_to(ROOT))] = sha(path)
    for name, digest in frozen.items():
        target = output / 'frozen-source' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, target)
        assert sha(target) == digest
    (output / 'start.json').write_text(json.dumps(dict(inputs=frozen), indent=2) + '\n')
    (output / 'sampler.asm').write_text(SAMPLER)
    (output / 'setup.asm').write_text('BITS 16\nCPU 8086\nORG 100h\nmov dx,3fbh\nmov al,80h\nout dx,al\nmov dx,3f8h\nmov al,12\nout dx,al\ninc dx\nxor al,al\nout dx,al\nmov dx,3fbh\nmov al,3\nout dx,al\nmov dx,3fch\nmov al,1\nout dx,al\nmov ax,4c00h\nint 21h\n')
    for source, binary in [('sampler', 'SNAP'), ('setup', 'SETUP')]:
        subprocess.run(['nasm', '-fbin', str(output / (source + '.asm')), '-o', str(output / (binary + '.COM'))], check=True)
    driver = r'''
#include <stdio.h>
#include <dos.h>
#include <process.h>
int main(int argc,char **argv){
 int compiled,result;void (__interrupt __far *before)(void);FILE *status;
 (void)argv;
 if(!freopen("ERROR.TXT","wb",stderr))return 90;
 before=_dos_getvect(0);
 compiled=spawnl(P_WAIT,"ASPCOMP.EXE","ASPCOMP","CASE.ASP","CASE.ASX",(char *)0);
 if(compiled)return 91;
 result=argc>1?spawnl(P_WAIT,"ASPECT.EXE","ASPECT","CASE.ASX","/S1:0003:03:N",(char *)0):
               spawnl(P_WAIT,"ASPECT.EXE","ASPECT","CASE.ASX",(char *)0);
 status=fopen("STATUS.TXT","w");if(!status)return 92;
 fprintf(status,"%d %u\n",result,_dos_getvect(0)==before);fclose(status);
 return 0;
}
'''
    (output / 'driver.c').write_text(driver)
    subprocess.run(['wcl', '-q', '-bt=dos', '-0', '-ms', '-ecc', '-s', '-w4', '-we', '-fe=CHECK.EXE', str(output / 'driver.c')], cwd=output, check=True)
    def raw(data):
        return ''.join('transmitraw "' + data[at:at+40].hex() + '"\r\n' for at in range(0, len(data), 40))
    cases = [
        ('all-octets', 'set pausechar 65\r\nset duplex half\r\n' + raw(bytes(range(256))), bytes(range(256)), 0, True),
        ('long-stream', raw(bytes(range(256)) * 8), bytes(range(256)) * 8, 0, True),
        ('mixed-legacy', 'string value\r\nvalue="00225e7eff"\r\ntransmitraw value\r\ntransmitraw ""\r\ntransmit "AT^M"\r\n', bytes.fromhex('00225e7eff') + b'AT\r', 0, True),
        ('invalid-late', 'transmitraw "' + '41' * 39 + 'g0"\r\n', b'', 7, True),
        ('invalid-odd', 'transmitraw "001"\r\n', b'', 7, True),
        ('no-attachment', 'transmitraw "41"\r\n', b'', 3, False),
    ]
    results = []
    for name, body, expected, error, attached in cases:
        folder = output / name
        folder.mkdir()
        for binary in ('ASPECT.EXE', 'ASPCOMP.EXE', 'CHECK.EXE', 'SETUP.COM', 'SNAP.COM'):
            shutil.copy2(output / binary, folder / binary)
        source = 'proc main\r\n' + body + 'endproc\r\n'
        (folder / 'CASE.ASP').write_bytes(source.encode('cp437'))
        server = socket.socket()
        server.bind(('127.0.0.1', 0))
        server.listen(1)
        server.settimeout(20)
        wire = bytearray()
        errors = []
        def receive():
            try:
                connection, _ = server.accept()
                with connection:
                    connection.settimeout(20)
                    while True:
                        data = connection.recv(4096)
                        if not data:
                            break
                        wire.extend(data)
            except (OSError, TimeoutError) as exc:
                errors.append(repr(exc))
            finally:
                server.close()
        thread = threading.Thread(target=receive, daemon=True)
        thread.start()
        config = f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
cycles=fixed 6000
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
mount d "{folder}"
d:
SETUP
SNAP B
CHECK {'attached' if attached else ''} >RESULT.TXT
if errorlevel 1 goto failed
echo PASS>PASS.TXT
goto finish
:failed
echo FAIL>FAIL.TXT
:finish
SNAP A
exit
'''
        (folder / 'dosbox.conf').write_text(config)
        with (folder / 'dosbox.log').open('w') as log:
            process = subprocess.run(['dosbox-x', '-fastlaunch', '-nogui', '-conf', str(folder / 'dosbox.conf')],
                                     env=dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy'),
                                     stdout=log, stderr=log, timeout=45)
        thread.join(3)
        assert not thread.is_alive(), 'Loopback receiver did not exit'
        (folder / 'wire.bin').write_bytes(wire)
        status = (folder / 'STATUS.TXT').read_text().split()
        checks = dict(DOS_normal_exit=process.returncode == 0 and (folder / 'PASS.TXT').is_file() and not (folder / 'FAIL.TXT').exists(),
                      exact_UART_bytes=bytes(wire) == expected, no_peer_errors=not errors,
                      expected_runtime_status=status == [str(error), '1'],
                      actual_DOS_compile_byte_identical=(folder / 'CASE.ASX').read_bytes() == compile_source(source),
                      hardware_restored=(folder / 'BEFORE.BIN').read_bytes() == (folder / 'AFTER.BIN').read_bytes() and (folder / 'BEFORE.BIN').stat().st_size == 42,
                      expected_error_output=(b'ASPECT:' in (folder / 'ERROR.TXT').read_bytes()) if error else not (folder / 'ERROR.TXT').read_bytes())
        for binary in ('ASPECT.EXE', 'ASPCOMP.EXE'):
            checks[binary + '_unchanged'] = sha(folder / binary) == sha(output / binary)
        result = dict(passed=all(checks.values()), case=name, checks=checks, peer_errors=errors,
                      expected_hex=expected.hex(), actual_hex=bytes(wire).hex())
        (folder / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
        results.append(result)
        print(json.dumps(dict(case=name, passed=result['passed'], bytes=len(wire))), flush=True)
    for name, digest in frozen.items():
        assert sha(ROOT / name) == sha(output / 'frozen-source' / name) == digest, name
    result = dict(passed=all(case['passed'] for case in results), cases=results, inputs=frozen,
                  captures_sha256={str(path.relative_to(output)): sha(path) for path in output.rglob('*')
                                  if path.is_file() and not path.is_relative_to(output / 'frozen-source')}, scope=__doc__)
    with (output / 'result.json').open('x') as stream:
        stream.write(json.dumps(result, indent=2) + '\n')
    assert result['passed'], [(case['case'], case['checks']) for case in results if not case['passed']]


if __name__ == '__main__':
    main()
