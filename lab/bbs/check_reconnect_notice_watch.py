#!/usr/bin/env python3
"""Exercise actual DOS notice capture, false prefixes and INT1C restoration."""
import argparse
import json
import os
import struct
import subprocess
import sys
from pathlib import Path
from audio_synchronet import ROOT, sha
sys.path.insert(0, str(ROOT / 'standalone'))
from reconnect_notice_watch import SAMPLER
from carrier_notice_watch import SAMPLER as OLD_SAMPLER

PROBE = r'''bits 16
cpu 8086
org 100h
cld
mov ax,3
int 10h
mov ax,0b800h
mov es,ax
xor di,di
mov ax,0720h
mov cx,2000
rep stosw
mov di,24*160+2
mov si,partial
call text
call wait_ticks
mov di,24*160+2
mov si,wrong
call text
call wait_ticks
mov di,22*160+2
mov si,lost
call text
call wait_ticks
mov di,0*160+2
mov si,rx_lost
call text
mov di,24*160+2
mov si,complete
call text
call wait_ticks
mov ah,1
int 16h
jnz fail
mov dx,passfile
jmp write
fail:mov dx,failfile
write:
mov ah,3ch
xor cx,cx
int 21h
jc exit
mov bx,ax
mov ah,3eh
int 21h
exit:mov ax,4c00h
int 21h
text:
lodsb
or al,al
jz .done
mov ah,7
stosw
jmp text
.done:ret
wait_ticks:
push es
mov ax,40h
mov es,ax
mov bx,[es:6ch]
.wait:
mov ax,[es:6ch]
sub ax,bx
cmp ax,6
jb .wait
pop es
ret
partial:db 'RX carrier',0
wrong:db 'Carpet lost',0
lost:db 'Carrier lost',0
rx_lost:db 'RX carrier lost',0
complete:db 'RX complete',0
passfile:db 'PASS.TXT',0
failfile:db 'FAIL.TXT',0
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--old-observer', action='store_true')
    args = parser.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT / 'build') and not out.exists()
    out.mkdir(parents=True)
    (out / 'sampler.asm').write_text(OLD_SAMPLER if args.old_observer else SAMPLER)
    (out / 'probe.asm').write_text(PROBE)
    for src, dst in [('sampler.asm', 'SNAP.COM'), ('probe.asm', 'PROBE.COM')]:
        subprocess.run(['nasm', '-fbin', str(out / src), '-o', str(out / dst)], check=True)
    (out / 'dosbox.conf').write_text(f'''[sdl]
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
SNAP B
PROBE
SNAP S
SNAP A
exit
''')
    with (out / 'dosbox.log').open('wb') as log:
        run = subprocess.run(['dosbox-x', '-fastlaunch', '-nogui', '-conf', str(out / 'dosbox.conf')],
            stdout=log, stderr=log, timeout=15, env=dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy'))
    read = lambda name: (out / name).read_bytes() if (out / name).exists() else b''
    raw = read('LABELS.BIN')
    assert len(raw) == 2566
    magic, count, ticks = struct.unpack_from('<3H', raw)
    assert magic == 0x4e5a and count <= 16
    notices = [raw[6 + i * 160:6 + (i + 1) * 160:2].decode('cp437').strip() for i in range(count)]
    checks = dict(normal_DOS_return=run.returncode == 0,
        hardware_and_INT1C_restored=len(read('BEFORE.BIN')) == 42 and read('BEFORE.BIN') == read('AFTER.BIN'),
        keyboard_untouched=(out / 'PASS.TXT').exists() and not (out / 'FAIL.TXT').exists(),
        off_footer_carrier_loss_captured='Carrier lost' in notices,
        stale_top_notice_does_not_hide_footer_completion='RX carrier lost' in notices and 'RX complete' in notices,
        only_exact_unique_notices=notices == ['Carrier lost', 'RX carrier lost', 'RX complete'])
    inputs = [Path(__file__).resolve(), ROOT / 'lab/bbs/reconnect_notice_watch.py', ROOT / 'lab/bbs/carrier_notice_watch.py', ROOT / 'lab/bbs/zmodem_label_watch.py', ROOT / 'standalone/test_terminal.py']
    result = dict(passed=all(checks.values()), old_observer=args.old_observer, checks=checks,
                  notices=notices, ticks=ticks, probe_sha256=sha(out / 'PROBE.COM'),
                  inputs={str(p.relative_to(ROOT)): sha(p) for p in inputs},
                  scope='Actual 8086 DOS/video/INT1C fixture. Reject partial/wrong prefixes, capture loss on row22 and simultaneous stale row0 loss plus row24 completion, deduplicate repeated frames, leave BIOS keyboard untouched and restore all42 hardware/vector bytes. No BBS/audio or application acceptance.')
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))
    assert result['passed']


if __name__ == '__main__':
    main()
