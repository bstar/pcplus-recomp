#!/usr/bin/env python3
"""Actual DOS8086 cap27 FAR screen scalar client, with controlled RPC/check gates."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
FLAGS = ['ASPECT_EXTERNAL_RENDER', 'ASPECT_EXTERNAL_UNWIND', 'ASPECT_SNAPSHOT_LEASE',
         'ASPECT_ALARM_VM', 'ASPECT_EMULATE_VM', 'ASPECT_GET_DISPLAY', 'ASPECT_GET_POLICY',
         'ASPECT_COMPILER_PARENT_LEASE', 'ASPECT_TERMINAL_QUERY', 'ASPECT_HITKEY_PARENT',
         'ASPECT_STATE_BUILTINS_PARENT', 'ASPECT_SCREEN_PARENT']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT/'build') and not out.exists()
    out.mkdir(parents=True)
    dependencies = [Path(__file__).resolve(), ROOT/'standalone/aspect_screen_client_driver.c',
                    ROOT/'src/aspect/resident_render.c', ROOT/'src/aspect/screen_client.c',
                    *sorted((ROOT/'src/aspect').glob('*.h'))]
    sources = {str(path.relative_to(ROOT)): sha(path) for path in dependencies}
    # Match the gateway's FARCODE class while using an explicit group to force
    # the FAR target into a different CS from this ordinary caller. This
    # fixture is not the application's native screen bank or resident bridge.
    probe = out/'screen-client-abi.asm'
    probe.write_text('''BITS 16
CPU 8086
GROUP SCREEN_CLIENT_BANK SCRIPT_SCREEN_CODE
SEGMENT SCRIPT_SCREEN_CODE public align=16 class=FARCODE use16
SEGMENT _TEXT public align=16 class=CODE use16
extern _aspect_render_screen_scalar
global _screen_probe_call
_screen_probe_call:
 push bp
 mov bp,sp
 push si
 push di
 sub sp,6
 mov [bp-6],ds
 mov [bp-8],ss
 mov [cs:screen_probe_expected_bp],bp
 mov si,0x1357
 mov di,0x2468
 push word [bp+6]
 push word [bp+4]
 call far _aspect_render_screen_scalar
 cmp bp,[cs:screen_probe_expected_bp]
 je .bp_ok
 mov bp,[cs:screen_probe_expected_bp]
 or word [ss:_screen_probe_abi],64
.bp_ok:
 mov [bp-10],ax
 mov ax,ds
 cmp ax,[ss:bp-6]
 je .ds_ok
 push ss
 pop ds
 or word [_screen_probe_abi],1
.ds_ok:
 mov ax,ss
 cmp ax,[bp-8]
 je .ss_ok
 or word [_screen_probe_abi],2
.ss_ok:
 cmp si,0x1357
 je .si_ok
 or word [_screen_probe_abi],4
.si_ok:
 cmp di,0x2468
 je .di_ok
 or word [_screen_probe_abi],8
.di_ok:
 mov ax,bp
 sub ax,14
 cmp sp,ax
 je .sp_ok
 or word [_screen_probe_abi],16
.sp_ok:
 pushf
 pop ax
 and ax,0x600
 cmp ax,0x200
 je .flags_ok
 or word [_screen_probe_abi],32
.flags_ok:
 mov ax,[bp-10]
 lea sp,[bp-4]
 pop di
 pop si
 pop bp
 ret
screen_probe_expected_bp: dw 0
SEGMENT _DATA public class=DATA use16
global _screen_probe_abi
_screen_probe_abi: dw 0
''')
    obj = out/'screen-client-abi.obj'
    subprocess.run(['nasm', '-fobj', str(probe), '-o', str(obj)], check=True)
    subprocess.run(['wcl', '-q', '-bt=dos', '-0', '-ms', '-ecc', '-s', '-ob', '-os',
        '-w4', '-we', '-k8192', *['-d'+flag for flag in FLAGS],
        '-i='+str(ROOT/'src/aspect'), '-fm=CLIENT.map', '-fe=CLIENT.EXE',
        str(ROOT/'standalone/aspect_screen_client_driver.c'), str(obj)], cwd=out, check=True)
    header_probe = out/'capability-profile.c'
    header_probe.write_text('#include "resident_render.h"\n'
        '#ifndef EXPECTED_CAP\n#define EXPECTED_CAP 27\n#endif\n'
        'typedef char capability_matches[(ASPECT_RENDER_CAP_VERSION==EXPECTED_CAP)?1:-1];\n')
    gate_cases = []
    for missing in ('ASPECT_STATE_BUILTINS_PARENT', 'ASPECT_HITKEY_PARENT',
        'ASPECT_TERMINAL_QUERY', 'ASPECT_COMPILER_PARENT_LEASE', 'ASPECT_GET_POLICY',
        'ASPECT_GET_DISPLAY', 'ASPECT_EMULATE_VM', 'ASPECT_SNAPSHOT_LEASE'):
        proc = subprocess.run(['wcc', '-q', '-bt=dos', '-0', '-ms', '-ecc', '-s', '-w4', '-we',
            *['-d'+flag for flag in FLAGS if flag != missing], '-i='+str(ROOT/'src/aspect'),
            '-fo='+str(out/('missing-'+missing+'.obj')), str(header_probe)],
            cwd=out, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        assert proc.returncode and 'Error! E1091:' in proc.stdout, (missing, proc.stdout)
        (out/('missing-'+missing+'.log')).write_text(proc.stdout)
        gate_cases.append(dict(missing_flag=missing, rejected=True))
    subprocess.run(['wcc', '-q', '-bt=dos', '-0', '-ms', '-ecc', '-s', '-w4', '-we',
        *['-d'+flag for flag in FLAGS if flag != 'ASPECT_SCREEN_PARENT'], '-dEXPECTED_CAP=26',
        '-i='+str(ROOT/'src/aspect'), '-fo='+str(out/'cap26-control.obj'), str(header_probe)], cwd=out, check=True)
    listing = (out/'CLIENT.map').read_text()
    rows = re.findall(r'^(\w+)\s+(\w+)\s+\w+\s+([0-9a-f]+):([0-9a-f]+)\s+([0-9a-f]+)\s*$', listing, re.M|re.I)
    assert sum(name == 'SCRIPT_SCREEN_CODE' for name, *_ in rows) == 1
    segments = {name: (cls, int(seg, 16), int(off, 16), int(size, 16))
        for name, cls, seg, off, size in rows}
    near, bank = segments['_TEXT'], segments['SCRIPT_SCREEN_CODE']
    assert bank[0] == 'FARCODE' and bank[3]
    assert near[1] != bank[1], 'FAR ABI proof requires different actual code segments'
    symbols = {name: (int(seg, 16), int(off, 16)) for seg, off, name in re.findall(
        r'^\s*([0-9a-f]+):([0-9a-f]+)[*+ ]+\s+(\w+)\s*$', listing, re.M|re.I)}
    assert symbols['_aspect_render_screen_scalar'][0] == bank[1]
    for name in ('_screen_probe_call', '_screen_wire_request', '_screen_client_check', '_aspect_render_screen_ready'):
        assert symbols[name][0] == near[1], name
    (out/'RUN.BAT').write_bytes(b'@echo off\r\nCLIENT >CHECK.LOG\r\nif errorlevel 1 goto failed\r\necho PASS>RESULT.TXT\r\ngoto done\r\n:failed\r\necho FAIL>RESULT.TXT\r\n:done\r\nexit\r\n')
    (out/'dosbox.conf').write_text('[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\nfpu=false\ncycles=fixed 30000\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "'+str(out)+'"\nc:\ncall RUN.BAT\nexit\n')
    with (out/'dosbox.log').open('w') as log:
        subprocess.run(['dosbox-x', '-fastlaunch', '-nogui', '-conf', str(out/'dosbox.conf')],
            cwd=out, stdout=log, stderr=log,
            env=dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy'), check=True, timeout=30)
    transcript = (out/'CHECK.LOG').read_text().strip()
    assert (out/'RESULT.TXT').read_text().strip() == 'PASS', transcript
    match = re.fullmatch(r'SCREEN_CLIENT (\d+) cases (\d+) checks 0 failures', transcript)
    assert match, transcript
    assert (int(match[1]), int(match[2])) == (2050, 14748), transcript
    assert all(sha(ROOT/path) == digest for path, digest in sources.items())
    result = dict(passed=True, cases=int(match[1]), checks=int(match[2]), capability=27,
        operations=list(range(32, 37)), compile_flags=FLAGS, sources=sources, original_inputs=[],
        compile_gate_cases=gate_cases, cap26_without_screen_compiles=True,
        transcript=transcript, code_segments=dict(resident=near[1], screen=bank[1], screen_class=bank[0]),
        artifacts={path.name: sha(path) for path in out.iterdir() if path.is_file()},
        scope=__doc__+' All five operations/all256 tagged bytes, twelve fullWORD payloads, six metadata low/high selectors and twelve decoded WORDs, all typed0..14 results, fifteen invalid tags, pre/post-check failure and typed-result precedence, invalid operations, detached/serial0/2/FFFF, twelve owners/waits with1/FFFF, stored-error preservation and retry. Eight missing-prerequisite profiles fail compilation; cap26 without screen remains valid. Native probe crosses distinct CS values and checks scalar AX, caller-stack/canaries, BP/SI/DI/DS/SS and IF/DF. No transport/poll/WHEN callbacks called. Private owner inputs, client admission and parent replies are controlled boundaries; no actual parent service, ASIO handshake rejection, native drawing, hardware or full ASPECT qualification.')
    (out/'result.json').write_text(json.dumps(result, indent=2)+'\n')
    print(transcript)


if __name__ == '__main__':
    main()
