#!/usr/bin/env python3
"""Compose native mouse/keyboard with a maintained driver-state owner."""
import json
from pathlib import Path
import subprocess
from omf_imports import records, externals
from build_native_mouse import ROOT, sha

OUT = ROOT / 'build/mouse-keyboard'


def main(dos_memory=False):
    output = ROOT / 'build/mouse-keyboard-dos' if dos_memory else OUT
    output.mkdir(parents=True, exist_ok=True)
    native = json.loads((ROOT / 'reconstruction/program_mouse/provenance.json').read_text())
    defaults = json.loads((ROOT / 'reconstruction/program_mouse/defaults.json').read_text())
    keyboard = json.loads((ROOT / 'reconstruction/keyboard/provenance.json').read_text())
    include = '-I' + str(ROOT / 'reconstruction/uart') + '/'
    sources = [ROOT / unit['file'] for unit in native['units']]
    for source, unit in zip(sources, native['units']):
        binary = output / (source.stem + '.bin')
        subprocess.run(['nasm', '-fbin', include, str(source), '-o', str(binary)], check=True)
        assert sha(binary) == unit['sha256']
    default_source = ROOT / 'reconstruction/program_mouse/defaults.asm'
    subprocess.run(['nasm', '-fbin', str(default_source), '-o', str(output / 'defaults.bin')], check=True)
    assert sha(output / 'defaults.bin') == defaults['sha256']
    core = ROOT / 'reconstruction/keyboard/core.asm'
    for i, unit in enumerate(keyboard['ranges']):
        binary = output / f'keyboard-{i}.bin'
        subprocess.run(['nasm', '-fbin', include, '-DKEYBOARD_REGION=' + str(i), str(core), '-o', str(binary)], check=True)
        assert sha(binary) == unit['sha256']
    sources += [default_source, core, ROOT / 'src/mouse/state.asm', ROOT / 'src/mouse/platform.asm',
                ROOT / 'standalone/mouse_keyboard_bridge.asm']
    if dos_memory:
        sources.append(ROOT / 'src/mouse/dos_memory.asm')
    objects = []
    for source in sources:
        obj = output / (source.stem + '.obj')
        subprocess.run(['nasm', '-fobj', include, '-DPROGRAM_MOUSE_OMF', '-DKEYBOARD_OMF',
                        str(source), '-o', str(obj)], check=True)
        objects.append(str(obj))
    c_sources = [ROOT / 'src/mouse/owner.c', ROOT / 'standalone/mouse_keyboard_diagnostic.c']
    subprocess.run(['wcl', '-q', '-bt=dos', '-0', '-ms', '-ecc', '-s', '-w4', '-we', '-k8192',
                    *(['-dMOUSE_DOS_PLATFORM'] if dos_memory else []),
                    '-i=' + str(ROOT / 'src/mouse'), '-fm=MOUSEKEY.map', '-fe=MOUSEKEY.EXE',
                    *[str(p) for p in c_sources], *objects], cwd=output, check=True)
    owner_imports = [name.decode() for kind, payload, raw in records((output / 'owner.o').read_bytes())
                     if kind == 0x8c for name, index in externals(payload)]
    if dos_memory:
        assert all(name.startswith('_mouse_') or name == '_small_code_' for name in owner_imports), owner_imports
    child = ROOT / 'standalone/mouse_keyboard_child.asm'
    for name, extra in [('MUTATE', []), ('VECTOR', ['-DCHANGE_VECTOR'])]:
        subprocess.run(['nasm', '-fbin', *extra, str(child), '-o', str(output / (name + '.COM'))], check=True)
    sources += c_sources + [child, Path(__file__), ROOT / 'standalone/build_native_mouse.py',
        ROOT / 'src/mouse/owner.h', ROOT / 'reconstruction/uart/encodings.inc',
        ROOT / 'reconstruction/keyboard/provenance.json', ROOT / 'reconstruction/program_mouse/provenance.json',
        ROOT / 'reconstruction/program_mouse/defaults.json', ROOT / 'standalone/omf_imports.py']
    manifest = dict(binary_sha256=sha(output / 'MOUSEKEY.EXE'), original_inputs=[], dos_memory=dos_memory,
                    owner_imports=owner_imports,
                    native_code_and_guard_bytes=599, native_default_data_bytes=30,
                    children={name: sha(output / name) for name in ('MUTATE.COM', 'VECTOR.COM')},
                    sources={str(p.relative_to(ROOT)): sha(p) for p in sources},
                    scope='Composed native mouse producer/keyboard consumer, guarded PRM scale/config and real INT33 state ownership. Separate diagnostic; no normal terminal/ASPECT publication.')
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print('MOUSEKEY.EXE', manifest['binary_sha256'])


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dos-memory', action='store_true')
    main(parser.parse_args().dos_memory)
