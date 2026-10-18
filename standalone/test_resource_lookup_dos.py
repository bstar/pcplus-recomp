#!/usr/bin/env python3
"""Actual DOS environment inheritance, XLT precedence and startup rejection."""
import hashlib
import json
from pathlib import Path
import shutil
from check_directory_live import word
from modem_fixtures import fixture
from test_connection_dos import run, ROOT, BINARY


def main():
    mapping = bytearray(range(256));mapping[ord('Q')] = 27;mapping[ord('x')] = ord('y')
    other = bytearray(mapping);other[ord('x')] = ord('z')
    banner = b'Q[2JQ[HFIRST BYTE SAFEQ[6nQ[0cQ[2;1HxQ[6n'
    deep = '/'.join(['A1234567', 'B1234567', 'C1234567', 'D1234567', 'E1234567', 'F123'])
    assert len('D:\\'+deep.replace('/', '\\')+'\\PCPLUS.XLT') == 63
    cases = []

    def case(name, *, files=None, directory='D:\\CFG', expected=0, explicit=None, mode=1, mapped=True):
        name = 'resource-xlt-'+name
        folder = ROOT/'build/connection-dos'/name
        if folder.exists():
            shutil.rmtree(folder)
        arguments = '@D:\\TEST.PRM' + (' /D:CaseTest:23' if not expected else '')
        if explicit:
            arguments += ' /X:'+explicit
        result = run(name, 'reject' if expected else 'success', 'p2500 a-x' if not expected else 'p500 a-x',
                     expected=expected, prm=word(fixture(), 0x1e0, mode), working_drive='d',
                     arguments=arguments, files=files, banner=banner if mapped else None,
                     environment={'PCPLUS': directory})
        if not expected and mapped:
            screen = (folder/'SCREEN.BIN').read_bytes()
            result['checks']['selected_table_maps_x_to_y'] = screen[160:162] == b'y\x07'
            result['passed'] = all(result['checks'].values())
            (folder/'result.json').write_text(json.dumps(result, indent=2)+'\n')
        assert result['passed'], result
        cases.append(result)

    case('environment-directory', files={'CFG/PCPLUS.XLT': bytes(mapping)})
    case('environment-trailing-separator', directory='D:\\CFG\\', files={'CFG/PCPLUS.XLT': bytes(mapping)})
    case('current-wins', files={'PCPLUS.XLT': bytes(mapping), 'CFG/PCPLUS.XLT': bytes(other)})
    case('current-ignores-invalid-environment', directory='A'*64, files={'PCPLUS.XLT': bytes(mapping)})
    case('explicit-ignores-invalid-environment', directory='A'*64, explicit='D:\\EXPLICIT.XLT',
         files={'EXPLICIT.XLT': bytes(mapping), 'PCPLUS.XLT': bytes(other)})
    case('identity-ignores-environment', directory='A'*64, mode=0, mapped=False)
    case('damaged-current-no-fallback', files={'PCPLUS.XLT': b'', 'CFG/PCPLUS.XLT': bytes(mapping)}, expected=7)
    case('missing-environment-table', files={}, expected=7)
    case('damaged-environment-table', files={'CFG/PCPLUS.XLT': bytes(257)}, expected=7)
    case('empty-environment', directory='', files={'CFG/PCPLUS.XLT': bytes(mapping)}, expected=7)
    case('oversized-directory', directory='A'*53, files={}, expected=7)
    case('maximum63-byte-path', directory='D:\\'+deep.replace('/', '\\'), files={deep+'/PCPLUS.XLT': bytes(mapping)})
    sources = [Path(__file__).resolve(), ROOT/'standalone/test_connection_dos.py',
               ROOT/'src/config/resource_path.c', ROOT/'src/config/resource_path.h',
               ROOT/'src/translation/xlt_default.c', ROOT/'src/translation/xlt_default.h']
    result = dict(passed=True, binary_sha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(), cases=cases,
                  sources={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
                  scope='Actual DOSBox-X inherited PSP/MCB environment, default-mode resource lookup, exact256-byte XLT import, native receive/parser/replies and pre-UART rejection. Same checked files and independent UART/PIC/IRQ before/after snapshots. Synthetic media and serial peer only; no physical modem or other-resource fallback claim.')
    (ROOT/'build/terminal/resource-lookup-dos-checks.json').write_text(json.dumps(result, indent=2)+'\n')
    print('Resource lookup DOS passed:', len(cases))


if __name__ == '__main__':
    main()
