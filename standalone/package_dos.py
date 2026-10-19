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
    link = ('proc main\r\ntransmit "^M"\r\nwaitfor "login:" 10\r\n'
            'if waitfor\r\nmessage "Prompt received"\r\n'
            'else\r\nmessage "Prompt not received"\r\nendif\r\nendproc\r\n')
    (OUT / 'LINK.ASP').write_bytes(link.encode('cp437'))
    (OUT / 'LINK.ASX').write_bytes(compile_source(link))
    instructions = ('PCPlus source reconstruction - current DOS programs\r\n'
                    '\r\nStart: TERMINAL COM1 38400 8N1 SOFT\r\n'
                    'Scripts: Alt-Z, File, A Run script, then HELLO.ASX.\r\n'
                    'Connected scripts resume automatically after success.\r\n'
                    'Offline scripts wait for a key before returning.\r\n'
                    'Or run directly: ASPECT HELLO.ASX\r\n'
                    '\r\nScripts run as a separate DOS process. This interpreter implements\r\n'
                    'a subset of ASPECT, including TRANSMIT and WAITFOR.\r\n'
                    'The menu lends the active port and returns unread data on exit.\r\n'
                    'Direct serial use: ASPECT LINK.ASX /S1:0003:03:N\r\n'
                    'Here 0003 is the hex divisor (38400 baud), 03 is 8N1.\r\n'
                    'Flow: N none, S software, H hardware, B both.\r\n'
                    'LINK sends CR and waits 10 seconds for login:; edit LINK.ASP as needed.\r\n'
                    'It does not dial or send a username/password.\r\n'
                    'Direct use requires DTR asserted; unread input needs a parent.\r\n'
                    'Menu scripts inherit the selected input XLT or seven-bit policy.\r\n'
                    'Unread bytes return unchanged for the terminal to process.\r\n'
                    'Connected scripts share the terminal ANSI screen and history\r\n'
                    'in supported 80x25 profiles when file/printer owners are closed.\r\n'
                    'Admitted script errors return to the terminal with a notice.\r\n'
                    'Other script events and application services remain incomplete.\r\n'
                    'Use Escape to cancel. Unknown commands report an error.\r\n'
                    'PRMEDIT edits an existing supported profile; no profile is bundled.\r\n')
    (OUT / 'README.TXT').write_bytes(instructions.encode('ascii'))
    result = dict(original_inputs=[], sources={'standalone/package_dos.py': sha(Path(__file__)),
                    'src/aspect/compiler.py': sha(ROOT / 'src/aspect/compiler.py')},
                  files={leaf: sha(OUT / leaf) for leaf in [*files, 'HELLO.ASP', 'HELLO.ASX', 'LINK.ASP', 'LINK.ASX', 'README.TXT']},
                  scope='Current source-built terminal and sibling helpers with authored example. No original executable or private configuration; full application distribution remains incomplete.')
    (OUT / 'manifest.json').write_text(json.dumps(result, indent=2) + '\n')
    print('DOS programs staged:', OUT)


if __name__ == '__main__':
    main()
