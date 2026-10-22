#!/usr/bin/env python3
"""Stage current source-built DOS programs and an authored ASPECT example."""
import argparse,json
from pathlib import Path
import shutil
import subprocess
import sys
from build_aspect_runner import ROOT, sha

OUT = ROOT / 'build/dos-package'


def main(mouse=False,stage_current=False):
    output=ROOT/'build/dos-package-mouse' if mouse else OUT
    for name in ([] if stage_current else ['terminal', 'setup', 'xlt_editor', 'aspect_runner', 'aspect_compiler_dos']):
        subprocess.run([sys.executable, str(ROOT / f'standalone/build_{name}.py'),
                        *(['--mouse'] if mouse and name in ('terminal','setup') else [])], check=True)
    output.mkdir(parents=True, exist_ok=True)
    files = {'TERMINAL.EXE': ('terminal-mouse' if mouse else 'terminal')+'/TERMINAL.EXE', 'ASPECT.EXE': 'aspect-runner/ASPECT.EXE',
             'PRMEDIT.EXE': ('setup-mouse' if mouse else 'setup')+'/PRMEDIT.EXE', 'XLTEDIT.EXE': 'xlt-editor/XLTEDIT.EXE',
             'ASPCOMP.EXE': 'aspect-compiler-dos/ASPCOMP.EXE'}
    inputs={}
    for leaf, relative in files.items():
        source=ROOT/'build'/relative;manifest=source.parent/'manifest.json';metadata=json.loads(manifest.read_text())
        assert metadata.get('original_inputs',[])==[] and metadata['binary_sha256']==sha(source)
        assert all(not Path(p).is_absolute() and '..' not in Path(p).parts and
                   Path(p).parts[0] not in ('analysis','build') and sha(ROOT/p)==h
                   for p,h in metadata['sources'].items())
        if leaf=='PRMEDIT.EXE':assert metadata['field_count']==(50 if mouse else 48)
        inputs[leaf]={'manifest':str(manifest.relative_to(ROOT)),'sha256':sha(manifest)}
        shutil.copyfile(source, output / leaf)
    sys.path.insert(0, str(ROOT / 'src/aspect'))
    from compiler import compile_source
    source = 'proc main\r\nmessage "ASPECT script ready"\r\nendproc\r\n'
    (output / 'HELLO.ASP').write_bytes(source.encode('cp437'))
    (output / 'HELLO.ASX').write_bytes(compile_source(source))
    link = ('proc main\r\ntransmit "^M"\r\nwaitfor "login:" 10\r\n'
            'if waitfor\r\nmessage "Prompt received"\r\n'
            'else\r\nmessage "Prompt not received"\r\nendif\r\nendproc\r\n')
    (output / 'LINK.ASP').write_bytes(link.encode('cp437'))
    (output / 'LINK.ASX').write_bytes(compile_source(link))
    instructions = ('PCPlus source reconstruction - current DOS programs\r\n'
                    '\r\nStart: TERMINAL COM1 38400 8N1 SOFT\r\n'
                    'Configured modem: TERMINAL @PCPLUS.PRM /D:5551234 /I:3\r\n'
                    '/I:0..32767 sets initialization reply seconds per command.\r\n'
                    'Omitted or zero keeps legacy initialization without reply waiting.\r\n'
                    'Positive waits for OK; ERROR/timeout prevents dialing.\r\n'
                    'Use initialization commands supported by your actual modem.\r\n'
                    'With the analog bridge, dial its local call target first.\r\n'
                    'Enter the BBS hostname at CONNECT> after modem carrier.\r\n'
                    'Scripts: Alt-Z, File, A Run script, then HELLO.ASX.\r\n'
                    'Connected scripts resume automatically after success.\r\n'
                    'Offline scripts wait for a key before returning.\r\n'
                    'Or run directly: ASPECT HELLO.ASX\r\n'
                    'Compile in DOS: ASPCOMP HELLO.ASP\r\n'
                    'Or select an output: ASPCOMP HELLO.ASP DEMO.ASX\r\n'
                    'A failed compile preserves an existing output.\r\n'
                    'The compiler covers the maintained ASPECT language subset.\r\n'
                    'Or compile and run: ASPECT HELLO.ASP\r\n'
                    'A missing ASX also compiles its ASP sibling automatically.\r\n'
                    'Keep ASPCOMP.EXE beside ASPECT.EXE.\r\n'
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
                    'WHEN/CWHEN, deferred CALL and SET WHENCASE are available.\r\n'
                    'Other script and application services remain incomplete.\r\n'
                    'Use Escape to cancel. Unknown commands report an error.\r\n'
                    'PRMEDIT edits an existing supported profile; no profile is bundled.\r\n')
    if mouse:
        instructions+=('\r\nMouse build: matching 50-field PRMEDIT is included.\r\n'
                       'Alt-F10, Terminal page, Mouse X/Y scale: 1..999.\r\n'
                       'F10 saves; Escape closes; acknowledge to resume with new scales.\r\n'
                       'Setup and the return prompt use the keyboard.\r\n'
                       'Repair before connecting: TERMINAL /S @PCPLUS.PRM\r\n'
                       'A mouse restore failure retains memory; resolve the driver or restart DOS.\r\n')
    (output / 'README.TXT').write_bytes(instructions.encode('ascii'))
    result = dict(original_inputs=[],experimental_mouse=mouse,input_manifests=inputs,sources={'standalone/package_dos.py': sha(Path(__file__)),
                    'src/aspect/compiler.py': sha(ROOT / 'src/aspect/compiler.py')},
                  files={leaf: sha(output / leaf) for leaf in [*files, 'HELLO.ASP', 'HELLO.ASX', 'LINK.ASP', 'LINK.ASX', 'README.TXT']},
                  scope='Current source-built terminal and sibling helpers with authored example. No original executable or private configuration; full application distribution remains incomplete.')
    (output / 'manifest.json').write_text(json.dumps(result, indent=2) + '\n')
    print('DOS programs staged:', output)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--mouse',action='store_true')
    parser.add_argument('--stage-current',action='store_true',help='Stage existing products after checking binary and current source identities; skip rebuilding')
    args=parser.parse_args();main(args.mouse,args.stage_current)
