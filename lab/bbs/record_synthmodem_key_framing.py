#!/usr/bin/env python3
"""Record scoped key-framing evidence without promoting failed runtime gates."""
import argparse
import json
from pathlib import Path
from synthmodem_vm_control import ROOT, sha


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cohort', type=Path, required=True)
    p.add_argument('--staging', type=Path, required=True)
    p.add_argument('--receipt', type=Path, default=ROOT/'docs/validation/synthmodem-key-framing.json')
    a = p.parse_args(); cohort = a.cohort.resolve(); staging = a.staging.resolve()
    assert all(n.is_relative_to(ROOT/'build') for n in (cohort, staging))
    target = a.receipt.resolve(); assert target.is_relative_to(ROOT/'docs/validation')
    read = lambda n: json.loads(n.read_text())
    runtime = read(staging/'result.json')
    unit = read(staging/'checks.json'); loopback = read(staging/'loopback.json')
    actual = read(cohort/'result.json'); audit = read(cohort/'independent-audit.json')
    caller = read(cohort/'offline-caller.json')
    integrity = read(cohort/'integrity-diagnosis.json')
    stopped = read(cohort/'test-stop.json') if (cohort/'test-stop.json').is_file() else None
    assert runtime['passed'] and unit['passed'] and loopback['passed']
    assert actual['input_sequence_timeout_ms'] == 250
    assert actual['route'] == 'editor'
    assert sha(cohort/'result.json') == audit['producer_sha256']
    assert sha(cohort/'rtp-from-caller.bin') == caller['capture_sha256']
    assert all(sha(ROOT/n) == h for n, h in runtime['frozen_inputs'].items())
    assert all(sha(staging/'runtime'/n) == h for n, h in runtime['files'].items())
    serial = (cohort/'serial-in.bin').read_bytes(); assert serial.startswith(b'ATZ\rATD1\r')
    decoded = b''.join(bytes.fromhex(row['hex']) for row in caller['received'])
    actual.pop('DOS_screen', None)
    names = [cohort/n for n in ('result.json', 'independent-audit.json', 'offline-caller.json', 'integrity-diagnosis.json')]
    if stopped is not None: names.append(cohort/'test-stop.json')
    names += [staging/n for n in ('result.json', 'checks.json', 'loopback.json')]
    names += [ROOT/'lab/bbs/patches/synthmodem-key-framing/check_loopback.js', Path(__file__).resolve()]
    checks = {'component_checks': unit['passed'], 'real_TCP_comparison': loopback['passed'],
              'actual_DOS_producer': actual['passed'], 'actual_DOS_independent_audit': audit['passed'],
              'offline_caller_matches_all_DOS_bytes': decoded == serial[9:]}
    pcm = guest = None
    if runtime.get('receive_trace'):
        assert actual['key_framing_trace']
        pcm = read(cohort/'PCM-analysis.json'); guest = read(cohort/'offline-guest.json')
        assert all(sha(cohort/n) == h for n, h in pcm['frozen_inputs'].items())
        assert sha(cohort/'modem_rx_8k.raw') == guest['capture_sha256']
        checks.update(trace_export_complete=actual['gateway']['receiveTrace']['exported'],
                      offline_guest_matches_all_DOS_bytes=guest['equals_authored_upstream'],
                      guest_PCM_equals_delayed_RTP_prefix=pcm['sample_alignment']['guest_PCM_equals_delayed_RTP_prefix'])
        names += [cohort/'PCM-analysis.json', cohort/'offline-guest.json']
    result = {'passed': all(checks.values()), 'checks': checks,
              'editor_semantic_checks_passed': all(audit['checks'][n] for n in
                  ['all_actual_BIOS_editor_keys_in_order','Home_changes_cursor_before_H',
                   'End_and_Delete_apply_to_draft','Insert_changes_to_overtype',
                   'Tab_advances_and_page_keys_preserve_boundary','CtrlY_clears_line_before_final_text',
                   'unsaved_final_line_visible','draft_never_saved']),
              'open_gateway_errors': actual['gateway']['errors'],
              'cohort': str(cohort.relative_to(ROOT)), 'staging': str(staging.relative_to(ROOT)),
              'component': unit, 'loopback': loopback, 'actual_DOS': actual,
              'independent_audit': audit, 'offline_caller': caller,
              'integrity_diagnosis': integrity, 'explicit_test_stop': stopped,
              'PCM_analysis': pcm, 'offline_guest': guest,
              'editor_result_classification': 'not_reached' if not actual['checks']['editor_entered'] else 'entered_inspect_semantic_gates',
              'evidence_sha256': {str(n.relative_to(ROOT)): sha(n) for n in names},
              'limitations': ['The serial-output recorder represents frontend send attempts. Screen snapshots validate the pre-close DOS editor state; DSP output during diagnostic export after serial-close is not proof DOS received those later bytes.',
                              'One-line page keys exercise document boundaries, not multiline scrolling. No post is saved and no file transfer is attempted.',
                              'A clean traced call does not fix the preserved normal-image byte-insertion failures. Complete editor/reset/receive acceptance remains separate.'],
              'scope': 'Opt-in250ms bridge key framing on the carrier image (with existing diagnostic PCM export only when declared), actual local stock ENiGMA one-line editor recipe, loopback byte readback and independent captures. PCM identity covers its recorded overlap, not the longer RTP export/shutdown tail. A scoped pass does not guarantee arbitrary remote TCP chunking, physical hardware, transfers, other rates or complete application functionality. Earlier receive-corruption failures remain unresolved.'}
    target.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'passed': result['passed'], 'checks': checks, 'receipt': str(target)}, indent=2))


if __name__ == '__main__': main()
