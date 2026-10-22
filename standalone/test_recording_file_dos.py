#!/usr/bin/env python3
"""Actual DOS exclusive recorder publication, shared owners and compiler/UART replay.

Owned synthetic media, real DOS create/write/close/rename/remove and shared
canonical guards. One case deliberately supplies a read-only kernel handle.
This does not accept the terminal Record UI or physical modem behavior.
"""
import argparse
import hashlib
import json
import os
import shutil
import socket
import subprocess
import threading
from pathlib import Path
from test_terminal import ROOT, SAMPLER


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


DRIVER = (ROOT / 'standalone/recording_file_dos_host.c').read_text()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--banked', action='store_true')
    args = parser.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT / 'build') and not out.exists()
    out.mkdir(parents=True)
    frozen = {}
    for directory, binary in [('aspect-runner', 'ASPECT.EXE'), ('aspect-compiler-dos', 'ASPCOMP.EXE')]:
        base = ROOT / 'build' / directory
        manifest = json.loads((base / 'manifest.json').read_text())
        assert not manifest['original_inputs'] and sha(base / binary) == manifest['binary_sha256']
        for name, digest in manifest['sources'].items():
            assert sha(ROOT / name) == digest, name
            assert name not in frozen or frozen[name] == digest
            frozen[name] = digest
        for path in [base / binary, base / 'manifest.json']:
            frozen[str(path.relative_to(ROOT))] = sha(path)
        shutil.copy2(base / binary, out / binary)
    extra = [Path(__file__).resolve(), ROOT / 'standalone/recording_file_dos_host.c',
             ROOT / 'src/aspect/recorder.c', ROOT / 'src/aspect/recorder.h', ROOT / 'standalone/test_terminal.py',
             *sorted((ROOT / 'src/recording').glob('*.[ch]')),
             *[ROOT / 'src/capture' / name for name in ('capture_file.c', 'capture_file.h', 'capture_fs.c', 'capture_fs.h', 'capture_reservation.c', 'capture_reservation.h')]]
    if args.banked:
        extra += [ROOT / 'src/terminal/config_abi.inc', ROOT / 'src/terminal/far_bridge.inc']
    for path in extra:
        frozen[str(path.relative_to(ROOT))] = sha(path)
    for name, digest in frozen.items():
        copy = out / 'frozen-source' / name
        copy.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, copy)
        assert sha(copy) == digest
    (out / 'start.json').write_text(json.dumps(dict(inputs=frozen), indent=2) + '\n')
    (out / 'driver.c').write_text(DRIVER)
    base = ['-q', '-bt=dos', '-0', '-ms', '-s', '-w4', '-we',
            '-i=' + str(ROOT / 'src/aspect'), '-i=' + str(ROOT / 'src/recording'),
            '-i=' + str(ROOT / 'src/capture'), '-i=' + str(ROOT)]
    sources = [out / 'driver.c', *[p for p in extra if p.suffix == '.c' and p.name != 'recording_file_dos_host.c']]
    if args.banked:
        # Reuse the production declared CRT services and exact bridge macros.
        names = ('memcpy', 'memset', 'memcmp', 'strchr', 'strcmp', 'strcpy', 'strlen')
        abi = (ROOT / 'src/terminal/config_abi.inc').read_text()
        declarations = []
        for name in names:
            line = f'CONFIG_REGISTER config_{name}_service_,{name}_'
            assert line in abi.splitlines()
            declarations.append(line)
        bridge = ('BITS 16\nCPU 8086\n%include "far_bridge.inc"\n'
                  'SEGMENT _TEXT public class=CODE use16\n'
                  '%define CONFIG_REGISTER NEAR_NAMED_SERVICE\n' + '\n'.join(declarations) + '\n'
                  'SEGMENT CONFIG_CODE public align=16 class=FARCODE use16\n'
                  'GROUP CONFIG_GROUP CONFIG_CODE\n'
                  '%undef CONFIG_REGISTER\n%macro CONFIG_REGISTER 2\n global %1\n'
                  ' %1:\n call far %1 %+ _resident\n ret\n%endmacro\n' + '\n'.join(declarations) + '\n')
        (out / 'bank.asm').write_text(bridge)
        subprocess.run(['nasm', '-fobj', '-I' + str(ROOT / 'src/terminal') + '/',
                        str(out / 'bank.asm'), '-o', str(out / 'bank.obj')], check=True)
        objects = [out / 'bank.obj']
        for source in sources:
            obj = out / (source.stem + '.o')
            flags = ['-ecc']
            if source in (ROOT / 'src/aspect/recorder.c', ROOT / 'src/recording/file.c'):
                flags = ['-nt=CONFIG_CODE', '-nc=FARCODE', *['-d' + n + '=config_' + n + '_service' for n in names]]
            if source == out / 'driver.c':
                flags += ['-dRECORDING_BANKED']
            subprocess.run(['wcc', *base, *flags, '-fo=' + str(obj), str(source)], cwd=out, check=True)
            objects.append(obj)
        subprocess.run(['wcl', *base, '-k8192', '-fm=RECORD.map', '-fe=RECORD.EXE', *map(str, objects)], cwd=out, check=True)
    else:
        subprocess.run(['wcl', *base, '-ecc', '-k8192', '-fm=RECORD.map', '-fe=RECORD.EXE', *map(str, sources)], cwd=out, check=True)
    (out / 'sampler.asm').write_text(SAMPLER)
    (out / 'setup.asm').write_text('BITS 16\nCPU 8086\nORG 100h\nmov dx,3fbh\nmov al,80h\nout dx,al\nmov dx,3f8h\nmov al,12\nout dx,al\ninc dx\nxor al,al\nout dx,al\nmov dx,3fbh\nmov al,3\nout dx,al\nmov dx,3fch\nmov al,1\nout dx,al\nmov ax,4c00h\nint 21h\n')
    for source, binary in [('sampler', 'SNAP'), ('setup', 'SETUP')]:
        subprocess.run(['nasm', '-fbin', str(out / (source + '.asm')), '-o', str(out / (binary + '.COM'))], check=True)
    cases = [
        ('ordinary', b'Name? ', bytes(range(256)), b'Name? ', 0),
        ('quoted-controls', b'\r\n"^>\x1e\x1f\xff', bytes(range(256)), b'\r\n"^>\x1e\x1f\xff', 0),
        ('long-control-prompt', bytes(range(1, 17)), bytes(range(256)) * 8, bytes(range(1, 17)), 0),
        ('timeout-no-payload', b'Name? ', b'MUST NOT SEND', b'Wrong! ', 0),
        ('writefail', b'', b'', b'', 8),
        ('cancel', b'', b'', b'', 14),
        ('replace', b'Name? ', bytes(range(256)), b'Name? ', 0),
        ('cwd-change', b'Name? ', bytes(range(256)), b'Name? ', 0),
        ('scratch-collision', b'Name? ', bytes(range(256)), b'Name? ', 0),
        ('existing-target', b'', b'', b'', 6),
        ('readonly-target', b'', b'', b'', 1),
        ('shared-target-owner', b'', b'', b'', 2),
        ('shared-other-owner', b'Name? ', bytes(range(256)), b'Name? ', 0),
        ('dual-record-owner', b'Name? ', bytes(range(256)), b'Name? ', 0),
        ('publish-race', b'', bytes(range(256)), b'', 10),
        ('restore-race', b'', bytes(range(256)), b'', 10),
    ]
    results = []
    for name, prompt, payload, reply, expected_status in cases:
        folder = out / name
        folder.mkdir()
        for binary in ('ASPECT.EXE', 'ASPCOMP.EXE', 'RECORD.EXE', 'SETUP.COM', 'SNAP.COM'):
            shutil.copy2(out / binary, folder / binary)
        (folder / 'PROMPT.BIN').write_bytes(prompt)
        (folder / 'PAYLOAD.BIN').write_bytes(payload)
        listener = socket.socket()
        listener.bind(('127.0.0.1', 0))
        listener.listen(1)
        listener.settimeout(15)
        wire = bytearray()
        errors = []
        sent = []
        port = listener.getsockname()[1]
        def peer():
            try:
                connection, _ = listener.accept()
                with connection:
                    connection.settimeout(15)
                    while True:
                        data = connection.recv(4096)
                        if not data:
                            break
                        wire.extend(data)
                        if reply and b'READY>' in wire and not sent:
                            connection.sendall(reply)
                            sent.append(reply.hex())
            except (OSError, TimeoutError) as exc:
                errors.append(repr(exc))
            finally:
                listener.close()
        thread = threading.Thread(target=peer, daemon=True)
        thread.start()
        config = f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
cycles=fixed 6000
[mixer]
nosound=true
[serial]
serial1=nullmodem server:127.0.0.1 port:{port} transparent:1 rxdelay:200 txdelay:1
serial2=disabled
serial3=disabled
serial4=disabled
[autoexec]
@echo off
mount c "{folder}"
mount d "{folder}"
d:
SETUP
SNAP B
RECORD {name} >RESULT.TXT
if errorlevel 1 goto failed
echo PASS>PASS.TXT
goto finish
:failed
echo FAIL>FAIL.TXT
:finish
SNAP A
exit
'''
        (folder / 'dosbox.conf').write_text(config)
        with (folder / 'dosbox.log').open('w') as log:
            process = subprocess.run(['dosbox-x', '-fastlaunch', '-nogui', '-conf', str(folder / 'dosbox.conf')],
                                     env=dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy'),
                                     stdout=log, stderr=log, timeout=45)
        thread.join(3)
        assert not thread.is_alive(), 'Owned peer did not exit'
        (folder / 'wire.bin').write_bytes(wire)
        (folder / 'peer-reply.bin').write_bytes(b''.join(bytes.fromhex(value) for value in sent))
        status = list(map(int, (folder / 'STATUS.TXT').read_text().split()))
        expected = b'' if expected_status else b'READY>' + (b'' if name == 'timeout-no-payload' else payload)
        checks = dict(DOS_normal_exit=process.returncode == 0 and (folder / 'PASS.TXT').exists() and not (folder / 'FAIL.TXT').exists(),
                      expected_status_and_one_close=status[:4] == [expected_status, 0 if name in ('existing-target', 'readonly-target', 'shared-target-owner') else 1, 1, 1],
                      exact_UART_bytes=bytes(wire) == expected, no_peer_errors=not errors,
                      expected_prompt_reply=sent == ([reply.hex()] if reply else []),
                      hardware_restored=(folder / 'BEFORE.BIN').read_bytes() == (folder / 'AFTER.BIN').read_bytes() and (folder / 'BEFORE.BIN').stat().st_size == 42,
                      no_script_runtime_errors=not (folder / 'ERROR.TXT').read_bytes())
        checks['publisher_ownership_resolved_or_recovery_retained'] = status[8:11] == ([1, 1, 1] if name == 'restore-race' else [0, 0, 0])
        checks['publisher_probe_and_reentry_guards'] = status[13] == 0
        checks['DOS_owner_size_and_closed_handle'] = status[18] == 326 and status[15] == 0
        if args.banked:
            segments = list(map(int, (folder / 'BANK.TXT').read_text().split()))
            checks['distinct_publisher_core_CS_and_resident_callbacks'] = (
                len(segments) == 4 and segments[0] == segments[3] and
                segments[1] == segments[2] and segments[0] != segments[1])
        temporary = {path.name for path in folder.glob('LPR*.TMP')}
        checks['only_owned_stage_removed_or_complete_recovery_retained'] = temporary == ({'LPR00001.TMP'} if name in ('scratch-collision', 'restore-race') else set())
        checks['no_unexpected_backup'] = len(list(folder.glob('LPR*.BAK'))) == (1 if name == 'restore-race' else 0)
        if not expected_status:
            checks['source_size_accounted'] = (folder / 'CASE.ASP').stat().st_size == status[6]
            checks['exact_recorded_input_counts'] = status[4:6] == [6 + len(payload), len(prompt)]
            checks['completed_source_published'] = status[7] == 1 and (folder / 'CASE.ASP').is_file() and (folder / 'CASE.ASX').is_file()
        else:
            checks['no_bytecode_or_new_recording_published'] = status[7] == 0 and not (folder / 'CASE.ASX').exists()
            if name in ('existing-target', 'readonly-target', 'shared-target-owner', 'publish-race', 'restore-race'):
                expected_target = b'OWNED!' if name == 'shared-target-owner' else b'RACED' if name in ('publish-race', 'restore-race') else b'ORIGINAL'
                checks['existing_or_raced_target_preserved'] = (folder / 'CASE.ASP').read_bytes() == expected_target
            else:
                checks['no_source_published'] = not (folder / 'CASE.ASP').exists()
        if name == 'writefail':
            checks['actual_readonly_handle_kernel_rejection'] = status[11] == 5
        if name == 'scratch-collision':
            checks['collided_file_preserved'] = (folder / 'LPR00001.TMP').read_bytes() == b'KEEP'
        if name == 'shared-other-owner':
            checks['independent_capture_keeps_writing'] = (folder / 'OTHER.LOG').read_bytes() == b'AB'
        if name == 'dual-record-owner':
            checks['second_publisher_created_no_target'] = not (folder / 'SECOND.ASP').exists()
        if name == 'shared-target-owner':
            checks['ownership_error_separate_from_DOS_error'] = status[11] == 0 and status[14] == 2
        if name == 'restore-race':
            checks['original_backup_and_complete_stage_retained'] = next(folder.glob('LPR*.BAK')).read_bytes() == b'ORIGINAL' and next(folder.glob('LPR*.TMP')).read_bytes().endswith(b'endproc\r\n')
            checks['actual_kernel_restore_refusal'] = status[11] != 0 and status[16] != 0 and status[7] == 0
        result = dict(passed=all(checks.values()), case=name, checks=checks, status=status,
                      actual_hex=bytes(wire).hex(), expected_hex=expected.hex(), peer_replies=sent, peer_errors=errors)
        (folder / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
        results.append(result)
        print(json.dumps(dict(case=name, passed=result['passed'], bytes=len(wire))), flush=True)
    for name, digest in frozen.items():
        assert sha(ROOT / name) == sha(out / 'frozen-source' / name) == digest, name
    result = dict(passed=all(case['passed'] for case in results), banked=args.banked, cases=results, inputs=frozen,
                  binary_sha256=sha(out / 'RECORD.EXE'), captures_sha256={str(path.relative_to(out)): sha(path) for path in out.rglob('*')
                                  if path.is_file() and not path.is_relative_to(out / 'frozen-source')}, scope=__doc__)
    with (out / 'result.json').open('x') as stream:
        stream.write(json.dumps(result, indent=2) + '\n')
    assert result['passed'], [(case['case'], case['checks']) for case in results if not case['passed']]


if __name__ == '__main__':
    main()
