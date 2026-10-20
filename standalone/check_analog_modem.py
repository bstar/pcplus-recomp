#!/usr/bin/env python3
"""Analog-modem acceptance prerequisites, with UART/clock hardware modeled.

Execute source-linked DOS controller/UART instructions. These checks explicitly
characterize current carrier policy; they do not establish Boca compatibility.
"""
import hashlib
import json
from pathlib import Path

from check_connection import Connection
from terminal_config_fixtures import RATES

ROOT = Path(__file__).resolve().parents[1]


class Analog(Connection):
 def __init__(self, rate=38400, **settings):
  self.divisor_writes = []
  super().__init__(**settings)
  self.put('terminal_baud_low', rate & 65535)
  self.put('terminal_baud_high', rate >> 16)
  self.uc.mem_write(self.symbols['terminal_dial_target'], b'1\0')
  assert self.call('terminal_connection_prepare') == 0 and not self.flags()
  self.call('uart_set_baud_divisor', [rate & 65535, rate >> 16])
  assert self.divisor_writes == [(0, (115200 // rate) & 255),
                                 (1, (115200 // rate) >> 8)]
  assert self.lcr == 3  # 8N1 preserved across divisor programming.

 def output_port(self, uc, port, size, value, data):
  if self.lcr & 128 and port in (self.get('uart_port_thr'), self.get('uart_port_thr') + 1):
   self.divisor_writes.append((port - self.get('uart_port_thr'), value))
   return
  super().output_port(uc, port, size, value, data)


def main():
 cases = []
 def record(name, count):
  cases.append({'case': name, 'inputs': count, 'passed': True})
  print(name, 'passed', count, flush=True)

 # Generic CONNECT deliberately matches before suffixes. With fixed DTE this
 # must neither mis-select 300 baud nor rewrite the hardware divisor.
 responses = (b'CONNECT', b'CONNECT 14400', b'CONNECT 9600/ARQ', b'CONNECT 38400/V42BIS')
 for rate in RATES:
  for response in responses:
   m = Analog(rate, autobaud=0, timeout=60)
   programmed = list(m.divisor_writes)
   m.connect(response)
   assert bytes(m.tx) == b'ATZ\rATD1\r'
   assert m.get('terminal_baud_low') + (m.get('terminal_baud_high') << 16) == rate
   assert m.get('connection_baud_index') == RATES.index(rate)
   assert m.divisor_writes == programmed and m.lcr == 3
 record('numeric-local-dial-fixed-DTE-and-verbose-result-suffixes', len(RATES) * len(responses))

 # A successful result currently admits online mode even if DCD never rises.
 # Keep this limitation visible rather than claiming strict carrier admission.
 m = Analog(timeout=60)
 m.carrier = False
 m.connect()
 m.poll(100)
 assert m.state() == 6
 m.carrier = True
 m.poll()
 assert m.state() == 6
 m.cts = False
 m.enqueue(b'UNSENT')
 m.poll()
 assert m.get('terminal_tx_count') == 6
 m.carrier = False
 m.poll()
 assert m.state() == 0 and m.get('connection_status') == 6
 assert m.get('terminal_tx_count') == 0 and b'UNSENT' not in bytes(m.tx)
 # New session must forget previous carrier history.
 m.cts = True
 m.connect()
 m.poll(40)
 assert m.state() == 6
 record('DCD-never-high-current-policy-loss-clears-TX-and-redial-resets-history', 3)

 for initial in (0x0a, 0x0b, 0x1e, 0x1f):
  for drop in (0, 1):
   m = Analog(drop=drop, timeout=60)
   m.mcr = initial
   m.connect()
   m.cts = False
   m.call('terminal_connection_cancel', ax=0)
   m.poll(18)
   if drop:
    assert m.state() == 8 and m.mcr == initial & ~1
    # Simulate an independent flow owner changing RTS during the DTR pulse.
    m.mcr ^= 2
    m.poll(18)
    assert m.mcr == initial ^ 2
    assert m.controls == [initial & ~1, initial ^ 2]
   else:
    assert not m.controls and m.mcr == initial
   assert m.state() == 0 and m.get('connection_status') == 4
 record('configured-DTR-pulse-restores-only-DTR-and-preserves-current-RTS', 8)

 m = Analog(timeout=60)
 m.start()
 m.waiting()
 m.tick += (55 * 1193182) // 65536
 m.poll()
 assert m.state() == 5
 m.receive(b'CONNECT 14400')
 m.poll()
 assert m.state() == 6
 m = Analog(timeout=60)
 m.cts = False
 m.start()
 m.tick += (61 * 1193182) // 65536
 m.poll(40)
 assert m.state() == 0 and m.get('connection_status') == 3 and not m.tx
 record('long-handshake-budget-and-stalled-init-use-configured-deadline', 2)

 binary = ROOT / 'build/terminal/TERMINAL.EXE'
 result = {'passed': True, 'binary_sha256': hashlib.sha256(binary.read_bytes()).hexdigest(),
           'input_sha256': {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
                            for p in ('build/terminal/terminal.map',
                                      'standalone/check_analog_modem.py',
                                      'standalone/check_connection.py',
                                      'standalone/check_transport.py',
                                      'standalone/dos_image.py',
                                      'standalone/modem_fixtures.py',
                                      'standalone/terminal_config_fixtures.py')},
           'cases': cases, 'inputs': sum(c['inputs'] for c in cases),
           'scope': 'Actual linked DOS controller and UART instructions; UART registers, BIOS ticks and keyboard are modeled. Numeric target is staged after CLI validation; no analog audio, SIP, Telnet, physical DCD/CTS or Boca test.',
           'known_limit': 'CONNECT admits online without requiring DCD high; generic CONNECT first-match remains legacy behavior.'}
 (ROOT / 'build/terminal/analog-modem-checks.json').write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
 main()
