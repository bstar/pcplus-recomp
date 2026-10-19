#!/usr/bin/env python3
"""Bounded private original-ASPCOMP call/frame/control-flow emission oracle.

No generated ASX is executed. Output offsets are displayed literally; this is
not a general decoder or replacement compiler.
"""
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
    cases = {}
    def main(name, body, tail=''):
        cases[name] = 'proc main\n'+body+'\nendproc\n'+tail
    main('EMPTY', '')
    main('EXIT', 'exit')
    main('CALLF', 'call helper', 'proc helper\npause 7\nendproc\n')
    main('GOSUBF', 'gosub helper', 'proc helper\npause 7\nendproc\n')
    cases['CALLB'] = 'proc helper\npause 7\nendproc\nproc main\ncall helper\nendproc\n'
    main('CALL2', 'call helper\ncall helper', 'proc helper\npause 7\nendproc\n')
    main('CALLLOC', 'call helper', 'proc helper\ninteger value\npause value\nendproc\n')
    main('MAINLOC', 'integer value\ncall helper', 'proc helper\npause 7\nendproc\n')
    main('BOTHLOC', 'integer value\ncall helper', 'proc helper\ninteger value\npause value\nendproc\n')
    main('NESTCALL', 'call helper', 'proc helper\ncall inner\nendproc\nproc inner\npause 7\nendproc\n')
    main('CALLSELF', 'call main')
    for name, body in {'IF1':'if 1\npause 7\nendif', 'IF0':'if 0\npause 7\nendif',
        'IFELSE':'if 1\npause 7\nelse\npause 8\nendif',
        'IFELIF':'if 1\npause 7\nelseif 0\npause 8\nendif',
        'IFCHAIN':'if 1\npause 7\nelseif 0\npause 8\nelse\npause 9\nendif',
        'IFNEST':'if 1\nif 0\npause 7\nendif\nendif',
        'WHILE0':'while 0\npause 7\nendwhile',
        'WHILE1':'while 1\npause 7\nendwhile',
        'WHILEX':'while 1\npause 7\nexitwhile\npause 8\nendwhile',
        'WHILEL':'while 1\npause 7\nloopwhile\npause 8\nendwhile',
        'WNEST':'while 1\nwhile 0\nexitwhile\nendwhile\nloopwhile\nendwhile',
        'WHIFX':'while 1\nif 1\nexitwhile\nendif\nendwhile',
        'BADX':'exitwhile', 'BADL':'loopwhile', 'BADEND':'endif',
        'IFCMP':'integer value\nif value = 7\npause 8\nendif',
        'WVAR':'integer value\nvalue = 3\nwhile value\nvalue = value - 1\nendwhile',
    }.items():
        main(name, body)
    for name, kind, use, arg in [('INT','intparm','pause value','7'),
                                ('LONG','longparm','pause value','7'),
                                ('STR','strparm','transmit value','"HELLO"'),
                                ('FLOAT','floatparm','pause value','7')]:
        main('P'+name, f'call helper {arg}', f'proc helper\n{kind} value\n{use}\nendproc\n')
        main('PN'+name, 'call helper', f'proc helper\n{kind} value\n{use}\nendproc\n')
        main('PL'+name, f'call helper {arg}', f'proc helper\n{kind} value\ninteger local\n{use}\nendproc\n')
    main('P2INT', 'call helper 7 8', 'proc helper\nintparm first, second\npause first\npause second\nendproc\n')
    main('P2COMMA', 'call helper 7,8', 'proc helper\nintparm first, second\npause first\npause second\nendproc\n')
    main('PMIX', 'call helper 7 "HELLO"', 'proc helper\nintparm number\nstrparm word\npause number\ntransmit word\nendproc\n')
    main('RETURN', 'call helper', 'proc helper\nreturn\npause 7\nendproc\n')
    main('RETLOC', 'call helper', 'proc helper\ninteger value\nreturn\npause 7\nendproc\n')
    for label, kind, arg in [('INT','intparm','7'),('LONG','longparm','7'),('STR','strparm','"HELLO"'),('FLOAT','floatparm','7.0')]:
        main('W'+label, f'call helper with {arg}', f'proc helper\n{kind} value\nendproc\n')
        main('WL'+label, f'call helper with {arg}', f'proc helper\n{kind} value\ninteger local\nendproc\n')
    main('W2INT', 'call helper with 7 8', 'proc helper\nintparm first, second\npause first\npause second\nendproc\n')
    main('W2COMMA', 'call helper with 7,8', 'proc helper\nintparm first, second\npause first\npause second\nendproc\n')
    main('WMIX', 'call helper with 7 "HELLO"', 'proc helper\nintparm number\nstrparm word\npause number\ntransmit word\nendproc\n')
    main('WSCOMMA', 'call helper with 7,"HELLO"', 'proc helper\nintparm number\nstrparm word\npause number\ntransmit word\nendproc\n')
    main('WPAREN', 'call helper with (7)', 'proc helper\nintparm number\npause number\nendproc\n')
    main('WINIT', 'call helper with 7', 'proc helper\nintparm number\ninteger local = 8\npause number\npause local\nendproc\n')
    padding = ('transmit "'+'A'*80+'"\n')*800
    main('FARCALL', 'call helper\n'+padding, 'proc helper\npause 7\nendproc\n')
    cases['FARMAIN'] = 'proc helper\n'+padding+'endproc\nproc main\ncall helper\nendproc\n'
    for label, arg in [('L32768','32768'),('L65535','65535'),('LMAX','2147483647'),('LMIN','-2147483648'),('LOVER','2147483648'),('LSUFF','7L'),('LHEX','0x8000')]:
        main(label, f'call helper with {arg}', 'proc helper\nlongparm value\nendproc\n')
    main('LVAR', 'long value\ncall helper with value', 'proc helper\nlongparm number\nendproc\n')
    main('LFROMI', 'integer value\ncall helper with value', 'proc helper\nlongparm number\nendproc\n')
    main('FARIF', 'if 1\n'+padding+'endif')
    main('FARWHILE', 'while 1\n'+padding+'endwhile')
    return {name: text.replace('\n', '\r\n').encode('ascii') for name, text in cases.items()}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--only', action='append')
    args = p.parse_args()
    out = args.output.resolve()
    assert out.parent == ROOT/'analysis/aspect-vm-runtime' and out.name.startswith('control-')
    original = ROOT/'analysis/pcplus-install/ASPCOMP.EXE'
    binary = original.read_bytes()
    assert sha(binary) == COMPILER_SHA
    out.mkdir(parents=True, exist_ok=False)
    (out/'ASPCOMP.EXE').write_bytes(binary)
    sources = corpus()
    if args.only:
        assert all(n in sources for n in args.only) and len(set(args.only)) == len(args.only)
        sources = {n: sources[n] for n in args.only}
    batch = ['@echo off']
    for name, data in sources.items():
        assert 1 <= len(name) <= 8
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
            record.update(hex=compiled.hex(' '), asx_sha256=sha(compiled), bytes=len(compiled),
                indexed_bytes=[dict(offset=i, hex=f'{b:02x}') for i, b in enumerate(compiled)])
        records.append(record)
    report = dict(compiler_sha256=COMPILER_SHA, harness_sha256=sha(Path(__file__).read_bytes()),
        cases=records, scope='Original compiler control-flow emission oracle; generated ASX not executed, indexed bytes are literal observations rather than a universal decoder.')
    (out/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    for r in records:
        diagnostic = next((s for s in r['diagnostic'].splitlines() if s.startswith('Error')), r['diagnostic'].splitlines()[-1])
        value = r.get('hex', diagnostic)
        print(r['name'], value if len(value)<512 else value[:384]+f' ... [{r["bytes"]} bytes]')
    print(json.dumps(dict(cases=len(records), accepted=sum(r['success'] for r in records)), indent=2))


if __name__ == '__main__':
    main()
