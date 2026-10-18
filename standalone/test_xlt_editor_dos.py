#!/usr/bin/env python3
"""Production XLT owner, injected DOS errors and BIOS-key UI on owned media."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/xlt-editor'
SOURCE = ROOT / 'src/translation'
BASE = ['wcl', '-q', '-bt=dos', '-0', '-ms', '-s', '-w4', '-we',
        '-k8192', '-i=' + str(SOURCE)]
COMMON = [SOURCE / n for n in ['editor_document.c', 'editor_fs.c',
                              'xlt_dos.c', 'xlt_dos_fs.c']]
IDENTITY = bytes(range(256))


def build():
    subprocess.run(BASE + ['-fe=OWNER.EXE', *map(str, COMMON),
                          str(ROOT / 'standalone/xlt_editor_owner_host.c')], cwd=OUT, check=True)
    subprocess.run(BASE + ['-fe=FAULT.EXE', str(SOURCE / 'editor_document.c'),
                          str(SOURCE / 'xlt_dos.c'),
                          str(ROOT / 'standalone/xlt_editor_fault_host.c')], cwd=OUT, check=True)
    subprocess.run(['wcc', '-q', '-bt=dos', '-0', '-ms', '-s', '-w4', '-we',
                    '-dmain=xlt_application_main', '-fo=editor_ui.obj',
                    str(SOURCE / 'editor_main.c')], cwd=OUT, check=True)
    subprocess.run(BASE + ['-fe=UI.EXE', 'editor_ui.obj', *map(str, COMMON),
                          str(ROOT / 'standalone/xlt_editor_ui_host.c')], cwd=OUT, check=True)


def run(name, program, keys='', fixtures=None, prelude='', expected_exit=0):
    directory = OUT / 'tests' / name
    if directory.exists():
        shutil.rmtree(directory)
    directory.mkdir(parents=True)
    for exe in ['XLTEDIT.EXE', 'UI.EXE', 'OWNER.EXE', 'FAULT.EXE']:
        shutil.copyfile(OUT / exe, directory / exe)
    for filename, data in (fixtures or {}).items():
        (directory / filename).write_bytes(data)
    schedule = 'ADDKEY p750 ' + ' p100 '.join(keys.split()) if keys else ''
    # Require an exact exit status, including the invalid-file entry paths.
    conf = f'''[sdl]
output=surface
[cpu]
core=normal
cputype=386
cycles=fixed 6000
[mixer]
nosound=true
[serial]
serial1=disabled
serial2=disabled
serial3=disabled
serial4=disabled
[autoexec]
@echo off
mount c "{directory}"
c:
{prelude}
{schedule}
{program} >LOG.TXT
if errorlevel {expected_exit + 1} goto fail
if not errorlevel {expected_exit} goto fail
echo PASS>PASS.TXT
goto done
:fail
echo FAIL>FAIL.TXT
:done
exit
'''
    (directory / 'dosbox.conf').write_text(conf)
    with (directory / 'dosbox.log').open('w') as log:
        proc = subprocess.run(['dosbox-x', '-fastlaunch', '-nogui', '-conf',
                               str(directory / 'dosbox.conf')], cwd=directory,
                              env=dict(os.environ, SDL_VIDEODRIVER='dummy',
                                       SDL_AUDIODRIVER='dummy'), stdout=log,
                              stderr=log, timeout=30)
    assert proc.returncode == 0 and (directory / 'PASS.TXT').exists(), (
        name, (directory / 'LOG.TXT').read_bytes())
    return directory


def main():
    build()
    cases = []
    for name in ['owner', 'fault']:
        d = run(name, name.upper())
        log = (d / 'LOG.TXT').read_text().strip()
        assert 'XLT ' + name.upper() + ' PASS' in log, log
        cases.append(dict(case=name, passed=True, log=log))
        print(name, log, flush=True)
    changed = bytearray(IDENTITY)
    changed[0] = 255
    changed[255] = 0
    recipes = [
        ('cancel', 'UI TABLE.XLT', 'enter home del 2 5 5 enter escape y', IDENTITY),
        ('save-both-pages', 'UI TABLE.XLT',
         'enter home del 2 5 5 enter f2 end enter home del del del 0 enter f1 escape', bytes(changed)),
        ('jump-byte26', 'UI TABLE.XLT',
         'g home del 2 6 enter enter home del del 2 5 5 enter f1 escape', IDENTITY[:26] + b'\xff' + IDENTITY[27:]),
        ('invalid-number-cancel', 'UI TABLE.XLT',
         'enter home del 2 5 6 enter escape escape', IDENTITY),
        ('identity-discard', 'UI TABLE.XLT', 'f4 escape y', bytes(reversed(IDENTITY))),
        ('identity-save', 'UI TABLE.XLT', 'f4 f1 escape', IDENTITY),
        ('reload-discard', 'UI TABLE.XLT',
         'enter home del 9 enter f3 y escape', IDENTITY),
        ('reload-refuse', 'UI TABLE.XLT',
         'enter home del 9 enter f3 n f1 escape', b'\x09' + IDENTITY[1:]),
        ('production', 'XLTEDIT TABLE.XLT',
         'enter home del 2 5 5 enter f1 escape', b'\xff' + IDENTITY[1:]),
        ('mono', 'UI TABLE.XLT 7', 'escape', IDENTITY),
        ('active-page-one', 'UI TABLE.XLT 3 1', 'escape', IDENTITY),
    ]
    for name, program, keys, expected in recipes:
        initial = bytes(reversed(IDENTITY)) if name.startswith('identity-') else IDENTITY
        d = run(name, program, keys, {'TABLE.XLT': initial})
        assert (d / 'TABLE.XLT').read_bytes() == expected, name
        if program.startswith('UI '):
            assert b'XLT UI RESTORED' in (d / 'LOG.TXT').read_bytes(), name
        assert not (d / 'XLTEDIT.BAK').exists() and not (d / 'XLTEDIT.$$$').exists(), name
        cases.append(dict(case=name, passed=True, exact_file=True,
                          screen_restored=program.startswith('UI ')))
        print(name, 'passed', flush=True)
    for name, keys, exists in [
            ('new-cancel', 'escape y', False),
            ('new-save', 'f1 escape', True)]:
        d = run(name, 'XLTEDIT /N NEW.XLT', keys)
        assert (d / 'NEW.XLT').exists() == exists, name
        if exists:
            assert (d / 'NEW.XLT').read_bytes() == IDENTITY
        cases.append(dict(case=name, passed=True, exact_file=True))
    for name, fixtures, prelude, status, keys in [
            ('readonly', {'TABLE.XLT': IDENTITY}, 'attrib +r TABLE.XLT', 0,
             'enter home del 9 enter f1 escape y'),
            ('collision', {'TABLE.XLT': IDENTITY, 'XLTEDIT.BAK': b'keep'}, '', 0,
             'enter home del 9 enter f1 escape y'),
            ('short', {'TABLE.XLT': IDENTITY[:-1]}, '', 2, ''),
            ('long', {'TABLE.XLT': IDENTITY + b'\0'}, '', 2, '')]:
        d = run(name, 'XLTEDIT TABLE.XLT', keys, fixtures, prelude, status)
        for filename, contents in fixtures.items():
            assert (d / filename).read_bytes() == contents, (name, filename)
        cases.append(dict(case=name, passed=True, exact_file=True))
    binaries = {name: hashlib.sha256((OUT / name).read_bytes()).hexdigest()
                for name in ['XLTEDIT.EXE', 'OWNER.EXE', 'FAULT.EXE', 'UI.EXE']}
    inputs = list(SOURCE.glob('editor*.[ch]')) + [SOURCE / n for n in
              ['xlt_dos.c', 'xlt_dos.h', 'xlt_dos_fs.c', 'xlt_dos_fs.h']]
    inputs += list((ROOT / 'standalone').glob('xlt_editor_*_host.c'))
    inputs += [Path(__file__).resolve(), ROOT / 'standalone/build_xlt_editor.py']
    result = dict(passed=True, cases=cases, binaries=binaries,
                  sources={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in inputs},
                  scope='Actual DOSBox-X production filesystem and BIOS-key UI tests plus production document/loader linked to injected DOS failures. Synthetic owned media only. No original application, live UART, physical modem or power-loss claim.')
    (OUT / 'checks.json').write_text(json.dumps(result, indent=2) + '\n')
    print('XLT editor DOS checks passed:', len(cases))


if __name__ == '__main__':
    main()
