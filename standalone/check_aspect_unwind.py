#!/usr/bin/env python3
"""Run actual linked8086 DOS nonlocal ASPECT error-unwind composition.

Optional original comparison checks all recovered flat units. Ordinary checks
never read the original executable, install, or REA database.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
from build_aspect_unwind import ROOT, OUT, sha

ORIGINAL_SHA = '6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
EXPECTED = {
    'dispatch':'d2006fe5dd53b6416aec915c9bd58b4ae1a11fc003aafef090279fa2d37520a6',
    'abort':'438b02dabdb0eb38da2426a0a618164c821810d6808bdad328d80dce5f66c8d3',
    'setjmp':'4903e9d5d0bf54876a6c28f86854b6a6fc995b0948ecaa9a910d2d2c0e69c052',
    'longjmp':'10edd48482a91a1412444fb830066c711619b2c31fd432182a19257442ffc2d6',
    'stack':'1aab9bd8ea8c0879214142073ea95bd8d2e5fc8abf1760663fbd607f6e19ea4a',
    'copy':'8f2d99034340eacf7ddcbe1a27e39d854b79bd600525001cb9979524a7d74fb6',
}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--original',type=Path,help='Explicit optional private original executable')
    args=parser.parse_args()
    subprocess.run(['python3',str(ROOT/'standalone/build_aspect_unwind.py')],check=True)
    manifest=json.loads((OUT/'manifest.json').read_text())
    optional=None
    if args.original:
        assert sha(args.original)==ORIGINAL_SHA
        original=args.original.read_bytes()
    for unit in manifest['native_units']:
        path=OUT/(unit['name']+'.bin')
        assert sha(path)==EXPECTED[unit['name']]==unit['flat_sha256']
        if args.original:
            start=unit['file_start']
            assert original[start:start+unit['bytes']]==path.read_bytes()
    if args.original:
        optional=dict(original_sha256=ORIGINAL_SHA,exact_bytes=sum(u['bytes'] for u in manifest['native_units']),
                      units=manifest['native_units'],scope='Exact static byte comparison; linkedDOS execution uses maintained source, not original executable.')
    for name in ('DONE.TXT','PASS.TXT','FAIL.TXT'):(OUT/name).unlink(missing_ok=True)
    config=f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
cycles=max
[mixer]
nosound=true
[autoexec]
@echo off
mount c "{OUT}"
c:
UNWIND >RESULT.TXT
if errorlevel 1 goto failed
echo PASS>PASS.TXT
goto done
:failed
echo FAIL>FAIL.TXT
:done
exit
'''
    (OUT/'dosbox.conf').write_text(config)
    with (OUT/'dosbox.log').open('w') as log:
        subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(OUT/'dosbox.conf')],
            env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),
            stdout=log,stderr=log,check=True,timeout=30)
    summary=(OUT/'DONE.TXT').read_text().strip()
    assert (OUT/'PASS.TXT').exists() and not (OUT/'FAIL.TXT').exists(),(OUT/'RESULT.TXT').read_text()
    assert summary.startswith('ASPECT_UNWIND 72 cases ') and summary.endswith('0 failures'),summary
    report=dict(passed=True,DOS_summary=summary,DOS_cases=72,
        binary_sha256=sha(OUT/'UNWIND.EXE'),manifest_sha256=sha(OUT/'manifest.json'),
        check_sha256=sha(Path(__file__).resolve()),optional_original=optional,
        original_inputs=[] if optional is None else [str(args.original)],
        scope='Recovered dispatcher, abort and real setjmp/longjmp run together in8086 DOS. Source-owned open/service/read/handler/error/wait/file/UI models; no complete interpreter or resource owner.',
        cases='Normal and seven modeled callback fault sites plus actual native stack-overflow105 x two owners x direct/chained scripts x position display off/on. Nested faults poison SI/DI and allocate frames; assert no fallthrough, stack/register/context canaries, untouched overflow destination and exactly-once cleanup/close/finish.')
    target=OUT/('checks-native.json' if optional else 'checks.json')
    target.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
