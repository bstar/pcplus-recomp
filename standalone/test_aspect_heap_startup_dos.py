#!/usr/bin/env python3
"""Exercise repeated parent ASPECT calls, all six streams and missing-file recovery."""
import argparse
import json
import shutil
import struct
import subprocess
import sys
from pathlib import Path
import test_connection_dos as harness
from directory_fixtures import prm
from test_directory_key_bindings_dos import actions
from build_path_session import ROOT, sha
sys.path.insert(0, str(ROOT / 'src/aspect'))
from compiler import compile_source


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['terminal', 'runner', 'output']:
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--nested-program',action='store_true',help='Run an actual DOS child twice around the six-stream and missing-file cases')
    parser.add_argument('--nested-graphics',action='store_true',help='Use default SAVE and let each child leave BIOS mode13h active')
    parser.add_argument('--exit-watch',action='store_true',help='Install a small passive diagnostic TSR; separate memory footprint from ordinary acceptance')
    parser.add_argument('--exit-watch-high',action='store_true',help='Require the passive observer to reside in UMB')
    parser.add_argument('--cpu',choices=['8086','386'],default='8086')
    args = parser.parse_args()
    assert not args.nested_graphics or args.nested_program
    assert not args.exit_watch_high or args.exit_watch
    binary, runner, out = args.terminal.resolve(), args.runner.resolve(), args.output.resolve()
    assert out.is_relative_to(ROOT / 'build') and not out.exists()
    sources = {}
    for program in [binary, runner]:
        m = json.loads(program.with_name('manifest.json').read_text())
        assert sha(program) == m['binary_sha256'] and not m.get('diagnostic_build')
        for name, expected in m['sources'].items():
            assert sha(ROOT / name) == expected, name
            sources[name] = expected
    for name in ['standalone/test_aspect_heap_startup_dos.py', 'standalone/test_connection_dos.py',
                 'standalone/test_directory_key_bindings_dos.py', 'src/aspect/compiler.py']:
        sources[name] = sha(ROOT / name)
    out.mkdir()
    stage = out / 'program'
    stage.mkdir()
    for program in [binary, runner]:
        shutil.copyfile(program, stage / program.name)
    first = 'proc main\nfopen 0 "D:\\FIRST.LOG" "wb"\nif failure\nexit\nendif\nfputs 0 "FIRST|"\nfclose 0\ntransmit "FIRSTOK^M"\nendproc\n'
    six = 'proc main\n'
    for i in range(6):
        six += f'fopen {i} "D:\\SLOT{i}.TXT" "wb"\nif failure\nexit\nendif\n'
    for i in range(6):
        six += f'fputs {i} "SLOT{i}|"\nfclose {i}\n'
    six += 'transmit "SIXOK^M"\nendproc\n'
    missing = 'proc main\nfopen 0 "D:\\ABSENT.TXT" "rb"\nif failure\ntransmit "MISSINGOK^M"\nelse\nexit\nendif\nfopen 0 "D:\\RECOVER.TXT" "wb"\nif failure\nexit\nendif\nfputs 0 "RECOVERED|"\nfclose 0\ntransmit "RECOVEROK^M"\nendproc\n'
    files = {}
    if args.nested_program:
        child = out / 'NEST.ASM'
        child_source='''BITS 16
CPU 8086
ORG 0x100
 mov dx,name
 mov ax,0x3d02
 int 0x21
 jnc opened
 cmp ax,2
 jne failed
 xor cx,cx
 mov ah,0x3c
 int 0x21
 jc failed
opened:
 mov bx,ax
 xor cx,cx
 xor dx,dx
 mov ax,0x4202
 int 0x21
 jc failed
 mov dx,message
 mov cx,6
 mov ah,0x40
 int 0x21
 jc failed
 cmp ax,6
 jne failed
 mov ah,0x3e
 int 0x21
 jc failed
 mov ax,0x4c00
 int 0x21
failed:
 mov ax,0x4c07
 int 0x21
name: db 'D:\\NEST.LOG',0
message: db 'CHILD|'
'''
        if args.nested_graphics:
            child_source=child_source.replace(' mov ax,0x4c00',' mov ax,0x0013\n int 0x10\n mov ax,0x4c00',1)
        child.write_text(child_source)
        subprocess.run(['nasm','-fbin',str(child),'-o',str(out/'NEST.COM')],check=True)
        files['NEST.COM']=(out/'NEST.COM').read_bytes()
        option='' if args.nested_graphics else ' NOCLEAR'
        first=first.replace('proc main\n','proc main\nrun "D:\\NEST.COM"'+option+'\n',1)
    keys = bytearray(actions(b'D:\\FIRST.ASX', 0))
    for i, (name, text) in enumerate([('FIRST', first), ('SIX', six), ('MISSING', missing)]):
        path = ('D:\\' + name + '.ASX').encode()
        keys[i * 54:(i + 1) * 54] = struct.pack('<H', 0) + path.ljust(52, b'\0')
        (out / (name + '.ASP')).write_text(text)
        files[name + '.ASX'] = compile_source(text)
    files['ACTIONS.KEY'] = bytes(keys)
    if args.exit_watch:
        import aspect_exit_watch
        sources.update(aspect_exit_watch.build(binary,runner,out/'EWATCH.COM'))
        files['EWATCH.COM']=(out/'EWATCH.COM').read_bytes()
    settings = bytearray(prm(port=3, baud=5))
    for offset, value in [(0x188,5),(0x4e4,8),(0x4e6,4),(0x1c2,0),(0x1c8,2),
                          (0x1ca,25),(0x4ec,0),(0x1bc,0),(0x1be,0),(0x1e6,0)]:
        struct.pack_into('<H', settings, offset, value)
    harness.BINARY = stage / 'TERMINAL.EXE'
    label = out.name
    result = harness.run(label, 'success',
        'p900 enter p3500 a-1 p1300 a-2 p1300 a-3 p1300 a-1 p1300 r e a d y enter p700 a-x',
        prm=bytes(settings), arguments='@TEST.PRM /T:D:\\ACTIONS.KEY /D:CaseTest:23',
        com=3, irq=5, cpu=args.cpu, working_drive='d', timeout=30, files=files,
        observer='EWATCH' if args.exit_watch else None,observer_high=args.exit_watch_high)
    drive = ROOT / 'build/connection-dos' / label
    wire = (drive / 'serial.bin').read_bytes()
    checks = dict(result['checks'], four_calls=wire.count(b'FIRSTOK\r') == 2,
                  all_six_streams=b'SIXOK\r' in wire,
                  missing_and_recovered=b'MISSINGOK\rRECOVEROK\r' in wire,
                  keyboard_after_scripts=wire.endswith(b'ready\r+++ATH\r'),
                  first_file=(drive / 'FIRST.LOG').exists() and (drive / 'FIRST.LOG').read_bytes() == b'FIRST|',
                  recovery_file=(drive / 'RECOVER.TXT').exists() and (drive / 'RECOVER.TXT').read_bytes() == b'RECOVERED|',
                  six_files=all((drive / f'SLOT{i}.TXT').exists() and (drive / f'SLOT{i}.TXT').read_bytes() == f'SLOT{i}|'.encode() for i in range(6)))
    for name, expected in sources.items():
        assert sha(ROOT / name) == expected, name
    if args.nested_program:
        checks['two_nested_children']=(drive/'NEST.LOG').exists() and (drive/'NEST.LOG').read_bytes()==b'CHILD|CHILD|'
    report = dict(passed=all(checks.values()), checks=checks, binary_sha256=sha(binary),
                  cpu=args.cpu,
                  interpreter_sha256=sha(runner), sources=sources, original_inputs=[],
                  scope=__doc__ + ' Actual DOS '+args.cpu+' COM3/IRQ5,synthetic modem and compiled owned scripts. No nested external PROGRAM or physical acceptance.')
    if args.nested_program:
        report['nested_child_source_sha256']=sha(out/'NEST.ASM')
        report['nested_child_sha256']=sha(out/'NEST.COM')
        report['nested_graphics']=args.nested_graphics
        report['scope']=__doc__+' Actual DOS '+args.cpu+' COM3/IRQ5; two '+('SAVE graphics' if args.nested_graphics else 'NOCLEAR text')+' DOS children surrounding six-stream and missing-file recovery. Synthetic modem; no physical or complete PROGRAM-option acceptance.'
    if args.exit_watch:
        report['exit_watch']=aspect_exit_watch.read(drive/'EXITSTAT.BIN')
        report['observer_sha256']=sha(out/'EWATCH.COM')
        report['exit_watch_high']=args.exit_watch_high
        assert not args.exit_watch_high or report['exit_watch']['resident_segment']>=0xa000
        report['scope']+=' Passive exit observer adds resident memory; diagnostic run, not an unobserved capacity proof.'
    (out / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
    print({k:v for k,v in checks.items() if not v})
    assert report['passed']


if __name__ == '__main__':
    main()
