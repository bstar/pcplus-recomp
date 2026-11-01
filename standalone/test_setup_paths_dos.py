#!/usr/bin/env python3
"""Exercise PRMEDIT absolute identities, decoys and drive/CWD restoration in DOS."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
from check_setup_model import image

ROOT = Path(__file__).resolve().parents[1]

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

SAMPLER = '''BITS 16
CPU 8086
ORG 100h
mov ah,19h
int 21h
mov [data],al
mov si,data+1
mov dl,3
mov ah,47h
int 21h
jc failed
mov si,data+65
mov dl,4
mov ah,47h
int 21h
jc failed
mov dx,before
cmp byte [82h],'B'
je write
mov dx,after
write:
xor cx,cx
mov ah,3ch
int 21h
jc failed
mov bx,ax
mov dx,data
mov cx,129
mov ah,40h
int 21h
mov ah,3eh
int 21h
mov ax,4c00h
int 21h
failed:
mov ax,4c01h
int 21h
before: db 'D:\\BEFORE.BIN',0
after: db 'D:\\AFTER.BIN',0
data: times 129 db 0
'''

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--editor', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    editor = args.editor.resolve()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT / 'build') and not out.exists()
    out.mkdir(parents=True)
    raw = bytearray(image())
    struct.pack_into('<HH', raw, 0x4e4, 8, 4)
    wanted = bytearray(raw)
    struct.pack_into('<H', wanted, 2, 5)  # 19200 DTE
    cases = []
    for label, argument, target, accepted in [
        ('leaf', 'VALID.PRM', 'D/OTHER/VALID.PRM', True),
        ('same-drive', 'D:\\CONFIG\\VALID.PRM', 'D/CONFIG/VALID.PRM', True),
        ('root', 'D:\\VALID.PRM', 'D/VALID.PRM', True),
        ('cross-drive', 'C:\\CONFIG\\VALID.PRM', 'C/CONFIG/VALID.PRM', True),
        ('lowercase-drive', 'c:\\CONFIG\\VALID.PRM', 'C/CONFIG/VALID.PRM', True),
        ('cross-drive-conflict', 'C:\\CONFIG\\VALID.PRM', None, True),
        ('relative-directory', '..\\CONFIG\\VALID.PRM', None, False),
        ('drive-relative', 'C:VALID.PRM', None, False),
        ('traversal', 'C:\\CONFIG\\..\\VALID.PRM', None, False),
        ('wildcard', 'C:\\CONFIG\\*.PRM', None, False),
        ('trailing-directory', 'C:\\CONFIG\\', None, False),
        ('device', 'C:\\CONFIG\\CON', None, False),
        ('missing-directory', 'C:\\MISSING\\VALID.PRM', None, False),
        ('missing-file', 'C:\\CONFIG\\MISSING.PRM', None, False),
    ]:
        folder = out / label
        for drive in ('C', 'D'):
            for sub in ('HOME', 'CONFIG', 'OTHER'):
                (folder / drive / sub).mkdir(parents=True)
            for sub in ('', 'CONFIG/', 'OTHER/'):
                (folder / drive / (sub + 'VALID.PRM')).write_bytes(raw)
        shutil.copyfile(editor, folder / 'D/PRMEDIT.EXE')
        conflict = label == 'cross-drive-conflict'
        if conflict:
            (folder / 'C/CONFIG/PRMEDIT.BAK').write_bytes(b'PRESERVE RECOVERY')
        (folder / 'cwd.asm').write_text(SAMPLER)
        subprocess.run(['nasm', '-fbin', str(folder / 'cwd.asm'), '-o', str(folder / 'D/CWD.COM')], check=True)
        keys = 'p900 tab home del del del del 1 9 2 0 0 f10 p400 escape' + (' y' if conflict else '')
        schedule = 'ADDKEY ' + ' p100 '.join(keys.split()) if accepted else ''
        config = f'''[sdl]
output=surface
[dosbox]
quit warning=false
[cpu]
core=normal
cputype=8086
cycles=fixed 6000
[mixer]
nosound=true
[autoexec]
@echo off
mount c "{folder / 'C'}"
mount d "{folder / 'D'}"
c:
cd \\HOME
d:
cd \\OTHER
D:\\CWD.COM B
{schedule}
D:\\PRMEDIT.EXE {argument}
if errorlevel 1 goto failed
echo OK>D:\\OK.TXT
goto collect
:failed
echo FAIL>D:\\FAIL.TXT
:collect
D:\\CWD.COM A
exit
'''
        (folder / 'dosbox.conf').write_text(config)
        with (folder / 'dosbox.log').open('w') as log:
            run = subprocess.run(['dosbox-x', '-fastlaunch', '-nogui', '-conf', str(folder / 'dosbox.conf')], stdout=log, stderr=log, timeout=25,
                                 env=dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy'))
        assert run.returncode == 0
        assert (folder / 'D/OK.TXT').exists() == accepted, label
        assert (folder / 'D/FAIL.TXT').exists() != accepted, label
        before = (folder / 'D/BEFORE.BIN').read_bytes()
        assert len(before) == 129 and before[0] == 3
        assert before == (folder / 'D/AFTER.BIN').read_bytes(), label
        for file in folder.rglob('*.PRM'):
            assert file.read_bytes() == (wanted if accepted and str(file.relative_to(folder)) == target else raw), (label, file)
        backups = list(folder.rglob('PRMEDIT.BAK'))
        assert not list(folder.rglob('PRMEDIT.$$$')), label
        if conflict:
            assert backups == [folder / 'C/CONFIG/PRMEDIT.BAK'] and backups[0].read_bytes() == b'PRESERVE RECOVERY'
        else:
            assert not backups, label
        cases.append(dict(case=label, passed=True, accepted=accepted, all_decoys_unchanged=True, drive_and_directories_restored=True))
        print('PASS', label, flush=True)
    result = dict(passed=True, editor_sha256=sha(editor), cases=cases, original_inputs=[],
                  sources={p: sha(ROOT / p) for p in ['src/config/setup_main.c', 'standalone/test_setup_paths_dos.py', 'standalone/check_setup_model.py']},
                  scope=__doc__ + ' Synthetic PRM images, actual editor UI save, invalid paths refuse. No physical hardware claim.')
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')

if __name__ == '__main__':
    main()
