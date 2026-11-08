#!/usr/bin/env python3
"""Actual BIOS-key saves/reload/cancel of the recovered one-byte Chat mode."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
from check_setup_model import image
from build_path_session import ROOT, sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--editor', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    editor, out = args.editor.resolve(), args.output.resolve()
    assert out.is_relative_to(ROOT / 'build') and not out.exists()
    manifest = json.loads(editor.with_name('manifest.json').read_text())
    assert manifest['experimental_chat_mode'] and manifest['experimental_mouse']
    assert manifest['experimental_notice_sound'] and manifest['field_count'] == 52
    assert sha(editor) == manifest['binary_sha256']
    for name, digest in manifest['sources'].items():
        assert sha(ROOT / name) == digest
    out.mkdir()
    shutil.copyfile(editor, out / 'PRMEDIT.EXE')
    initial = bytearray(image())
    initial[0x1f2:0x1f4] = b'\xff\xa7'
    initial[0x4e4:0x4e8] = b'\x08\0\x04\0'
    (out / 'VALID.PRM').write_bytes(initial)
    cases = []
    for label, value, save in [('immediate', 0, True), ('buffered', 1, True),
                                ('noncanonical-buffered', 255, True), ('cancel', 0, False)]:
        before = (out / 'VALID.PRM').read_bytes()
        # PgDn selects TERMINAL. Reverse from its first field crosses pages,
        # so walk all fifteen following TERMINAL fields explicitly.
        keys = ['pgdown'] + ['tab'] * 15 + ['home', 'del', 'del', 'del'] + list(str(value))
        keys += ['f10', 'escape'] if save else ['escape', 'y']
        schedule = 'ADDKEY p700 ' + ' p100 '.join(keys)
        config = out / 'dosbox.conf'
        config.write_text(f'[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=386\ncycles=fixed 6000\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "{out}"\nc:\n{schedule}\nPRMEDIT VALID.PRM\nif errorlevel 1 goto fail\necho PASS>PASS.TXT\ngoto done\n:fail\necho FAIL>FAIL.TXT\n:done\nexit\n')
        for name in ('PASS.TXT', 'FAIL.TXT'):
            (out / name).unlink(missing_ok=True)
        with (out / (label + '.log')).open('w') as log:
            subprocess.run(['dosbox-x', '-fastlaunch', '-nogui', '-conf', str(config)],
                stdout=log, stderr=log, check=True, timeout=25,
                env=dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy'))
        assert (out / 'PASS.TXT').exists() and not (out / 'FAIL.TXT').exists(), label
        expected = bytearray(before)
        if save:
            expected[0x1f2] = value
        after = (out / 'VALID.PRM').read_bytes()
        assert after == expected and after[0x1f3] == 0xa7, label
        assert not any((out / name).exists() for name in ('PRMEDIT.BAK', 'PRMEDIT.$$$'))
        assert sha(out / 'PRMEDIT.EXE') == sha(editor)
        (out / (label + '.prm')).write_bytes(after)
        cases.append(dict(case=label, passed=True, full_image_exact=True,
                          mode=after[0x1f2], opaque_neighbor=after[0x1f3], image_sha256=sha(out / 'VALID.PRM')))
        print('PASS', label, flush=True)
    sources = ['standalone/test_chat_mode_setup_dos.py', 'standalone/check_setup_model.py',
               'standalone/check_modem_import.py', 'standalone/build_path_session.py']
    result = dict(passed=True, cases=cases, editor_sha256=sha(editor),
        sources={**manifest['sources'], **{name: sha(ROOT / name) for name in sources}},
        scope=__doc__ + ' Source-built offline editor with synthetic PRM only. Each save is reloaded by the next invocation. No live terminal import, modem connection or physical acceptance.')
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    main()
