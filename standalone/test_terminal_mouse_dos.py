#!/usr/bin/env python3
"""Actual terminal mouse menus/PROGRAM and safe retained-callback shutdown."""
import argparse
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess
import uuid
import test_aspect_renderer_dos as render
from modem_fixtures import fixture

ROOT = render.ROOT
sha = render.sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label', default='mouse-' + uuid.uuid4().hex)
    parser.add_argument('--case', action='append', choices=['normal', 'menu', 'program', 'quarantine', 'invalid-scale', 'no-driver', 'unsupported-driver'])
    args = parser.parse_args()
    assert re.fullmatch(r'[A-Za-z0-9_-]+', args.label)
    out = ROOT / 'build/terminal-mouse-tests' / args.label
    out.mkdir(parents=True, exist_ok=False)
    binary = ROOT / 'build/terminal-mouse/TERMINAL.EXE'
    manifest = json.loads((binary.parent / 'manifest.json').read_text())
    assert manifest['experimental_mouse'] and not manifest['experimental_external_render']
    assert manifest['binary_sha256'] == sha(binary)
    sources = {**manifest['sources']}
    names = ['standalone/test_terminal_mouse_dos.py', 'standalone/terminal_mouse_observer.c',
             'standalone/terminal_mouse_observer.asm', 'standalone/test_aspect_renderer_dos.py',
             'standalone/test_connection_dos.py', 'standalone/test_terminal.py',
             'standalone/modem_fixtures.py', 'standalone/terminal_config_fixtures.py',
             'standalone/directory_test_support.py', 'standalone/mouse_keyboard_child.asm']
    sources.update({p:sha(ROOT / p) for p in names})
    for name, digest in sources.items():
        assert sha(ROOT / name) == digest, name
        target = out / 'sources' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    subprocess.run(['nasm', '-fobj', str(out / 'sources/standalone/terminal_mouse_observer.asm'),
                    '-o', str(out / 'observer.obj')], check=True)
    subprocess.run(['wcl', '-q', '-bt=dos', '-0', '-ms', '-ecc', '-s', '-w4', '-we',
                    '-k8192', '-dEXPECTED_KEEP=' + str(manifest['memory_layout']['retained_parent_paragraphs']),
                    str(out / 'sources/standalone/terminal_mouse_observer.c'), str(out / 'observer.obj'),
                    '-fe=MOBS.EXE', '-fm=MOBS.map'], cwd=out, check=True)
    subprocess.run(['nasm', '-fbin', str(out / 'sources/standalone/mouse_keyboard_child.asm'),
                    '-o', str(out / 'MUTATE.COM')], check=True)
    render.OUT = out
    # Only replace the launched process with the independent DOS observer.
    # All peer bytes, hardware samples and actual production client are retained.
    original = ROOT / 'standalone/test_connection_dos.py'
    source = original.read_text().replace('cputype=386', 'cputype=8086')
    source = source.replace("out=ROOT/'build/connection-dos'/name", 'out=RENDER_OUT/name')
    source = source.replace("checks['immediate_banner_not_dropped']=len(screen)==4000 and screen[:30:2]==b'FIRST BYTE SAFE'",
                            "checks['actual_screen_snapshot']=len(screen)==4000")
    old = r'C:\\TERMINAL {arguments}'
    assert source.count(old) == 1
    source = source.replace(old, r'D:\\MOBS {MOUSE_MODE} {arguments}')
    # A new independent module avoids inherited instrumentation from other labs.
    import types
    harness = types.ModuleType('mouse_connection_observer')
    harness.__file__ = str(original)
    harness.RENDER_OUT = out
    exec(compile(source, str(original), 'exec'), harness.__dict__)
    cases = [
        ('normal', 'N', 'p2500 r e a d y p500 a-x'),
        ('menu', 'S', 'p2500 a-z p2500 r e a d y p500 a-x'),
        ('program', 'N', 'p2500 a-1 p1800 space p800 r e a d y p500 a-x'),
        ('quarantine', 'Q', 'p2500 a-x'),
        ('invalid-scale', 'R', 'p1000 a-x'),
        ('no-driver', 'B', 'p2500 r e a d y p500 a-x'),
        ('unsupported-driver', 'U', 'p2500 r e a d y p500 a-x'),
    ]
    if args.case:
        cases = [c for c in cases if c[0] in args.case]
    results = []
    for name, mode, keys in cases:
        folder = out / name
        folder.mkdir()
        shutil.copyfile(binary, folder / 'TERMINAL.EXE')
        harness.BINARY = folder / 'TERMINAL.EXE'
        harness.MOUSE_MODE = mode
        settings = bytearray(fixture(timeout=5))
        struct.pack_into('<HH', settings, 0x4e4, 0 if mode == 'R' else 8, 4)
        files = {'MOBS.EXE':(out / 'MOBS.EXE').read_bytes(), 'MUTATE.COM':(out / 'MUTATE.COM').read_bytes()}
        arguments = '@D:\\TEST.PRM /D:CaseTest:23'
        if name == 'program':
            mapping = bytearray(540)
            for i in range(10):
                struct.pack_into('<H', mapping, i * 54, 3)
            struct.pack_into('<H', mapping, 0, 1)
            command = b'D:\\MUTATE.COM'
            mapping[2:2+len(command)] = command
            files['TEST.KEY'] = bytes(mapping)
            arguments += ' /T:D:\\TEST.KEY'
        banner = b'\x1b[2J\x1b[HQSTOP BYTE SAFE\x1b[6n\x1b[0c' if mode == 'Q' else None
        result = harness.run(name, 'reject' if mode == 'R' else 'success', keys,
            prm=bytes(settings), arguments=arguments, files=files, working_drive='d', banner=banner)
        report = (folder / 'MOUSE.OUT').read_text() if (folder / 'MOUSE.OUT').exists() else ''
        summary = re.fullmatch(r'MOUSEOBS checks=(\d+) failures=(\d+) child=(\d+) retained=(\d+) driver_bytes=(\d+) stage=(\d+) callback=(\d+) registrations=(\d+)\s*', report)
        checks = result['checks']
        checks['independent_mouse_observer'] = bool(summary) and int(summary[2]) == 0 and int(summary[1]) >= 9
        if mode != 'R':
            checks['real_serial_replies'] = result['checks'].get('actual_DOS_CPR', False)
        if name in ('normal', 'menu', 'program', 'no-driver', 'unsupported-driver'):
            checks['ordinary_input_after_mouse_owner'] = b'ready' in (folder / 'serial.bin').read_bytes()
        if name == 'menu':
            capture = folder / 'PCPLUS.SCR'
            checks['native_mouse_menu_action'] = bool(summary) and int(summary[6]) == 2 and capture.is_file()
            checks['snapshot_uses_live_screen'] = capture.is_file() and b'FIRST BYTE SAFE' in capture.read_bytes() and b'Command Menu' not in capture.read_bytes()
        if name == 'program':
            checks['real_child_verified_callback_absent'] = (folder / 'CHILD.OK').is_file() and (folder / 'CHILD.OK').read_bytes() == b'MOUSE CHILD\r\n'
        if mode == 'Q':
            checks['retained_callback_invoked_and_reclaimed'] = bool(summary) and tuple(map(int, (summary[3],summary[4],summary[6],summary[7]))) == (0x030e,1,1,1)
        if mode == 'R':
            checks['invalid_scale_rejected_before_dial'] = bool(summary) and int(summary[3]) == 7 and not result['commands']
        if mode in ('B','U'):
            checks['BIOS_fallback_without_mouse_registration'] = bool(summary) and int(summary[8]) == 0
        result.update(passed=all(checks.values()), mouse_report=report,
                      observer_sha256=sha(out / 'MOBS.EXE'), production_binary_sha256=sha(binary))
        (folder / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
        results.append(result)
        print(name, 'MOUSE PASS' if result['passed'] else checks, flush=True)
    report = dict(passed=all(c['passed'] for c in results), cases=results,
        sources=sources, sources_unchanged=all(sha(ROOT / p) == h for p,h in sources.items()),
        binary_sha256=sha(binary), observer_sha256=sha(out / 'MOBS.EXE'),
        scope='Actual8086 DOS production terminal and native registered mouse callback, independent CRT observer, menu action/real DOS child, driver snapshots and controlled TSR repair/reclaim. Physical input and other kernels remain separate.')
    report['passed'] &= report['sources_unchanged']
    (out / 'checks.json').write_text(json.dumps(report, indent=2) + '\n')
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
