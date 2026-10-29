#!/usr/bin/env python3
"""Run packaged START/SETUP launchers on a synthetic card in actual DOS8086."""
import argparse
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys

from package_special_edition import ROOT, PRODUCTS, sha
from check_setup_model import image
from test_directory_key_bindings_dos import actions
from test_terminal import SAMPLER

sys.path.insert(0, str(ROOT / 'src/aspect'))
from compiler import compile_source


def run(package, out, setup=False, splash_only=False,irq=None,com=2,after_child_view=False):
    manifest = json.loads((package / 'manifest.json').read_text())
    assert manifest['card_written'] is False
    for name, digest in manifest['sources'].items():
        assert sha(ROOT / name) == digest, name
    for leaf, digest in manifest['files'].items():
        assert sha(package / 'PCPLUSSE' / leaf) == digest, leaf
    out.mkdir(parents=True, exist_ok=False)
    drive = out / 'drive'
    drive.mkdir()
    app = drive / 'PCPLUSSE'
    shutil.copytree(package / 'PCPLUSSE', app)
    raw = bytearray(image())
    assert com in (1,2,3,4)
    base=(0x3f8,0x2f8,0x3e8,0x2e8)[com-1]
    struct.pack_into('<H', raw, 0, com-1)
    struct.pack_into('<H', raw, 0x174+2*(com-1), base)
    struct.pack_into('<HH', raw, 0x4e4, 8, 4)
    if irq is not None:
        assert irq in (3,4,5,7)and manifest.get('experimental_custom_irq')
        struct.pack_into('<H',raw,0x184+2*(com-1),irq)
    fixtures = {'PCPLUS.PRM': bytes(raw), 'PCPLUS.XLT': bytes(range(256)),
                'PCPLUS.DIR': b'PRIVATE-DIRECTORY-PRESERVATION-SENTINEL'}
    # No directory selector is requested; a local dialing file is not opened.
    for leaf, data in fixtures.items():
        (app / leaf).write_bytes(data)
    source = ('integer value\nproc main\nvalue=' + '(' * 120 + '37' + ')' * 120 +
              '\nif value==37\nfopen 0 "RESULT.BIN" "wb"\n'
              'fputs 0 "SPECIAL-COMPILED"\nfclose 0\nendif\nendproc\n')
    (app / 'TEST.ASP').write_text(source, encoding='ascii')
    (app / 'ACTIONS.KEY').write_bytes(actions(b'C:\\PCPLUSSE\\TEST.ASP', 0))
    sampler = SAMPLER.replace('D:\\', 'C:\\')
    for offset in (0, 1, 3, 4):
        sampler = sampler.replace(hex(0x3f8 + offset), hex(base + offset))
    (drive / 'sample.asm').write_text(sampler)
    subprocess.run(['nasm', '-fbin', str(drive / 'sample.asm'), '-o', str(drive / 'SNAP.COM')], check=True)
    subprocess.run(['nasm', '-fbin', str(ROOT / 'standalone/special_watch.asm'),
                    '-o', str(drive / 'WATCH.COM')], check=True)
    strategy = manifest.get('experimental_directory_resource_owner',False)
    if strategy:
        subprocess.run(['nasm','-fbin',str(ROOT/'standalone/dos_strategy_sample.asm'),'-o',str(drive/'STRAT.COM')],check=True)
    if after_child_view:
        assert strategy and not setup and not splash_only
        (drive/'rview.asm').write_text((ROOT/'standalone/redisplay_watch.asm').read_text().replace('D:\\','C:\\'))
        subprocess.run(['nasm','-fbin',str(drive/'rview.asm'),'-o',str(drive/'RVIEW.COM')],check=True)
    launcher = 'SETUP' if setup else 'START'
    observe = setup or splash_only
    keys = ('p900 escape p1100 enter p1500 a-z p700 escape p600 a-x' if setup else
            'p900 enter p1500 a-z p700 escape p600 a-x' if splash_only else
            'p900 enter p1500 a-1 p6500 space p700 a-x')
    if after_child_view:keys=keys.replace('a-x','c-pgup p1200 escape p500 a-x')
    config = ('[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\n'
              'cycles=fixed 12000\n[serial]\n'+
              ''.join('serial'+str(n)+'=dummy'+(' irq:'+str(irq)if n==com and irq is not None else '')+'\n'
                      for n in range(1,5))+
              '[mixer]\nnosound=true\n[autoexec]\n@echo off\n'
              'mount c "' + str(drive) + '"\nc:\nset PCPLUS=C:\\ORIGINAL\n' +
              ('WATCH T\n' if observe else '')+('RVIEW T\n' if after_child_view else '')+('STRAT B\n' if strategy else '')+'SNAP B\nADDKEY ' + keys + '\n'
              'CALL C:\\PCPLUSSE\\' + launcher + '.BAT /T:ACTIONS.KEY\n'+
              ('C:\\STRAT A\n' if strategy else '')+'SET >C:\\ENV.TXT\nC:\\SNAP S\nC:\\SNAP A\n'+('C:\\RVIEW\n' if after_child_view else '')+('C:\\WATCH\n' if observe else '')+
              'if errorlevel 1 goto failed\necho RETURNED>C:\\RETURN.TXT\nexit\n'
              ':failed\necho FAIL>C:\\FAIL.TXT\nexit\n')
    (out / 'dosbox.conf').write_text(config)
    with (out / 'dosbox.log').open('w') as log:
        proc = subprocess.run(['dosbox-x', '-fastlaunch', '-nogui', '-conf', str(out / 'dosbox.conf')],
                              cwd=drive, stdout=log, stderr=log, timeout=30,
                              env=dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy'))
    assert proc.returncode == 0 and (drive / 'RETURN.TXT').exists() and not (drive / 'FAIL.TXT').exists()
    if observe:
        video = (drive / 'SPLASH.BIN').read_bytes()
        assert len(video) == 8000
        at = (9 * 80 + 27) * 2
        assert video[at:at + 38:2] == b'LoC SPECIAL EDITION'
        assert video[at + 1:at + 38:2] == b'\x5f' * 19
    assert (drive / 'BEFORE.BIN').read_bytes() == (drive / 'AFTER.BIN').read_bytes()
    if strategy:
        assert len((drive/'STRATB.BIN').read_bytes())==2 and (drive/'STRATB.BIN').read_bytes()==(drive/'STRATA.BIN').read_bytes()
    if after_child_view:
        captured=(drive/'RVIEW.BIN').read_bytes();assert len(captured)==10246
        magic,count,ticks=struct.unpack_from('<3H',captured)
        assert magic==0x4452 and 1<=count<=32 and ticks>5
    env = (drive / 'ENV.TXT').read_bytes().upper().splitlines()
    assert b'PCPLUS=C:\\ORIGINAL' in env and not any(s.startswith(b'LOC_PCPLUS=') for s in env)
    for leaf, data in fixtures.items():
        assert (app / leaf).read_bytes() == data, leaf
    if not observe:
        assert (app / 'RESULT.BIN').read_bytes() == b'SPECIAL-COMPILED'
        assert (app / 'TEST.ASX').read_bytes() == compile_source(source)
    else:
        assert not (app / 'TEST.ASX').exists() and not (app / 'RESULT.BIN').exists()
    for leaf in PRODUCTS:
        assert sha(app / leaf) == manifest['files'][leaf]
    result = dict(passed=True, launcher=launcher, cpu='8086', port=com, io_base=base, resident_observer=observe,
                  irq=irq,
                  package_manifest_sha256=sha(package / 'manifest.json'),
                  package_files=manifest['files'],
                  checks=['launcher returns to DOS', 'PCPLUS environment restored',
                          f'COM{com}/PIC/IRQ vectors restored', 'private PRM/DIR/XLT unchanged',
                          'packaged binaries unchanged'] + (['actual magenta splash captured by independent timer'] if observe else
                          ['nested DOS source compilation produces exact ASX', 'script writes expected result'])+(['DOS allocation strategy restored'] if strategy else [])+(['frozen-history viewer reopens after nested child return'] if after_child_view else []),
                  sources={n: sha(ROOT / n) for n in ['standalone/test_special_package_dos.py',
                           'standalone/special_watch.asm', 'standalone/test_terminal.py',
                           'standalone/check_setup_model.py', 'standalone/test_directory_key_bindings_dos.py',
                           'src/aspect/compiler.py']+(['standalone/dos_strategy_sample.asm'] if strategy else [])+(['standalone/redisplay_watch.asm'] if after_child_view else [])},
                  artifacts={str(p.relative_to(out)): sha(p) for p in out.rglob('*') if p.is_file()},
                  scope=__doc__ + ' Dummy serial ports; no live BBS, card write or physical modem test.')
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print('PASS special package', launcher)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--package', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--setup', action='store_true')
    p.add_argument('--splash-only', action='store_true')
    p.add_argument('--after-child-view',action='store_true',help='Observe redisplay after nested compilation and frozen-memory reacquisition')
    p.add_argument('--irq',type=int,choices=[3,4,5,7])
    p.add_argument('--com',type=int,choices=[1,2,3,4],default=2)
    args = p.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT / 'build') and not out.exists()
    assert not (args.setup and args.splash_only)
    run(args.package.resolve(), out, args.setup, args.splash_only,args.irq,args.com,args.after_child_view)


if __name__ == '__main__':
    main()
