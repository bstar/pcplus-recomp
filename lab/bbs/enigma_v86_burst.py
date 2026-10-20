#!/usr/bin/env python3
"""Actual BRE name burst and normal return through an explicit bridge candidate."""
import argparse
import json
from pathlib import Path
import time

from enigma_key_stream_fixture import ROOT, PORT, owned, sha
from enigma_v86_fixture import state
from enigma_concurrent_upload import Peer, Lab
from enigma_notes_dos import messages
import synchronet


def run(args):
    candidate = owned(args.candidate)
    assert args.label.replace('-', '').replace('_', '').isalnum()
    meta = json.loads((candidate / 'v86-door-instance.json').read_text())
    assert meta['input_bridge']
    inputs = {name: candidate / name for name in meta['fixture_inputs']}
    inputs.update({f'dependency/{name}': candidate / 'node_modules' / name for name in meta['dependency_inputs']})
    inputs.update(runner=Path(__file__), peer=ROOT / 'lab/bbs/enigma_concurrent_upload.py',
        telnet=ROOT / 'lab/bbs/synchronet.py')
    for name, digest in meta['fixture_inputs'].items():
        assert sha(candidate / name) == digest
    for name, digest in meta['dependency_inputs'].items():
        assert sha(candidate / 'node_modules' / name) == digest
    before = {name: sha(path) for name, path in inputs.items()}
    out = ROOT / 'build/bbs-lab/results/enigma' / args.label
    out.mkdir(parents=True, exist_ok=False)
    synchronet.PORT = PORT
    lab = Lab(candidate, out)
    phases = []
    count = messages(candidate)
    trace = candidate / 'v86-input-trace.jsonl'
    if 'input_trace' in meta:
        assert not trace.exists(), 'Fresh observation trace required'
    try:
        with Peer('loclab') as peer:
            lab.peers = [peer]
            lab.login(peer, 'LoC-Lab-2026!')
            lab.go(peer, b'D\r', 'doorsMainMenu')
            lab.go(peer, b'2\r', 'locBarrenRealms')
            def wait_text(token, start, seconds=20):
                lab.wait(lambda: token in Peer.cleaned(peer.history[start:]), token, seconds)
            wait_text('Name your Realm:', 0)
            def command(data, prompt, label):
                at, wire = len(peer.history), len(peer.tx)
                peer.application(data, label)
                wait_text(prompt, at)
                phases.append(dict(label=label, sent=data.hex(), wire_at=wire,
                    received_at=at, received_end=len(peer.history), prompt=prompt))
            command(b'LoC Lab\r', 'Name Your Empire LoC Lab?', 'one burst name')
            command(b'Y', 'Instructions?', 'confirm name hotkey')
            command(b'N', 'Paused', 'decline instructions hotkey')
            command(b'\r', '[Barren Realms Elite]', 'title pause')
            at = len(peer.history)
            peer.application(b'0\r', 'quit game')
            lab.wait(lambda: lab.menu(peer) == 'doorsMainMenu' and any(
                row.get('name') == 'LoC-bre' and row.get('msg') == 'v86 emulator stopped'
                for row in lab.rows(peer)), 'normal worker stop and Doors return', 25)
            wait_text('Returning to LoSs oF CoNtRoL', at)
            acknowledged = 0
            def doors_ready():
                nonlocal acknowledged
                visible = Peer.cleaned(peer.history[at:])
                pause = '>> smash your keyboard <<'
                if visible.rfind('[ LoC ]') > visible.rfind(pause):
                    return True
                amount = visible.count(pause)
                if amount > acknowledged:
                    assert 'ACHIEVEMENT' in visible
                    acknowledged = amount
                    peer.application(b'\r', 'acknowledge achievement')
                return False
            lab.wait(doors_ready, 'Doors prompt after achievement interrupts')
            lab.go(peer, b'Q\r', 'mainMenu')
            lab.pause(.5)
            lifecycle = [row['msg'] for row in lab.rows(peer) if row.get('name') == 'LoC-bre'
                and row.get('msg') in ('v86 emulator ready', 'v86 emulator stopped')]
            checks = dict(name_confirmation_in_response_to_exact_burst=phases[0]['sent'] == b'LoC Lab\r'.hex(),
                complete_route=len(phases) == 4 and lab.menu(peer) == 'mainMenu',
                normal_worker_lifecycle=lifecycle == ['v86 emulator ready', 'v86 emulator stopped'],
                no_disconnect_shutdown=not any('disconnected' in row.get('msg', '').lower()
                    and 'v86' in row['msg'].lower() for row in lab.rows(peer)),
                no_worker_errors=not any('v86' in row.get('msg', '').lower() and
                    any(word in row['msg'].lower() for word in ('error', 'non-zero')) for row in lab.rows(peer)))
    finally:
        lab.save()
    checks.update(inputs_unchanged=before == {name: sha(path) for name, path in inputs.items()},
        original_images_unchanged=all(state(args.server_root / name) == value for name, value in meta['source_images'].items()),
        no_post_saved=count == messages(candidate))
    if 'input_trace' in meta:
        trace_rows = [json.loads(line) for line in trace.read_text().splitlines()]
        (out / 'uart-trace.jsonl').write_bytes(trace.read_bytes())
        received = [row['value'] for row in trace_rows if row['event'] == 'receive-before']
        read = [row['value'] for row in trace_rows if row['event'] == 'guest-read']
        checks['UART_never_contains_more_than_one_byte'] = max(row['length'] for row in trace_rows) <= 1
        checks['all_received_bytes_consumed_exactly'] = received == read and received[:8] == list(b'LoC Lab\r')
    result = dict(passed=all(checks.values()), checks=checks, phases=phases,
        input_hashes=before, source_images=meta['source_images'],
        scope='Declared loopback reference peer, actual owned BRE/v86 and private image. Exact burst name then real game normal return. Instrumentation explicit when present; not DOS or physical-modem acceptance.')
    (out / 'v86-burst-checks.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(passed=result['passed'], checks=checks), indent=2))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--server-root', type=Path, required=True)
    parser.add_argument('--label', required=True)
    raise SystemExit(run(parser.parse_args()))
