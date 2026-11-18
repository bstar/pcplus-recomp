#!/usr/bin/env python3
"""Source-only parent local-screen platform and namespaced native frame kernels."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import struct

ROOT = Path(__file__).resolve().parents[1]
NATIVE = {
    'program_ui': ('scroll', 'cell_offset', 'fill', 'snow_cell'),
    'notice_window': ('frame', 'cell', 'horizontal', 'vertical', 'write', 'stride'),
}
ALIASES = {
    'display_scroll': 'terminal_screen_native_scroll',
    'display_cell_offset': 'terminal_screen_native_offset',
    'display_columns': 'screen_columns',
    'display_fill': 'terminal_screen_native_fill',
    'display_snow_cell': 'terminal_screen_native_snow',
    'display_segment': 'text_video_segment',
    'display_status_port': 'text_cga_status_port',
    'window_frame': 'terminal_screen_native_frame',
    'window_cell': 'terminal_screen_native_cell',
    'window_horizontal': 'terminal_screen_native_horizontal',
    'window_vertical': 'terminal_screen_native_vertical',
    'window_write': 'terminal_screen_native_write',
    'window_stride': 'terminal_screen_native_stride',
    'window_offset8': 'terminal_screen_native_offset',
    'window_fill': 'terminal_screen_native_fill',
    'window_snow_cell': 'terminal_screen_native_snow',
    'window_state_7a78': 'text_video_segment',
    'window_state_7a8e': 'text_cga_status_port',
    'window_state_7a7a': 'screen_video_row_bytes',
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build(output):
    """Return (objects,sources); read no original executable or analysis image."""
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    include = '-I'+str(ROOT/'reconstruction/uart')+'/'
    sources = [Path(__file__).resolve(), ROOT/'reconstruction/uart/encodings.inc']
    objects = []
    for group, names in NATIVE.items():
        provenance = ROOT/'reconstruction'/group/'provenance.json'
        sources.append(provenance)
        units = {Path(u['file']).stem: u for u in json.loads(provenance.read_text())['units']}
        for name in names:
            unit = units[name]
            source = ROOT/unit['file']
            sources.append(source)
            stem = 'screen-platform-'+group+'-'+name
            binary = output/(stem+'.bin')
            subprocess.run(['nasm', '-fbin', include, str(source), '-o', str(binary)], check=True)
            assert len(binary.read_bytes()) == unit['bytes'] and sha(binary) == unit['sha256'], source
            obj = output/(stem+'.obj')
            define = 'PROGRAM_DISPLAY_OMF' if group == 'program_ui' else 'NOTICE_WINDOW_OMF'
            subprocess.run(['nasm', '-fobj', include, '-D'+define,
                '-D_TEXT=ASPECT_CODE', '-DCODE=FARCODE',
                *['-D'+key+'='+value for key, value in ALIASES.items()],
                str(source), '-o', str(obj)], check=True)
            objects.append(str(obj))
    source = ROOT/'src/terminal/script_screen_platform.asm'
    sources.append(source)
    obj = output/'screen-platform-adapters.obj'
    subprocess.run(['nasm', '-fobj', str(source), '-o', str(obj)], check=True)
    objects.append(str(obj))
    return objects, sources


def audit(map_path):
    """Require the new platform's public ABI in ASPECT_CODE and measure bridges."""
    text = Path(map_path).read_text()
    segments = {name: (int(seg, 16), int(off, 16), int(size, 16))
        for name, seg, off, size in re.findall(
            r'^(\w+)\s+\w+\s+\w+\s+([0-9a-f]+):([0-9a-f]+)\s+([0-9a-f]+)\s*$', text, re.M|re.I)}
    symbols = {name: (int(seg, 16), int(off, 16)) for seg, off, name in re.findall(
        r'^\s*([0-9a-f]+):([0-9a-f]+)[*+ ]+\s+(\w+)\s*$', text, re.M|re.I)}
    near, bank = segments['_TEXT'], segments['ASPECT_CODE']
    assert near[0] != bank[0], 'Proof requires distinct resident and platform CS values'
    for suffix in ('scroll', 'draw_box', 'clear_home', 'set_cursor', 'reset_attribute',
                   'read_attribute', 'write_attribute', 'home'):
        assert symbols['terminal_screen_'+suffix][0] == bank[0], suffix
    for suffix in ('scroll', 'frame', 'cell', 'horizontal', 'vertical', 'write',
                   'stride', 'offset', 'fill', 'snow'):
        assert symbols['terminal_screen_native_'+suffix][0] == bank[0], suffix
    first, last = (symbols['terminal_screen_resident_'+edge] for edge in ('begin', 'end'))
    assert first[0] == last[0] == near[0] and last[1]-first[1] == 23
    return dict(resident_bridge_bytes=23, platform_segment=bank[0],
        frame_glyphs='c9cdbbbabccdc8ba', near_DATA_bytes_added=0,
        frame_scope='Verified original startup glyphs; runtime frame selection is not implemented.')


def check(output, objects, sources):
    """Replay the linked platform/native kernels with declared BIOS boundaries."""
    from dos_image import DosImage
    from unicorn import UC_HOOK_CODE, UC_HOOK_INTR
    from unicorn.x86_const import (UC_X86_REG_AX, UC_X86_REG_BP, UC_X86_REG_BX,
        UC_X86_REG_CX, UC_X86_REG_DX, UC_X86_REG_SI, UC_X86_REG_DI, UC_X86_REG_ES,
        UC_X86_REG_DS, UC_X86_REG_SS, UC_X86_REG_CS, UC_X86_REG_IP, UC_X86_REG_SP, UC_X86_REG_EFLAGS)

    # The application supplies these imports. Execute the real ordinary cursor,
    # attribute reset, HOME, clear wrapper, video read and byte write. The clear
    # rectangle and HOME attribute-boundary interfaces are explicitly modeled;
    # their independent application owners are not reconstructed by this test.
    fixture = output/'screen-platform-fixture.asm'
    words = dict(screen_columns=80, text_video_segment=0xb800, text_cga_status_port=0,
        screen_video_row_bytes=160, screen_attribute_row_bytes=80,
        attributes_normal_value=7, attributes_current=0x70, csi_last_row=23,
        csi_last_column=79, csi_origin_row=2, screen_attribute_checks=0,
        screen_use_bios_cursor=1, screen_viewport_enabled=0, screen_viewport_left=52,
        screen_viewport_active=1, screen_viewport_offset=0, screen_viewport_right=79,
        screen_visible_column=0, screen_video_offset=0, screen_previous_column=0,
        screen_attribute_offset=0, screen_cursor_column=0, screen_previous_row=0,
        screen_cursor_row=0)
    fixture.write_text('''BITS 16
CPU 8086
GROUP SCREEN_PROBE_GROUP ASPECT_CODE
SEGMENT ASPECT_CODE public align=16 class=FARCODE use16
SEGMENT _TEXT public align=16 class=CODE use16
..start: ret
extern screen_set_cursor
global attribute_screen_set_cursor_far
attribute_screen_set_cursor_far: call screen_set_cursor
 retf
global csi_service_2530,screen_adjust_attribute_boundary
csi_service_2530: ret 8
screen_adjust_attribute_boundary: ret 4
global screen_viewport_enter,screen_viewport_leave,screen_viewport_refresh
screen_viewport_enter: ret
screen_viewport_leave: ret
screen_viewport_refresh: ret
GROUP DGROUP _DATA STACK
SEGMENT _DATA public align=16 class=DATA use16
'''+''.join('global '+name+'\n'+name+': dw '+str(value)+'\n' for name, value in words.items())+'''
SEGMENT STACK stack align=16 class=STACK use16
 resb 8192
global terminal_stack_top
terminal_stack_top:
''')
    fixture_obj = output/'screen-platform-fixture.obj'
    subprocess.run(['nasm', '-fobj', str(fixture), '-o', str(fixture_obj)], check=True)
    linked = [*objects, str(fixture_obj)]
    imports = [('attributes/reset', 'ATTRIBUTES_OMF'),
        ('terminal_services/clear_home', 'TERMINAL_SERVICES_OMF'),
        ('input_dispatch/home', 'INPUT_DISPATCH_OMF'),
        ('screen/set_cursor', 'SCREEN_OMF'), ('screen/cursor_pack', 'SCREEN_OMF'),
        ('screen/cursor_output', 'SCREEN_OMF'), ('ui_windows/read_byte', 'UI_WINDOWS_OMF'),
        ('text/char', 'TEXT_OMF')]
    # The CGA branch is linked too, but this replay admits direct output only.
    imports.append(('text/cga_sync', 'TEXT_OMF'))
    for name, define in imports:
        source = ROOT/'reconstruction'/(name+'.asm')
        sources.append(source)
        obj = output/('screen-probe-'+name.replace('/', '-')+'.obj')
        subprocess.run(['nasm', '-fobj', '-I'+str(ROOT/'reconstruction/uart')+'/',
            '-D'+define, str(source), '-o', str(obj)], check=True)
        linked.append(str(obj))
    exe, map_path = output/'SCREEN.EXE', output/'screen.map'
    subprocess.run(['wlink', 'system', 'dos', 'option', 'quiet', 'option', 'map='+str(map_path),
        'name', str(exe), 'file', ','.join(linked)], check=True)
    layout = audit(map_path)
    m = DosImage(exe, map_path)
    u = m.uc
    map_text = map_path.read_text()
    bank_segment = m.base_segment+int(re.search(r'^ASPECT_CODE\s+FARCODE\s+\S+\s+([0-9a-f]+):', map_text, re.M|re.I)[1], 16)
    stop, events = bank_segment*16+0xfffe, []
    state = dict(done=False)

    def pop_native(count):
        sp = u.reg_read(UC_X86_REG_SP)
        frame = bytes(u.mem_read(m.data_base+sp, 2+2*count))
        args = struct.unpack('<'+'H'*(count+1), frame)
        u.reg_write(UC_X86_REG_SP, sp+2+count*2)
        u.reg_write(UC_X86_REG_IP, args[0])
        return args[1:]

    def code(uc, address, size, user):
        if address == stop:
            state['done'] = True
            uc.emu_stop()
        elif address == m.symbols['csi_service_2530']:
            events.append(('canonical-rectangle-model', *pop_native(4)))
        elif address == m.symbols['screen_adjust_attribute_boundary']:
            events.append(('attribute-boundary-model', *pop_native(2)))
        elif address in [m.symbols[name] for name in ('screen_viewport_enter', 'screen_viewport_leave', 'screen_viewport_refresh')]:
            raise AssertionError('Unexpected viewport dependency in narrow proof')

    def interrupt(uc, number, user):
        ax = uc.reg_read(UC_X86_REG_AX)
        assert number == 0x10 and ax>>8 in (2, 6), (number, hex(ax))
        if ax>>8 == 2:
            position = uc.reg_read(UC_X86_REG_DX)
            events.append(('BIOS02-model', position>>8, position&255))
            uc.mem_write(0x450, struct.pack('<H', position))
        else:
            count, attribute = ax&255, uc.reg_read(UC_X86_REG_BX)>>8
            top, bottom = uc.reg_read(UC_X86_REG_CX), uc.reg_read(UC_X86_REG_DX)
            events.append(('BIOS06-model', attribute, bottom, top, count))
            # Only the BIOS boundary is modeled. Native argument construction,
            # direct frame drawing and attribute-byte accesses execute on x86.

    u.hook_add(UC_HOOK_CODE, code)
    u.hook_add(UC_HOOK_INTR, interrupt)
    checks, cases = 0, 0

    def expect(condition, detail=''):
        nonlocal checks
        checks += 1
        assert condition, detail

    def call(name, args=(), ax=0, dx=0):
        nonlocal cases
        cases += 1
        events.clear()
        state['done'] = False
        frame = struct.pack('<'+'H'*(len(args)+1), 0xfffe, *args)
        sp = m.offset('terminal_stack_top')-64-len(frame)
        u.mem_write(m.data_base+sp, frame+b'SCREEN-CANARY')
        for register, value in ((UC_X86_REG_CS, bank_segment), (UC_X86_REG_DS, m.ds),
            (UC_X86_REG_SS, m.ds), (UC_X86_REG_SP, sp), (UC_X86_REG_AX, ax),
            (UC_X86_REG_DX, dx), (UC_X86_REG_BP, 0x1357), (UC_X86_REG_SI, 0x2468),
            (UC_X86_REG_DI, 0x369c), (UC_X86_REG_ES, 0x6789), (UC_X86_REG_EFLAGS, 0x202)):
            u.reg_write(register, value)
        u.emu_start(m.symbols['terminal_screen_'+name], 0, count=100000)
        expect(state['done'], name)
        expect(u.reg_read(UC_X86_REG_SP) == sp+len(frame), name+' RETn')
        for register, value in ((UC_X86_REG_BP, 0x1357), (UC_X86_REG_SI, 0x2468),
            (UC_X86_REG_DI, 0x369c), (UC_X86_REG_DS, m.ds), (UC_X86_REG_SS, m.ds)):
            expect(u.reg_read(register) == value, name+' register')
        expect(bytes(u.mem_read(m.data_base+sp, len(frame)+13)) == frame+b'SCREEN-CANARY', name+' frame')
        expect(u.reg_read(UC_X86_REG_EFLAGS)&0x600 == 0x200, name+' IF/DF')
        return u.reg_read(UC_X86_REG_AX)

    for value in range(256):
        offset = 24*160+79*2+1
        u.mem_write(0xb8000+offset-1, b'Q\x11')
        call('write_attribute', (offset, value|0xa500))
        expect(bytes(u.mem_read(0xb8000+offset-1, 2)) == bytes((ord('Q'), value)))
        expect(call('read_attribute', (offset,)) == value)
        expect(not events)
    for count in (0, 1, 25, 50, 0x100, 0xffff):
        call('scroll', (0xab47, 0x184f, 0x0000, count))
        expect(events == [('BIOS06-model', 0x47, 0x184f, 0, count&255)])
    for normal in (0, 7, 0xff, 0xff00, 0xffff):
        call('reset_attribute', ax=normal)
        expect(m.get('attributes_normal_value') == m.get('attributes_current') == normal)
        expect(not events)
        call('clear_home')
        expect(events == [('canonical-rectangle-model', normal, 0x174f, 0, 0), ('BIOS02-model', 2, 0)])
        expect(m.get('attributes_normal_value') == m.get('attributes_current') == normal)
    for row, column in ((0, 0), (23, 79), (24, 79), (27, 79), (42, 79), (49, 79)):
        call('set_cursor', ax=row, dx=column)
        expect(events == [('BIOS02-model', row, column)])
        expect(m.get('screen_cursor_row') == row and m.get('screen_cursor_column') == column)
        expect(m.get('screen_attribute_offset') == row*80+column)
        expect(m.get('screen_video_offset') == row*160+column*2)
    for checked in (0, 1):
        m.put('screen_attribute_checks', checked)
        call('home')
        expect(events == [('BIOS02-model', 0, 0)]+([('attribute-boundary-model', 0, 1)] if checked else []))
        expect(m.get('screen_cursor_row') == m.get('screen_cursor_column') == 0)
    glyphs = bytes.fromhex('c9cdbbbabccdc8ba')
    for top, left, bottom, right in ((2, 3, 7, 11), (0, 0, 24, 79), (23, 0, 24, 79), (0, 0, 49, 79)):
        before = bytes((i*37+11)&255 for i in range(8000))
        u.mem_write(0xb8000, before)
        call('draw_box', (0x1247, bottom<<8|right, top<<8|left))
        expected = bytearray(before)
        cells = {(top, left): glyphs[0], (top, right): glyphs[2],
            (bottom, right): glyphs[4], (bottom, left): glyphs[6]}
        for col in range(left+1, right):
            cells[top, col], cells[bottom, col] = glyphs[1], glyphs[5]
        for row in range(top+1, bottom):
            cells[row, right], cells[row, left] = glyphs[3], glyphs[7]
        for (row, col), char in cells.items():
            at = row*160+col*2
            expected[at:at+2] = bytes((char, 0x47))
        expect(bytes(u.mem_read(0xb8000, 8000)) == bytes(expected), 'native frame pixels')
        expect(not events)
    return dict(passed=True, cases=cases, checks=checks, layout=layout,
        executable_sha256=sha(exe), fixture_sha256=sha(fixture),
        scope='Linked native direct-output frame/read/write/cursor/reset/HOME/clear-wrapper and exact RETn/ABI replay; BIOS02/06, canonical clear rectangle and HOME boundary are modeled. No DOS/BIOS renderer or live-terminal qualification.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--check', action='store_true', help='Link a bounded native CPU proof with explicitly modeled external owners')
    args = parser.parse_args()
    output = args.output.resolve()
    assert output.is_relative_to(ROOT/'build')
    objects, sources = build(output)
    checked = check(output, objects, sources) if args.check else None
    result = dict(passed=True, original_inputs=[], objects=objects,
        sources={str(path.relative_to(ROOT)): sha(path) for path in sources},
        resident_bridge_bytes=23, near_DATA_bytes_added=0,
        frame_glyphs='c9cdbbbabccdc8ba',
        limitations=[('Linked CPU proof has explicitly modeled external owners; no DOS/BIOS renderer qualification.' if checked else
            'Assembly and flat-kernel digest checks only; no linked execution or BIOS renderer qualification.'),
            'Original startup frame profile only; runtime frame-pointer changes and PRM mapping remain open.',
            'The caller owns authenticated admission, local scope, physical geometry, shadow continuity and bounded rectangles.'])
    if checked:
        result['CPU_proof'] = checked
    (output/'result.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(dict(passed=True, objects=len(objects), resident_bridge_bytes=23,
        **({'CPU_cases': checked['cases'], 'CPU_checks': checked['checks']} if checked else {}))))


if __name__ == '__main__':
    main()
