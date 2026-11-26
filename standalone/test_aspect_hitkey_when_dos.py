#!/usr/bin/env python3
"""Full-parent DOS HITKEY reads in post-GET deferred plain/framed WHEN CALL.

The unchanged GET harness retains every original check and wire expectation.
The CALL is staged during GET; its worker runs after the synchronous field
retires. An extra BIOS Up word remains after Enter for two non-consuming reads.
This does not establish script execution inside a live GET field owner.
"""
import argparse
import hashlib
import inspect
import json
from pathlib import Path
import sys

import test_aspect_get_vm_dos as base

ROOT = base.ROOT
ORIGINAL_WHEN_DEFINITIONS = base.when_definitions


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def definitions():
    rows = ORIGINAL_WHEN_DEFINITIONS()
    for row in rows:
        source = row['source']
        assert source.count('integer hits\n') == 1
        assert source.count('transmit "GETREADY"\n') == 1
        assert source.count('hits=hits+1\n') == 1
        source = source.replace('integer hits\n', 'integer hits,observed0,observed1\n', 1)
        source = source.replace('transmit "GETREADY"\n', 'set keys on\ntransmit "GETREADY"\n', 1)
        source = source.replace('hits=hits+1\n',
            'observed0=hitkey\nobserved1=hitkey\n'
            'if observed0!=18432 || observed1!=18432\ntransmit "BADHITKEYDEFERRED"\nendif\n'
            'hits=hits+1\n', 1)
        assert source.count('=hitkey\n') == 2
        row.update(source=source, HITKEY_deferred_WHEN=True,
                   field_BIOS_words=row['field_BIOS_words']+[0x4800])
    assert len(rows) == 2 and all(r['when_action'] and r['direct_GET'] for r in rows)
    return rows


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('parent-dir', 'child-dir', 'compiler-dir', 'output'):
        p.add_argument('--'+name, type=Path, required=True)
    a = p.parse_args()
    parent, child, compiler, out = (getattr(a, n).resolve()
        for n in ('parent_dir', 'child_dir', 'compiler_dir', 'output'))
    assert out.is_relative_to(ROOT/'build') and not out.exists()
    pm, cm = (json.loads((n/'manifest.json').read_text()) for n in (parent, child))
    assert pm['experimental_hitkey_parent'] and cm['experimental_hitkey']
    fixtures = definitions()
    base.when_definitions = lambda: fixtures
    source = inspect.getsource(base.main)
    harness_sha = hashlib.sha256(source.encode()).hexdigest()
    sys.argv = [sys.argv[0], '--parent-dir', str(parent), '--child-dir', str(child),
                '--get-compiler-dir', str(compiler), '--output', str(out),
                '--cpu', '8086', '--when-cases']
    status = base.main()
    report = json.loads((out/'checks.json').read_text())
    assert len(report['cases']) == 2 and report['when_cases']
    for case in report['cases']:
        folder = out/case['case']
        fixture = next(r for r in fixtures if r['name'] == case['case'])
        wire = (folder/'serial.bin').read_bytes()
        observer = (folder/'observer.asm').read_text()
        checks = case['checks']
        checks.update(
            worker_completed_two_retained_word_HITKEY_reads=(wire.count(b'WORKER') == 1
                and b'BADHITKEYDEFERRED' not in wire and b'BAD' not in wire),
            HITKEY_worker_guard_precedes_completion=(fixture['source'].index('observed0=hitkey\n')
                < fixture['source'].index('observed1=hitkey\n')
                < fixture['source'].index('if observed0!=18432 || observed1!=18432\n')
                < fixture['source'].index('hits=hits+1\n')),
            native_KEYSON_before_GET_and_WHEN=(fixture['source'].index('set keys on\n')
                < fixture['source'].index('transmit "GETREADY"\n')),
            GET_parked_before_WHEN_and_input=(case['GET_waiting_before_WHEN'] == 1
                and case['GET_pending_WHEN_gate'] == 1),
            exact_inline_worker_and_field_wire=(b'GETREADYINLINEWORKERLoC42\rSynth42\r' in wire),
            original_CALL_staged_input_gate_retained=(' cmp word [cs:get_when_waiting],1\n'
                ' jne .done\n mov [cs:get_when_gate],ax\n' in observer),
            Up_word_follows_field_Enter=(fixture['field_BIOS_words'][-2:] == [0x1c0d, 0x4800]),
        )
        case.update(HITKEY_deferred_WHEN=True, HITKEY_expected_words=[0x4800, 0x4800],
                    live_GET_modal_script_execution_verified=False,
                    passed=all(checks.values()))
        (folder/'result.json').write_text(json.dumps(case, indent=2)+'\n')
    dependencies = [Path(__file__).resolve(), Path(base.__file__),
        ROOT/'standalone/test_aspect_renderer_dos.py', ROOT/'standalone/test_connection_dos.py',
        ROOT/'standalone/directory_fixtures.py', ROOT/'standalone/modem_fixtures.py',
        ROOT/'standalone/terminal_config_fixtures.py']
    report.update(passed=status == 0 and all(c['passed'] for c in report['cases']),
        HITKEY_deferred_WHEN=True, HITKEY_reads=4,
        unchanged_harness_source_sha256=harness_sha, checker_sha256=sha(__file__),
        live_GET_modal_script_execution_verified=False,
        sources={str(p.relative_to(ROOT)): sha(p) for p in dependencies},
        scope=__doc__+' Two actual8086 DOS executions with host/DOS compiler equality, '
        'native KEYS ON keyboard-disable, GET-field-before-WHEN observation, plain and framed '
        'deferred CALL workers and two HITKEY reads before incrementing global hits[0]. The '
        'unchanged observer injects the field text, Enter and Up only after CALL is staged; '
        'both worker observations must retain the same18432 BIOS word. The synchronous GET '
        'loop retires before the dispatcher executes the worker. Original INLINE/WORKER/'
        'edited-field/password/parent-return checks remain required. Execution of script '
        'operands inside a live modal GET field remains unproven/currently deferred; controlled '
        'parent/C-client modal-owner tests are separate. Synthetic PRM, owned modem peer and '
        'emulated BIOS/UART; no hardware, live BBS, arbitrary interrupts or full ASPECT claim.')
    (out/'result.json').write_text(json.dumps(report, indent=2)+'\n')
    print('HITKEY_DEFERRED_WHEN_GET', len(report['cases']), 'cases', report['passed'])
    assert report['passed']


if __name__ == '__main__':
    main()
