#!/usr/bin/env python3
"""Stage current source-built DOS programs and an authored ASPECT example."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
from build_aspect_runner import ROOT, sha

OUT = ROOT / 'build/dos-package'


def main():
    for name in ['terminal', 'setup', 'xlt_editor', 'aspect_runner']:
        subprocess.run([sys.executable, str(ROOT / f'standalone/build_{name}.py')], check=True)
    OUT.mkdir(parents=True, exist_ok=True)
    files = {'TERMINAL.EXE': 'terminal/TERMINAL.EXE', 'ASPECT.EXE': 'aspect-runner/ASPECT.EXE',
             'PRMEDIT.EXE': 'setup/PRMEDIT.EXE', 'XLTEDIT.EXE': 'xlt-editor/XLTEDIT.EXE'}
    for leaf, relative in files.items():
        shutil.copyfile(ROOT / 'build' / relative, OUT / leaf)
    sys.path.insert(0, str(ROOT / 'src/aspect'))
    from compiler import compile_source
    source = 'proc main\r\nmessage "ASPECT script ready"\r\nendproc\r\n'
    (OUT / 'HELLO.ASP').write_bytes(source.encode('cp437'))
    (OUT / 'HELLO.ASX').write_bytes(compile_source(source))
    instructions = ('PCPlus source reconstruction - current DOS programs\r\n'
                    '\r\nStart: TERMINAL COM1 38400 8N1 SOFT\r\n'
                    'Scripts: Alt-Z, File, A Run script, then HELLO.ASX.\r\n'
                    'Press a key after the child finishes to return to the terminal.\r\n'
                    'Or run directly: ASPECT HELLO.ASX\r\n'
                    '\r\nScripts run as a separate DOS process. This interpreter implements\r\n'
                    'a subset of ASPECT; serial scripting is not connected yet.\r\n'
                    'Use Escape to cancel. Unknown commands report an error.\r\n'
                    'PRMEDIT edits an existing supported profile; no profile is bundled.\r\n')
    (OUT / 'README.TXT').write_bytes(instructions.encode('ascii'))
    result = dict(original_inputs=[], sources={'standalone/package_dos.py': sha(Path(__file__)),
                    'src/aspect/compiler.py': sha(ROOT / 'src/aspect/compiler.py')},
                  files={leaf: sha(OUT / leaf) for leaf in [*files, 'HELLO.ASP', 'HELLO.ASX', 'README.TXT']},
                  scope='Current source-built terminal and sibling helpers with authored example. No original executable or private configuration; full application distribution remains incomplete.')
    (OUT / 'manifest.json').write_text(json.dumps(result, indent=2) + '\n')
    print('DOS programs staged:', OUT)


if __name__ == '__main__':
    main()
