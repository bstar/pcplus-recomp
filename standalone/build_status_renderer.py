#!/usr/bin/env python3
"""Link full recovered status drawing with real text services and far bridges."""
import hashlib
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/status-renderer'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    objects, deps = [], {}
    def asm(source, flags=()):
        obj = OUT / (str(len(objects)) + '.obj')
        subprocess.run(['nasm', '-f', 'obj', '-Ireconstruction/uart/', '-Istandalone/',
                        *flags, source, '-o', str(obj)], cwd=ROOT, check=True)
        objects.append(obj)
        deps[source] = sha(ROOT / source)
    for source in ('status_refresh', 'status_fill'):
        asm('reconstruction/terminal_reset/' + source + '.asm',
            ['-DTERMINAL_RESET_OMF', '-DSTATUS_CONFIG_CODE', '-Dtext_fill_cells=status_text_fill',
             '-Dtext_write_packed=status_text_packed', '-Dterminal_reset_ui_75e8=status_ui_printf',
             '-Dterminal_reset_ui_7630=status_character_fill', '-Dterminal_reset_status_message=status_message'])
    asm('src/status/status_helpers.asm', ['-DSTATUS_HELPERS_CONFIG',
        '-Dui_write_string=status_write_string', '-Dprogram_strlen=status_strlen'])
    asm('src/status/status_renderer_bridge.asm')
    for source in ('write_string', 'coordinate', 'cga_blank', 'cga_unblank'):
        asm('reconstruction/ui_windows/' + source + '.asm', ['-DUI_WINDOWS_OMF'])
    for source in ('fill', 'packed', 'cga_sync'):
        asm('reconstruction/text/' + source + '.asm', ['-DTEXT_OMF'])
    asm('reconstruction/program_exec/strlen.asm', ['-DPROGRAM_EXEC_OMF'])
    asm('standalone/status_renderer_host.asm')
    obj = OUT / 'formatter.obj'
    subprocess.run(['wcc', '-q', '-bt=dos', '-0', '-ms', '-ecc', '-s', '-w4', '-we',
                    '-fo=' + str(obj), 'src/status/status_formatter.c'], cwd=ROOT, check=True)
    objects.append(obj)
    deps.update({name: sha(ROOT / name) for name in ('src/status/status_formatter.c',
        'src/status/status_formatter.h', 'src/status/status_state.inc', 'standalone/status_renderer_state.inc', 'reconstruction/uart/encodings.inc')})
    subprocess.run(['wlink', 'system', 'dos', 'option', 'quiet', 'option',
                    'map=' + str(OUT / 'status.map'), 'name', str(OUT / 'STATUS.EXE'),
                    'file', ','.join(map(str, objects))], cwd=ROOT, check=True)
    result = dict(original_inputs=[], source_dependencies=deps,
                  builder_sha256=sha(Path(__file__)), binary_sha256=sha(OUT / 'STATUS.EXE'))
    (OUT / 'manifest.json').write_text(json.dumps(result, indent=2) + '\n')
    print('Built full native status renderer', result['binary_sha256'])


if __name__ == '__main__':
    main()
