#!/usr/bin/env python3
"""Run packaged START/SETUP launchers on a synthetic card in actual DOS8086."""
import argparse
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys

from package_special_edition import ROOT, sha
from check_setup_model import image
from test_directory_key_bindings_dos import actions
from test_terminal import SAMPLER
from package_connection_test import validate_dos_directory

sys.path.insert(0, str(ROOT / 'src/aspect'))
from compiler import compile_source


def run(package, out, setup=False, splash_only=False,irq=None,com=2,after_child_view=False,precompile=False,bios_absent=False,chat_help=False,native_line_port=False,meta_editor=False,keymap_editor=False):
    assert not precompile or not (setup or splash_only or after_child_view)
    assert not chat_help or not (setup or splash_only or after_child_view or precompile)
    manifest = json.loads((package / 'manifest.json').read_text())
    assert not keymap_editor or (manifest.get('experimental_keymap_editor') and not any((setup,splash_only,after_child_view,precompile,chat_help,native_line_port,meta_editor)))
    assert not meta_editor or (manifest.get('experimental_meta_editor') and not (setup or splash_only or after_child_view or precompile or chat_help or native_line_port))
    assert not native_line_port or (manifest.get('experimental_line_port_overlay') and not (setup or splash_only or after_child_view or precompile or chat_help))
    assert not chat_help or manifest.get('experimental_chat_help')
    dos_directory=validate_dos_directory(manifest.get('dos_directory','PCPLUSSE'))
    dos_root='C:\\'+dos_directory
    assert manifest['card_written'] is False
    for name, digest in manifest['sources'].items():
        assert sha(ROOT / name) == digest, name
    for leaf, digest in manifest['files'].items():
        assert sha(package / dos_directory / leaf) == digest, leaf
    out.mkdir(parents=True, exist_ok=False)
    drive = out / 'drive'
    drive.mkdir()
    app = drive / dos_directory
    shutil.copytree(package / dos_directory, app)
    raw = bytearray(image())
    # The editor fixture preserves arbitrary opaque bytes. The current parent
    # also applies saved display preferences at startup, so supply an admitted
    # VGA25/status-visible frame instead of opaque values for these four words.
    for at,value in ((0x1c2,0),(0x1c8,2),(0x1ca,25),(0x4ec,0)):
        struct.pack_into('<H',raw,at,value)
    assert com in (1,2,3,4)
    base=(0x3f8,0x2f8,0x3e8,0x2e8)[com-1]
    struct.pack_into('<H', raw, 0, com-1)
    struct.pack_into('<H', raw, 0x174+2*(com-1), base)
    struct.pack_into('<HH', raw, 0x4e4, 8, 4)
    if irq is not None:
        assert irq in (3,4,5,7)and manifest.get('experimental_custom_irq')
        struct.pack_into('<H',raw,0x184+2*(com-1),irq)
    if keymap_editor:struct.pack_into('<H',raw,0x194,6)
    fixtures = {'PCPLUS.PRM': bytes(raw), 'PCPLUS.XLT': bytes(range(256)),
                'PCPLUS.DIR': b'PRIVATE-DIRECTORY-PRESERVATION-SENTINEL',
                'PCPLUS.KEY': bytes(10*54), 'PCPLUS.KBD': bytes(7*948),
                'PCPLUS.FON': b'PRIVATE-CALL-HISTORY-PRESERVATION-SENTINEL\r\n'}
    # No directory selector is requested; a local dialing file is not opened.
    for leaf, data in fixtures.items():
        (app / leaf).write_bytes(data)
    if keymap_editor:(app/'SYN.KBD').write_bytes(bytes(33*948))
    source = ('integer value\nproc main\nvalue=' + '(' * 120 + '37' + ')' * 120 +
              '\nif value==37\nfopen 0 "RESULT.BIN" "wb"\n'
              'fputs 0 "SPECIAL-COMPILED"\nfclose 0\nendif\nendproc\n')
    new_commands=precompile and manifest.get('experimental_alarm_VM',False)
    if new_commands:
        source=source.replace('proc main\n','proc main\nalarm 0\ndate s0\ntime s1 1\n',1)
    emulate=precompile and manifest.get('experimental_emulate_VM',False)
    if emulate:source=source.replace('proc main\n','proc main\nemulate vt220\nemulate ansi\n',1)
    (app / 'TEST.ASP').write_text(source, encoding='ascii')
    (app / 'ACTIONS.KEY').write_bytes(actions((dos_root+('\\TEST.ASX' if precompile else '\\TEST.ASP')).encode('ascii'), 0))
    sampler = SAMPLER.replace('D:\\', 'C:\\')
    for offset in (0, 1, 3, 4):
        sampler = sampler.replace(hex(0x3f8 + offset), hex(base + offset))
    (drive / 'sample.asm').write_text(sampler)
    subprocess.run(['nasm', '-fbin', str(drive / 'sample.asm'), '-o', str(drive / 'SNAP.COM')], check=True)
    if bios_absent:
        assert manifest.get('experimental_custom_irq')
        # Test-only DOS utility: emulate a BIOS omitting the configured UART.
        # Leave the real emulated UART intact; never alter product instructions.
        (drive/'unlist.asm').write_text('BITS 16\nCPU 8086\nORG 0x100\n'
            'mov ax,0x40\nmov es,ax\nmov word [es:'+str((com-1)*2)+'],0\n'
            'mov ax,0x4c00\nint 0x21\n')
        subprocess.run(['nasm','-fbin',str(drive/'unlist.asm'),'-o',str(drive/'UNLIST.COM')],check=True)
    subprocess.run(['nasm', '-fbin', str(ROOT / 'standalone/special_watch.asm'),
                    '-o', str(drive / 'WATCH.COM')], check=True)
    if chat_help:
        source=(ROOT/'standalone/global_help_watch.asm').read_text()
        for old,new in [("cmp byte [es:190],'P'","cmp byte [es:72],'R'"),("cmp byte [es:194],'R'","cmp byte [es:74],'E'"),("cmp byte [es:198],'O'","cmp byte [es:76],'M'"),("cmp byte [es:2],'T'","cmp byte [es:2],'C'"),("cmp byte [es:4],'e'","cmp byte [es:4],'h'"),("cmp byte [es:6],'r'","cmp byte [es:6],'a'")]:
            assert source.count(old)==1;source=source.replace(old,new)
        source=source.replace(' jmp .candidate\n.help:'," cmp byte [es:3200],'A'\n jne .done\n cmp byte [es:3202],'B'\n jne .done\n jmp .candidate\n.help:")
        assert source.count("name: db 'HELPUI.BIN',0")==1
        source=source.replace("name: db 'HELPUI.BIN',0","name: db 'C:\\HELPUI.BIN',0")
        (drive/'HELPWAT.ASM').write_text(source)
        subprocess.run(['nasm','-fbin',str(drive/'HELPWAT.ASM'),'-o',str(drive/'HELPWAT.COM')],check=True)
    if native_line_port or meta_editor:
        source=(ROOT/'standalone/path_dialog_watch.asm').read_text()
        begin=source.index(' cmp word [es:806]');end=source.index('%if WATCH_KIND',begin)
        marker=''' cmp byte [es:522],'M'
 jne .done
 cmp byte [es:524],'E'
 jne .done
 cmp byte [es:532],'K'
 jne .done
''' if meta_editor else ''' cmp byte [es:356],0xc9
 jne .done
 cmp byte [es:542],'C'
 jne .done
 cmp byte [es:1000],'B'
 jne .done
'''
        source=source[:begin]+marker+source[end:]
        source=source.replace('D:\\PATHVIEW.BIN','C:\\PATHVIEW.BIN')
        (drive/'LINEWAT.ASM').write_text(source)
        subprocess.run(['nasm','-fbin','-DWATCH_KIND=0',str(drive/'LINEWAT.ASM'),'-o',str(drive/'LINEWAT.COM')],check=True)
    strategy = manifest.get('experimental_directory_resource_owner',False)
    if strategy:
        subprocess.run(['nasm','-fbin',str(ROOT/'standalone/dos_strategy_sample.asm'),'-o',str(drive/'STRAT.COM')],check=True)
    if after_child_view:
        assert strategy and not setup and not splash_only
        (drive/'rview.asm').write_text((ROOT/'standalone/redisplay_watch.asm').read_text().replace('D:\\','C:\\'))
        subprocess.run(['nasm','-fbin',str(drive/'rview.asm'),'-o',str(drive/'RVIEW.COM')],check=True)
    launcher = 'SETUP' if setup else 'START'
    observe = setup or splash_only
    keys = ('p900 escape p1100 enter p1500 a-z p700 escape p600 a-x' if setup else
            'p900 enter p1500 a-z p700 escape p600 a-x' if splash_only else
            'p900 enter p1500 a-1 p6500 space p700 a-x')
    if after_child_view:keys=keys.replace('a-x','c-pgup p1200 escape p500 a-x')
    if chat_help:keys='p900 enter p1800 a-o p1500 A B p1000 a-z p2500 escape p1200 escape p1000 a-x'
    if native_line_port:keys='p900 enter p1800 a-p p2200 escape p1000 a-x'
    if keymap_editor:keys='p900 enter p1800 a-f8 p3000 f1 p200 tab n e w enter p300 a-s p900 escape p900 a-x'
    if meta_editor:keys='p900 enter p1800 a-m p3000 escape p900 a-z p2500 escape p700 a-x'
    config = ('[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\n'
              'cycles=fixed 12000\n[serial]\n'+
              ''.join('serial'+str(n)+'=dummy'+(' irq:'+str(irq)if n==com and irq is not None else '')+'\n'
                      for n in range(1,5))+
              '[mixer]\nnosound=true\n[autoexec]\n@echo off\n'
              'mount c "' + str(drive) + '"\nc:\nset PCPLUS=C:\\ORIGINAL\n' +
              ('WATCH T\n' if observe else '')+('LINEWAT T\n' if native_line_port or meta_editor else '')+('HELPWAT T\n' if chat_help else '')+('RVIEW T\n' if after_child_view else '')+('STRAT B\n' if strategy else '')+('UNLIST\n' if bios_absent else '')+'SNAP B\n'+
              ('CD \\'+dos_directory+'\nASPCOMP TEST.ASP\nIF ERRORLEVEL 1 GOTO failed\nCD \\\n' if precompile else '')+
              'ADDKEY ' + keys + '\n'
              'CALL '+dos_root+'\\' + launcher + '.BAT /T:ACTIONS.KEY'+(' /K:'+dos_root+'\\SYN.KBD' if keymap_editor else '')+'\n'+
              ('C:\\STRAT A\n' if strategy else '')+'SET >C:\\ENV.TXT\nC:\\SNAP S\nC:\\SNAP A\n'+('C:\\LINEWAT\n' if native_line_port or meta_editor else '')+('C:\\HELPWAT\n' if chat_help else '')+('C:\\RVIEW\n' if after_child_view else '')+('C:\\WATCH\n' if observe else '')+
              'if errorlevel 1 goto failed\necho RETURNED>C:\\RETURN.TXT\nexit\n'
              ':failed\necho FAIL>C:\\FAIL.TXT\nexit\n')
    (out / 'dosbox.conf').write_text(config)
    with (out / 'dosbox.log').open('w') as log:
        proc = subprocess.run(['dosbox-x', '-fastlaunch', '-nogui', '-conf', str(out / 'dosbox.conf')],
                              cwd=drive, stdout=log, stderr=log, timeout=30,
                              env=dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy'))
    assert proc.returncode == 0 and (drive / 'RETURN.TXT').exists() and not (drive / 'FAIL.TXT').exists()
    if observe:
        video = (drive / 'SPLASH.BIN').read_bytes()
        assert len(video) == 8000
        at = (18 * 80 + 36) * 2
        assert video[at:at + 38:2] == b'LoC SPECIAL EDITION'
        assert video[at + 1:at + 38:2] == b'\x0f' * 19
    assert (drive / 'BEFORE.BIN').read_bytes() == (drive / 'AFTER.BIN').read_bytes()
    assert b'Unsupported terminal function' not in (drive/'SCREEN.BIN').read_bytes()[::2]
    if strategy:
        assert len((drive/'STRATB.BIN').read_bytes())==2 and (drive/'STRATB.BIN').read_bytes()==(drive/'STRATA.BIN').read_bytes()
    if after_child_view:
        captured=(drive/'RVIEW.BIN').read_bytes();assert len(captured)==10246
        magic,count,ticks=struct.unpack_from('<3H',captured)
        assert magic==0x4452 and 1<=count<=32 and ticks>5
    env = (drive / 'ENV.TXT').read_bytes().upper().splitlines()
    assert b'PCPLUS=C:\\ORIGINAL' in env and not any(s.startswith(b'LOC_PCPLUS=') for s in env)
    for leaf, data in fixtures.items():
        assert (app / leaf).read_bytes() == data, leaf
    if native_line_port or meta_editor:
        captured=(drive/'PATHVIEW.BIN').read_bytes();assert len(captured)==4071
        magic,flags,ticks=struct.unpack_from('<3H',captured)
        assert magic==0x5044 and flags==3 and ticks>2
        text=captured[6:4006:2]
        if meta_editor:assert text[3*80+20:3*80+31]==b' META KEYS '
        else:assert b'CURRENT SETTINGS:' in text and b'Esc) Exit   Alt-S) Save and Exit  YOUR CHOICE:' in text
        assert not (app/'TEST.ASX').exists() and not (app/'RESULT.BIN').exists()
    elif chat_help:
        captured=(drive/'HELPUI.BIN').read_bytes();assert len(captured)==24020
        words=struct.unpack_from('<10H',captured);before=captured[20:8020];helper=captured[8020:16020];after=captured[16020:24020]
        assert words[:2]==(0x4847,3) and words[3]==25 and words[4:6]==words[8:10]
        assert before==after and before[3200:3204:2]==b'AB' and helper[2:20:2]==b'Chat Mode'
        assert not (app/'TEST.ASX').exists() and not (app/'RESULT.BIN').exists()
    elif keymap_editor:
        expected=bytearray(33*948);expected[6*948+16*12:6*948+16*12+4]=b'new\0'
        assert (app/'SYN.KBD').read_bytes()==expected
        assert not (app/'KBDSTG.$$$').exists() and not (app/'KBDBAK.$$$').exists()
    elif not observe:
        assert (app / 'RESULT.BIN').read_bytes() == b'SPECIAL-COMPILED'
        assert (app / 'TEST.ASX').read_bytes() == compile_source(source)
    else:
        assert not (app / 'TEST.ASX').exists() and not (app / 'RESULT.BIN').exists()
    for leaf in manifest['files']:
        assert sha(app / leaf) == manifest['files'][leaf]
    result = dict(passed=True, launcher=launcher, dos_directory=dos_directory,cpu='8086', port=com, io_base=base, resident_observer=observe,
                  irq=irq, precompiled_before_terminal=precompile, bios_port_omitted=bios_absent,chat_help=chat_help,
                  native_line_port=native_line_port,meta_editor=meta_editor,keymap_editor=keymap_editor,
                  packaged_ASPECT_clock_alarm_exercised=new_commands,
                  packaged_ASPECT_EMULATE_exercised=emulate,
                  package_manifest_sha256=sha(package / 'manifest.json'),
                  package_files=manifest['files'],
                  private_fixture_sha256={leaf:sha(app/leaf) for leaf in fixtures},
                  checks=['launcher returns to DOS', 'PCPLUS environment restored',
                          f'COM{com}/PIC/IRQ vectors restored', 'private PRM/DIR/KEY/KBD/XLT/FON unchanged',
                          'packaged binaries unchanged'] + (['actual packaged Alt-F8 saves only the selected KBD and returns; shorter private KBD unchanged'] if keymap_editor else ['actual packaged Alt-M loads its sibling module and returns'] if meta_editor else ['actual packaged Alt-P loads its sibling module and returns'] if native_line_port else ['actual packaged Chat/PCHELP round trip retains AB and exact frame/cursor'] if chat_help else ['actual magenta splash captured by independent timer'] if observe else
                          [('DOS precompilation produces exact ASX' if precompile else 'nested DOS source compilation produces exact ASX'), 'script writes expected result'])+(['DOS allocation strategy restored'] if strategy else [])+(['frozen-history viewer reopens after nested child return'] if after_child_view else []),
                  sources={n: sha(ROOT / n) for n in ['standalone/test_special_package_dos.py',
                           'standalone/special_watch.asm', 'standalone/test_terminal.py',
                           'standalone/check_setup_model.py', 'standalone/test_directory_key_bindings_dos.py',
                           'src/aspect/compiler.py']+(['standalone/path_dialog_watch.asm'] if native_line_port or meta_editor else [])+(['standalone/global_help_watch.asm'] if chat_help else [])+(['standalone/dos_strategy_sample.asm'] if strategy else [])+(['standalone/redisplay_watch.asm'] if after_child_view else [])},
                  artifacts={str(p.relative_to(out)): sha(p) for p in out.rglob('*') if p.is_file()},
                  scope=__doc__ + ' Dummy serial ports; no live BBS, card write or physical modem test.')
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print('PASS special package', launcher)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--package', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--setup', action='store_true')
    p.add_argument('--splash-only', action='store_true')
    p.add_argument('--after-child-view',action='store_true',help='Observe redisplay after nested compilation and frozen-memory reacquisition')
    p.add_argument('--irq',type=int,choices=[3,4,5,7])
    p.add_argument('--com',type=int,choices=[1,2,3,4],default=2)
    p.add_argument('--precompile',action='store_true',help='Compile at the DOS prompt before retaining the terminal/interpreter')
    p.add_argument('--bios-absent',action='store_true',help='Clear the selected BIOS UART entry before launch; keep actual UART present')
    p.add_argument('--chat-help',action='store_true',help='Exercise packaged Chat and PCHELP with retained input/frame/cursor')
    p.add_argument('--native-line-port',action='store_true',help='Observe packaged Alt-P loading its matching sibling module')
    p.add_argument('--keymap-editor',action='store_true',help='Edit/save through packaged START and its sibling PCKEYMAP, preserving existing private fixtures')
    p.add_argument('--meta-editor',action='store_true',help='Observe packaged Alt-M loading its matching sibling module')
    args = p.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT / 'build') and not out.exists()
    assert not (args.setup and args.splash_only)
    run(args.package.resolve(), out, args.setup, args.splash_only,args.irq,args.com,args.after_child_view,args.precompile,args.bios_absent,args.chat_help,args.native_line_port,args.meta_editor,args.keymap_editor)


if __name__ == '__main__':
    main()
