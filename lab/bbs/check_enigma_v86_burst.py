#!/usr/bin/env python3
"""Audit actual UART stall evidence and repaired reference-route captures."""
import argparse
import copy
import json
from pathlib import Path

from enigma_key_stream_fixture import ROOT, owned, sha
from enigma_concurrent_upload import Peer
from enigma_infocom_probe import ordered


def baseline_checks(rows):
    received = [r for r in rows if r['event'] == 'receive-before']
    reads = [r for r in rows if r['event'] == 'guest-read']
    return dict(entire_name_received=[r['value'] for r in received[:8]] == list(b'LoC Lab\r'),
        one_synchronous_burst=len(received) >= 8 and len({r['ic'] for r in received[:8]}) == 1,
        only_first_byte_consumed=len(reads) == 1 and reads[0]['value'] == 76,
        pending_bytes_and_asserted_receive_irq=bool(reads) and reads[0]['length'] == 7
            and reads[0]['queue'] == list(b'oC Lab\r') and reads[0]['iir'] == 4
            and reads[0]['ier'] & 1 == 1 and reads[0]['fifo'] == 0,
        later_input_finds_guest_still_running_with_same_pending_bytes=len(received) == 9 and bool(reads)
            and received[-1]['ms'] > reads[0]['ms'] and received[-1]['ic'] != reads[0]['ic']
            and received[-1]['queue'] == list(b'oC Lab\r') and received[-1]['iir'] == 4)


def route_checks(report, display, wire, rows, trace):
    auth = [r for r in rows if r.get('msg') == 'User "loclab" successfully logged in']
    own = [r for r in rows if len(auth) == 1 and r.get('sessionId') == auth[0].get('sessionId')]
    lifecycle = [r['msg'] for r in own if r.get('name') == 'LoC-bre'
        and r.get('msg') in ('v86 emulator ready', 'v86 emulator stopped')]
    phases = report['phases']
    expected = [(b'LoC Lab\r', 'Name Your Empire LoC Lab?'), (b'Y', 'Instructions?'),
                (b'N', 'Paused'), (b'\r', '[Barren Realms Elite]')]
    valid_phases = len(phases) == len(expected)
    for phase, (data, prompt) in zip(phases, expected):
        at, end, tx = phase['received_at'], phase['received_end'], phase['wire_at']
        valid_phases &= (phase['sent'] == data.hex() and phase['prompt'] == prompt
            and 0 <= tx <= len(wire)-len(data) and wire[tx:tx+len(data)] == data
            and 0 <= at < end <= len(display) and prompt in Peer.cleaned(display[at:end]))
    menus = '\n'.join(r['menuName'] for r in own if r.get('menuName'))
    result = dict(unique_authentication=len(auth) == 1, all_phase_inputs_and_actual_responses=valid_phases,
        quit_and_main_inputs=ordered(wire, [b'LoC Lab\r', b'Y', b'N', b'\r', b'0\r', b'Q\r']) is not None,
        menu_route=ordered(menus, ['mainMenu', 'doorsMainMenu', 'locBarrenRealms', 'doorsMainMenu', 'mainMenu']) is not None,
        normal_worker_lifecycle=lifecycle == ['v86 emulator ready', 'v86 emulator stopped'],
        no_worker_error_or_disconnect=not any('v86' in r.get('msg', '').lower()
            and any(t in r['msg'].lower() for t in ('error', 'non-zero', 'disconnected')) for r in rows))
    if trace is not None:
        received = [r['value'] for r in trace if r['event'] == 'receive-before']
        read = [r['value'] for r in trace if r['event'] == 'guest-read']
        result.update(one_byte_UART_window=bool(trace) and max(r['length'] for r in trace) <= 1,
            exact_consumption=received == read and received[:8] == list(b'LoC Lab\r'))
    return result


def run(args):
    for label in (args.label, args.baseline_label):
        assert label.replace('-', '').replace('_', '').isalnum()
    folder = ROOT / 'build/bbs-lab/results/enigma' / args.label
    baseline_folder = ROOT / 'build/bbs-lab/results/enigma' / args.baseline_label
    baseline = owned(args.baseline_candidate) / 'v86-input-trace.jsonl'
    baseline_rows = [json.loads(line) for line in baseline.read_text().splitlines()]
    before = baseline_checks(baseline_rows)
    baseline_report = json.loads((baseline_folder / 'characterization.json').read_text())
    baseline_events = json.loads((baseline_folder / 'loclab/events.json').read_text())
    before['declared_exact_name_burst_and_followup'] = [e['hex'] for e in baseline_events
        if e.get('label') == 'reference door input'] == [b'LoC Lab\r'.hex(), b'\r'.hex()]
    before['frozen_baseline_inputs_and_original_images'] = baseline_report['inputs_unchanged'] and baseline_report['source_images_unchanged']
    assert all(before.values()), before
    report = json.loads((folder / 'v86-burst-checks.json').read_text())
    assert report['passed'] and all(report['checks'].values())
    display = (folder / 'loclab/display.bin').read_bytes()
    wire = (folder / 'loclab/client-wire.bin').read_bytes()
    events = json.loads((folder / 'loclab/events.json').read_text())
    assert len([e for e in events if e.get('label') == 'one burst name' and e['hex'] == b'LoC Lab\r'.hex()]) == 1
    rows = [json.loads(line) for line in (folder / 'server-session.jsonl').read_text().splitlines()]
    trace_path = folder / 'uart-trace.jsonl'
    trace = [json.loads(line) for line in trace_path.read_text().splitlines()] if trace_path.exists() else None
    checks = route_checks(report, display, wire, rows, trace)
    assert all(checks.values()), checks
    cases = []
    def reject(name, current=report, text=display, sent=wire, logs=rows, uart=trace):
        assert not all(route_checks(current, text, sent, logs, uart).values()), name
        cases.append(dict(case=name, rejected=True))
    reject('missing-confirmation', text=display.replace(b'Name Your Empire', b'X' * len(b'Name Your Empire')))
    reject('missing-name-byte', sent=wire.replace(b'LoC Lab\r', b'LoX Lab\r'))
    reject('missing-quit', sent=wire.replace(b'0\r', b'X\r'))
    reject('missing-main-input', sent=wire.replace(b'Q\r', b'X\r'))
    reject('missing-worker-stop', logs=[r for r in rows if r.get('msg') != 'v86 emulator stopped'])
    reject('worker-error', logs=rows + [dict(msg='v86 worker error')])
    reject('disconnect-shutdown', logs=rows + [dict(msg='Client disconnected — stopping v86 worker')])
    reject('missing-authentication', logs=[r for r in rows if r.get('msg') != 'User "loclab" successfully logged in'])
    changed = copy.deepcopy(report)
    changed['phases'][0]['received_end'] = changed['phases'][0]['received_at']
    reject('empty-name-response-range', current=changed)
    changed = copy.deepcopy(report)
    changed['phases'][0]['wire_at'] += 1
    reject('incorrect-wire-offset', current=changed)
    if trace is not None:
        reject('missing-guest-read', uart=[r for r in trace if r['event'] != 'guest-read'])
        changed = copy.deepcopy(trace)
        changed[-1]['length'] = 2
        reject('multiple-bytes-in-guest-UART', uart=changed)
    for name, altered in [
        ('counterexample-with-no-read', [r for r in baseline_rows if r['event'] != 'guest-read']),
        ('counterexample-with-no-name', [r for r in baseline_rows if r['event'] != 'receive-before']),
        ('counterexample-with-no-followup', [r for r in baseline_rows if r['ms'] < baseline_rows[-1]['ms']]),
    ]:
        assert not all(baseline_checks(altered).values()), name
        cases.append(dict(case=name, rejected=True))
    captures = [folder / name for name in ('v86-burst-checks.json', 'loclab/display.bin',
        'loclab/client-wire.bin', 'loclab/events.json', 'server-session.jsonl')]
    if trace_path.exists(): captures.append(trace_path)
    captures += [baseline, baseline_folder / 'characterization.json', baseline_folder / 'loclab/events.json']
    result = dict(passed=True, checks=checks, baseline_checks=before, cases=cases,
        captures={str(p.relative_to(ROOT)): sha(p) for p in captures}, checker_sha256=sha(Path(__file__)),
        scope='Passive actual UART stall and repaired reference route evidence; no synthetic game replies or DOS claim.')
    (folder / 'v86-burst-audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print('Burst audit:', len(cases), 'corruptions rejected; UART counterexample verified')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label', required=True)
    parser.add_argument('--baseline-label', required=True)
    parser.add_argument('--baseline-candidate', type=Path, required=True)
    run(parser.parse_args())
