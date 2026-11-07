#!/usr/bin/env python3
"""Exercise repeated parent ASPECT calls, all six streams and missing-file recovery."""
import argparse
import json
import shutil
import struct
import inspect
import re
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
    parser.add_argument('--streams-around-child',action='store_true',help='Also retain six buffered streams across a third real DOS child')
    parser.add_argument('--nested-graphics',action='store_true',help='Use default SAVE and let each child leave BIOS mode13h active')
    parser.add_argument('--nested-wait',choices=['space','escape'],help='Real PROGRAM WAIT continued by this BIOS key; Escape is a continue key, not script cancellation')
    parser.add_argument('--display-rows',type=int,choices=[25,28,43,50],default=25)
    parser.add_argument('--exit-watch',action='store_true',help='Install a small passive diagnostic TSR; separate memory footprint from ordinary acceptance')
    parser.add_argument('--exit-watch-high',action='store_true',help='Require the passive observer to reside in UMB')
    parser.add_argument('--cpu',choices=['8086','386'],default='8086')
    parser.add_argument('--program-result-probe',action='store_true',help='Explicitly admit only the marked PROGRAM-result diagnostic interpreter')
    parser.add_argument('--inner-screen',action='store_true',help='Passive pre/post inner screen witness; requires graphics child and386/UMB observer')
    parser.add_argument('--lease-fault-phase',type=int,choices=[0,5,6,8,10,17,22],default=0,help='Explicitly admit the matching one-shot FAULT.ASX divide diagnostic')
    parser.add_argument('--lease-fault-foreign-ds',action='store_true',help='Require the marked diagnostic that faults with DS=B800h and the owned SS')
    parser.add_argument('--lease-fault-kind',choices=['divide','abort','dispatcher'],default='divide')
    parser.add_argument('--fault-open-streams',action='store_true',help='Keep six buffered streams and exact PROGRAM copies live at the selected fault')
    parser.add_argument('--held-streams',action='store_true',help='Keep six buffered streams across each FIRST child, including PROGRAM WAIT')
    parser.add_argument('--clock-queries',action='store_true',help='Query local DATE/TIME strings across each FIRST child and save a clock trace')
    args = parser.parse_args()
    assert not args.nested_graphics or args.nested_program
    if args.streams_around_child:assert args.nested_program and not args.lease_fault_phase
    if args.nested_wait:assert args.nested_graphics and not args.lease_fault_phase and not args.inner_screen
    assert not args.exit_watch_high or args.exit_watch
    assert not args.inner_screen or (args.nested_graphics and args.cpu=='386' and not args.exit_watch)
    if args.lease_fault_phase:assert args.nested_graphics and args.program_result_probe and args.exit_watch and args.exit_watch_high and args.cpu=='386'
    if args.lease_fault_foreign_ds:assert args.lease_fault_phase
    if args.lease_fault_kind!='divide':assert args.lease_fault_phase and not args.lease_fault_foreign_ds
    if args.fault_open_streams:assert args.lease_fault_phase
    if args.held_streams:assert args.nested_program and not args.lease_fault_phase
    binary, runner, out = args.terminal.resolve(), args.runner.resolve(), args.output.resolve()
    assert out.is_relative_to(ROOT / 'build') and not out.exists()
    sources = {}
    for program in [binary, runner]:
        m = json.loads(program.with_name('manifest.json').read_text())
        assert sha(program) == m['binary_sha256']
        assert not m.get('diagnostic_build') or (program==runner and args.program_result_probe and m.get('diagnostic_program_result_probe'))
        if program==runner:assert m.get('diagnostic_lease_fault_phase',0)==args.lease_fault_phase
        if program==runner:assert bool(m.get('diagnostic_lease_fault_foreign_ds'))==args.lease_fault_foreign_ds
        if program==runner:assert m.get('diagnostic_lease_fault_kind','divide')==args.lease_fault_kind
        if program==runner:assert bool(m.get('diagnostic_script_buffer_owners'))==args.fault_open_streams
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
    if args.streams_around_child:
        for i in range(6):six += f'fputs {i} "SLOT{i}|"\n'
        six+='run "D:\\NEST.COM"'+('' if args.nested_graphics else ' NOCLEAR')+'\n'
        for i in range(6):six+=f'fputs {i} "AFTER{i}|"\n'
        for i in range(6):six+=f'fclose {i}\n'
    else:
        for i in range(6):six+=f'fputs {i} "SLOT{i}|"\nfclose {i}\n'
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
        if args.nested_wait:option+=' WAIT'
        first=first.replace('proc main\n','proc main\nrun "D:\\NEST.COM"'+option+'\n',1)
        if args.fault_open_streams or args.held_streams:
            before=''.join(f'fopen {i} "D:\\HOLD{i}.BIN" "wb"\nfputs {i} "HELD{i}|"\n' for i in range(6))
            after=''.join(f'fclose {i}\n' for i in range(6))
            first=first.replace('proc main\n','proc main\n'+before,1)
            first=first.replace('run "D:\\NEST.COM"'+option+'\n','run "D:\\NEST.COM"'+option+'\n'+after,1)
        if args.inner_screen:
            before='fopen 0 "D:\\FPRE.TXT" "wb"\nif failure\nexit\nendif\nfclose 0\n'
            after=before.replace('FPRE.TXT','FPST.TXT')
            first=first.replace('run "D:\\NEST.COM"\n',before+'run "D:\\NEST.COM"\n'+after,1)
    if args.clock_queries:
        queries='string clock_date,clock12,clock24\ndate clock_date\ntime clock12 0\ntime clock24 1\n'
        first=first.replace('proc main\n','proc main\n'+queries,1)
        trace='fopen 0 "D:\\CLOCK.LOG" "wb"\nfputs 0 clock_date\nfputc 0 32\nfputs 0 clock12\nfputc 0 32\nfputs 0 clock24\nfclose 0\n'
        first=first.replace('transmit "FIRSTOK^M"',trace+'transmit "FIRSTOK^M"',1)
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
        sources.update(aspect_exit_watch.build(binary,runner,out/'EWATCH.COM',wait=bool(args.nested_wait)))
        files['EWATCH.COM']=(out/'EWATCH.COM').read_bytes()
    if args.inner_screen:
        import snapshot_screen_watch
        sources.update(snapshot_screen_watch.build(binary,runner,out/'SSWATCH.COM',5,args.display_rows))
        files['SSWATCH.COM']=(out/'SSWATCH.COM').read_bytes()
    settings = bytearray(prm(port=3, baud=5))
    for offset, value in [(0x188,5),(0x4e4,8),(0x4e6,4),(0x1c2,0),(0x1c8,2),
                          (0x1ca,args.display_rows),(0x4ec,0),(0x1bc,0),(0x1be,0),(0x1e6,0)]:
        struct.pack_into('<H', settings, offset, value)
    harness.BINARY = stage / 'TERMINAL.EXE'
    if args.display_rows!=25:
        harness.SAMPLER=harness.SAMPLER.replace('mov cx,4000','mov cx,8000')
        source=inspect.getsource(harness.run)
        assert source.count('len(screen)==4000')==1
        exec(compile(source.replace('len(screen)==4000','len(screen)==8000'),harness.__file__,'exec'),harness.__dict__)
    label = out.name
    schedule='p900 enter p3500 a-1 p1300 a-2 p1300 a-3 p1300 a-1 p1300 r e a d y enter p700 a-x'
    if args.lease_fault_phase:schedule=schedule.replace('a-3 p1300 a-1','a-3 p1300 a-4')
    if args.nested_wait:
        schedule=schedule.replace('a-1 p1300',f'a-1 p700 {args.nested_wait} p600')
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
                  six_files=all((drive / f'SLOT{i}.TXT').exists() and (drive / f'SLOT{i}.TXT').read_bytes() == (f'SLOT{i}|'+(f'AFTER{i}|' if args.streams_around_child else '')).encode() for i in range(6)))
    if args.clock_queries:
        checks['actual_parent_clock_queries']=(drive/'CLOCK.LOG').exists() and bool(re.fullmatch(rb'\d{2}/\d{2}/\d{2,3} \d{2}:\d{2}:\d{2}[AP]M \d{2}:\d{2}:\d{2}',(drive/'CLOCK.LOG').read_bytes()))
    for name, expected in sources.items():
        assert sha(ROOT / name) == expected, name
    if args.nested_program:
        checks['three_nested_children' if args.streams_around_child else 'two_nested_children']=(drive/'NEST.LOG').exists() and (drive/'NEST.LOG').read_bytes()==b'CHILD|'*(3 if args.streams_around_child else 2)
        viewport_cells=(args.display_rows-1)*80
        characters=bytearray(b'FIRST BYTE SAFE'.ljust(viewport_cells,b' '))
        if args.lease_fault_phase:
            notice=b'FIRST BYTE SAFEASPECT: '+(b'CPU arithmetic fault (error 12' if args.lease_fault_kind=='divide' else b'file or output error (error 5')+b', opcode 9B, step '+(b'14' if args.fault_open_streams else b'2')+b')'
            characters[:len(notice)]=notice
            notice=b'ASPECT returned an error.';characters[160:160+len(notice)]=notice
        expected=b''.join(bytes([c,7]) for c in characters)
        checks['exact_viewport_cells']=(drive/'SCREEN.BIN').read_bytes()[:viewport_cells*2]==expected
    if args.lease_fault_phase:
        checks.pop('four_calls');checks.pop('two_nested_children')
        checks['one_failed_and_one_recovered_FIRST']=wire.count(b'FIRSTOK\r')==1
        child_count=2 if args.lease_fault_phase in (10,22) else 1
        checks['child_count_matches_fault_boundary']=(drive/'NEST.LOG').read_bytes()==b'CHILD|'*child_count
    if args.held_streams:
        checks['held_files_preserved']=all((drive/f'HOLD{i}.BIN').read_bytes()==f'HELD{i}|'.encode() for i in range(6))
    report = dict(passed=all(checks.values()), checks=checks, binary_sha256=sha(binary),
                  program_result_probe=args.program_result_probe,
                  cpu=args.cpu,
                  physical_rows=args.display_rows,
                  streams_around_child=args.streams_around_child,
                  held_streams=args.held_streams,
                  clock_queries=args.clock_queries,
                  interpreter_sha256=sha(runner), sources=sources, original_inputs=[],
                  scope=__doc__ + ' Actual DOS '+args.cpu+' COM3/IRQ5,synthetic modem and compiled owned scripts. No nested external PROGRAM or physical acceptance.')
    if args.nested_program:
        report['nested_child_source_sha256']=sha(out/'NEST.ASM')
        report['nested_child_sha256']=sha(out/'NEST.COM')
        report['nested_graphics']=args.nested_graphics
        report['nested_child_count']=3 if args.streams_around_child else 2
        report['scope']=__doc__+' Actual DOS '+args.cpu+' COM3/IRQ5; '+str(report['nested_child_count'])+' '+('SAVE graphics' if args.nested_graphics else 'NOCLEAR text')+' DOS children with six-stream and missing-file recovery. Synthetic modem; no physical or complete PROGRAM-option acceptance.'
    if args.exit_watch:
        report['exit_watch']=aspect_exit_watch.read(drive/'EXITSTAT.BIN')
        report['observer_sha256']=sha(out/'EWATCH.COM')
        report['exit_watch_high']=args.exit_watch_high
        assert not args.exit_watch_high or report['exit_watch']['resident_segment']>=0xa000
        report['scope']+=' Passive exit observer adds resident memory; diagnostic run, not an unobserved capacity proof.'
        if args.nested_wait:
            records=aspect_exit_watch.read_wait(drive/'WAITSTAT.BIN')
            key=0x3920 if args.nested_wait=='space' else 0x011b
            checks['two_real_owned_WAIT_reads']=len(records)==2 and all(
                r['ds']==r['ss'] and r['ds']!=0 and r['parent_program']==2 and
                r['parent_snapshot']==r['waiting']==r['display_owned']==r['program_busy']==r['serial_active']==1 and
                r['serial_detached']==0 and r['key']==key for r in records)
            checks['all_WAIT_exits_clean']=len(report['exit_watch']['exits'])==4 and all(
                e[k]==0 for e in report['exit_watch']['exits'] for k in
                ['error','cleanup_error','external_scope','display_owned','program_busy','process_busy'])
            report['wait_reads']=records
            report['passed']=all(checks.values())
    if args.nested_wait:
        report['nested_wait']=args.nested_wait
        report['scope']+=' PROGRAM WAIT consumes actual BIOS '+args.nested_wait+' after graphics return; this is not ASPECT cancellation.'
    if args.lease_fault_phase:
        exits=report['exit_watch']['exits'];probes=report['exit_watch']['program_results']
        expected_error=12 if args.lease_fault_kind=='divide' else 5
        key={'divide':'actual_selected_divide','abort':'actual_typed_abort','dispatcher':'actual_dispatcher_unwind'}[args.lease_fault_kind]
        checks[key]=len(exits)==4 and exits[0]['error']==expected_error and exits[0]['opcode']==155 and probes[0]['stage']==256+args.lease_fault_phase
        checks['parent_lease_live_before_divide']=probes[0]['status']==1
        fault_ds=probes[0]['display_status'];fault_ss=probes[0]['serial_status']
        checks['selected_fault_DS_SS']=fault_ds==0xb800 and fault_ss!=fault_ds if args.lease_fault_foreign_ds else fault_ds==fault_ss and fault_ds!=0
        checks['later_calls_succeed']=len(exits)==4 and all(e['error']==0 for e in exits[1:]) and probes[3]['stage']==2 and probes[3]['status']==0
        checks['all_owners_retired']=all(e[k]==0 for e in exits for k in ['cleanup_error','external_scope','display_owned','program_busy','process_busy'])
        if args.fault_open_streams:
            pointers=aspect_exit_watch.read_buffers(drive/'BUFPTRS.BIN')
            checks['twelve_buffers_live_at_fault']=probes[0]['process_status']==0x0606
            checks['all_buffer_pointers_retired']=len(exits)==4 and all(v==0 for row in pointers for v in row)
            checks['held_files_preserved']=all((drive/f'HOLD{i}.BIN').read_bytes()==f'HELD{i}|'.encode() for i in range(6))
            report['buffer_exit_pointers']=pointers[:len(exits)]
        report['lease_fault_phase']=args.lease_fault_phase
        report['fault_witness']=dict(kind=args.lease_fault_kind,parent_lease_live=probes[0]['status']==1,ds=fault_ds,ss=fault_ss,foreign_ds=args.lease_fault_foreign_ds)
        report['passed']=all(checks.values())
        report['scope']+=' One selected '+args.lease_fault_kind+' fault in FAULT.ASX, then six streams/missing-file recovery and normal nested FIRST.ASX in the same terminal. No injected cleanup success.'
    if args.inner_screen:
        report['inner_screen']=snapshot_screen_watch.verify(drive/'SSCREEN.BIN',args.display_rows)
        checks['child_observed_graphics_mode']=(drive/'CHMODE.BIN').read_bytes()==b'\x13'*(3 if args.streams_around_child else 2)
        checks['marker_files_created']=all((drive/n).exists() and (drive/n).stat().st_size==0 for n in ['FPRE.TXT','FPST.TXT'])
        report['passed']=all(checks.values())
        report['scope']+=' Separate386/XMS/UMB passive full inner screen/cursor witness and child-reported BIOS graphics mode; no physical timing claim.'
    (out / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
    if args.lease_fault_phase:assert 'all_owners_retired' in checks and 'selected_fault_DS_SS' in checks
    print({k:v for k,v in checks.items() if not v})
    assert report['passed']


if __name__ == '__main__':
    main()
