#!/usr/bin/env python3
"""Actual 8086 DOS stdio through native file handlers, on fresh owned files."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
from build_aspect_script_file_backend import ROOT, OUT, sha, main as build


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--label', default='check-' + str(time.time_ns()))
    a = p.parse_args()
    assert re.fullmatch(r'[A-Za-z0-9_-]+', a.label)
    build()
    stage = OUT / 'tests' / a.label
    stage.mkdir(parents=True, exist_ok=False)
    binary = OUT / 'SCRIPTIO.EXE'
    before = sha(binary)
    shutil.copyfile(binary, stage / binary.name)
    config = f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
fpu=false
cycles=max
[mixer]
nosound=true
[autoexec]
@echo off
mount c "{stage}"
c:
SCRIPTIO >RESULT.TXT
if errorlevel 1 goto failed
echo PASS>PASS.TXT
goto done
:failed
echo FAIL>FAIL.TXT
:done
exit
'''
    (stage / 'dosbox.conf').write_text(config)
    with (stage / 'dosbox.log').open('w') as log:
        subprocess.run(['dosbox-x', '-fastlaunch', '-nogui', '-conf', str(stage / 'dosbox.conf')],
                       cwd=stage, env=dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy'),
                       stdout=log, stderr=log, check=True, timeout=40)
    output = (stage / 'RESULT.TXT').read_text()
    assert (stage / 'PASS.TXT').exists() and not (stage / 'FAIL.TXT').exists(), output
    summary = re.search(r'^SCRIPT_FILES (\d+) checks 0 failures$', output, re.M)
    cycles = re.search(r'^CYCLES 100 six-slot rounds farheap(\d+) nearheap(\d+) JFT-preserved$', output, re.M)
    assert summary and cycles, output
    expected = {
        'BINARY.BIN': bytes(range(256)) + bytes(255 - n for n in range(80)),
        'LINES.BIN': b'A\r\nB\nC\x1a',
        'TEXT.TXT': b'A\r\nB\r\nEND\x1aTAIL\r\n',
        'SPARSE.BIN': bytes(70000) + b'A',
        'REPLACE.BIN': b'previous', 'BADCL.BIN': b'', 'BADEND.BIN': b'',
        'GOODEND.BIN': b'kept', 'APPEND.BIN': b'firstsecond!',
        'LONGTXT.BIN': b'A' * 80 + b'\r\nEND',
        **{f'SLOT{n}.BIN': b'cycle' for n in range(6)},
    }
    for name, data in expected.items():
        assert (stage / name).read_bytes() == data, name
    assert not (stage / 'ABSENT').exists() and not (stage / 'INVALID.BIN').exists()
    assert sha(binary) == before == sha(stage / binary.name)
    report = dict(passed=True, DOS_summary=summary[0], assertions=int(summary[1]),
                  cycles=100, simultaneous_slots=6, binary_sha256=before,
                  heap_observation=dict(far_used_blocks=int(cycles[1]), near_used_blocks=int(cycles[2]),
                                        addresses_and_sizes_preserved=True, inherited_JFT_entries_preserved=20),
                  manifest_sha256=sha(OUT / 'manifest.json'), checker_sha256=sha(Path(__file__)),
                  result_sha256=sha(stage / 'RESULT.TXT'), original_inputs=[],
                  files={name: dict(bytes=len(data), sha256=sha(stage / name))
                         for name, data in expected.items()},
                  scope='Actual native13 handlers and3 helpers over real owned DOS stdio. Binary/text bytes, CRLF/controlZ, 32bit positions beyond64KiB, read-only errors, failed replacement, explicit and cleanup DOS-close faults, six-slot100-cycle near/far heap and JFT identity, guarded string writes. Typed operand/writeback/returning-warning/lowercase callbacks are test boundaries; actual interpreter/compiler/abort/CHAIN integration and original CRT equivalence remain separate.')
    (stage / 'checks.json').write_text(json.dumps(report, indent=2) + '\n')
    (OUT / 'checks.json').write_text(json.dumps(dict(report, run=str(stage.relative_to(ROOT))), indent=2) + '\n')
    print(report['DOS_summary'], ';', len(expected), 'byte-exact files; result:', stage)


if __name__ == '__main__':
    main()
