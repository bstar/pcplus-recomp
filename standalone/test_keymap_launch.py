#!/usr/bin/env python3
"""Check native keymap caller frames, source reproduction and linked8086 DOS ABI.

All six callees are explicit models. Optional original input is SHA-pinned;
no helper, settings file, real video or PROGRAM child is executed by the model.
"""
import argparse
import hashlib
import itertools
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
from unicorn import Uc, UC_ARCH_X86, UC_MODE_16, UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_AX, UC_X86_REG_BP, UC_X86_REG_CS, UC_X86_REG_DS, UC_X86_REG_DX, UC_X86_REG_ES, UC_X86_REG_IP, UC_X86_REG_SI, UC_X86_REG_SP, UC_X86_REG_SS

ROOT = Path(__file__).resolve().parents[1]
DATA = 0x40000
ENTRY = 0x145a
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def execute(code, profile, filename, screen, located, status):
    u = Uc(UC_ARCH_X86, UC_MODE_16)
    u.mem_map(0, 0x100000)
    u.mem_write(0x10000 + ENTRY, code)
    for address in (0x82b6, 0x6bbe, 0x353d, 0x433d, 0x4870, 0x0cd2):
        u.mem_write(0x10000 + address, b'\xc3')
    for reg, value in ((UC_X86_REG_CS, 0x1000), (UC_X86_REG_DS, DATA >> 4),
                       (UC_X86_REG_SS, DATA >> 4), (UC_X86_REG_SP, 0xd000),
                       (UC_X86_REG_BP, 0xb0b0), (UC_X86_REG_SI, 0x5151)):
        u.reg_write(reg, value)
    u.mem_write(DATA + 0xd000, struct.pack('<H', 0xf000))
    u.mem_write(DATA + 0x1d18, struct.pack('<H', profile))
    u.mem_write(DATA + 0x3262, filename + b'\0')
    u.mem_write(DATA + 0x4675, b'%d %s\0PCKEYMAP.EXE\0')
    u.mem_write(DATA + 0xce69, b'G')
    u.mem_write(DATA + 0xceea, b'H')
    signed = profile if profile < 32768 else profile - 65536
    tail = str(signed).encode() + b' ' + filename
    events = []
    minimum = 0xd000

    def hook(cpu, address, size, _):
        nonlocal minimum
        sp = cpu.reg_read(UC_X86_REG_SP)
        minimum = min(minimum, sp)
        if address == 0x1f000:
            cpu.emu_stop()
            return
        if 0x10000 + ENTRY <= address < 0x10000 + ENTRY + len(code):return
        ret = struct.unpack('<H', cpu.mem_read(DATA + sp, 2))[0]
        words = lambda n: struct.unpack('<' + 'H' * n, cpu.mem_read(DATA + sp + 2, n * 2))
        cleanup, result = 0, 0
        if address == 0x182b6:
            assert words(4) == (0xce6a, 0x4675, profile, 0x3262)
            events.append(('format', profile, filename.hex()))
            cpu.mem_write(DATA + 0xce6a, tail + b'\0')
        elif address == 0x16bbe:
            events.append(('save', screen))
            result = screen & 65535
            cpu.reg_write(UC_X86_REG_DX, screen >> 16)
            cpu.reg_write(UC_X86_REG_ES, 0x7123)  # ES is not a preserved return contract.
        elif address == 0x1353d:
            assert words(5) == (0x467b, 0xce6a, 0, 0, 0)
            events.append(('locate', located))
            result = located
        elif address == 0x1433d:
            assert words(5) == (located, 0xce6a, 0, 0, 0)
            assert bytes(cpu.mem_read(DATA + 0xce6a, len(tail) + 1)) == tail + b'\0'
            events.append(('program', status))
            result = status
        elif address == 0x14870:
            assert words(2) == (screen & 65535, screen >> 16)
            events.append(('restore', screen))
            cleanup = 4
        elif address == 0x10cd2:
            events.append(('reload',))
            result = 0x9567
        else:raise AssertionError(('Unexpected execution outside wrapper/models', hex(address)))
        cpu.reg_write(UC_X86_REG_AX, result)
        cpu.reg_write(UC_X86_REG_SP, sp + 2 + cleanup)
        cpu.reg_write(UC_X86_REG_IP, ret)

    u.hook_add(UC_HOOK_CODE, hook)
    u.emu_start(0x10000 + ENTRY, 0x20000, count=1000)
    assert u.reg_read(UC_X86_REG_IP) == 0xf000
    assert u.reg_read(UC_X86_REG_SP) == 0xd002 and minimum == 0xcfec
    assert u.reg_read(UC_X86_REG_BP) == 0xb0b0 and u.reg_read(UC_X86_REG_SI) == 0x5151
    assert u.reg_read(UC_X86_REG_AX) == 0x9567
    assert bytes(u.mem_read(DATA + 0xce69, 1)) == b'G' and bytes(u.mem_read(DATA + 0xceea, 1)) == b'H'
    assert events == [('format', profile, filename.hex()), ('save', screen), ('locate', located),
                      ('program', status), ('restore', screen), ('reload',)]
    return events


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--original', type=Path)
    a = p.parse_args()
    build, out = a.build.resolve(), a.output.resolve()
    assert build.is_relative_to(ROOT / 'build') and out.is_relative_to(ROOT / 'build') and not out.exists()
    manifest = json.loads((build / 'manifest.json').read_text())
    assert manifest['passed'] and not manifest['original_inputs']
    assert manifest['linked_opcodes_verified'] and manifest['linked_data_references'] == manifest['linked_near_calls'] == 6
    assert manifest['nonzero_DGROUP_data_offset'] >= 128
    assert sha(build / 'KMLAUNCH.EXE') == manifest['binary_sha256']
    for name, expected in manifest['sources'].items():assert sha(ROOT / name) == expected, name
    out.mkdir(parents=True)
    rebuilt = (build / 'launch.bin').read_bytes()
    proof = json.loads((ROOT / 'reconstruction/keymap_launcher/provenance.json').read_text())
    original = None
    if a.original:
        data = a.original.read_bytes()
        assert hashlib.sha256(data).hexdigest() == proof['source_sha256']
        original = data[proof['source_file_offset']:proof['source_file_offset'] + proof['bytes']]
        assert original == rebuilt
        assert data[0x1200 + 0x488c:0x1200 + 0x488f] == b'\xc2\x04\0'
        assert data[proof['factory_literals_file_offset']:proof['factory_literals_file_offset'] + 19] == b'%d %s\0PCKEYMAP.EXE\0'
    traces = []
    profiles = [*range(33), 65535]
    vectors = itertools.product(profiles, (b'', b'SYNTH.KBD', b'C:\\KBDS\\NET.KBD'),
                                (0, 0x89abcdef), ((0x6200, 0), (0, 65535), (0x6200, 1)))
    for profile, name, screen, (located, status) in vectors:
        trace = execute(rebuilt, profile, name, screen, located, status)
        if original is not None:assert execute(original, profile, name, screen, located, status) == trace
        traces.append(trace)
    fresh = out / 'source'
    for name, expected in manifest['sources'].items():
        path = fresh / name
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, path)
        assert sha(path) == expected
    environment = dict(os.environ, GIT_CEILING_DIRECTORIES=str(out))
    assert subprocess.run(['git', 'rev-parse', '--show-toplevel'], cwd=fresh, env=environment, capture_output=True).returncode
    with (out / 'cold-build.log').open('w') as log:
        subprocess.run([sys.executable, 'standalone/build_keymap_launch.py', '--output', 'build/cold'],
                       cwd=fresh, env=environment, stdout=log, stderr=log, check=True)
    cold = fresh / 'build/cold'
    assert sha(cold / 'launch.bin') == sha(build / 'launch.bin')
    assert sha(cold / 'KMLAUNCH.EXE') == sha(build / 'KMLAUNCH.EXE')
    drive = out / 'dos'
    drive.mkdir()
    shutil.copyfile(build / 'KMLAUNCH.EXE', drive / 'KMLAUNCH.EXE')
    config = out / 'dosbox.conf'
    config.write_text('[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=fixed 6000\n'
                      '[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "' + str(drive) +
                      '"\nc:\nKMLAUNCH >RESULT.TXT\nif errorlevel 1 goto failed\necho PASS>PASS.TXT\ngoto done\n'
                      ':failed\necho FAIL>FAIL.TXT\n:done\nexit\n')
    with (out / 'dosbox.log').open('w') as log:
        result = subprocess.run(['dosbox-x', '-fastlaunch', '-nogui', '-conf', str(config)],
                                env=dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy'),
                                stdout=log, stderr=log, timeout=15)
    assert result.returncode == 0 and (drive / 'PASS.TXT').exists() and not (drive / 'FAIL.TXT').exists()
    assert b'PASS KEYMAP LAUNCH 8 ABI CASES' in (drive / 'RESULT.TXT').read_bytes()
    report = dict(passed=True, flat_bytes=78, flat_sha256=sha(build / 'launch.bin'),
                  binary_sha256=sha(build / 'KMLAUNCH.EXE'), model_cases=len(traces), DOS_cases=8,
                  original_compared=original is not None, source_sha256=proof['source_sha256'] if original is not None else None,
                  trace_sha256=hashlib.sha256(json.dumps(traces).encode()).hexdigest(),
                  caller_stack_bytes=20, source_export_files=len(manifest['sources']), ancestor_git_unavailable=True,
                  cold_binary_reproduced=True, linked_opcodes_verified=True,
                  sources={**manifest['sources'], str(Path(__file__).relative_to(ROOT)): sha(Path(__file__))},
                  scope=__doc__ + ' Models verify caller order/arguments, opaque screen handle, RET4 cleanup, reload after all modeled PROGRAM outcomes, BP/SI/SP and guard bytes. No original editor, real CRT/lookup/PROGRAM/video/load-file behavior or terminal integration claim.')
    (out / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
    print('PASS78-byte keymap caller:', len(traces), 'modeled frames,8DOS ABI cases, exact5file source reproduction')


if __name__ == '__main__':
    main()
