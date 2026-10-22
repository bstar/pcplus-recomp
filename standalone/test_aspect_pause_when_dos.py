#!/usr/bin/env python3
"""Actual DOS WHEN transmit/deferred CALL ordering during live terminal PAUSE."""
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
BASE = ROOT / 'build/aspect-pause-when-dos'
ESC = b'\x1b'
QUERY = ESC + b'[6n'


def definitions():
    result = []
    for name, register, helper, marker, before, after in [
        ('transmit', 'when 0 "WAKE" transmit "EVENT"', '', b'WAKE', b'EVENT', b''),
        ('call', 'when 0 "WAKE" call worker',
         'proc worker\ntransmit "EVENT"\nendproc\n', b'WAKE', b'', b'EVENT'),
        ('framed-call', 'when 0 "WAKE" call worker',
         'proc worker\ninteger local_value\nlocal_value = 37\nif local_value == 37\ntransmit "FRAME"\nelse\ntransmit "BADFRAME"\nendif\nendproc\n', b'WAKE', b'', b'FRAME'),
        ('plain-terminal', '', '', b'LIVE', b'', b''),
        ('future-wait', '', '', b'STALE', b'', b''),
        ('two-calls', 'when 0 "WAKE" call first\nwhen 1 "BELL" call second',
         'proc first\ntransmit "FIRST"\nendproc\nproc second\ntransmit "SECOND"\nendproc\n',
         b'WAKEBELL', b'', b'SECONDFIRST'),
    ]:
        column = 26 + len(marker)
        reply = ESC + ('[1;%dR' % column).encode()
        source = ('proc main\nwaitfor "LOGIN:" 5\nset duplex full\ntransmit "KEYREADY"\n'
                  'waitfor "HOLD" 10\n' + register + '\npause 4\ntransmit "PAUSEDONE"\n'
                  'waitfor "END" 30\nif waitfor\ntransmit $D_PWORD\ntransmit "^M"\n'
                  'pause 1\nendif\nendproc\n' + helper)
        result.append(dict(name='pause-when-' + name, source=source, profile=4,
                           bios_policy='STANDARD', custom=False, success=True,
                           banner=ESC + b'[2J' + ESC + b'[HFIRST BYTE SAFE' + QUERY + ESC + b'[0cLOGIN:',
                           keys='p1800 k e y s p200 a-z p5500 escape p300 d o n e p2500 space p700 r e a d y p700 a-x',
                           key_wire=b'keys' + before + reply + after + b'PAUSEDONEdone',
                           post=QUERY, post_reply=ESC + ('[1;%dR' % (column + 3)).encode(),
                           screen=[(0, 0, 'FIRST BYTE SAFE'), (0, 21, 'HOLD' + marker.decode() + 'END')],
                           marker=marker, reply=reply))
        if name == 'plain-terminal':
            result[-1]['keys'] = 'p1800 k e y s p6100 d o n e p2500 space p700 r e a d y p700 a-x'
            result[-1]['no_window'] = True
        if name == 'future-wait':
            result[-1]['source'] = source.replace('transmit "PAUSEDONE"\n',
                'transmit "PAUSEDONE"\nwaitfor "STALE" 1\nif waitfor\ntransmit "BADSTALE"\nelse\ntransmit "FRESHONLY"\nendif\n')
            result[-1]['keys'] = result[-1]['keys'].replace('p300 d o n e', 'p2600 d o n e')
            result[-1]['key_wire'] = b'keys' + reply + b'PAUSEDONEFRESHONLYdone'
    return result


def main():
    original = keys.adapter
    renderer = keys.renderer
    specs = {spec['name']: spec for spec in definitions()}
    streams = {}

    def adapter():
        module = original()
        run = module.run

        def staged(*args, **kwargs):
            events = streams.setdefault(args[0], [])
            module.socket = types.SimpleNamespace(
                socket=lambda: TracedSocket(socket.socket(), events), timeout=socket.timeout)
            kwargs['online_updates'] = [(2.0, b'HOLD'), (3.0, specs[args[0]]['marker'] + QUERY)]
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
    report = json.loads((folder / 'checks.json').read_text())
    results = []
    for case in report['cases']:
        name = case['case']
        spec, events = specs[name], streams[name]
        target = folder / name
        (target / 'peer-events.json').write_text(json.dumps(events, indent=2) + '\n')
        hold = next(event for event in events if event['kind'] == 'send' and event['hex'] == b'HOLD'.hex())
        query = next(event for event in events if event['kind'] == 'send' and
                     event['hex'] == (spec['marker'] + QUERY).hex())
        received, pause_end, response = b'', None, None
        for event in events:
            if event['kind'] != 'receive' or event['time'] < hold['time']:
                continue
            received += bytes.fromhex(event['hex'])
            if response is None and spec['reply'] in received:
                response = event['time']
            if pause_end is None and b'PAUSEDONE' in received:
                pause_end = event['time']
        delay = None if response is None else response - query['time']
        elapsed = None if pause_end is None else pause_end - hold['time']
        observation = struct.unpack('<7H', (target / 'RENDER.BIN').read_bytes()[-14:])
        checks = dict(functional_native_WHEN_wire_and_screen=case['passed'],
                      native_pause_duration_retained=elapsed is not None and 4 <= elapsed <= 5,
                      query_reply_before_pause_end=response is not None and pause_end is not None and response < pause_end,
                      query_reply_within_one_second=delay is not None and 0 <= delay <= 1,
                      expected_window_observation=observation == (0,0,0,0,0,0,0) if spec.get('no_window') else observation[1:3] == (1, 1))
        results.append(dict(case=name, passed=all(checks.values()), checks=checks,
                            query_reply_delay_seconds=delay, pause_complete_after_hold_seconds=elapsed,
                            observation=observation, raw_wire_sha256=renderer.sha(target / 'serial.bin')))
    result = dict(passed=all(case['passed'] for case in results), cases=results,
                  parent_sha256=report['terminal_sha256'], runner_sha256=report['runner_sha256'],
                  checker_sha256=renderer.sha(Path(__file__)),
                  captures_sha256={str(p.relative_to(folder)): renderer.sha(p)
                                  for p in folder.rglob('*') if p.is_file()}, scope=__doc__)
    (folder / 'pause-checks.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result['cases']))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
