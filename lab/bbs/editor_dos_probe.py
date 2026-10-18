#!/usr/bin/env python3
"""Run the maintained DOS BBS harness against an explicit immutable binary copy.
Usage: editor_dos_probe.py /absolute/TERMINAL.EXE <test_dos.py arguments>
Only redirects its binary boundary; all fixtures, UART sampler, protocol and
result validation execute the unmodified maintained harness implementation.
"""
import argparse,sys
from pathlib import Path
binary=Path(sys.argv.pop(1)).resolve()
assert binary.is_file() and binary.suffix.upper()=='.EXE'
if '--keys' in sys.argv:
 keys=sys.argv[sys.argv.index('--keys')+1]
 invalid={'insert','delete','pageup','pagedown','pgdn','backspace'} & set(keys.split())
 assert not invalid,'DOSBox ADDKEY queue stops at unsupported tokens; use ins/del/pgup/pgdown/bs: '+repr(invalid)
 parser=argparse.ArgumentParser(add_help=False)
 parser.add_argument('--directory-browser',action='store_true');parser.add_argument('--directory-fixture',action='store_true');parser.add_argument('--dial-fixture',action='store_true')
 parser.add_argument('--entry',type=int,default=3);parser.add_argument('--wait',type=int,default=12)
 options,_=parser.parse_known_args(sys.argv[1:])
 automatic=options.directory_fixture or options.dial_fixture
 prefix='p1000 ' if automatic else 'p1000 a t d enter '
 if options.directory_browser:prefix='p500 '+('down p100 '*(options.entry-1))+'enter p1000 '
 command='ADDKEY '+prefix+keys+f' p{options.wait*1000} a-x'
 assert len(command)<500,'Complete ADDKEY command exceeds safe DOS command-line bound'
source=Path(__file__).with_name('test_dos.py')
text=source.read_text()
old="binary=ROOT/'build/terminal/TERMINAL.EXE'"
assert text.count(old)==1,'Maintained harness binary selection changed; review adapter'
text=text.replace(old,'binary=Path('+repr(str(binary))+')')
exec(compile(text,str(source),'exec'),{'__file__':str(source),'__name__':'__main__'})
