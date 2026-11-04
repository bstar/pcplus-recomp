#!/usr/bin/env python3
"""Linked ASPECT admission/report/callback paths with an owned callback ABI peer.

BIOS/UART/DOS setup modeled. Actual child execution is separate DOS evidence.
"""
import argparse
import hashlib
import json
import struct
import subprocess
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
import check_transport as transport

ROOT = Path(__file__).resolve().parents[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--terminal', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    binary, out = a.terminal.resolve(), a.output.resolve()
    assert out.is_relative_to(ROOT / 'build')
    out.mkdir(parents=True, exist_ok=False)
    manifest = json.loads((binary.parent / 'manifest.json').read_text())
    assert manifest['experimental_window_size_report'] and sha(binary) == manifest['binary_sha256']
    for n, h in manifest['sources'].items():
        assert sha(ROOT / n) == h, n
    transport.BINARY, transport.MAP = binary, binary.parent / 'terminal.map'
    from check_display_transaction_live import Transaction
    from check_window_size_report_live import state
    fixture = ROOT / 'standalone/size_report_callback_fixture.asm'
    callback = out / 'CALLBACK.BIN'
    subprocess.run(['nasm', '-fbin', str(fixture), '-o', str(callback)], check=True)
    # Private owned memory outside the loaded/retained application extent.
    segment = 0x9800
    cases = []

    def fresh(rows=25, hidden=0, profile=6, fail=65535):
        m = Transaction()
        assert m.base + manifest['memory_layout']['minimum_allocated_module_bytes'] < segment * 16
        m.saved(hidden, 2, rows, 0)
        assert m.invoke(entry='_terminal_display_apply_saved') == 0
        m.put('csi_terminal_id', profile)
        for name, value in dict(terminal_program_active=1, terminal_program_kind=4,
                                terminal_parser_active=1, terminal_aspect_active=1,
                                ansi_private=0, ansi_secondary=0, ansi_parameter_count=1,
                                ansi_parameters=18).items():
            m.put(name, value)
        m.uc.mem_write(segment * 16 + 0x100, callback.read_bytes())
        m.uc.mem_write(segment * 16 + 0x80, struct.pack('<3H', 0, fail, 0))
        # Maintained mutable bridge fields, not instructions. Assert the public
        # source layout from which the unexported callback/count offsets derive.
        bridge = (ROOT / 'src/aspect/resident_bridge.asm').read_text()
        assert 'rb_busy: dw 0\nrb_ds: dw 0\nrb_low: dw 0\nrb_top: dw 0\nrb_body: dw 0\nrb_callback: dd 0' in bridge
        m.uc.mem_write(m.symbols['resident_bridge_busy'] + 10, struct.pack('<2H', 0x100, segment))
        m.uc.mem_write(m.symbols['render_started'], struct.pack('<2H', 0, 4096))
        return m

    def invoke(m):
        u = m.uc
        stopped = []
        def observe(cpu, address, size, data):
            if address == m.symbols['terminal_render_typed_abort']:
                stopped.append(cpu.reg_read(UC_X86_REG_AX))
                cpu.emu_stop()
        handle = u.hook_add(UC_HOOK_CODE, observe)
        seg, _ = m.entries['terminal_window_size_report']
        sp = m.offset('terminal_stack_top') - 4
        u.mem_write(m.data_base + sp, struct.pack('<2H', m.return_offset, m.code_segment))
        registers = [(UC_X86_REG_CS, m.base_segment + seg), (UC_X86_REG_DS, m.ds),
                     (UC_X86_REG_SS, m.ds), (UC_X86_REG_SP, sp), (UC_X86_REG_BP, 0xbabe),
                     (UC_X86_REG_SI, 0x1234), (UC_X86_REG_DI, 0x5678), (UC_X86_REG_EFLAGS, 0x202)]
        for r, value in registers:
            u.reg_write(r, value)
        m.returned = False
        try:
            u.emu_start(m.symbols['terminal_window_size_report'], 0, count=1000000)
        finally:
            u.hook_del(handle)
        if not stopped:
            assert m.returned and u.reg_read(UC_X86_REG_SP) == sp + 4
            for r, value in registers[1:3] + registers[4:7]:
                assert u.reg_read(r) == value
        count = struct.unpack('<H', u.mem_read(segment * 16 + 0x80, 2))[0]
        return bytes(u.mem_read(segment * 16 + 0x1000, count)), stopped

    for rows in (25, 28, 43, 50):
        for hidden in (0, 1):
            for profile in (4, 6):
                m = fresh(rows, hidden, profile)
                before = state(m)
                ring = bytes(m.uc.mem_read(m.symbols['terminal_tx_buffer'], 1024))
                data, stopped = invoke(m)
                assert data == f'\x1b[8;{rows - (not hidden)};80t'.encode() and not stopped
                assert state(m) == before and not m.get('terminal_tx_count') and not m.tx
                assert bytes(m.uc.mem_read(m.symbols['terminal_tx_buffer'], 1024)) == ring
                cases.append(dict(case=f'rows-{rows}-hidden-{hidden}-profile-{profile}', passed=True))
    for name, value, abort in [('terminal_program_kind', 0, [3]), ('terminal_parser_active', 0, [3]),
                               ('terminal_parser_active', 17, [3]), ('terminal_program_pending', 1, [3]),
                               ('connection_state', 2, [3]), ('terminal_aspect_active', 2, []),
                               ('terminal_quit', 1, []), ('terminal_transfer_active', 1, []),
                               ('_terminal_row_geometry_active', 1, [])]:
        m = fresh()
        m.put(name, value)
        data, stopped = invoke(m)
        assert not data and stopped == abort and not m.get('terminal_tx_count')
        cases.append(dict(case=f'refuse-{name}-{value}', typed_abort=abort, passed=True))
    expected = b'\x1b[8;24;80t'
    for index in range(len(expected)):
        m = fresh(fail=index)
        before = state(m)
        data, stopped = invoke(m)
        assert data == expected[:index] and stopped == [9] and state(m) == before
        assert not m.get('terminal_tx_count') and not m.tx
        cases.append(dict(case=f'callback-serial-failure-after-{index}', typed_abort=9, passed=True))
    sources = ['standalone/check_aspect_size_report_live.py', 'standalone/size_report_callback_fixture.asm',
               'standalone/check_window_size_report_live.py', 'standalone/check_display_transaction_live.py']
    result = dict(passed=True, inputs=len(cases), cases=cases, terminal_sha256=sha(binary),
                  manifest_sha256=sha(binary.parent / 'manifest.json'),
                  sources={n: sha(ROOT / n) for n in sources}, scope=__doc__ +
                  ' Real parent preflight, report and resident bridge dispatch execute to an authored far callback. Failure cases stop at the actual typed-abort entry; they do not claim subsequent unwind/cleanup. No product instructions patched.')
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print('PASS attached size-report paths:', len(cases))


if __name__ == '__main__':
    main()
