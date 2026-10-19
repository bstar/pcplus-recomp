#!/usr/bin/env python3
"""Private bounded original-ASPCOMP declaration/header oracle (no ASX execution)."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
COMPILER_SHA = '5664fdfae375774da5303cc8b53c00ef773a6650132de73c7206e46ddc05039a'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def corpus():
    cases = {
        'EMPTY': 'proc main\nendproc\n',
        'INT1': 'proc main\ninteger value\nendproc\n',
        'LONG1': 'proc main\nlong value\nendproc\n',
        'STR1': 'proc main\nstring value\nendproc\n',
        'STR2': 'proc main\nstring first\nstring second\nendproc\n',
        'STRLIST': 'proc main\nstring first, second\nendproc\n',
        'INTLIST': 'proc main\ninteger first, second\nendproc\n',
        'LONGLIST': 'proc main\nlong first, second\nendproc\n',
        'GSTR': 'string value\nproc main\nendproc\n',
        'GINT': 'integer value\nproc main\nendproc\n',
        'GLONG': 'long value\nproc main\nendproc\n',
        'MIXED': 'proc main\ninteger number\nlong wide\nstring userstr\nendproc\n',
        'STRUSE': 'proc main\nstring userstr\ntransmit userstr\nendproc\n',
        'BUILTIN': 'proc main\ntransmit s0\ntransmit s9\nendproc\n',
        'REDECL': 'proc main\nstring userstr\nstring userstr\nendproc\n',
        'TWOLOCAL': 'proc main\nstring first\ncall helper\nendproc\nproc helper\nstring second\nendproc\n',
        'SAMENAME': 'proc main\nstring userstr\ncall helper\nendproc\nproc helper\nstring userstr\nendproc\n',
        'GLOBAL': 'string global\nproc main\nstring local\ncall helper\nendproc\nproc helper\nstring other\nendproc\n',
        'STRLEN': 'proc main\nstring value 80\nendproc\n',
        'STRARR': 'proc main\nstring value[2]\nendproc\n',
        'INTINIT': 'proc main\ninteger value = 7\nendproc\n',
        'STRINIT': 'proc main\nstring value = "HELLO"\nendproc\n',
    }
    for kind in ['string', 'integer', 'long']:
        for count in [9, 10, 11, 31, 32, 33, 63, 64, 65, 127, 128, 129, 254, 255, 256]:
            name = kind[:1].upper()+f'{count:03}'
            cases[name] = 'proc main\n'+''.join(f'{kind} v{i}\n' for i in range(count))+'endproc\n'
    for kind in ['string', 'integer', 'long']:
        for count in [1, 2, 31, 32, 63, 64, 127, 128, 129, 254, 255, 256, 257]:
            name = 'G'+kind[:1].upper()+f'{count:03}'
            cases[name] = ''.join(f'{kind} g{i}\n' for i in range(count))+'proc main\nendproc\n'
    cases['GMIX'] = 'string gs1,gs2\ninteger gi1,gi2\nlong gl1,gl2\nproc main\nstring ls1\nendproc\n'
    cases['SHADOW'] = 'string value\nproc main\nstring value\ntransmit value\nendproc\n'
    cases['SPLIT128'] = 'proc main\n'+''.join(f'string v{i}\n' for i in range(128))+'call helper\nendproc\nproc helper\nstring second\nendproc\n'
    cases['SPLIT256'] = 'proc main\n'+''.join(f'string v{i}\n' for i in range(128))+'call helper\nendproc\nproc helper\n'+''.join(f'string w{i}\n' for i in range(128))+'endproc\n'
    cases['MIX128'] = 'proc main\n'+''.join(f'{["string","integer","long"][i%3]} v{i}\n' for i in range(128))+'endproc\n'
    cases['MIX129'] = 'proc main\n'+''.join(f'{["string","integer","long"][i%3]} v{i}\n' for i in range(129))+'endproc\n'
    cases['GMIX128'] = ''.join(f'{["string","integer","long"][i%3]} v{i}\n' for i in range(128))+'proc main\nendproc\n'
    cases['GMIX129'] = ''.join(f'{["string","integer","long"][i%3]} v{i}\n' for i in range(129))+'proc main\nendproc\n'
    cases['GALL128'] = ''.join(f'{kind} {kind[0]}v{i}\n' for kind in ['string','integer','long'] for i in range(128))+'proc main\nendproc\n'
    cases['GLOC128'] = ''.join(f'string gv{i}\n' for i in range(128))+'proc main\n'+''.join(f'string lv{i}\n' for i in range(128))+'endproc\n'
    cases['GSTRUSE'] = 'string value\nproc main\ntransmit value\nendproc\n'
    cases['GSTR2USE'] = 'string first,second\nproc main\ntransmit first\ntransmit second\nendproc\n'
    cases['GINTUSE'] = 'integer value\nproc main\nvalue = 7\nendproc\n'
    cases['GLONGUSE'] = 'long value\nproc main\nvalue = 7\nendproc\n'
    return {name: text.replace('\n', '\r\n').encode('ascii') for name, text in cases.items()}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--only', action='append', help='Run selected named cases; repeat for multiple names')
    args = p.parse_args()
    out = args.output.resolve()
    assert out.parent == ROOT/'analysis/aspect-vm-runtime' and out.name.startswith('header-')
    original = ROOT/'analysis/pcplus-install/ASPCOMP.EXE'
    binary = original.read_bytes()
    assert sha(binary) == COMPILER_SHA
    out.mkdir(parents=True, exist_ok=False)
    (out/'ASPCOMP.EXE').write_bytes(binary)
    batch = ['@echo off']
    sources = corpus()
    if args.only:
        assert len(set(args.only)) == len(args.only) and all(name in sources for name in args.only)
        sources = {name: sources[name] for name in args.only}
    for name, data in sources.items():
        (out/(name+'.ASP')).write_bytes(data)
        batch += [f'ASPCOMP {name}.ASP > {name}.LOG', f'if errorlevel 1 goto E{name}',
                  f'echo ZERO>{name}.RC', f'goto D{name}', f':E{name}',
                  f'echo NONZERO>{name}.RC', f':D{name}']
    batch += ['echo COMPLETE>DONE.TXT']
    (out/'RUN.BAT').write_bytes(('\r\n'.join(batch)+'\r\n').encode())
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
        asx = out/(name+'.ASX')
        success = b'Script file successfully compiled!' in log
        rc = (out/(name+'.RC')).read_text().strip()
        assert success == asx.exists() and (rc == 'ZERO') == success and rc in ('ZERO', 'NONZERO')
        record = dict(name=name, source_sha256=sha(data), success=success,
            return_class=rc, diagnostic=log.decode('cp437').strip(), log_sha256=sha(log))
        if asx.exists():
            compiled = asx.read_bytes()
            record.update(header_byte=compiled[0], hex=compiled.hex(' '),
                          asx_sha256=sha(compiled), bytes=len(compiled))
        records.append(record)
    report = dict(compiler_sha256=COMPILER_SHA, harness_sha256=sha(Path(__file__).read_bytes()),
        cases=records, scope='Original compiler declaration/header oracle; source-owned scripts, no generated ASX executed, no original application or maintained compiler/VM behavior claimed.')
    (out/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    for r in records:
        print(r['name'], r.get('header_byte', '-'), r.get('hex', r['diagnostic'].splitlines()[-1]))
    print(json.dumps(dict(cases=len(records), accepted=sum(r['success'] for r in records)), indent=2))


if __name__ == '__main__':
    main()
