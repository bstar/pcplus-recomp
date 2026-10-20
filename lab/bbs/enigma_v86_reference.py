#!/usr/bin/env python3
"""Characterize real owned DOS doors with a declared loopback reference peer.

Interactive commands are test-terminal input; :wait N only receives output,
:paced TEXT sends characters 200ms apart, and :close disconnects. No acceptance
or DOS-client assertion is inferred here.
"""
import argparse
import contextlib
import json
from pathlib import Path

from enigma_key_stream_fixture import ROOT, PORT, owned, sha
from enigma_v86_fixture import state
from enigma_concurrent_upload import Peer, Lab
import synchronet


def run(args):
    candidate = owned(args.candidate)
    assert args.label.replace('-', '').replace('_', '').isalnum()
    fixture = json.loads((candidate / 'v86-door-instance.json').read_text())
    for name, digest in fixture['fixture_inputs'].items():
        assert sha(candidate / name) == digest
    for name, digest in fixture['dependency_inputs'].items():
        assert sha(candidate / 'node_modules' / name) == digest
    out = ROOT / 'build/bbs-lab/results/enigma' / args.label
    out.mkdir(parents=True, exist_ok=False)
    synchronet.PORT = PORT
    lab = Lab(candidate, out)
    inputs = {name: candidate / name for name in fixture['fixture_inputs']}
    inputs.update(runner=Path(__file__), peer=ROOT / 'lab/bbs/enigma_concurrent_upload.py',
                  telnet=ROOT / 'lab/bbs/synchronet.py')
    before = {name: sha(path) for name, path in inputs.items()}
    steps = []
    try:
        with Peer('loclab') as peer:
            lab.peers = [peer]
            lab.login(peer, 'LoC-Lab-2026!')
            lab.go(peer, b'D\r', 'doorsMainMenu')
            lab.go(peer, b'1\r' if args.game == 'gwar' else b'2\r',
                   'locGlobalWar' if args.game == 'gwar' else 'locBarrenRealms')
            at = len(peer.history)
            lab.pause(12)
            print(Peer.cleaned(peer.history[at:])[-5000:], flush=True)
            while True:
                try:
                    command = input('REFERENCE> ')
                except EOFError:
                    break
                if command == ':close':
                    break
                at = len(peer.history)
                if command.startswith(':wait '):
                    delay = float(command[6:])
                    assert 0 < delay <= 30
                    lab.pause(delay)
                elif command.startswith(':paced '):
                    for byte in command[7:].encode('ascii') + b'\r':
                        peer.application(bytes([byte]), 'declared paced reference input')
                        lab.pause(.2)
                    lab.pause(2)
                else:
                    peer.application(command.encode('ascii') + b'\r', 'reference door input')
                    lab.pause(2)
                text = Peer.cleaned(peer.history[at:])
                steps.append(dict(command=command, menu=lab.menu(peer), received=len(peer.history)-at))
                print(text[-5000:], flush=True)
    finally:
        lab.save()
        images = {name: state(candidate / name) for name in fixture['initial_images']}
        report = dict(classification='reference characterization', game=args.game, steps=steps,
            inputs_unchanged=before == {name: sha(path) for name, path in inputs.items()}, input_hashes=before,
            source_images_unchanged=all(state(args.server_root / name) == value for name, value in fixture['source_images'].items()),
            clone_images=images, scope='Declared reference Telnet/ANSI peer into actual owned door/worker and private image clones. No DOS-client or normal-return acceptance inferred.')
        (out / 'characterization.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--server-root', type=Path, required=True)
    parser.add_argument('--label', required=True)
    parser.add_argument('--game', choices=['gwar', 'bre'], required=True)
    run(parser.parse_args())
