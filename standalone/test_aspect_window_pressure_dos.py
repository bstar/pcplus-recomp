#!/usr/bin/env python3
"""Paced ANSI traffic exceeding the RX ring during actual DOS script help.

Every packet paints a separate 32-cell tile with alternating foreground colors
and requests CPR at its end. All tiles remain in the final screen, so receiving
only a final marker cannot satisfy this test. This is an emulated UART load
test, not a physical flow-control or sustained file-transfer claim.
"""
import json
import socket
import struct
import sys
import types
from pathlib import Path
import test_aspect_keys_dos as keys
import test_aspect_script_window_dos as window
from test_aspect_window_query_dos import TracedSocket

ROOT = keys.ROOT
BASE = ROOT / 'build/aspect-window-pressure-dos'
ESC = b'\x1b'
QUERY = ESC + b'[6n'
PAUSE = False


def packets():
    result = []
    for index in range(44):
        row, column = index // 2 + 2, 1 if index % 2 == 0 else 41
        text = ('PKT%02d:' % index + ''.join(chr(65 + (index * 7 + i * 11) % 26)
                                            for i in range(26))).encode('ascii')
        assert len(text) == 32
        payload = ESC + ('[%d;%dH' % (row, column)).encode()
        for cell, byte in enumerate(text):
            payload += ESC + (b'[31m' if cell % 2 == 0 else b'[32m') + bytes([byte])
        payload += ESC + b'[0m' + QUERY
        reply = ESC + ('[%d;%dR' % (row, column + len(text))).encode()
        result.append(dict(row=row, column=column, text=text, payload=payload,
                           reply=reply, scheduled=2.0 + index * .1))
    return result


def definitions():
    source = ('proc main\nwaitfor "LOGIN:" 5\nset duplex full\n'
              'transmit "KEYREADY"\nwaitfor "END" 30\nif waitfor\n'
              'transmit $D_PWORD\ntransmit "^M"\npause 1\nendif\nendproc\n')
    if PAUSE:
        source = source.replace('waitfor "END" 30', 'waitfor "HOLD" 10\npause 6\ntransmit "PAUSEDONE"\nwaitfor "END" 30')
    return [dict(name='window-pressure-4' , source=source, profile=4,
                 bios_policy='STANDARD', custom=False, success=True,
                 banner=ESC + b'[2J' + ESC + b'[HFIRST BYTE SAFE' + QUERY + ESC + b'[0cLOGIN:',
                 keys='p1800 k e y s p200 a-z p7500 escape p300 d o n e p2500 space p700 r e a d y p700 a-x',
                 key_wire=b'keys' + b''.join(packet['reply'] for packet in packets()) + (b'PAUSEDONE' if PAUSE else b'') + b'done',
                 post=QUERY, post_reply=ESC + b'[23;76R', screen=[(0, 0, 'FIRST BYTE SAFE')])]


def main():
    global PAUSE
    if '--during-pause' in sys.argv:
        PAUSE = True
        sys.argv.remove('--during-pause')
    original = keys.adapter
    renderer = keys.renderer
    events = []
    workload = packets()

    def adapter():
        module = original()
        run = module.run
        module.socket = types.SimpleNamespace(
            socket=lambda: TracedSocket(socket.socket(), events), timeout=socket.timeout)

        def staged(*args, **kwargs):
            kwargs['online_updates'] = ([(1.8,b'HOLD')] if PAUSE else []) + [(p['scheduled'], p['payload']) for p in workload]
            return run(*args, **kwargs)

        module.run = staged
        return module

    keys.OUT = BASE
    keys.definitions = definitions
    keys.adapter = adapter
    renderer.observer = window.make_observer(
        renderer.observer, window.symbols(ROOT / 'build/terminal/terminal.map'),
        window.symbols(ROOT / 'build/aspect-runner/ASPECT.map'), render_progress=True)
    keys.main()
    folder = BASE / sys.argv[sys.argv.index('--label') + 1]
    (folder / 'peer-events.json').write_text(json.dumps(events, indent=2) + '\n')
    report = json.loads((folder / 'checks.json').read_text())
    case = report['cases'][0]
    screen = (folder / case['case'] / 'SCREEN.BIN').read_bytes()
    raw = (folder / case['case'] / 'RENDER.BIN').read_bytes()
    first_tick, advanced, seen, help_seen, ticks, peak, menu = struct.unpack('<7H', raw[-14:])
    cells, colors, delays = [], [], []
    sends = [event for event in events if event['kind'] == 'send']
    for packet in workload:
        at = 2 * ((packet['row'] - 1) * 80 + packet['column'] - 1)
        cells.append(screen[at:at + 64:2] == packet['text'])
        colors.append(screen[at + 1:at + 64:2] == bytes([4, 2] * 16))
        sent = [event for event in sends if bytes.fromhex(event['hex']) == packet['payload']]
        assert len(sent) == 1
        received = b''
        completion = None
        for event in events:
            if event['kind'] == 'receive' and event['time'] >= sent[0]['time']:
                received += bytes.fromhex(event['hex'])
                if packet['reply'] in received:
                    completion = event['time']
                    break
        delays.append(None if completion is None else completion - sent[0]['time'])
    checks = dict(DOS_functional_checks=report['passed'] and case['passed'],
                  actual_help_window_observed=seen == 1 and ticks > 30,
                  actual_render_advances_under_window=advanced == 1,
                  offered_bytes_exceed_4096_ring=sum(len(p['payload']) for p in workload) > 4096,
                  all_1408_tile_characters_match=all(cells),
                  all_1408_tile_attributes_match=all(colors),
                  all_44_CPR_replies_within_one_second=all(d is not None and 0 <= d <= 1 for d in delays))
    pause_elapsed = None
    if PAUSE:
        hold = next(event for event in events if event['kind'] == 'send' and event['hex'] == b'HOLD'.hex())
        received = b''
        for event in events:
            if event['kind'] == 'receive' and event['time'] >= hold['time']:
                received += bytes.fromhex(event['hex'])
                if b'PAUSEDONE' in received:
                    pause_elapsed = event['time'] - hold['time']
                    break
        checks['six_second_pause_duration_retained'] = pause_elapsed is not None and 6 <= pause_elapsed <= 7
    result = dict(passed=all(checks.values()), checks=checks, during_pause=PAUSE, pause_elapsed_seconds=pause_elapsed,
                  payload_bytes=sum(len(p['payload']) for p in workload), packet_count=len(workload),
                  packet_reply_delay_seconds=delays, window_ticks=ticks, child_ring_peak=peak,
                  first_render_tick=first_tick, tile_cells_match=cells, tile_colors_match=colors,
                  parent_sha256=report['terminal_sha256'], runner_sha256=report['runner_sha256'],
                  checker_sha256=renderer.sha(Path(__file__)),
                  captures_sha256={str(p.relative_to(folder)): renderer.sha(p)
                                  for p in folder.rglob('*') if p.is_file()},
                  scope=__doc__)
    (folder / 'pressure-checks.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(passed=result['passed'], checks=checks, payload_bytes=result['payload_bytes'],
                         max_reply_delay=max((d for d in delays if d is not None), default=None),
                         window_ticks=ticks, child_ring_peak=peak)))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
