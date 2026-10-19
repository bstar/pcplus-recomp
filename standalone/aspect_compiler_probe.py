#!/usr/bin/env python3
"""Bounded private ASPCOMP 1.01 DOS oracle; never an ordinary build input.

Run using ./tools/dev --command python3 standalone/aspect_compiler_probe.py
--output analysis/aspect-compiler/LABEL. Original compiler and generated ASX
remain in ignored analysis; this tool does not execute generated scripts.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
COMPILER_SHA256 = '5664fdfae375774da5303cc8b53c00ef773a6650132de73c7206e46ddc05039a'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def corpus():
    cases = {'EMPTY': '', 'EXIT': 'exit', 'BAD': 'xyzzy'}
    for i, text in enumerate(['', 'A', 'B', 'AA', 'AB', 'ABC', 'AAAA', 'AAAAA',
                              'HELLO', 'WORLD', 'HELLO', 'ATNET1^M', '^M',
                              '^J', '^^', 'a', '0', ' '*8, 'A'*32, 'A'*100, 'A'*255, 'A'*256,
                              'A'*63, 'A'*64, 'A'*78, 'A'*79, 'A'*80, 'A'*81,
                              *('A'*n for n in [114,115,116,127,128,244,245,255,256]),
                              'é', 'Ç', '^@', '^A', '^Z', '^?', '^~', '^0', '^1',
                              '\"', '\\', 'A\tB']):
        cases[f'S{i:02}'] = f'transmit "{text}"'
    for i, number in enumerate([0, 1, 2, 3, 10, 127, 128, 255, 256, 257,
                                32767, 32768, 65535, -1]):
        cases[f'N{i:02}'] = f'pause {number}'
    for i, command in enumerate(['set port com1', 'set port com2',
                                'set baudrate 9600', 'set baudrate 38400',
                                'set databits 7', 'set databits 8',
                                'set parity none', 'set parity even',
                                'set stopbits 1', 'set stopbits 2',
                                'emulate ansi', 'emulate vt100',
                                'beep', 'clear', 'hangup', 'waitfor "ABC"',
                                'if 1\ntransmit "YES"\nendif',
                                'while 0\nexit\nendwhile']):
        cases[f'C{i:02}'] = command
    cases['TWICE'] = 'transmit "HELLO"\ntransmit "HELLO"'
    cases['COMMENT'] = '; an ignored comment\ntransmit "HELLO"'
    cases['BLANK'] = '\ntransmit "HELLO"'
    cases['SPACES'] = '   transmit    "HELLO"'
    cases['BEFORE'] = 'clear\ntransmit "HELLO"'
    cases['CASE'] = 'TrAnSmIt "HELLO"'
    cases['PROCS'] = 'call helper\nendproc\nproc helper\ntransmit "HELLO"'
    return {name: ('proc main\n' + body + '\nendproc\n').replace('\n', '\r\n').encode('cp437')
            for name, body in cases.items()}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--compiler', type=Path, default=ROOT/'analysis/pcplus-install/ASPCOMP.EXE')
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    original = args.compiler.resolve()
    assert not original.name.lower().endswith('.analysis.exe')
    compiler = original.read_bytes()
    assert digest(compiler) == COMPILER_SHA256, 'Unexpected compiler; preserve target identity'
    out = args.output.resolve()
    assert out.is_relative_to(ROOT/'analysis/aspect-compiler'), 'Private outputs must stay under ignored analysis/aspect-compiler'
    out.mkdir(parents=True, exist_ok=False)
    (out/'ASPCOMP.EXE').write_bytes(compiler)
    sources = corpus()
    for name, data in sources.items():
        (out/(name+'.ASP')).write_bytes(data)
    # Record compiler return levels separately from human-readable success diagnostics.
    batch = ['@echo off']
    for name in sources:
        batch += [f'ASPCOMP {name}.ASP > {name}.LOG',
                  f'if errorlevel 1 goto E{name}',
                  f'echo ZERO>{name}.RC', f'goto D{name}',
                  f':E{name}', f'echo NONZERO>{name}.RC', f':D{name}']
    batch += ['echo COMPLETE>DONE.TXT']
    (out/'RUN.BAT').write_bytes(('\r\n'.join(batch)+'\r\n').encode('ascii'))
    config = f'''[sdl]
output=surface
[cpu]
core=normal
cputype=386
cycles=fixed 6000
[mixer]
nosound=true
[autoexec]
@echo off
mount c "{out}"
c:
call RUN.BAT
exit
'''
    (out/'dosbox.conf').write_text(config)
    with (out/'dosbox.log').open('w') as log:
        result = subprocess.run(['dosbox-x', '-fastlaunch', '-nogui', '-conf', str(out/'dosbox.conf')],
                                cwd=out, env=dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy'),
                                stdout=log, stderr=log, timeout=60)
    assert result.returncode == 0 and (out/'DONE.TXT').read_text().strip() == 'COMPLETE'
    records = []
    for name, data in sources.items():
        log = (out/(name+'.LOG')).read_bytes()
        binary = out/(name+'.ASX')
        return_class = (out/(name+'.RC')).read_text().strip()
        assert return_class in ('ZERO', 'NONZERO')
        record = dict(name=name, source_sha256=digest(data), log_sha256=digest(log),
                      return_class=return_class,
                      success=b'Script file successfully compiled!' in log,
                      diagnostic=log.decode('cp437').strip())
        if binary.exists():
            value = binary.read_bytes()
            record.update(asx_sha256=digest(value), bytes=len(value), hex=value.hex(' '))
        assert record['success'] == binary.exists(), record
        assert record['success'] == (return_class == 'ZERO'), record
        records.append(record)
    report = dict(compiler_sha256=digest(compiler), harness_sha256=digest(Path(__file__).read_bytes()),
                  original_source=str(original), output=str(out), cases=records,
                  scope='Original DOS compiler oracle only; generated ASX scripts were not executed; no compiler or VM completeness claim.')
    (out/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(dict(output=str(out), cases=len(records), successful=sum(r['success'] for r in records)), indent=2))


if __name__ == '__main__':
    main()
