#!/usr/bin/env python3
"""Observe authentic Alt-P in DOS; originals and captured screens stay private."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = '6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--save', action='store_true')
    args = parser.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT / 'build')
    out.mkdir(parents=True, exist_ok=False)
    c = out / 'c'
    c.mkdir()
    original = ROOT / 'analysis/pcplus-originals/PCPLUS-main-2.01.EXE'
    assert sha(original) == EXPECTED
    shutil.copyfile(original, c / 'PCPLUS.EXE')
    fixture = ROOT / 'build/cwd-ui-recovery-20261104/first/c/PCPLUS.PRM'
    before = bytearray(fixture.read_bytes())
    struct.pack_into('<5H', before, 0, 0, 5, 0, 1, 8)  # COM1 /19200 /8N1
    (c / 'PCPLUS.PRM').write_bytes(before)
    for name in ('PCPLUS.KEY', 'PCPLUS.KBD', 'PCPLUS.XLT'):
        source = ROOT / 'analysis/pcplus-install' / name
        if source.exists():
            shutil.copyfile(source, c / name)
    watcher = ROOT / 'standalone/viewer_original_watch.asm'
    shutil.copyfile(watcher, out / 'watch.asm')
    subprocess.run(['nasm', '-fbin', str(out / 'watch.asm'), '-o', str(c / 'WATCH.COM')], check=True)
    leave = 'a-s' if args.save else 'escape'
    keys = ('p750 enter p3250 a-p p900 5 p700 e p700 ' + leave +
            ' p700 a-p p900 escape p700 a-x p400 y enter p500 a-x p400 y enter')
    config = out / 'dosbox.conf'
    config.write_text(f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
fpu=false
cycles=fixed 6000
[mixer]
nosound=true
[serial]
serial1=dummy
serial2=disabled
serial3=disabled
serial4=disabled
[autoexec]
@echo off
mount c "{c}"
c:
WATCH T
ADDKEY {keys}
C:\\PCPLUS
C:\\WATCH
echo DONE>C:\\DONE.TXT
exit
''')
    with (out / 'dosbox.log').open('w') as log:
        subprocess.run(['dosbox-x', '-fastlaunch', '-nogui', '-conf', str(config)],
            cwd=out, env=dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy'),
            stdout=log, stderr=log, check=True, timeout=40)
    raw = (c / 'EDITVIEW.BIN').read_bytes()
    magic, count, ticks = struct.unpack_from('<3H', raw)
    assert magic == 0x4544 and count and (c / 'DONE.TXT').exists()
    frames = []
    for i in range(count):
        cursor, shape = struct.unpack_from('<2H', raw, 6 + i * 4004)
        frame = raw[10 + i * 4004:4010 + i * 4004]
        (out / f'frame-{i}.bin').write_bytes(frame)
        (out / f'frame-{i}.txt').write_text('\n'.join(
            frame[r * 160:(r + 1) * 160:2].decode('cp437') for r in range(25)))
        frames.append(dict(index=i, cursor=[cursor >> 8, cursor & 255],
                           shape=shape, sha256=hashlib.sha256(frame).hexdigest()))
    after = (c / 'PCPLUS.PRM').read_bytes()
    assert sha(c / 'PCPLUS.EXE') == EXPECTED
    result = dict(original_sha256=EXPECTED, producer_sha256=sha(Path(__file__)),
        watcher_sha256=sha(watcher), keys=keys, save=args.save, frames=frames,
        before_sha256=hashlib.sha256(before).hexdigest(), after_sha256=sha(c / 'PCPLUS.PRM'),
        before_words=list(struct.unpack_from('<5H', before)),
        after_words=list(struct.unpack_from('<5H', after)),
        changed_offsets=[i for i, (a, b) in enumerate(zip(before, after)) if a != b],
        length_unchanged=len(before) == len(after), original_unchanged=True, done=True,
        limitations=['Authentic original in DOSBox-X with dummy COM1; passive VGA/BDA watcher. No physical modem or reconstructed popup.'])
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print('Original Alt-P:', 'Alt-S' if args.save else 'Escape', count, 'frames;',
          result['after_words'], 'changed offsets', result['changed_offsets'])


if __name__ == '__main__':
    main()
