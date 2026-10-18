#!/usr/bin/env python3
"""Production DOS PRMEDIT mode adoption and post-child UART/input transforms."""
import hashlib
import json
from pathlib import Path
from build_live_translation_child import main as build_child, OUT as child_dir
from check_setup_model import image
from check_directory_live import word
from test_setup_startup_dos import run, OUT, ROOT, BINARY, EDITOR

IDENTITY = bytes(range(256))
FIELD = 'pgdown ' + 'tab '*8 + 'home del '


def main():
    cases = []
    mapping = bytearray(IDENTITY);mapping[ord('L')] = ord('X')
    other = bytearray(IDENTITY);other[ord('L')] = ord('Z')
    high = bytes(value | 128 for value in b' LIVE')
    recipes = [
        ('enable-table', 0, 1, 'y', {'PCPLUS.XLT': bytes(mapping)}, None, b' XIVE', None),
        ('disable-table', 1, 0, 'y', {'PCPLUS.XLT': bytes(mapping)}, None, b' LIVE', None),
        ('enable-sevenbit', 0, 2, 'y', {}, high, b' LIVE', None),
        ('disable-sevenbit', 2, 0, 'y', {}, high, high, None),
        ('decline-sevenbit', 0, 2, 'space', {}, high, high, None),
        ('missing-table-keeps-identity', 0, 1, 'space', {}, None, b' LIVE', None),
        ('short-table-keeps-mask', 2, 1, 'space', {'PCPLUS.XLT': bytes(255)}, high, b' LIVE', None),
        ('environment-table', 0, 1, 'y', {'CFG/PCPLUS.XLT': bytes(mapping)}, None, b' XIVE', {'PCPLUS': 'D:\\CFG'}),
        ('explicit-X-keeps-table', 0, 2, 'space', {'EXPLICIT.XLT': bytes(mapping)}, None, b' XIVE', None),
    ]
    for name, initial, desired, answer, files, post, expected, environment in recipes:
        name = 'live-xlt-'+name
        arguments = '@TEST.PRM' + (' /X:EXPLICIT.XLT' if 'explicit-X' in name else '')
        keys = 'p2000 a-f10 p500 '+FIELD+str(desired)+' f10 escape '+answer+' r e a d y'
        proof, actual = run(name, keys=keys, arguments=arguments, payload=word(image(), 0x1e0, initial),
                            post_echo=True, rate_mask=1, line_mask=1, files=files,
                            post_banner=post, environment=environment)
        assert actual == word(image(), 0x1e0, desired), name
        screen = (OUT/name/'SCREEN.BIN').read_bytes()
        assert screen[22:32:2] == expected, (name, screen[22:32:2], expected)
        proof['checks']['post_child_characters_prove_effective_input_mode'] = True
        proof['checks']['exact_saved_PRM_mode'] = True
        cases.append(proof)

    # A separate source-built child deliberately changes CWD after editing the
    # same mapped field. Production editor coverage above stays independent.
    build_child()
    name = 'live-xlt-child-cwd-binding'
    proof, actual = run(name, keys='p2000 a-f10 p500 y r e a d y', arguments='@TEST.PRM',
                        post_echo=True, rate_mask=1, line_mask=1, child_binary=child_dir/'CHDIR.EXE',
                        files={'PCPLUS.XLT': bytes(mapping), 'OTHER/PCPLUS.XLT': bytes(other)})
    assert actual == word(image(), 0x1e0, 1)
    assert (OUT/name/'SCREEN.BIN').read_bytes()[22:32:2] == b' XIVE'
    proof['checks']['child_CWD_did_not_retarget_table_or_PRM'] = True;cases.append(proof)
    inputs = [Path(__file__).resolve(), ROOT/'standalone/test_setup_startup_dos.py',
              ROOT/'standalone/live_translation_child.c', ROOT/'src/translation/xlt_live.c',
              ROOT/'standalone/build_live_translation_child.py',
              ROOT/'src/translation/xlt_live.h', ROOT/'src/terminal/setup_translation.asm']
    result = dict(passed=True, terminal_sha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),
                  editor_sha256=hashlib.sha256(EDITOR.read_bytes()).hexdigest(), cases=cases,
                  child_sha256=hashlib.sha256((child_dir/'CHDIR.EXE').read_bytes()).hexdigest(),
                  sources={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
                  scope='Actual DOSBox-X production PRMEDIT live changes, Y/decline, exact saved mode, table enable/disable,7-bit enable/disable, default/environment file errors and explicit /X override. Fresh physical UART peer bytes and CPR prove effective receive transforms; independent IRQ/UART/PIC restoration and unchanged fixtures. Separate source-built child changes CWD to verify frozen table/PRM paths. No physical modem, same-mode reload command or original PCSETUP ABI claim.')
    (ROOT/'build/terminal/live-translation-dos-checks.json').write_text(json.dumps(result, indent=2)+'\n')
    print('Live translation DOS passed', len(cases))


if __name__ == '__main__':
    main()
