#!/usr/bin/env python3
"""Current DOS release -> actual SynthModem proxy -> stock owned ENiGMA ZMODEM.

SIP/audio and physical carrier are outside this serial-side lab. The ordinary
Hayes shim supplies modem commands only; SynthModem alone owns Telnet. Actual
BBS helper bytes, protocol controls, files and menu return are audited unchanged.
"""
import argparse
import fcntl
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import time
from enigma import SOURCE, COMMIT, process_pid
from product_inputs import ROOT, select_product, sha


def metadata(name, expected):
    assert re.fullmatch(r'P[A-F0-9]{6}\.BIN', name)
    expected = expected.resolve()
    assert expected.is_relative_to(ROOT / 'build') and expected.is_file()
    code = r'''const root=process.argv[1];process.chdir(root);
const c=require(root+'/core/oputil/oputil_common');c.initConfigAndDatabases(e=>{if(e)throw e;
const F=require(root+'/core/file_entry');F.findByFileNameWildcard(process.argv[2],(e,rows)=>{
if(e)throw e; console.log(JSON.stringify(rows.map(f=>({fileName:f.fileName,filePath:f.filePath,fileSha256:f.fileSha256,areaTag:f.areaTag,meta:f.meta}))));process.exit(0);});});'''
    rows = json.loads(subprocess.check_output(['node', '-e', code, str(SOURCE), name], cwd=SOURCE, text=True))
    good = len(rows) == 1
    if good:
        r = rows[0]
        path = Path(r['filePath']).resolve()
        good = (path.is_relative_to(SOURCE / 'file_base') and r['areaTag'] == 'pcplus_transfer' and
                r['fileName'] == name and r['fileSha256'] == sha(expected) and
                int(r['meta']['byte_size']) == expected.stat().st_size and path.read_bytes() == expected.read_bytes())
    print(json.dumps(dict(passed=good, entries=rows)))
    return 0 if good else 1


def post_count():
    with sqlite3.connect('file:' + str(SOURCE / 'db/message.sqlite3') + '?mode=ro', uri=True) as db:
        return db.execute('SELECT COUNT(*) FROM message').fetchone()[0]


def main(a):
    assert re.fullmatch('[a-z0-9-]+', a.label)
    assert process_pid(), 'Owned stock ENiGMA must already be running'
    lock = (ROOT / 'build/bbs-lab/enigma/.dos-integration.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    binary, sources = select_product(a.terminal, 'TERMINAL.EXE')
    from terminal_geometry import terminal_geometry
    geometry = terminal_geometry(binary)
    logical=a.rows-(not a.hidden) if a.size_probe else geometry['rows']
    assert a.size_probe or (a.rows,a.hidden)==(25,0)
    manifest = json.loads((binary.parent / 'manifest.json').read_text())
    assert manifest['experimental_original_reference'] and manifest['special_edition']
    base = ROOT / 'build/bbs-lab'
    wrapper = base / (a.label + '-transfer')
    wrapper.mkdir(parents=True, exist_ok=False)
    output = base / 'results/enigma' / a.label
    assert not output.exists()
    bridge = base / (a.label + '-proxy')
    sources += [ROOT / n for n in ('lab/bbs/test_proxy_transfer_dos.py', 'lab/bbs/test_zmodem_dos.py',
                'lab/bbs/test_transfer_dos.py', 'lab/bbs/modem.py', 'lab/bbs/synthmodem_proxy_serial.js',
                'lab/bbs/audit_zmodem.py', 'lab/bbs/editor-recipes.json', 'lab/bbs/terminal_geometry.py','standalone/display_startup_geometry.asm')]
    before = {str(p.relative_to(ROOT)): sha(p) for p in sources}
    server_paths = [SOURCE / n for n in ('main.js', 'core/client.js', 'core/file_transfer.js',
                    'core/file_entry.js', 'core/file_transfer_protocol_select.js', 'core/upload.js',
                    'core/file_base_area.js', 'core/multi_line_edit_text_view.js', 'core/view_controller.js',
                    'config/menus/loc-file_base.hjson', 'config/config.hjson', 'package-lock.json','core/string_util.js',
                    'core/user_interrupt_queue.js','core/menu_module.js')]
    server_paths.append(SOURCE.parent / 'helpers/sexyz')
    server_before = {str(p.relative_to(ROOT)): sha(p) for p in server_paths}
    posts = post_count()
    name = a.download_name
    assert name=='PCXTEST.BIN' or re.fullmatch(r'P[A-F0-9]{6}\.BIN',name)
    fixture = SOURCE / 'file_base/pcplus_transfer' / name
    if a.mode == 'upload':
        name = 'P' + hashlib.sha256(a.label.encode()).hexdigest()[:6].upper() + '.BIN'
        fixture = wrapper / name
        payload=bytes(range(256))*4+hashlib.sha256(a.label.encode()).digest()
        if a.upload_bytes!=len(payload):
            pattern=bytes(range(256))+b'\x1b[8;50;80t\xff\xfb\x1f\xff\xfa\x1f'+hashlib.sha256(a.label.encode()).digest()
            payload=(pattern*((a.upload_bytes+len(pattern)-1)//len(pattern)))[:a.upload_bytes]
        fixture.write_bytes(payload)
        assert not (SOURCE / 'file_base/pcplus_transfer' / name).exists()
    if a.size_probe:assert manifest['experimental_display_startup']
    assert fixture.is_file()
    fixture_sha = sha(fixture)
    prefix = json.loads((ROOT / 'lab/bbs/editor-recipes.json').read_text())['enigma_unsaved']['keyboard_input']
    prefix = prefix[:prefix.index('M enter')].replace('n p6000 n p3000 enter', 'n p6000 enter')
    prefix = 'p900 enter p2500 l o c enter ' + prefix + 'c-y p2000 F enter p2000 '
    if a.post_menu_reset:assert re.fullmatch(r'P[A-F0-9]{6}\.BIN',name)
    filename = ' '.join(name)
    if a.mode == 'download':
        keys = prefix + ('S enter p2000 ' + filename + ' enter p1500 enter p2000 t p1500 q p1500 escape '
                         'p1000 D enter p2000 a p1500 enter p1000 '
                         'a-z p150 pgdown p300 f2 p150 f2 p300 D : \\ R E C V \\ enter '
                         'p30000 enter p2000 S enter p1500 ' + filename + ' enter p1500 enter')
        start = b'D\r'
        post = b'S\r'
        if a.post_menu_reset:
            # An earned achievement can pause the first list transition.
            # Escape dismisses that pause, then exits the list; another Escape
            # is harmless at File Base. Reopen the current filter before the
            # final checks. The full original search remains before download.
            old='p2000 S enter p1500 '+filename+' enter p1500 enter'
            assert keys.count(old)==1
            keys=keys.replace(old,'p2000 L enter p1500 escape p1500 escape p1500 L enter p1500')
            post=b'\x1b\x1bL\r'
        size_text=subprocess.check_output(['node','-e','process.stdout.write(require(process.argv[1]).formatByteSize(Number(process.argv[2])))',str(SOURCE/'core/string_util.js'),str(fixture.stat().st_size)],text=True)
        menus = [name + ' ', size_text+' ', 'KB ']
    else:
        # BIN scanning supplies a filename description (file_base_area.js), so
        # upload.js starts details at tags: tags -> year -> Continue (two Tabs).
        # A third Tab cycles back into description and Enter inserts a newline.
        keys = prefix + ('U enter p1500 tab p1000 tab p1000 tab p1000 enter p1500 enter p1000 '
                         'a-z p150 pgup p300 f2 p150 f2 p300 D : \\ S E N D \\ * . B I N enter '
                         'p30000 tab p1000 tab p1000 enter p6000 enter p2000 L enter p5000')
        start = b'U\r'
        post = b'L\r'
        menus = [name]
        if a.post_menu_reset:
            old='p2000 L enter p5000'
            assert keys.count(old)==1
            keys=keys.replace(old,'p2000 L enter p1500 escape p1500 escape p1500 L enter p5000')
            post=b'\x1b\x1bL\r'
    keys=keys.replace('p30000','p'+str(a.transfer_wait_ms))
    assert len('ADDKEY p1000 ' + keys + ' p3000 a-x') < 500
    proxy = subprocess.Popen(['node', str(ROOT / 'lab/bbs/synthmodem_proxy_serial.js'), '--runtime', str(a.runtime.resolve()),
                             '--output', str(bridge), '--bbs-port', '23233', '--framing-ms', '250',
                             '--byte-delay-ms', '0', '--terminal-rows', str(logical),*(['--probe-terminal-size'] if a.size_probe else [])],
                             stdout=subprocess.DEVNULL, stderr=(wrapper / 'proxy.log').open('w'))
    try:
        deadline = time.monotonic() + 15
        while not (bridge / 'ready.json').exists():
            assert proxy.poll() is None and time.monotonic() < deadline, 'Proxy readiness failed'
            time.sleep(.05)
        ready = json.loads((bridge / 'ready.json').read_text())
        command = [sys.executable, str(ROOT / 'lab/bbs/test_zmodem_dos.py'), 'enigma', '--port', '23233',
                   '--upstream-port', str(ready['endpoint']['port']), '--binary', str(binary), '--sha256', sha(binary),
                   '--label', a.label, '--mode', a.mode, '--file', name + '=' + str(fixture),
                   '--dial-fixture', '--com', '3', '--irq', '5', '--cpu', '8086', '--mouse-scales', '8', '4',
                   '--hangup-guard-ms', '500',
                   '--keys', keys, '--start-input-hex', start.hex(), '--post-input-hex', post.hex(),
                   '--timeout', '260', '--wait', '8']
        if a.size_probe:command+=['--display-rows',str(a.rows),'--status-hidden',str(a.hidden)]
        for menu in menus:
            command += ['--post-menu', menu]
        if a.mode == 'upload':
            audit = [str(ROOT / 'tools/bbs-dev'), '--command', 'python', str(Path(__file__).resolve()),
                     '--audit-name', name, '--expected', str(fixture)]
            command += ['--server-directory', str(SOURCE / 'file_base/pcplus_transfer'),
                        '--server-audit-command-json', json.dumps(audit)]
        (wrapper / 'command.json').write_text(json.dumps(command, indent=2) + '\n')
        with (wrapper / 'harness.log').open('w') as log:
            code = subprocess.call(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
        deadline = time.monotonic() + 5
        while not (bridge / '1-closed.json').exists() and time.monotonic() < deadline:
            time.sleep(.05)
        closed = json.loads((bridge / '1-closed.json').read_text())
        result = json.loads((output / 'result.json').read_text())
        model = json.loads((output / 'modem.json').read_text())
        # This directly binds the raw serial adapter's bytes to the independent
        # protocol auditor's observed streams; literal FF must survive once.
        checks = dict(harness=code == 0 and result['passed'], source_unchanged=all(sha(ROOT / n) == h for n, h in before.items()),
                      server_inputs_unchanged=all(sha(ROOT / n) == h for n, h in server_before.items()),
                      proxy_source_unchanged=closed['source_unchanged'], no_post_saved=posts == post_count(),
                      fixture_unchanged=sha(fixture) == fixture_sha, raw_upstream=result.get('raw_upstream') is True,
                      modeled_guarded_hangup=len([e for e in model['events'] if e['kind']=='guarded-hangup'])==1,
                      same_proxy_input=(bridge / '1-serial-input.bin').read_bytes() == (output / 'bbs-sent.bin').read_bytes(),
                      same_proxy_output=(bridge / '1-serial-output.bin').read_bytes() == (output / 'display.bin').read_bytes())
        report = dict(passed=all(checks.values()),display_layout=dict(physical_rows=a.rows,logical_rows=logical,status_hidden=a.hidden) if a.size_probe else None, checks=checks, mode=a.mode, terminal_sha256=sha(binary),
                      product_inputs=before, server_inputs=server_before, server_commit=COMMIT, proxy=ready,
                      protocol_checks=result.get('checks'), protocol_errors=result.get('errors'),
                      fixture=dict(name=name, bytes=fixture.stat().st_size, sha256=fixture_sha),
                      scope=__doc__)
        (wrapper / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(dict(passed=report['passed'], checks=checks, protocol_errors=result.get('errors')), indent=2))
        return 0 if report['passed'] else 1
    finally:
        proxy.terminate()
        try:
            proxy.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proxy.kill()
            proxy.wait()


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runtime', type=Path)
    p.add_argument('--terminal', type=Path)
    p.add_argument('--label')
    p.add_argument('--size-probe',action='store_true')
    p.add_argument('--rows',type=int,choices=[25,28,43,50],default=25)
    p.add_argument('--hidden',type=int,choices=[0,1],default=0)
    p.add_argument('--download-name',default='PCXTEST.BIN')
    p.add_argument('--post-menu-reset',action='store_true',help='Dismiss a queued achievement/list before reopening the post-transfer file list')
    p.add_argument('--upload-bytes',type=int,choices=[1056,65539],default=1056)
    p.add_argument('--transfer-wait-ms',type=int,choices=[30000,60000,90000],default=30000)
    p.add_argument('--mode', choices=['download', 'upload'])
    p.add_argument('--audit-name')
    p.add_argument('--expected', type=Path)
    a = p.parse_args()
    if a.audit_name:
        assert a.expected
        raise SystemExit(metadata(a.audit_name, a.expected))
    assert a.runtime and a.terminal and a.label and a.mode
    raise SystemExit(main(a))
