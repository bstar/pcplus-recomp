#!/usr/bin/env python3
"""Actual DOS PRMEDIT workflows for proved transfer settings, synthetic media.
No terminal automatic-transfer or remote peer claim.
"""
import hashlib
import json
import struct
from test_setup_dos import OUT, ROOT, build, image, run

def main():
    build()
    cases = []
    # Terminal page order retains the old profile/translation/clipboard fields.
    field = 'pgdown ' + 'tab ' * 10
    recipes = [
        ('enable', field + 'home del 1 f10 escape', 1, b''),
        ('nonzero-word', field + 'home del 6 5 5 3 5 f10 escape', 65535, b''),
        ('directory', field + 'tab i n b o x f10 escape', 0, b'inbox'),
        ('both', field + 'home del 1 tab d o w n l o a d f10 escape', 1, b'download'),
        ('cancel', field + 'home del 1 tab i n b o x escape y', 0, b''),
        ('bad-device', field + 'tab c o n f10 escape y', 0, b''),
    ]
    # A 63-byte supported path requires scrolling the 53-column field viewport.
    path = b'/'.join([b'A' * 8] * 7) + b'/'
    keys = ' '.join('/' if c == 47 else 'a' for c in path)
    recipes.append(('long-directory', field + 'tab ' + keys + ' f10 escape', 0, path.lower()))
    for name, keys, enabled, path in recipes:
        folder = run('transfer-settings-' + name, 'UI VALID.PRM', keys)
        expected = bytearray(image())
        struct.pack_into('<H', expected, 0x42c, enabled)
        expected[0x31c:0x31c + len(path) + 1] = path + b'\0'
        actual = (folder / 'VALID.PRM').read_bytes()
        assert actual == bytes(expected), name
        assert b'SETUP UI RESTORED' in (folder / 'LOG.TXT').read_bytes(), name
        cases.append(dict(case=name, passed=True, full_file_exact=True,
                          screen_cursor_shape_page_restored=True,
                          input_sha256=hashlib.sha256(image()).hexdigest(),
                          output_sha256=hashlib.sha256(actual).hexdigest()))
        print(name, 'passed', flush=True)
    sources = ['src/config/transfer_import.c', 'src/config/transfer_import.h',
               'src/config/setup_model.c', 'src/config/setup_model.h', 'src/config/setup_main.c',
               'src/config/setup_document.c', 'standalone/check_setup_model.py',
               'standalone/test_setup_dos.py', 'standalone/test_transfer_settings_dos.py',
               'standalone/build_setup.py']
    result = dict(passed=True, cases=cases,
                  editor_sha256=hashlib.sha256((OUT / 'PRMEDIT.EXE').read_bytes()).hexdigest(),
                  sources={p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in sources},
                  scope='Actual DOS BIOS-key PRMEDIT UI and checked owner on synthetic media. Exact full-image enable/nonzero/path/both/cancel/device-refusal/63-byte-path saves and screen restoration. No live terminal adoption, automatic download, BBS or physical modem claim.')
    (OUT / 'transfer-settings-checks.json').write_text(json.dumps(result, indent=2) + '\n')

if __name__ == '__main__':
    main()
