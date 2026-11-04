#!/usr/bin/env python3
"""Compare linked banked/unbanked keyboard execution; model only OS/hardware."""
import argparse
import hashlib
import json
from pathlib import Path
from unicorn.x86_const import UC_X86_REG_AX
import check_transport as transport
from check_recording_ui_live import UI as BaseUI
from check_recording_rx_live import ordinary


class UI(BaseUI):
    def interrupt(self, u, n, d):
        if n == 0x10 and u.reg_read(UC_X86_REG_AX) >> 8 == 1:
            return  # BIOS cursor shape; framebuffer and cursor position remain real.
        super().interrupt(u, n, d)


FIELDS = '''terminal_quit terminal_exit_code terminal_tx_count terminal_tx_head
terminal_tx_tail terminal_deferred_count terminal_menu_pending terminal_macro_active
terminal_program_pending terminal_program_active terminal_transfer_pending
terminal_transfer_active terminal_aspect_active terminal_ansi_wait_active
terminal_ansi_wait_cancel terminal_snapshot_active terminal_monitor_active
terminal_controller_active uart_break_hold _redisplay_active _command_menu_active
connection_state modes_value_1d1a screen_cursor_column screen_cursor_row
terminal_local_control_status terminal_sink_398a_enabled terminal_cr_adds_lf'''.split()


def run(binary, keys, setup):
    transport.BINARY = binary
    transport.MAP = binary.parent / 'terminal.map'
    m = UI()
    # Match main's initialized history store; the loader-only fixture does not
    # execute main and its far BSS can otherwise contain unrelated image bytes.
    m.uc.mem_write(m.symbols['terminal_history_buffer'], bytes(63000))
    ordinary(m, b'BEFORE\x1b[31m RED\x1b[0m')
    if setup == 'macro':
        m.put('terminal_macro_active', 1)
    elif setup == 'parser':
        m.put('terminal_parser_active', 1)
    elif setup == 'wait':
        m.put('terminal_ansi_wait_active', 1)
    elif setup == 'cts':
        m.put('uart_hardware_flow', 1)
        m.cts = False
    for key in keys:
        m.keys.append(key)
        if key == 0x6800:
            m.keys.append(27)  # Actual synchronous capture filename prompt.
        m.call('terminal_poll_io', limit=1000000)
    return dict(
        values={n: m.get(n) for n in FIELDS if n in m.symbols},
        screen=bytes(m.uc.mem_read(0xb8000, 4000)).hex(),
        history=hashlib.sha256(m.uc.mem_read(m.symbols['terminal_history_buffer'], 63000)).hexdigest(),
        fifo=bytes(m.uc.mem_read(m.symbols['terminal_deferred_count'], 70)).hex(),
        tx=m.tx, bios_remaining=list(m.keys),
        files={n: bytes(v).hex() for n, v in m.files.items()},
        handles=m.handles, positions=m.positions,
    )


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline', type=Path, required=True)
    p.add_argument('--terminal', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=False)
    before = json.loads((a.baseline.parent / 'manifest.json').read_text())
    after = json.loads((a.terminal.parent / 'manifest.json').read_text())
    assert not before.get('experimental_keyboard_bank') and after['experimental_keyboard_bank']
    cases = []
    scenarios = [('ascii-%02x' % key, [key], '') for key in range(256)]
    scenarios += [('scan-%02x' % key, [key << 8], '') for key in range(256)]
    for setup in ('macro', 'parser', 'wait', 'cts'):
        for key in (ord('a'), 27, 0x2c00, 0x2d00, 0x2300, 0x2e00, 0x1600, 0x1200):
            scenarios.append((setup + '-' + hex(key), [key], setup))
    scenarios += [
        ('menu-clear', [0x2c00, 0x2e00], ''),
        ('menu-reset', [0x2c00, 0x1600], ''),
        ('menu-duplex-echo', [0x2c00, 0x1200, ord('x')], ''),
        ('menu-escape', [0x2c00, 27], ''),
        ('duplex-roundtrip', [0x1200, ord('x'), 0x1200, ord('y')], ''),
        ('macro-cancel', [ord('a'), 27, ord('b')], 'macro'),
        ('wait-cancel', [ord('a'), 27], 'wait'),
    ]
    for name, keys, setup in scenarios:
        try:
            original = run(a.baseline, keys, setup)
            banked = run(a.terminal, keys, setup)
        except Exception as error:
            raise AssertionError('Keyboard scenario failed: ' + name) from error
        differing = [k for k in original if original[k] != banked[k]]
        assert not differing, (name, differing)
        cases.append(dict(case=name, passed=True))
        if len(cases) % 64 == 0:
            print(len(cases), 'keyboard comparisons PASS', flush=True)
    report = dict(passed=True, baseline_sha256=hashlib.sha256(a.baseline.read_bytes()).hexdigest(),
                  terminal_sha256=hashlib.sha256(a.terminal.read_bytes()).hexdigest(), cases=cases,
                  scope=__doc__ + ' No physical DOS/modem acceptance; unavailable commands remain unavailable.')
    (a.output / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
    print('PASS', len(cases), 'linked keyboard comparisons', flush=True)


if __name__ == '__main__':
    main()
