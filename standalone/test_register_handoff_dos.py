#!/usr/bin/env python3
"""Inspect all register bytes across real DOS ASPECT invocations and failures."""
import argparse
import hashlib
import json
import re
import shutil
import struct
import subprocess
import sys
from pathlib import Path

import test_connection_dos as harness
from directory_fixtures import directory, prm
from test_directory_key_bindings_dos import actions

ROOT = harness.ROOT
sys.path.insert(0, str(ROOT / 'src/aspect'))
from compiler import compile_source


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def symbols(path):
    return {name: (int(seg, 16), int(off, 16)) for seg, off, name in re.findall(
        r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$', path.read_text(), re.M | re.I)}


def seal(raw, token):
    value = token
    for byte in raw:
        value = (((value << 1) | (value >> 15)) & 65535) ^ byte
    return value


def reset(raw):
    result = bytearray(raw)
    result[:20] = bytes(20)
    for index in range(10):
        result[20 + index * 81] = 0
    return bytes(result)


def assigned(previous, generation):
    result = bytearray(reset(previous))
    values = [generation * 1000 + index * 29 for index in range(10)]
    struct.pack_into('<10H', result, 0, *values)
    strings = [('A' * 76 + f'{index:04}') if generation == 1 else f'B{index}' for index in range(10)]
    for index, text in enumerate(strings):
        start = 20 + index * 81
        # Native assignment flushes the complete 81-byte scratch slot.
        result[start:start + 81] = text.encode() + bytes(81 - len(text))
    return bytes(result), values, strings


def script(generation, fault=False, hide=False):
    _, values, strings = assigned(bytes(830), generation)
    source = 'integer ' + ','.join(f'g{i}' for i in range(10)) + '\nproc main\nrun "D:\\DUMP.COM" NOCLEAR\n'
    for index in range(10):
        source += f'g{index}={values[index]}\ns{index}="{strings[index]}"\n'
    source += 'run "D:\\DUMP.COM" NOCLEAR\n'
    if fault:
        source += 'run "D:\\FAULT.COM" NOCLEAR\n'
    if hide:
        source += 'run "D:\\HIDE.COM" NOCLEAR\n'
    source += f'transmit "BANK{generation}^M"\nendproc\n'
    compiled = compile_source(source)
    # The maintained compiler exposes native S0..S9 but not integer bank A.
    # Explicit native operand fixtures route ten unique global destinations
    # (tag8D,index) to the recovered bank-A destination (tag65,index).
    patches = []
    for index in range(10):
        old = bytes([0x8d, index])
        assert compiled.count(old) == 1, (index, compiled.count(old))
        at = compiled.index(old)
        compiled = compiled[:at] + bytes([0x65, index]) + compiled[at + 2:]
        patches.append(dict(offset=at, before=old.hex(), after=bytes([0x65, index]).hex()))
    return source, compiled, patches


def observer(parent, child):
    owner_seg, owner_off = parent['_terminal_register_owner']
    integer_seg, integer_off = child['_runtime_integer_a']
    string_seg, string_off = child['_runtime_string_bank_a']
    assert integer_seg == string_seg
    return f'''BITS 16
CPU 8086
ORG 0x100
start:
 mov ax,[0x16]
 mov [child_psp],ax
 mov es,ax
 mov ax,[es:0x16]
 add ax,{16 + owner_seg}
 mov [parent_segment],ax
 mov dx,counter
 mov ax,0x3d00
 int 0x21
 jc first
 mov bx,ax
 mov dx,number
 mov cx,1
 mov ah,0x3f
 int 0x21
 jc failed
 cmp ax,1
 jne failed
 mov ah,0x3e
 int 0x21
 jc failed
 jmp numbered
first:
 cmp ax,2
 jne failed
numbered:
 cmp byte [number],9
 ja failed
 mov al,[number]
 add al,'0'
 mov [owner_name+5],al
 mov [child_name+5],al
 inc byte [number]
 mov dx,counter
 xor cx,cx
 mov ah,0x3c
 int 0x21
 jc failed
 mov bx,ax
 mov dx,number
 mov cx,1
 mov ah,0x40
 int 0x21
 jc failed
 cmp ax,1
 jne failed
 mov ah,0x3e
 int 0x21
 jc failed
 mov dx,owner_name
 call create
 push ds
 mov ds,[parent_segment]
 mov dx,{owner_off}
 mov cx,1734
 call write
 pop ds
 call close
 mov dx,child_name
 call create
 mov ax,[child_psp]
 add ax,{16 + integer_seg}
 push ds
 mov ds,ax
 mov dx,{integer_off}
 mov cx,20
 call write
 mov dx,{string_off}
 mov cx,810
 call write
 pop ds
 call close
 mov ax,0x4c00
 int 0x21
create:
 xor cx,cx
 mov ah,0x3c
 int 0x21
 jc failed
 mov bx,ax
 ret
write:
 mov ah,0x40
 int 0x21
 jc failed
 cmp ax,cx
 jne failed
 ret
close:
 mov ah,0x3e
 int 0x21
 jc failed
 ret
failed:
 mov ax,0x4c02
 int 0x21
child_psp: dw 0
parent_segment: dw 0
number: db 0
counter: db 'COUNT.DAT',0
owner_name: db 'OWNER0.BIN',0
child_name: db 'CHILD0.BIN',0
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label', required=True)
    parser.add_argument('--port', type=int, choices=[1, 2], default=1)
    parser.add_argument('--case', choices=['normal', 'bad-token', 'missing-script', 'missing-helper'], default='normal')
    args = parser.parse_args()
    assert re.fullmatch('[A-Za-z0-9_-]+', args.label)
    output = ROOT / 'build/register-handoff-dos' / args.label
    output.mkdir(parents=True, exist_ok=False)
    parent = ROOT / 'build/terminal-directory-keys-process-bank-session-capture-projection-bound-registers'
    child = ROOT / 'build/aspect-register-parent'
    sources = {}
    for folder, name in [(parent, 'TERMINAL.EXE'), (child, 'ASPECT.EXE')]:
        manifest = json.loads((folder / 'manifest.json').read_text())
        assert manifest['experimental_register_handoff'] and sha(folder / name) == manifest['binary_sha256']
        for path, digest in manifest['sources'].items():
            assert path not in sources or sources[path] == digest
            sources[path] = digest
    parent_symbols = symbols(parent / 'terminal.map')
    helper = output / 'DUMP.ASM'
    helper.write_text(observer(parent_symbols, symbols(child / 'ASPECT.map')))
    subprocess.run(['nasm', '-fbin', str(helper), '-o', str(output / 'DUMP.COM')], check=True)
    seg, off = parent_symbols['_terminal_register_owner']
    (output / 'FAULT.ASM').write_text(f'''BITS 16
CPU 8086
ORG 0x100
 mov ax,[0x16]
 mov es,ax
 mov ax,[es:0x16]
 add ax,{16 + seg}
 mov es,ax
 xor word [es:{off + 68}],1
 mov ax,0x4c00
 int 0x21
''')
    subprocess.run(['nasm', '-fbin', str(output / 'FAULT.ASM'), '-o', str(output / 'FAULT.COM')], check=True)
    for name, before, after in [('HIDE', 'EXE', 'SAV'), ('RESTORE', 'SAV', 'EXE')]:
        rename = output / (name + '.ASM')
        rename.write_text(f'''BITS 16
CPU 8086
ORG 0x100
 push ds
 pop es
 mov dx,old_name
 mov di,new_name
 mov ah,0x56
 int 0x21
 jc failed
 mov dx,flag_name
 xor cx,cx
 mov ah,0x3c
 int 0x21
 jc failed
 mov bx,ax
 mov ah,0x3e
 int 0x21
 jc failed
 mov ax,0x4c00
 int 0x21
failed:
 mov ax,0x4c02
 int 0x21
old_name: db 'C:\\ASPECT.{before}',0
new_name: db 'C:\\ASPECT.{after}',0
flag_name: db '{name}.OK',0
''')
        subprocess.run(['nasm', '-fbin', str(rename), '-o', str(output / (name + '.COM'))], check=True)
    package = output / 'package'
    package.mkdir()
    shutil.copyfile(parent / 'TERMINAL.EXE', package / 'TERMINAL.EXE')
    shutil.copyfile(child / 'ASPECT.EXE', package / 'ASPECT.EXE')
    bindings = bytearray(actions(b'FIRST.ASX', 0))
    for index, target in [(1, b'BAD.ASX' if args.case == 'bad-token' else b'ABSENT.ASX' if args.case == 'missing-script' else b'SECOND.ASX'),
                          (2, b'SECOND.ASX'), (3, b'OBSERVE.ASX')]:
        struct.pack_into('<H', bindings, index * 54, 0)
        bindings[index * 54 + 2:index * 54 + 2 + len(target)] = target
    if args.case == 'missing-helper':
        for index, kind, target in [(2, 1, b'D:\\RESTORE.COM'), (3, 0, b'SECOND.ASX'), (4, 0, b'OBSERVE.ASX')]:
            bindings[index * 54:(index + 1) * 54] = struct.pack('<H', kind) + target + bytes(52 - len(target))
    files = {'ACTIONS.KEY': bytes(bindings), 'DUMP.COM': (output / 'DUMP.COM').read_bytes(),
             'FAULT.COM': (output / 'FAULT.COM').read_bytes(),
             'OBSERVE.ASX': compile_source('proc main\nrun "D:\\DUMP.COM" NOCLEAR\ntransmit "OBSERVE^M"\nendproc\n')}
    for name in ['HIDE', 'RESTORE']:
        files[name + '.COM'] = (output / (name + '.COM')).read_bytes()
    patches = {}
    for name, generation, fault in [('FIRST', 1, False), ('SECOND', 2, False), ('BAD', 2, True)]:
        source, compiled, edits = script(generation, fault, hide=name == 'FIRST' and args.case == 'missing-helper')
        (output / (name + '.ASP')).write_text(source)
        files[name + '.ASX'] = compiled
        patches[name] = edits
    raw = bytearray(directory(port=args.port))
    raw[250 + 0x56:250 + 0x56 + 9] = b'actions\0\0'
    settings = bytearray(prm(port=args.port))
    struct.pack_into('<HH', settings, 0x4e4, 8, 4)
    keys = 'p3000 a-1 p900 a-2 p900 '
    if args.case in ('bad-token', 'missing-script'):
        keys += 'p300 a-3 p900 '
    if args.case == 'missing-helper':
        keys += 'space p300 a-3 p900 space p300 a-4 p900 a-5 p700 '
    else:
        keys += 'a-4 p700 '
    keys += 'r e a d y p500 a-x'
    harness.BINARY = package / 'TERMINAL.EXE'
    result = harness.run('register-' + args.label, 'success', keys, directory=bytes(raw), prm=bytes(settings),
                         com=args.port, working_drive='d', arguments='@D:\\TEST.PRM /E:D:\\TEST.DIR /N:1',
                         files=files, cpu='8086', online_triggers=[(b'OBSERVE\r', b'\x1b[5n')])
    folder = ROOT / 'build/connection-dos' / ('register-' + args.label)
    zero = bytes(830)
    first, _, _ = assigned(zero, 1)
    second, _, _ = assigned(first, 2)
    expected = [(zero, zero), (zero, first), (first, reset(first))]
    if args.case == 'bad-token':
        expected += [(first, second), (first, reset(first))]
    expected += [(first, second), (second, reset(second))]
    # Missing script never initializes the interpreter or runs the observer.
    if args.case in ('missing-script', 'missing-helper'):
        expected = [(zero, zero), (zero, first), (first, reset(first)), (first, second), (second, reset(second))]
    tokens = [1, 1, 2, 2, 3]
    epochs = [0, 0, 1, 1, 2]
    if args.case == 'bad-token':
        tokens = [1, 1, 2, 2, 3, 3, 4]
        epochs = [0, 0, 1, 1, 1, 1, 3]
    elif args.case in ('missing-script', 'missing-helper'):
        tokens = [1, 1, 3, 3, 4]
        epochs = [0, 0, 1, 1, 3]
    snapshots = []
    for index, (accepted, live) in enumerate(expected):
        owner = (folder / f'OWNER{index}.BIN').read_bytes()
        actual_live = (folder / f'CHILD{index}.BIN').read_bytes()
        phase, token, epoch, checksum = struct.unpack_from('<4H', owner)
        assert len(owner) == 1734 and phase == 1
        assert token == tokens[index] and epoch == epochs[index], (index, token, epoch)
        assert owner[904:] == accepted, (index, 'accepted bank')
        assert checksum == seal(accepted, epoch), (index, 'accepted seal')
        assert actual_live == live, (index, 'live bank',
                                     [(n, a, b) for n, (a, b) in enumerate(zip(actual_live, live)) if a != b][:12])
        assert owner[74:904] == reset(accepted), (index, 'prepared exchange')
        snapshots.append(dict(index=index, token=token, epoch=epoch, owner_sha256=sha(folder / f'OWNER{index}.BIN'),
                              child_sha256=sha(folder / f'CHILD{index}.BIN')))
    assert len(list(folder.glob('OWNER*.BIN'))) == len(expected)
    wire = (folder / 'serial.bin').read_bytes()
    expected_wire = b'BANK1\r' + (b'BANK2\r' if args.case == 'bad-token' else b'') + b'BANK2\rOBSERVE\rready'
    assert expected_wire in wire.replace(b'\x1b[0n', b''), wire
    assert wire.index(b'OBSERVE\r') < wire.index(b'\x1b[0n'), 'No real RX/parser reply after final child'
    assert result['passed'], result
    if args.case == 'missing-helper':
        assert (folder / 'HIDE.OK').exists() and (folder / 'RESTORE.OK').exists()
        assert sha(package / 'ASPECT.EXE') == sha(child / 'ASPECT.EXE')
        assert not (package / 'ASPECT.SAV').exists()
    for name in ['standalone/test_register_handoff_dos.py', 'standalone/test_connection_dos.py',
                 'standalone/test_terminal.py', 'standalone/test_directory_key_bindings_dos.py',
                 'standalone/directory_fixtures.py', 'standalone/directory_test_support.py',
                 'standalone/terminal_config_fixtures.py', 'standalone/modem_fixtures.py', 'src/aspect/compiler.py']:
        sources[name] = sha(ROOT / name)
    for name, digest in sources.items():
        assert sha(ROOT / name) == digest, name
        dest = output / 'sources' / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, dest)
    report = dict(passed=True, case=args.case, port=args.port, cpu='8086', snapshots=snapshots, sources=sources,
                  operand_fixture_patches=patches, parent_sha256=sha(parent / 'TERMINAL.EXE'), child_sha256=sha(child / 'ASPECT.EXE'),
                  DOS=result, scope='Actual source-built DOS terminal/ASPECT and nested observer. All830 register bytes, native reset/tails, returned acceptance and continued serial output. Integer-bank-A destinations are explicit native operand fixtures, not a compiler feature claim. Synthetic modem, no physical hardware or HOOK routing acceptance.')
    (output / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
    print('PASS', args.case, args.port, len(expected), 'complete bank snapshots')


if __name__ == '__main__':
    main()
