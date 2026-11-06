#!/usr/bin/env python3
"""Check diagnostic fopen records against real owned DOS files and missing paths."""
import argparse
import json
import os
import struct
import subprocess
from pathlib import Path
from build_path_session import ROOT, sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    assert output.is_relative_to(ROOT / 'build') and not output.exists()
    output.mkdir()
    source = output / 'probe.c'
    source.write_text('''#include "file_io.h"
#include <dos.h>
#include <errno.h>
int main(void){
 aspect_file f;int h;unsigned n;
 if(_dos_creat("D:\\\\SMALL.ASX",0,&h))return 10;
 if(_dos_write(h,"X",1,&n)||n!=1||_dos_close(h))return 11;
 if(aspect_file_init(&f))return 12;
 errno=0;
 if(aspect_file_open(&f,"D:\\\\SMALL.ASX")||aspect_file_close(&f))return 13;
 errno=0;
 if(aspect_file_open(&f,"D:\\\\MISSING.ASX")!=ASPECT_FILE_IO||f.handle||errno!=ENOENT)return 14;
 return 0;
}
''')
    subprocess.run(['wcl', '-q', '-bt=dos', '-0', '-ms', '-ecc', '-s', '-w4', '-we',
                    '-DASPECT_FILE_OPEN_PROBE', '-i=' + str(ROOT / 'src/aspect'),
                    '-fe=PROBE.EXE', str(source), str(ROOT / 'src/aspect/file_io.c')],
                   cwd=output, check=True)
    config = output / 'dosbox.conf'
    config.write_text(f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
cycles=fixed 6000
[mixer]
nosound=true
[autoexec]
@echo off
mount c "{output}"
mount d "{output}"
c:
PROBE
if errorlevel 1 goto failed
echo PASS>PASS.TXT
goto done
:failed
echo FAIL>FAIL.TXT
:done
exit
''')
    with (output / 'dosbox.log').open('w') as log:
        run = subprocess.run(['dosbox-x', '-fastlaunch', '-nogui', '-conf', str(config)],
                             cwd=output, env=dict(os.environ, SDL_VIDEODRIVER='dummy',
                             SDL_AUDIODRIVER='dummy'), stdout=log, stderr=log, timeout=25)
    assert run.returncode == 0 and (output / 'PASS.TXT').exists() and not (output / 'FAIL.TXT').exists()
    data = (output / 'FOPEN.BIN').read_bytes()
    assert len(data) == 192
    rows = []
    for offset, path, ok, error, dos in [(0, b'D:\\SMALL.ASX', 1, 0, 65535),
                                        (96, b'D:\\MISSING.ASX', 0, 1, 2)]:
        record = data[offset:offset + 96]
        words = struct.unpack_from('<7H', record)
        assert words == (0x4f46, 1, ok, error, dos, 0, len(path)), words
        assert record[14:].split(b'\0', 1)[0] == path
        rows.append(dict(path=path.decode(), fopen_succeeded=bool(ok), errno=error,
                         raw_DOS_open_status=dos, passed=True))
    result = dict(passed=True, cases=rows, original_inputs=[],
                  sources={n: sha(ROOT / n) for n in ['standalone/test_file_open_probe_dos.py',
                           'src/aspect/file_io.c', 'src/aspect/file_io.h']},
                  capture_sha256=sha(output / 'FOPEN.BIN'),
                  scope=__doc__ + ' Diagnostic compiler flag only; real DOS8086 stdio and raw read-only comparison. No parent/BBS/physical acceptance.')
    (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print('PASS real DOS fopen success/missing path,errno and raw DOS records')


if __name__ == '__main__':
    main()
