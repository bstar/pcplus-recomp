#!/usr/bin/env python3
"""Seven ASPECT invocations in one parent: valid, five ALARM errors, valid."""
import argparse
import json
import shutil
import struct
import subprocess
from pathlib import Path
import aspect_exit_watch as watch
import test_connection_dos as harness
from directory_fixtures import prm
from test_directory_key_bindings_dos import actions
from build_context_help import ROOT, sha
from compiler import compile_source
from alarm_error_fixtures import mutate

CHILD = '''BITS 16
CPU 8086
ORG 100h
 mov dx,name
 mov ax,0x3d02
 int 0x21
 jnc opened
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
 mov dx,token
 mov cx,1
 mov ah,0x40
 int 0x21
 jc failed
 cmp ax,1
 jne failed
 mov ah,0x3e
 int 0x21
 jc failed
 mov ax,0x4c00
 int 0x21
failed:
 mov ax,0x4c01
 int 0x21
name: db 'D:\\CHILD.LOG',0
token: db 'T'
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('parent', 'child', 'errors', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    parent, child, errors, out = (getattr(args, n).resolve() for n in ('parent', 'child', 'errors', 'output'))
    assert out.is_relative_to(ROOT / 'build') and not out.exists()
    gate = json.loads((errors / 'checks.json').read_text())
    assert gate['passed'] and len(gate['cases']) == 5
    assert gate['terminal_sha256'] == sha(parent) and gate['runner_sha256'] == sha(child)
    sources = {}
    for product in (parent, child):
        manifest = json.loads(product.with_name('manifest.json').read_text())
        assert manifest['binary_sha256'] == sha(product) and not manifest.get('diagnostic_build')
        for name, digest in manifest['sources'].items():
            assert sha(ROOT / name) == digest, name
            sources[name] = digest
    out.mkdir()
    stage = out / 'program'
    stage.mkdir()
    for product in (parent, child):
        shutil.copyfile(product, stage / product.name)
    (out / 'NEST.ASM').write_text(CHILD)
    subprocess.run(['nasm', '-fbin', str(out / 'NEST.ASM'), '-o', str(out / 'NEST.COM')], check=True)
    files = {'ASPECT.EXE': child.read_bytes(), 'NEST.COM': (out / 'NEST.COM').read_bytes()}
    recover = 'proc main\n'
    for slot in range(6):
        recover += f'fopen {slot} "D:\\SLOT{slot}.BIN" "wb"\nif failure\nexit\nendif\nfputs {slot} "BEFORE{slot}|"\n'
    recover += 'run "D:\\NEST.COM" NOCLEAR\n'
    for slot in range(6):
        recover += f'fputs {slot} "AFTER{slot}|"\nfclose {slot}\n'
    recover += 'alarm 0\ntransmit "RECOVEROK^M"\nendproc\n'
    files['RECOVER.ASP'] = recover.encode()
    files['RECOVER.ASX'] = compile_source(recover)
    bindings = bytearray(actions(b'D:\\RECOVER.ASX', 0))
    expected = [0]
    inputs = {str((errors / 'checks.json').relative_to(ROOT)): sha(errors / 'checks.json')}
    for index, case in enumerate(gate['cases'], 1):
        folder = errors / case['case']
        kind = case['case'].removeprefix('alarm-vm-errors-')
        original = (folder / 'LOGIN.ASP').read_text()
        assert mutate(compile_source(original), kind) == (folder / 'LOGIN.ASX').read_bytes()
        text = 'proc main\ntransmit "ERR'+str(index)+'START"\nalarm '+('-1' if kind=='negative' else '4')+'\ntransmit "BADAFTER"\nendproc\n'
        value = mutate(compile_source(text), kind)
        name = f'ERR{index}.ASX'
        files[name] = value
        files[f'ERR{index}.ASP'] = text.encode()
        inputs[str((folder / 'LOGIN.ASX').relative_to(ROOT))] = sha(folder / 'LOGIN.ASX')
        bindings[index * 54:(index + 1) * 54] = struct.pack('<H', 0) + ('D:\\' + name).encode().ljust(52, b'\0')
        expected.append(case['passive_observer_header'][6])
    assert expected == [0, 7, 7, 7, 5, 5]
    expected.append(0)
    files['ACTIONS.KEY'] = bytes(bindings)
    sources.update(watch.build(parent, child, out / 'EWATCH.COM'))
    files['EWATCH.COM'] = (out / 'EWATCH.COM').read_bytes()
    settings = bytearray(prm(port=3, baud=5))
    for offset, value in ((0x188,5),(0x4e4,8),(0x4e6,4),(0x1c2,0),(0x1c8,2),
                          (0x1ca,25),(0x4ec,0),(0x1bc,0),(0x1be,4),(0x1e6,0)):
        struct.pack_into('<H', settings, offset, value)
    harness.BINARY = stage / parent.name
    assert not (ROOT / 'build/connection-dos' / out.name).exists()
    schedule = 'p900 enter p3500 a-1 p1500 ' + ' '.join(f'a-{i} p1500' for i in range(2,7)) + ' a-1 p1500 r e a d y enter p700 a-x'
    connection = harness.run(out.name, 'success', schedule, prm=bytes(settings),
                             arguments='@TEST.PRM /T:D:\\ACTIONS.KEY /D:CaseTest:23',
                             com=3, irq=5, cpu='386', working_drive='d', timeout=40,
                             files=files, observer='EWATCH', observer_high=True)
    capture = ROOT / 'build/connection-dos' / out.name
    telemetry = watch.read(capture / 'EXITSTAT.BIN')
    exits = telemetry['exits']
    wire = (capture / 'serial.bin').read_bytes()
    checks = dict(connection['checks'], seven_actual_invocations=telemetry['launches'] == len(exits) == 7,
                  exact_exit_errors=[e['error'] for e in exits] == expected,
                  exact_DOS_exit_codes=[e['exit'] for e in exits] == expected,
                  all_child_ABIs=all(e['ds'] == e['ss'] and e['ds'] for e in exits),
                  all_owners_retired=all(e[k] == 0 for e in exits for k in ('cleanup_error','external_scope','display_owned','program_busy','process_busy')),
                  two_recoveries=wire.count(b'RECOVEROK\r') == 2,
                  errors_do_not_continue=b'BADAFTER' not in wire,
                  two_nested_children=(capture / 'CHILD.LOG').is_file() and (capture / 'CHILD.LOG').read_bytes() == b'TT',
                  six_buffered_streams_reusable=all((capture / f'SLOT{i}.BIN').is_file() and (capture / f'SLOT{i}.BIN').read_bytes() == f'BEFORE{i}|AFTER{i}|'.encode() for i in range(6)),
                  parent_keys_resume=b'ready' in wire)
    for name in ('standalone/test_alarm_error_recovery_dos.py','standalone/alarm_error_fixtures.py','standalone/test_connection_dos.py',
                 'standalone/test_directory_key_bindings_dos.py','standalone/directory_fixtures.py','src/aspect/compiler.py'):
        sources[name] = sha(ROOT / name)
    for name, digest in sources.items():
        assert sha(ROOT / name) == digest, name
    result = dict(passed=all(checks.values()), checks=checks, products={'TERMINAL.EXE':sha(parent),'ASPECT.EXE':sha(child)},
                  exit_watch=telemetry, sources=sources, inputs=inputs,
                  artifacts={str(f.relative_to(ROOT)):sha(f) for f in capture.iterdir() if f.is_file()},
                  child_source=CHILD, recovery_source=recover, original_inputs=[],
                  scope=__doc__ + ' Actual 386 DOS/UART, UMB passive observer, owned modem peer; no automatic application recovery substitute, physical modem or full arbitrary-bytecode safety claim.')
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print('PASS' if result['passed'] else 'FAIL', checks)
    assert result['passed']


if __name__ == '__main__':
    main()
