#!/usr/bin/env python3
"""Actual DOS8086 HITKEY child client with controlled scalar parent requests."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
FLAGS = ['ASPECT_EXTERNAL_RENDER', 'ASPECT_EXTERNAL_UNWIND', 'ASPECT_SNAPSHOT_LEASE',
         'ASPECT_ALARM_VM', 'ASPECT_EMULATE_VM', 'ASPECT_GET_DISPLAY',
         'ASPECT_GET_POLICY', 'ASPECT_COMPILER_PARENT_LEASE', 'ASPECT_TERMINAL_QUERY',
         'ASPECT_HITKEY_PARENT']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--screen-profile', action='store_true',
                   help='Exercise shared private-owner admission under capability27')
    a = p.parse_args()
    out = a.output.resolve()
    assert out.is_relative_to(ROOT/'build') and not out.exists()
    out.mkdir(parents=True)
    dependencies = [Path(__file__).resolve(), ROOT/'standalone/hitkey_client_driver.c',
                    ROOT/'src/aspect/resident_render.c', *sorted((ROOT/'src/aspect').glob('*.h'))]
    sources = {str(p.relative_to(ROOT)): sha(p) for p in dependencies}
    flags = FLAGS+(['ASPECT_STATE_BUILTINS_PARENT', 'ASPECT_SCREEN_PARENT'] if a.screen_profile else [])
    subprocess.run(['wcl', '-q', '-bt=dos', '-0', '-ms', '-ecc', '-s', '-ob', '-os',
                    '-w4', '-we', '-k8192', *['-d'+f for f in flags],
                    '-i='+str(ROOT/'src/aspect'), '-fm=CLIENT.map', '-fe=CLIENT.EXE',
                    str(ROOT/'standalone/hitkey_client_driver.c')], cwd=out, check=True)
    (out/'RUN.BAT').write_bytes(b'@echo off\r\nCLIENT >CHECK.LOG\r\nif errorlevel 1 goto failed\r\necho PASS>RESULT.TXT\r\ngoto done\r\n:failed\r\necho FAIL>RESULT.TXT\r\n:done\r\nexit\r\n')
    (out/'dosbox.conf').write_text('[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\nfpu=false\ncycles=fixed 30000\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "'+str(out)+'"\nc:\ncall RUN.BAT\nexit\n')
    with (out/'dosbox.log').open('w') as log:
        subprocess.run(['dosbox-x', '-fastlaunch', '-nogui', '-conf', str(out/'dosbox.conf')],
                       cwd=out, stdout=log, stderr=log,
                       env=dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy'),
                       check=True, timeout=30)
    transcript = (out/'CHECK.LOG').read_text().strip()
    assert (out/'RESULT.TXT').read_text().strip() == 'PASS', transcript
    match = re.fullmatch(r'HITKEY_CLIENT (\d+) cases (\d+) checks 0 failures', transcript)
    assert match, transcript
    assert all(sha(ROOT/p) == digest for p, digest in sources.items())
    result = dict(passed=True, cases=int(match[1]), checks=int(match[2]),
                  compile_flags=flags, capability=27 if a.screen_profile else 25,
                  screen_profile=a.screen_profile, sources=sources, original_inputs=[], transcript=transcript,
                  artifacts={p.name: sha(p) for p in out.iterdir() if p.is_file()},
                  scope=__doc__+' Fifteen full WORD values and fifteen changed-future-key cases; exact op30/31 with payload0, no premature destination publication, refusal/bad tags at either phase, all typed1..14 errors, pre/post-client faults and precedence, PROGRAM/snapshot/seven in-flight wait guards, all seven field/window/confirm owner combinations admitted, serial0/2/FFFF, detached/invalid output, canaries and successful retry. No transport/poll/WHEN callback boundary called. The parent one-sample/retire behavior and client admission are controlled models; real native peek, parent pending-word identity, far bridge, capability mismatch and physical hardware require separate tests.')
    (out/'result.json').write_text(json.dumps(result, indent=2)+'\n')
    print(transcript)


if __name__ == '__main__':
    main()
