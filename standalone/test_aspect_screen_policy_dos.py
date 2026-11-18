#!/usr/bin/env python3
"""Compile and execute the screen-command pure policy, with a separate legacy run.

Synthetic parent globals, far planes and controlled BIOS metadata are fixtures.
This does not execute a parent renderer, screen kernel or hardware transaction.
"""
import argparse
import contextlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess

import build_aspect_renderer_policy as build
import check_aspect_renderer_policy as legacy

ROOT = build.ROOT

EXTRA = r'''
static void geometry(unsigned physical,unsigned hidden,unsigned width,unsigned pane,unsigned row,unsigned col){
 unsigned rows=physical-(hidden?0:1);
 fixture_valid();ui_window_rows=physical;*(unsigned char __far *)MK_FP(0x40,0x84)=physical-1;
 csi_row_count=rows;csi_last_row=screen_last_row=csi_origin_bottom=rows-1;
 screen_attribute_row_bytes=csi_column_count=width;csi_last_column=width-1;erase_cell_count=rows*width;
 ui_flow_suppressed=hidden;ui_flow_region_cells=80;ui_flow_video_base=3840;ui_flow_coordinate_base=0x1800;
 if(width==132){screen_viewport_enabled=1;screen_viewport_left=52;screen_viewport_right=79;
  screen_viewport_active=pane;screen_viewport_offset=pane?0:52;}
 screen_cursor_row=row;screen_cursor_column=col;screen_visible_column=col-screen_viewport_offset;
 screen_attribute_offset=row*width+col;screen_video_offset=row*160+screen_visible_column*2;
}
static void screen_matrix(void){
 static unsigned physicals[4]={25,28,43,50};
 unsigned p,hidden,width,pane,col,row,which,logical;
 for(p=0;p<4;++p)for(hidden=0;hidden<2;++hidden)for(which=0;which<(p?2:6);++which){
  width=which<2?80:132;pane=which==5||which==4?0:1;
  col=which==0||which==2?0:which==3||which==1?79:which==4?52:131;
  logical=physicals[p]-(hidden?0:1);
  for(row=0;row<3;++row){
   geometry(physicals[p],hidden,width,pane,row==0?logical-1:row==1?physicals[p]-1:physicals[p],col);
   admit(row==2?3:0);
   terminal_aspect_active=terminal_parser_active=1;
   ck(aspect_render_preflight_command()==(row==2?3:0));
   ck(aspect_render_preflight_control('A')==(row==2?3:0));
  }
  geometry(physicals[p],hidden,width,pane,physicals[p]-1,col);screen_last_row=logical;admit(3);
  geometry(physicals[p],hidden,width,pane,physicals[p]-1,col);screen_first_row=logical;admit(3);
  geometry(physicals[p],hidden,width,pane,physicals[p]-1,col);csi_origin_bottom=logical;admit(3);
  geometry(physicals[p],hidden,width,pane,physicals[p]-1,col);csi_origin_row=logical;admit(3);
  geometry(physicals[p],hidden,width,pane,physicals[p]-1,col);++screen_video_offset;admit(3);
  geometry(physicals[p],hidden,width,pane,physicals[p]-1,col);++screen_attribute_offset;admit(3);
  geometry(physicals[p],hidden,width,pane,physicals[p]-1,col);++screen_visible_column;admit(3);
  geometry(physicals[p],hidden,width,pane,physicals[p]-1,col);++csi_row_count;admit(3);
  geometry(physicals[p],hidden,width,pane,physicals[p]-1,col);++ui_window_rows;admit(3);
  if(p){geometry(physicals[p],hidden,width,pane,physicals[p]-1,col);fixture_status_layout=1;admit(3);}
 }
 /* Larger physical modes retain narrow-only admission. */
 for(p=1;p<4;++p){geometry(physicals[p],1,132,0,0,131);admit(3);}
 fixture_valid();
}
'''


def adapted_driver():
    source = build.C
    needle = '#define WORD(name) unsigned name;'
    assert source.count(needle) == 1
    source = source.replace(needle, '#include "../terminal/row_geometry.h"\n'
                            'unsigned ui_window_rows,fixture_status_layout;\n'
                            '#pragma aux ui_window_rows "ui_window_rows";\n'+needle)
    needle = 'redisplay_active=command_menu_active=0;terminal_history_pending=0;'
    assert source.count(needle) == 1
    source = source.replace(needle, needle+'\nui_window_rows=25;fixture_status_layout=0;'
                            '*(unsigned char __far *)MK_FP(0x40,0x84)=24;')
    needle = 'int main(void){unsigned i,k,setting,priv,prefix,v,h,result;FILE *f;'
    assert source.count(needle) == 1
    source = source.replace(needle, EXTRA+'\n'+needle+'\nunsigned long old_checks,old_failures;'
                            'unsigned char saved_rows=*(unsigned char __far *)MK_FP(0x40,0x84);')
    needle = 'printf("POLICY checks=%lu failures=%lu\\n",checks,failures);'
    assert source.count(needle) == 1
    source = source.replace(needle, 'old_checks=checks;old_failures=failures;screen_matrix();\n'
                            'printf("SCREEN checks=%lu failures=%lu legacy_checks=%lu legacy_failures=%lu\\n",'
                            'checks-old_checks,failures-old_failures,old_checks,old_failures);\n'+needle)
    needle = 'return failures?1:0;'
    assert source.count(needle) == 1
    source = source.replace(needle, '*(unsigned char __far *)MK_FP(0x40,0x84)=saved_rows;\n'+needle)
    # Even summary-file failure restores the caller BIOS metadata.
    source = source.replace('if(!f)return 2;', 'if(!f){*(unsigned char __far *)MK_FP(0x40,0x84)=saved_rows;return 2;}')
    return source


def compile_profile(out):
    out.mkdir()
    (out/'driver.c').write_text(adapted_driver())
    planes = ('BITS 16\nCPU 8086\nSEGMENT SHADOW public align=16 class=FAR_DATA use16\n'
              'global erase_shadow_cells\nerase_shadow_cells: resb 8192\n'
              'SEGMENT HISTORY public align=16 class=FAR_DATA use16\nglobal terminal_history_buffer\n'
              'terminal_history_buffer: resb 63000\n'
              'SEGMENT ASPECT_CODE public align=1 class=CODE use16\n'
              'global _terminal_row_status_layout\nextern _fixture_status_layout\n'
              '_terminal_row_status_layout: mov ax,[_fixture_status_layout]\nretf\n')
    (out/'planes.asm').write_text(planes)
    subprocess.run(['nasm', '-fobj', str(out/'planes.asm'), '-o', str(out/'planes.obj')], check=True)
    subprocess.run(['wcc', '-q', '-bt=dos', '-0', '-ms', '-s', '-w4', '-we', '-nt=ASPECT_CODE',
                    '-dTERMINAL_ASPECT_ROWS', '-dASPECT_SCREEN_COMMANDS', '-fo='+str(out/'policy.obj'),
                    str(ROOT/'src/aspect/renderer_policy.c')], check=True)
    subprocess.run(['wdis', '-l='+str(out/'policy.dis'), str(out/'policy.obj')], check=True)
    subprocess.run(['wcl', '-q', '-bt=dos', '-0', '-ms', '-s', '-w4', '-we', '-nt=ASPECT_CODE',
                    '-k8192', '-fm=POLICY.MAP',
                    *['-I'+str(ROOT/'src'/p) for p in ['aspect', 'capture', 'printer', 'transfer']],
                    '-fe=POLICY.EXE', str(out/'driver.c'), str(out/'policy.obj'), str(out/'planes.obj')], cwd=out, check=True)
    sources = [Path(__file__).resolve(), Path(build.__file__), Path(legacy.__file__),
               ROOT/'src/aspect/renderer_policy.c', ROOT/'src/aspect/renderer_policy.h',
               ROOT/'src/terminal/row_geometry.h']
    sources += [ROOT/'src'/p for p in ['capture/capture_file.h', 'capture/capture_session.h',
                'printer/printer_device.h', 'transfer/download_file.h', 'transfer/upload_file.h',
                'transfer/batch_download.h', 'transfer/batch_header.h']]
    manifest = dict(binary_sha256=build.sha(out/'POLICY.EXE'),
                    sources={str(p.relative_to(ROOT)): build.sha(p) for p in sources},
                    generated_sources={p.name: build.sha(p) for p in [out/'driver.c', out/'planes.asm']},
                    defines=['TERMINAL_ASPECT_ROWS', 'ASPECT_SCREEN_COMMANDS'], original_inputs=[])
    (out/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    return manifest


def cpu_matrix(out):
    from unicorn import Uc, UC_ARCH_X86, UC_MODE_16, UC_HOOK_CODE, UC_HOOK_MEM_WRITE, UC_HOOK_INTR
    from unicorn.x86_const import (UC_X86_REG_AX, UC_X86_REG_BP,
        UC_X86_REG_SI, UC_X86_REG_DI, UC_X86_REG_CS, UC_X86_REG_DS, UC_X86_REG_SS,
        UC_X86_REG_ES, UC_X86_REG_SP, UC_X86_REG_IP)
    symbols = {}
    maptext = (out/'POLICY.MAP').read_text()
    for line in maptext.splitlines():
        m = re.match(r'^\s*([0-9A-Fa-f]{4}):([0-9A-Fa-f]{4,8})[*+]?\s+(\w+)', line)
        if m:
            symbols[m[3]] = (int(m[1], 16), int(m[2], 16))
    load = 0x2000
    ds = load+int(re.search(r'DGROUP\s+([0-9A-Fa-f]{4}):', maptext)[1], 16)
    raw = (out/'POLICY.EXE').read_bytes()
    header = struct.unpack_from('<14H', raw)
    body = bytearray(raw[header[4]*16:])
    for i in range(header[3]):
        off, seg = struct.unpack_from('<HH', raw, header[12]+4*i)
        at = seg*16+off
        struct.pack_into('<H', body, at, (struct.unpack_from('<H', body, at)[0]+load)&65535)
    u = Uc(UC_ARCH_X86, UC_MODE_16)
    u.mem_map(0, 2*1024*1024)
    u.mem_write(load*16, bytes(body))
    address = lambda name: (load+symbols[name][0])*16+symbols[name][1]
    listing = (out/'policy.dis').read_text()
    segments = re.findall(r'Segment: (\w+) .*?([0-9A-Fa-f]{8}) bytes', listing)
    assert segments and all(int(v, 16) == 0 for n, v in segments if n != 'ASPECT_CODE')
    size = int(dict(segments)['ASPECT_CODE'], 16)
    local = int(re.search(r'^([0-9A-Fa-f]+)\s+_aspect_render_admit:', listing, re.M)[1], 16)
    start = address('_aspect_render_admit')-local
    stub = address('_terminal_row_status_layout')
    assert bytes(u.mem_read(stub, 4))[0] == 0xa1 and bytes(u.mem_read(stub, 4))[-1] == 0xcb
    active = False
    visited = set()
    writes = []

    def hook(cpu, at, length, _):
        if cpu.reg_read(UC_X86_REG_IP) == 0xf000:
            cpu.emu_stop()
        elif active:
            assert start <= at < start+size or stub <= at < stub+4, ('external code', hex(at))
            visited.add(at)

    def write(cpu, access, at, length, value, _):
        if active:
            assert ds*16+0xe000 <= at and at+length <= ds*16+0xf000, ('nonstack write', at, length)
            writes.append((at, length))

    def interrupt(cpu, num, _):
        raise AssertionError(('forbidden interrupt', num))

    u.hook_add(UC_HOOK_CODE, hook)
    u.hook_add(UC_HOOK_MEM_WRITE, write)
    u.hook_add(UC_HOOK_INTR, interrupt)

    def invoke(name, arg=None, pure=True):
        nonlocal active
        regs = [(UC_X86_REG_BP, 0x1357),
                (UC_X86_REG_SI, 0x2468), (UC_X86_REG_DI, 0x369a)]
        for reg, value in [(UC_X86_REG_CS, load), (UC_X86_REG_DS, ds), (UC_X86_REG_SS, ds),
                           (UC_X86_REG_ES, ds), (UC_X86_REG_SP, 0xf000)]+regs:
            u.reg_write(reg, value)
        u.mem_write(ds*16+0xf000, struct.pack('<H', 0xf000))
        if arg is not None:
            u.mem_write(ds*16+0xf002, struct.pack('<H', arg))
        active = pure
        u.emu_start(address(name), 0, count=1000000)
        active = False
        assert u.reg_read(UC_X86_REG_IP) == 0xf000 and u.reg_read(UC_X86_REG_SP) == 0xf002
        assert u.reg_read(UC_X86_REG_DS) == u.reg_read(UC_X86_REG_SS) == ds
        for reg, value in regs:
            assert u.reg_read(reg) == value
        return u.reg_read(UC_X86_REG_AX)

    def word(name, value):
        u.mem_write(address(name), struct.pack('<H', value))

    def seed(physical, hidden, width, pane, row, col):
        invoke('_fixture_valid', pure=False)
        u.mem_write(0x449, b'\x03\x50\0')
        u.mem_write(0x462, b'\0')
        u.mem_write(0x484, bytes([physical-1]))
        logical = physical-(not hidden)
        offset = 52 if width == 132 and not pane else 0
        fields = dict(ui_window_rows=physical, csi_row_count=logical, csi_last_row=logical-1,
                      screen_last_row=logical-1, csi_origin_bottom=logical-1,
                      screen_attribute_row_bytes=width, csi_column_count=width, csi_last_column=width-1,
                      erase_cell_count=width*logical, ui_flow_suppressed=hidden, ui_flow_region_cells=80,
                      ui_flow_video_base=3840, ui_flow_coordinate_base=0x1800,
                      screen_cursor_row=row, screen_cursor_column=col, screen_visible_column=col-offset,
                      screen_attribute_offset=row*width+col, screen_video_offset=row*160+(col-offset)*2)
        if width == 132:
            fields.update(screen_viewport_enabled=1, screen_viewport_left=52, screen_viewport_right=79,
                          screen_viewport_active=pane, screen_viewport_offset=offset)
        for field, value in fields.items():
            word(field, value)
        return logical

    records = []
    def check(expected, label):
        for name, arg in [('_aspect_render_admit', None), ('_aspect_render_preflight_command', None),
                          ('_aspect_render_preflight_control', 65)]:
            word('terminal_aspect_active', int(name != '_aspect_render_admit'))
            word('terminal_parser_active', int(name != '_aspect_render_admit'))
            assert invoke(name, arg) == expected, (label, name, expected)
        records.append(dict(case=label, result=expected, policy_calls=3))

    for physical in (25, 28, 43, 50):
        for hidden in (0, 1):
            columns = [(80, 0, 0), (80, 0, 79)]
            if physical == 25:
                columns += [(132, 1, 0), (132, 1, 79), (132, 0, 52), (132, 0, 131)]
            for width, pane, col in columns:
                prefix = f'{physical}/{hidden}/{width}/{pane}/{col}'
                for row in (physical-(not hidden)-1, physical-1, physical):
                    seed(physical, hidden, width, pane, row, col)
                    check(3 if row == physical else 0, prefix+'/row='+str(row))
                logical = physical-(not hidden)
                for field, value in [('screen_last_row', logical), ('screen_first_row', logical),
                    ('csi_origin_bottom', logical), ('csi_origin_row', logical),
                    ('screen_video_offset', (physical-1)*160+(col-(52 if width == 132 and not pane else 0))*2+1),
                    ('screen_attribute_offset', (physical-1)*width+col+1),
                    ('screen_visible_column', col-(52 if width == 132 and not pane else 0)+1),
                    ('csi_row_count', logical+1), ('ui_window_rows', physical+1)]:
                    seed(physical, hidden, width, pane, physical-1, col)
                    word(field, value)
                    check(3, prefix+'/bad='+field)
                if physical != 25:
                    seed(physical, hidden, width, pane, physical-1, col)
                    word('_fixture_status_layout', 1)
                    check(3, prefix+'/bad=status-layout')
    for physical in (28, 43, 50):
        seed(physical, 1, 132, 0, 0, 131)
        check(3, str(physical)+'/wide-refused')
    return dict(passed=True, cases=len(records), policy_calls=3*len(records), records=records,
                no_external_code=True, no_nonstack_writes=True, checked_stack_writes=len(writes),
                visited_instruction_addresses=len(visited), zero_policy_DATA=True,
                allowed_code='Only compiled policy object and four-byte far status-layout fixture',
                ABI='Near cdecl, DS=SS, balanced stack, BP/SI/DI preserved')


def run_dos(out):
    folder = out/'dos-run'
    folder.mkdir()
    shutil.copyfile(out/'POLICY.EXE', folder/'POLICY.EXE')
    cfg = f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
cycles=max
[mixer]
nosound=true
[autoexec]
@echo off
mount c "{folder}"
c:
POLICY >CONSOLE.TXT
if errorlevel 1 goto failed
echo PASS>PASS.TXT
goto done
:failed
echo FAIL>FAIL.TXT
:done
exit
'''
    (folder/'dosbox.conf').write_text(cfg)
    with (folder/'dosbox.log').open('w') as log:
        status = subprocess.run(['dosbox-x', '-fastlaunch', '-nogui', '-conf', str(folder/'dosbox.conf')],
                                stdout=log, stderr=log, timeout=60,
                                env=dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy'))
    text = (folder/'CONSOLE.TXT').read_text()
    summary = re.search(r'SCREEN checks=(\d+) failures=(\d+) legacy_checks=(\d+) legacy_failures=(\d+)', text)
    assert status.returncode == 0 and (folder/'PASS.TXT').exists() and not (folder/'FAIL.TXT').exists(), text
    assert summary and int(summary[1]) > 500 and int(summary[2]) == int(summary[4]) == 0, text
    assert int(summary[3]) > 20000
    assert build.sha(folder/'POLICY.EXE') == build.sha(out/'POLICY.EXE')
    return dict(passed=True, screen_checks=int(summary[1]), retained_legacy_checks=int(summary[3]),
                failures=0, summary=summary[0], run_directory=str(folder.relative_to(ROOT)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT/'build') and not out.exists()
    out.mkdir()
    # Run the maintained default build/checker unchanged in its own fresh folder.
    build.OUT = legacy.OUT = out/'legacy'
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        build.main()
        assert legacy.main() == 0
    (out/'legacy.log').write_text(log.getvalue())
    old = json.loads((build.OUT/'checks.json').read_text())
    manifest = compile_profile(out/'screen')
    cpu = cpu_matrix(out/'screen')
    dos = run_dos(out/'screen')
    for name, digest in manifest['sources'].items():
        assert build.sha(ROOT/name) == digest
    report = dict(passed=True, legacy_default=old, screen_DOS=dos, screen_CPU=cpu,
                  screen_manifest_sha256=build.sha(out/'screen/manifest.json'),
                  screen_binary_sha256=manifest['binary_sha256'], checker_sha256=build.sha(Path(__file__)),
                  original_inputs=[], scope=__doc__+' Legacy expectations are retained unchanged both in the default profile and the screen-enabled full matrix. Physical25/28/43/50, shown/hidden logical windows, coherent physical last-row cursor caches, narrow columns0/79 and25-row panned wide columns0/79/52/131, malformed bounds/caches, and large-mode wide/status-layout refusals are tested. CPU executions permit only pure policy and the real far-cdecl status stub; writes are restricted to caller stack. DOS fixture BIOS row metadata is restored on exit. Separate from full-parent DOS, native kernel and hardware qualification.')
    (out/'result.json').write_text(json.dumps(report, indent=2)+'\n')
    print('SCREEN_POLICY', dos['summary'], 'CPU cases='+str(cpu['cases']), 'calls='+str(cpu['policy_calls']))
    print('LEGACY_DEFAULT', old['DOS_summary'], 'CPU cases='+str(old['cpu']['count']))


if __name__ == '__main__':
    main()
