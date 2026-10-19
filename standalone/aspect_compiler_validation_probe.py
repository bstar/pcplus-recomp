#!/usr/bin/env python3
"""Independent authored compiler-emission validation oracle."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
COMPILER = '5664fdfae375774da5303cc8b53c00ef773a6650132de73c7206e46ddc05039a'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def corpus():
    cases = {}
    def add(name, decl, body):
        source = decl + '\nproc main\n' + body + '\nendproc\n'
        cases[name] = dict(source=source.replace('\n', '\r\n'))
    decl = 'integer a,b,c,d,z'
    init = 'a = 2\nb = 3\nc = 4\nd = 5\n'
    for name, expr in [('NESTSUB','(a+b)-(c+d)'), ('NESTMUL','(a+b)*(c-d)'),
                       ('NESTDIV','(a+b)/(c-d)'), ('NESTMOD','(a+b)%(c-d)'),
                       ('NESTCMP','(a+b)<(c+d)'), ('NESTADD','(a+b)+(c+d)')]:
        add(name, decl, init + 'z = ' + expr)
    for name, expr in [('BOOLAND','0 && 1'), ('BOOLOR','1 || 0'),
                       ('BOOLA11','1 && 1'), ('BOOLO00','0 || 0'),
                       ('BOOLMIX','1 || 0 && 0'), ('BOOLVAR','a && b')]:
        add(name, decl, init + 'if ' + expr + '\nz = 7\nelse\nz = 9\nendif')
    add('NEWFRAME','integer output','integer rose = 17,oak = 4\noutput = rose * 3 - oak')
    add('NEWSTR','string output','output = "WiFi"\nstrcat output " modem"\nstrupr output')
    add('NEWCONV','string output\nlong number','atol "count:-123456end" number\nltoa number output')
    return cases


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    assert out.parent == ROOT / 'analysis/aspect-compiler-validation' and out.name.startswith('compiler-')
    binary = (ROOT / 'analysis/pcplus-install/ASPCOMP.EXE').read_bytes()
    assert sha(binary) == COMPILER
    out.mkdir(parents=True, exist_ok=False)
    (out / 'ASPCOMP.EXE').write_bytes(binary)
    cases = corpus()
    batch = ['@echo off']
    for name, case in cases.items():
        assert len(name) <= 8
        (out / (name + '.ASP')).write_bytes(case['source'].encode('cp437'))
        batch += [f'ASPCOMP {name}.ASP >{name}.LOG', f'if errorlevel 1 goto E{name}',
                  f'echo ZERO>{name}.RC', f'goto D{name}', f':E{name}',
                  f'echo NONZERO>{name}.RC', f':D{name}']
    batch += ['echo COMPLETE>DONE.TXT']
    (out / 'RUN.BAT').write_bytes(('\r\n'.join(batch) + '\r\n').encode('ascii'))
    config = f'[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=386\ncycles=fixed 6000\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "{out}"\nc:\ncall RUN.BAT\nexit\n'
    (out / 'dosbox.conf').write_text(config)
    with (out / 'dosbox.log').open('w') as log:
        subprocess.run(['dosbox-x', '-fastlaunch', '-nogui', '-conf', str(out / 'dosbox.conf')],
                       cwd=out, env=dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy'),
                       stdout=log, stderr=log, check=True, timeout=60)
    assert (out / 'DONE.TXT').read_text().strip() == 'COMPLETE'
    records = []
    for name, case in cases.items():
        log = (out / (name + '.LOG')).read_bytes()
        compiled = out / (name + '.ASX')
        success = b'Script file successfully compiled!' in log
        rc = (out / (name + '.RC')).read_text().strip()
        assert (rc == 'ZERO') == success == compiled.exists()
        record = dict(name=name, source=case['source'], source_sha256=sha(case['source'].encode('cp437')),
                      success=success, log_sha256=sha(log),
                      errors=[s for s in log.decode('cp437').splitlines() if s.startswith('Error')])
        if success:
            data = compiled.read_bytes()
            record.update(hex=data.hex(' '), asx_sha256=sha(data))
        records.append(record)
        print(name, 'accepted' if success else record['errors'])
    report = dict(compiler_sha256=COMPILER, harness_sha256=sha(Path(__file__).read_bytes()), cases=records,
                  scope='Authored source compilation only; expected values fixed independently before runtime execution.')
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print('accepted', sum(r['success'] for r in records), 'of', len(records))


if __name__ == '__main__':
    main()
