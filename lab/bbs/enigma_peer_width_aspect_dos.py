#!/usr/bin/env python3
"""Real BBS width requests during a source-built ASPECT process, with a passive observer."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys

from enigma_peer_width_fixture import ROOT, PORT, owned, pid, verify
from product_inputs import select_product

sys.path.insert(0, str(ROOT / 'standalone'))
from test_directory_key_bindings_dos import actions
sys.path.insert(0, str(ROOT / 'src/aspect'))
from compiler import compile_source


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source():
    text = 'proc main\nfopen 4 "D:\\WIDE.LOG" "wb"\nfputs 4 "START|"\npause 2\n'
    for key, mark in [('WIDTH^M', '0'), ('^[[C', '1'), ('^[[D', '2'), ('n', '3'), ('w', '4')]:
        text += ('transmit "' + key + '"\nwaitfor "LOCWIDE" 12\nif waitfor\nfputs 4 "' + mark +
                 '|"\nelse\nfputs 4 "FAIL|"\nfclose 4\nexit\nendif\nwaitquiet 1 5\n')
    text += ('transmit "q"\nwaitfor "Main Menu" 12\nif waitfor\nfputs 4 "RETURN|"\n'
             'else\nfputs 4 "FAILRETURN|"\nendif\nfclose 4\nendproc\n')
    return text


def observer(binary, output):
    listing = (binary.parent / 'terminal.map').read_text()
    symbols = {n: (int(s, 16), int(o, 16)) for s, o, n in re.findall(
        r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$', listing, re.M | re.I)}
    dg = int(re.search(r'^DGROUP\s+([0-9a-f]+):', listing, re.M | re.I)[1], 16)
    data = 'screen_columns screen_attribute_row_bytes screen_attributes_base screen_attribute_cells terminal_aspect_active terminal_parser_active terminal_ansi_wait_active terminal_program_active'.split()
    defines = {n.upper(): symbols[n][0] * 16 + symbols[n][1] - dg * 16 for n in data}
    defines['PROGRAM_ACTIVE'] = defines.pop('TERMINAL_PROGRAM_ACTIVE')
    defines['DGROUP_REL'] = dg
    defines['LIVE_CODE_REL'] = symbols['terminal_native_width_far'][0]
    for n in ['reset_live_active', 'reset_bank_busy']:
        assert symbols[n][0] == defines['LIVE_CODE_REL']
        defines[n.upper()] = symbols[n][1]
    lease = ['render_attached', 'resident_bridge_busy', 'terminal_script_overlay_visible']
    assert len({symbols[n][0] for n in lease}) == 1
    defines['ASPECT_CODE_REL'] = symbols[lease[0]][0]
    defines.update({n.upper(): symbols[n][1] for n in lease})
    (output / 'bbs_width_offsets.inc').write_text(''.join(f'%define {n} {v}\n' for n, v in defines.items()))
    subprocess.run(['nasm', '-fbin', '-I' + str(output) + '/',
                    str(ROOT / 'lab/bbs/peer_width_aspect_watch.asm'), '-o', str(output / 'BWATCH.COM')], check=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate', type=Path, required=True)
    p.add_argument('--terminal', type=Path, required=True)
    p.add_argument('--runner', type=Path, required=True)
    p.add_argument('--compiler', type=Path)
    p.add_argument('--window', action='store_true')
    p.add_argument('--packet-delay-ms', type=int, choices=range(101), default=0)
    p.add_argument('--label', required=True)
    a = p.parse_args()
    assert re.fullmatch(r'[A-Za-z0-9_-]+', a.label)
    candidate = owned(a.candidate)
    verify(candidate)
    assert pid(candidate)
    binary, inputs = select_product(a.terminal, 'TERMINAL.EXE')
    runner, runner_sources = select_product(a.runner, 'ASPECT.EXE')
    inputs += runner_sources + [binary, runner]
    output = ROOT / 'build/bbs-lab/results/enigma' / a.label
    wrapper = output.with_name(a.label + '-wrapper')
    output.mkdir(exist_ok=False)
    wrapper.mkdir(exist_ok=False)
    parent = wrapper / 'parent'
    parent.mkdir()
    for original in [binary, runner]:
        shutil.copyfile(original, parent / original.name)
    asp = source()
    expected_asx = compile_source(asp)
    if a.compiler:
        compiler, compiler_sources = select_product(a.compiler, 'ASPCOMP.EXE')
        inputs += compiler_sources + [compiler]
        shutil.copyfile(compiler, parent / compiler.name)
        (output / 'WIDE.ASP').write_text(asp, encoding='ascii')
    else:
        (output / 'WIDE.ASX').write_bytes(expected_asx)
    key = wrapper / 'BIND.KEY'
    key.write_bytes(actions(b'D:\\WIDE.ASP' if a.compiler else b'D:\\WIDE.ASX', 0))
    observer(binary, output)
    event_file = candidate / 'logs/peer-width.jsonl'
    event_offset = event_file.stat().st_size if event_file.exists() else 0
    server_log = candidate / 'logs/enigma-bbs.log'
    log_offset = server_log.stat().st_size
    inputs += [candidate / 'peer-width-instance.json', candidate / 'mods/pcplus_width/pcplus_width.js',
               candidate / 'config/config.hjson', candidate / 'config/menus/loc-main.hjson']
    inputs += [ROOT / 'lab/bbs' / n for n in ['enigma_peer_width_aspect_dos.py', 'peer_width_aspect_watch.asm',
               'enigma_peer_width_fixture.py', 'peer_width_module.js', 'test_dos.py', 'editor_dos_probe.py',
               'modem.py', 'editor-recipes.json', 'product_inputs.py']]
    inputs += [ROOT / 'standalone/test_directory_key_bindings_dos.py', ROOT / 'src/aspect/compiler.py', key,
               output / 'BWATCH.COM', output / 'bbs_width_offsets.inc']
    canonical = json.loads((ROOT / 'lab/bbs/editor-recipes.json').read_text())['enigma_unsaved']['keyboard_input']
    login = canonical[:canonical.index('M enter')]
    keys = 'p500 enter ' + login + 'a-1 ' + ('p600 a-z ' if a.window else '') + 'p23000 F enter p3000'
    command = [sys.executable, 'lab/bbs/editor_dos_probe.py', str(parent / 'TERMINAL.EXE'), 'enigma',
               '--port', str(PORT), '--server-log', str(server_log), '--label', a.label, '--keys', keys,
               '--wait', '1', '--timeout', '180', '--com', '2', '--baud', '19200', '--flow', 'HARD',
               '--dial-fixture', '--cpu', '8086', '--irq', '5', '--mouse-scales', '8', '4',
               '--meta-fixture', str(key), '--packet-delay-ms', str(a.packet_delay_ms)]
    (wrapper / 'command.json').write_text(json.dumps(command, indent=2) + '\n')
    # The maintained adapter runs SNAP, then the read-only observer before the
    # unchanged terminal. Both sampler invocations and restoration checks remain.
    adapter = (ROOT / 'lab/bbs/editor_dos_probe.py').read_text()
    harness_path = ROOT / 'lab/bbs/test_dos.py'
    original = harness_path.read_text()
    assert original.count('D:\\\\SNAP B\n') == 1
    patched = original.replace('D:\\\\SNAP B\n', 'D:\\\\SNAP B\nD:\\\\BWATCH\n')
    entry = wrapper / 'entry.py'
    # Read interception is scoped to this one source file in the harness process;
    # no application instruction, byte stream or helper return is patched.
    entry.write_text('import sys\nfrom pathlib import Path\n' +
        'sys.path.insert(0,' + repr(str(ROOT / 'lab/bbs')) + ')\n' +
        '_read=Path.read_text\n_target=Path(' + repr(str(harness_path)) + ')\n' +
        '_source=' + repr(patched) + '\n' +
        'def read(self,*a,**k):\n return _source if self==_target else _read(self,*a,**k)\n' +
        'Path.read_text=read\n' +
        'exec(compile(' + repr(adapter) + ',' + repr(str(ROOT / 'lab/bbs/editor_dos_probe.py')) +
        ',"exec"),{"__file__":' + repr(str(ROOT / 'lab/bbs/editor_dos_probe.py')) + ',"__name__":"__main__"})\n')
    invocation = [sys.executable, str(entry), *command[2:]]
    (wrapper / 'invocation.json').write_text(json.dumps(invocation, indent=2) + '\n')
    inputs += [entry, binary.parent / 'terminal.map', *parent.glob('*'),
               output / ('WIDE.ASP' if a.compiler else 'WIDE.ASX')]
    before = {str(f.relative_to(ROOT)): sha(f) for f in inputs}
    with (wrapper / 'harness.log').open('w') as log:
        code = subprocess.call(invocation, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
    events_raw = event_file.read_bytes()[event_offset:] if event_file.exists() else b''
    (wrapper / 'peer-width.jsonl').write_bytes(events_raw)
    events = [json.loads(line) for line in events_raw.splitlines()]
    server_raw = server_log.read_bytes()[log_offset:]
    (wrapper / 'server-session.jsonl').write_bytes(server_raw)
    logs = [json.loads(line) for line in server_raw.splitlines()]
    raw = (output / 'BBSOBS.BIN').read_bytes() if (output / 'BBSOBS.BIN').exists() else b''
    state = struct.unpack('<21H', raw) if len(raw) == 42 else ()
    result = json.loads((output / 'result.json').read_text()) if (output / 'result.json').exists() else {}
    marker = (output / 'WIDE.LOG').read_bytes() if (output / 'WIDE.LOG').exists() else b''
    checks = dict(harness=code == 0 and result.get('passed', False),
                  script_progress=marker == b'START|0|1|2|3|4|RETURN|',
                  exact_ASX=(output / 'WIDE.ASX').exists() and (output / 'WIDE.ASX').read_bytes() == expected_asx,
                  authenticated=any(e['kind'] == 'enter' and e['user'] == 'loclab' for e in events),
                  widths=[(e['width'], e['selection']) for e in events if e['kind'] == 'paint'] == [(132, 0), (132, 1), (132, 0), (80, 0), (132, 0)],
                  actual_server_CPR=[e['args'] for e in events if e['kind'] == 'cpr'] == [[2, 128]] * 3 + [[2, 80], [2, 128]],
                  observed_ASPECT=bool(state) and state[0:2] == (0x4257, 1) and state[2] == state[3] != 0 and state[9] > 0 and state[10] > 0,
                  observed_window=bool(state) and (state[11] > 0) == a.window,
                  child_return=bool(state) and state[4:6] == (1, 0) and state[6] == state[7] != 0,
                  root_return=bool(state) and state[8] == 0 and state[12:] == (80, 0, 0, 0, 0, 0, 0, 0, 1),
                  manual_file_menu=any(e.get('menuName') == 'fileBaseMainMenu' for e in logs),
                  immutable_inputs=before == {str(f.relative_to(ROOT)): sha(f) for f in inputs})
    verify(candidate)
    report = dict(passed=all(checks.values()), checks=checks, inputs=before, state=state, marker=marker.decode('ascii', errors='replace'),
                  binary_sha256=sha(binary), runner_sha256=sha(runner), window=a.window,
                  source_compilation=bool(a.compiler), modem_packet_delay_ms=a.packet_delay_ms,
                  script=asp, artifacts={str(f.relative_to(ROOT)): sha(f) for f in [*output.glob('*'), *wrapper.glob('*'), *parent.glob('*')] if f.is_file()},
                  scope='Authenticated synthetic ENiGMA width menu during genuine DOS ASPECT execution; passive DOS observer; subsequent manual File Base navigation. Explicit selected stock/buffered or decoder candidate, not physical or full application acceptance.')
    (wrapper / 'checks.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(passed=report['passed'], checks=checks, state=state, marker=report['marker']), indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
