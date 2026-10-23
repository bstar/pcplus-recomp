#!/usr/bin/env python3
"""Execute source-built helpers inside a diagnostic terminal after actual startup."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
from check_setup_model import image
from check_startup_import import terminal_expected
from check_modem_import import expected as modem_expected
from directory_fixtures import directory
from test_terminal import SAMPLER

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT / 'build') and not out.exists()
    out.mkdir(parents=True)
    base = ROOT / 'build/terminal-directory-keys-process-bank-session-capture-projection-bound-registers-controls-return-execute-hookprobe'
    manifest = json.loads((base / 'manifest.json').read_text())
    assert manifest['experimental_hook_execute'] and manifest['hook_transaction_probe']
    assert sha(base / 'TERMINAL.EXE') == manifest['binary_sha256']
    helper_source = ROOT / 'standalone/hook_transaction_child.c'
    subprocess.run(['wcl', '-q', '-bt=dos', '-0', '-ms', '-ecc', '-s', '-w4', '-we',
                    '-k8192', '-fm=HOOKCH.map', '-fe=HOOKCH.EXE', str(helper_source),
                    str(base / 'hook_exchange.obj')], cwd=out, check=True)
    raw = bytearray(image())
    struct.pack_into('<HH', raw, 0x4e4, 8, 4)
    struct.pack_into('<H', raw, 0x1bc, 1)
    cases = []
    recipes = [('serial', '@TEST.PRM 19200', None, False),
               ('MODEM', '@TEST.PRM /D:CaseTest:23 38400', None, False),
               ('directory-MODEM', '@TEST.PRM /E:TEST.DIR /N:1', 0, False),
               ('directory-DIRECT', '@TEST.PRM /E:TEST.DIR /N:1', 1, True),
               ('serial-inactive', '@TEST.PRM 19200', None, True)]
    initial_bank = bytearray(128 + i % 127 for i in range(830))
    for i in range(10): initial_bank[20 + i*81:22 + i*81] = bytes([ord('A') + i, 0])
    changed_bank = bytearray(initial_bank)
    for i in range(20): changed_bank[i] ^= 0x3c
    for i in range(10): changed_bank[20 + i*81:23 + i*81] = bytes([ord('H'), ord('0') + i, 0])
    for name, arguments, direct, inactive in recipes:
        folder = out / name
        folder.mkdir()
        source = bytearray(raw)
        if inactive: source[10:0x174] = b'\xff' * (0x174 - 10)
        (folder / 'TEST.PRM').write_bytes(source)
        if direct is not None: (folder / 'TEST.DIR').write_bytes(directory(direct=direct))
        for name_in in ['TERMINAL.EXE', 'HOOKCH.EXE']:
            shutil.copyfile((base if name_in == 'TERMINAL.EXE' else out) / name_in, folder / name_in)
        (folder / 'sampler.asm').write_text(SAMPLER)
        subprocess.run(['nasm', '-fbin', str(folder / 'sampler.asm'), '-o', str(folder / 'SNAP.COM')], check=True)
        (folder / 'dosbox.conf').write_text(f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
cycles=fixed 6000
[mixer]
nosound=true
[autoexec]
@echo off
mount d "{folder}"
d:
SNAP B
TERMINAL {arguments}
if errorlevel 1 goto fail
echo PASS>PASS.TXT
goto done
:fail
echo FAIL>FAIL.TXT
:done
SNAP A
exit
''')
        with (folder / 'dosbox.log').open('w') as log:
            run = subprocess.run(['dosbox-x', '-fastlaunch', '-nogui', '-conf', str(folder / 'dosbox.conf')],
                                 cwd=folder, env=dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy'),
                                 stdout=log, stderr=log, timeout=60)
        assert run.returncode == 0 and (folder / 'PASS.TXT').exists() and not (folder / 'FAIL.TXT').exists(), name
        current = bytearray(source)
        serial = name in ('serial', 'serial-inactive')
        active = name in ('MODEM', 'directory-MODEM')
        struct.pack_into('<H', current, 2, 5 if serial else 6)
        struct.pack_into('<H', current, 0x194, 6 if direct is not None else 4)
        if serial: struct.pack_into('<H', current, 0x1a4, 350)
        changed = bytearray(current)
        for at, value in [(0x1ae, 30), (0x1bc, 0), (0x4e4, 321), (0x4e6, 654), (0x42c, 1)]:
            struct.pack_into('<H', changed, at, value)
        latest = None
        for index in range(10):
            actual = (folder / f'STAGE{index}.BIN').read_bytes()
            if index in (0, 5, 6):
                proposal = bytearray(changed if index == 0 else current)
                if index == 6: struct.pack_into('<H', proposal, 0x1bc, 65535)
                bank = changed_bank if index == 0 else initial_bank
                plan = bytearray(struct.pack('<3H', int(active), 0xe020 if index == 0 else 0, int(index != 5)))
                plan += terminal_expected(proposal)
                if active: plan += modem_expected(proposal)
                else:
                    modem = bytearray(368)
                    struct.pack_into('<H', modem, 14, current[0x1e2])
                    struct.pack_into('<H', modem, 12, struct.unpack_from('<H', current, 0x1e4)[0])
                    struct.pack_into('<H', modem, 366, struct.unpack_from('<H', current, 0x1a4)[0])
                    plan += modem
                plan += struct.pack('<H', int(index == 0)) + b'.\0'.ljust(64, b'\0')
                plan += struct.pack('<3H', int(index != 0), 321 if index == 0 else 8, 654 if index == 0 else 4)
                latest = bank + proposal + plan
            assert actual == latest, (name, index, [(i,a,b) for i,(a,b) in enumerate(zip(actual, latest)) if a != b][:10])
        results = (folder / 'RESULTS.BIN').read_bytes()
        assert len(results) == 200
        words = [struct.unpack_from('<10H', results, i*20) for i in range(10)]
        assert [r[0] for r in words] == [0,5,7,7,6,0,0,7,7,5]
        assert words[1][1] == 5 and words[2][6:] == (6,0,2,0x200)
        assert words[3][6] == 5 and words[4][4] == 23
        assert words[7][6] == (7 if active else 6) and words[8][6] == 2
        assert words[9][1] == 4 and words[9][2] != 0
        assert (folder / 'RBFORE.BIN').read_bytes() == (folder / 'RBAGAIN.BIN').read_bytes() == initial_bank
        assert (folder / 'BASE0.BIN').read_bytes() == (folder / 'BASE1.BIN').read_bytes()
        assert (folder / 'BASE0.BIN').read_bytes()[8:] == source
        assert (folder / 'TEST.PRM').read_bytes() == source
        assert (folder / 'BEFORE.BIN').read_bytes() == (folder / 'AFTER.BIN').read_bytes()
        assert len((folder / 'BEFORE.BIN').read_bytes()) == 42
        assert (folder / 'DIAG.BIN').read_bytes() == b'\0\0'
        assert (folder / 'STACK.BIN').read_bytes() == b'\xa5' * 256
        assert sha(folder / 'TERMINAL.EXE') == manifest['binary_sha256']
        cases.append(dict(case=name, passed=True, helpers=10, statuses=[r[0] for r in words],
                          artifacts={p.name:sha(p) for p in folder.iterdir() if p.is_file()}))
        print('PASS8086', name, '10 helper attempts, exact proposals and retained session', flush=True)
    sources = dict(manifest['sources'])
    for name in ['standalone/test_hook_transaction_dos.py', 'standalone/hook_transaction_child.c',
                 'standalone/check_setup_model.py', 'standalone/check_startup_import.py',
                 'standalone/check_modem_import.py', 'standalone/directory_fixtures.py', 'standalone/test_terminal.py']:
        sources[name] = sha(ROOT / name)
    for name, digest in sources.items(): assert sha(ROOT / name) == digest, name
    rebuild = out / 'rebuild'
    rebuild.mkdir()
    subprocess.run(['wcl', '-q', '-bt=dos', '-0', '-ms', '-ecc', '-s', '-w4', '-we',
                    '-k8192', '-fm=HOOKCH.map', '-fe=HOOKCH.EXE', str(helper_source),
                    str(base / 'hook_exchange.obj')], cwd=rebuild, check=True)
    assert sha(rebuild / 'HOOKCH.EXE') == sha(out / 'HOOKCH.EXE')
    report = dict(passed=True, cases=cases, sources=sources, binary_sha256=manifest['binary_sha256'],
                  helper_sha256=sha(out / 'HOOKCH.EXE'), original_inputs=[],
                  scope='Actual source-built terminal startup and owned helper EXEC on8086. Accepted register bank '
                  'preserved without per-script reset, supported proposals validated, nonzero/missing/invalid child '
                  'returns rejected, pending proposal busy/discard, exact full proposal and unchanged baseline/registers/files/hardware. '
                  'Diagnostic before UART/mouse acquisition; no online foreground routing or settings adoption acceptance.')
    (out / 'result.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__': main()
