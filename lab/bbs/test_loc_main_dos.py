#!/usr/bin/env python3
"""Authenticate against copied LoC main module, return from menus and type.

Actual DOS/staged proxy/owned stock-core fixture, not the live board or hardware.
"""
import argparse
import fcntl
import json
import re
import subprocess
import sys
import time
from pathlib import Path

from product_inputs import ROOT, select_product, sha
from enigma_loc_menu_fixture import verify
from enigma_key_stream_fixture import owned, pid
from enigma_peer_width_fixture import PORT
from terminal_geometry import terminal_geometry


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate', type=Path, required=True)
    p.add_argument('--runtime', type=Path, required=True)
    p.add_argument('--terminal', type=Path, required=True)
    p.add_argument('--label', required=True)
    p.add_argument('--rows', type=int, choices=[25,28,43,50], default=25)
    p.add_argument('--hidden', type=int, choices=[0,1], default=0)
    a = p.parse_args()
    assert re.fullmatch('[A-Za-z0-9_-]+', a.label)
    candidate = owned(a.candidate)
    assert pid(candidate)
    verify(candidate)
    lock = (candidate / '.loc-menu-dos.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    binary, sources = select_product(a.terminal, 'TERMINAL.EXE')
    geometry = terminal_geometry(binary)
    layout = dict(physical_rows=a.rows, logical_rows=a.rows-(not a.hidden), status_hidden=a.hidden)
    names = ['lab/bbs/test_loc_main_dos.py', 'lab/bbs/enigma_loc_menu_fixture.py',
             'lab/bbs/enigma_peer_width_fixture.py', 'lab/bbs/synthmodem_proxy_serial.js',
             'lab/bbs/test_dos.py', 'lab/bbs/editor_dos_probe.py', 'lab/bbs/modem.py',
             'lab/bbs/editor-recipes.json', 'standalone/reference_watch.asm',
             'standalone/display_startup_geometry.asm', 'reconstruction/command_reference/provenance.json']
    sources += [ROOT / name for name in names]
    meta = json.loads((candidate / 'loc-menu-instance.json').read_text())
    sources += [candidate / name for name in meta['fixture_inputs']]
    sources += [candidate / 'loc-menu-instance.json', candidate / 'peer-width-instance.json']
    frozen = {str(path.relative_to(ROOT)): sha(path) for path in sources}
    base = ROOT / 'build/bbs-lab'
    out, bridge = base / 'results/enigma' / a.label, base / (a.label+'-proxy')
    assert not out.exists() and not bridge.exists()
    out.mkdir(parents=True)
    observer = out / 'REFWATCH.COM'
    subprocess.run(['nasm', '-fbin', str(ROOT / 'standalone/reference_watch.asm'), '-o', str(observer)], check=True)
    server_log = candidate / 'logs/enigma-bbs.log'
    offset = server_log.stat().st_size
    proc = subprocess.Popen(['node', str(ROOT / 'lab/bbs/synthmodem_proxy_serial.js'),
        '--runtime', str(a.runtime.resolve()), '--output', str(bridge), '--bbs-port', str(PORT),
        '--framing-ms', '250', '--byte-delay-ms', '20', '--terminal-rows', str(layout['logical_rows']),
        '--probe-terminal-size', '--screen-reference', '--freeze-trigger', 'LOCSNAP'],
        stdout=subprocess.DEVNULL, stderr=(out/'bridge-errors.log').open('w'), text=True)
    try:
        deadline = time.monotonic()+10
        while not (bridge/'ready.json').exists():
            assert proc.poll() is None and time.monotonic()<deadline
            time.sleep(.05)
        ready = json.loads((bridge/'ready.json').read_text())
        recipe = json.loads((ROOT/'lab/bbs/editor-recipes.json').read_text())['enigma_unsaved']['keyboard_input']
        prefix = recipe[:recipe.index('M enter')]
        keys = 'p900 enter p2500 l o c enter '+prefix
        # Native Alt-Z must be observed, then the actual stock message menu and
        # return precede a live typed command-field marker (no Enter afterward).
        keys += 'a-z p900 escape p700 M enter p3500 Q enter p3500 L O C S N A P p2500 a-x'
        command = [sys.executable, str(ROOT/'lab/bbs/editor_dos_probe.py'), str(binary), 'enigma',
            '--port', str(ready['endpoint']['port']), '--server-log', str(server_log), '--label', a.label,
            '--com', '3', '--baud', '19200', '--flow', 'HARD', '--dial-fixture', '--irq', '5',
            '--mouse-scales', '8', '4', '--cpu', '8086', '--timeout', '160', '--wait', '2',
            '--raw-upstream', '--keys', keys, '--display-rows', str(a.rows), '--status-hidden', str(a.hidden),
            '--video-observer', str(observer)]
        with (out/'harness.log').open('w') as log:
            code = subprocess.run(command, cwd=ROOT, stdout=log, stderr=log, timeout=175).returncode
        base_result = json.loads((out/'result.json').read_text())
        rows = [json.loads(line) for line in server_log.read_bytes()[offset:].splitlines()]
        sessions = {r['sessionId'] for r in rows if r.get('msg') == 'User "loclab" successfully logged in'}
        assert len(sessions)==1, sessions
        session = sessions.pop()
        rows = [r for r in rows if r.get('sessionId')==session]
        (out/'server-session.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
        menus = [r['menuName'] for r in rows if r.get('menuName')]
        proof = json.loads((bridge/'1-screen-reference.json').read_text())
        native = (out/'REFVIEW.BIN').read_bytes()
        labels = json.loads((ROOT/'reconstruction/command_reference/provenance.json').read_text())['labels']
        screen = (out/'SCREEN.BIN').read_bytes()
        checks = dict(harness=code==0 and base_result['passed'], authenticated=True,
            actual_reference_observed=len(native)==12006 and native[:2]==b'FR' and int.from_bytes(native[2:4],'little')&1!=0,
            all_native_labels=all(r['name'].encode() in native[6:4006:2] for r in labels),
            message_menu_entered='messageBaseMainMenu' in menus,
            returned_to_custom_main=menus.count('mainMenu')>=2 and menus[-1]=='mainMenu',
            no_post_saved=not any('posted message to' in r.get('msg','') for r in rows),
            typed_field_visible=b'LOCSNAP' in screen[:layout['logical_rows']*160:2],
            real_CPR_boundary=proof['armed'] and proof['frozen'] and proof['reply'] is not None and proof['probeReplyConsumed'],
            source_unchanged=all(sha(ROOT/name)==digest for name,digest in frozen.items()))
        verify(candidate)
        result = dict(passed=all(checks.values()), checks=checks, server='ENiGMA',
            binary_sha256=sha(binary), screen_sha256=sha(out/'SCREEN.BIN'), terminal_geometry=geometry,
            display_layout=layout, screen_reference=proof, product_inputs=frozen, bridge=ready,
            command=command, fixture=str(candidate.relative_to(ROOT)), menus=menus,
            scope=__doc__+' Authenticated synthetic account, real Alt-Z passive witness, M/Q menu return and typed field before real CPR freeze. Selected custom module/form/layout with stock-core M/F/G subset only; no whole live-board assertion.')
        (out/'proxy-integration.json').write_text(json.dumps(result, indent=2)+'\n')
        print(a.label, 'PASS' if result['passed'] else [k for k,v in checks.items() if not v], flush=True)
        assert result['passed']
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill(); proc.wait()


if __name__ == '__main__':
    main()
