#!/usr/bin/env python3
"""Real DOS numeric dial followed by typing a BBS hostname at CONNECT>.

Synthetic serial peer only: no claim of SIP/audio or physical modem coverage.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

from modem_fixtures import fixture
from test_connection_dos import run

ROOT = Path(__file__).resolve().parents[1]


def main():
 parser = argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--label', required=True)
 label = parser.parse_args().label
 assert re.fullmatch(r'[a-z0-9][a-z0-9-]{0,70}', label)
 out = ROOT / 'build/connection-dos' / label
 assert not out.exists(), 'Use a fresh label to preserve prior attempts'
 inputs = ['build/terminal/TERMINAL.EXE', 'build/terminal/terminal.map',
           'standalone/test_analog_dial_dos.py', 'standalone/test_connection_dos.py',
           'standalone/modem_fixtures.py', 'standalone/terminal_config_fixtures.py',
           'standalone/test_terminal.py', 'standalone/directory_test_support.py']
 def hashes():
  return {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in inputs}
 frozen = hashes()
 proof = run(label, 'success', 'p4000 b b s . e x a m p l e enter p700 a-x',
             prm=fixture(timeout=60, autobaud=0), target=b'1',
             arguments='@D:\\TEST.PRM /D:1 COM1 38400 8N1 HARD',
             banner=b'\x1b[2J\x1b[HFIRST BYTE SAFE\x1b[6n\x1b[0c\r\nCONNECT> ')
 wire = (out / 'serial.bin').read_bytes()
 screen = (out / 'SCREEN.BIN').read_bytes()[::2]
 proof['checks'].update({
  'numeric_local_dial_only': proof['commands'] == ['ATZ', 'ATD1'],
  'BBS_hostname_sent_as_online_terminal_data': b'bbs.example\r' in wire,
  'hostname_not_used_in_ATD_command': b'ATDbbs' not in wire,
  'bridge_prompt_displayed': b'CONNECT> ' in screen,
  'frozen_inputs_unchanged': hashes() == frozen,
 })
 proof['passed'] = all(proof['checks'].values())
 proof['frozen_inputs'] = frozen
 proof['scope'] = ('Actual DOS CLI /D:1, initialization, dial, CONNECT, ANSI replies, '
                   'bridge prompt display and BIOS-keyboard hostname transmission. '
                   'Synthetic serial peer; no analog carrier/audio, SIP, Telnet '
                   'negotiation, remote BBS, or physical UART timing.')
 (out / 'analog-result.json').write_text(json.dumps(proof, indent=2) + '\n')
 print('analog-dial', 'PASS' if proof['passed'] else json.dumps(proof), flush=True)
 return 0 if proof['passed'] else 1


if __name__ == '__main__':
 raise SystemExit(main())
