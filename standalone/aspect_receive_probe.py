#!/usr/bin/env python3
"""Optional original-compiler oracle for authored receive command compiler grammar."""
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

    def add(name, declarations, body, expected=None, helper='', serial=None):
        source = declarations + '\nproc main\n' + body + '\nendproc\n' + helper
        cases[name] = dict(source=source.replace('\n', '\r\n'), expected=expected, serial=serial)

    for prefix, command in [('GC', 'comgetc'), ('GD', 'comgetcd')]:
        add(prefix+'INT', 'integer outcome', command+' outcome')
        add(prefix+'NONE', '', command)
        add(prefix+'NUM', '', command+' 7')
        add(prefix+'LONG', 'long outcome', command+' outcome')
        add(prefix+'STR', 'string outcome', command+' outcome')
        add(prefix+'TIME', 'integer outcome', command+' outcome 1')
        add(prefix+'LOC', 'integer outcome', 'integer val\n'+command+' val\noutcome = val')
        add(prefix+'PARM', 'integer outcome', 'call worker with 7', helper='proc worker\nintparm val\n'+command+' val\noutcome = val\nendproc\n')
    for index, args in enumerate(['buffer', 'buffer 1', 'buffer 1 2', 'buffer 1 2 3',
                                  '1 buffer', 'buffer "END"', 'buffer "END" 1',
                                  'buffer 1 "END"', 'buffer 1 2 "END"', 'buffer FOREVER',
                                  'buffer 80 1', 'buffer 1 FOREVER', 'buffer 80 1 13']):
        add('RG'+str(index), 'string buffer', 'rget '+args)
    for index, args in enumerate(['', '1', '0', '-1', '32767', '32768', '1L', '1.0',
                                  '1 2', 'FOREVER', '"x"', 'ticks', 'ticks 1']):
        add('WQ'+str(index), 'integer ticks', 'waitquiet '+args)
    for prefix, command in [('GC', 'comgetc'), ('GD', 'comgetcd'), ('RG', 'rget'), ('WQ', 'waitquiet')]:
        add(prefix+'STAT', 'integer outcome', 'outcome = '+command)
    for name, decl, body, helper in [
        ('GCBIN', 'integer first,second,third', 'comgetc first\ncomgetc second\ncomgetc third', ''),
        ('GCREPEAT', 'integer first,second', 'comgetc first\ncomgetc second', ''),
        ('GDDELAY', 'integer outcome', 'comgetcd outcome', ''),
        ('RGLOCAL', 'string outcome', 'string value = "OLD"\nrget value 5 1\noutcome = value', ''),
        ('RGPARM', 'string outcome', 'call worker with "OLD"', 'proc worker\nstrparm value\nrget value 5 1\noutcome = value\nendproc\n'),
        ('RGGLOB', 'string buffer', 'buffer = "OLD"\nrget buffer 5 1', ''),
        ('RGFIXED', 'string outcome', 'rget s0 5 1\noutcome = s0', ''),
        ('RGLIT', '', 'rget "LITERAL" 5 1', ''),
        ('RGINT', 'integer outcome', 'rget outcome 5 1', ''),
        ('RGLONG', 'long outcome', 'rget outcome 5 1', ''),
        ('RGMAX0', 'string buffer', 'rget buffer 0 1', ''),
        ('RGMAX81', 'string buffer', 'rget buffer 81 1', ''),
        ('RGMAXNEG', 'string buffer', 'rget buffer -1 1', ''),
        ('RGTM0', 'string buffer', 'rget buffer 5 0', ''),
        ('RGTMNEG', 'string buffer', 'rget buffer 5 -1', ''),
        ('RGTMWIDE', 'string buffer', 'rget buffer 5 32768', ''),
        ('RGTMLONG', 'string buffer', 'rget buffer 5 1L', ''),
        ('RGTMFLT', 'string buffer', 'rget buffer 5 1.0', ''),
        ('RGVARS', 'string buffer', 'integer length = 5,deadline = 1\nrget buffer length deadline', ''),
        ('RGMXLONG', 'string buffer\nlong length', 'rget buffer length 1', ''),
        ('WQOPT0', '', 'waitquiet 1 0', ''),
        ('WQOPTNEG', '', 'waitquiet 1 -1', ''),
        ('WQOPTFOR', '', 'waitquiet 1 FOREVER', ''),
        ('WQTMWIDE', '', 'waitquiet 1 32768', ''),
        ('WQTMFLT', '', 'waitquiet 1 1.0', ''),
        ('WQLOCAL', '', 'integer quiet = 1,total = 2\nwaitquiet quiet total', ''),
        ('WQPARM', '', 'call worker with 1 2', 'proc worker\nintparm quiet,total\nwaitquiet quiet total\nendproc\n'),
        ('WQLONG', 'long quiet', 'waitquiet quiet 2', ''),
        ('STATFOR', 'integer outcome', 'outcome = FOREVER', ''),
        ('STATDATA', 'integer outcome', 'outcome = COMDATA', ''),
        ('STATFND', 'integer outcome', 'outcome = FOUND', ''),
    ]:
        add(name, decl, body, helper=helper)
    add('GCEMPTY', 'integer outcome', 'comgetc outcome')
    add('GDDATA', 'integer outcome', 'comgetcd outcome')
    add('RGFULL', 'string buffer', 'rget buffer 80 1')
    add('RGBIN', 'string buffer\ninteger first,second', 'rget buffer 5 1\nstrpeek buffer 1 first\nstrpeek buffer 2 second')
    add('RGEMPTY', 'string buffer', 'rget buffer 80 1')
    add('RGTIME', 'string buffer', 'rget buffer 80 1')
    add('RGWRAP', 'string buffer', 'rget buffer 80 1')
    add('RGZEROQ', 'string buffer', 'rget buffer 0 1')
    add('WQBURST', '', 'waitquiet 1 3')
    add('WQSHORT', '', 'waitquiet 2 1')
    add('WQFSTRM', '', 'waitquiet 2 FOREVER')
    add('WQTIE', '', 'waitquiet 1 1')
    add('WQZEROT', '', 'waitquiet 0 0')
    add('STATD0', 'integer outcome', 'outcome = COMDATA')

    def model(name, data=b'', *, seconds_step=0):
        cases[name]['serial'] = dict(enabled=True, input_hex=data.hex(), send_after_tx_hex='',
            case_sensitive=False, dos_peer=False, initial_ticks=0, tick_step=1,
            initial_seconds=0, seconds_step=seconds_step)

    def expect(name, values, data=b'', *, seconds_step=0):
        model(name, data, seconds_step=seconds_step)
        cases[name]['expected'] = dict(tx_hex='', stdout_hex='', **values)

    # Loader D770 increments E382 after D6EA's reset: effective COMGETC/Cd
    # defaults suppress echo even though displayE37E=1. No console bytes here.
    for name, data, value in [
        ('GCINT', b'A', 65), ('GCLOC', b'\xff', 255), ('GCPARM', b'\x00', 0),
        ('GDINT', b'\r', 13), ('GDLOC', b'B', 66), ('GDPARM', b'\x7f', 127),
        ('GCEMPTY', b'', 65535), ('GDDELAY', b'', 65535), ('GDDATA', b'\x1a', 26),
    ]:
        expect(name, {'integer0': value}, data)
    expect('GCBIN', {'integer0': 0, 'integer1': 128, 'integer2': 255}, bytes.fromhex('0080ff'))
    expect('GCREPEAT', {'integer0': 65, 'integer1': 65535}, b'A')

    rget = {
        'RG0': (b'HELLO\rTAIL', 'HELLO', 0, 4),
        'RG1': (b'AB\r', 'A', 0, 2), 'RG2': (b'AB\r', 'A', 0, 2),
        'RG9': (b'AB\r', 'A', 0, 2), 'RG10': (b'HELLO\rTAIL', 'HELLO', 0, 4),
        'RG11': (b'AB\r', 'A', 0, 2),
        'RGLOCAL': (b'NEW\r', 'NEW', 0, 0), 'RGPARM': (b'NEW\r', 'NEW', 0, 0),
        'RGGLOB': (b'NEW\r', 'NEW', 0, 0), 'RGFIXED': (b'NEW\r', 'NEW', 0, 0),
        'RGMAX0': (b'', '', 1, 0), 'RGTM0': (b'ABC\r', '', 1, 4),
        'RGVARS': (b'NEW\r', 'NEW', 0, 0),
        'RGFULL': (b'A' * 80, 'A' * 80, 0, 0),
        'RGBIN': (bytes.fromhex('4100ff0d'), 'A', 0, 0),
        'RGEMPTY': (b'\r', '', 0, 0), 'RGTIME': (b'', '', 1, 0),
        'RGWRAP': (b'', '', 1, 0),
    }
    quiet = {
        'WQ0': (b'', 0, 0), 'WQ1': (b'', 0, 0), 'WQ2': (b'', 0, 0),
        'WQ4': (b'', 1, 0), 'WQ8': (b'', 0, 0), 'WQ9': (b'', 0, 0),
        'WQ11': (b'', 0, 0), 'WQ12': (b'', 0, 0),
        'WQOPTFOR': (b'', 0, 0), 'WQLOCAL': (b'', 0, 0),
        'WQPARM': (b'', 0, 0), 'WQBURST': (b'A', 0, 0),
        'WQSHORT': (b'A', 1, 0), 'WQFSTRM': (b'A', 0, 0), 'WQTIE': (b'', 0, 0),
    }
    def observe(name, data, status, remaining, text=None):
        case = cases[name]
        prior = case['source'].split('proc main', 1)[0].splitlines()
        # Independent declared bank index, not a compiler output observation.
        first = sum(len(line.split(None, 1)[1].split(',')) for line in prior
                    if line.startswith('integer '))
        case['source'] = case['source'].replace('proc main\r\n',
            'integer statuscode,good,remaining\r\nproc main\r\n', 1)
        case['source'] = case['source'].replace('endproc\r\n',
            'statuscode = failure\r\ngood = success\r\nremaining = COMDATA\r\nendproc\r\n', 1)
        values = {f'integer{first}': status, f'integer{first+1}': int(status == 0),
                  f'integer{first+2}': remaining}
        if text is not None:
            values['string0'] = text
        expect(name, values, data, seconds_step=int(not data))
    for name, (data, text, status, remaining) in rget.items():
        observe(name, data, status, remaining, text)
    cases['RGBIN']['expected'].update(integer0=0, integer1=255)
    cases['RGWRAP']['serial'].update(initial_seconds=59, seconds_step=1)
    for name, (data, status, remaining) in quiet.items():
        observe(name, data, status, remaining)
    for name in ('RGMAX81', 'RGMAXNEG', 'RGTMNEG', 'WQ3', 'WQOPT0', 'WQOPTNEG', 'WQZEROT'):
        expect(name, dict(error='operand', native_error=1))
    expect('STATFOR', {'integer0': 1})
    expect('STATDATA', {'integer0': 3}, b'ABC')
    expect('STATD0', {'integer0': 0})
    cases['RGZEROQ'].update(expected={}, compiler_only_reason='Native max0 tests the endpointer rather than length and can overrun81-byte destination with an unterminated stream; queued-byte quirk is not executed in general VM corpus.')
    cases['STATFND'].update(expected={}, compiler_only_reason='FOUND builtin23 reads unrelated E39C; this phase does not establish its producer semantics or wire it as a new general service.')
    return cases


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    assert out.parent == ROOT / 'analysis/aspect-receive' and out.name.startswith('compiler-')
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
