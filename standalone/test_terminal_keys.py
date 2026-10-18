#!/usr/bin/env python3
"""Actual DOS BIOS key events, KBD startup import and binary UART output."""
import hashlib
import json
import struct
from pathlib import Path
from test_connection_dos import run, ROOT, BINARY
from modem_fixtures import fixture


def main():
    cases = []

    def check(name, keys, wanted, **options):
        proof = run('keys-' + name, options.pop('mode', 'success'), keys, **options)
        folder = ROOT / 'build/connection-dos' / ('keys-' + name)
        wire = (folder / 'serial.bin').read_bytes()
        proof['checks']['exact_key_output'] = wanted in wire if wanted is not None else not wire
        proof['passed'] = all(proof['checks'].values())
        (folder / 'result.json').write_text(json.dumps(proof, indent=2) + '\n')
        cases.append(proof)
        print(name, 'PASS' if proof['passed'] else json.dumps(proof), flush=True)

    default_keys = 'p3000 k e y s p120 home p120 end p120 ins p120 del p120 pgup p120 pgdown p120 tab p120 s-tab p120 bs p120 enter p120 f1 p120 f5 p120 d o n e p500 a-x'
    check('network-navigation', default_keys,
          b'keys\x1b[H\x1b[F\x1b[2~\x1b[3~\x1b[5~\x1b[6~\t\x1b[Z\b\r\x1bOP\x1b[15~done')
    check('function-modifiers', 'p3000 k e y s p120 f11 p120 f12 p120 s-f1 p120 s-f12 p120 c-f1 p120 c-f12 p120 d o n e p500 a-x',
          b'keys\x1b[23~\x1b[24~\x1b[1;2P\x1b[24;2~\x1b[1;5P\x1b[24;5~done')

    library = bytearray(7 * 948)
    bindings = {6: b'CUSTOM-TAB', 7: b'BACKTAB', 8: b'INSERT', 9: b'DELETE',
                10: b'BACKSPACE', 13: b'PAGE-UP', 14: b'PAGE-DOWN',
                16: b'\xffF1', 50: b'UP', 56: b'HOME', 57: b'END',
                72: b'UP', 76: b'HOME', 77: b'END', 78: b'\r\n'}
    for profile in (4, 6):
        for slot, value in bindings.items():
            at = profile * 948 + slot * 12
            library[at:at + len(value)] = value
    for profile in (4, 6):
        settings = bytearray(fixture(timeout=5))
        struct.pack_into('<H', settings, 0x194, profile)
        check('KBD-profile-' + str(profile),
              'p3000 k e y s p120 home p120 end p120 up p120 tab p120 f1 p120 enter p120 d o n e p500 a-x',
              b'keysHOMEENDUPCUSTOM-TAB\0F1\r\ndone', prm=bytes(settings), profile=profile,
              arguments='@D:\\TEST.PRM /D:CaseTest:23 /K:D:\\TEST.KBD', files={'TEST.KBD': bytes(library)})

    for name, data in (('empty', b''), ('short', bytes(library[:-1])), ('suffix', bytes(library) + b'X'),
                       ('missing-profile', bytes(948)), ('unterminated', bytes(library[:6 * 948]) + b'X' * 12 + bytes(948 - 12))):
        check('invalid-' + name, 'p500 a-x', None, mode='reject', expected=7,
              arguments='/K:D:\\TEST.KBD', files={'TEST.KBD': data})
    check('missing-file', 'p500 a-x', None, mode='reject', expected=7,
          arguments='/K:D:\\NOFILE.KBD')

    summary = {'passed': all(case['passed'] for case in cases),
               'binary_sha256': hashlib.sha256(BINARY.read_bytes()).hexdigest(), 'cases': cases,
               'scope': 'Actual DOS BIOS events, startup profile selection, strict synthetic KBD import, FF-to-wire-NUL conversion, live sender/UART and restored IRQ/PIC/register state. No installed mappings or physical modem.'}
    out = ROOT / 'build/terminal-keys'; out.mkdir(parents=True, exist_ok=True)
    (out / 'result.json').write_text(json.dumps(summary, indent=2) + '\n')
    return 0 if summary['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
