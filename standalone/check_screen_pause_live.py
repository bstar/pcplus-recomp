#!/usr/bin/env python3
"""Execute linked pause/menu/UART/render code; BIOS, UART and DOS are modeled."""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
import check_transport as transport
from check_recording_ui_live import UI
from check_recording_rx_live import ordinary

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--terminal', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
a.output.mkdir(parents=True, exist_ok=False)
transport.BINARY = a.terminal.resolve()
transport.MAP = a.terminal.parent / 'terminal.map'
manifest = json.loads((a.terminal.parent / 'manifest.json').read_text())
assert manifest['experimental_screen_pause']
cases = []


def check(name, operation):
    operation()
    cases.append(dict(case=name, passed=True))
    print(name, 'PASS', flush=True)


def drive(m, key=ord('x'), *, menu=False, stalled=False, quit=False, deferred=False):
    before = bytes(m.uc.mem_read(0xb8000, 4000))
    shape = m.shape
    cursor = (m.get('screen_cursor_row'), m.get('screen_cursor_column'))
    polls = []
    def hardware(u, address, size, data):
        if address != m.symbols['terminal_pause_poll_far']:
            return
        assert m.get('terminal_screen_pause_active') == 1
        video = bytes(u.mem_read(0xb8000, 4000))
        assert video[:3840] == before[:3840] and b'Screen paused.' in video[3840::2]
        assert m.shape == shape | 0x2000
        polls.append(address)
        if len(polls) == 1:
            m.rx.extend(b'AFTER\x1b[6n')
        if len(polls) == 4:
            if quit:
                m.put('terminal_quit', 1)
            else:
                m.keys.extend((key, ord('z')))
    hook = m.uc.hook_add(UC_HOOK_CODE, hardware)
    if menu:
        m.key(0x2c00)
        assert m.get('_command_menu_active')
    if deferred:
        m.call('terminal_poll_io', limit=1000000)
    else:
        m.key(0x3100)
    m.uc.hook_del(hook)
    assert len(polls) >= 4 and not m.get('terminal_screen_pause_active')
    assert bytes(m.uc.mem_read(0xb8000, 4000)) == before and m.shape == shape
    assert (m.get('screen_cursor_row'), m.get('screen_cursor_column')) == cursor
    assert not m.get('_command_menu_active') and not m.get('_redisplay_active')
    assert not m.get('terminal_local_control_status') and not m.files and not m.handles
    assert bytes(m.tx) == (b'' if stalled else b'\x13\x11')
    if quit:
        assert not m.keys
        return
    assert list(m.keys) == [ord('z')], 'Resume key was not consumed exactly once'
    m.thre = True
    m.cts = True
    m.put('uart_tx_paused', 0)
    m.call('terminal_poll_io')
    ordinary(m, b'')
    m.drain()
    assert b'AFTER' in m.text()
    assert bytes(m.tx).startswith(b'\x11' if stalled else b'\x13\x11')
    assert bytes(m.tx).endswith(b'z\x1b[1;6R'), bytes(m.tx)
    assert not m.get('terminal_quit') and not m.get('terminal_deferred_count')


for key in (ord('x'), 27, 0x2d00, 0x4800):
    for menu in (False, True):
        check('consume-one-resume-key-' + hex(key) + '-menu-' + str(menu), lambda key=key, menu=menu: drive(UI(), key, menu=menu))


def pressure(kind):
    m = UI()
    if kind == 'THRE':
        m.thre = False
    elif kind == 'CTS':
        m.put('uart_hardware_flow', 1)
        m.cts = False
    else:
        m.put('uart_tx_paused', 1)
    drive(m, stalled=kind == 'THRE')


for kind in ('THRE', 'CTS', 'peer-XOFF'):
    check('responsive-under-' + kind, lambda kind=kind: pressure(kind))
check('external-quit-restores-view-and-resumes-peer', lambda: drive(UI(), quit=True))


def replay():
    m = UI()
    m.put('terminal_parser_active', 1)
    m.key(0x3100)
    assert m.get('terminal_deferred_count') == 1 and not m.tx
    m.put('terminal_parser_active', 0)
    drive(m, deferred=True)


check('parser-deferred-pause-runs-once-after-owner-release', replay)


def carrier_notice():
    m = UI()
    m.advance_ticks = True
    m.put('connection_enabled', 1, 1)
    m.put('connection_state', 6)
    m.put('connection_status', 1)
    # The private "seen" byte immediately follows enabled in the owned source.
    # Start online with a previously observed DCD high; hardware falls below.
    m.uc.mem_write(m.symbols['connection_enabled'] + 1, b'\x01')
    before = bytes(m.uc.mem_read(0xb8000, 4000))
    polls = []
    def hardware(u, address, size, data):
        if address != m.symbols['terminal_pause_poll_far']:
            return
        polls.append(address)
        assert b'Screen paused.' in m.text()[-80:]
        m.tick += 5  # Give the real DCD low-qualification deadline BIOS time.
        if len(polls) == 2:
            m.carrier = False
        if len(polls) == 12:
            m.keys.append(ord('x'))
    hook = m.uc.hook_add(UC_HOOK_CODE, hardware)
    m.key(0x3100)
    m.uc.hook_del(hook)
    assert m.get('connection_state') == 0 and m.get('connection_status') == 6
    assert b'Screen paused.' not in m.text() and bytes(m.tx) == b'\x13\x11'
    assert bytes(m.uc.mem_read(0xb8000, 3840)) == before[:3840]
    m.call('terminal_connection_notice_restore')
    assert bytes(m.uc.mem_read(0xb8000, 4000)) == before, 'Pause prompt contaminated the notice underlay'


check('carrier-loss-notice-waits-for-row-release-and-restores-real-underlay', carrier_notice)


for blocked in (False, True):
    def shutdown(blocked=blocked):
        m = UI()
        m.put('uart_software_flow', 0)
        m.put('uart_flow_pending', 17, 1)
        m.thre = not blocked
        m.advance_ticks = True
        m.call('terminal_release_flow', limit=1000000)
        assert bool(m.get('terminal_cleanup_flow_failed')) == blocked
        assert m.get('terminal_exit_code') == (11 if blocked else 0)
        assert bytes(m.tx) == (b'' if blocked else b'\x11')
    check('manual-resume-shutdown-with-SOFT-disabled-blocked-' + str(blocked), shutdown)


for field in ('terminal_parser_active', 'terminal_macro_active', 'terminal_program_pending', 'terminal_program_active',
              'terminal_transfer_pending', 'terminal_transfer_active', 'terminal_aspect_active', 'terminal_ansi_wait_active',
              'terminal_snapshot_active', 'uart_break_hold', '_redisplay_active', '_command_menu_active',
              'terminal_monitor_active', 'terminal_controller_active'):
    # Only admission is exercised here; each owner-specific UI dispatch is
    # separately covered by existing local-control and owner regressions.
    def deferred_only(field=field):
        m = UI()
        m.put(field, 1)
        segment = next(c['relative_segment'] for c in manifest['memory_layout']['code_segments'] if c['name'] == 'CONFIG_CODE')
        sp = m.offset('terminal_stack_top') - 4
        m.uc.mem_write(m.data_base + sp, struct.pack('<HH', m.return_offset, m.code_segment))
        for r, v in ((UC_X86_REG_CS, m.base_segment + segment), (UC_X86_REG_DS, m.ds), (UC_X86_REG_SS, m.ds),
                     (UC_X86_REG_SP, sp), (UC_X86_REG_AX, 0x3100)):
            m.uc.reg_write(r, v)
        before = bytes(m.uc.mem_read(0xb8000, 4000))
        m.returned = False
        m.uc.emu_start(m.symbols['terminal_local_control_key'], 0, count=100000)
        assert m.returned and m.get('terminal_deferred_count') == 1 and m.get('terminal_local_control_status') == 1
        assert not m.tx and bytes(m.uc.mem_read(0xb8000, 4000)) == before
    check('defer-for-' + field, deferred_only)


for field, value in (('text_video_segment', 0xb000), ('screen_video_row_bytes', 264), ('screen_attribute_row_bytes', 132), ('screen_viewport_enabled', 1),
                     ('ui_flow_suppressed', 1), ('ui_flow_suppressed', 65535),
                     ('ui_flow_region_cells', 79), ('ui_flow_video_base', 3680),
                     ('ui_flow_coordinate_base', 0x1700), ('screen_columns', 40)):
    def unsupported(field=field, value=value):
        m = UI()
        m.put(field, value)
        before = bytes(m.uc.mem_read(0xb8000, 4000))
        m.key(0x3100)
        assert m.get('terminal_local_control_status') == 3 and not m.get('terminal_screen_pause_active')
        assert not m.tx and bytes(m.uc.mem_read(0xb8000, 4000)) == before
    check('refuse-unsupported-' + field, unsupported)

for field, value in (('height', 49), ('mode', 7), ('page', 1), ('columns', 40)):
    def unsupported_bios(field=field, value=value):
        m = UI()
        if field == 'height':
            m.uc.mem_write(0x484, bytes([value]))
        else:
            setattr(m, field, value)
        before = bytes(m.uc.mem_read(0xb8000, 4000))
        m.key(0x3100)
        assert m.get('terminal_local_control_status') == 3 and not m.tx
        assert bytes(m.uc.mem_read(0xb8000, 4000)) == before
    check('refuse-unsupported-BIOS-' + field, unsupported_bios)

for shape in (0x0607, 0x2000, 0x260f):
    def cursor(shape=shape):
        m = UI()
        m.shape = shape
        drive(m)
    check('restore-incoming-cursor-shape-' + hex(shape), cursor)

report = dict(passed=True, terminal_sha256=hashlib.sha256(a.terminal.read_bytes()).hexdigest(), cases=cases, scope=__doc__ + ' No physical/SIP acceptance or unbounded peer-pressure guarantee.')
(a.output / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
