#!/usr/bin/env python3
"""Drop real emulated DCD during partial CSI, then redial in the same DOS process."""
import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import time

from product_inputs import ROOT, select_product
from enigma_peer_width_aspect_dos import observer
sys.path.insert(0, str(ROOT / 'standalone'))
from directory_fixtures import prm
from test_directory_key_bindings_dos import actions
from test_terminal import SAMPLER
sys.path.insert(0, str(ROOT / 'src/aspect'))
from compiler import compile_source


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def carrier_observer(binary, runner, out):
    observer(binary, out)
    listing = (binary.parent / 'terminal.map').read_text()
    symbols = {n: (int(s, 16), int(o, 16)) for s, o, n in re.findall(
        r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$', listing, re.M | re.I)}
    dg = int(re.search(r'^DGROUP\s+([0-9a-f]+):', listing, re.M | re.I)[1], 16)
    with (out / 'bbs_width_offsets.inc').open('a') as stream:
        for name in ['connection_state', 'connection_status', 'connection_carrier_seen', 'connection_enabled', 'csi_unimplemented_service',
                     '_recording_terminal_cookie', '_recording_terminal_owner', 'terminal_controller_active', '_redisplay_active', '_command_menu_active',
                     'terminal_program_kind', 'terminal_aspect_adopt', 'terminal_program_status']:
            segment, offset = symbols[name]
            stream.write(f'%define {name.upper().lstrip("_")} {segment * 16 + offset - dg * 16}\n')
        stream.write(f'%define RENDER_CHILD_DS {symbols["render_child_ds"][1]}\n')
        child_listing = (runner.parent / 'ASPECT.map').read_text()
        child_symbols = {n: (int(s, 16), int(o, 16)) for s, o, n in re.findall(
            r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$', child_listing, re.M | re.I)}
        child_dg = int(re.search(r'^DGROUP\s+([0-9a-f]+):', child_listing, re.M | re.I)[1], 16)
        for label, name in [('CHILD_ERROR', '_runtime_error'), ('CHILD_OPCODE', '_runtime_last_opcode'),
                            ('CHILD_DEFERRED', '_runtime_when_deferred'), ('CHILD_ARMED', '_runtime_when_disconnect_armed'),
                            ('CHILD_WAIT', '_runtime_wait_gate'), ('CHILD_MSR_PORT', 'uart_port_msr'),
                            ('CHILD_PENDING', '_runtime_when_pending_service'), ('CHILD_SERIAL_STATUS', '_aspect_serial_status')]:
            segment, offset = child_symbols[name]
            assert segment == child_dg, name
            stream.write(f'%define {label} {offset}\n')
    source = (ROOT / 'lab/bbs/peer_width_aspect_watch.asm').read_text()
    extra = ['pending_ticks', 'high_ticks', 'loss_ticks', 'loss_idle_ticks', 'loss_width',
             'loss_parser', 'loss_scope', 'loss_program', 'loss_live', 'loss_bank',
             'loss_service', 'loss_state', 'loss_status', 'final_connection', 'final_status',
             'loss_enabled', 'final_enabled', 'first_enabled', 'dial_key_reads', 'dial_key_state',
             'dial_key_enabled', 'dial_key_parser', 'dial_key_scope', 'dial_key_program',
             'dial_key_record_cookie', 'dial_key_record_owner', 'dial_key_controller',
             'dial_key_redisplay', 'dial_key_menu', 'redial_init_ticks', 'dial_key_child_count',
             'dial_key_kind', 'dial_key_adopt', 'dial_key_program_status', 'dial_child_ds',
             'dial_child_error', 'dial_child_opcode', 'dial_child_deferred', 'dial_child_armed',
             'dial_child_wait', 'dial_child_msr_port', 'dial_child_pending', 'dial_child_serial_status']
    source = source.replace('dw 0x4257,1', 'dw 0x4357,1', 1)
    source = source.replace('sample_end:', ''.join(n + ': dw ' + ('0' if i < 4 or n in ('dial_key_reads', 'redial_init_ticks') else '0xffff') + '\n'
                            for i, n in enumerate(extra)) + 'sample_end:', 1)
    needle = ' mov ax,[cs:root_ds]\n sub ax,DGROUP_REL\n add ax,ASPECT_CODE_REL\n'
    assert source.count(needle) >= 1
    trace = ''' mov ax,[cs:root_ds]
 mov es,ax
 cmp word [cs:first_enabled],0xffff
 jne .high
 xor ax,ax
 mov al,[es:CONNECTION_ENABLED]
 mov [cs:first_enabled],ax
.high:
 cmp word [cs:loss_idle_ticks],0
 je .online
 cmp word [es:CONNECTION_STATE],1
 je .redial_init
 cmp word [es:CONNECTION_STATE],2
 jne .online
.redial_init:
 inc word [cs:redial_init_ticks]
.online:
 cmp word [es:CONNECTION_STATE],6
 jne .loss
 cmp byte [es:CONNECTION_CARRIER_SEEN],0
 je .loss
 inc word [cs:high_ticks]
 cmp word [es:TERMINAL_PARSER_ACTIVE],0
 je .loss
 inc word [cs:pending_ticks]
.loss:
 cmp word [es:CONNECTION_STATUS],6
 jne .carrier_done
 inc word [cs:loss_ticks]
 cmp word [es:CONNECTION_STATE],0
 jne .carrier_done
 cmp word [es:TERMINAL_PARSER_ACTIVE],0
 jne .carrier_done
 cmp word [es:TERMINAL_ASPECT_ACTIVE],0
 jne .carrier_done
 cmp word [es:PROGRAM_ACTIVE],0
 jne .carrier_done
 mov ax,[cs:root_ds]
 sub ax,DGROUP_REL
 add ax,LIVE_CODE_REL
 mov es,ax
 cmp word [es:RESET_LIVE_ACTIVE],0
 jne .carrier_done
 cmp word [es:RESET_BANK_BUSY],0
 jne .carrier_done
 inc word [cs:loss_idle_ticks]
 mov ax,[cs:root_ds]
 mov es,ax
 mov ax,[es:SCREEN_ATTRIBUTE_ROW_BYTES]
 mov [cs:loss_width],ax
 mov ax,[es:TERMINAL_PARSER_ACTIVE]
 mov [cs:loss_parser],ax
 mov ax,[es:TERMINAL_ASPECT_ACTIVE]
 mov [cs:loss_scope],ax
 mov ax,[es:PROGRAM_ACTIVE]
 mov [cs:loss_program],ax
 mov word [cs:loss_live],0
 mov word [cs:loss_bank],0
 mov ax,[es:CSI_UNIMPLEMENTED_SERVICE]
 mov [cs:loss_service],ax
 mov ax,[es:CONNECTION_STATE]
 mov [cs:loss_state],ax
 mov ax,[es:CONNECTION_STATUS]
 mov [cs:loss_status],ax
 xor ax,ax
 mov al,[es:CONNECTION_ENABLED]
 mov [cs:loss_enabled],ax
.carrier_done:
'''
    source = source.replace(needle, trace + needle, 1)
    source = source.replace('old21: dw 0,0', 'old21: dw 0,0\nold16: dw 0,0', 1)
    keyboard = '''handler16:
 cmp ah,0
 je .read
 cmp ah,0x10
 jne .chain
.read:
 pushf
 call far [cs:old16]
 save
 cmp ax,0x2000
 jne .done
 cmp word [cs:staged],1
 jne .done
 inc word [cs:dial_key_reads]
 mov ax,[cs:root_ds]
 mov es,ax
 mov ax,[es:CONNECTION_STATE]
 mov [cs:dial_key_state],ax
 xor ax,ax
 mov al,[es:CONNECTION_ENABLED]
 mov [cs:dial_key_enabled],ax
 mov ax,[es:TERMINAL_PARSER_ACTIVE]
 mov [cs:dial_key_parser],ax
 mov ax,[es:TERMINAL_ASPECT_ACTIVE]
 mov [cs:dial_key_scope],ax
 mov ax,[es:PROGRAM_ACTIVE]
 mov [cs:dial_key_program],ax
 mov ax,[es:RECORDING_TERMINAL_COOKIE]
 mov [cs:dial_key_record_cookie],ax
 mov ax,[es:RECORDING_TERMINAL_OWNER+156]
 mov [cs:dial_key_record_owner],ax
 mov ax,[es:TERMINAL_CONTROLLER_ACTIVE]
 mov [cs:dial_key_controller],ax
 mov ax,[es:REDISPLAY_ACTIVE]
 mov [cs:dial_key_redisplay],ax
 mov ax,[es:COMMAND_MENU_ACTIVE]
 mov [cs:dial_key_menu],ax
 mov ax,[cs:child_count]
 mov [cs:dial_key_child_count],ax
 mov ax,[es:TERMINAL_PROGRAM_KIND]
 mov [cs:dial_key_kind],ax
 mov ax,[es:TERMINAL_ASPECT_ADOPT]
 mov [cs:dial_key_adopt],ax
 mov ax,[es:TERMINAL_PROGRAM_STATUS]
 mov [cs:dial_key_program_status],ax
 cmp word [cs:child_count],0
 jne .done
 mov ax,[cs:root_ds]
 sub ax,DGROUP_REL
 add ax,ASPECT_CODE_REL
 mov es,ax
 mov ax,[es:RENDER_CHILD_DS]
 mov [cs:dial_child_ds],ax
 or ax,ax
 jz .done
 mov es,ax
 mov ax,[es:CHILD_ERROR]
 mov [cs:dial_child_error],ax
 mov ax,[es:CHILD_OPCODE]
 mov [cs:dial_child_opcode],ax
 mov ax,[es:CHILD_DEFERRED]
 mov [cs:dial_child_deferred],ax
 mov ax,[es:CHILD_ARMED]
 mov [cs:dial_child_armed],ax
 mov ax,[es:CHILD_WAIT]
 mov [cs:dial_child_wait],ax
 mov ax,[es:CHILD_MSR_PORT]
 mov [cs:dial_child_msr_port],ax
 mov ax,[es:CHILD_PENDING]
 mov [cs:dial_child_pending],ax
 mov ax,[es:CHILD_SERIAL_STATUS]
 mov [cs:dial_child_serial_status],ax
.done:
 restore
 iret
.chain:
 jmp far [cs:old16]
'''
    source = source.replace('handler21:\n', keyboard + 'handler21:\n', 1)
    source = source.replace(' mov dx,[cs:old21]\n', ' mov dx,[cs:old16]\n mov ds,[cs:old16+2]\n mov ax,0x2516\n int 0x21\n mov dx,[cs:old21]\n', 1)
    source = source.replace('start:\n', 'start:\n mov ax,0x3516\n int 0x21\n mov [old16],bx\n mov [old16+2],es\n mov dx,handler16\n mov ax,0x2516\n int 0x21\n', 1)
    needle = ' mov [cs:final_aspect],ax\n push cs\n'
    assert source.count(needle) == 1
    source = source.replace(needle, ''' mov [cs:final_aspect],ax
 mov ax,[CONNECTION_STATE]
 mov [cs:final_connection],ax
 mov ax,[CONNECTION_STATUS]
 mov [cs:final_status],ax
 xor ax,ax
 mov al,[CONNECTION_ENABLED]
 mov [cs:final_enabled],ax
 push cs
''')
    (out / 'carrier-watch.asm').write_text(source)
    subprocess.run(['nasm', '-fbin', '-I' + str(out) + '/', str(out / 'carrier-watch.asm'),
                    '-o', str(out / 'BWATCH.COM')], check=True)


async def run(a):
    out = a.output.resolve()
    assert out.is_relative_to(ROOT / 'build') and not out.exists()
    out.mkdir(parents=True)
    parent = out / 'parent'
    parent.mkdir()
    binary, inputs = select_product(a.terminal, 'TERMINAL.EXE')
    runner, child_inputs = select_product(a.runner, 'ASPECT.EXE')
    inputs += child_inputs + [binary, runner, binary.parent / 'terminal.map', runner.parent / 'ASPECT.map']
    for path in (binary, runner):
        shutil.copyfile(path, parent / path.name)
    script = ('proc main\nfopen 4 "D:\\WIDE.LOG" "wb"\nfputs 4 "START|"\npause 2\n'
              'transmit "SCRIPTREADY^M"\nwaitfor "WIDTHREADY" 10\nif waitfor\n'
              'fputs 4 "WIDE|"\ntransmit "WIDEACK^M"\nwaitfor "END" ' + str(a.wait_seconds) + '\n'
              'if waitfor\nfputs 4 "BADEND|"\nelse\nfputs 4 "RETURN|"\nendif\n'
              'else\nfputs 4 "FAILWIDE|"\nendif\nfclose 4\nendproc\n')
    if a.disconnect_handler:
        script = script.replace('pause 2\n', 'when disconnect call lost\npause 2\n', 1)
        script += 'proc lost\nfputs 4 "LOST|"\nfclose 4\nexit\nendproc\n'
    if a.compiler:
        compiler, compiler_inputs = select_product(a.compiler, 'ASPCOMP.EXE')
        inputs += compiler_inputs + [compiler]
        shutil.copyfile(compiler, parent / compiler.name)
        (out / 'WIDE.ASP').write_text(script, encoding='ascii')
    else:
        (out / 'WIDE.ASX').write_bytes(compile_source(script))
    (out / 'ACTIONS.KEY').write_bytes(actions(b'D:\\WIDE.ASP' if a.compiler else b'D:\\WIDE.ASX', 0))
    carrier_observer(binary, runner, out)
    sampler = SAMPLER
    for offset in (0, 1, 3, 4):
        sampler = sampler.replace(hex(0x3f8 + offset), hex(0x2f8 + offset))
    needle = ' mov dx,0x70\n mov cx,4\n mov ah,0x40\n int 0x21\n'
    assert sampler.count(needle) == 1
    sampler = sampler.replace(needle, needle + ' mov dx,0x58\n mov cx,4\n mov ah,0x40\n int 0x21\n')
    (out / 'sampler.asm').write_text(sampler)
    subprocess.run(['nasm', '-fbin', str(out / 'sampler.asm'), '-o', str(out / 'SNAP.COM')], check=True)
    config = bytearray(prm(port=2, baud=5, soft=0, hard=1))
    struct.pack_into('<H', config, 0x186, 5)
    struct.pack_into('<HH', config, 0x4e4, 8, 4)
    config[0x18:0x47] = b'AT&K3^M'.ljust(47, b'\0')
    (out / 'TEST.PRM').write_bytes(config)
    sessions = []
    owners = set()
    started = time.monotonic()

    async def peer(reader, writer):
        owner = asyncio.current_task()
        owners.add(owner)
        item = dict(index=len(sessions) + 1, received=bytearray(), sent=bytearray(), events=[], errors=[])
        sessions.append(item)

        def event(kind):
            item['events'].append(dict(kind=kind, seconds=round(time.monotonic() - started, 4)))

        async def send(data):
            item['sent'].extend(data)
            writer.write(data)
            await writer.drain()

        try:
            event('connected')
            if item['index'] == 2:
                await send(b'\x1b[?3l\x1b[2;73HNARROW!\x1b[6n\x1b[?3h\x1b[2;121HRECOVER\x1b[6n')
            while data := await reader.read(4096):
                item['received'].extend(data)
                if item['index'] == 1 and b'SCRIPTREADY\r' in item['received'] and not item.get('wide'):
                    item['wide'] = True
                    event('wide-request')
                    await send(b'\x1b[?3h\x1b[2;121HINITIAL\x1b[6nWIDTHREADY')
                if item['index'] == 1 and b'WIDEACK\r' in item['received']:
                    await send(b'\x1b[?3')
                    event('partial-command')
                    await asyncio.sleep(1)
                    event('carrier-drop')
                    writer.transport.abort()
                    break
                if item['index'] == 2 and b'ready' in item['received'] and not item.get('keyboard'):
                    item['keyboard'] = True
                    event('keyboard-after-redial')
                    await send(b'\x1b[3;1HKEYOK\x1b[6n')
        except (OSError, ConnectionError) as error:
            item['errors'].append(type(error).__name__)
        finally:
            writer.close()
            event('closed')
            owners.discard(owner)

    server = await asyncio.start_server(peer, '127.0.0.1', 0)
    port = server.sockets[0].getsockname()[1]
    keys = 'p900 enter p2500 a-1 ' + ('p600 a-z ' if a.window else '')
    redial_delay = max(11000, (a.wait_seconds + 7) * 1000)
    keys += f'p{redial_delay} a-d p5000 r e a d y p2000 a-x'
    text = f'''[sdl]
output=surface
[dosbox]
memsize=8
[cpu]
core=normal
cputype=8086
cycles=fixed 6000
[mixer]
nosound=true
[serial]
serial1=disabled
serial2=modem irq:5 listenport:0
serial3=disabled
serial4=disabled
[autoexec]
@echo off
mount c "{parent}"
mount d "{out}"
c:
D:\\SNAP B
D:\\BWATCH
ADDKEY {keys}
TERMINAL @D:\\TEST.PRM /D:127.0.0.1:{port} /T:D:\\ACTIONS.KEY
if errorlevel 1 goto failed
echo PASS>D:\\PASS.TXT
goto capture
:failed
echo FAIL>D:\\FAIL.TXT
:capture
D:\\SNAP S
D:\\SNAP A
exit
'''
    (out / 'dosbox.conf').write_text(text)
    inputs += [Path(__file__), ROOT / 'lab/bbs/enigma_peer_width_aspect_dos.py',
               ROOT / 'lab/bbs/peer_width_aspect_watch.asm', ROOT / 'lab/bbs/product_inputs.py',
               ROOT / 'standalone/test_terminal.py', ROOT / 'standalone/directory_fixtures.py',
               ROOT / 'standalone/modem_fixtures.py', ROOT / 'standalone/terminal_config_fixtures.py',
               ROOT / 'standalone/test_directory_key_bindings_dos.py', ROOT / 'src/aspect/compiler.py']
    inputs += list(parent.iterdir()) + [out / n for n in ['ACTIONS.KEY', 'BWATCH.COM', 'SNAP.COM',
               'carrier-watch.asm', 'sampler.asm', 'bbs_width_offsets.inc', 'dosbox.conf', 'TEST.PRM',
               'WIDE.ASP' if a.compiler else 'WIDE.ASX']]
    before = {str(p.relative_to(ROOT)): sha(p) for p in inputs}
    try:
        with (out / 'dosbox.log').open('w') as log:
            process = await asyncio.create_subprocess_exec('dosbox-x', '-fastlaunch', '-nogui', '-conf',
                      str(out / 'dosbox.conf'), cwd=out, stdout=log, stderr=log,
                      env=dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy'))
            try:
                code = await asyncio.wait_for(process.wait(), 75)
            except asyncio.TimeoutError:
                process.terminate()
                try:
                    await asyncio.wait_for(process.wait(), 5)
                except asyncio.TimeoutError:
                    process.kill()
                    await process.wait()
                code = -1
    finally:
        server.close()
        if hasattr(server, 'close_clients'):
            server.close_clients()
        for task in list(owners):
            task.cancel()
        await asyncio.gather(*list(owners), return_exceptions=True)
        await asyncio.wait_for(server.wait_closed(), 3)
    for item in sessions:
        folder = out / f"connection-{item['index']}"
        folder.mkdir()
        (folder / 'received.bin').write_bytes(item.pop('received'))
        (folder / 'sent.bin').write_bytes(item.pop('sent'))
    raw = (out / 'BBSOBS.BIN').read_bytes() if (out / 'BBSOBS.BIN').exists() else b''
    state = struct.unpack('<64H', raw) if len(raw) == 128 else ()
    marker = (out / 'WIDE.LOG').read_bytes() if (out / 'WIDE.LOG').exists() else b''
    first = (out / 'connection-1/received.bin').read_bytes() if sessions else b''
    second = (out / 'connection-2/received.bin').read_bytes() if len(sessions) >= 2 else b''
    baseline = (out / 'BEFORE.BIN').read_bytes() if (out / 'BEFORE.BIN').exists() else b''
    final = (out / 'AFTER.BIN').read_bytes() if (out / 'AFTER.BIN').exists() else b''
    checks = dict(DOS_exit=code == 0 and (out / 'PASS.TXT').exists(),
                  hardware_restored=len(baseline) == 46 and baseline == final,
                  two_connections=len(sessions) == 2,
                  committed_wide=b'\x1b[2;128R' in first and b'WIDEACK\r' in first,
                  child_progress=marker == (b'START|WIDE|LOST|' if a.disconnect_handler else b'START|WIDE|RETURN|'),
                  real_ASPECT=bool(state) and state[2] == state[3] != 0 and state[9] > 0 and state[10] > 0,
                  window=bool(state) and (state[11] > 0) == a.window,
                  child_exit=bool(state) and state[4:6] == (1, 0) and state[6] == state[7] != 0,
                  pending_parser=bool(state) and state[21] >= 12 and state[22] > 0,
                  retired_loss=bool(state) and state[23] > 0 and state[24] > 0 and state[25:34] == (132, 0, 0, 0, 0, 0, 0, 0, 6),
                  modem_still_enabled=bool(state) and state[36:39] == (1, 1, 1),
                  redial_key_after_notice=bool(state) and state[39:45] == (1, 0, 1, 0, 0, 0) and state[50] > 0,
                  redial_widths=b'\x1b[2;80R' in second and b'\x1b[2;128R' in second,
                  keyboard_after_redial=b'ready' in second and b'\x1b[3;6R' in second,
                  root_idle=bool(state) and state[8] == 0 and state[12:21] == (132, 0, 0, 0, 0, 0, 0, 0, 1),
                  exact_ASX=(out / 'WIDE.ASX').exists() and (out / 'WIDE.ASX').read_bytes() == compile_source(script),
                  actual_modem_commands=(out / 'dosbox.log').read_text().count('Command sent to modem: ->AT&K3<-') == 2,
                  actual_modem_carrier_drop='Modem response: NO CARRIER' in (out / 'dosbox.log').read_text(),
                  peer_errors_absent=all(not s['errors'] for s in sessions),
                  inputs_unchanged=before == {str(p.relative_to(ROOT)): sha(p) for p in inputs})
    report = dict(passed=all(checks.values()), checks=checks, state=state, marker=marker.decode('ascii', errors='replace'),
                  sessions=sessions, inputs=before, binary_sha256=sha(binary), runner_sha256=sha(runner),
                  window=a.window, source_compilation=bool(a.compiler), disconnect_handler=a.disconnect_handler, wait_seconds=a.wait_seconds, script=script,
                  artifacts={str(p.relative_to(ROOT)): sha(p) for p in out.rglob('*') if p.is_file()},
                  scope='DOSBox-X built-in Hayes modem owns carrier/DCD and Hayes responses. Raw loopback peer closes after partial CSI; same DOS parent redials and handles widths/keyboard. Passive observer; no physical modem or full application claim.')
    (out / 'checks.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ['passed', 'checks', 'state', 'marker', 'sessions']}, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--terminal', type=Path, required=True)
    p.add_argument('--runner', type=Path, required=True)
    p.add_argument('--compiler', type=Path)
    p.add_argument('--window', action='store_true')
    p.add_argument('--disconnect-handler', action='store_true')
    p.add_argument('--wait-seconds', type=int, choices=range(3, 31), default=3)
    p.add_argument('--output', type=Path, required=True)
    raise SystemExit(asyncio.run(run(p.parse_args())))
