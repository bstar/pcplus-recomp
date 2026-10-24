#!/usr/bin/env python3
"""Run a menu-launched ASPECT login, then the owned Synchronet editor recipe.

Only the loopback synthetic LABUSER account is used. Drafts remain unsaved.
The username/password are sent by the source-built DOS child, not ADDKEY.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src/aspect'))
from compiler import compile_source
from modem import Telnet
from product_inputs import select_product
import hook_session_probe


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def observed_driver():
    """Add only an INT1C video observer around the unchanged DOS application."""
    sys.argv.pop(1)
    observer_high='--observer-high' in sys.argv
    if observer_high:sys.argv.remove('--observer-high')
    path = ROOT / 'lab/bbs/editor_dos_probe.py'
    adapter = path.read_text()
    marker = "exec(compile(text,str(source),'exec'),{'__file__':str(source),'__name__':'__main__'})"
    assert adapter.count(marker) == 1
    before = 'D:' + chr(92) * 2 + 'SNAP B'
    after = 'D:' + chr(92) * 2 + 'SNAP S'
    install = before + ('\nLOADHIGH C:' if observer_high else '\nC:') + chr(92) * 2 + 'SCRIPT T'
    collect = 'C:' + chr(92) * 2 + 'SCRIPT\n' + after
    prelude = (f'assert text.count({before!r}) == text.count({after!r}) == 1\n'
               f'text = text.replace({before!r}, {install!r}).replace({after!r}, {collect!r})\n')
    if observer_high:
        prelude += "assert text.count('[mixer]\\nnosound=true') == 1\ntext = text.replace('[mixer]\\nnosound=true', '[dos]\\numb=true\\n[mixer]\\nnosound=true')\n"
    exec(compile(adapter.replace(marker, prelude + marker), str(path), 'exec'),
         {'__file__': str(path), '__name__': '__main__'})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label', required=True)
    parser.add_argument('--hook-session',choices=['accept','reject'],help='Exercise live kind2 helper returns before editing')
    parser.add_argument('--source', action='store_true', help='Compile LOGON.ASP in the actual DOS child')
    parser.add_argument('--observer-high',action='store_true',help='Require the passive observer to reside in DOS upper memory')
    parser.add_argument('--terminal', type=Path, default=ROOT/'build/terminal/TERMINAL.EXE')
    parser.add_argument('--runner', type=Path, default=ROOT/'build/aspect-runner/ASPECT.EXE')
    parser.add_argument('--mouse-scales', type=int, nargs=2)
    parser.add_argument('--cpu', choices=['8086','286','386','486'], default='386')
    args = parser.parse_args()
    assert args.label and all(c.isalnum() or c in '-_' for c in args.label)
    output = ROOT / 'build/bbs-lab/results/synchronet' / args.label
    stage = ROOT / 'build/bbs-lab/script-login' / args.label
    assert not output.exists() and not stage.exists(), 'Preserve earlier attempts; choose a fresh label'
    stage.mkdir(parents=True)
    terminal, terminal_sources = select_product(args.terminal, 'TERMINAL.EXE')
    runner, runner_sources = select_product(args.runner, 'ASPECT.EXE')
    sys.path.insert(0, str(ROOT / 'standalone'))
    import test_script_launch_dos as launch
    launch.OUT = stage
    launch.watcher()
    watch = (stage / 'watch.asm').read_text().replace("'SCRIPT LIVE'", "'LOGIN SENT'")
    watch = watch.replace('sample: dw 4d43h,0,0,0',
                          'sample: dw 4d43h,0,0,0\nconsole: times 4000 db 0')
    watch = watch.replace('or [sample+2],bx', '''test [sample+2],bx
 jnz .seen
 push ds
 push es
 push si
 push di
 push cx
 push ds
 pop es
 mov ax,0xb800
 mov ds,ax
 xor si,si
 mov di,console
 mov cx,2000
 cld
 rep movsw
 pop cx
 pop di
 pop si
 pop es
 pop ds
.seen:
 or [sample+2],bx''')
    watch = watch.replace('mov dx,handler','mov ax,cs\n mov [sample+6],ax\n mov dx,handler')
    watch = watch.replace('mov cx,8', 'mov cx,4008').replace('cmp ax,8', 'cmp ax,4008')
    watch = watch.replace('buffer: times 8 db 0', 'buffer: times 4008 db 0')
    (stage / 'watch.asm').write_text(watch)
    subprocess.run(['nasm', '-f', 'bin', str(stage / 'watch.asm'), '-o', str(stage / 'SCRIPT.COM')], check=True)
    for product, leaf in [(terminal, 'TERMINAL.EXE'), (runner, 'ASPECT.EXE')]:
        shutil.copyfile(product, stage / leaf)
    # The terminal has already rendered Login:. A ready Password: is matched
    # by native WAITFOR before the second TRANSMIT. Returning immediately lets
    # the parent's renderer answer subsequent terminal queries and show logon.
    source = ('proc main\r\ntransmit "LABUSER^M"\r\n'
              'waitfor "Password:" 10\r\nif waitfor\r\n'
              'transmit "LABPASS42^M"\r\nmessage "LOGIN SENT"\r\n'
              'else\r\nmessage "PASSWORD PROMPT NOT RECEIVED"\r\n'
              'endif\r\nendproc\r\n')
    (stage / 'LOGON.ASP').write_bytes(source.encode('ascii'))
    if args.source:
        shutil.copyfile(ROOT/'build/aspect-compiler-dos/ASPCOMP.EXE',stage/'ASPCOMP.EXE')
    else:
        (stage / 'LOGON.ASX').write_bytes(compile_source(source))
    hook_sources=hook_session_probe.prepare(stage,terminal,args.hook_session) if args.hook_session else []
    recipe_path = ROOT / 'lab/bbs/synchronet-editor-recipe.json'
    original = json.loads(recipe_path.read_text())['keyboard_input']
    login = 'p13000 L A B U S E R enter p2000 L A B P A S S 4 2 enter p8000 '
    assert original.startswith(login)
    keys = ('p13000 a-z p300 a p300 l o g o n . a s x enter '
            'p8000 ' + original[len(login):])
    if args.source:
        keys=keys.replace('l o g o n . a s x','l o g o n . a s p')
    assert 'LABUSER' not in keys.replace(' ', '').upper()
    assert 'LABPASS42' not in keys.replace(' ', '').upper()
    assert 'enter' not in keys[keys.index('A B C D E'):].split()
    if args.hook_session:keys=hook_session_probe.schedule(keys)
    sources = hook_sources + [ROOT/'lab/bbs/hook_session_probe.py', Path(__file__), recipe_path, ROOT / 'src/aspect/compiler.py']
    sources += terminal_sources + runner_sources
    sources += [ROOT / 'standalone' / leaf for leaf in
                ('test_script_launch_dos.py', 'command_menu_watch.asm')]
    sources += [ROOT / 'lab/bbs' / leaf for leaf in
                ('editor_dos_probe.py', 'test_dos.py', 'modem.py', 'check_editor_dos.py')]
    inputs = {str(p.relative_to(ROOT)): sha(p) for p in sources}
    staged = {p.name: sha(p) for p in stage.iterdir() if p.is_file()}
    command = [sys.executable, str(Path(__file__)), '--observe-driver',
               str(stage / 'TERMINAL.EXE'), 'synchronet', '--port', '23231',
               '--label', args.label, '--com', '2', '--baud', '19200', '--flow', 'HARD',
               '--dial-fixture', '--timeout', '140', '--wait', '2', '--keys', keys]
    if args.hook_session:command += ['--meta-fixture',str(stage/'ACTIONS.KEY')]
    if args.observer_high:command += ['--observer-high']
    command += ['--cpu', args.cpu]
    if args.mouse_scales:
        command += ['--mouse-scales', *map(str, args.mouse_scales)]
    # Freeze the inputs, schedule and expected credential boundary before DOS.
    (stage / 'predictions.json').write_text(json.dumps(dict(
        sources=inputs, staged=staged, command=command,
        expected_login_wire_hex=b'LABUSER\rLABPASS42\r'.hex(),
        compile_in_DOS=args.source,expected_ASX_sha256=hashlib.sha256(compile_source(source)).hexdigest(),
        expected_editor_passed=True), indent=2) + '\n')
    with (stage / 'harness.log').open('w') as log:
        code = subprocess.call(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
    assert (output / 'result.json').exists(), 'No completed DOS report; preserve harness.log'
    with (stage / 'audit.log').open('w') as log:
        audit_code = subprocess.call([sys.executable, str(ROOT / 'lab/bbs/check_editor_dos.py'),
                                     'synchronet', '--label', args.label], cwd=ROOT,
                                    stdout=log, stderr=subprocess.STDOUT)
    run = json.loads((output / 'result.json').read_text())
    audit = json.loads((output / 'semantic-audit.json').read_text())
    codec = Telnet()
    wire, _ = codec.feed((output / 'bbs-sent.bin').read_bytes())
    display = (output / 'display.bin').read_bytes()
    prefix = wire.split(b'LABUSER', 1)[0] if b'LABUSER' in wire else wire
    observed = (output / 'SCRIPT.BIN').read_bytes() if (output / 'SCRIPT.BIN').exists() else b''
    magic, bits, ticks, observer_segment = struct.unpack('<4H', observed[:8]) if len(observed) == 4008 else (0, 0, 0, 0)
    checks = dict(
        DOS_harness=code == 0 and run['passed'],
        current_terminal=run['binary_sha256'] == staged['TERMINAL.EXE'] == sha(terminal),
        current_runner=staged['ASPECT.EXE'] == sha(runner),
        source_compilation=(not args.source or (stage/'LOGON.ASX').read_bytes()==compile_source(source)),
        inputs_unchanged=inputs == {str(p.relative_to(ROOT)): sha(p) for p in sources}
                         and all(sha(stage / leaf) == digest for leaf, digest in staged.items()),
        credentials_not_in_keyboard=run['keyboard_input'] == keys
                                   and 'LABPASS42' not in keys.replace(' ', '').upper(),
        script_credentials_once=wire.count(b'LABUSER\r') == wire.count(b'LABPASS42\r') == 1
                               and b'LABUSER\rLABPASS42\r' in wire,
        no_other_login_text_before_script=all(c in b'\x1b[?;0123456789cR' for c in prefix),
        authenticated_display=b'Logging on to LoC Protocol Lab as LABUSER' in display,
        no_error_or_blocking_return_prompt=magic == 0x4d43 and ticks > 0 and (bits & 6) == 0,
        observer_placement=not args.observer_high or observer_segment>=0xa000,
        resumed_parent_editor=audit_code == 0 and audit['passed'],
        draft_aborted=audit['checks']['draft_aborted'],
    )
    if args.hook_session:
        hook=hook_session_probe.inspect(stage,args.hook_session)
        checks['helper_session']=hook['passed']
    result = dict(passed=all(checks.values()), checks=checks, sources=inputs,
                  staged=staged, predictions_sha256=sha(stage / 'predictions.json'),
                  terminal_sha256=staged['TERMINAL.EXE'], runner_sha256=staged['ASPECT.EXE'],
                  run=run, editor=audit,
                  observer_bits=bits,observer_segment=observer_segment,observer_high=args.observer_high,
                  artifacts={str(p.relative_to(ROOT)): sha(p) for p in output.iterdir() if p.is_file()},
                  scope='Actual DOS menu-launched source-built ASPECT sends synthetic local Synchronet credentials; native WAITFOR gates password transmission. INT1C passively rejects launch-error or blocking return prompts; successful connected script resumes parent rendering and unsaved stock-editor checks. No physical modem, full script renderer or whole-application claim.')
    (stage / 'checks.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(passed=result['passed'], checks=checks), indent=2))
    assert result['passed'], 'Script login/editor workflow failed; retained evidence must be inspected'


if __name__ == '__main__':
    if sys.argv[1:2] == ['--observe-driver']:
        observed_driver()
    else:
        main()
