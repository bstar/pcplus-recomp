#!/usr/bin/env python3
"""Optional original-compiler oracle for authored console and comparison command grammar."""
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

    def add(name, declarations, body, expected=None, helper=''):
        source = declarations + '\nproc main\n' + body + '\nendproc\n' + helper
        cases[name] = dict(source=source.replace('\n', '\r\n'), expected=expected)

    add('MSGONE', '', 'message "HELLO"')
    add('MSGEMPTY', '', 'message ""')
    add('MSGCTRL', '', 'message "A^MB^JC"')
    add('MSGCAR', '', 'message "^A^@^^"')
    add('MSGHIGH', '', 'message "éÇ"')
    add('MSGGLB', 'string msgbuf', 'msgbuf = "GLOBAL"\nmessage msgbuf')
    add('MSGLOCAL', '', 'string msgbuf = "LOCAL"\nmessage msgbuf')
    add('MSGPARM', '', 'call worker with "PARAM"', helper='proc worker\nstrparm msgbuf\nmessage msgbuf\nendproc\n')
    add('MSGTWICE', '', 'message "ONE"\nmessage "TWO"')
    add('MSGMAX', '', 'message "' + 'A' * 80 + '"')
    add('MSGNUM', '', 'message 7')
    add('MSGMISS', '', 'message')
    add('MSGEXTRA', '', 'message "A" "B"')
    add('EXPLAIN', 'integer outcome', 'outcome = 1\nexit\noutcome = 9')
    add('EXNEST', 'integer outcome', 'call worker\noutcome = 9', helper='proc worker\noutcome = 7\nexit\nendproc\n')
    add('EXARG', '', 'exit 7')
    add('EXSTR', '', 'exit "x"')
    add('PZ', '', 'pause 0')
    add('PONE', '', 'pause 1')
    add('PSUFF', '', 'pause 7L')
    add('PNSUFF', '', 'pause -7L')
    add('PN', '', 'pause 7')
    add('PNEG', '', 'pause -1')
    add('PMIN', '', 'pause -32768')
    add('PMAX', '', 'pause 32767')
    add('PUNSIGN', '', 'pause 32768')
    add('PWORD', '', 'integer ticks = 3\npause ticks')
    add('PLVAR', '', 'long ticks = 3L\npause ticks')
    add('PLONG', '', 'pause 65537')
    add('PFLOAT', '', 'pause 7.0')
    add('PSTR', '', 'pause "x"')
    add('PMISS', '', 'pause')
    add('TXONE', '', 'transmit "AT^M"')
    add('TXEMPTY', '', 'transmit ""')
    add('TXNUM', '', 'transmit 7')
    add('TXEXTRA', '', 'transmit "A" "B"')
    add('WFONE', '', 'waitfor "login:"')
    add('WFTIME', '', 'waitfor "login:" 5')
    add('WFREV', '', 'waitfor 5 "login:"')
    add('WFWIDE', '', 'waitfor "login:" 32768')
    add('WFSUFF', '', 'waitfor "login:" 7L')
    add('WFEMPTY', '', 'waitfor "" 0')
    add('WFMISS', '', 'waitfor')
    add('RS2', 'integer outcome', 'rstrcmp "ABC" "ABC"\noutcome = failure')
    add('RS3', 'integer outcome', 'rstrcmp "ABC" "ABD" 2\noutcome = failure')
    add('RSCASE', 'integer outcome', 'rstrcmp "abc" "ABC"\noutcome = failure')
    add('RSDIFF', 'integer outcome', 'rstrcmp "ABC" "ABD"\noutcome = failure')
    add('RSPREF', 'integer outcome', 'rstrcmp "AB" "ABC"\noutcome = failure')
    add('RSEMPTY', 'integer outcome', 'rstrcmp "" ""\noutcome = failure')
    add('RSZERO', 'integer outcome', 'rstrcmp "ABC" "ABD" 0\noutcome = failure')
    add('RSBAD', '', 'rstrcmp "ABC" "ABD" 81')
    add('RSLOCAL', 'integer outcome', 'string first = "ABC",second = "ABD"\nrstrcmp first second 2\noutcome = failure')
    add('RS4', '', 'rstrcmp "ABC" "ABD" 0 2')
    add('RSMISS', '', 'rstrcmp "ABC"')
    add('RSNUM', '', 'rstrcmp 1 2 3')
    predictions = {
        'MSGONE': {'stdout_hex': '48454c4c4f0d0a'},
        'MSGEMPTY': {'stdout_hex': '0d0a'},
        'MSGCTRL': {'stdout_hex': '410d420a430d0a'},
        'MSGCAR': {'stdout_hex': '01ff1e0d0a'},
        'MSGHIGH': {'stdout_hex': '82800d0a'},
        'MSGGLB': {'stdout_hex': '474c4f42414c0d0a', 'string0': 'GLOBAL'},
        'MSGLOCAL': {'stdout_hex': '4c4f43414c0d0a'},
        'MSGPARM': {'stdout_hex': '504152414d0d0a'},
        'MSGTWICE': {'stdout_hex': '4f4e450d0a54574f0d0a'},
        'MSGMAX': {'stdout_hex': ('41' * 80) + '0d0a'},
        'EXPLAIN': {'integer0': 1}, 'EXNEST': {'integer0': 7},
        'PZ': {}, 'PONE': {},
        'PNEG': {'error': 'operand', 'native_error': 1},
        'PMIN': {'error': 'operand', 'native_error': 1},
        'PN': {}, 'PMAX': {}, 'PWORD': {},
        'TXONE': {'error': 'unsupported'}, 'TXEMPTY': {'error': 'unsupported'},
        'WFONE': {'error': 'unsupported'}, 'WFTIME': {'error': 'unsupported'},
        'WFEMPTY': {'error': 'unsupported'},
        'RS2': {'integer0': 0}, 'RS3': {'integer0': 0},
        'RSCASE': {'integer0': 1}, 'RSDIFF': {'integer0': 65535},
        'RSPREF': {'integer0': 65535}, 'RSEMPTY': {'integer0': 0},
        'RSZERO': {'integer0': 0},
        'RSBAD': {'error': 'operand', 'native_error': 1},
        'RSLOCAL': {'integer0': 0},
    }
    for name, expected in predictions.items():
        cases[name]['expected'] = expected
    for name in ('PN', 'PMAX', 'PWORD'):
        cases[name]['dos_excluded_reason'] = 'Compiler grammar only: avoid a native BIOS delay of ' + {'PN': '7', 'PMAX': '32767', 'PWORD': '3'}[name] + ' seconds in regression execution.'
    return cases


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    assert out.parent == ROOT / 'analysis/aspect-console' and out.name.startswith('compiler-')
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
