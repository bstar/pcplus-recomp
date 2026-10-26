#!/usr/bin/env python3
"""Check compiled cross-bank cdecl frames and reject damaged MZ call bindings.

Only BIOS/UART/DOS boundaries are modeled. The observer reads real machine
state; it never changes instructions, return frames or product state.
"""
import argparse
import hashlib
import json
import struct
import tempfile
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import (UC_X86_REG_CS, UC_X86_REG_SS, UC_X86_REG_DS,
    UC_X86_REG_BP, UC_X86_REG_SI, UC_X86_REG_DI, UC_X86_REG_SP)
import check_transport as transport
from terminal_memory import inspect_terminal_memory


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--terminal', type=Path, required=True)
    args = parser.parse_args()
    binary = args.terminal.resolve()
    listing = binary.parent / 'terminal.map'
    manifest = json.loads((binary.parent / 'manifest.json').read_text())
    assert manifest['experimental_original_reference']
    assert sha(binary) == manifest['binary_sha256']
    for name, digest in manifest['sources'].items():
        assert sha(transport.ROOT / name) == digest, name
    layout = inspect_terminal_memory(binary, listing)
    sites = layout['command_menu_banked_call_sites']
    assert len(sites) == 2 and not layout['recording_UI_optimized_sites']
    regions = {c['name']: c for c in layout['code_segments']}
    assert layout['command_menu_code_segment'] == regions['REFERENCE_CODE']['relative_segment']
    assert regions['CONFIG_CODE']['bytes'] < 54000
    assert layout['near_bytes'] == 64096 and layout['history_bytes'] == 63000

    # The same full memory validator must reject independently damaged far
    # targets and omitted loader relocations at both compiled menu call sites.
    image = binary.read_bytes()
    header = struct.unpack_from('<14H', image)
    module = header[4] * 16
    negatives = []
    with tempfile.TemporaryDirectory(prefix='pcplus-menu-bank-') as tmp:
        damaged = Path(tmp) / 'DAMAGED.EXE'
        for site in sites:
            reloc = next(header[12] + 4 * i for i in range(header[3])
                if (lambda pair: pair[0] + 16 * pair[1])(
                    struct.unpack_from('<HH', image, header[12] + 4 * i)) == site + 3)
            for kind in ('target', 'relocation'):
                data = bytearray(image)
                if kind == 'target':
                    data[module + site + 1] ^= 1
                else:
                    struct.pack_into('<HH', data, reloc, 0, 0)
                damaged.write_bytes(data)
                try:
                    inspect_terminal_memory(damaged, listing)
                except AssertionError:
                    negatives.append(dict(site=site, damage=kind, rejected=True))
                else:
                    raise AssertionError(('Damaged menu binding accepted', site, kind))

    transport.BINARY = binary
    transport.MAP = listing
    from check_recording_ui_live import UI
    from check_recording_rx_live import ordinary
    UI.browser_key = 0x2960
    machine = UI()
    pending, frames = [], []
    registers = (UC_X86_REG_BP, UC_X86_REG_SI, UC_X86_REG_DI,
                 UC_X86_REG_DS, UC_X86_REG_SS)
    targets = {machine.symbols[n]: n for n in
               ('_command_menu_event', '_recording_ui_ready')}

    def observe(uc, address, size, user):
        if pending and address == pending[-1]['return_address']:
            frame = pending.pop()
            assert uc.reg_read(UC_X86_REG_SP) == frame['sp'] + 4, frame
            assert [uc.reg_read(r) for r in registers] == frame['registers'], frame
            frame['returned'] = True
            frames.append(frame)
        if address not in targets:
            return
        sp = uc.reg_read(UC_X86_REG_SP)
        assert uc.reg_read(UC_X86_REG_DS) == uc.reg_read(UC_X86_REG_SS) == machine.ds
        ip, cs = struct.unpack('<HH', uc.mem_read(machine.data_base + sp, 4))
        name = targets[address]
        expected = regions['CONFIG_CODE' if name == '_command_menu_event' else 'REFERENCE_CODE']['relative_segment']
        assert cs == machine.base_segment + expected, (name, cs, expected)
        frame = dict(target=name, sp=sp, return_address=cs * 16 + ip,
                     registers=[uc.reg_read(r) for r in registers])
        if name == '_command_menu_event':
            event, key, off, seg = struct.unpack('<4H', uc.mem_read(machine.data_base + sp + 4, 8))
            assert seg * 16 + off == machine.symbols['redisplay_view']
            frame.update(event=event, key=key)
        pending.append(frame)

    machine.uc.hook_add(UC_HOOK_CODE, observe)
    machine.key(0x2c00)
    machine.key(0x4d00)
    machine.key(0x5000)
    machine.key(0x5000)
    machine.key(0x3b00)
    machine.key(27)
    machine.key(0x2960)
    machine.key(27)
    machine.key(0x1300)
    machine.key(13)
    assert machine.field('state') == 1
    ordinary(machine, b'Name? ')
    for byte in b'bstar':
        machine.key(byte)
    machine.drain()
    machine.key(0x1300)
    assert machine.field('published') == 1
    machine.key(27)
    machine.key(0x2c00)
    machine.call('terminal_redisplay_stop')
    assert not pending and not machine.get('_redisplay_active')
    assert not machine.get('_command_menu_active') and not machine.handles
    assert not machine.get('terminal_quit')
    assert b'transmitraw "6273746172"' in machine.files['PCPLUS.ASP']
    assert {f['event'] for f in frames if f['target'] == '_command_menu_event'} == {0, 1, 4}
    assert sum(f['target'] == '_recording_ui_ready' for f in frames) == 2
    result = dict(passed=True, binary_sha256=sha(binary),
        cross_bank_frames=frames, rejected_bindings=negatives,
        near_bytes=layout['near_bytes'], history_bytes=layout['history_bytes'],
        code_bytes={name: regions[name]['bytes'] for name in ('_TEXT', 'CONFIG_CODE', 'REFERENCE_CODE')},
        inputs={str(p.relative_to(transport.ROOT)): sha(p) for p in
            (Path(__file__).resolve(), transport.ROOT / 'standalone/terminal_memory.py')},
        scope=__doc__ + ' Tests actual menu open/key/stop returns, shared far frame, both recorder admission calls, script publication and nested bank returns. Hardware/DOS modeled; actual DOS and BBS checks remain separate.')
    output = binary.parent / 'command-bank-checks.json'
    output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(passed=True, observed_frames=len(frames), rejected_bindings=len(negatives), output=str(output))))


if __name__ == '__main__':
    main()
