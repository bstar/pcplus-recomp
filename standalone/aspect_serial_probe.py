#!/usr/bin/env python3
"""Optional original-compiler oracle for authored serial-script compiler grammar."""
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

    add('SXTX', '', 'transmit "AT^M"')
    add('SXEMPTY', '', 'transmit ""')
    add('SXCTL', '', 'transmit "A^MB^JC^AD"')
    add('SXHIGH', '', 'transmit "éÇ"')
    add('SXCARA', '', 'transmit "^@^^"')
    add('SXPAUSE', '', 'transmit "A~B"')
    add('SXLOCAL', '', 'string linebuf = "LOCAL^M"\ntransmit linebuf')
    add('SXGLOBAL', 'string linebuf', 'linebuf = "GLOBAL^M"\ntransmit linebuf')
    add('SXPARM', '', 'call worker with "PARAM^M"', helper='proc worker\nstrparm linebuf\ntransmit linebuf\nendproc\n')
    add('SXMAX', '', 'transmit "' + 'A' * 80 + '"')
    add('SXTWICE', '', 'transmit "ONE^M"\ntransmit "TWO^M"')
    add('SWHIT', 'integer outcome', 'transmit "READY^M"\nwaitfor "login:" 2\noutcome = waitfor')
    add('SWCASE', 'integer outcome', 'transmit "READY^M"\nwaitfor "login:" 1\noutcome = waitfor')
    add('SWEMPTY', 'integer outcome', 'waitfor "" 0\noutcome = waitfor')
    add('SWZERO', 'integer outcome', 'waitfor "missing" 0\noutcome = waitfor')
    add('SWNOHIT', 'integer outcome', 'transmit "READY^M"\nwaitfor "absent" 1\noutcome = waitfor')
    add('SWPREFIX', 'integer outcome', 'transmit "READY^M"\nwaitfor "ABAAB" 1\noutcome = waitfor')
    add('SWOVER', 'integer outcome', 'transmit "READY^M"\nwaitfor "ABC" 2\noutcome = waitfor')
    add('SWHIGH', 'integer outcome', 'transmit "READY^M"\nwaitfor "é" 1\noutcome = waitfor')
    add('SWSTRICT', 'integer outcome', 'transmit "READY^M"\nwaitfor "login:" 1\noutcome = waitfor')
    add('SWMID', 'integer outcome', 'waitfor "missing" 1\noutcome = waitfor')
    add('SWLOCAL', 'integer outcome', 'string needle = "READY"\ntransmit "READY^M"\nwaitfor needle 2\noutcome = waitfor')
    add('SWPARM', 'integer outcome', 'call worker with "READY"', helper='proc worker\nstrparm needle\ntransmit "READY^M"\nwaitfor needle 2\noutcome = waitfor\nendproc\n')
    add('SWDEF', 'integer outcome', 'transmit "READY^M"\nwaitfor "READY"\noutcome = waitfor')
    add('SWEMP1', 'integer outcome', 'waitfor "" 1\noutcome = waitfor')
    add('SWEMPDEF', 'integer outcome', 'waitfor ""\noutcome = waitfor')
    add('SWEMPF', 'integer outcome', 'waitfor "" FOREVER\noutcome = waitfor')
    add('SWFOREM', 'integer outcome', 'transmit "READY^M"\nwaitfor "READY" FOREVER\noutcome = waitfor')
    add('SWFOREV', '', 'waitfor "missing" FOREVER')
    add('SWSTAT', 'integer outcome', 'waitfor "" 0\noutcome = waitfor')
    add('SWBAD', '', 'waitfor "READY" -1')
    add('SWLONG', '', 'waitfor "READY" 32767')
    add('SWMISS', '', 'waitfor')
    add('SWFLOAT', '', 'waitfor "READY" 1.0')
    add('SWEXTRA', '', 'waitfor "READY" 1 2')
    add('SXMISS', '', 'transmit')
    add('SXNUM', '', 'transmit 1')
    tx = {
        'SXTX': b'AT\r', 'SXEMPTY': b'', 'SXCTL': b'A\rB\nC\x01D',
        'SXHIGH': bytes.fromhex('8280'), 'SXCARA': bytes.fromhex('001e'),
        'SXPAUSE': b'AB', 'SXLOCAL': b'LOCAL\r', 'SXGLOBAL': b'GLOBAL\r',
        'SXPARM': b'PARAM\r', 'SXMAX': b'A' * 80, 'SXTWICE': b'ONE\rTWO\r',
    }
    for name, data in tx.items():
        cases[name]['expected'] = {'tx_hex': data.hex(), 'stdout_hex': ''}
        cases[name]['serial'] = dict(enabled=True, input_hex='', send_after_tx_hex='',
                                     case_sensitive=False, dos_peer=True)
    cases['SXGLOBAL']['expected']['string0'] = 'GLOBAL^M'
    receive = {
        'SWHIT': (b'noise LoGiN:TRAIL', 1),
        'SWCASE': (b'LOGIN:', 1), 'SWEMP1': (b'', 1),
        'SWEMPDEF': (b'', 1), 'SWEMPF': (b'', 1), 'SWFOREM': (b'READY', 1),
        'SWNOHIT': (b'noise', 0), 'SWPREFIX': (b'ABABAAB', 0),
        'SWOVER': (b'AABC', 1), 'SWHIGH': (bytes.fromhex('90'), 0),
        'SWSTRICT': (b'LOGIN:', 0), 'SWMID': (b'', 0),
        'SWLOCAL': (b'ready', 1), 'SWPARM': (b'ready', 1),
        'SWDEF': (b'READY', 1),
    }
    for name, (data, status) in receive.items():
        case = cases[name]
        case['source'] = case['source'].replace('outcome = waitfor\r\n',
            'outcome = waitfor\r\nif outcome\r\nmessage "MATCH"\r\nelse\r\nmessage "TIMEOUT"\r\nendif\r\n')
        marker = b'READY\r' if 'transmit' in case['source'] else b''
        case['serial'] = dict(enabled=True, input_hex=data.hex(), send_after_tx_hex=marker.hex(),
                              case_sensitive=name == 'SWSTRICT',
                              dos_peer=name not in ('SWSTRICT', 'SWMID'))
        case['expected'] = dict(tx_hex=marker.hex(), integer0=status,
                                stdout_hex=(b'MATCH\r\n' if status else b'TIMEOUT\r\n').hex())
    cases['SWMID']['serial'].update(initial_ticks=0x1800b0 - 8, tick_step=1)
    for name in ('SWEMPTY', 'SWSTAT'):
        cases[name]['source'] = cases[name]['source'].replace('outcome = waitfor\r\n',
            'outcome = waitfor\r\nif outcome\r\nmessage "MATCH"\r\nelse\r\nmessage "TIMEOUT"\r\nendif\r\n')
    for name in ('SWBAD', 'SWEMPTY', 'SWSTAT', 'SWZERO'):
        cases[name]['serial'] = dict(enabled=True, input_hex='', send_after_tx_hex='', case_sensitive=False, dos_peer=True)
        cases[name]['expected'] = dict(tx_hex='', stdout_hex='', error='operand', native_error=1)
    for name, reason in {
        'SWFOREV': 'The actual FOREVER enum1A is indefinite with a nonempty needle and no queued input.',
        'SWLONG': 'Avoid a32767-second timeout in execution; compiler grammar evidence only.',
    }.items():
        cases[name]['compiler_only_reason'] = reason
        cases[name]['expected'] = {}
    return cases


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    assert out.parent == ROOT / 'analysis/aspect-serial' and out.name.startswith('compiler-')
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
