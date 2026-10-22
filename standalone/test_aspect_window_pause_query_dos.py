#!/usr/bin/env python3
"""Check CPR service during an ASPECT PAUSE entered after help opens.

HOLD is received by WAITFOR while help is already open. PAUSE then retains its
normal delay; the peer sends CPR during that delay. A correct reply after PAUSE
is insufficient if it misses the declared one-second compatibility deadline.
"""
import json
import sys
from pathlib import Path
import test_aspect_window_query_dos as query


def main():
    original_definitions = query.definitions
    original_adapter = query.keys.adapter

    def definitions():
        case = dict(original_definitions()[0])
        case.update(name='window-pause-query-4',
                    source=case['source'].replace('waitfor "END" 30',
                        'waitfor "HOLD" 10\npause 4\ntransmit "PAUSEDONE"\nwaitfor "END" 30'),
                    key_wire=b'keys\x1b[1;26RPAUSEDONEdone',
                    post_reply=b'\x1b[1;29R', extra_reply=b'\x1b[1;26R',
                    screen=[(0, 0, 'FIRST BYTE SAFE'), (0, 21, 'HOLDEND')])
        return [case]

    def adapter():
        module = original_adapter()
        run = module.run

        def staged(*args, **kwargs):
            kwargs['online_updates'] = [(2.0, b'HOLD'), (3.0, b'\x1b[6n')]
            return run(*args, **kwargs)

        module.run = staged
        return module

    query.BASE = query.ROOT / 'build/aspect-window-pause-query-dos'
    query.REPLY = b'\x1b[1;26R'
    query.definitions = definitions
    query.keys.adapter = adapter
    result = query.main()
    folder = query.BASE / sys.argv[sys.argv.index('--label') + 1]
    path = folder / 'query-checks.json'
    receipt = json.loads(path.read_text())
    events = json.loads((folder / 'peer-events.json').read_text())
    hold = next(event for event in events if event['kind'] == 'send' and event['hex'] == b'HOLD'.hex())
    received = b''
    pause_end = None
    for event in events:
        if event['kind'] == 'receive' and event['time'] >= hold['time']:
            received += bytes.fromhex(event['hex'])
            if b'PAUSEDONE' in received:
                pause_end = event['time']
                break
    elapsed = None if pause_end is None else pause_end - hold['time']
    receipt['checks']['four_second_pause_duration_retained'] = elapsed is not None and 4 <= elapsed <= 5
    receipt['passed'] = all(receipt['checks'].values())
    receipt.update(pause_complete_after_hold_seconds=elapsed, pause_driver_sha256=query.keys.renderer.sha(Path(__file__)),
                   scope=__doc__, pause_seconds=4, hold_send_after_connect=2.0,
                   query_send_after_connect=3.0)
    path.write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(dict(passed=receipt['passed'],pause_complete_after_hold_seconds=elapsed,checks=receipt['checks'])))
    return 0 if receipt['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
