#!/usr/bin/env python3
"""Saved translation selection: real linked validators, editor, driver and owner."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from check_translation_live import Translation, ROOT, BINARY
from check_terminal_config import Import
from terminal_config_fixtures import image
from check_live_configuration import Model as Candidate
from check_live_setup_owner import Owner
from check_directory_live import word
from check_setup_model import Model as Editor, build as build_editor
from check_live_setup_apply import launch
from live_setup_kernel import LiveSettings


def main(original=False):
    groups = []
    def check(name, fn):
        count = fn()
        groups.append(dict(case=name, inputs=count, passed=True))
        print(name, 'PASS', count, flush=True)

    def decoding():
        for mode in (0, 1, 2):
            m = Import()
            status, data = m.decode(image(translation=mode))
            assert status == 0 and len(data) == 42 and struct.unpack_from('<H', data, 40)[0] == mode
        for mode in (3, 127, 256, 65535):
            m = Import()
            status, data = m.decode(image(translation=mode))
            assert status == 12 and data == b'\xcc' * 42
        return 7
    check('PRM-offset1e0-three-modes-exact42-byte-plan-and-invalid-atomic-rejection', decoding)

    def startup():
        mapping = bytearray(range(256));mapping[ord('x')] = ord('y')
        m = Translation();assert m.load(None, selected=False, prm_mode=0) == 0
        assert m.get('terminal_translation_mode') == 0 and m.get('uart_rx_mask') == 255 and not m.xlt_calls
        m = Translation();assert m.load(mapping, selected=False, prm_mode=1) == 0
        assert m.get('terminal_translation_mode') == 1 and m.get('uart_rx_mask') == 255
        assert m.xlt_calls[0][1] == 'PCPLUS.XLT'
        m.feed_normal(b'x');assert bytes(m.uc.mem_read(0xb8000, 2)) == b'y\x07'
        m = Translation();assert m.load(None, selected=False, prm_mode=1) == 12
        assert not m.get('terminal_translation_mode') and not m.get('terminal_translation_enabled')
        for mode in (0, 1, 2):
            m = Translation();assert m.load(mapping, prm_mode=mode) == 0
            assert m.get('terminal_translation_mode') == 1 and m.get('uart_rx_mask') == 255
            assert m.xlt_calls[0][1] == 'TEST.XLT'
        return 6
    check('saved-mode-startup-default-name-missing-table-and-explicit-X-override', startup)

    def masking():
        m = Translation();assert m.load(None, selected=False, prm_mode=2) == 0
        assert m.get('terminal_translation_mode') == 2 and m.get('uart_rx_mask') == 127
        assert not m.xlt_calls and not m.get('terminal_translation_enabled')
        m.receive_irq(bytes(range(256)))
        assert [m.call('uart_receive_byte') for _ in range(256)] == [i & 127 for i in range(256)]
        m.feed_normal(b'\x1bc')
        assert m.get('uart_rx_mask') == 127 and m.get('terminal_translation_mode') == 2
        m.enter();expected=bytes(i & 127 for i in range(256))
        assert m.feed(bytes(range(256))) == expected
        m.stop();assert m.dump() == expected
        return 513
    check('all256-original-driver-mask-values-raw-monitor-and-RIS-retention', masking)

    def transfers():
        for name in ('terminal_transfer_start', 'terminal_upload_start'):
            m = Translation();assert m.load(None, selected=False, prm_mode=2) == 0
            before = {name: bytes(value) for name, value in m.files.items()}
            m.call(name)
            assert not m.get('terminal_transfer_pending') and not m.get('terminal_transfer_active')
            assert not m.handles and before == {name: bytes(value) for name, value in m.files.items()}
        from check_terminal_transfer_live import LiveTransfer
        m = LiveTransfer(data=bytes(range(256)) * 4)
        m.put('terminal_translation_mode', 1);m.put('terminal_translation_enabled', 1)
        m.uc.mem_write(m.symbols['terminal_translation_table'], bytes(256))
        m.receive()
        assert m.storage()[0] == 3 and bytes(m.files['OWNED.BIN']) == m.payload and not m.handles
        return 3
    check('binary-upload-and-download-refused-before-filename-or-file-ownership', transfers)

    def transactions():
        Candidate.terminal = True
        for active_mode in (0, 1, 2):
            for mode in (0, 1, 2):
                flag = 2048 if mode != active_mode else 0
                m = Candidate();m.uc.mem_write(m.data_base + m.active + 40, struct.pack('<H', active_mode))
                m.raw = word(m.raw, 0x1e0, mode)
                assert m.decode() == (0, (0, 0)) and m.change() == flag
                assert struct.unpack_from('<H', m.output(), 40)[0] == mode
                owner = Owner();owner.uc.mem_write(owner.data_base + owner.active + 40, struct.pack('<H', active_mode))
                owner.ready();owner.raw = word(owner.raw, 0x1e0, mode)
                assert owner.finish() == (0, (0, 0, 0, flag))
                assert owner.output()[40:42] == struct.pack('<H', active_mode)
        for mode in (3, 65535):
            m = Candidate();m.raw = word(m.raw, 0x1e0, mode)
            assert m.decode(mask=15) == (2, (2, 12))
        owner = Owner();owner.uc.mem_write(owner.data_base + owner.active + 40, b'\x01\0')
        assert owner.bind() == 0 and owner.begin(16384) == 0
        owner.raw = word(owner.raw, 0x1e0, 2)
        assert owner.finish() == (0, (0, 0, 0, 0)) and owner.output()[40:42] == b'\x01\0'
        owner = Owner();assert owner.bind() == 0 and owner.begin(16384) == 0
        owner.raw = word(owner.raw, 0x1e0, 3)
        assert owner.finish() == (5, (5, 2, 0, 0))
        return 22
    check('pure-plan-classification-live-deferral-CLI-precedence-and-raw-validation', transactions)

    def editor():
        build_editor();m = Editor()
        for mode in (0, 1, 2):
            m.reset();before = m.raw()
            assert m.set(44, str(mode).encode()) == 0
            assert m.raw() == word(before, 0x1e0, mode)
            assert m.validate() == (0, 65535)
        for text in (b'3', b'65535', b'-1', b'X', b''):
            assert m.set(44, text) == 2
        return 8
    check('45th-editor-field-three-valid-values-opaque-preservation-and-invalid-edits', editor)

    def application():
        for active_mode, desired in ((0, 2), (2, 0)):
            m = LiveSettings();mask = 127 if active_mode == 2 else 255
            m.put('terminal_translation_mode', active_mode);m.put('uart_rx_mask', mask)
            launch(m, word(word(m.raw, 0x1e0, desired), 0x1ae, 30))
            outcome = struct.unpack('<4H', m.uc.mem_read(m.symbols['terminal_setup_outcome'], 8))
            assert outcome == (0, 0, 32, 2048)
            assert m.get('attributes_normal_value') == 30
            assert m.get('terminal_translation_mode') == active_mode and m.get('uart_rx_mask') == mask
            assert b'deferred changes need restart' in m.local_text
        return 2
    check('actual-AltF10-foreground-keeps-mask-while-adopting-independent-display-edit', application)

    native = []
    if original:
        from check_translation import Machine, DATA, TABLE
        source = (ROOT / 'analysis/pcplus-originals/PCPLUS-main-2.01.EXE').read_bytes()
        assert hashlib.sha256(source).hexdigest() == '6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
        manifest = json.loads((ROOT / 'analysis/pcplus-overlays/manifest.json').read_text())
        overlay = manifest['overlays'][2]
        for mode in (0, 1, 2, 3, 65535):
            m = Machine(source)
            start = overlay['source_file_offset'];end = start + overlay['initialized_bytes']
            blob = source[start:end]
            assert hashlib.sha256(blob).hexdigest() == overlay['sha256']
            m.uc.mem_write(0x10000 + overlay['relative_load_segment'] * 16, blob)
            m.word(0x1d64, mode);m.word(0x324e, 0x4100)
            m.open_result = 0x4500;m.close_result = 0;m.file_bytes = bytes([ord('Z')]) * 256
            m.call(0xdef8)
            assert bytes(m.uc.mem_read(DATA + TABLE, 256)) == (m.file_bytes if mode == 1 else bytes(range(256)))
            mask = struct.unpack('<H', m.uc.mem_read(DATA + 0x8e22, 2))[0]
            assert mask == (127 if mode == 2 else 255)
            assert bool(m.calls) == (mode == 1)
            native.append(dict(mode=mode, mask=mask, loaded=bool(m.calls)))
    helpers = ['check_translation_modes.py', 'check_translation_live.py', 'check_terminal_config.py',
               'terminal_config_fixtures.py', 'check_live_configuration.py', 'check_live_setup_owner.py',
               'check_setup_model.py', 'check_live_setup_apply.py', 'live_setup_kernel.py',
               'check_translation.py', 'check_terminal_transfer_live.py']
    result = dict(passed=True, binary_sha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),
                  inputs=sum(g['inputs'] for g in groups), cases=groups, original_cases=native,
                  original_sha256='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904' if original else None,
                  sources={'standalone/' + name: hashlib.sha256((ROOT / 'standalone' / name).read_bytes()).hexdigest() for name in helpers},
                  scope='Actual linked42-byte PRM validator,626-byte candidate/owner,45-field editor, driver, monitor, RIS and transfer gates. Hardware/DOS modeled except editor diagnostic compilation. Optional genuine-original overlay3 comparison uses controlled CRT boundaries; no synthetic analysis EXE executes. Invalid native selections default to identity; maintained validator deliberately rejects them.')
    (ROOT / 'build/terminal/translation-mode-checks.json').write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser();parser.add_argument('--original', action='store_true')
    main(parser.parse_args().original)
