#!/usr/bin/env python3
"""Passively check real DOS error-write/cold-readback evidence and corruptions."""
import argparse
import copy
import json
from pathlib import Path

from enigma_key_stream_fixture import ROOT, sha


def audit(report, readback, final_has_marker):
    baseline = report['classification'] == 'verified data-loss counterexample'
    fault = report['modeled_flush_fault'] == 'partial'
    first, second = report['first'], report['second']
    stops = [e for e in report['events'] if e['id'] == 1 and e['event'] == 'message' and e['value']['type'] == 'stopped']
    early = [e for e in report['events'] if e['id'] == 1 and e['event'] == 'message' and e['value']['type'] == 'error']
    stop = stops[0] if len(stops) == 1 else None
    marker = report['marker'].encode('ascii')
    checks = dict(single_callback_per_run=first['returns'] == second['returns'] == 1,
        slots_and_listeners_released=all(row['slot_released'] and row['input_listeners'] == row['end_listeners'] == 0 for row in (first, second)),
        image_transfer_proven=bool(stop) and stop['parent_has_marker'],
        raw_guest_readback=(marker in readback) == (not baseline),
        final_disk_agrees_with_guest=final_has_marker == (not baseline),
        expected_initial_commit=first['marker_in_disk'] == (not baseline and not fault),
        completion_order=bool(stop) and (first['return_ms'] < stop['ms'] if baseline else first['return_ms'] >= stop['ms']),
        stopped_error_protocol=(bool(early) if baseline else not early and bool(stop) and 'serial input queue is full' in stop['value'].get('error', '')),
        input_identity_stable=report['checks']['inputs_unchanged'],
        both_children_exited=len([e for e in report['events'] if e['event'] == 'exit' and e['value'] == '0']) == 2)
    if baseline or fault:
        checks['old_complete_image_preserved'] = report['initial_disk_sha256'] == report['disk_after_first_sha256']
    if fault:
        checks['IO_failure_reported'] = bool(first['flush_failure']) and any(
            row['msg'] == 'v86 image flush failed' and row.get('imageCommitted') is False
            and 'modeled ENOSPC' in row.get('error', '') for row in report['logs'])
        checks['retained_state_retry_and_cold_readback'] = marker in readback and final_has_marker and not first['marker_in_disk']
    return checks


def run(args):
    assert args.label.replace('-', '').replace('_', '').isalnum()
    folder = ROOT / 'build/bbs-lab/results/enigma' / args.label
    report = json.loads((folder / 'shutdown-checks.json').read_text())
    assert report['passed'] and all(report['checks'].values())
    readback = (folder / 'serial-2.bin').read_bytes()
    final = report['marker'].encode() in (folder / 'probe.img').read_bytes()
    checks = audit(report, readback, final)
    assert all(checks.values()), checks
    cases = []
    def reject(name, current=report, serial=readback, present=final):
        assert not all(audit(current, serial, present).values()), name
        cases.append(dict(case=name, rejected=True))
    changed = copy.deepcopy(report)
    changed['events'] = [e for e in changed['events'] if not (e['id'] == 1 and e['event'] == 'message' and e['value']['type'] == 'stopped')]
    reject('missing-disk-return-event', current=changed)
    changed = copy.deepcopy(report)
    next(e for e in changed['events'] if e['id'] == 1 and e['event'] == 'message' and e['value']['type'] == 'stopped')['parent_has_marker'] = False
    reject('child-never-returned-guest-write', current=changed)
    changed = copy.deepcopy(report)
    changed['first']['returns'] = 2
    reject('duplicate-menu-completion', current=changed)
    changed = copy.deepcopy(report)
    changed['first']['slot_released'] = False
    reject('door-slot-leaked', current=changed)
    changed = copy.deepcopy(report)
    changed['first']['input_listeners'] = 1
    reject('input-listener-leaked', current=changed)
    changed = copy.deepcopy(report)
    changed['checks']['inputs_unchanged'] = False
    reject('mutated-frozen-input', current=changed)
    reject('cold-disk-result-contradiction', present=not final)
    changed = copy.deepcopy(report)
    changed['events'] = [e for e in changed['events'] if e['event'] != 'exit']
    reject('children-not-observed-exiting', current=changed)
    if report['classification'] == 'verified data-loss counterexample':
        reject('counterexample-actually-read-back-write', serial=readback + report['marker'].encode())
        changed = copy.deepcopy(report)
        changed['first']['return_ms'] = max(e['ms'] for e in changed['events']) + 1
        reject('counterexample-did-not-return-early', current=changed)
    else:
        reject('lost-cold-guest-file-readback', serial=readback.replace(report['marker'].encode(), b''))
        changed = copy.deepcopy(report)
        changed['first']['return_ms'] = -1
        reject('completion-before-image-transfer', current=changed)
        changed = copy.deepcopy(report)
        stop = next(e for e in changed['events'] if e['id'] == 1 and e['event'] == 'message' and e['value']['type'] == 'stopped')
        stop['value'].pop('error')
        reject('controlled-error-not-preserved-in-stopped', current=changed)
    if report['modeled_flush_fault']:
        changed = copy.deepcopy(report)
        changed['disk_after_first_sha256'] = 'damaged'
        reject('partial-write-overwrote-previous-image', current=changed)
        changed = copy.deepcopy(report)
        changed['logs'] = [row for row in changed['logs'] if row['msg'] != 'v86 image flush failed']
        reject('failed-flush-not-reported', current=changed)
    result = dict(passed=True, checks=checks, cases=cases, checker_sha256=sha(Path(__file__)),
        captures={name: sha(folder / name) for name in ('shutdown-checks.json', 'serial-1.bin', 'serial-2.bin', 'probe.img')},
        scope='Passive real VM file-write, controlled overflow, image transfer, completion ordering and cold readback. Modeled partial syscall fault explicit; no game replies, physical or power-cut claim.')
    (folder / 'shutdown-audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(args.label, ':', len(cases), 'corruptions rejected')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label', required=True)
    run(parser.parse_args())
