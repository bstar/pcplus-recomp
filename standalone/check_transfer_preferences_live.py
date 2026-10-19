#!/usr/bin/env python3
"""Linked one-image startup and live-child transfer-preference transactions.
Synthetic PRM/directory/DOS boundaries; no automatic BBS session claim.
"""
import hashlib
import json
import struct
from check_startup_import import Startup, terminal_expected
from check_modem_import import expected as modem_expected
from check_directory_context import Context
from check_directory_live import word, text
from check_live_setup_apply import LiveSettings, launch
from check_terminal_zmodem_live import ROOT, BINARY

def expected(raw):
    enabled = bool(int.from_bytes(raw[0x42c:0x42e], 'little'))
    path = raw[0x31c:0x35c].split(b'\0')[0] or b'.'
    return struct.pack('<H', enabled) + path.ljust(64, b'\0')

def main():
    cases = []
    def done(name, count):
        cases.append(dict(case=name, inputs=count, passed=True)); print(name, count, flush=True)
    count = 0
    for modem in (False, True):
        for enabled in (0, 1, 65535):
            for path in (b'', b'INBOX', b'C:\\', b'C:'):
                m = Startup();m.payload = text(word(m.payload, 0x42c, enabled), 0x31c, 64, path)
                prefs = m.offset('_terminal_transfer_preferences')
                status = m.call('_terminal_preferences_read', [m.path, m.serial, m.modem if modem else 0, prefs, m.result], limit=2000000)
                assert status == 0 and len(m.calls) == 1
                assert bytes(m.uc.mem_read(m.data_base + prefs, 66)) == expected(m.payload)
                assert m.plans()[0] == terminal_expected(m.payload)
                if modem:assert m.plans()[1] == modem_expected(m.payload)
                count += 1
    done('single-PRM-read-atomic-startup-with-and-without-modem-plans', count)
    count = 0
    for path in (b'CON', b'../OUT', b'A' * 64):
        m = Startup();raw = bytearray(m.payload)
        raw[0x31c:0x31c + min(len(path)+1, 64)] = (path + b'\0')[:64];m.payload = bytes(raw)
        prefs = m.offset('_terminal_transfer_preferences');m.poison()
        m.uc.mem_write(m.data_base + prefs, b'\xce' * 66);before = m.plans()
        assert m.call('_terminal_preferences_read', [m.path, m.serial, m.modem, prefs, m.result], limit=2000000) == 14
        assert m.plans() == before and bytes(m.uc.mem_read(m.data_base + prefs, 66)) == b'\xce' * 66
        count += 1
    done('invalid-transfer-preference-keeps-all-startup-plans-unchanged', count)
    m = Startup();prefs = m.offset('_terminal_transfer_preferences')
    good = [m.path, m.serial, m.modem, prefs, m.result]
    count = 0
    for index, pointer in ((0,0), (1,0), (3,0), (1,0xffff), (2,0xfff0),
                           (3,0xffc0), (4,0xfffc), (3,m.serial), (4,m.modem),
                           (1,m.path), (2,prefs), (4,prefs)):
        args = list(good);args[index] = pointer;before = m.plans()
        assert m.call('_terminal_preferences_read', args, limit=1000000) == 6
        assert not m.calls and m.plans() == before
        count += 1
    done('startup-null-alias-and-wrap-arguments-refuse-before-loading', count)
    m = Context();prefs = m.offset('_terminal_transfer_preferences')
    good = m.arguments() + [m.context, prefs];count = 0
    for index, pointer in ((0,0), (1,0), (4,0), (5,0), (6,0), (7,0), (8,0),
                           (9,0), (9,0xffc0), (8,0xff00), (7,m.context),
                           (9,m.serial), (5,m.plan), (4,m.prm_path)):
        args = list(good);args[index] = pointer;before = m.outputs()
        assert m.call('_terminal_directory_preferences_read', args, limit=1000000) == 1
        assert not m.calls and m.outputs() == before
        count += 1
    done('directory-null-alias-and-wrap-arguments-refuse-before-any-read', count)
    for entry in (1, 17, 200):
        m = Context();m.entry = entry;m.poison();prefs = m.offset('_terminal_transfer_preferences')
        assert m.call('_terminal_directory_preferences_read', m.arguments() + [m.context, prefs], limit=3000000) == 0
        assert m.context_bytes() == m.expected_context()
        assert bytes(m.uc.mem_read(m.data_base + prefs, 66)) == expected(m.prm)
        assert [c[0] for c in m.calls] == ['prm', 'directory']
    done('ten-argument-directory-reader-retains-selection-and-preferences', 3)
    for enabled, path in ((1,b'INBOX'), (65535,b'C:\\RX'), (0,b'')):
        m = LiveSettings();raw = text(word(m.raw, 0x42c, enabled), 0x31c, 64, path)
        launch(m, raw)
        assert m.get('terminal_setup_apply_status') == 0
        assert bytes(m.uc.mem_read(m.symbols['_terminal_transfer_preferences'], 66)) == expected(raw)
        assert m.call('_live_setup_transfer_settings', [m.offset('_terminal_transfer_preferences')]) == 7
    done('successful-child-adopts-transfer-preferences-and-consumes-offer', 3)
    m = LiveSettings();before = bytes(m.uc.mem_read(m.symbols['_terminal_transfer_preferences'], 66))
    launch(m, text(word(m.raw,0x42c,1),0x31c,64,b'CON'))
    assert m.get('terminal_setup_apply_status') != 0
    assert bytes(m.uc.mem_read(m.symbols['_terminal_transfer_preferences'], 66)) == before
    done('invalid-child-path-preserves-active-transfer-preferences', 1)
    result = dict(passed=True, cases=cases, binary_sha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),
                  scope='Actual linked startup readers, ten-word bridge and live PROGRAM/settings adoption. Only synthetic DOS/file boundaries modeled; no actual DOS/BBS preference workflow claim.')
    (ROOT / 'build/terminal/transfer-preferences-live-checks.json').write_text(json.dumps(result, indent=2) + '\n')

if __name__ == '__main__':
    main()
