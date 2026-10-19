#!/usr/bin/env python3
"""Optional original-compiler oracle for authored numeric/text conversions."""
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

    for name, text, value in [
        ('CVIZERO', '0', 0), ('CVIPOS', '12345', 12345), ('CVINEG', '-12345', 53191),
        ('CVIMIN', '-32768', 32768), ('CVIMAX', '32767', 32767),
        ('CVIWRAP', '65537', 1), ('CVIEMPTY', '', 0), ('CVINONE', 'abc', 0),
        ('CVIPRE', 'cost: 42 dollars', 42), ('CVIJUNK', 'x-.x--7z', 65529),
        ('CVIDOT', '.75', 75), ('CVISIGN', '+12', 12), ('CVIHI', 'éÇ-17', 65519),
        ('CVILONG', '4294967297', 1), ('CVISUFF', '12.99', 12),
        ('CVIWS', '  \t-21', 65515), ('CVIZNEG', '-0', 0), ('CVINAN', '--..', 0),
    ]:
        add(name, 'integer outcome', f'atoi "{text}" outcome', {'integer0': value})
    for name, text, value in [
        ('CVLZERO', '0', 0), ('CVLPOS', '2147483647', 2147483647),
        ('CVLMIN', '-2147483648', 2147483648), ('CVLMAX', '4294967295', 4294967295),
        ('CVLWRAP', '4294967296', 0), ('CVLNEG', '-4294967295', 1),
        ('CVLPRE', 'abc -7654321end', 4287312975), ('CVLEMPTY', '', 0),
    ]:
        add(name, 'long outcome', f'atol "{text}" outcome', {'long0': value})
    for name, value, text in [
        ('CVTZERO', '0', '0'), ('CVTPOS', '32767', '32767'),
        ('CVTMIN', '-32768', '-32768'), ('CVTNEG', '-1', '-1'),
    ]:
        add(name, 'string outcome', f'itoa {value} outcome', {'string0': text})
    for name, value, text in [
        ('CVUZERO', '0L', '0'), ('CVUMAX', '2147483647L', '2147483647'),
        ('CVUMIN', '-2147483648L', '-2147483648'), ('CVUNEG', '-1L', '-1'),
    ]:
        add(name, 'string outcome', f'ltoa {value} outcome', {'string0': text})
    add('CVILOC', 'integer outcome', 'string value = "x-123"\natoi value outcome', {'integer0': 65413})
    add('CVIPARM', 'integer outcome', 'call helper with "v=321"', {'integer0': 321},
        'proc helper\nstrparm value\natoi value outcome\nendproc\n')
    add('CVTLOC', 'string outcome', 'integer number = -42\nstring value\nitoa number value\noutcome = value', {'string0': '-42'})
    add('CVCHAIN', 'string outcome\ninteger number', 'atoi "n=-123" number\nitoa number outcome', {'integer0': 65413, 'string0': '-123'})
    add('CVORDER', 'integer outcome', 'atoi outcome "123"')
    add('CVTMISS', 'string outcome', 'itoa outcome')
    add('CVBADTY', 'string outcome', 'atoi "123" outcome')
    add('CVLTYPE', 'integer outcome', 'atol "123" outcome')
    return cases


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    assert out.parent == ROOT / 'analysis/aspect-conversions' and out.name.startswith('compiler-')
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
