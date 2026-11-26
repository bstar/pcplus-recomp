#!/usr/bin/env python3
"""Bounded source-only DOS8086 directory-view and adopted-script origin hooks."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    out = a.output.resolve()
    assert out.is_relative_to(ROOT/'build') and not out.exists()
    out.mkdir(parents=True)
    names = ['standalone/test_aspect_state_directory_dos.py',
             'standalone/aspect_state_directory_driver.c',
             'standalone/aspect_state_directory_boundaries.asm',
             'src/redisplay/directory_view.c', 'src/redisplay/directory_view.h',
             'src/directory/directory_reader.c', 'src/directory/directory_reader.h',
             'src/directory/directory_reader_fs.h', 'src/directory/directory_dos.h',
             'src/terminal/script_launch.asm', 'src/directory/directory_live.inc']
    sources = {n: sha(ROOT/n) for n in names}
    # The exact first function is compiled without the unrelated later loader.
    # Its near call is resolved to an explicit observation stub, not a product edit.
    source = (ROOT/'src/terminal/script_launch.asm').read_text()
    end = source.index('\n; AX selected entry0/1..200')
    prefix = source[:end]
    assert prefix.count('terminal_directory_script_connected:') == 1
    (out/'connected.asm').write_text(prefix+'\nextern terminal_script_start,_aspect_fromddir\n')
    flags = ['-q', '-bt=dos', '-0', '-ms', '-ecc', '-s', '-os', '-w4', '-we', '-dASPECT_STATE_BUILTINS']
    for name, path in [('view','src/redisplay/directory_view.c'), ('reader','src/directory/directory_reader.c'),
                       ('driver','standalone/aspect_state_directory_driver.c')]:
        # Keep source code strings in their original _CODE segment; all calls use
        # the production far ABI. No implementation branch is substituted.
        subprocess.run(['wcl', '-c', *flags, '-fo='+name+'.obj', str(ROOT/path)], cwd=out, check=True)
    for name, path, extra in [('connected',out/'connected.asm', ['-DDIRECTORY_RESOURCE_ADOPTION','-DASPECT_STATE_BUILTINS']),
                              ('boundaries',ROOT/'standalone/aspect_state_directory_boundaries.asm',[])]:
        subprocess.run(['nasm','-fobj','-I'+str(ROOT/'src/directory')+'/',*extra,str(path),'-o',name+'.obj'],cwd=out,check=True)
    subprocess.run(['wcl',*flags,'-k8192','-fm=STATE.map','-fe=STATE.EXE',
                    'view.obj','reader.obj','driver.obj','connected.obj','boundaries.obj'],cwd=out,check=True)
    (out/'RUN.BAT').write_bytes(b'@echo off\r\nSTATE >CHECK.LOG\r\nif errorlevel 1 goto failed\r\necho PASS>RESULT.TXT\r\ngoto done\r\n:failed\r\necho FAIL>RESULT.TXT\r\n:done\r\nexit\r\n')
    (out/'dosbox.conf').write_text('[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\nfpu=false\ncycles=fixed 30000\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "'+str(out)+'"\nc:\ncall RUN.BAT\nexit\n')
    with (out/'dosbox.log').open('w') as log:
        subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],cwd=out,
                       stdout=log,stderr=log,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),check=True,timeout=30)
    transcript=(out/'CHECK.LOG').read_text().strip()
    assert (out/'RESULT.TXT').read_text().strip()=='PASS',transcript
    match=re.fullmatch(r'ASPECT_STATE_DIRECTORY (\d+) cases (\d+) checks 0 failures',transcript)
    assert match,transcript
    assert all(sha(ROOT/n)==digest for n,digest in sources.items())
    result=dict(passed=True,cases=int(match[1]),checks=int(match[2]),transcript=transcript,
                sources=sources,original_inputs=[],function_extraction=dict(source='src/terminal/script_launch.asm',
                start_line=1,end_line=len(prefix.splitlines()),sha256=hashlib.sha256(prefix.encode()).hexdigest()),
                compile_flags=flags,artifacts={p.name:sha(p) for p in out.iterdir() if p.is_file()},
                scope=__doc__,coverage=[
                    'DS=SS; ten prior WORD origins cleared by interactive event0 before actual full-frame draw; both origin neighbors and frame neighbors remain intact.',
                    'Immediate Escape and a complete read-only browse leave origin zero; inactive/redraw/idle/loading/cancel/paging/reload/forced-stop retain injected nonzero origins.',
                    'Browser/editor busy reader gates retain post-open origin without opening a file.',
                    'Ten full WORD entries reach the loader observer via adopted status2 and legacy status0/name; legacy NUL/space and adopted statuses1/3/65535 preserve origin.',
                    'Invalid context and each of four busy gates reject before staged-name callback and loader, preserving origin.'],limitations=[
                    'Real view rendering and real incremental reader execute; filesystem stubs provide an exact-size zero-filled public directory without actual file IO.',
                    'Unchanged first ASM function extracted from source; actual adopted-name implementation and terminal_script_start loader are explicit staged-status/name and loader-entry observation stubs.',
                    'Standalone _CODE component placement uses production function ABIs; optional DIRECTORY_CODE bank/wrapper linkage is outside this probe.',
                    'No live terminal routing, adopted resource ownership, executable loader, physical DOS machine, original binary equivalence or whole-application completeness is established.'])
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(transcript)


if __name__=='__main__':
    main()
