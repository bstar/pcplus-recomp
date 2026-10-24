#!/usr/bin/env python3
"""Synchronet width requests during a genuine source-built ASPECT process."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys

from synchronet_peer_width_fixture import ROOT, PORT, owned, pid
from synchronet_aspect_width_fixture import verify
from enigma_peer_width_aspect_dos import observer, source as enigma_source
from product_inputs import select_product

sys.path.insert(0, str(ROOT / 'standalone'))
from test_directory_key_bindings_dos import actions
sys.path.insert(0, str(ROOT / 'src/aspect'))
from compiler import compile_source


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source():
    script = enigma_source().replace('WIDTH^M', 'A')
    return script.replace('waitfor "Main Menu" 12',
        'waitfor "Hit a key" 12\nif waitfor\ntransmit " "\nelse\n'
        'fputs 4 "FAILPAUSE|"\nfclose 4\nexit\nendif\nwaitfor "Main" 12')


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
    output = ROOT / 'build/bbs-lab/results/synchronet' / a.label
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
    event_file = candidate / 'data/peer-width.jsonl'
    event_offset = event_file.stat().st_size if event_file.exists() else 0
    server_log = candidate / 'instance.log'
    log_offset = server_log.stat().st_size
    metadata = json.loads((candidate / 'peer-width-instance.json').read_text())
    inputs += [candidate / 'peer-width-instance.json']
    inputs += [candidate / n for n in metadata['fixture_inputs']]
    inputs += [ROOT / n for n in metadata['composition_sources']]
    inputs += [ROOT / 'lab/bbs' / n for n in ['synchronet_aspect_width_dos.py', 'peer_width_aspect_watch.asm',
               'synchronet_peer_width_fixture.py', 'enigma_peer_width_aspect_dos.py', 'test_dos.py', 'editor_dos_probe.py',
               'modem.py', 'editor-recipes.json', 'product_inputs.py']]
    inputs += [ROOT / 'standalone/test_directory_key_bindings_dos.py', ROOT / 'src/aspect/compiler.py', key,
               output / 'BWATCH.COM', output / 'bbs_width_offsets.inc']
    login = ('p13000 L A B U S E R enter p2000 L A B P A S S 4 2 enter '
             'p8000 space p3000 Q enter p5000 space p4000 ')
    keys = 'p500 enter ' + login + 'a-1 ' + ('p600 a-z ' if a.window else '') + 'p23000 T p3000'
    command = [sys.executable, 'lab/bbs/editor_dos_probe.py', str(parent / 'TERMINAL.EXE'), 'synchronet',
               '--port', str(PORT), '--label', a.label, '--keys', keys,
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
    (wrapper / 'server-session.log').write_bytes(server_raw)
    raw = (output / 'BBSOBS.BIN').read_bytes() if (output / 'BBSOBS.BIN').exists() else b''
    state = struct.unpack('<21H', raw) if len(raw) == 42 else ()
    result = json.loads((output / 'result.json').read_text()) if (output / 'result.json').exists() else {}
    marker = (output / 'WIDE.LOG').read_bytes() if (output / 'WIDE.LOG').exists() else b''
    checks = dict(harness=code == 0 and result.get('passed', False),
                  script_progress=marker == b'START|0|1|2|3|4|RETURN|',
                  exact_ASX=(output / 'WIDE.ASX').exists() and (output / 'WIDE.ASX').read_bytes() == expected_asx,
                  authenticated=any(e['kind'] == 'enter' and e['user'] == 'LABUSER' for e in events),
                  widths=[(e['width'], e['selection']) for e in events if e['kind'] == 'paint'] == [(132, 0), (132, 1), (132, 0), (80, 0), (132, 0)],
                  actual_server_CPR=[e['position'] for e in events if e['kind'] == 'cpr'] == [dict(x=128, y=2)] * 3 + [dict(x=80, y=2), dict(x=128, y=2)],
                  started_by_child=any(e['kind'] == 'start' and e['key'] == 'A' for e in events),
                  observed_ASPECT=bool(state) and state[0:2] == (0x4257, 1) and state[2] == state[3] != 0 and state[9] > 0 and state[10] > 0,
                  observed_window=bool(state) and (state[11] > 0) == a.window,
                  child_return=bool(state) and state[4:6] == (1, 0) and state[6] == state[7] != 0,
                  root_return=bool(state) and state[8] == 0 and state[12:] == (80, 0, 0, 0, 0, 0, 0, 0, 1),
                  manual_file_menu=str(candidate / 'text/menu/transfer.').encode() in server_raw,
                  final_file_prompt=(output / 'screen.txt').exists() and '■ File ■' in (output / 'screen.txt').read_text(),
                  immutable_inputs=before == {str(f.relative_to(ROOT)): sha(f) for f in inputs})
    verify(candidate)
    report = dict(passed=all(checks.values()), checks=checks, inputs=before, state=state, marker=marker.decode('ascii', errors='replace'),
                  binary_sha256=sha(binary), runner_sha256=sha(runner), window=a.window,
                  source_compilation=bool(a.compiler), modem_packet_delay_ms=a.packet_delay_ms,
                  script=asp, artifacts={str(f.relative_to(ROOT)): sha(f) for f in [*output.glob('*'), *wrapper.glob('*'), *parent.glob('*')] if f.is_file()},
                  scope='Authenticated private Synchronet runtime and delayed-start synthetic width shell during genuine DOS ASPECT execution; passive DOS observer; native server cursor/key parsing; subsequent manual stock File Transfer navigation. Not physical or full application acceptance.')
    (wrapper / 'checks.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(passed=report['passed'], checks=checks, state=state, marker=report['marker']), indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
