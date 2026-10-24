#!/usr/bin/env python3
"""Run an actual DOS child beneath attached ASPECT at logical width132."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys

from product_inputs import ROOT, select_product
from enigma_peer_width_aspect_dos import observer
sys.path.insert(0, str(ROOT / 'standalone'))
import test_connection_dos as harness
from test_directory_key_bindings_dos import actions
sys.path.insert(0, str(ROOT / 'src/aspect'))
from compiler import compile_source


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


CHILD = r'''bits 16
cpu 8086
org 100h
push cs
pop ds
mov ax,0x0f00
int 0x10
mov [initial],ax
mov [page],bh
%ifdef GRAPHICS
mov ax,0x13
int 0x10
%else
mov ax,0xb800
mov es,ax
mov word [es:0],0x4e58
%endif
mov dx,name
xor cx,cx
mov ah,0x3c
int 0x21
jc failed
mov bx,ax
mov dx,initial
mov cx,3
mov ah,0x40
int 0x21
jc failed
cmp ax,3
jne failed
mov ah,0x3e
int 0x21
mov ax,0x4c25
int 0x21
failed:
mov ax,0x4c63
int 0x21
initial: dw 0
page: db 0
name: db 'D:\CHILD.BIN',0
'''


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--terminal', type=Path, required=True)
    p.add_argument('--runner', type=Path, required=True)
    p.add_argument('--compiler', type=Path)
    p.add_argument('--window', action='store_true')
    p.add_argument('--noclear', action='store_true')
    p.add_argument('--graphics', action='store_true')
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    binary, inputs = select_product(a.terminal, 'TERMINAL.EXE')
    runner, extra = select_product(a.runner, 'ASPECT.EXE')
    inputs += extra + [binary, runner]
    out = a.output.resolve()
    assert out.is_relative_to(ROOT / 'build') and not out.exists()
    out.mkdir(parents=True)
    parent = out / 'parent'
    parent.mkdir()
    for path in [binary, runner]:
        shutil.copyfile(path, parent / path.name)
    script = ('proc main\nfopen 4 "D:\\WIDE.LOG" "wb"\nfputs 4 "START|"\npause 2\n'
              'transmit "SCRIPTREADY^M"\nwaitfor "WIDTHREADY" 8\n'
              'if failure\nfputs 4 "FAILWIDTH|"\nfclose 4\nexit\nendif\n'
              'fputs 4 "WIDE|"\npause 1\nrun "D:\\CHILD.COM"' +
              (' NOCLEAR' if a.noclear else '') + '\n'
              'fputs 4 "CHILDRETURN|"\ntransmit "AFTERCHILD^M"\n'
              'waitfor "RESUMED" 8\nif waitfor\nfputs 4 "RESUMED|"\n'
              'else\nfputs 4 "FAILRESUME|"\nendif\nfclose 4\nendproc\n')
    files = {'ACTIONS.KEY': actions(b'D:\\WIDE.ASP' if a.compiler else b'D:\\WIDE.ASX', 0)}
    if a.compiler:
        compiler, extra = select_product(a.compiler, 'ASPCOMP.EXE')
        inputs += extra + [compiler]
        shutil.copyfile(compiler, parent / compiler.name)
        files['WIDE.ASP'] = script.encode('ascii')
    else:
        files['WIDE.ASX'] = compile_source(script)
    (out / 'child.asm').write_text(CHILD)
    subprocess.run(['nasm', '-fbin', *(['-DGRAPHICS'] if a.graphics else []),
                    str(out / 'child.asm'), '-o', str(out / 'CHILD.COM')], check=True)
    files['CHILD.COM'] = (out / 'CHILD.COM').read_bytes()
    observer(binary, out)
    symbols = {n: (int(s, 16), int(o, 16)) for s, o, n in re.findall(
        r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',
        (binary.parent / 'terminal.map').read_text(), re.M | re.I)}
    with (out / 'bbs_width_offsets.inc').open('a') as stream:
        for name in ['render_program_owned', 'render_program_begins', 'render_program_ends']:
            assert symbols[name][0] == symbols['render_attached'][0]
            stream.write(f'%define {name.upper()} {symbols[name][1]}\n')
    watch = (ROOT / 'lab/bbs/peer_width_aspect_watch.asm').read_text()
    watch = watch.replace('sample_end:', 'nested_status: dw 0xffff\nnested_execs: dw 0\n'
                          'nested_owner: dw 0xffff\nfinal_owned: dw 0xffff\n'
                          'final_begins: dw 0\nfinal_ends: dw 0\n'
                          'bridge_cursor_calls: dw 0\nsample_end:', 1)
    needle = '.done:\n restore\n jmp far [cs:old10]\n'
    assert watch.count(needle) == 1
    watch = watch.replace(needle, '''.done:
 cmp ah,2
 jne .cursor_checked
 cmp word [cs:staged],1
 jne .cursor_checked
 mov ax,ds
 cmp ax,[cs:root_ds]
 jne .cursor_checked
 sub ax,DGROUP_REL
 add ax,ASPECT_CODE_REL
 mov es,ax
 cmp word [es:RENDER_ATTACHED],1
 jne .cursor_checked
 cmp word [es:RESIDENT_BRIDGE_BUSY],1
 jne .cursor_checked
 inc word [cs:bridge_cursor_calls]
.cursor_checked:
 restore
 jmp far [cs:old10]
''', 1)
    needle = ' inc word [cs:child_count]\n'
    assert watch.count(needle) == 1
    watch = watch.replace(needle, ' cmp word [cs:child_count],0\n jne .child_record\n'
                          ' mov [cs:nested_status],ax\n.child_record:\n' + needle, 1)
    needle = 'handler21:\n'
    assert watch.count(needle) == 1
    watch = watch.replace(needle, needle + ''' save
 cmp ah,0x4b
 jne .exec_checked
 cmp word [cs:staged],1
 jne .exec_checked
 mov ax,[cs:root_ds]
 sub ax,DGROUP_REL
 add ax,ASPECT_CODE_REL
 mov es,ax
 mov ax,[es:RENDER_PROGRAM_OWNED]
 or ax,ax
 jz .exec_checked
 inc word [cs:nested_execs]
 mov [cs:nested_owner],ax
.exec_checked:
 restore
''', 1)
    needle = ' mov [cs:final_aspect],ax\n'
    assert watch.count(needle) == 1
    watch = watch.replace(needle, needle + ''' mov ax,[es:RENDER_PROGRAM_OWNED]
 mov [cs:final_owned],ax
 mov ax,[es:RENDER_PROGRAM_BEGINS]
 mov [cs:final_begins],ax
 mov ax,[es:RENDER_PROGRAM_ENDS]
 mov [cs:final_ends],ax
''', 1)
    (out / 'process-watch.asm').write_text(watch)
    subprocess.run(['nasm', '-fbin', '-I' + str(out) + '/',
                    str(out / 'process-watch.asm'), '-o', str(out / 'BWATCH.COM')], check=True)
    # The compiler exits before width132 identifies the root. The nested COM
    # and interpreter exit after identification; require both actual exits.
    files['BWATCH.COM'] = (out / 'BWATCH.COM').read_bytes()
    original = Path(harness.__file__).read_text()
    # BWATCH removes its own hooks at root exit; invoking it again would install
    # a second observer immediately before the after-snapshot.
    assert original.count('{observer_stop}\n') == 1
    original = original.replace('{observer_stop}\n', '')
    needle = "out=ROOT/'build/connection-dos'/name"
    assert original.count(needle) == 1
    scope = dict(harness.__dict__, LABEL_ROOT=out)
    exec(compile(original.replace(needle, 'out=LABEL_ROOT/name'), harness.__file__, 'exec'), scope)
    scope['BINARY'] = parent / 'TERMINAL.EXE'
    settings = bytearray(harness.fixture(timeout=5))
    manifest = json.loads((binary.parent / 'manifest.json').read_text())
    if manifest.get('experimental_custom_irq'):
        struct.pack_into('<HH', settings, 0x184, 4, 3)
    if manifest.get('experimental_mouse'):
        struct.pack_into('<HH', settings, 0x4e4, 8, 4)
    inputs += [Path(__file__), ROOT / 'lab/bbs/enigma_peer_width_aspect_dos.py',
               ROOT / 'lab/bbs/peer_width_aspect_watch.asm', ROOT / 'lab/bbs/product_inputs.py',
               Path(harness.__file__), ROOT / 'standalone/test_terminal.py',
               ROOT / 'standalone/test_directory_key_bindings_dos.py',
               ROOT / 'standalone/modem_fixtures.py', ROOT / 'standalone/terminal_config_fixtures.py',
               ROOT / 'standalone/directory_test_support.py', ROOT / 'src/aspect/compiler.py',
               out / 'child.asm', out / 'CHILD.COM', out / 'BWATCH.COM',
               out / 'bbs_width_offsets.inc', out / 'process-watch.asm', *parent.iterdir()]
    frozen = {str(path.relative_to(ROOT)): sha(path) for path in inputs}
    keys = 'p900 enter p2300 a-1 ' + ('p600 a-z ' if a.window else '') + 'p8500 r e a d y p1200 a-x'
    result = scope['run']('product', 'success', keys, prm=bytes(settings), files=files,
        observer='BWATCH', cpu='8086',
        arguments='@D:\\TEST.PRM /D:CaseTest:23 /T:D:\\ACTIONS.KEY',
        online_triggers=[(b'SCRIPTREADY\r', b'\x1b[?3h\x1b[2;121HINITIAL\x1b[6nWIDTHREADY'),
                         (b'AFTERCHILD\r', b'\x1b[6n\x1b[3;121HRESUMED\x1b[6n'),
                         (b'ready', b'\x1b[?3l\x1b[2;73HNARROW!\x1b[6n')])
    folder = out / 'product'
    raw = (folder / 'BBSOBS.BIN').read_bytes() if (folder / 'BBSOBS.BIN').exists() else b''
    state = struct.unpack('<28H', raw) if len(raw) == 56 else ()
    wire = (folder / 'serial.bin').read_bytes()
    marker = (folder / 'WIDE.LOG').read_bytes() if (folder / 'WIDE.LOG').exists() else b''
    child = (folder / 'CHILD.BIN').read_bytes() if (folder / 'CHILD.BIN').exists() else b''
    checks = dict(result['checks'])
    checks.pop('immediate_banner_not_dropped', None)
    checks.update(script_progress=marker == b'START|WIDE|CHILDRETURN|RESUMED|',
                  actual_child=child == b'\x03\x50\x00',
                  exact_ASX=(folder / 'WIDE.ASX').exists() and (folder / 'WIDE.ASX').read_bytes() == compile_source(script),
                  observer_root=bool(state) and state[:2] == (0x4257, 1) and state[2] == state[3] != 0,
                  two_exits=bool(state) and state[4:6] == (2, 0) and state[21] == 37,
                  real_external_lease=bool(state) and state[22:27] == (1, 1 if a.noclear else 2, 0, 1, 1),
                  attached_renderer=bool(state) and state[9] > 0 and state[27] > 0,
                  script_window=bool(state) and (state[11] > 0) == a.window,
                  normal_parent=bool(state) and state[8] == 0 and state[12:21] == (80, 0, 0, 0, 0, 0, 0, 0, 1),
                  wide_before=b'\x1b[2;128R' in wire,
                  continued_renderer=b'\x1b[3;128R' in wire,
                  keyboard_and_narrow=b'ready' in wire and b'\x1b[2;80R' in wire,
                  inputs_unchanged=frozen == {str(path.relative_to(ROOT)): sha(path) for path in inputs})
    report = dict(passed=all(checks.values()), checks=checks, inputs=frozen, state=state,
                  marker=marker.decode('ascii', errors='replace'), script=script,
                  source_compilation=bool(a.compiler), window=a.window, noclear=a.noclear, graphics=a.graphics,
                  binary_sha256=sha(binary), runner_sha256=sha(runner),
                  artifacts={str(path.relative_to(ROOT)): sha(path) for path in out.rglob('*') if path.is_file()},
                  scope='Actual DOS child beneath attached ASPECT after a peer width132 commit; continued renderer/keyboard/width changes and hardware restoration. Synthetic serial modem, no physical or full-plane preservation claim.')
    (out / 'checks.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(passed=report['passed'], checks=checks, state=state, marker=report['marker']), indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
