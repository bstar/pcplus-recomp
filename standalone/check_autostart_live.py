#!/usr/bin/env python3
"""Linked invitation owner and actual ZMODEM receiver, modeled DOS/hardware.
Ordinary input is observed without replacing product instructions or callbacks.
"""
import hashlib
import json
import struct
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_SP
from check_terminal_zmodem_live import LiveZmodem, ROOT, BINARY
from check_zmodem import h

class Automatic(LiveZmodem):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.delivered = bytearray()
        self.uc.hook_add(UC_HOOK_CODE, self.observe)
        self.call('_terminal_autostart_initialize')
        self.put('_terminal_transfer_preferences', 1)
        self.uc.mem_write(self.symbols['_terminal_transfer_preferences'] + 2,
                          b'D:\\RECV\\'.ljust(64, b'\0'))
    def observe(self, u, address, size, _):
        if address == self.symbols['_terminal_auto_deliver']:
            sp = u.reg_read(UC_X86_REG_SP)
            value = struct.unpack('<H', u.mem_read(self.data_base + sp + 2, 2))[0]
            self.delivered.append(value)
    def feed(self, wire):
        for value in wire:
            self.call('_terminal_autostart_input', [value], limit=1000000)

def main():
    cases = []
    def check(name, fn):
        fn(); cases.append(dict(case=name, passed=True)); print(name, 'PASS', flush=True)
    def receive():
        for size in (0, 1, 1025, 18433):
            m = Automatic(source=(bytes(range(256)) * 73)[:size])
            # The invitation uses the real UART ISR and ordinary main-loop read.
            for value in h(0)[:20]:
                m.rx.append(value)
                byte = m.call('uart_receive_byte')
                assert byte == value, (byte,value,m.get("uart_rx_count"))
                m.call('_terminal_autostart_input', [byte], limit=1000000)
            assert m.get('terminal_transfer_pending') == 1 and m.get('terminal_transfer_automatic') == 1
            assert not m.delivered and m.get('terminal_transfer_protocol') == 2
            m.rx.extend(h(0)[20:])
            m.call('terminal_transfer_poll', limit=100000000)
            assert m.get('terminal_transfer_fault') == 0 and not m.get('terminal_transfer_active')
            assert not m.get('terminal_transfer_automatic') and not m.script and not m.pending
            assert bytes(m.files['D:\\RECV\\ONE.BIN']) == m.source
            assert not m.filename_sent and not m.waiting_ui
    check('UART-invitation-starts-checked-receiver-without-prompt-four-sizes', receive)
    def conserve():
        for wire in (b'BBS text\r\n', b'***x', h(0)[:13] + b'!',
                     h(0)[:16] + b'1' + h(0)[17:], h(1), h(0, 0x12000000)):
            m = Automatic();m.feed(wire);m.call('_terminal_autostart_flush')
            assert m.delivered == wire and not m.get('terminal_transfer_pending'), wire
    check('ordinary-truncated-corrupt-other-header-and-command-input-preserved', conserve)
    def deadline():
        for length in range(1, 20):
            m = Automatic();m.advance_ticks = False;m.tick = 100
            prefix = h(0)[:length];m.feed(prefix)
            assert not m.delivered
            m.tick = 135;m.call('_terminal_autostart_poll');assert not m.delivered
            m.tick = 136;m.call('_terminal_autostart_poll')
            assert m.delivered == prefix and not m.get('terminal_transfer_pending')
    check('nineteen-truncations-expire-at-serviced-36-tick-deadline', deadline)
    def midnight():
        from check_meta_actions_live import DAY
        for before in (DAY-1, DAY-18, 65535):
            m = Automatic();m.advance_ticks = False;m.tick = before;m.feed(b'**')
            m.tick = (before+35) % DAY;m.call('_terminal_autostart_poll')
            assert not m.delivered
            m.tick = (before+36) % DAY;m.call('_terminal_autostart_poll')
            assert m.delivered == b'**'
    check('midnight-and-low-word-rollover-preserve-complete-deadline', midnight)
    def guards():
        for field, value in [('_terminal_transfer_preferences', 0), ('uart_rx_mask', 127),
                             ('uart_software_flow', 1), ('uart_break_hold', 1),
                             ('terminal_monitor_active', 1), ('terminal_controller_active', 1),
                             ('terminal_transfer_pending', 1), ('terminal_transfer_active', 1),
                             ('terminal_program_pending', 1), ('terminal_program_active', 1),
                             ('terminal_macro_active', 1), ('connection_state', 2),
                             ('terminal_parser_active', 1), ('terminal_ansi_wait_active', 1)]:
            m = Automatic();m.feed(b'*');assert not m.delivered
            m.put(field, value);m.call('_terminal_autostart_poll')
            assert m.delivered == b'*', field
    check('disabled-format-and-twelve-owner-boundaries-flush-held-input', guards)
    result = dict(passed=True, cases=cases, binary_sha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),
                  scope='Linked UART invitation, foreground recognizer, automatic admission, UI bypass and checked ZMODEM file owner. BIOS/UART/ticks/DOS kernel modeled, independent peer scripts; ordinary input observed without patching product callbacks. No actual DOS or BBS automatic-reception claim.')
    (ROOT / 'build/terminal/autostart-live-checks.json').write_text(json.dumps(result, indent=2) + '\n')

if __name__ == '__main__':
    main()
