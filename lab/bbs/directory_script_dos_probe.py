#!/usr/bin/env python3
"""Run the owned Synchronet login/editor audit through a directory-bound script.

Reuse the immutable-binary/observer/unsaved-editor harness, changing only the
synthetic directory fixture, script source and keyboard schedule. Neither the
menu launcher nor the keyboard supplies credentials in this experiment.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'lab/bbs/script_login_dos_probe.py'
text = BASE.read_text()
use_when = '--when' in sys.argv
if use_when:
    sys.argv.remove('--when')


def replace(old, new):
    global text
    assert text.count(old) == 1, old
    text = text.replace(old, new)


# Inject a declared synthetic directory factory into the unchanged DOS runner.
# Its selected entry carries the script stem and the owned account's password.
factory = '''
def bound_directory(**options):
    data = bytearray(directory_image(**options))
    start = 250 + (options['entry'] - 1) * 114
    data[start+52:start+61] = b'LOGON\\0\\0\\0\\0'
    data[start+75:start+86] = b'LABPASS42\\0\\0'
    return bytes(data)
'''
old = "    prelude = (f'assert text.count({before!r}) == text.count({after!r}) == 1\\n'"
new = ("    fixture_code = " + repr(factory) + "\n"
       "    prelude_fixture = (\"assert text.count('async def run(args):') == 1\\n\"\n"
       "                       + 'text = text.replace(\\\"directory_fixture=directory_image(\\\", \\\"directory_fixture=bound_directory(\\\")\\n'\n"
       "                       + 'text = text.replace(\\\"async def run(args):\\\", ' + repr(fixture_code + '\\nasync def run(args):') + ')\\n')\n"
       "    prelude = (f'assert text.count({before!r}) == text.count({after!r}) == 1\\n'")
replace(old, new)
replace("adapter.replace(marker, prelude + marker)", "adapter.replace(marker, prelude_fixture + prelude + marker)")
start = text.index("    source = ('proc main")
end = text.index("    (stage / 'LOGON.ASP')", start)
source = ('proc main\r\nwaitfor "Login:" 25\r\nif waitfor\r\n'
          'transmit "LABUSER^M"\r\nwaitfor "Password:" 10\r\nif waitfor\r\n'
          'transmit $D_PWORD\r\ntransmit "^M"\r\nmessage "LOGIN SENT"\r\n'
          'else\r\nmessage "PASSWORD PROMPT NOT RECEIVED"\r\nendif\r\n'
          'else\r\nmessage "LOGIN PROMPT NOT RECEIVED"\r\nendif\r\nendproc\r\n')
if use_when:
    source = ('proc main\r\nwhen 0 "Login:" transmit "LABUSER^M"\r\n'
              'waitfor "Password:" 25\r\nif waitfor\r\ncwhen 0\r\n'
              'transmit $D_PWORD\r\ntransmit "^M"\r\nmessage "LOGIN SENT"\r\n'
              'else\r\nmessage "PASSWORD PROMPT NOT RECEIVED"\r\nendif\r\nendproc\r\n')
text = text[:start] + '    source = ' + repr(source) + '\n' + text[end:]
replace("    keys = ('p13000 a-z p300 a p300 l o g o n . a s x enter '\n            'p8000 ' + original[len(login):])",
        "    keys = 'p25000 ' + original[len(login):]")
replace("'--dial-fixture', '--timeout', '140'", "'--directory-fixture', '--entry', '3', '--timeout', '160'")
# A previous cancelled/failed session can retain the Notices sub-board. Select
# writable General explicitly instead of depending on mutable account history.
replace("    if args.hook_session:keys=hook_session_probe.schedule(keys)",
        "    if args.hook_session:\n"
        "        assert keys.count('P p2000 K E Y T E S T') == 1\n"
        "        keys=keys.replace('P p2000 K E Y T E S T','J p600 1 enter p800 2 enter p1000 P p2000 K E Y T E S T')\n"
        "        keys=hook_session_probe.schedule(keys)")

replace("sources = hook_sources + [ROOT/'lab/bbs/hook_session_probe.py', Path(__file__), recipe_path, ROOT / 'src/aspect/compiler.py']",
        "sources = hook_sources + [ROOT/'lab/bbs/hook_session_probe.py', Path(__file__), ROOT / 'lab/bbs/script_login_dos_probe.py', recipe_path, ROOT / 'src/aspect/compiler.py']")
replace("'editor_dos_probe.py', 'test_dos.py', 'modem.py', 'check_editor_dos.py')",
        "'editor_dos_probe.py', 'test_dos.py', 'modem.py', 'check_editor_dos.py')]\n"
        "    sources += [ROOT / 'standalone/directory_fixtures.py', ROOT / 'standalone/directory_test_support.py']\n"
        "    # Existing harness dependencies remain bound below.\n"
        "    sources += [ROOT / 'lab/bbs' / leaf for leaf in ()")
replace("scope='Actual DOS menu-launched source-built ASPECT sends synthetic local Synchronet credentials; native WAITFOR gates password transmission. INT1C passively rejects launch-error or blocking return prompts; successful connected script resumes parent rendering and unsaved stock-editor checks. No physical modem, full script renderer or whole-application claim.'",
        "scope='Actual DOS directory-bound ASPECT waits for Login and Password, then transmits the selected synthetic directory password explicitly. No BIOS credential or script-launch keys. Parent resumes stock Synchronet editor; directory accounting, device restoration and draft abort are checked. No physical modem or full application claim.'")
if use_when:
    replace('ASPECT waits for Login and Password',
            'ASPECT uses native WHEN to transmit the username when Login arrives during WAITFOR')
exec(compile(text, str(BASE), 'exec'), {'__file__': __file__, '__name__': '__main__'})
