#!/usr/bin/env python3
"""Build a CRT-free assembly parent with the maintained banked mouse owner."""
import json
from pathlib import Path
import re
import subprocess
from build_native_mouse import ROOT, sha
from omf_imports import records, externals

OUT = ROOT / 'build/mouse-bank'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    include = ['-I' + str(ROOT / p) + '/' for p in
               ('src/terminal', 'src/mouse', 'reconstruction/uart')]
    sources, objects = [], []

    def assembly(relative, name=None, flags=()):
        source = ROOT / relative
        obj = OUT / ((name or source.stem) + '.obj')
        subprocess.run(['nasm', '-fobj', *include, *flags, str(source), '-o', str(obj)], check=True)
        sources.append(source)
        objects.append(obj)

    assembly('standalone/mouse_bank_host.asm')
    assembly('src/mouse/bank.asm')
    native = json.loads((ROOT / 'reconstruction/program_mouse/provenance.json').read_text())
    for unit in native['units']:
        source = ROOT / unit['file']
        flat = OUT / (source.stem + '.bin')
        subprocess.run(['nasm', '-fbin', *include, str(source), '-o', str(flat)], check=True)
        assert sha(flat) == unit['sha256']
        assembly(unit['file'], flags=['-DPROGRAM_MOUSE_OMF', '-D_TEXT=MOUSE_CODE', '-DCODE=FARCODE'])
    defaults = json.loads((ROOT / 'reconstruction/program_mouse/defaults.json').read_text())
    default_source = ROOT / 'reconstruction/program_mouse/defaults.asm'
    subprocess.run(['nasm', '-fbin', str(default_source), '-o', str(OUT / 'defaults.bin')], check=True)
    assert sha(OUT / 'defaults.bin') == defaults['sha256']
    keyboard = json.loads((ROOT / 'reconstruction/keyboard/provenance.json').read_text())
    for index, unit in enumerate(keyboard['ranges']):
        flat = OUT / f'keyboard-{index}.bin'
        subprocess.run(['nasm', '-fbin', *include, '-DKEYBOARD_REGION=' + str(index),
            str(ROOT / 'reconstruction/keyboard/core.asm'), '-o', str(flat)], check=True)
        assert sha(flat) == unit['sha256']
    assembly('reconstruction/program_mouse/defaults.asm', flags=['-DPROGRAM_MOUSE_OMF'])
    assembly('reconstruction/keyboard/core.asm', flags=['-DKEYBOARD_OMF'])
    assembly('src/mouse/state.asm')
    for relative in ('src/mouse/platform.asm', 'src/mouse/dos_memory.asm'):
        assembly(relative, flags=['-DMOUSE_BANK', '-D_TEXT=MOUSE_CODE', '-DCODE=FARCODE'])
    assembly('src/mouse/entries.asm')
    assembly('standalone/mouse_keyboard_bridge.asm', flags=[
        '-D_TEXT=MOUSE_CODE', '-DCODE=FARCODE', '-D_mouse_test_emit=_mouse_test_emit_impl'])
    assembly('standalone/mouse_bank_test_entry.asm')
    assembly('src/mouse/dos_memory.asm', 'test_memory', flags=[
        '-D_mouse_platform_allocate=_test_allocate', '-D_mouse_platform_release=_test_release',
        '-D_mouse_platform_vector=_test_vector'])
    assembly('src/process/dos_exec.asm')
    api = re.findall(r'^MOUSE_ENTRY (\w+),(\d+)$', (ROOT / 'src/mouse/abi.inc').read_text(), re.M)
    assert len(api) == 8
    imports = {}
    for relative, flags in [('src/mouse/owner.c', ['-dMOUSE_DOS_PLATFORM', '-nt=MOUSE_CODE', '-nc=FARCODE',
                  *['-d' + name[1:] + '=' + name[1:] + '_impl' for name, words in api]]),
                ('standalone/mouse_bank_diagnostic.c', [])]:
        source = ROOT / relative
        obj = OUT / (source.stem + '.obj')
        subprocess.run(['wcc', '-q', '-bt=dos', '-0', '-ms', '-ecc', '-s', '-w4', '-we',
            '-i=' + str(ROOT / 'src/mouse'), '-i=' + str(ROOT / 'src/process'),
            '-fo=' + str(obj), *flags, str(source)], check=True)
        sources.append(source)
        objects.append(obj)
        imports[relative] = [name.decode() for kind, payload, raw in records(obj.read_bytes())
                             if kind == 0x8c for name, index in externals(payload)]
    assert all(n.startswith('_mouse_') or n == '_small_code_' for n in imports['src/mouse/owner.c'])
    assembly('standalone/mouse_bank_end.asm')
    response = OUT / 'link.lnk'
    response.write_text('system dos\noption quiet\noption map=MOUSEBNK.map\n'
        'option nodefaultlibs\norder clname CODE clname FARCODE clname DATA clname BSS clname STACK\n'
        'name MOUSEBNK.EXE\n' + ''.join('file ' + p.name + '\n' for p in objects))
    subprocess.run(['wlink', '@' + str(response)], cwd=OUT, check=True)
    listing = (OUT / 'MOUSEBNK.map').read_text()
    segments = {name:dict(start=int(seg,16)*16+int(off,16), bytes=int(size,16), segment=int(seg,16))
        for name, seg, off, size in re.findall(
            r'^(\w+)\s+\w+\s+\w+\s+([0-9a-f]{4}):([0-9a-f]{4})\s+([0-9a-f]+)\s*$', listing, re.M|re.I)}
    symbols = {name:int(seg,16)*16+int(off,16) for seg,off,name in re.findall(
        r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$', listing, re.M|re.I)}
    stack_end = symbols['terminal_stack_top']
    assert segments['_TEXT']['start'] == 0 and 60000 < segments['_TEXT']['bytes'] < 65536
    assert segments['MOUSE_CODE']['segment'] != 0 and segments['MOUSE_CODE']['bytes'] < 65536
    assert symbols['mouse_bank_bss_start'] == segments['_BSS']['start']
    assert segments['_BSS']['start'] + segments['_BSS']['bytes'] <= symbols['mouse_bank_bss_end'] <= segments['STACK']['start']
    assert stack_end == segments['STACK']['start'] + segments['STACK']['bytes']
    assert stack_end - segments['_DATA']['start'] <= 0xfff0
    assert all(s['start']+s['bytes'] <= stack_end for s in segments.values())
    child = ROOT / 'standalone/mouse_keyboard_child.asm'
    for name, flags in [('MUTATE', []), ('VECTOR', ['-DCHANGE_VECTOR'])]:
        subprocess.run(['nasm', '-fbin', *flags, str(child), '-o', str(OUT / (name + '.COM'))], check=True)
    sources += [child, Path(__file__), ROOT / 'standalone/build_native_mouse.py', ROOT / 'standalone/omf_imports.py',
        ROOT / 'src/mouse/abi.inc', ROOT / 'src/mouse/owner.h', ROOT / 'src/process/dos_exec.h',
        ROOT / 'src/terminal/far_bridge.inc', ROOT / 'reconstruction/uart/encodings.inc',
        ROOT / 'reconstruction/program_mouse/provenance.json',
        ROOT / 'reconstruction/program_mouse/defaults.json', ROOT / 'reconstruction/keyboard/provenance.json']
    manifest = dict(binary_sha256=sha(OUT / 'MOUSEBNK.EXE'), original_inputs=[], CRT_libraries=[], bank=True, dos_memory=True,
        owner_imports=imports['src/mouse/owner.c'], diagnostic_imports=imports['standalone/mouse_bank_diagnostic.c'],
        segments=segments, retained_paragraphs=0x10+(stack_end+15)//16,
        native_code_and_guard_bytes=599, native_default_data_bytes=30,
        children={name:sha(OUT / name) for name in ('MUTATE.COM', 'VECTOR.COM')},
        sources={str(p.relative_to(ROOT)):sha(p) for p in sources},
        scope='CRT-free assembly parent, banked mouse owner and resident native keyboard; real maintained DOS EXEC. Not yet published in terminal menus or ASPECT.')
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print('MOUSEBNK.EXE', manifest['binary_sha256'])


if __name__ == '__main__':
    main()
