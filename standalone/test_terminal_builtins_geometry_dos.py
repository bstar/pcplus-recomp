#!/usr/bin/env python3
"""Full-parent DOS terminal getters across physical rows and logical wide/status views.

Reuses the GET product harness without removing or weakening its assertions.
Only fixture definitions and each case's synthetic PRM physical-row preference
are adapted; cursor changes execute through real peer parser and MESSAGE output.
"""
import argparse
import hashlib
import inspect
import json
from pathlib import Path
import sys

import test_aspect_get_vm_dos as base

ROOT = base.ROOT


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def guard(expression, label):
    return 'if '+expression+'\ntransmit "BAD'+label+'"\nendif\n'


def definitions():
    template = ORIGINAL_DEFINITIONS()[0]
    rows = []
    for physical in (25, 28, 43, 50):
        for hidden in (0, 1):
            logical = physical-(not hidden)
            geometry = '$scrncols!=80 || $scrnrows!='+str(physical)
            attributes = '$termbold!=47 || $termdim!=63 || $termnorm!=7 || $termrev!=112 || $termuline!=1'
            triggers = [('BOTTOMREADY', [(0.25, '\x1b[99;1H\x1b[6nGEOBOTTOM:')])]
            source = ('string value\nproc main\nwaitfor "LOGIN:" 5\nset msg_crlf off\n'
                      +guard(geometry+' || '+attributes, 'GEOMETRY')
                      +guard('$col!=21 || $row!=0', 'INITIAL')
                      +'message "AB"\n'
                      +guard('$col!=23 || $row!=0 || '+geometry, 'FRESHLOCAL')
                      +'transmit "BOTTOMREADY"\nwaitfor "GEOBOTTOM:" 5\n'
                      +guard('$col!=10 || $row!='+str(logical-1)+' || '+geometry, 'BOTTOM')
                      +'transmit "GEOBOTTOM"\n')
            if physical == 25:
                triggers += [('WIDEREADY', [(0.25, '\x1b[?3h\x1b[3;116HWIDE:')]) ,
                             ('WIDEBOTTOMREADY', [(0.25, '\x1b[99;127HWEND:')])]
                source += ('transmit "WIDEREADY"\nwaitfor "WIDE:" 5\n'
                           +guard('$col!=120 || $row!=2 || '+geometry, 'WIDE')
                           +'message "ABCDE"\n'
                           +guard('$col!=125 || $row!=2 || '+geometry, 'FRESH')
                           +'transmit "WIDEBOTTOMREADY"\nwaitfor "WEND:" 5\n'
                           +guard('$col!=131 || $row!='+str(logical-1)+' || '+geometry, 'WIDEBOTTOM')
                           +'transmit "GEOWIDE"\n')
            triggers += [('RESTOREREADY', [(0.25, ('\x1b[?3l' if physical == 25 else '')
                                           +'\x1b[2J\x1b[HFIRST BYTE SAFELOGIN:')])]
            source += 'transmit "RESTOREREADY"\nwaitfor "LOGIN:" 5\n'
            source += (guard('$col!=21 || $row!=0 || '+geometry+' || '+attributes, 'RESTORE')
                       +'transmit "GEORESTORE"\ntransmit "GETREADY"\nget value 10\n'
                       +guard('$col!=26 || $row!=0 || '+geometry, 'AFTERGET')
                       +'transmit value\ntransmit "^M"\ntransmit $D_PWORD\ntransmit "^M"\npause 1\nendproc\n')
            rows.append(dict(template, name='geometry-'+str(physical)+'-'+('hidden' if hidden else 'shown'),
                             source=source, direct_GET=True, physical_rows=physical,
                             logical_rows=logical, policy_status_hidden=hidden,
                             peer_triggers=triggers))
    return rows


ORIGINAL_DEFINITIONS = base.definitions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('parent-dir', 'child-dir', 'compiler-dir', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT/'build') and not out.exists()
    parent = args.parent_dir.resolve()
    child = args.child_dir.resolve()
    compiler = args.compiler_dir.resolve()
    pm = json.loads((parent/'manifest.json').read_text())
    cm = json.loads((child/'manifest.json').read_text())
    assert pm['experimental_terminal_query'] and pm['experimental_aspect_row_owner']
    assert cm['experimental_terminal_builtins']
    fixtures = definitions()
    base.definitions = lambda: fixtures
    source = inspect.getsource(base.main)
    needle = "  if active_case[0] is not None and 'policy_status_hidden' in active_case[0]:"
    assert source.count(needle) == 1
    source = source.replace(needle,
                            "  if active_case[0] is not None:\n   struct.pack_into('<H',data,0x1ca,active_case[0]['physical_rows'])\n"+needle)
    # This adds only the per-case physical PRM preference. Existing setup,
    # observer, compiler comparison, parent return and full check set stay live.
    adapted_sha = hashlib.sha256(source.encode()).hexdigest()
    exec(compile(source, base.__file__, 'exec'), base.__dict__)
    sys.argv = [sys.argv[0], '--parent-dir', str(parent), '--child-dir', str(child),
                '--get-compiler-dir', str(compiler), '--output', str(out), '--cpu', '8086']
    status = base.main()
    report = json.loads((out/'checks.json').read_text())
    for case in report['cases']:
        fixture = next(r for r in fixtures if r['name'] == case['case'])
        wire = (out/case['case']/'serial.bin').read_bytes()
        checks = case['checks']
        checks.update(
            no_geometry_guard_failed=b'BAD' not in wire,
            logical_bottom_and_physical_height_proved=wire.count(b'GEOBOTTOM') == 1,
            cursor_and_attributes_restored=wire.count(b'GEORESTORE') == 1,
            wide_full_word_cursor_proved=wire.count(b'GEOWIDE') == int(fixture['physical_rows'] == 25),
            exact_probe_order=(wire.find(b'GEOBOTTOM') < wire.find(b'GEORESTORE') < wire.find(b'GETREADY')),
            exact_peer_logical_bottom_report=('\x1b['+str(fixture['logical_rows'])+';1R').encode() in wire,
        )
        case.update(physical_rows=fixture['physical_rows'], logical_rows=fixture['logical_rows'],
                    status_hidden=fixture['policy_status_hidden'],
                    wide_cursor_cases=fixture['physical_rows'] == 25,
                    passed=all(checks.values()))
        (out/case['case']/'result.json').write_text(json.dumps(case, indent=2)+'\n')
    dependencies = [Path(__file__).resolve(), Path(base.__file__), ROOT/'standalone/test_aspect_renderer_dos.py',
                    ROOT/'standalone/test_connection_dos.py', ROOT/'standalone/directory_fixtures.py',
                    ROOT/'standalone/modem_fixtures.py', ROOT/'standalone/terminal_config_fixtures.py']
    report.update(passed=status == 0 and all(c['passed'] for c in report['cases']),
                  geometry_builtins=True, physical_rows=[25, 28, 43, 50],
                  adapted_harness_source_sha256=adapted_sha,
                  checker_sha256=sha(__file__),
                  sources={str(p.relative_to(ROOT)): sha(p) for p in dependencies},
                  scope=__doc__+' Eight product executions at25/28/43/50 physical rows with shown/hidden status; actual DOS/Python compiler agreement, live getter queries at peer-parser bottom-row clamps and after local MESSAGE, wide logical132 cursor120/125/131 retaining physical80columns at25rows, and GET/parent/keyboard return. Peer responses and expected CPR are fixed before execution. Synthetic PRM fixtures, BIOS/UART and owned modem peer; not physical hardware, BBS, concurrent mutation or arbitrary terminal/ASPECT parity.')
    (out/'result.json').write_text(json.dumps(report, indent=2)+'\n')
    print('TERMINAL_GEOMETRY', len(report['cases']), 'cases', report['passed'])
    assert report['passed']


if __name__ == '__main__':
    main()
