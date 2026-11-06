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
    parser.add_argument('--program-result-probe',action='store_true',help='Explicitly admit only the marked PROGRAM-result diagnostic interpreter')
    parser.add_argument('--inner-screen',action='store_true',help='Passive pre/post inner screen witness; requires graphics child and386/UMB observer')
    parser.add_argument('--lease-fault-phase',type=int,choices=[0,5,6,8,10,17,22],default=0,help='Explicitly admit the matching one-shot FAULT.ASX divide diagnostic')
    parser.add_argument('--lease-fault-foreign-ds',action='store_true',help='Require the marked diagnostic that faults with DS=B800h and the owned SS')
    args = parser.parse_args()
    assert not args.nested_graphics or args.nested_program
    assert not args.exit_watch_high or args.exit_watch
    assert not args.inner_screen or (args.nested_graphics and args.cpu=='386' and not args.exit_watch)
    if args.lease_fault_phase:assert args.nested_graphics and args.program_result_probe and args.exit_watch and args.exit_watch_high and args.cpu=='386'
    if args.lease_fault_foreign_ds:assert args.lease_fault_phase
    binary, runner, out = args.terminal.resolve(), args.runner.resolve(), args.output.resolve()
    assert out.is_relative_to(ROOT / 'build') and not out.exists()
    sources = {}
    for program in [binary, runner]:
        m = json.loads(program.with_name('manifest.json').read_text())
        assert sha(program) == m['binary_sha256']
        assert not m.get('diagnostic_build') or (program==runner and args.program_result_probe and m.get('diagnostic_program_result_probe'))
        if program==runner:assert m.get('diagnostic_lease_fault_phase',0)==args.lease_fault_phase
        if program==runner:assert bool(m.get('diagnostic_lease_fault_foreign_ds'))==args.lease_fault_foreign_ds
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
        if args.inner_screen:
            child_source=child_source.replace(' mov ax,0x4c00', ''' mov ah,0x0f
 int 0x10
 mov [mode],al
 mov dx,mode_name
 mov ax,0x3d02
 int 0x21
 jnc mode_opened
 cmp ax,2
 jne failed
 xor cx,cx
 mov ah,0x3c
 int 0x21
 jc failed
mode_opened:
 mov bx,ax
 xor cx,cx
 xor dx,dx
 mov ax,0x4202
 int 0x21
 jc failed
 mov dx,mode
 mov cx,1
 mov ah,0x40
 int 0x21
 jc failed
 cmp ax,1
 jne failed
 mov ah,0x3e
 int 0x21
 jc failed
 mov ax,0x4c00''',1)
            child_source+="\nmode: db 0\nmode_name: db 'D:\\CHMODE.BIN',0\n"
        child.write_text(child_source)
        subprocess.run(['nasm','-fbin',str(child),'-o',str(out/'NEST.COM')],check=True)
        files['NEST.COM']=(out/'NEST.COM').read_bytes()
        option='' if args.nested_graphics else ' NOCLEAR'
        first=first.replace('proc main\n','proc main\nrun "D:\\NEST.COM"'+option+'\n',1)
        if args.inner_screen:
            before='fopen 0 "D:\\FPRE.TXT" "wb"\nif failure\nexit\nendif\nfclose 0\n'
            after=before.replace('FPRE.TXT','FPST.TXT')
            first=first.replace('run "D:\\NEST.COM"\n',before+'run "D:\\NEST.COM"\n'+after,1)
    keys = bytearray(actions(b'D:\\FIRST.ASX', 0))
    for i, (name, text) in enumerate([('FIRST', first), ('SIX', six), ('MISSING', missing)]):
        path = ('D:\\' + name + '.ASX').encode()
        keys[i * 54:(i + 1) * 54] = struct.pack('<H', 0) + path.ljust(52, b'\0')
        (out / (name + '.ASP')).write_text(text)
        files[name + '.ASX'] = compile_source(text)
    if args.lease_fault_phase:
        files['FAULT.ASX']=files['FIRST.ASX']
        keys[:54]=struct.pack('<H',0)+b'D:\\FAULT.ASX'.ljust(52,b'\0')
        keys[3*54:4*54]=struct.pack('<H',0)+b'D:\\FIRST.ASX'.ljust(52,b'\0')
    files['ACTIONS.KEY'] = bytes(keys)
    if args.exit_watch:
        import aspect_exit_watch
        sources.update(aspect_exit_watch.build(binary,runner,out/'EWATCH.COM'))
        files['EWATCH.COM']=(out/'EWATCH.COM').read_bytes()
    if args.inner_screen:
        import snapshot_screen_watch
        sources.update(snapshot_screen_watch.build(binary,runner,out/'SSWATCH.COM',5))
        files['SSWATCH.COM']=(out/'SSWATCH.COM').read_bytes()
    settings = bytearray(prm(port=3, baud=5))
    for offset, value in [(0x188,5),(0x4e4,8),(0x4e6,4),(0x1c2,0),(0x1c8,2),
                          (0x1ca,25),(0x4ec,0),(0x1bc,0),(0x1be,0),(0x1e6,0)]:
        struct.pack_into('<H', settings, offset, value)
    harness.BINARY = stage / 'TERMINAL.EXE'
    label = out.name
    schedule='p900 enter p3500 a-1 p1300 a-2 p1300 a-3 p1300 a-1 p1300 r e a d y enter p700 a-x'
    if args.lease_fault_phase:schedule=schedule.replace('a-3 p1300 a-1','a-3 p1300 a-4')
    result = harness.run(label, 'success',
        schedule,
        prm=bytes(settings), arguments='@TEST.PRM /T:D:\\ACTIONS.KEY /D:CaseTest:23',
        com=3, irq=5, cpu=args.cpu, working_drive='d', timeout=30, files=files,
        observer='SSWATCH' if args.inner_screen else 'EWATCH' if args.exit_watch else None,
        observer_high=args.exit_watch_high or args.inner_screen)
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
        characters=bytearray(b'FIRST BYTE SAFE'.ljust(1920,b' '))
        if args.lease_fault_phase:
            notice=b'FIRST BYTE SAFEASPECT: CPU arithmetic fault (error 12, opcode 9B, step 2)'
            characters[:len(notice)]=notice
            notice=b'ASPECT returned an error.';characters[160:160+len(notice)]=notice
        expected=b''.join(bytes([c,7]) for c in characters)
        checks['exact_1920_viewport_cells']=(drive/'SCREEN.BIN').read_bytes()[:3840]==expected
    if args.lease_fault_phase:
        checks.pop('four_calls');checks.pop('two_nested_children')
        checks['one_failed_and_one_recovered_FIRST']=wire.count(b'FIRSTOK\r')==1
        child_count=2 if args.lease_fault_phase in (10,22) else 1
        checks['child_count_matches_fault_boundary']=(drive/'NEST.LOG').read_bytes()==b'CHILD|'*child_count
    report = dict(passed=all(checks.values()), checks=checks, binary_sha256=sha(binary),
                  program_result_probe=args.program_result_probe,
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
        if args.lease_fault_phase:
            exits=report['exit_watch']['exits'];probes=report['exit_watch']['program_results']
            checks['actual_selected_divide']=len(exits)==4 and exits[0]['error']==12 and exits[0]['opcode']==155 and probes[0]['stage']==256+args.lease_fault_phase
            checks['parent_lease_live_before_divide']=probes[0]['status']==1
            fault_ds=probes[0]['display_status'];fault_ss=probes[0]['serial_status']
            checks['selected_fault_DS_SS']=fault_ds==0xb800 and fault_ss!=fault_ds if args.lease_fault_foreign_ds else fault_ds==fault_ss and fault_ds!=0
            checks['later_calls_succeed']=len(exits)==4 and all(e['error']==0 for e in exits[1:]) and probes[3]['stage']==2 and probes[3]['status']==0
            checks['all_owners_retired']=all(e[k]==0 for e in exits for k in ['cleanup_error','external_scope','display_owned','program_busy','process_busy'])
            report['lease_fault_phase']=args.lease_fault_phase
            report['fault_witness']=dict(parent_lease_live=probes[0]['status']==1,ds=fault_ds,ss=fault_ss,foreign_ds=args.lease_fault_foreign_ds)
            report['passed']=all(checks.values())
            report['scope']+=' One real own-stack DIV in FAULT.ASX, then six streams/missing-file recovery and normal nested FIRST.ASX in the same terminal. No injected cleanup success.'
    if args.inner_screen:
        report['inner_screen']=snapshot_screen_watch.verify(drive/'SSCREEN.BIN')
        checks['child_observed_graphics_mode']=(drive/'CHMODE.BIN').read_bytes()==b'\x13\x13'
        checks['marker_files_created']=all((drive/n).exists() and (drive/n).stat().st_size==0 for n in ['FPRE.TXT','FPST.TXT'])
        report['passed']=all(checks.values())
        report['scope']+=' Separate386/XMS/UMB passive full inner screen/cursor witness and child-reported BIOS graphics mode; no physical timing claim.'
    (out / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
    print({k:v for k,v in checks.items() if not v})
    assert report['passed']


if __name__ == '__main__':
    main()
