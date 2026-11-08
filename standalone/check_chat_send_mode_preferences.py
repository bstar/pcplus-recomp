#!/usr/bin/env python3
"""Linked Chat preference publication; DOS file effects are explicitly modeled."""
import argparse
import json
import struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_EFLAGS
import check_display_preferences_live as fixture
from build_path_session import ROOT, sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--terminal', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    binary, out = args.terminal.resolve(), args.output.resolve()
    manifest = json.loads(binary.with_name('manifest.json').read_text())
    assert manifest['experimental_chat_send_mode'] and sha(binary) == manifest['binary_sha256']
    for name, digest in manifest['sources'].items():
        assert sha(ROOT / name) == digest
    fixture.startup.BINARY = fixture.directory.BINARY = binary
    fixture.startup.MAP = fixture.directory.MAP = binary.with_name('terminal.map')
    assert out.is_relative_to(ROOT / 'build') and not out.exists()
    out.mkdir()
    cases = []
    for kind in ('serial', 'modem', 'directory'):
        values = range(256) if kind == 'serial' else (0, 1, 2, 127, 255)
        count = 0
        for value in values:
            model = fixture.new(kind)
            raw = bytearray(model.prm if kind == 'directory' else model.payload)
            raw[0x1f2:0x1f4] = bytes([value, 167])
            if kind == 'directory':
                model.prm = bytes(raw)
            else:
                model.payload = bytes(raw)
            model.put('_terminal_chat_buffered', 0x5aa5)
            reached = []
            def publish(uc, address, size, unused):
                if address == model.symbols['_hook_baseline_publish']:
                    assert model.get('_terminal_chat_buffered') == 0x5aa5
                    reached.append(True)
            hook = model.uc.hook_add(UC_HOOK_CODE, publish)
            try:
                assert fixture.invoke(model, kind) == 0
            finally:
                model.uc.hook_del(hook)
            assert reached == [True] and model.get('_terminal_chat_buffered') == value
            count += 1
        cases.append(dict(case=kind + '-raw-byte-publication-after-baseline', inputs=count, passed=True))
    for kind in ('modem', 'directory'):
        for fault in ('io', 'serial', 'modem', 'transfer', 'mouse', 'baseline'):
            model = fixture.new(kind)
            model.put('_terminal_chat_buffered', 0x5aa5)
            if fault == 'io':
                if kind == 'directory':
                    model.prm_status = 1
                else:
                    model.load_status = 1
            elif fault != 'baseline':
                at, value = {'serial': (0, 8), 'modem': (14, 2),
                             'transfer': (0x31c, 0x4f43), 'mouse': (0x4e4, 0)}[fault]
                raw = bytearray(model.prm if kind == 'directory' else model.payload)
                struct.pack_into('<H', raw, at, value)
                if fault == 'transfer':
                    raw[0x31c:0x320] = b'CON\0'
                if kind == 'directory':
                    model.prm = bytes(raw)
                else:
                    model.payload = bytes(raw)
            reached = []
            def refuse(uc, address, size, unused):
                if fault == 'baseline' and address == model.symbols['_hook_baseline_publish']:
                    reached.append(True)
                    uc.reg_write(UC_X86_REG_EFLAGS, uc.reg_read(UC_X86_REG_EFLAGS) & ~0x200)
            hook = model.uc.hook_add(UC_HOOK_CODE, refuse)
            try:
                status = fixture.invoke(model, kind)
            finally:
                model.uc.hook_del(hook)
            assert status and model.get('_terminal_chat_buffered') == 0x5aa5
            if fault == 'baseline':
                assert status == 16 and reached == [True]
            cases.append(dict(case=kind + '-' + fault + '-refusal-retains-mode', inputs=1, passed=True))
    count = 0
    for kind in ('serial', 'modem', 'directory'):
        for index in (range(5) if kind != 'directory' else (0, 1, 4, 5, 6, 7, 8, 9)):
            if kind == 'serial' and index == 2:
                continue
            model = fixture.new(kind)
            model.put('_terminal_chat_buffered', 0x5aa5)
            arguments = fixture.args(model, kind)
            arguments[index] = model.offset('_terminal_chat_buffered')
            assert fixture.invoke(model, kind, arguments) != 0
            assert not model.calls and model.get('_terminal_chat_buffered') == 0x5aa5
            count += 1
    cases.append(dict(case='global-alias-refusal-before-file-IO', inputs=count, passed=True))
    names = ['standalone/check_chat_send_mode_preferences.py', 'standalone/check_display_preferences_live.py',
             'standalone/check_startup_import.py', 'standalone/check_directory_live.py',
             'standalone/check_directory_context.py', 'standalone/dos_image.py']
    result = dict(passed=True, cases=cases, inputs=sum(row['inputs'] for row in cases),
                  binary_sha256=sha(binary), sources={**manifest['sources'], **{name: sha(ROOT / name) for name in names}},
                  scope=__doc__ + ' Actual public serial/modem/directory readers and late baseline validation execute with DS=SS. All raw bytes and alias/refusal ordering checked. No real file IO, BIOS keys, live commit, BBS or physical claim.')
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print('PASS', result['inputs'], 'startup preference cases')


if __name__ == '__main__':
    main()
