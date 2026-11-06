#!/usr/bin/env python3
"""Replay actual linked Chat storage exclusion; BIOS/UART remain modeled.

No Chat loader call, input/output frontend or physical acceptance is claimed.
"""
import argparse
import json
import re
import struct
from pathlib import Path
from unicorn import UC_HOOK_CODE, UC_HOOK_INTR
from unicorn.x86_const import *
import check_transport
from check_redisplay_live import Redisplay
from build_path_session import ROOT, sha


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('terminal', 'output'):
        p.add_argument('--'+name, type=Path, required=True)
    a = p.parse_args()
    binary, out = a.terminal.resolve(), a.output.resolve()
    assert out.is_relative_to(ROOT/'build') and not out.exists()
    manifest = json.loads(binary.with_name('manifest.json').read_text())
    assert manifest['experimental_chat_storage'] and sha(binary) == manifest['binary_sha256']
    for name, digest in manifest['sources'].items():
        assert sha(ROOT/name) == digest, name
    check_transport.BINARY, check_transport.MAP = binary, binary.with_name('terminal.map')
    listing = check_transport.MAP.read_text()
    symbols = {name: (int(off,16), int(seg,16)) for seg, off, name in re.findall(
        r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$', listing, re.M|re.I)}
    cases = []

    def fresh():
        m = Redisplay()
        assert m.get('screen_attribute_row_bytes') == 80
        m.reject_viewer = False
        def forbidden(u, address, size, unused):
            if m.reject_viewer:
                assert address != m.symbols['_redisplay_event_impl'], 'Storage entered viewer C'
        m.uc.hook_add(UC_HOOK_CODE, forbidden)
        m.storage = b'\xa5'*63494
        m.uc.mem_write(m.symbols['redisplay_snapshot'], m.storage)
        m.frames = b'\x5a'*16000
        m.uc.mem_write(m.symbols['redisplay_live'], m.frames)
        return m

    def untouched(m):
        assert bytes(m.uc.mem_read(m.symbols['redisplay_snapshot'],63494)) == m.storage
        assert bytes(m.uc.mem_read(m.symbols['redisplay_live'],16000)) == m.frames

    def far(m, name):
        off, seg = symbols[name]
        u = m.uc
        stub = b'\x9a'+struct.pack('<HH',off,seg+m.base_segment)+b'\xf4'
        u.mem_write(0xe0000,stub)
        done = []
        def stop(u, address, size, unused):
            if address == 0xe0005:
                done.append(True)
                u.emu_stop()
        hook = u.hook_add(UC_HOOK_CODE,stop)
        registers = [(UC_X86_REG_AX,0x4321),(UC_X86_REG_BX,0x9876),
                     (UC_X86_REG_CX,0x4567),(UC_X86_REG_DX,0xabcd),
                     (UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),
                     (UC_X86_REG_DI,0x5678),(UC_X86_REG_ES,0xb800),
                     (UC_X86_REG_DS,m.ds),(UC_X86_REG_SS,m.ds)]
        sp = m.offset('terminal_stack_top')-64
        for reg, value in registers:
            u.reg_write(reg,value)
        for reg, value in [(UC_X86_REG_CS,0xe000),(UC_X86_REG_IP,0),
                           (UC_X86_REG_SP,sp),(UC_X86_REG_EFLAGS,0x202)]:
            u.reg_write(reg,value)
        try:
            u.emu_start(0xe0000,0,count=100000)
        finally:
            u.hook_del(hook)
        assert done and u.reg_read(UC_X86_REG_SP)==sp, name
        for reg, value in registers:
            assert u.reg_read(reg)==value, (name,reg)
        return bool(u.reg_read(UC_X86_REG_EFLAGS)&1)

    def record(label):
        cases.append(dict(case=label,passed=True))

    owners = ['_redisplay_active','_redisplay_live_ready','_redisplay_export_pending',
              '_redisplay_search_pending','_command_menu_active','terminal_transfer_pending',
              'terminal_transfer_active','terminal_program_pending','terminal_program_active',
              'terminal_macro_active','terminal_monitor_active','terminal_controller_active',
              'terminal_ansi_wait_active','terminal_snapshot_active','uart_break_hold',
              'terminal_parser_active']
    for name in owners:
        m = fresh()
        m.put(name,1)
        assert far(m,'terminal_chat_storage_acquire')
        assert m.get('_redisplay_active') == (1 if name=='_redisplay_active' else 0)
        untouched(m)
        record('refuse-'+name)
    for name in ('terminal_browser_screen_owned','terminal_editor_screen_owned'):
        m = fresh()
        m.uc.mem_write(m.symbols[name],b'\x01')
        assert far(m,'terminal_chat_storage_acquire') and not m.get('_redisplay_active')
        untouched(m)
        record('refuse-'+name)
    for field, value in [('screen_attribute_row_bytes',132),('screen_attribute_row_bytes',40),
                         ('screen_video_row_bytes',264),('screen_viewport_enabled',1),
                         ('text_video_segment',0xb000),('text_cga_status_port',0x3da),
                         *[('connection_state',v) for v in (1,2,3,4,5,7,65535)]]:
        m = fresh()
        m.put(field,value)
        assert far(m,'terminal_chat_storage_acquire') and not m.get('_redisplay_active')
        untouched(m)
        record('refuse-'+field+'-'+str(value))
    for connected in (0,6):
        m = fresh()
        m.put('connection_state',connected)
        m.reject_viewer = True
        for cycle in range(8):
            assert not far(m,'terminal_chat_storage_acquire') and m.get('_redisplay_active')==2
            assert far(m,'terminal_chat_storage_acquire') and m.get('_redisplay_active')==2
            for entry in ('terminal_redisplay_before','terminal_redisplay_idle','terminal_redisplay_stop'):
                m.call(entry)
                assert m.get('_redisplay_active')==2
            for key in (0,27,13,0x2c00,0x1800,0x1e00,0x2f00,0x2000,0xffff):
                m.call('terminal_redisplay_key',ax=key)
                assert m.uc.reg_read(UC_X86_REG_EFLAGS)&1 and m.get('_redisplay_active')==2
            assert m.call('terminal_directory_choose')==2
            assert m.call('terminal_directory_edit',[0])==0
            m.call('terminal_snapshot_start')
            assert not m.get('terminal_snapshot_active')
            assert m.call('reset_bank_call',ax=1)==1
            assert m.call('terminal_program_start',ax=m.offset('terminal_program_command'))==2
            assert not m.get('terminal_program_pending')
            untouched(m)
            assert not far(m,'terminal_chat_storage_release') and not m.get('_redisplay_active')
            assert far(m,'terminal_chat_storage_release')
            record('lifetime-'+str(connected)+'-'+str(cycle))
    for value in (0,1,3,65535):
        m = fresh()
        m.put('_redisplay_active',value)
        assert far(m,'terminal_chat_storage_release') and m.get('_redisplay_active')==value
        untouched(m)
        record('release-not-owner-'+str(value))
    m = fresh()
    assert not far(m,'terminal_chat_storage_acquire')
    assert not far(m,'terminal_chat_storage_release')
    m.call('terminal_redisplay_key',ax=0x2c00,limit=3000000)
    assert m.get('_redisplay_active')==1
    assert far(m,'terminal_chat_storage_acquire') and far(m,'terminal_chat_storage_release')
    m.call('terminal_redisplay_key',ax=27,limit=3000000)
    assert not m.get('_redisplay_active')
    assert not far(m,'terminal_chat_storage_acquire')
    assert not far(m,'terminal_chat_storage_release')
    record('normal-viewer-after-release-and-owner-refusal')
    m = fresh()
    assert not far(m,'terminal_chat_storage_acquire')
    assert not far(m,'terminal_chat_storage_release')
    for key in (ord('`'),9):
        m.call('terminal_redisplay_key',ax=key,limit=3000000)
        assert m.get('_redisplay_active')==1
    assert m.call('terminal_redisplay_key',ax=ord('D'),limit=3000000)==0xf600
    assert not m.get('_redisplay_active') and not m.get('_command_menu_active') and not m.tx
    record('browser-connection-redial-action-after-release')
    if manifest['experimental_aspect_snapshot_lease']:
        import check_aspect_parent_process as parent_model
        from check_snapshot_lease import Parent
        parent_model.OUT=binary.parent
        m=Parent(manifest['memory_layout'])
        assert m.operation(9,1)==0
        m.put('_redisplay_active',2)
        assert m.operation(17,4000)==10 and not m.get('render_snapshot_owned')
        record('aspect-frame-lease-defensively-refuses-chat-owner')
    names = ['standalone/check_chat_storage_live.py','standalone/check_redisplay_live.py',
             'standalone/check_terminal_reset_live.py','standalone/check_line_edit_live.py',
             'standalone/check_transport.py','standalone/dos_image.py',
             'standalone/check_snapshot_lease.py','standalone/check_aspect_parent_process.py',
             'standalone/check_aspect_program_client.py']
    out.mkdir(parents=True)
    report = dict(passed=True,binary_sha256=sha(binary),cases=cases,lease_cycles=16,
                  snapshot_index_bytes=63494,frame_bytes=16000,new_near_state_bytes=0,
                  sources={n:sha(ROOT/n) for n in names},scope=__doc__+
                  ' Actual linked acquire/release, common view admission and competing frontend guards; register/stack ABI, exact frozen storage/frames, explicit retirement and normal viewer reentry. Foreground caller DS=SS; no loader-under-lease, all internal entrypoints, real DOS/BIOS/UART or full Chat claim.')
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS',len(cases),'linked Chat storage cases;',16,'lease cycles')


if __name__ == '__main__':
    main()
