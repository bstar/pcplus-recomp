#!/usr/bin/env python3
"""Require an observed modem pause during the actual stock-editor mapper run."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    folder = args.output.resolve()
    assert folder.is_relative_to(ROOT/'build/bbs-lab/results')
    modem = json.loads((folder/'modem.json').read_text())
    run = json.loads((folder/'proxy-integration.json').read_text())
    data = (folder/'serial-sent.bin').read_bytes()
    marker = data.find(b'KEYTEST')
    lines = [event for event in modem['events'] if event['kind']=='serial-lines']
    pauses = []
    for first, last in zip(lines,lines[1:]):
        if (not first['rts'] and first['dtr'] and last['rts'] and last['dtr']
                and marker>=0 and first['delivered']>=marker+7
                and last['seconds']-first['seconds']>=1):
            pauses.append(dict(begin=first,end=last,seconds=round(last['seconds']-first['seconds'],3)))
    checks = dict(actual_mapper_and_editor_return=run['passed'] and run['keymap']['passed'],
                  control_line_model=modem['flow_mode']=='RTS-model',
                  post_subject_pause_observed=bool(pauses),
                  no_BBS_bytes_delivered_while_paused=bool(pauses) and all(p['begin']['delivered']==p['end']['delivered'] for p in pauses),
                  actual_DOS_exit_zero=(folder/'EXITCODE.BIN').read_bytes()==bytes(6))
    names = ['modem.json','proxy-integration.json','keymap-audit.json','EXITCODE.BIN','serial-sent.bin','serial-received.bin']
    sha = lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
    result = dict(passed=all(checks.values()),checks=checks,pauses=pauses,
                  parent_sha256=run['binary_sha256'],helper_sha256=run['keymap']['helper_sha256'],
                  capture_inputs={name:sha(folder/name) for name in names},
                  sources={str(Path(__file__).resolve().relative_to(ROOT)):sha(Path(__file__))},
                  scope='Actual DOSBox RTS envelopes, model holds peer CTS/DSR high and gates single-byte BBS delivery while RTS is low. DTR stays asserted during measured mapper pause. No real CTS transitions, modem latency, analog/SIP/audio or physical acceptance.')
    (folder/'keymap-flow-audit.json').write_text(json.dumps(result,indent=2)+'\n')
    assert result['passed'],checks
    print('PASS mapper RTS pause:',[p['seconds'] for p in pauses],'seconds; no delivery during pause')


if __name__ == '__main__':
    main()
