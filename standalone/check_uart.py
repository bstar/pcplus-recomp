#!/usr/bin/env python3
"""Replay the actual linked DOS UART code with controlled UART/PIC/BIOS state.

This model checks bounded driver paths. It is not physical UART evidence.
Only the source-built MZ executable and its linker map are inputs.
"""
import collections
import hashlib
import json
from pathlib import Path
import re
import struct

from unicorn import Uc, UC_ARCH_X86, UC_MODE_16, UC_HOOK_CODE, UC_HOOK_INSN, UC_HOOK_INTR
from unicorn.x86_const import (UC_X86_REG_AX, UC_X86_REG_BX, UC_X86_REG_CX,
    UC_X86_REG_DX, UC_X86_REG_CS, UC_X86_REG_DS, UC_X86_REG_ES, UC_X86_REG_SS,
    UC_X86_REG_SP, UC_X86_REG_IP, UC_X86_REG_EFLAGS, UC_X86_INS_IN, UC_X86_INS_OUT)

ROOT = Path(__file__).resolve().parents[1]
BINARY = ROOT / 'build/standalone/SERIAL.EXE'
MAP = ROOT / 'build/standalone/serial.map'


class Machine:
    def __init__(self):
        self.image = BINARY.read_bytes()
        header = struct.unpack_from('<14H', self.image)
        size = (header[2] - 1) * 512 + (header[1] or 512)
        self.base_segment = 0x1000
        self.base = self.base_segment * 16
        self.uc = Uc(UC_ARCH_X86, UC_MODE_16)
        self.uc.mem_map(0, 0x100000)
        self.uc.mem_write(self.base, self.image[header[4] * 16:size])
        for i in range(header[3]):
            off, seg = struct.unpack_from('<HH', self.image, header[12] + i * 4)
            at = self.base + seg * 16 + off
            value = struct.unpack('<H', self.uc.mem_read(at, 2))[0]
            self.uc.mem_write(at, struct.pack('<H', (value + self.base_segment) & 0xffff))
        listing = MAP.read_text()
        group = re.search(r'^DGROUP\s+([0-9a-f]+):([0-9a-f]+)', listing, re.M | re.I)
        self.ds = self.base_segment + int(group[1], 16)
        self.data_base = self.ds * 16
        self.symbols = {}
        for seg, off, name in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$', listing, re.M | re.I):
            self.symbols[name] = self.base + int(seg, 16) * 16 + int(off, 16)
        self.rx = collections.deque()
        self.tx = []
        self.writes = []
        self.polls = collections.Counter()
        self.registers = {0x21: 0xff, 0x3fb: 3, 0x3fc: 0xb, 0x3f9: 0, 0x3fd: 0x60, 0x3fe: 0x90}
        self.divisor = [12, 0]
        self.cts_after = 0
        self.abort_after = None
        self.abort_polls = 0
        self.seconds = iter(range(100000))
        self.clock_calls = 0
        self.vectors = {0x0c: (0x1234, 0xf000)}
        self.returned = False
        self.uc.hook_add(UC_HOOK_CODE, self._code)
        self.uc.hook_add(UC_HOOK_INSN, self._input, None, 1, 0, UC_X86_INS_IN)
        self.uc.hook_add(UC_HOOK_INSN, self._output, None, 1, 0, UC_X86_INS_OUT)
        self.uc.hook_add(UC_HOOK_INTR, self._interrupt)

    def get(self, name, width=2):
        return int.from_bytes(self.uc.mem_read(self.symbols[name], width), 'little')

    def put(self, name, value, width=2):
        self.uc.mem_write(self.symbols[name], value.to_bytes(width, 'little'))

    def _code(self, uc, address, size, _):
        if address == self.base + 0xf000:
            self.returned = True
            uc.emu_stop()
        if address == self.symbols['pcplus_escape_pressed']:
            self.abort_polls += 1
            if self.abort_after is not None and self.abort_polls >= self.abort_after:
                # Model a host's escape callback result without executing its body.
                uc.reg_write(UC_X86_REG_AX, 1)
                sp = uc.reg_read(UC_X86_REG_SP)
                target = int.from_bytes(uc.mem_read(self.data_base + sp, 2), 'little')
                uc.reg_write(UC_X86_REG_SP, sp + 2)
                uc.reg_write(UC_X86_REG_IP, target)

    def _input(self, uc, port, size, _):
        self.polls[port] += 1
        if port in (0x3f8, 0x3f9) and self.registers[0x3fb] & 0x80:
            return self.divisor[port - 0x3f8]
        if port == 0x3f8:
            return self.rx.popleft() if self.rx else 0
        if port == 0x3fa:
            return 4 if self.rx else 1
        if port == 0x3fe and self.polls[port] <= self.cts_after:
            return self.registers[port] & ~0x10
        return self.registers.get(port, 0)

    def _output(self, uc, port, size, value, _):
        value &= (1 << (size * 8)) - 1
        self.writes.append((port, value))
        if port in (0x3f8, 0x3f9) and self.registers[0x3fb] & 0x80:
            self.divisor[port - 0x3f8] = value
        elif port == 0x3f8:
            self.tx.append(value)
        else:
            self.registers[port] = value

    def _interrupt(self, uc, number, _):
        ax = uc.reg_read(UC_X86_REG_AX)
        if number != 0x21:
            raise AssertionError(f'Unexpected DOS interrupt {number:x}')
        if ax >> 8 == 0x2c:
            seconds = next(self.seconds) % 60
            self.clock_calls += 1
            uc.reg_write(UC_X86_REG_DX, seconds << 8)
        elif ax >> 8 == 0x35:
            off, seg = self.vectors[ax & 0xff]
            uc.reg_write(UC_X86_REG_BX, off)
            uc.reg_write(UC_X86_REG_ES, seg)
        elif ax >> 8 == 0x25:
            self.vectors[ax & 0xff] = (uc.reg_read(UC_X86_REG_DX), uc.reg_read(UC_X86_REG_DS))
        else:
            raise AssertionError(f'Unexpected DOS service {ax:x}')

    def call(self, name, arguments=(), irq=False, limit=200000, **registers):
        uc = self.uc
        uc.reg_write(UC_X86_REG_CS, self.base_segment)
        uc.reg_write(UC_X86_REG_DS, self.ds)
        uc.reg_write(UC_X86_REG_SS, self.ds)
        uc.reg_write(UC_X86_REG_EFLAGS, 0x202)
        for register, value in registers.items():
            uc.reg_write(globals()['UC_X86_REG_' + register.upper()], value)
        words = ([0xf000, self.base_segment, 0x202] if irq else [0xf000]) + list(arguments)
        sp = 0xf000 - len(words) * 2
        uc.mem_write(self.data_base + sp, struct.pack('<' + 'H' * len(words), *words))
        uc.reg_write(UC_X86_REG_SP, sp)
        self.returned = False
        uc.emu_start(self.symbols[name], self.base + 0x10000, count=limit)
        assert self.returned, f'{name} did not return within {limit} instructions'
        return uc.reg_read(UC_X86_REG_AX)

    def receive_irq(self, data):
        self.rx.extend(data)
        self.call('uart_receive_interrupt', irq=True)


def run():
    cases = []

    def record(name, operation):
        operation()
        cases.append({'case': name, 'passed': True})
        print(name, 'passed', flush=True)

    def ring():
        m = Machine()
        assert m.call('uart_receive_byte') == 0xffff
        m.receive_irq(bytes([0x00, 0x80, 0xff]))
        assert m.get('uart_rx_count') == 3
        assert [m.call('uart_receive_byte') for _ in range(3)] == [0, 0x80, 0xff]
        assert m.call('uart_receive_byte') == 0xffff
        last = m.get('uart_rx_last')
        m.put('uart_rx_read', last)
        m.put('uart_rx_write', last)
        m.receive_irq(b'ab')
        assert m.get('uart_rx_write') == m.symbols['uart_rx_buffer'] - m.data_base + 1
        assert [m.call('uart_receive_byte') for _ in range(2)] == [97, 98]
        m.call('uart_unreceive_byte')
        assert m.call('uart_receive_byte') == 98
        m.receive_irq(b'queued')
        m.call('uart_clear_receive_buffer')
        assert m.get('uart_rx_count') == 0
        assert m.get('uart_rx_read') == m.get('uart_rx_write')
    record('empty-binary-wrap-unreceive-clear', ring)

    def software():
        m = Machine()
        m.put('uart_software_flow', 1)
        m.receive_irq(b'A' * 3072)
        assert not m.tx and m.get('uart_rx_count') == 3072
        m.receive_irq(b'B')
        assert not m.tx and m.get('uart_flow_pending', 1) == 0x13
        m.call('uart_poll_flow')
        assert m.tx == [0x13] and m.get('uart_xoff_sent', 1) == 1
        m.receive_irq(b'C' * 30)
        assert m.tx == [0x13]
        while m.get('uart_rx_count') > 129:
            m.call('uart_receive_byte')
        assert m.tx == [0x13]
        m.call('uart_receive_byte')
        assert m.tx == [0x13] and m.get('uart_xoff_sent', 1) == 0
        m.call('uart_poll_flow')
        assert m.tx == [0x13, 0x11]
        m.receive_irq(b'\x13')
        assert m.get('uart_tx_paused') == 1
        count = m.get('uart_rx_count')
        m.receive_irq(b'\x11')
        assert m.get('uart_tx_paused') == 0 and m.get('uart_rx_count') == count
    record('software-flow-high-low-water-and-control-bytes', software)

    def hardware():
        m = Machine()
        m.put('uart_hardware_flow', 1)
        m.receive_irq(b'A' * 3073)
        assert m.registers[0x3fc] == 9 and m.get('uart_rts_lowered', 1) == 1
        while m.get('uart_rx_count') > 128:
            m.call('uart_receive_byte')
        assert m.registers[0x3fc] == 11 and m.get('uart_rts_lowered', 1) == 0
        m.cts_after = 20
        m.call('uart_transmit_byte', [0x5a])
        assert m.polls[0x3fe] == 21 and m.tx == [0x5a]
    record('hardware-flow-high-low-water-and-cts-recovery', hardware)

    for mode in ('none', 'software', 'hardware'):
        def overflow(mode=mode):
            m = Machine()
            if mode != 'none':
                m.put('uart_' + mode + '_flow', 1)
            # A peer ignoring backpressure must not overwrite unread bytes.
            m.receive_irq(b'A' * 4096)
            for _ in range(8):
                m.receive_irq(b'Z')
            assert m.get('uart_rx_count') == 4096, f'{mode}: receive count exceeded capacity: {m.get("uart_rx_count")}'
            assert bytes(m.uc.mem_read(m.symbols['uart_rx_buffer'], 4096)) == b'A' * 4096
            assert m.get('uart_rx_dropped') == 8
            m.put('uart_rx_dropped',0xffff)
            m.receive_irq(b'ignored burst')
            assert m.get('uart_rx_dropped') == 0xffff and not m.rx
        record('receive-overflow-' + mode, overflow)

    def bounded_writes():
        m = Machine()
        for paused, hardware, cts, ready in [(1,0,True,True), (0,1,False,True), (0,0,True,False)]:
            m.put('uart_tx_paused', paused)
            m.put('uart_hardware_flow', hardware)
            m.registers[0x3fe] = 0x90 if cts else 0x80
            m.registers[0x3fd] = 0x60 if ready else 0
            assert m.call('uart_try_write', ax=0x55, limit=100) == 0x55
            assert m.uc.reg_read(UC_X86_REG_EFLAGS) & 1 and not m.tx
        m.put('uart_software_flow',1)
        m.receive_irq(b'A' * 3073)
        assert m.get('uart_flow_pending',1) == 0x13 and not m.tx
        m.call('uart_poll_flow', limit=100)
        assert m.get('uart_flow_pending',1) == 0x13 and not m.tx
        m.registers[0x3fd] = 0x60
        m.call('uart_poll_flow', limit=100)
        assert m.tx == [0x13] and m.get('uart_flow_pending',1) == 0
        m.put('uart_software_flow',0)
        m.put('uart_hardware_flow',1)
        m.registers[0x3fe] = 0x90
        assert m.call('uart_try_write',ax=0x55,limit=100) == 0x55
        assert not m.uc.reg_read(UC_X86_REG_EFLAGS) & 1 and m.tx == [0x13,0x55]
    record('bounded-writes-and-flow-queue-under-cts-thre-xoff-stalls', bounded_writes)

    def timeouts():
        m = Machine()
        m.seconds = iter([58, 59, 0, 1])
        assert m.call('uart_available', [3]) == 0xffff
        assert m.clock_calls == 4
        m.put('uart_tx_paused', 1)
        m.seconds = iter(range(20, 41))
        m.call('uart_transmit_byte', [0x4b])
        assert m.get('uart_tx_paused') == 0 and m.tx == [0x4b]
        assert m.clock_calls == 25
    record('receive-and-xoff-timeouts-across-seconds-rollover', timeouts)

    def settings():
        m = Machine()
        original = dict(m.registers)
        divisor = m.divisor.copy()
        m.call('uart_save_hardware_state')
        m.call('uart_set_baud_divisor', [38400, 0])
        assert m.divisor == [3, 0]
        m.call('uart_set_baud_divisor', [0, 1])
        assert m.divisor == [1, 0]
        m.call('uart_set_line_control', [0, 8, 1])
        assert m.registers[0x3fb] == 3
        m.call('uart_install_interrupt', [0x0c])
        assert m.vectors[0x0c] == (m.symbols['uart_receive_interrupt'] - m.base, m.base_segment)
        m.call('uart_enable')
        assert m.registers[0x21] == 0xef and m.registers[0x3f9] == 1
        m.call('uart_disable')
        m.call('uart_restore_interrupt', [0x0c])
        m.call('uart_restore_hardware_state')
        assert m.vectors[0x0c] == (0x1234, 0xf000)
        assert m.divisor == divisor
        assert m.registers == original
    record('baud-line-irq-and-hardware-restoration', settings)

    result = {'passed': True, 'binary_sha256': hashlib.sha256(BINARY.read_bytes()).hexdigest(),
              'cases': cases, 'scope': 'Linked source-only DOS code in Unicorn; controlled UART/PIC/DOS callbacks, no physical-device evidence.'}
    (ROOT / 'build/standalone/uart-checks.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    run()
