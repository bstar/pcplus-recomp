#!/usr/bin/env python3
"""Actual DOS8086 custom IRQ RX/TX and restored hardware, diagnostic and full VM."""
import argparse
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import threading

from package_special_edition import ROOT, sha
from test_terminal import SAMPLER
sys.path.insert(0, str(ROOT / 'src/aspect'))
from compiler import compile_source


def run(out, port, irq, flow='N', *, full=False, legacy=False, wrong=False):
    out.mkdir(parents=True, exist_ok=False)
    product = ROOT / ('build/aspect-register-parent-custom-irq/ASPECT.EXE' if full else
                      'build/aspect-serial-custom-irq/SERIAL.EXE')
    manifest = json.loads((product.parent / 'manifest.json').read_text())
    assert sha(product) == manifest['binary_sha256']
    for name, digest in manifest['sources'].items():
        assert sha(ROOT / name) == digest, name
    shutil.copyfile(product, out / product.name)
    source = ('proc main\ntransmit "D"\nwaitfor "READY" 4\n'
              'if waitfor\ntransmit "R"\nendif\nendproc\n')
    (out / 'CASE.ASP').write_text(source)
    (out / 'CASE.ASX').write_bytes(compile_source(source))
    base = [0x3f8, 0x2f8, 0x3e8, 0x2e8][port - 1]
    sampler = SAMPLER
    for offset in (0, 1, 3, 4):
        sampler = sampler.replace(hex(0x3f8 + offset), hex(base + offset))
    (out / 'snap.asm').write_text(sampler)
    (out / 'setup.asm').write_text(f'''BITS 16
CPU 8086
ORG 0x100
mov dx,{base + 3}
mov al,0x80
out dx,al
mov dx,{base}
mov al,12
out dx,al
inc dx
xor al,al
out dx,al
mov dx,{base + 3}
mov al,3
out dx,al
mov dx,{base + 4}
mov al,1
out dx,al
mov ax,0x4c00
int 0x21
''')
    for stem in ('snap', 'setup'):
        subprocess.run(['nasm', '-fbin', str(out / (stem + '.asm')), '-o', str(out / (stem + '.COM'))], check=True)
    server = socket.socket()
    server.bind(('127.0.0.1', 0))
    server.listen(1)
    server.settimeout(10)
    wire = bytearray()
    errors = []

    def peer():
        try:
            conn, _ = server.accept()
            with conn:
                conn.settimeout(10)
                sent = False
                while True:
                    data = conn.recv(4096)
                    if not data:
                        break
                    wire.extend(data)
                    if b'D' in wire and not sent:
                        conn.sendall(b'READY' if full else b'\x00\x1a\x80\xff')
                        sent = True
        except OSError as error:
            errors.append(str(error))

    thread = threading.Thread(target=peer, daemon=True)
    thread.start()
    physical_irq = irq
    lease_irq = (4 if port in (1, 3) else 3) if wrong else irq
    flag = f'/S{port}:0003:03:{flow}' + ('' if legacy else f':I{lease_irq}')
    command = ('ASPECT CASE.ASX ' if full else 'SERIAL ') + flag
    serial = '\n'.join(f'serial{i}=' + (f'nullmodem server:127.0.0.1 port:{server.getsockname()[1]} '
                        f'transparent:1 irq:{physical_irq} rxdelay:200 txdelay:1' if i == port else 'disabled')
                       for i in range(1, 5))
    expected = 23 if wrong else 0
    config = f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
cycles=fixed 6000
[mixer]
nosound=true
[sblaster]
sbtype=none
[serial]
{serial}
[autoexec]
@echo off
mount d "{out}"
d:
SETUP
SNAP B
{command} >RESULT.TXT
if errorlevel {expected + 1} goto failed
if errorlevel {expected} goto passed
goto failed
:passed
echo PASS>PASS.TXT
goto done
:failed
echo FAIL>FAIL.TXT
:done
SNAP A
exit
'''
    (out / 'dosbox.conf').write_text(config)
    try:
        with (out / 'dosbox.log').open('w') as log:
            proc = subprocess.run(['dosbox-x', '-fastlaunch', '-nogui', '-conf', str(out / 'dosbox.conf')],
                                  cwd=out, stdout=log, stderr=log, timeout=18,
                                  env=dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy'))
    finally:
        thread.join(1)
        server.close()
    (out / 'serial.bin').write_bytes(wire)
    assert proc.returncode == 0 and (out / 'PASS.TXT').exists() and not (out / 'FAIL.TXT').exists()
    before, after = [(out / f'{name}.BIN').read_bytes() for name in ('BEFORE', 'AFTER')]
    assert len(before) == 42 and before == after
    expected_wire = (b'\x11' if flow in ('S', 'B') else b'') + b'D' + (b'' if wrong else b'R') + (b'\x13' if flow in ('S', 'B') else b'')
    assert bytes(wire) == expected_wire, (out.name, wire, expected_wire)
    assert not errors, errors
    if not full:
        assert (out / 'RESULT.TXT').read_bytes() == (b'status=23 count=0\r\n' if wrong else b'status=0 count=0\r\n')
    sources = dict(manifest['sources'])
    for name in ('standalone/test_aspect_custom_irq_dos.py', 'standalone/test_terminal.py',
                 'standalone/package_special_edition.py', 'src/aspect/compiler.py'):
        sources[name] = sha(ROOT / name)
    result = dict(passed=True, cpu='8086', port=port, physical_irq=physical_irq, lease_irq=lease_irq,
                  full_VM=full, legacy_option=legacy, flow=flow, deliberate_mismatch=wrong,
                  binary_sha256=sha(product), wire_hex=wire.hex(), sources=sources,
                  expected_DOS_exit=expected,
                  artifacts={p.name: sha(p) for p in out.iterdir() if p.is_file()},
                  scope=__doc__ + ' Nullmodem synthetic peer. No parent PRM/live setup or physical modem claim.')
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print('PASS', out.name, flush=True)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT / 'build') and not out.exists()
    out.mkdir(parents=True)
    cases = []
    for port in range(1, 5):
        for irq in (3, 4, 5, 7):
            cases.append(run(out / f'diagnostic-com{port}-irq{irq}', port, irq))
    for port, irq, flow in [(1, 5, 'S'), (2, 7, 'H'), (3, 5, 'B'), (4, 7, 'B')]:
        cases.append(run(out / f'diagnostic-com{port}-irq{irq}-{flow}', port, irq, flow))
    for port, irq in [(1, 4), (2, 3)]:
        cases.append(run(out / f'legacy-com{port}', port, irq, legacy=True))
    for port, irq in [(1, 5), (2, 7)]:
        cases.append(run(out / f'mismatch-com{port}', port, irq, wrong=True))
    for port, irq, flow in [(1, 5, 'N'), (2, 7, 'H'), (3, 5, 'S'), (4, 7, 'B'), (1, 4, 'N')]:
        cases.append(run(out / f'full-com{port}-irq{irq}-{flow}', port, irq, flow, full=True, legacy=irq == 4))
    result = dict(passed=True, cases=cases, original_inputs=[], scope=__doc__)
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    main()
