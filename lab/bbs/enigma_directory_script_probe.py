#!/usr/bin/env python3
"""Audit directory-bound ASPECT login and an unsaved stock ENiGMA editor.

Only the owned loopback account is used. The child sends credentials; keyboard
input starts after login. An explicit optional ENiGMA keymap is audited separately
from the default keymap. Immediate byte forwarding remains enabled.
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
from observer_layout import compact_watcher


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
    fixture_code = """
def bound_directory(**options):
    data = bytearray(directory_image(**options))
    start = 250 + (options['entry'] - 1) * 114
    data[start+52:start+61] = b'LOGON\\0\\0\\0\\0'
    return bytes(data)
"""
    fixture = ("assert text.count('async def run(args):') == 1\n"
               "text = text.replace('directory_fixture=directory_image(', 'directory_fixture=bound_directory(')\n"
               + 'text = text.replace("async def run(args):", ' + repr(fixture_code + '\nasync def run(args):') + ')\n')
    prelude = (f'assert text.count({before!r}) == text.count({after!r}) == 1\n'
               f'text = text.replace({before!r}, {install!r}).replace({after!r}, {collect!r})\n')
    if observer_high:
        prelude += "assert text.count('[mixer]\\nnosound=true') == 1\ntext = text.replace('[mixer]\\nnosound=true', '[dos]\\numb=true\\n[mixer]\\nnosound=true')\n"
    exec(compile(adapter.replace(marker, fixture + prelude + marker), str(path), 'exec'),
         {'__file__': str(path), '__name__': '__main__'})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label', required=True)
    parser.add_argument('--hook-session',choices=['accept','reject'],help='Exercise live kind2 helper returns before editing')
    parser.add_argument('--source', action='store_true', help='Compile LOGON.ASP in the actual DOS child')
    parser.add_argument('--observer-high',action='store_true',help='Require the passive observer to reside in DOS upper memory')
    parser.add_argument('--compact-observer',action='store_true',help='Retain pattern/tick checks with no resident screen-copy buffer')
    parser.add_argument('--profile', choices=['network', 'enigma-editor'], default='network')
    parser.add_argument('--packet-delay-ms', type=int, choices=range(101), default=0)
    parser.add_argument('--terminal', type=Path, default=ROOT/'build/terminal/TERMINAL.EXE')
    parser.add_argument('--runner', type=Path, default=ROOT/'build/aspect-runner/ASPECT.EXE')
    parser.add_argument('--mouse-scales', type=int, nargs=2)
    parser.add_argument('--irq', type=int, choices=[3,4,5,7])
    parser.add_argument('--cpu', choices=['8086','286','386','486'], default='386')
    args = parser.parse_args()
    assert not (args.observer_high and args.compact_observer)
    assert args.label and all(c.isalnum() or c in '-_' for c in args.label)
    output = ROOT / 'build/bbs-lab/results/enigma' / args.label
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
    if args.compact_observer:watch=compact_watcher(watch)
    (stage / 'watch.asm').write_text(watch)
    subprocess.run(['nasm', '-f', 'bin', str(stage / 'watch.asm'), '-o', str(stage / 'SCRIPT.COM')], check=True)
    for product, leaf in [(terminal, 'TERMINAL.EXE'), (runner, 'ASPECT.EXE')]:
        shutil.copyfile(product, stage / leaf)
    # Both fields are painted before focus is installed. WAITQUIET drains the
    # complete form and terminal probes before transmitting either field.
    # The native directory password field holds only ten characters; this
    # owned test account has twelve, so its password is explicit script data.
    source = 'proc main\r\nwaitfor "lOGIN" 25\r\nif waitfor\r\ntransmit "^M"\r\nwaitfor "PASSW_" 10\r\nif waitfor\r\nwaitquiet 1 10\r\ntransmit "loclab^M"\r\nwaitquiet 1 10\r\ntransmit "LoC-Lab-2026!^M"\r\nmessage "LOGIN SENT"\r\nelse\r\nmessage "PASSWORD FORM NOT RECEIVED"\r\nendif\r\nelse\r\nmessage "LOGIN MATRIX NOT RECEIVED"\r\nendif\r\nendproc\r\n'
    (stage / 'LOGON.ASP').write_bytes(source.encode('ascii'))
    if args.source:
        shutil.copyfile(ROOT/'build/aspect-compiler-dos/ASPCOMP.EXE',stage/'ASPCOMP.EXE')
    else:
        (stage / 'LOGON.ASX').write_bytes(compile_source(source))
    hook_sources=hook_session_probe.prepare(stage,terminal,args.hook_session) if args.hook_session else []
    recipe_path = ROOT / 'lab/bbs/editor-recipes.json'
    original = json.loads(recipe_path.read_text())['enigma_unsaved']['keyboard_input']
    login = 'p12000 enter p7000 l o c l a b enter p2500 L o C - L a b - 2 0 2 6 ! enter p11000 '
    assert original.startswith(login)
    keys = 'p33000 ' + original[len(login):]
    assert 'loclab' not in keys.replace(' ', '')
    assert 'LoC-Lab-2026!' not in keys.replace(' ', '')
    assert 'enter' not in keys[keys.index('A B C D E'):].split()
    if args.hook_session:keys=hook_session_probe.schedule(keys)
    sources = hook_sources + [ROOT/'lab/bbs/hook_session_probe.py', Path(__file__), recipe_path, ROOT / 'src/aspect/compiler.py']
    sources += terminal_sources + runner_sources + [ROOT/'lab/bbs/observer_layout.py']
    sources += [ROOT / 'standalone' / leaf for leaf in
                ('test_script_launch_dos.py', 'command_menu_watch.asm')]
    sources += [ROOT / 'lab/bbs' / leaf for leaf in
                ('editor_dos_probe.py', 'test_dos.py', 'modem.py', 'check_editor_dos.py')]
    sources += [ROOT / 'standalone/directory_fixtures.py', ROOT / 'standalone/directory_test_support.py']
    inputs = {str(p.relative_to(ROOT)): sha(p) for p in sources}
    staged = {p.name: sha(p) for p in stage.iterdir() if p.is_file()}
    server = ROOT / 'build/bbs-lab/enigma/source'
    server_commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=server, text=True).strip()
    assert server_commit == '6c25317168b762f7d9088a54d3f8295438827a0e'
    server_sources = {}
    for leaf in ('core/client.js', 'core/multi_line_edit_text_view.js'):
        original_bytes = subprocess.check_output(['git', 'show', 'HEAD:' + leaf], cwd=server)
        assert (server / leaf).read_bytes() == original_bytes, 'Stock server input/editor required'
        server_sources[leaf] = sha(server / leaf)
    keymap = ROOT / 'build/keyboard-profiles' / ('ENIGMA.KBD' if args.profile == 'enigma-editor' else 'NETWORK.KBD')
    assert keymap.is_file(), 'Build keyboard-profiles first'
    sources.append(keymap)
    inputs[str(keymap.relative_to(ROOT))] = sha(keymap)
    command = [sys.executable, str(Path(__file__)), '--observe-driver',
               str(stage / 'TERMINAL.EXE'), 'enigma', '--port', '23233',
               '--label', args.label, '--com', '2', '--baud', '19200', '--flow', 'HARD',
               '--directory-fixture', '--entry', '3', '--keymap-fixture', str(keymap),
               '--packet-delay-ms', str(args.packet_delay_ms), '--timeout', '170', '--wait', '2', '--keys', keys]
    if args.hook_session:command += ['--meta-fixture',str(stage/'ACTIONS.KEY')]
    if args.observer_high:command += ['--observer-high']
    command += ['--cpu', args.cpu]
    if args.irq is not None:command += ['--irq',str(args.irq)]
    if args.mouse_scales:
        command += ['--mouse-scales', *map(str, args.mouse_scales)]
    # Freeze the inputs, schedule and expected credential boundary before DOS.
    (stage / 'predictions.json').write_text(json.dumps(dict(
        sources=inputs, staged=staged, command=command,
        server_commit=server_commit, server_sources=server_sources,
        expected_login_wire_hex=b'loclab\rLoC-Lab-2026!\r'.hex(),
        compile_in_DOS=args.source,expected_ASX_sha256=hashlib.sha256(compile_source(source)).hexdigest(),
        expected_editor_passed=True), indent=2) + '\n')
    with (stage / 'harness.log').open('w') as log:
        code = subprocess.call(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
    assert (output / 'result.json').exists(), 'No completed DOS report; preserve harness.log'
    with (stage / 'audit.log').open('w') as log:
        audit_code = subprocess.call([sys.executable, str(ROOT / 'lab/bbs/check_editor_dos.py'),
                                     'enigma', '--label', args.label, '--disconnect-unsaved', '--keyboard-profile', args.profile], cwd=ROOT,
                                    stdout=log, stderr=subprocess.STDOUT)
    run = json.loads((output / 'result.json').read_text())
    audit = json.loads((output / 'semantic-audit.json').read_text())
    codec = Telnet()
    wire, _ = codec.feed((output / 'bbs-sent.bin').read_bytes())
    display = (output / 'display.bin').read_bytes()
    prefix = wire.split(b'loclab', 1)[0] if b'loclab' in wire else wire
    observed = (output / 'SCRIPT.BIN').read_bytes() if (output / 'SCRIPT.BIN').exists() else b''
    magic, bits, ticks, observer_segment = struct.unpack('<4H', observed[:8]) if len(observed) == (8 if args.compact_observer else 4008) else (0, 0, 0, 0)
    checks = dict(
        DOS_harness=code == 0 and run['passed'],
        current_terminal=run['binary_sha256'] == staged['TERMINAL.EXE'] == sha(terminal),
        current_runner=staged['ASPECT.EXE'] == sha(runner),
        source_compilation=(not args.source or (stage/'LOGON.ASX').read_bytes()==compile_source(source)),
        inputs_unchanged=inputs == {str(p.relative_to(ROOT)): sha(p) for p in sources}
                         and all(sha(stage / leaf) == digest for leaf, digest in staged.items()),
        stock_server_unchanged=server_sources == {leaf: sha(server / leaf) for leaf in server_sources},
        credentials_not_in_keyboard=run['keyboard_input'] == keys
                                   and 'LoC-Lab-2026!' not in keys.replace(' ', ''),
        script_credentials_once=wire.count(b'loclab\r') == wire.count(b'LoC-Lab-2026!\r') == 1
                               and b'loclab\rLoC-Lab-2026!\r' in wire,
        no_other_login_text_before_script=all(c in b'\x1b[?;0123456789cR\r' for c in prefix),
        authenticated_server_log=any(json.loads(row).get('msg') == 'User \"loclab\" successfully logged in' for row in (output / 'server-session.jsonl').read_text().splitlines()),
        no_error_or_blocking_return_prompt=magic == 0x4d43 and ticks > 0 and (bits & 6) == 0,
        observer_placement=not args.observer_high or observer_segment>=0xa000,
        resumed_parent_editor=audit_code == 0 and audit['passed'],
        no_post_saved=audit['checks']['no_post_saved'],
    )
    if args.hook_session:
        hook=hook_session_probe.inspect(stage,args.hook_session)
        checks['helper_session']=hook['passed']
    result = dict(keyboard_profile=args.profile, modem_packet_delay_ms=args.packet_delay_ms,
                  server_commit=server_commit, server_sources=server_sources,
                  passed=all(checks.values()), checks=checks, sources=inputs,
                  staged=staged, predictions_sha256=sha(stage / 'predictions.json'),
                  terminal_sha256=staged['TERMINAL.EXE'], runner_sha256=staged['ASPECT.EXE'],
                  run=run, editor=audit,
                  observer_bits=bits,observer_segment=observer_segment,observer_high=args.observer_high,observer_compact=args.compact_observer,
                  artifacts={str(p.relative_to(ROOT)): sha(p) for p in output.iterdir() if p.is_file()},
                  scope='Actual DOS directory-bound script sends only synthetic local ENiGMA credentials after native prompt and quiet waits. Passive INT1C observer checks launcher errors. Stock editor checks use the explicitly recorded modem buffering delay and keyboard profile. Disconnect leaves the draft unsaved. Buffered experiments do not replace immediate-forwarding failures. No physical modem or full application claim.')
    (stage / 'checks.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(passed=result['passed'], checks=checks), indent=2))
    assert result['passed'], 'Script login/editor workflow failed; retained evidence must be inspected'


if __name__ == '__main__':
    if sys.argv[1:2] == ['--observe-driver']:
        observed_driver()
    else:
        main()
