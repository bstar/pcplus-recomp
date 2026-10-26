#!/usr/bin/env python3
"""Build the source-only DOS16 directory selection proposal component."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
from build_phone_log_file import stable_header

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/directory-selection'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    units = ['src/directory/directory_selection.c', 'src/config/live_configuration.c',
             'src/config/terminal_import.c', 'src/config/modem_import.c',
             'src/config/transfer_import.c', 'src/config/prm_dos.c',
             'src/directory/directory_live.c', 'src/directory/directory_dos.c',
             'standalone/directory_selection_diagnostic.c']
    headers = ['src/directory/directory_selection.h', 'src/directory/directory_live.h',
               'src/directory/directory_dos.h', 'src/config/live_configuration.h',
               'src/config/terminal_import.h', 'src/config/modem_import.h',
               'src/config/transfer_import.h', 'src/config/prm_dos.h',
               'src/config/irq_policy.h']
    flags = ['-q', '-bt=dos', '-0', '-ms', '-s', '-w4', '-we', '-zld',
             '-dDIRECTORY_KEY_BINDINGS', '-dTERMINAL_CUSTOM_IRQ',
             '-i=' + str(ROOT/'src/config'), '-i=' + str(ROOT/'src/directory')]
    objects = []
    for source in units:
        obj = Path(source).stem + '.obj'
        subprocess.run(['wcl', '-c', *flags, '-fo=' + obj,
                        os.path.relpath(ROOT/source, OUT)], cwd=OUT, check=True)
        stable_header(OUT/obj, source)
        objects.append(obj)
    asm = 'reconstruction/directory_dial/bounded.asm'
    subprocess.run(['nasm', '-fobj', asm, '-o', str(OUT/'number.obj')], cwd=ROOT, check=True)
    objects.append('number.obj')
    subprocess.run(['wcl', *flags, '-k8192', '-fm=SELECTION.map', '-fe=SELECT.EXE',
                    *objects], cwd=OUT, check=True)
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    sources = units + headers + [asm, 'standalone/build_directory_selection.py',
                               'standalone/build_phone_log_file.py']
    report = dict(kind='source-only-pure-directory-selection-proposal', original_inputs=[],
                  binary_sha256=sha(OUT/'SELECT.EXE'),
                  objects={n: sha(OUT/n) for n in objects},
                  sources={n: sha(ROOT/n) for n in sorted(sources)},
                  proposal_bytes=1190, stack_bytes=8192,
                  limitations=['Component only; live UI and selected-entry adoption remain open.',
                               'Path spellings and binding syntax do not establish resource identity or availability.'])
    (OUT/'manifest.json').write_text(json.dumps(report, indent=2)+'\n')
    print('Built SELECT.EXE', report['binary_sha256'])


if __name__ == '__main__':
    main()
