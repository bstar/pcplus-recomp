#!/usr/bin/env python3
"""Exercise the test helper's prerequisite watchdog through actual BIOS keys."""
import argparse
import json
import os
from pathlib import Path
import subprocess
from synthmodem_vm_control import ROOT, sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    out = parser.parse_args().output.resolve(); assert out.is_relative_to(ROOT/'build')
    out.mkdir(parents=True, exist_ok=False)
    source = '''bits 16
cpu 8086
org 100h
xor ah,ah
int 16h
mov [key],ax
mov ah,3ch
xor cx,cx
mov dx,filename
int 21h
jc failure
mov bx,ax
mov ah,40h
mov cx,2
mov dx,key
int 21h
cmp ax,2
jne failure
mov ah,3eh
int 21h
mov ax,4c00h
int 21h
failure: mov ax,4c01h
int 21h
key: dw 0
filename: db 'KEY.BIN',0
'''
    (out/'keyread.asm').write_text(source)
    subprocess.run(['nasm','-fbin','-DAUDIO_EDITOR_WATCHDOG_TICKS=36',
                    str(ROOT/'lab/bbs/audio_editor_keys.asm'),'-o',str(out/'EXITKEY.COM')], check=True)
    for asm, leaf in [(out/'keyread.asm','KEYREAD.COM'),(ROOT/'lab/bbs/audio_get_vector.asm','KEYVEC.COM')]:
        subprocess.run(['nasm','-fbin',str(asm),'-o',str(out/leaf)], check=True)
    (out/'dosbox.conf').write_text(f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
cycles=fixed 6000
[autoexec]
@echo off
mount c "{out}"
mount d "{out}"
c:
EXITKEY
KEYREAD
if errorlevel 1 goto fail
echo PASS>PASS.TXT
goto done
:fail
echo FAIL>FAIL.TXT
:done
KEYVEC
exit
''')
    with (out/'dosbox.log').open('w') as log:
        run = subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],
                             stdout=log,stderr=log,timeout=12,
                             env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'))
    read = lambda n: (out/n).read_bytes() if (out/n).is_file() else b''
    checks = {'normal_DOS_return':run.returncode==0 and (out/'PASS.TXT').is_file() and not (out/'FAIL.TXT').exists(),
              'actual_BIOS_Alt_X':read('KEY.BIN')==b'\x00\x2d',
              'timer_vector_restored':len(read('KEYOLD.BIN'))==4 and read('KEYOLD.BIN')==read('KEYNEW.BIN')}
    names = [Path(__file__).resolve(), ROOT/'lab/bbs/audio_editor_keys.asm', ROOT/'lab/bbs/audio_get_vector.asm']
    result = {'passed':all(checks.values()),'checks':checks,'inputs':{str(n.relative_to(ROOT)):sha(n) for n in names},
              'scope':'Actual DOS BIOS-key and timer restoration test with36-tick test-only deadline and no KEYTEST screen. Production lab deadline remains12600ticks. A guard exit provides no script/editor acceptance; no product or UART behavior is replaced.'}
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2)); assert result['passed']


if __name__ == '__main__': main()
