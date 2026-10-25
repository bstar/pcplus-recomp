#!/usr/bin/env python3
"""Execute original-key candidate UI/dispatch; only hardware and DOS are modeled."""
import argparse
import hashlib
import json
from pathlib import Path
import check_transport as transport


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--terminal',type=Path,required=True)
    args=p.parse_args();binary=args.terminal.resolve();base=binary.parent
    manifest=json.loads((base/'manifest.json').read_text())
    assert manifest['experimental_original_keys'] and not manifest.get('original_inputs')
    assert hashlib.sha256(binary.read_bytes()).hexdigest()==manifest['binary_sha256']
    for name,digest in manifest['sources'].items():
        assert hashlib.sha256((transport.ROOT/name).read_bytes()).hexdigest()==digest,name
    transport.BINARY=binary;transport.MAP=base/'terminal.map'
    from check_recording_ui_live import UI
    from check_recording_rx_live import ordinary
    cases=[]
    def check(name,fn):
        count=fn();cases.append(dict(case=name,inputs=count,passed=True));print(name,count,flush=True)
    def recorder():
        m=UI();m.key(0x1300)
        assert b'Recording file:' in m.text() and not m.get('terminal_transfer_pending')
        m.key(13);assert m.field('state')==1 and not m.get('_redisplay_active')
        ordinary(m,b'Name? ')
        for b in b'bstar':m.key(b)
        m.drain();m.key(0x1300)
        assert b'Recording saved.' in m.text() and m.field('published')==1
        assert b'transmitraw "6273746172"' in m.files['PCPLUS.ASP']
        m.back();assert not m.get('terminal_quit') and not m.handles
        return 9
    check('Alt-R-start-receive-transmit-and-save-real-recorder',recorder)
    def background():
        m=UI();m.key(0x1300);view=bytes(m.uc.mem_read(0xb8000,4000))
        payload=b'BBS-DURING-DIALOG'
        # Match the actual main-loop frame transaction around normal parsing.
        m.call('terminal_redisplay_before');ordinary(m,payload+b'\x1b[6n')
        m.call('terminal_redisplay_idle');m.drain()
        assert bytes(m.uc.mem_read(0xb8000,4000))==view
        assert bytes(m.tx)==f'\x1b[1;{len(payload)+1}R'.encode()
        assert not m.get('uart_rx_dropped') and not m.handles
        m.back();assert payload in m.text() and not m.get('terminal_quit')
        return 1
    check('direct-recorder-services-BBS-query-and-restores-updated-screen',background)
    def settings():
        for key in [0x1f00,0x1900,0x7100]:
            m=UI();m.put('terminal_setup_status',0xffff);m.key(key)
            assert m.get('terminal_setup_status')==1
            assert not m.get('terminal_transfer_pending') and not m.get('terminal_quit') and not m.tx
        return 3
    check('Alt-S-Alt-P-and-retained-Alt-F10-use-settings-eligibility',settings)
    def history():
        for key in [0x6d00,0x8400,0x84e0]:
            m=UI();ordinary(m,b'HISTORY\r\n');m.key(key)
            assert m.get('_redisplay_active') and not m.get('_command_menu_active')
            assert b'HISTORY' in m.text();m.key(27)
            assert not m.get('_redisplay_active') and not m.get('terminal_quit')
        return 3
    check('Alt-F6-and-existing-Ctrl-PgUp-open-serviced-history',history)
    def pages():
        for key,slot,wire in [(0x49e0,58,b'\x1b[5~'),(0x51e0,59,b'\x1b[6~')]:
            m=UI();m.uc.mem_write(m.symbols['terminal_keymap']+12*slot,wire+bytes(12-len(wire)))
            m.key(key);m.drain()
            assert bytes(m.tx)==wire and not m.get('terminal_transfer_pending') and not m.get('terminal_quit')
            m=UI();m.uc.mem_write(m.symbols['terminal_keymap']+12*slot,bytes(12))
            m.key(key)
            assert m.get('terminal_transfer_pending') and not m.get('terminal_quit') and not m.tx
            m.keys.append(27);m.call('terminal_transfer_poll',limit=6000000)
            assert not m.get('terminal_transfer_pending')
        # An unterminated assignment remains an error, never a transfer request.
        m=UI();m.uc.mem_write(m.symbols['terminal_keymap']+12*58,b'X'*12);m.key(0x49e0)
        assert m.get('terminal_quit') and not m.get('terminal_transfer_pending')
        return 5
    check('assigned-page-keys-send-exactly-unassigned-open-transfer-invalid-stays-error',pages)
    def menus():
        for letter in b'RS':
            m=UI();m.menu();m.key(letter)
            assert m.get('terminal_transfer_pending') and not m.get('terminal_quit')
            m.keys.append(27);m.call('terminal_transfer_poll',limit=6000000)
            assert not m.get('terminal_transfer_pending')
        return 2
    check('menu-transfers-remain-accessible-after-Alt-R-Alt-S-restoration',menus)
    def guarded():
        for owner in ['terminal_transfer_pending','terminal_program_pending','terminal_macro_active',
                      'terminal_monitor_active','terminal_controller_active','terminal_ansi_wait_active']:
            m=UI();m.put(owner,1);m.key(0x1300)
            assert not m.get('_command_menu_active') and m.field('state')==0 and not m.get('terminal_quit')
        return 6
    check('direct-recorder-respects-existing-exclusive-owner-guards',guarded)
    result=dict(passed=True,binary_sha256=manifest['binary_sha256'],cases=cases,
        scope=__doc__+' No product service is skipped or replaced. Original reference/pull-down layout and full menu parity remain open.')
    (base/'original-key-checks.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':main()
